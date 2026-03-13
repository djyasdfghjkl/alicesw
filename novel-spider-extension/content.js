// content.js

function crawlPage() {
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
            const novelItems = document.querySelectorAll('.list-group-item');
            novelItems.forEach(item => {
                const titleElem = item.querySelector('h5 a');
                const authorElem = item.querySelector('a[href*="/search\?q=.*&f=author"]');
                
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
    
    // 可以添加其他网站的爬取逻辑
    // else if (window.location.hostname === '其他网站域名') {
    //     // 其他网站的爬取逻辑
    // }
    
    return novels;
}

// 暴露给外部调用
window.crawlPage = crawlPage;