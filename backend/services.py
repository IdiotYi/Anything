"""Business services for lightweight search and progressive detail loading."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from .cache import TTLCache
from .config import (
    DETAIL_CACHE_MAX_ENTRIES,
    DETAIL_CACHE_TTL_SECONDS,
    DETAIL_ERROR_CACHE_TTL_SECONDS,
    DETAIL_WORKERS,
    SEARCH_CACHE_MAX_ENTRIES,
    SEARCH_CACHE_TTL_SECONDS,
)
from .upstream import UpstreamClient, is_allowed_detail_url


class MovieService:
    def __init__(self, client_factory=UpstreamClient):
        self.client_factory = client_factory
        self.search_cache = TTLCache(SEARCH_CACHE_TTL_SECONDS, SEARCH_CACHE_MAX_ENTRIES)
        self.detail_cache = TTLCache(DETAIL_CACHE_TTL_SECONDS, DETAIL_CACHE_MAX_ENTRIES)

    def clear_caches(self):
        self.search_cache.clear()
        self.detail_cache.clear()

    def search(self, keyword):
        cache_key = " ".join(keyword.split()).casefold()
        cached = self.search_cache.get(cache_key)
        if cached is not None:
            return cached, True

        with self.client_factory() as client:
            movies = client.search(keyword)
        results = [
            {
                "title": movie.get("title", ""),
                "detailUrl": movie.get("url", ""),
                "posterUrl": "",
                "downloadLinks": [],
                "detailsLoaded": False,
            }
            for movie in movies
            if is_allowed_detail_url(movie.get("url", ""))
        ]
        self.search_cache.set(cache_key, results)
        return results, False

    def load_details(self, detail_urls):
        results = [None] * len(detail_urls)
        cache_hits = 0
        workers = min(DETAIL_WORKERS, len(detail_urls))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self._load_detail, url): index
                for index, url in enumerate(detail_urls)
            }
            for future in as_completed(futures):
                index = futures[future]
                detail, cached = future.result()
                results[index] = detail
                cache_hits += int(cached)
        return results, cache_hits

    def _load_detail(self, detail_url):
        cached = self.detail_cache.get(detail_url)
        if cached is not None:
            return cached, True
        try:
            with self.client_factory() as client:
                detail = client.fetch_detail(detail_url)
            value = {
                "detailUrl": detail_url,
                "posterUrl": detail["posterUrl"],
                "downloadLinks": detail["downloadLinks"],
                "detailsLoaded": True,
            }
            self.detail_cache.set(detail_url, value)
        except Exception as exc:  # noqa: BLE001
            print(f"解析详情页失败 {detail_url}: {exc}")
            value = {
                "detailUrl": detail_url,
                "posterUrl": "",
                "downloadLinks": [],
                "detailsLoaded": True,
                "detailError": True,
            }
            self.detail_cache.set(detail_url, value, DETAIL_ERROR_CACHE_TTL_SECONDS)
        return value, False
