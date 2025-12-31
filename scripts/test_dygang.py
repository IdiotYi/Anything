import requests
import urllib.parse

def search_dygang(keyword: str) -> str:
    """复现后端跳转逻辑，方便单独调试"""
    keyword_gb2312 = keyword.encode("gb2312")

    url = "https://www.dygang.cc/e/search/index.php"

    data = {
        "tempid": "1",
        "tbname": "article",
        "keyboard": keyword_gb2312,
        "show": "title,smalltext",
        "Submit": urllib.parse.quote("搜索".encode("gb2312"))
    }

    response = requests.post(url, data=data, allow_redirects=False, timeout=10)

    location = response.headers.get("Location")
    if not location or "searchid=" not in location:
        return "请求失败，未触发跳转"

    parsed = urllib.parse.urlparse(location)
    query = urllib.parse.parse_qs(parsed.query)
    search_ids = query.get("searchid")

    if search_ids and search_ids[0]:
        search_id = search_ids[0]
    else:
        search_id = location.split("searchid=")[-1].split("&")[0]

    return f"https://www.dygang.cc/e/search/result/?searchid={search_id}"

if __name__ == "__main__":
    keyword = input("请输入电影名：")
    result = search_dygang(keyword)
    print("搜索结果URL：", result)
