"""Application constants that are safe to keep in source control."""

UPSTREAM_BASE_URL = "https://www.dygangs.me"
ALLOWED_DETAIL_HOSTS = frozenset({"www.dygangs.me", "dygangs.me"})

SEARCH_CACHE_TTL_SECONDS = 5 * 60
DETAIL_CACHE_TTL_SECONDS = 30 * 60
DETAIL_ERROR_CACHE_TTL_SECONDS = 2 * 60
SEARCH_CACHE_MAX_ENTRIES = 128
DETAIL_CACHE_MAX_ENTRIES = 512

MAX_DETAIL_BATCH = 6
DETAIL_WORKERS = 6
MAX_QUERY_LENGTH = 80
REQUEST_TIMEOUT = (4, 10)

CORS_ORIGINS = (
    "http://127.0.0.1:8000",
    "http://localhost:8000",
)
