# 小说爬虫工具

这是一个基于Python的小说爬虫工具，可以从爱丽丝书屋 (ALICESW.COM) 网站爬取小说内容。

## 功能特性

- 支持多种搜索方式：按标题、作者、标签或模糊搜索
- 自动获取小说的所有章节
- 提取章节内容并保持格式
- 支持保存到本地文件

## 依赖库

- requests
- beautifulsoup4
- lxml

## 安装依赖

```bash
pip install requests beautifulsoup4 lxml
```

## 使用方法

### 1. 交互式使用

运行主程序：

```bash
python novel_spider.py
```

按照提示选择搜索类型和输入关键词。

### 2. 编程方式使用

```python
from novel_spider import NovelSpider

spider = NovelSpider()

# 搜索小说
novels = spider.search_novels("女友", "_all")
print(f"找到 {len(novels)} 本小说")

# 获取小说章节
if novels:
    chapters = spider.get_novel_chapters(novels[0]['url'])
    print(f"找到 {len(chapters)} 个章节")

    # 获取章节内容
    if chapters:
        content = spider.get_chapter_content(chapters[0]['url'])
        print(f"内容长度: {len(content)} 字符")
```

## 主要类和方法

- `NovelSpider`: 主爬虫类
  - `search_novels(keyword, search_type)`: 搜索小说
  - `get_novel_chapters(novel_url)`: 获取小说章节列表
  - `get_chapter_content(chapter_url)`: 获取章节内容
  - `get_novel_content_by_search(keyword, search_type)`: 一键搜索并获取小说内容
  - `save_novel_to_file(novel_data, filename)`: 保存小说到文件

## 注意事项

1. 请合理使用，避免请求过于频繁
2. 请遵守网站的robots.txt协议和相关法律法规
3. 本工具仅供学习交流使用，请勿用于商业用途
4. 网站内容版权归原作者所有

## 工作流程

1. 搜索阶段：访问 `https://www.alicesw.com/search.html?q={keyword}&f={type}`
2. 详情页：获取小说章节列表
3. 内容页：提取 `<div class="read-content j_readContent user_ad_content">` 中的内容