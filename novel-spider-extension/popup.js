// popup.js

let novels = [];

// 爬取小说
function crawlNovels() {
    document.getElementById('status').textContent = '正在爬取...';
    document.getElementById('novelList').innerHTML = '<div class="loading">正在爬取页面内容...</div>';
    document.getElementById('downloadBtn').disabled = true;
    
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        chrome.scripting.executeScript({
            target: {tabId: tabs[0].id},
            function: function() {
                const novels = [];
                
                // 爬取爱丽丝书屋的小说
                if (window.location.hostname === 'www.alicesw.com') {
                    // 从小说详情页爬取
                    if (window.location.pathname.includes('/novel/')) {
                        const title = document.querySelector('h1, .novel_title')?.textContent?.trim() || '未知标题';
                        const author = document.querySelector('a[href*="/search\?q=.*&f=author"]')?.textContent?.trim() || '未知作者';
                        
                        novels.push({
                            title: title,
                            author: author,
                            url: window.location.href,
                            source: 'alicesw'
                        });
                    }
                    
                    // 从搜索结果页爬取
                    else if (window.location.pathname.includes('/search')) {
                        // 尝试多种选择器来匹配小说项
                        const novelItems = document.querySelectorAll('div[class*="list-group-item"], div[class*="novel-item"], .novel-list > div');
                        
                        if (novelItems.length === 0) {
                            // 尝试直接查找包含小说信息的元素
                            const allElements = document.querySelectorAll('div');
                            allElements.forEach(item => {
                                const titleElem = item.querySelector('a[href*="/novel/"]');
                                if (titleElem) {
                                    const title = titleElem.textContent.trim();
                                    const url = titleElem.href;
                                    
                                    // 查找作者信息
                                    let author = '未知作者';
                                    const authorElem = item.querySelector('a[href*="/search\?q="][href*="&f=author"]');
                                    if (authorElem) {
                                        author = authorElem.textContent.trim();
                                    } else {
                                        // 尝试其他方式查找作者
                                        const textContent = item.textContent;
                                        const authorMatch = textContent.match(/作者：([^\s]+)/);
                                        if (authorMatch) {
                                            author = authorMatch[1];
                                        }
                                    }
                                    
                                    novels.push({
                                        title: title,
                                        author: author,
                                        url: url,
                                        source: 'alicesw'
                                    });
                                }
                            });
                        } else {
                            novelItems.forEach(item => {
                                const titleElem = item.querySelector('h5 a, a[href*="/novel/"]');
                                const authorElem = item.querySelector('a[href*="/search\?q=.*&f=author"], a[href*="/search\?q="][href*="&f=author"]');
                                
                                if (titleElem) {
                                    const title = titleElem.textContent.trim();
                                    const url = titleElem.href;
                                    const author = authorElem?.textContent?.trim() || '未知作者';
                                    
                                    novels.push({
                                        title: title,
                                        author: author,
                                        url: url,
                                        source: 'alicesw'
                                    });
                                }
                            });
                        }
                    }
                }
                
                return novels;
            }
        }, function(results) {
            if (results && results[0]) {
                novels = results[0].result;
                displayNovels(novels);
                document.getElementById('status').textContent = `找到 ${novels.length} 本小说`;
                document.getElementById('downloadBtn').disabled = novels.length === 0;
            } else {
                document.getElementById('status').textContent = '未找到小说';
                document.getElementById('novelList').innerHTML = '<div class="loading">页面中未找到小说</div>';
            }
        });
    });
}

// 显示小说列表
function displayNovels(novelList) {
    const novelListElement = document.getElementById('novelList');
    if (novelList.length === 0) {
        novelListElement.innerHTML = '<div class="loading">未找到小说</div>';
        return;
    }
    
    novelListElement.innerHTML = novelList.map((novel, index) => `
        <div class="novel-item">
            <input type="checkbox" id="novel-${index}" value="${index}">
            <div>
                <div class="novel-title">${novel.title}</div>
                <div class="novel-author">作者: ${novel.author}</div>
            </div>
        </div>
    `).join('');
}

// 下载选中的小说
function downloadSelected() {
    const selectedCheckboxes = document.querySelectorAll('input[type="checkbox"]:checked');
    const selectedNovels = Array.from(selectedCheckboxes).map(checkbox => {
        const index = parseInt(checkbox.value);
        return novels[index];
    });
    
    if (selectedNovels.length === 0) {
        document.getElementById('status').textContent = '请选择要下载的小说';
        return;
    }
    
    document.getElementById('status').textContent = `正在下载 ${selectedNovels.length} 本小说...`;
    
    // 发送消息给后台脚本下载
    chrome.runtime.sendMessage({
        action: 'downloadNovels',
        novels: selectedNovels
    }, function(response) {
        if (response.success) {
            document.getElementById('status').textContent = '下载完成！';
        } else {
            document.getElementById('status').textContent = '下载失败';
        }
    });
}

// 绑定事件
document.getElementById('crawlBtn').addEventListener('click', crawlNovels);
document.getElementById('downloadBtn').addEventListener('click', downloadSelected);

// 初始化
window.onload = function() {
    // 自动爬取当前页面
    crawlNovels();
};