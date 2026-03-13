// background.js

// 监听消息
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.action === 'downloadNovels') {
        downloadNovels(request.novels).then(success => {
            sendResponse({success: success});
        });
        return true; // 异步响应
    }
});

// 下载小说
async function downloadNovels(novels) {
    for (const novel of novels) {
        try {
            // 根据不同的网站使用不同的爬取逻辑
            if (novel.source === 'alicesw') {
                await downloadAliceNovel(novel);
            }
        } catch (error) {
            console.error('下载小说失败:', error);
            return false;
        }
    }
    return true;
}

// 下载爱丽丝书屋的小说
async function downloadAliceNovel(novel) {
    return new Promise(async (resolve, reject) => {
        try {
            // 爬取小说内容
            const novelContent = await crawlNovelContent(novel.url);
            
            // 创建文件内容
            let content = `小说标题：${novel.title}\n`;
            content += `作者：${novel.author}\n`;
            content += `网址：${novel.url}\n`;
            content += '='.repeat(50) + '\n\n';
            
            for (const chapter of novelContent.chapters) {
                content += `章节：${chapter.title}\n`;
                content += '-'.repeat(30) + '\n';
                content += chapter.content + '\n\n';
            }
            
            // 清理文件名
            const cleanTitle = novel.title.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_');
            const filename = `${cleanTitle}.txt`;
            
            // 使用data URL下载
            const encoder = new TextEncoder();
            const data = encoder.encode(content);
            const blob = new Blob([data], {type: 'text/plain;charset=utf-8'});
            
            // 使用FileReader读取blob并创建data URL
            const reader = new FileReader();
            reader.onload = function(e) {
                const dataUrl = e.target.result;
                
                chrome.downloads.download({
                    url: dataUrl,
                    filename: filename,
                    saveAs: false
                }, function(downloadId) {
                    if (downloadId) {
                        resolve(true);
                    } else {
                        reject(new Error('下载失败'));
                    }
                });
            };
            reader.onerror = function() {
                reject(new Error('创建文件失败'));
            };
            reader.readAsDataURL(blob);
        } catch (error) {
            reject(error);
        }
    });
}

// 爬取小说内容
async function crawlNovelContent(url) {
    return new Promise((resolve, reject) => {
        // 从小说URL提取ID，构建章节列表页面URL
        let chaptersUrl = url;
        const novelIdMatch = url.match(/\/novel\/(\d+)\.html/);
        if (novelIdMatch) {
            const novelId = novelIdMatch[1];
            chaptersUrl = `https://www.alicesw.com/other/chapters/id/${novelId}.html`;
        }
        
        console.log(`章节列表页面: ${chaptersUrl}`);
        
        fetch(chaptersUrl)
            .then(response => response.text())
            .then(html => {
                // 提取章节列表 - 模拟 .mulu_list li a 选择器
                const chapters = [];
                
                // 优先从章节列表页面提取，使用更精确的正则表达式匹配 .mulu_list li a
                const muluListRegex = /<div\s+class="mulu_list"[^>]*>([\s\S]*?)<\/div>/;
                const muluMatch = html.match(muluListRegex);
                
                if (muluMatch) {
                    const muluContent = muluMatch[1];
                    const chapterRegex = /<li[^>]*><a[^>]+href="([^"]+)"[^>]*>([^<]+)<\/a><\/li>/g;
                    let match;
                    
                    while ((match = chapterRegex.exec(muluContent)) !== null) {
                        const chapterUrl = match[1];
                        const chapterTitle = match[2].trim();
                        
                        if (chapterTitle) {
                            chapters.push({
                                title: chapterTitle,
                                url: chapterUrl.startsWith('http') ? chapterUrl : new URL(chapterUrl, chaptersUrl).href
                            });
                        }
                    }
                }
                
                // 如果章节列表页面没有找到，尝试从原始页面获取
                if (chapters.length === 0) {
                    console.log('从原始页面提取章节');
                    // 尝试多种方式提取章节
                    const chapterRegexes = [
                        /<li[^>]*><a[^>]+href="([^"]+)"[^>]*>([^<]+)<\/a><\/li>/g,
                        /<a[^>]+href="([^"\s]+\/book\/[^"\s]+)"[^>]*>([^<]+)<\/a>/g
                    ];
                    
                    chapterRegexes.forEach(regex => {
                        let match;
                        while ((match = regex.exec(html)) !== null) {
                            const chapterUrl = match[1];
                            const chapterTitle = match[2].trim();
                            
                            if (chapterUrl.includes('/book/') && chapterTitle && !chapters.some(c => c.url === chapterUrl)) {
                                chapters.push({
                                    title: chapterTitle,
                                    url: chapterUrl.startsWith('http') ? chapterUrl : new URL(chapterUrl, chaptersUrl).href
                                });
                            }
                        }
                    });
                }
                
                console.log(`找到 ${chapters.length} 个章节`);
                
                // 为每个章节获取内容
                const chapterPromises = chapters.map(chapter => {
                    return fetch(chapter.url)
                        .then(response => response.text())
                        .then(chapterHtml => {
                            // 提取章节内容，参考Python实现的逻辑
                            let content = '';
                            
                            // 尝试匹配 read-content class
                            let contentMatch = chapterHtml.match(/<div\s+class="read-content"[^>]*>([\s\S]*?)<\/div>/);
                            
                            // 如果没有找到，尝试匹配包含 read 和 content 的 class
                            if (!contentMatch) {
                                contentMatch = chapterHtml.match(/<div\s+class="[^"]*read[^"]*content[^"]*"[^>]*>([\s\S]*?)<\/div>/);
                            }
                            
                            // 如果还是没有找到，尝试匹配其他可能的内容容器
                            if (!contentMatch) {
                                contentMatch = chapterHtml.match(/<div\s+class="[^"]*content[^"]*"[^>]*>([\s\S]*?)<\/div>/);
                            }
                            
                            if (contentMatch && contentMatch[1]) {
                                // 移除不需要的元素（script、style、广告等）
                                let contentHtml = contentMatch[1];
                                // 移除 script 标签
                                contentHtml = contentHtml.replace(/<script[^>]*>[\s\S]*?<\/script>/g, '');
                                // 移除 style 标签
                                contentHtml = contentHtml.replace(/<style[^>]*>[\s\S]*?<\/style>/g, '');
                                // 移除广告标签
                                contentHtml = contentHtml.replace(/<div[^>]*class="[^"]*ad[^"]*"[^>]*>[\s\S]*?<\/div>/g, '');
                                contentHtml = contentHtml.replace(/<p[^>]*class="[^"]*ad[^"]*"[^>]*>[\s\S]*?<\/p>/g, '');
                                contentHtml = contentHtml.replace(/<span[^>]*class="[^"]*ad[^"]*"[^>]*>[\s\S]*?<\/span>/g, '');
                                // 移除所有HTML标签
                                content = contentHtml.replace(/<[^>]+>/g, '').trim();
                                // 替换多个换行符为单个换行符
                                content = content.replace(/\n+/g, '\n');
                                // 移除首尾空白
                                content = content.trim();
                            } else {
                                // 尝试直接从页面中提取文本内容
                                const textMatch = chapterHtml.match(/<body[^>]*>([\s\S]*?)<\/body>/);
                                if (textMatch) {
                                    let textContent = textMatch[1];
                                    // 移除HTML标签
                                    textContent = textContent.replace(/<[^>]+>/g, '').trim();
                                    // 替换多个换行符为单个换行符
                                    textContent = textContent.replace(/\n+/g, '\n');
                                    // 提取合理长度的内容
                                    content = textContent.substring(0, 10000) || '未能找到章节内容';
                                } else {
                                    content = '未能找到章节内容';
                                }
                            }
                            
                            return {
                                title: chapter.title,
                                content: content
                            };
                        })
                        .catch(error => {
                            console.error(`获取章节内容失败: ${chapter.title}`, error);
                            return {
                                title: chapter.title,
                                content: '获取内容失败'
                            };
                        });
                });
                
                Promise.all(chapterPromises)
                    .then(chaptersWithContent => {
                        resolve({chapters: chaptersWithContent});
                    })
                    .catch(error => reject(error));
            })
            .catch(error => reject(error));
    });
}