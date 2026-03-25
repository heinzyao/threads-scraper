# threads-scraper

**繁體中文** | [English](#english)

以關鍵字搜尋 Threads 貼文，自動擷取並匯出為 Excel。

使用 Playwright 攔截頁面 SSR 資料（Relay `__bbox` 格式），無需 API key。

---

## 需求

- Python 3.14+
- [uv](https://github.com/astral-sh/uv)

## 安裝

```bash
uv sync
uv run playwright install chromium
```

## 使用

```bash
# 單一關鍵字（預設 50 篇，headless 模式）
uv run python main.py --keyword "AI"

# 多關鍵字批次搜尋（結果合併到同一 Excel）
uv run python main.py --keyword "AI" "LLM" "台股"

# 排除包含指定詞的貼文
uv run python main.py --keyword "AI" --exclude "廣告" "spam"

# 多關鍵字 + 排除 + 日期過濾
uv run python main.py --keyword "AI" "LLM" --exclude "廣告" \
  --start-date 2026-01-01 --end-date 2026-03-31 --max-posts 30

# 自訂輸出路徑
uv run python main.py --keyword "AI" --output output/ai_posts.xlsx

# 開啟瀏覽器視窗（方便除錯）
uv run python main.py --keyword "AI" --no-headless

# 使用登入 session（可取得更多貼文，首次會開啟瀏覽器要求手動登入）
uv run python main.py --keyword "AI" --login
```

## 參數說明

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `--keyword` | 必填 | 搜尋關鍵字（可多個，空格分隔）|
| `--exclude` | — | 排除包含指定詞的貼文（可多個，case-insensitive）|
| `--max-posts` | 50 | 最大抓取貼文數（每個關鍵字各自計算）|
| `--sort` | recent | 排序：`recent`（最新）/ `top`（熱門）|
| `--start-date` | — | 起始日期 `YYYY-MM-DD`（可選）|
| `--end-date` | — | 結束日期 `YYYY-MM-DD`（可選）|
| `--output` | `threads_output.xlsx` | 輸出檔名 |
| `--headless` / `--no-headless` | headless | 是否無頭模式 |
| `--delay` | 3.0 | 滾動間隔秒數 |
| `--login` | False | 使用登入 session（session 快取於 `auth.json`）|

## 輸出欄位

| 欄位 | 說明 |
|------|------|
| 查詢日期 | 執行當天日期 |
| 搜尋關鍵字 | 觸發此貼文的關鍵字（多關鍵字命中時以 ` / ` 合併）|
| 發文時間 | 貼文 UTC 時間 |
| 帳號 | 作者 @handle |
| 貼文連結 | `threads.com/@user/post/...` |
| 標籤 | 正文中的 #hashtag |
| 內容 | 貼文全文 |

## 技術說明

- **資料來源**：解析初始 HTML 頁面中 Relay/Comet `__bbox` SSR JSON blob
- **無限滾動**：連續 3 次滾動無新貼文時停止；登入用戶可觸發更多 API 請求
- **去重**：以貼文 URL 為 key 去除重複
- **日期過濾**：Threads 搜尋 API 不支援伺服器端日期篩選，改用 `taken_at` timestamp 在 client-side 過濾

> **注意**：未登入時每次約可取得 20 篇貼文（Threads 限制）。使用 `--login` 並手動完成登入可取得更多結果。

---

<a name="english"></a>

# threads-scraper — English

[繁體中文](#threads-scraper) | **English**

Search Threads posts by keyword, automatically scrape results, and export to Excel.

Uses Playwright to intercept SSR page data (Relay `__bbox` format). No API key required.

---

## Requirements

- Python 3.14+
- [uv](https://github.com/astral-sh/uv)

## Installation

```bash
uv sync
uv run playwright install chromium
```

## Usage

```bash
# Single keyword (default 50 posts, headless mode)
uv run python main.py --keyword "AI"

# Multiple keywords — results merged into one Excel file
uv run python main.py --keyword "AI" "LLM" "stocks"

# Exclude posts containing specific words
uv run python main.py --keyword "AI" --exclude "ad" "spam"

# Multiple keywords + exclusion + date filter
uv run python main.py --keyword "AI" "LLM" --exclude "ad" \
  --start-date 2026-01-01 --end-date 2026-03-31 --max-posts 30

# Custom output path
uv run python main.py --keyword "AI" --output output/ai_posts.xlsx

# Show browser window (useful for debugging)
uv run python main.py --keyword "AI" --no-headless

# Use a login session (retrieves more posts; first run opens browser for manual login)
uv run python main.py --keyword "AI" --login
```

## Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--keyword` | required | Search keywords (multiple values separated by spaces) |
| `--exclude` | — | Exclude posts containing these words (multiple values, case-insensitive) |
| `--max-posts` | 50 | Maximum posts to fetch (counted per keyword) |
| `--sort` | recent | Sort order: `recent` (newest) / `top` (popular) |
| `--start-date` | — | Start date filter `YYYY-MM-DD` (optional) |
| `--end-date` | — | End date filter `YYYY-MM-DD` (optional) |
| `--output` | `threads_output.xlsx` | Output filename |
| `--headless` / `--no-headless` | headless | Run browser in headless mode or not |
| `--delay` | 3.0 | Scroll interval in seconds |
| `--login` | False | Use login session (session cached in `auth.json`) |

## Output Columns

| Column | Description |
|--------|-------------|
| 查詢日期 | Date the script was run |
| 搜尋關鍵字 | Keyword(s) that matched this post (multiple matches joined with ` / `) |
| 發文時間 | Post UTC timestamp |
| 帳號 | Author @handle |
| 貼文連結 | `threads.com/@user/post/...` |
| 標籤 | #hashtags found in post body |
| 內容 | Full post text |

## How It Works

- **Data source**: Parses the Relay/Comet `__bbox` SSR JSON blob embedded in the initial HTML page
- **Infinite scroll**: Stops after 3 consecutive scrolls with no new posts; logged-in users trigger additional API requests
- **Deduplication**: Posts are deduplicated by URL
- **Date filtering**: The Threads search API does not support server-side date filtering; client-side filtering is applied using the `taken_at` timestamp

> **Note**: Without login, each search returns approximately 20 posts (Threads limitation). Use `--login` and complete the manual login to retrieve more results.
