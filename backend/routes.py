"""HTTP routes for the Anything API."""

import time

from flask import Blueprint, current_app, jsonify, request, send_from_directory

from .config import MAX_DETAIL_BATCH, MAX_QUERY_LENGTH
from .upstream import is_allowed_detail_url

api = Blueprint("api", __name__)


def _service():
    return current_app.extensions["movie_service"]


@api.get("/api/search")
def search():
    keyword = request.args.get("q", "").strip()
    if not keyword:
        return jsonify({"error": "请提供搜索关键词"}), 400
    if len(keyword) > MAX_QUERY_LENGTH:
        return jsonify({"error": f"搜索关键词不能超过 {MAX_QUERY_LENGTH} 个字符"}), 400

    started = time.perf_counter()
    try:
        results, cached = _service().search(keyword)
    except Exception as exc:  # noqa: BLE001
        current_app.logger.warning("upstream search failed: %s", exc)
        return jsonify({"error": "上游搜索服务暂时不可用"}), 502
    return jsonify({
        "success": True,
        "keyword": keyword,
        "count": len(results),
        "results": results,
        "cached": cached,
        "elapsedMs": round((time.perf_counter() - started) * 1000),
        "note": "已先展示搜索结果，海报与资源信息将按当前页并行加载。",
    })


@api.post("/api/details")
def details():
    payload = request.get_json(silent=True) or {}
    detail_urls = payload.get("urls")
    if not isinstance(detail_urls, list) or not detail_urls:
        return jsonify({"error": "请提供详情页 URL 列表"}), 400
    if len(detail_urls) > MAX_DETAIL_BATCH:
        return jsonify({"error": f"每次最多加载 {MAX_DETAIL_BATCH} 个详情"}), 400
    if any(not isinstance(url, str) or not is_allowed_detail_url(url) for url in detail_urls):
        return jsonify({"error": "包含不受支持的详情页 URL"}), 400

    unique_urls = list(dict.fromkeys(detail_urls))
    started = time.perf_counter()
    unique_results, cache_hits = _service().load_details(unique_urls)
    details_by_url = {item["detailUrl"]: item for item in unique_results}
    return jsonify({
        "success": True,
        "results": [details_by_url[url] for url in detail_urls],
        "cacheHits": cache_hits,
        "elapsedMs": round((time.perf_counter() - started) * 1000),
    })


@api.get("/healthz")
def health():
    """Liveness endpoint used by the container platform and deployments."""
    return jsonify({"status": "ok"})


@api.get("/")
def index():
    """Serve the browser application from the same origin as the API."""
    return send_from_directory(current_app.config["FRONTEND_DIR"], "index.html")
