from config import parse_args
from scraper import scrape
from exporter import export


def main():
    config = parse_args()

    print(f"=== Threads 爬蟲啟動 ===")
    print(f"關鍵字：{config.keyword}")
    print(f"最大貼文數：{config.max_posts}")
    print(f"排序：{config.sort}")
    if config.start_date:
        print(f"起始日期：{config.start_date}")
    if config.end_date:
        print(f"結束日期：{config.end_date}")
    print(f"無頭模式：{config.headless}")
    print()

    posts = scrape(config)

    if not posts:
        print("未抓到任何貼文，請確認關鍵字或網路狀態。")
        return

    output_path = export(posts, config.output)
    print()
    print(f"=== 完成 ===")
    print(f"共匯出 {len(posts)} 篇貼文")
    print(f"輸出檔案：{output_path.resolve()}")


if __name__ == "__main__":
    main()
