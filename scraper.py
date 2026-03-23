import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, Page, Response

from config import Config

AUTH_JSON = Path(__file__).parent / "auth.json"


def _parse_post_node(post: dict) -> Optional[dict]:
    """解析單一 post 節點，回傳標準化 dict 或 None。"""
    user = post.get("user", {}) or {}
    username = user.get("username", "")
    if not username:
        return None

    pk = post.get("pk", "") or post.get("id", "")
    code = post.get("code", "") or post.get("shortcode", "")

    if code:
        link = f"https://www.threads.com/@{username}/post/{code}"
    elif pk:
        link = f"https://www.threads.com/@{username}/post/{pk}"
    else:
        link = f"https://www.threads.com/@{username}"

    caption = post.get("caption", {})
    content = caption.get("text", "") if isinstance(caption, dict) else (str(caption) if caption else "")

    taken_at = post.get("taken_at", 0) or 0
    if taken_at:
        ts = datetime.fromtimestamp(int(taken_at), tz=timezone.utc)
        timestamp = ts.strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        timestamp = ""

    tags = re.findall(r"#(\w+)", content)
    tag_str = " ".join(f"#{t}" for t in tags)

    return {
        "timestamp": timestamp,
        "account": f"@{username}",
        "link": link,
        "tag": tag_str,
        "content": content,
        "taken_at_ts": int(taken_at) if taken_at else 0,
    }


def _extract_posts_from_ssr(html: str) -> list[dict]:
    """從 SSR HTML 的 __bbox JSON 中提取貼文。"""
    posts = []

    # 找所有 __bbox 區塊（Relay/Comet SSR 格式）
    for m in re.finditer(r'\{"__bbox":\{', html):
        start = m.start()
        # 找對應的結尾大括號
        depth = 0
        end = start
        for i, c in enumerate(html[start:], start):
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end == start:
            continue

        try:
            blob = json.loads(html[start:end])
        except json.JSONDecodeError:
            continue

        bbox = blob.get("__bbox") or {}
        result = bbox.get("result") or {}
        data = result.get("data") or {}

        # searchResults 結構
        search_results = data.get("searchResults") or {}
        edges = search_results.get("edges", [])
        for edge in edges:
            thread = edge.get("node", {}).get("thread", {})
            for item in thread.get("thread_items", []):
                post = item.get("post", {})
                if post:
                    p = _parse_post_node(post)
                    if p:
                        posts.append(p)

    return posts


def _extract_posts_from_json(data: dict) -> list[dict]:
    """從 JSON 回應（bulk-route-definitions 等）遞迴提取貼文。"""
    posts = []

    def walk(obj):
        if isinstance(obj, list):
            for item in obj:
                walk(item)
        elif isinstance(obj, dict):
            if "thread_items" in obj:
                for item in obj["thread_items"]:
                    post = item.get("post", {})
                    if post:
                        p = _parse_post_node(post)
                        if p:
                            posts.append(p)
            # 搜尋 edges (GraphQL pagination)
            elif "edges" in obj and isinstance(obj.get("edges"), list):
                for edge in obj["edges"]:
                    thread = edge.get("node", {}).get("thread", {})
                    for item in thread.get("thread_items", []):
                        post = item.get("post", {})
                        if post:
                            p = _parse_post_node(post)
                            if p:
                                posts.append(p)
                for v in obj.values():
                    if isinstance(v, (dict, list)):
                        walk(v)
            else:
                for v in obj.values():
                    walk(v)

    walk(data)
    return posts


def _parse_response_body(body: str) -> Optional[dict]:
    """解析回應 body，去除 for(;;); 前綴後轉為 dict。"""
    text = body
    if text.startswith("for (;;);"):
        text = text[9:]
    elif text.startswith("for(;;);"):
        text = text[8:]
    try:
        return json.loads(text)
    except Exception:
        return None


def _do_login(page: Page) -> None:
    page.goto("https://www.threads.com/login")
    print("請在瀏覽器中完成登入...")
    input("登入完成後請按 Enter：")


def scrape(config: Config) -> list[dict]:
    """執行爬蟲，回傳貼文列表。"""
    collected: dict[str, dict] = {}

    def add_posts(posts: list[dict]):
        for p in posts:
            if p["link"] not in collected:
                collected[p["link"]] = p

    def handle_response(response: Response):
        url = response.url
        # 跳過靜態資源
        if any(x in url for x in ['.js', '.css', 'fbcdn.net', 'cdninstagram.com', 'rsrc.php']):
            return
        try:
            body = response.text()
        except Exception:
            return

        # HTML 頁面：從 __bbox SSR 解析
        ctype = response.headers.get("content-type", "")
        if "text/html" in ctype:
            posts = _extract_posts_from_ssr(body)
            if posts:
                add_posts(posts)
                print(f"  [HTML SSR] 解析到 {len(posts)} 篇貼文")
            return

        # JSON / JavaScript 回應：嘗試解析
        data = _parse_response_body(body)
        if data:
            posts = _extract_posts_from_json(data)
            if posts:
                add_posts(posts)
                print(f"  [JSON] 從 {url[:60]} 解析到 {len(posts)} 篇貼文")

    with sync_playwright() as pw:
        context_kwargs = {
            "viewport": {"width": 1280, "height": 900},
            "user_agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }

        if config.login and AUTH_JSON.exists():
            print(f"載入登入 session：{AUTH_JSON}")
            context_kwargs["storage_state"] = str(AUTH_JSON)

        if config.login and not AUTH_JSON.exists():
            browser = pw.chromium.launch(headless=False)
            context = browser.new_context(**context_kwargs)
            page = context.new_page()
            _do_login(page)
            context.storage_state(path=str(AUTH_JSON))
            print(f"Session 已儲存至 {AUTH_JSON}")
            browser.close()
            context_kwargs["storage_state"] = str(AUTH_JSON)

        browser = pw.chromium.launch(headless=config.headless)
        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        page.on("response", handle_response)

        serp_type = "recent" if config.sort == "recent" else "default"
        # 使用 threads.com（threads.net 已 301 重導）
        url = f"https://www.threads.com/search?q={config.keyword}&serp_type={serp_type}"
        print(f"前往搜尋頁：{url}")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

        print(f"初始載入後收集到 {len(collected)} 篇")

        # 無限滾動（對登入用戶有效，可觸發更多 API 請求）
        no_new_count = 0
        max_no_new = 3

        while len(collected) < config.max_posts and no_new_count < max_no_new:
            prev_count = len(collected)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(int(config.delay * 1000))

            if len(collected) == prev_count:
                no_new_count += 1
                print(f"  滾動無新貼文（{no_new_count}/{max_no_new}）")
            else:
                no_new_count = 0
                print(f"  已收集 {len(collected)} 篇...")

        browser.close()

    posts = list(collected.values())
    print(f"爬蟲完成，共收集 {len(posts)} 篇貼文（過濾前）")

    # 日期過濾
    if config.start_date or config.end_date:
        filtered = []
        for p in posts:
            ts = p.get("taken_at_ts", 0)
            if not ts:
                filtered.append(p)
                continue
            post_date = datetime.fromtimestamp(ts, tz=timezone.utc).date()
            if config.start_date and post_date < config.start_date:
                continue
            if config.end_date and post_date > config.end_date:
                continue
            filtered.append(p)
        print(f"日期過濾後剩 {len(filtered)} 篇")
        posts = filtered

    for p in posts:
        p.pop("taken_at_ts", None)

    return posts[:config.max_posts]
