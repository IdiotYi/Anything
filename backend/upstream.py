"""HTTP client for the configured movie index upstream."""

import urllib.parse
from urllib.parse import urlparse

import requests

from .config import ALLOWED_DETAIL_HOSTS, REQUEST_TIMEOUT, UPSTREAM_BASE_URL
from .parsers import parse_movie_page, parse_search_page

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"


def decode_upstream_html(response):
    try:
        return response.content.decode("gbk")
    except UnicodeDecodeError:
        response.encoding = response.apparent_encoding or "utf-8"
        return response.text


def is_allowed_detail_url(url):
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


class UpstreamClient:
    def __init__(self, session=None):
        self.session = session or requests.Session()
        self._owns_session = session is None

    def close(self):
        if self._owns_session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def search(self, keyword):
        search_url = self._create_search_url(keyword)
        if not search_url:
            return []
        response = self.session.get(
            search_url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return parse_search_page(decode_upstream_html(response), search_url)

    def fetch_detail(self, detail_url):
        if not is_allowed_detail_url(detail_url):
            raise ValueError("unsupported detail URL")
        response = self.session.get(
            detail_url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return parse_movie_page(decode_upstream_html(response), detail_url)

    def _create_search_url(self, keyword):
        keyword_bytes = keyword.encode("gb2312", errors="ignore")
        payload = {
            "tempid": "1",
            "tbname": "article",
            "keyboard": keyword_bytes,
            "show": "title,smalltext",
            "Submit": urllib.parse.quote("搜索".encode("gb2312")),
        }
        headers = {
            "User-Agent": USER_AGENT,
            "Referer": UPSTREAM_BASE_URL,
            "Origin": UPSTREAM_BASE_URL,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        response = self.session.post(
            f"{UPSTREAM_BASE_URL}/e/search/index.php",
            data=payload,
            headers=headers,
            allow_redirects=False,
            timeout=REQUEST_TIMEOUT,
        )
        location = response.headers.get("Location")
        if not location or "searchid=" not in location:
            return None
        parsed = urllib.parse.urlparse(location)
        search_ids = urllib.parse.parse_qs(parsed.query).get("searchid")
        search_id = search_ids[0] if search_ids and search_ids[0] else location.split("searchid=")[-1].split("&")[0]
        return f"{UPSTREAM_BASE_URL}/e/search/result/?searchid={search_id}" if search_id else None
