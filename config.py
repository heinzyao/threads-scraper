import argparse
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Config:
    keyword: str
    max_posts: int
    sort: str
    start_date: Optional[date]
    end_date: Optional[date]
    output: str
    headless: bool
    delay: float
    login: bool


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Threads 關鍵字爬蟲")
    parser.add_argument("--keyword", required=True, help="搜尋關鍵字")
    parser.add_argument("--max-posts", type=int, default=50, help="最大抓取貼文數（預設 50）")
    parser.add_argument("--sort", choices=["recent", "top"], default="recent", help="排序方式（預設 recent）")
    parser.add_argument("--start-date", help="起始日期 YYYY-MM-DD（可選）")
    parser.add_argument("--end-date", help="結束日期 YYYY-MM-DD（可選）")
    parser.add_argument("--output", default="threads_output.xlsx", help="輸出檔名（預設 threads_output.xlsx）")
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True, help="無頭模式（預設 True）")
    parser.add_argument("--delay", type=float, default=3.0, help="滾動間隔秒數（預設 3）")
    parser.add_argument("--login", action="store_true", default=False, help="是否使用登入 session")

    args = parser.parse_args()

    start_date = date.fromisoformat(args.start_date) if args.start_date else None
    end_date = date.fromisoformat(args.end_date) if args.end_date else None

    return Config(
        keyword=args.keyword,
        max_posts=args.max_posts,
        sort=args.sort,
        start_date=start_date,
        end_date=end_date,
        output=args.output,
        headless=args.headless,
        delay=args.delay,
        login=args.login,
    )
