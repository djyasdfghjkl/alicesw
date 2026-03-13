"""
爱丽丝书屋小说爬虫 - 批量下载版 v2.0
支持选择保存格式：单文件或每章一个文件
"""
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import re
import os
import sys
from urllib.parse import urlparse

# 获取程序所在目录
if getattr(sys, 'frozen', False):
    # 如果是打包后的 exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 如果是源代码运行
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


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
        """搜索小说"""
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
                    
                    author_elem = item.find('a', href=re.compile(r'/search\?q=.*&f=author'))
                    author = author_elem.get_text(strip=True) if author_elem else ""
                    
                    intro_elem = item.find('p', class_='content-txt')
                    intro = intro_elem.get_text(strip=True)[:100] if intro_elem else ""
                    
                    novels.append({
                        'title': title,
                        'url': url,
                        'author': author,
                        'intro': intro
                    })
            
            return novels
        except Exception as e:
            print(f"搜索小说时出错：{e}")
            return []

    def get_novel_chapters(self, novel_url):
        """获取小说的所有章节"""
        try:
            novel_id_match = re.search(r'/novel/(\d+)\.html', novel_url)
            if novel_id_match:
                novel_id = novel_id_match.group(1)
                chapters_url = f"{self.base_url}/other/chapters/id/{novel_id}.html"
            else:
                chapters_url = novel_url

            response = self.session.get(chapters_url)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            chapter_links = []
            chapter_elements = soup.select('.mulu_list li a')
            
            for elem in chapter_elements:
                title = elem.get_text(strip=True)
                url = urllib.parse.urljoin(self.base_url, elem.get('href'))
                chapter_links.append({
                    'title': title,
                    'url': url
                })
            
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
            print(f"获取小说章节时出错：{e}")
            return []

    def get_chapter_content(self, chapter_url):
        """获取章节内容"""
        try:
            response = self.session.get(chapter_url)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            content_div = soup.find('div', class_='read-content')
            if not content_div:
                content_div = soup.find('div', {'class': re.compile(r'.*read.*content.*')})
            
            if content_div:
                for unwanted in content_div(["script", "style", "div.ad", "p.ad", "span.ad"]):
                    unwanted.decompose()
                
                content = content_div.get_text(separator='\n', strip=True)
                return content
            else:
                return "未能找到章节内容"
        except Exception as e:
            print(f"获取章节内容时出错：{e}")
            return ""

    def get_novel_content_by_url(self, novel_url, novel_title=None, novel_author=None):
        """通过 URL 获取小说内容"""
        try:
            if not novel_title or not novel_author:
                response = self.session.get(novel_url)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                
                if not novel_title:
                    title_elem = soup.find('div', class_='novel_title')
                    novel_title = title_elem.get_text(strip=True) if title_elem else "未知标题"
                
                if not novel_author:
                    author_elem = soup.find('a', href=re.compile(r'/search.html\?q=.*&f=author'))
                    novel_author = author_elem.get_text(strip=True) if author_elem else "未知作者"
            
            chapters = self.get_novel_chapters(novel_url)
            print(f"共找到 {len(chapters)} 个章节")
            
            novel_content = {
                'title': novel_title,
                'author': novel_author,
                'url': novel_url,
                'chapters': []
            }
            
            for i, chapter in enumerate(chapters):
                print(f"正在获取章节：{chapter['title']} ({i+1}/{len(chapters)})")
                content = self.get_chapter_content(chapter['url'])
                novel_content['chapters'].append({
                    'title': chapter['title'],
                    'content': content
                })
                
                time.sleep(0.2)
            
            return novel_content
        except Exception as e:
            print(f"获取小说内容时出错：{e}")
            return {}

    def download_multiple_novels(self, novels_list, save_format="single"):
        """批量下载小说"""
        downloaded_novels = []
        
        # 使用绝对路径
        download_dir = os.path.join(BASE_DIR, "downloads")
        print(f"下载目录：{download_dir}")
        
        for i, novel in enumerate(novels_list):
            print(f"\n正在下载第 {i+1}/{len(novels_list)} 本小说：{novel['title']}")
            novel_data = self.get_novel_content_by_url(novel['url'], novel['title'], novel['author'])
            
            if novel_data and novel_data.get('chapters'):
                print(f"成功获取小说内容，共 {len(novel_data['chapters'])} 章")
                downloaded_novels.append(novel_data)
                self.save_novel_to_file(novel_data, download_dir, save_format)
                print(f"已下载：{novel_data['title']}")
            else:
                print(f"下载失败：{novel['title']} - 未获取到章节内容")
        
        print(f"\n本次共下载 {len(downloaded_novels)}/{len(novels_list)} 本小说")
        return downloaded_novels

    def save_novel_to_file(self, novel_data, download_dir="downloads", save_format="single"):
        """
        保存小说到文件
        :param novel_data: 小说数据
        :param download_dir: 下载目录
        :param save_format: 保存格式 ('single' 单文件，'chapter' 每章一个文件)
        """
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        
        # 清理文件名中的非法字符
        clean_title = "".join(c for c in novel_data['title'] if c.isalnum() or c in (' ', '-', '_', '.', '(', ')', '[', ']')).rstrip()
        # 进一步清理可能的非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            clean_title = clean_title.replace(char, '_')
        
        # 限制文件夹名长度（Windows最大255字符）
        if len(clean_title) > 100:
            clean_title = clean_title[:100]
        
        if not clean_title:
            clean_title = "未知小说"
        
        if save_format == "single":
            filename = os.path.join(download_dir, f"{clean_title}.txt")
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"小说标题：{novel_data['title']}\n")
                f.write(f"作者：{novel_data['author']}\n")
                f.write("="*50 + "\n\n")
                
                for chapter in novel_data['chapters']:
                    f.write(f"章节：{chapter['title']}\n")
                    f.write("-"*30 + "\n")
                    f.write(f"{chapter['content']}\n\n")
            
            print(f"小说已保存到：{filename}")
        
        elif save_format == "chapter":
            novel_folder = os.path.join(download_dir, clean_title)
            try:
                if not os.path.exists(novel_folder):
                    os.makedirs(novel_folder)
            except Exception as e:
                print(f"创建小说文件夹失败：{e}")
                # 使用备用名称 - 只保留基本标识符
                import hashlib
                hash_obj = hashlib.md5(novel_data['title'].encode('utf-8'))
                backup_title = f"小说_{hash_obj.hexdigest()[:8]}"
                novel_folder = os.path.join(download_dir, backup_title)
                if not os.path.exists(novel_folder):
                    os.makedirs(novel_folder)
                print(f"使用备用文件夹名：{novel_folder}")
            
            # 保存小说信息文件
            info_file = os.path.join(novel_folder, "小说信息.txt")
            try:
                with open(info_file, 'w', encoding='utf-8') as f:
                    f.write(f"小说标题：{novel_data['title']}\n")
                    f.write(f"作者：{novel_data['author']}\n")
                    f.write(f"章节数：{len(novel_data['chapters'])}\n")
            except Exception as e:
                print(f"保存小说信息时出错：{e}")
                return
            
            # 保存每一章
            for i, chapter in enumerate(novel_data['chapters'], 1):
                clean_chapter_title = "".join(c for c in chapter['title'] if c.isalnum() or c in (' ', '-', '_', '.', '(', ')', '[', ']')).rstrip()
                # 清理章节标题中的非法字符
                for char in illegal_chars:
                    clean_chapter_title = clean_chapter_title.replace(char, '_')
                
                # 限制章节标题长度
                if len(clean_chapter_title) > 50:
                    clean_chapter_title = clean_chapter_title[:50]
                
                if not clean_chapter_title:
                    clean_chapter_title = f"第{i}章"
                
                chapter_file = os.path.join(novel_folder, f"{i:03d}_{clean_chapter_title}.txt")
                
                try:
                    with open(chapter_file, 'w', encoding='utf-8') as f:
                        f.write(f"章节：{chapter['title']}\n")
                        f.write("-"*30 + "\n")
                        f.write(f"{chapter['content']}\n")
                except Exception as e:
                    print(f"保存章节 {i} 时出错：{e}")
                
                if (i + 1) % 10 == 0 or i == len(novel_data['chapters']):
                    print(f"已保存 {i}/{len(novel_data['chapters'])} 章")
            
            print(f"小说已保存到文件夹：{novel_folder}")


def main():
    print("爱丽丝书屋小说爬虫 - 批量下载版 v2.0")
    print("="*50)
    
    spider = NovelSpider()
    
    while True:
        print("\n请选择操作:")
        print("1. 搜索小说并选择下载")
        print("2. 退出程序")
        
        choice = input("\n请输入选项 (1-2): ").strip()
        
        if choice == '1':
            print("\n搜索类型:")
            print("1. 按标题搜索")
            print("2. 按作者搜索") 
            print("3. 按标签搜索")
            print("4. 模糊搜索")
            
            search_choice = input("\n请选择搜索类型 (1-4): ").strip()
            search_types = {'1': 'title', '2': 'author', '3': 'tag', '4': '_all'}
            search_type = search_types.get(search_choice, '_all')
            
            keyword = input("\n请输入搜索关键词: ").strip()
            
            if not keyword:
                print("关键词不能为空!")
                continue
            
            print("\n正在搜索...")
            novels = spider.search_novels(keyword, search_type)
            
            if not novels:
                print("未找到相关小说!")
                continue
            
            print(f"\n找到 {len(novels)} 本相关小说:")
            for i, novel in enumerate(novels, 1):
                print(f"{i}. {novel['title']} - 作者：{novel['author']}")
                print(f"   简介：{novel['intro'][:100]}{'...' if len(novel['intro']) > 100 else ''}")
                print()
            
            print("请选择下载方式:")
            print("1. 选择指定编号的小说下载")
            print("2. 下载前 N 本小说")
            print("3. 下载所有小说")
            
            download_choice = input("\n请选择下载方式 (1-3): ").strip()
            
            novels_to_download = []
            
            if download_choice == '1':
                while True:
                    print("\n请输入要下载的小说编号 (用逗号分隔，例如：1,3,5 或 1，3，5): ")
                    selected_nums = input().strip()
                    try:
                        nums = [int(n.strip()) - 1 for n in selected_nums.replace('，', ',').split(',') if n.strip()]
                        novels_to_download = [novels[i] for i in nums if 0 <= i < len(novels)]
                        if not novels_to_download:
                            print("没有有效的编号，请重新输入!")
                            continue
                        break
                    except ValueError:
                        print("输入格式错误，请重新输入!")
                        continue
            
            elif download_choice == '2':
                while True:
                    try:
                        n = int(input(f"\n请输入要下载前几本小说 (1-{len(novels)}): "))
                        if 1 <= n <= len(novels):
                            novels_to_download = novels[:n]
                            break
                        else:
                            print(f"请输入 1 到{len(novels)}之间的数字!")
                    except ValueError:
                        print("请输入有效数字，请重新输入!")
            
            elif download_choice == '3':
                novels_to_download = novels[:]
            
            else:
                print("无效选择!")
                continue
            
            if not novels_to_download:
                print("没有选择任何小说!")
                continue
            
            print(f"\n确认下载以下 {len(novels_to_download)} 本小说:")
            for novel in novels_to_download:
                print(f"- {novel['title']} - 作者：{novel['author']}")
            
            # 选择保存格式
            print("\n请选择保存格式:")
            print("1. 单文件模式（整本小说保存为一个 txt 文件）")
            print("2. 章节模式（每章保存为一个 txt 文件，放在文件夹中）")
            
            format_choice = input("\n请选择保存格式 (1-2): ").strip()
            save_format = "single" if format_choice == '1' else "chapter"
            
            print("\n开始下载...")
            spider.download_multiple_novels(novels_to_download, save_format)
            
            print(f"\n下载完成!")
            print(f"文件保存在：{os.path.join(BASE_DIR, 'downloads')} 目录下")
            
            continue_choice = input("\n是否继续使用？(y/n): ").strip().lower()
            if continue_choice != 'y':
                break
                
        elif choice == '2':
            print("\n感谢使用，再见！")
            break
        else:
            print("无效选项，请重新选择!")


if __name__ == "__main__":
    main()