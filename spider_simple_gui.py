"""
爱丽丝书屋小说爬虫 - 简化版GUI
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import re
import os
import threading
from urllib.parse import urlparse
import webbrowser


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
                    
                    # 提取作者
                    author_elem = item.find('a', href=re.compile(r'/search\?q=.*&f=author'))
                    author = author_elem.get_text(strip=True) if author_elem else ""
                    
                    # 提取简介
                    intro_elem = item.find('p', class_='content-txt')
                    intro = intro_elem.get_text(strip=True)[:100] if intro_elem else ""  # 只取前100个字符
                    
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
        """获取小说的所有章节"""
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
        """获取章节内容"""
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

    def get_novel_content_by_url(self, novel_url, novel_title=None, novel_author=None):
        """通过URL获取小说内容"""
        try:
            # 如果没有提供标题，从页面获取
            if not novel_title or not novel_author:
                response = self.session.get(novel_url)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 尝试获取标题和作者
                if not novel_title:
                    title_elem = soup.find('div', class_='novel_title')
                    novel_title = title_elem.get_text(strip=True) if title_elem else "未知标题"
                
                if not novel_author:
                    author_elem = soup.find('a', href=re.compile(r'/search.html\?q=.*&f=author'))
                    novel_author = author_elem.get_text(strip=True) if author_elem else "未知作者"
            
            # 获取章节
            chapters = self.get_novel_chapters(novel_url)
            
            # 获取每章内容
            novel_content = {
                'title': novel_title,
                'author': novel_author,
                'url': novel_url,
                'chapters': []
            }
            
            for i, chapter in enumerate(chapters):
                content = self.get_chapter_content(chapter['url'])
                novel_content['chapters'].append({
                    'title': chapter['title'],
                    'content': content
                })
                
                # 添加延时避免请求过快
                time.sleep(0.2)
            
            return novel_content
        except Exception as e:
            print(f"获取小说内容时出错: {e}")
            return {}


class NovelSpiderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("爱丽丝书屋小说爬虫 - 简化版")
        self.root.geometry("800x600")
        
        self.spider = NovelSpider()
        self.downloaded_files = []  # 记录下载的文件
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        # 搜索框架
        search_frame = ttk.Frame(self.root)
        search_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(search_frame, text="搜索关键词:").pack(side=tk.LEFT)
        
        self.keyword_entry = ttk.Entry(search_frame, width=30)
        self.keyword_entry.pack(side=tk.LEFT, padx=5)
        self.keyword_entry.bind('<Return>', lambda event: self.search_novels())
        
        ttk.Label(search_frame, text="搜索类型:").pack(side=tk.LEFT, padx=(20, 5))
        
        self.search_type_var = tk.StringVar(value="模糊搜索")
        search_type_combo = ttk.Combobox(
            search_frame, 
            textvariable=self.search_type_var,
            values=["标题", "作者", "标签", "模糊搜索"],
            state="readonly",
            width=10
        )
        search_type_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(search_frame, text="搜索", command=self.search_novels).pack(side=tk.LEFT, padx=5)
        
        # 结果框架
        result_frame = ttk.Frame(self.root)
        result_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # 创建树形视图显示搜索结果
        columns = ('序号', '标题', '作者', '简介')
        self.tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Button(button_frame, text="下载选中", command=self.download_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="下载全部", command=self.download_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="管理下载", command=self.manage_downloads).pack(side=tk.LEFT, padx=5)
        
        # 进度条
        self.progress = ttk.Progressbar(self.root, mode='determinate')
        self.progress.pack(pady=5, padx=10, fill=tk.X)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def search_novels(self):
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showwarning("警告", "请输入搜索关键词")
            return
        
        # 映射搜索类型
        type_map = {"标题": "title", "作者": "author", "标签": "tag", "模糊搜索": "_all"}
        search_type = type_map.get(self.search_type_var.get(), "_all")
        
        self.status_var.set("正在搜索...")
        self.root.update()
        
        try:
            # 清空现有结果
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            novels = self.spider.search_novels(keyword, search_type)
            
            for i, novel in enumerate(novels, 1):
                self.tree.insert('', 'end', values=(i, novel['title'], novel['author'], novel['intro']))
            
            self.status_var.set(f"搜索完成，找到 {len(novels)} 本小说")
        except Exception as e:
            messagebox.showerror("错误", f"搜索失败: {str(e)}")
            self.status_var.set("搜索失败")
    
    def download_selected(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要下载的小说")
            return
        
        novels_to_download = []
        for item in selected_items:
            values = self.tree.item(item, 'values')
            # 迋建一个模拟的novel对象，实际需要重新搜索获取URL
            keyword = self.keyword_entry.get().strip()
            type_map = {"标题": "title", "作者": "author", "标签": "tag", "模糊搜索": "_all"}
            search_type = type_map.get(self.search_type_var.get(), "_all")
            
            novels = self.spider.search_novels(keyword, search_type)
            # 根据序号找到对应的小说
            idx = int(values[0]) - 1
            if 0 <= idx < len(novels):
                novels_to_download.append(novels[idx])
        
        if novels_to_download:
            self.download_novels_thread(novels_to_download)
    
    def download_all(self):
        all_items = self.tree.get_children()
        if not all_items:
            messagebox.showwarning("警告", "没有可下载的小说")
            return
        
        novels_to_download = []
        keyword = self.keyword_entry.get().strip()
        type_map = {"标题": "title", "作者": "author", "标签": "tag", "模糊搜索": "_all"}
        search_type = type_map.get(self.search_type_var.get(), "_all")
        
        novels = self.spider.search_novels(keyword, search_type)
        
        novels_to_download = novels
        
        if novels_to_download:
            self.download_novels_thread(novels_to_download)
    
    def download_novels_thread(self, novels_list):
        thread = threading.Thread(target=self.download_novels, args=(novels_list,))
        thread.daemon = True
        thread.start()
    
    def download_novels(self, novels_list):
        try:
            total = len(novels_list)
            self.progress['maximum'] = total
            self.progress['value'] = 0
            
            for i, novel in enumerate(novels_list):
                self.status_var.set(f"正在下载第 {i+1}/{total} 本: {novel['title']}")
                self.root.update()
                
                novel_data = self.spider.get_novel_content_by_url(novel['url'], novel['title'], novel['author'])
                
                if novel_data:
                    # 获取系统下载目录
                    download_path = os.path.join(os.path.expanduser("~"), "Downloads")
                    if not os.path.exists(download_path):
                        download_path = os.path.join(os.path.expanduser("~"), "Download")
                        if not os.path.exists(download_path):
                            download_path = os.getcwd()  # 回退到当前目录
                    
                    # 保存文件
                    clean_title = "".join(c for c in novel_data['title'] if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                    if not clean_title:
                        clean_title = "未知小说"
                    
                    filename = os.path.join(download_path, f"{clean_title}.txt")
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"小说标题: {novel_data['title']}\n")
                        f.write(f"作者: {novel_data['author']}\n")
                        f.write(f"网址: {novel_data['url']}\n")
                        f.write("="*50 + "\n\n")
                        
                        for chapter in novel_data['chapters']:
                            f.write(f"章节: {chapter['title']}\n")
                            f.write("-"*30 + "\n")
                            f.write(f"{chapter['content']}\n\n")
                    
                    self.downloaded_files.append(filename)
                
                self.progress['value'] = i + 1
                self.root.update()
            
            self.status_var.set(f"下载完成! 共下载 {len(novels_list)} 本小说")
            messagebox.showinfo("完成", f"下载完成!\n共下载 {len(novels_list)} 本小说\n保存在系统下载目录")
            
        except Exception as e:
            messagebox.showerror("错误", f"下载过程中出错: {str(e)}")
        finally:
            self.progress['value'] = 0
    
    def manage_downloads(self):
        if not self.downloaded_files:
            messagebox.showinfo("提示", "暂无下载记录")
            return
        
        # 创建管理窗口
        manage_window = tk.Toplevel(self.root)
        manage_window.title("下载管理")
        manage_window.geometry("600x400")
        
        # 创建列表框显示下载文件
        listbox_frame = ttk.Frame(manage_window)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        listbox = tk.Listbox(listbox_frame)
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        for file in self.downloaded_files:
            listbox.insert(tk.END, os.path.basename(file))
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 功能按钮
        btn_frame = ttk.Frame(manage_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def open_file():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请选择要打开的文件")
                return
            idx = selection[0]
            filepath = self.downloaded_files[idx]
            os.startfile(filepath)
        
        def copy_path():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请选择要复制路径的文件")
                return
            idx = selection[0]
            filepath = self.downloaded_files[idx]
            self.root.clipboard_clear()
            self.root.clipboard_append(filepath)
            messagebox.showinfo("提示", "路径已复制到剪贴板")
        
        def online_view():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请选择要在线查看的文件")
                return
            idx = selection[0]
            filepath = self.downloaded_files[idx]
            # 在线查看功能 - 这里只是打开文件
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建文本查看窗口
            viewer = tk.Toplevel(self.root)
            viewer.title(f"在线查看 - {os.path.basename(filepath)}")
            viewer.geometry("700x500")
            
            text_frame = ttk.Frame(viewer)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD)
            scrollbar_v = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
            scrollbar_h = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=text_widget.xview)
            text_widget.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
            
            text_widget.insert(tk.END, content)
            text_widget.config(state=tk.DISABLED)  # 设置为只读
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
            scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(btn_frame, text="打开文件", command=open_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="复制路径", command=copy_path).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="在线查看", command=online_view).pack(side=tk.LEFT, padx=5)


def main():
    root = tk.Tk()
    app = NovelSpiderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()