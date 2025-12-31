from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import urllib.parse

app = Flask(__name__)
CORS(app)

def search_movies(keyword):
    """使用帝国影视站点生成搜索结果链接"""
    search_url = search_dygang(keyword)

    if not search_url:
        return []

    title = f"在帝国影视搜索：{keyword}"

    result = {
        'title': title,
        'size': '',
        'year': '',
        'quality': '',
        'language': '',
        'detailUrl': search_url,
        'searchUrl': search_url,
        'magnetLink': None,
        'downloadLinks': [
            {
                'type': 'search',
                'url': search_url,
                'text': '打开搜索结果'
            }
        ],
        'seeders': '',
        'leechers': ''
    }

    return [result]


def search_dygang(keyword):
    """调用帝国影视的搜索接口并获取跳转URL"""
    base_url = "https://www.dygang.cc"

    try:
        try:
            keyword_bytes = keyword.encode('gb2312')
        except UnicodeEncodeError:
            keyword_bytes = keyword.encode('gb2312', errors='ignore')

        payload = {
            'tempid': '1',
            'tbname': 'article',
            'keyboard': keyword_bytes,
            'show': 'title,smalltext',
            'Submit': urllib.parse.quote('搜索'.encode('gb2312'))
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': base_url,
            'Origin': base_url,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.post(
            f"{base_url}/e/search/index.php",
            data=payload,
            headers=headers,
            allow_redirects=False,
            timeout=10
        )

        location = response.headers.get('Location')

        if not location or 'searchid=' not in location:
            return None

        parsed = urllib.parse.urlparse(location)
        query = urllib.parse.parse_qs(parsed.query)
        search_id_values = query.get('searchid')

        if search_id_values and search_id_values[0]:
            search_id = search_id_values[0]
        else:
            search_id = location.split('searchid=')[-1].split('&')[0]

        if not search_id:
            return None

        return f"{base_url}/e/search/result/?searchid={search_id}"

    except requests.RequestException as exc:
        print(f"搜索请求失败: {exc}")
        return None

@app.route('/api/search', methods=['GET'])
def search():
    """
    搜索API端点
    """
    keyword = request.args.get('q', '').strip()
    
    if not keyword:
        return jsonify({'error': '请提供搜索关键词'}), 400
    
    results = search_movies(keyword)
    
    return jsonify({
        'success': True,
        'keyword': keyword,
        'count': len(results),
        'results': results,
        'note': '结果链接由帝国影视站点提供，可能存在访问限制。'
    })

@app.route('/api/detail', methods=['GET'])
def get_detail():
    """
    获取详情页下载链接（演示版本）
    """
    url = request.args.get('url', '').strip()
    
    if not url:
        return jsonify({'error': '请提供详情页URL'}), 400
    
    # 返回演示数据
    links = [
        {
            'type': 'magnet',
            'url': 'magnet:?xt=urn:btih:' + '0' * 40,
            'text': '磁力链接（演示）'
        }
    ]
    
    return jsonify({
        'success': True,
        'downloadLinks': links
    })

@app.route('/')
def index():
    return """
    <h1>Anything API Server</h1>
    <p>电影种子搜索API服务</p>
    <h3>API端点：</h3>
    <ul>
        <li>GET /api/search?q=电影名 - 搜索电影</li>
        <li>GET /api/detail?url=详情页URL - 获取下载链接</li>
    </ul>
    <h3>示例搜索：</h3>
    <ul>
        <li><a href="/api/search?q=新闻女王">搜索：新闻女王</a></li>
        <li><a href="/api/search?q=繁花">搜索：繁花</a></li>
        <li><a href="/api/search?q=阿凡达">搜索：阿凡达</a></li>
        <li><a href="/api/search?q=流浪地球">搜索：流浪地球</a></li>
    </ul>
    <p><small>当前直接返回帝国影视搜索结果链接。</small></p>
    """

if __name__ == '__main__':
    print("=" * 60)
    print("Anything 电影搜索服务启动")
    print("=" * 60)
    print("服务地址: http://localhost:5000")
    print("前端页面: 请在浏览器中打开 frontend/index.html")
    print("\n当前使用帝国影视站点生成搜索链接")
    print("=" * 60)
    app.run(debug=True, port=5000)
