"""Application configuration loaded from safe defaults and environment values."""

import os


def _csv_env(name, default=()):
    value = os.getenv(name)
    if value is None:
        return tuple(default)
    return tuple(item.strip() for item in value.split(",") if item.strip())


UPSTREAM_BASE_URL = os.getenv("UPSTREAM_BASE_URL", "https://www.dygangs.me").rstrip("/")
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

# The production UI is same-origin and needs no CORS. Set this only when a
# separately hosted development frontend must call the API.
CORS_ORIGINS = _csv_env("CORS_ORIGINS")
