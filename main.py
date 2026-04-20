import dataclasses

from config import parse_args
from scraper import scrape
from exporter import export


def _apply_exclude(posts: list[dict], exclude: list[str]) -> list[dict]:
    """過濾掉內容含任一排除詞的貼文（case-insensitive）。"""
    if not exclude:
        return posts
    lower_excludes = [kw.lower() for kw in exclude]
    return [
        p for p in posts
        if not any(ex in p.get("content", "").lower() for ex in lower_excludes)
    ]


def _apply_include_exact(posts: list[dict], keyword: str) -> list[dict]:
    """確保貼文內容精確包含指定的搜尋關鍵字（case-insensitive）。"""
    lower_kw = keyword.lower()
    return [
        p for p in posts
        if lower_kw in p.get("content", "").lower()
    ]


def main():
    config = parse_args()

    print("=== Threads 爬蟲啟動 ===")
    print(f"關鍵字：{' / '.join(config.keywords)}")
    print(f"最大貼文數（每關鍵字）：{config.max_posts}")
    print(f"排序：{config.sort}")
    if config.start_date:
        print(f"起始日期：{config.start_date}")
    if config.end_date:
        print(f"結束日期：{config.end_date}")
    if config.exclude:
        print(f"排除關鍵字：{config.exclude}")
    print(f"無頭模式：{config.headless}")
    print()

    # 跨關鍵字去重：URL -> post dict（含 search_keyword 欄位）
    merged: dict[str, dict] = {}

    for kw in config.keywords:
        print(f"--- 搜尋關鍵字：{kw} ---")
        single_config = dataclasses.replace(config, keyword=kw)
        posts = scrape(single_config)

        # 針對搜尋關鍵字進行精確內文比對
        before_exact = len(posts)
        posts = _apply_include_exact(posts, kw)
        if before_exact != len(posts):
            print(f"  精確包含過濾：{before_exact} → {len(posts)} 篇（移除未完整包含 '{kw}' 的 {before_exact - len(posts)} 篇）")

        for p in posts:
            url = p["link"]
            if url not in merged:
                merged[url] = {**p, "search_keyword": kw}
            else:
                # 同一貼文出現在多個關鍵字結果，合併顯示
                existing = merged[url]["search_keyword"].split(" / ")
                if kw not in existing:
                    merged[url]["search_keyword"] += f" / {kw}"

        print()

    all_posts = list(merged.values())

    # 排除關鍵字過濾
    if config.exclude:
        before = len(all_posts)
        all_posts = _apply_exclude(all_posts, config.exclude)
        print(f"排除過濾：{before} → {len(all_posts)} 篇（移除 {before - len(all_posts)} 篇）")

    if not all_posts:
        print("未抓到任何貼文（或全部被排除），請確認關鍵字或網路狀態。")
        return

    output_path = export(all_posts, config.output)
    print()
    print("=== 完成 ===")
    print(f"共匯出 {len(all_posts)} 篇貼文")
    print(f"輸出檔案：{output_path.resolve()}")


if __name__ == "__main__":
    main()
