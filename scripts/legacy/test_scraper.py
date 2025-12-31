import requests
from bs4 import BeautifulSoup
import re

BASE_URL = "https://www.dygang.cc"

def test_search():
    keyword = "新闻女王"
    search_url = f"{BASE_URL}/e/search/index.php"
    
    data = {
        'show': 'title,smalltext',
        'tempid': '1',
        'tbname': 'article',
        'keyboard': keyword,
        'Submit': '搜索'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': BASE_URL,
    }
    
    try:
        response = requests.post(search_url, data=data, headers=headers, allow_redirects=True, timeout=10)
        response.encoding = 'gbk'
        
        print(f"状态码: {response.status_code}")
        print(f"最终URL: {response.url}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        print(f"页面标题: {soup.title.string if soup.title else 'No title'}")
        
        with open('test_result.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("\nHTML已保存到 test_result.html")
        
        print("\n=== 尝试不同的选择器 ===")
        
        print("\n1. 所有包含 /i/ 的链接:")
        links = soup.find_all('a', href=re.compile(r'/i/\d+\.html'))
        print(f"找到 {len(links)} 个结果")
        for i, link in enumerate(links[:5]):
            print(f"  - {link.get_text(strip=True)[:50]} -> {link.get('href')}")
        
        print("\n2. 查找table标签:")
        tables = soup.find_all('table')
        print(f"找到 {len(tables)} 个table")
        
        print("\n3. 查找div.co_content8:")
        divs = soup.find_all('div', class_='co_content8')
        print(f"找到 {len(divs)} 个结果")
        
        print("\n4. 查找class包含'content'的div:")
        divs2 = soup.find_all('div', class_=re.compile('content'))
        print(f"找到 {len(divs2)} 个结果")
        for i, div in enumerate(divs2[:3]):
            print(f"  - class: {div.get('class')}")
        
        print("\n5. 分析前10个链接的父元素:")
        all_links = soup.find_all('a', href=True)[:10]
        for link in all_links:
            parent = link.parent
            print(f"  - 父元素: {parent.name}, class: {parent.get('class')}, 文本: {link.get_text(strip=True)[:30]}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_search()
