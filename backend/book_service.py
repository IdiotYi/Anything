"""Book search service with TTL caching."""

from .cache import TTLCache
from .config import SEARCH_CACHE_MAX_ENTRIES, SEARCH_CACHE_TTL_SECONDS
from .book_upstream import BookUpstreamClient


class BookService:
    def __init__(self, client_factory=BookUpstreamClient):
        self.client_factory = client_factory
        self.search_cache = TTLCache(SEARCH_CACHE_TTL_SECONDS, SEARCH_CACHE_MAX_ENTRIES)

    def clear_caches(self):
        self.search_cache.clear()

    def search(self, keyword: str):
        cache_key = " ".join(keyword.split()).casefold()
        cached = self.search_cache.get(cache_key)
        if cached is not None:
            return cached, True

        client = self.client_factory()
        books = client.search(keyword)
        results = books if books else []
        self.search_cache.set(cache_key, results)
        return results, False
