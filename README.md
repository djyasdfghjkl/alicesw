# 爱丽丝书屋全站小说一键爬取器 🚀💦

**专为爱丽丝书屋 (alicesw.org / alicesw.com / alicesw.click 等域名) 量身定制的异步小说批量下载神器**

爱丽丝书屋——那个标签齐全、重口不阉割、绿帽NTR凌辱调教样样齐全的成人幻想小说天堂，现在你可以用Python几分钟就把整个书库扒到本地硬盘里，离线慢慢“研究”。

**核心亮点（为什么值得star）**

- 全异步 + 并发控制 → 爬几千章小说速度飞起，不卡不崩
- 智能正文提取 → 适配爱丽丝书屋最新页面结构（2026年3月验证通过）
- 支持登录态 → 带上cookie就能下需要权限的限制级内容
- 自动章节排序 + 文件名序号 → 书架整齐得像Kindle导入一样
- 防反爬友好 → 随机UA + 代理支持 + 重试机制 + 指数退避
- 标签/分类/排行一键爬 → 想只扒“绿帽”“媚黑”“时间停止”专区？一行命令搞定

**适用人群**

- 硬盘党：不想每次都开浏览器翻几十页点下一章
- 研究党：想批量分析爱丽丝书屋的“创作趋势”（笑）
- 离线党：机场/地铁/断网环境也要继续“学习”
- 开源贡献者：想帮这个项目适配更多成人小说站的欢迎pr

**快速使用**
dist\小说爬虫工具\_批量版.exe，直接下载使用即可

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
