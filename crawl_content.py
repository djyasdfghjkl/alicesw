from novel_spider import NovelSpider
import argparse

parser = argparse.ArgumentParser(description='爬取小说章节内容')
parser.add_argument('novel_url', type=str, help='小说目录页URL')
args = parser.parse_args()

spider = NovelSpider()



    chapters = spider.get_novel_chapters(novels[0][args.novel_url])
    print(f"找到 {len(chapters)} 个章节")

    # 获取章节内容
    if chapters:
        content = spider.get_chapter_content(chapters[0][args.novel_url])
        print(f"内容长度: {len(content)} 字符")