import os
import sys
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

# 添加 scripts 目录到 Python 路径。
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from getdetailedtorrent import parse_movie_detail
from gettorrenturl import parse_search_results

app = Flask(__name__)
CORS(app)

BASE_URL = "https://www.dygangs.me"
ALLOWED_DETAIL_HOSTS = {"www.dygangs.me", "dygangs.me"}
SEARCH_CACHE_TTL = 5 * 60
DETAIL_CACHE_TTL = 30 * 60
DETAIL_ERROR_CACHE_TTL = 2 * 60
SEARCH_CACHE_MAX_ENTRIES = 128
DETAIL_CACHE_MAX_ENTRIES = 512
MAX_DETAIL_BATCH = 6
DETAIL_WORKERS = 6

_cache_lock = threading.Lock()
_search_cache = {}
_detail_cache = {}


def _cache_get(cache, key):
    """Return a non-expired cache value, or None."""
    now = time.monotonic()
    with _cache_lock:
        entry = cache.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if expires_at <= now:
            cache.pop(key, None)
            return None
        return value


def _cache_set(cache, key, value, ttl, max_entries):
    now = time.monotonic()
    with _cache_lock:
        expired = [cache_key for cache_key, (expires_at, _) in cache.items() if expires_at <= now]
        for cache_key in expired:
            cache.pop(cache_key, None)
        if key not in cache and len(cache) >= max_entries:
            oldest_key = min(cache, key=lambda cache_key: cache[cache_key][0])
            cache.pop(oldest_key, None)
        cache[key] = (now + ttl, value)


def _is_allowed_detail_url(url):
    """Only allow HTTPS detail pages on the configured upstream host."""
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme == "https"
            and parsed.hostname in ALLOWED_DETAIL_HOSTS
            and (parsed.port is None or parsed.port == 443)
            and parsed.path.lower().endswith(".htm")
        )
    except ValueError:
        return False


def search_dygang(keyword, session=None):
    """Call the upstream search endpoint and return its result-page URL."""
    client = session or requests

    try:
        try:
            keyword_bytes = keyword.encode("gb2312")
        except UnicodeEncodeError:
            keyword_bytes = keyword.encode("gb2312", errors="ignore")

        payload = {
            "tempid": "1",
            "tbname": "article",
            "keyboard": keyword_bytes,
            "show": "title,smalltext",
            "Submit": urllib.parse.quote("搜索".encode("gb2312")),
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Referer": BASE_URL,
            "Origin": BASE_URL,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        response = client.post(
            f"{BASE_URL}/e/search/index.php",
            data=payload,
            headers=headers,
            allow_redirects=False,
            timeout=(4, 10),
        )
        location = response.headers.get("Location")
        if not location or "searchid=" not in location:
            return None

        parsed = urllib.parse.urlparse(location)
        search_ids = urllib.parse.parse_qs(parsed.query).get("searchid")
        search_id = search_ids[0] if search_ids and search_ids[0] else location.split("searchid=")[-1].split("&")[0]
        return f"{BASE_URL}/e/search/result/?searchid={search_id}" if search_id else None
    except requests.RequestException as exc:
        print(f"搜索请求失败: {exc}")
        return None


def search_movies(keyword):
    """Return lightweight search results without waiting for every detail page."""
    cache_key = keyword.casefold()
    cached = _cache_get(_search_cache, cache_key)
    if cached is not None:
        return cached, True

    try:
        # Reusing the session saves a second TLS/proxy handshake for the result page.
        with requests.Session() as session:
            search_url = search_dygang(keyword, session=session)
            if not search_url:
                return [], False
            movies = parse_search_results(search_url, session=session)

        results = [
            {
                "title": movie.get("title", ""),
                "detailUrl": movie.get("url", ""),
                "posterUrl": "",
                "downloadLinks": [],
                "detailsLoaded": False,
            }
            for movie in movies
            if _is_allowed_detail_url(movie.get("url", ""))
        ]
        _cache_set(_search_cache, cache_key, results, SEARCH_CACHE_TTL, SEARCH_CACHE_MAX_ENTRIES)
        return results, False
    except Exception as exc:  # noqa: BLE001
        print(f"搜索电影失败: {exc}")
        return [], False


def _load_movie_detail(detail_url):
    cached = _cache_get(_detail_cache, detail_url)
    if cached is not None:
        return cached, True

    try:
        detail = parse_movie_detail(detail_url)
        value = {
            "detailUrl": detail_url,
            "posterUrl": detail["posterUrl"],
            "downloadLinks": detail["downloadLinks"],
            "detailsLoaded": True,
        }
        _cache_set(_detail_cache, detail_url, value, DETAIL_CACHE_TTL, DETAIL_CACHE_MAX_ENTRIES)
        return value, False
    except Exception as exc:  # noqa: BLE001
        print(f"解析详情页失败 {detail_url}: {exc}")
        value = {
            "detailUrl": detail_url,
            "posterUrl": "",
            "downloadLinks": [],
            "detailsLoaded": True,
            "detailError": True,
        }
        # A short negative cache prevents a broken upstream page from delaying every revisit.
        _cache_set(_detail_cache, detail_url, value, DETAIL_ERROR_CACHE_TTL, DETAIL_CACHE_MAX_ENTRIES)
        return value, False


def load_details(detail_urls):
    """Fetch one visible page concurrently while preserving request order."""
    results = [None] * len(detail_urls)
    cache_hits = 0
    with ThreadPoolExecutor(max_workers=min(DETAIL_WORKERS, len(detail_urls))) as executor:
        futures = {
            executor.submit(_load_movie_detail, url): index
            for index, url in enumerate(detail_urls)
        }
        for future in as_completed(futures):
            index = futures[future]
            detail, cached = future.result()
            results[index] = detail
            cache_hits += int(cached)
    return results, cache_hits


@app.get("/api/search")
def search():
    keyword = request.args.get("q", "").strip()
    if not keyword:
        return jsonify({"error": "请提供搜索关键词"}), 400
    if len(keyword) > 80:
        return jsonify({"error": "搜索关键词不能超过 80 个字符"}), 400

    started = time.perf_counter()
    results, cached = search_movies(keyword)
    return jsonify({
        "success": True,
        "keyword": keyword,
        "count": len(results),
        "results": results,
        "cached": cached,
        "elapsedMs": round((time.perf_counter() - started) * 1000),
        "note": "已先展示搜索结果，海报与资源信息将按当前页并行加载。",
    })


@app.post("/api/details")
def details():
    payload = request.get_json(silent=True) or {}
    detail_urls = payload.get("urls")
    if not isinstance(detail_urls, list) or not detail_urls:
        return jsonify({"error": "请提供详情页 URL 列表"}), 400
    if len(detail_urls) > MAX_DETAIL_BATCH:
        return jsonify({"error": f"每次最多加载 {MAX_DETAIL_BATCH} 个详情"}), 400
    if any(not isinstance(url, str) or not _is_allowed_detail_url(url) for url in detail_urls):
        return jsonify({"error": "包含不受支持的详情页 URL"}), 400

    # Deduplicate network work, then restore the caller's order.
    unique_urls = list(dict.fromkeys(detail_urls))
    started = time.perf_counter()
    unique_results, cache_hits = load_details(unique_urls)
    details_by_url = {item["detailUrl"]: item for item in unique_results}
    ordered_results = [details_by_url[url] for url in detail_urls]
    return jsonify({
        "success": True,
        "results": ordered_results,
        "cacheHits": cache_hits,
        "elapsedMs": round((time.perf_counter() - started) * 1000),
    })


@app.get("/")
def index():
    return """
    <h1>Anything API Server</h1>
    <p>电影搜索 API 服务</p>
    <ul>
        <li>GET /api/search?q=电影名 - 快速返回轻量搜索结果</li>
        <li>POST /api/details - 并行加载当前页海报与下载链接</li>
    </ul>
    """


if __name__ == "__main__":
    print("=" * 60)
    print("Anything 电影搜索服务启动")
    print("服务地址: http://localhost:5000")
    print("前端页面: http://127.0.0.1:8000")
    print("=" * 60)
    app.run(debug=True, port=5000, threaded=True)
