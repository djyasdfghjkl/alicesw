import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import re


class NovelSpider:
    def __init__(self):
        self.base_url = "https://www.alicesw.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': self.base_url,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def search_novels(self, keyword, search_type='_all'):
        """
        搜索小说
        :param keyword: 搜索关键词
        :param search_type: 搜索类型 ('title', 'author', 'tag', '_all')
        :return: 小说列表 [{'title': '', 'url': '', 'author': '', 'intro': ''}]
        """
        if search_type == 'tag':
            search_url = f"{self.base_url}/search.html?q={urllib.parse.quote(keyword)}&f=tag"
        elif search_type == 'author':
            search_url = f"{self.base_url}/search.html?q={urllib.parse.quote(keyword)}&f=author"
        else:
            search_url = f"{self.base_url}/search.html?q={urllib.parse.quote(keyword)}&f=_all"

        try:
            response = self.session.get(search_url)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            novels = []
            list_items = soup.find_all('div', class_='list-group-item')
            
            for item in list_items:
                title_elem = item.find('h5').find('a')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = urllib.parse.urljoin(self.base_url, title_elem.get('href'))
                    
                    # 提取作者
                    author_elem = item.find('a', href=re.compile(r'/search\?q=.*&f=author'))
                    author = author_elem.get_text(strip=True) if author_elem else ""
                    
                    # 提取简介
                    intro_elem = item.find('p', class_='content-txt')
                    intro = intro_elem.get_text(strip=True) if intro_elem else ""
                    
                    novels.append({
                        'title': title,
                        'url': url,
                        'author': author,
                        'intro': intro
                    })
            
            return novels
        except Exception as e:
            print(f"搜索小说时出错: {e}")
            return []

    def get_novel_chapters(self, novel_url):
        """
        获取小说的所有章节
        :param novel_url: 小说详情页URL
        :return: 章节列表 [{'title': '', 'url': ''}]
        """
        try:
            # 从novel_url提取小说ID
            novel_id_match = re.search(r'/novel/(\d+)\.html', novel_url)
            if novel_id_match:
                novel_id = novel_id_match.group(1)
                # 使用章节列表页面URL
                chapters_url = f"{self.base_url}/other/chapters/id/{novel_id}.html"
            else:
                # 如果无法提取ID，则使用原来的URL
                chapters_url = novel_url

            response = self.session.get(chapters_url)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            # 从章节列表页面获取所有章节 - 使用正确的选择器
            chapter_links = []
            chapter_elements = soup.select('.mulu_list li a')
            
            for elem in chapter_elements:
                title = elem.get_text(strip=True)
                url = urllib.parse.urljoin(self.base_url, elem.get('href'))
                chapter_links.append({
                    'title': title,
                    'url': url
                })
            
            # 如果在章节列表页面没有找到章节，尝试从原始小说页面获取
            if not chapter_links:
                response = self.session.get(novel_url)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                
                chapter_elements = soup.select('.mulu_list li a')
                for elem in chapter_elements:
                    title = elem.get_text(strip=True)
                    url = urllib.parse.urljoin(self.base_url, elem.get('href'))
                    chapter_links.append({
                        'title': title,
                        'url': url
                    })
            
            return chapter_links
        except Exception as e:
            print(f"获取小说章节时出错: {e}")
            return []

    def get_chapter_content(self, chapter_url):
        """
        获取章节内容
        :param chapter_url: 章节URL
        :return: 章节内容
        """
        try:
            response = self.session.get(chapter_url)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找内容区域
            content_div = soup.find('div', class_='read-content')
            if not content_div:
                # 尝试其他可能的选择器
                content_div = soup.find('div', {'class': re.compile(r'.*read.*content.*')})
            
            if content_div:
                # 清理内容，移除不需要的标签
                for unwanted in content_div(["script", "style", "div.ad", "p.ad", "span.ad"]):
                    unwanted.decompose()
                
                content = content_div.get_text(separator='\n', strip=True)
                return content
            else:
                return "未能找到章节内容"
        except Exception as e:
            print(f"获取章节内容时出错: {e}")
            return ""

    def get_novel_content_by_search(self, keyword, search_type='_all'):
        """
        通过搜索获取小说内容
        :param keyword: 搜索关键词
        :param search_type: 搜索类型
        :return: 包含小说信息和内容的字典
        """
        print(f"正在搜索关键词: {keyword}")
        novels = self.search_novels(keyword, search_type)
        
        if not novels:
            print("未找到相关小说")
            return {}
        
        # 取第一个结果
        novel = novels[0]
        print(f"找到小说: {novel['title']}, 作者: {novel['author']}")
        
        # 获取章节
        chapters = self.get_novel_chapters(novel['url'])
        print(f"共找到 {len(chapters)} 个章节")
        
        # 获取每章内容
        novel_content = {
            'title': novel['title'],
            'author': novel['author'],
            'intro': novel['intro'],
            'chapters': []
        }
        
        for i, chapter in enumerate(chapters):
            print(f"正在获取章节: {chapter['title']} ({i+1}/{len(chapters)})")
            content = self.get_chapter_content(chapter['url'])
            novel_content['chapters'].append({
                'title': chapter['title'],
                'content': content
            })
            
            # 添加延时避免请求过快
            time.sleep(1)
        
        return novel_content

    def save_novel_to_file(self, novel_data, filename=None):
        """
        保存小说到文件
        :param novel_data: 小说数据
        :param filename: 文件名
        """
        if not filename:
            filename = f"{novel_data['title']}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"小说标题: {novel_data['title']}\n")
            f.write(f"作者: {novel_data['author']}\n")
            f.write(f"简介: {novel_data['intro']}\n")
            f.write("="*50 + "\n\n")
            
            for chapter in novel_data['chapters']:
                f.write(f"章节: {chapter['title']}\n")
                f.write("-"*30 + "\n")
                f.write(f"{chapter['content']}\n\n")
        
        print(f"小说已保存到: {filename}")


def main():
    spider = NovelSpider()
    
    print("欢迎使用小说爬虫工具")
    print("1. 按标题搜索")
    print("2. 按作者搜索") 
    print("3. 按标签搜索")
    print("4. 模糊搜索")
    
    choice = input("请选择搜索类型 (1-4): ").strip()
    search_types = {'1': 'title', '2': 'author', '3': 'tag', '4': '_all'}
    search_type = search_types.get(choice, '_all')
    
    keyword = input("请输入搜索关键词: ").strip()
    
    if not keyword:
        print("关键词不能为空")
        return
    
    print("\n正在爬取小说内容...")
    novel_data = spider.get_novel_content_by_search(keyword, search_type)
    
    if novel_data:
        print(f"\n成功获取小说: {novel_data['title']}")
        print(f"章节数量: {len(novel_data['chapters'])}")
        
        save_choice = input("\n是否保存到文件? (y/n): ").strip().lower()
        if save_choice == 'y':
            filename = input("请输入文件名 (默认为小说标题.txt): ").strip()
            if not filename:
                filename = None
            spider.save_novel_to_file(novel_data, filename)

    else:
        print("未能获取到小说内容")


if __name__ == "__main__":
    main()