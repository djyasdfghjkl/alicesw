"""
爱丽丝书屋小说爬虫 - Web版
"""
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, send_from_directory
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import re
import os
import threading
from urllib.parse import urlparse
import json
from io import BytesIO
import zipfile

app = Flask(__name__)

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
                        'id': len(novels) + 1,
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


# 全局爬虫实例
spider = NovelSpider()


@app.route('/')
def index():
    return render_template('index.html')


# 静态文件路由
@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('.', 'manifest.json')


@app.route('/service-worker.js')
def serve_service_worker():
    return send_from_directory('.', 'service-worker.js')


@app.route('/icons/<path:filename>')
def serve_icon(filename):
    return send_from_directory('icons', filename)


@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    keyword = data.get('keyword', '')
    search_type = data.get('search_type', '_all')
    
    if not keyword:
        return jsonify({'error': '关键词不能为空'}), 400
    
    novels = spider.search_novels(keyword, search_type)
    return jsonify({'novels': novels})


@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    novel_ids = data.get('novel_ids', [])
    
    if not novel_ids:
        return jsonify({'error': '请选择要下载的小说'}), 400
    
    # 这里需要根据ID获取小说URL，实际情况可能需要调整
    # 暂时假设直接传递URL
    novel_urls = data.get('novel_urls', [])
    novel_titles = data.get('novel_titles', [])
    novel_authors = data.get('novel_authors', [])
    
    # 创建内存中的ZIP文件
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, url in enumerate(novel_urls):
            if i < len(novel_titles) and i < len(novel_authors):
                title = novel_titles[i]
                author = novel_authors[i]
                
                novel_data = spider.get_novel_content_by_url(url, title, author)
                
                if novel_data:
                    # 生成文件内容
                    content = f"小说标题: {novel_data['title']}\n"
                    content += f"作者: {novel_data['author']}\n"
                    content += f"网址: {novel_data['url']}\n"
                    content += "="*50 + "\n\n"
                    
                    for chapter in novel_data['chapters']:
                        content += f"章节: {chapter['title']}\n"
                        content += "-"*30 + "\n"
                        content += f"{chapter['content']}\n\n"
                    
                    # 添加到ZIP
                    clean_title = "".join(c for c in novel_data['title'] if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                    if not clean_title:
                        clean_title = "未知小说"
                    
                    filename = f"{clean_title}.txt"
                    zip_file.writestr(filename, content)
    
    zip_buffer.seek(0)
    
    # 返回ZIP文件
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='novels.zip'
    )


if __name__ == '__main__':
    # 创建templates目录
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    app.run(debug=True, host='0.0.0.0', port=5000)