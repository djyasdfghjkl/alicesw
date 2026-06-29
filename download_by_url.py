import argparse
import os
from spider_batch import NovelSpider, BASE_DIR

def main():
    parser = argparse.ArgumentParser(description="通过小说目录/书页 URL 下载整本小说")
    parser.add_argument('url', help='小说目录页或书页 URL')
    parser.add_argument('-f', '--format', choices=['single', 'chapter'], default='single', help='保存格式：single 或 chapter')
    parser.add_argument('--title', help='可选：指定小说标题，覆盖自动识别')
    parser.add_argument('--author', help='可选：指定作者，覆盖自动识别')
    args = parser.parse_args()

    spider = NovelSpider()
    novel = spider.get_novel_content_by_url(args.url, novel_title=args.title, novel_author=args.author)
    if not novel or not novel.get('chapters'):
        print("未获取到小说内容")
        return 1

    download_dir = os.path.join(BASE_DIR, "downloads")
    spider.save_novel_to_file(novel, download_dir=download_dir, save_format=args.format)
    print(f"保存目录：{download_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())