"""Utilities for extracting poster and download links from movie detail pages."""

from html.parser import HTMLParser
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def _fetch_html(detail_url: str) -> str:
    """Download a detail page and return decoded HTML."""
    response = requests.get(
        detail_url,
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )
    response.raise_for_status()

    try:
        return response.content.decode("gbk")
    except UnicodeDecodeError:
        response.encoding = response.apparent_encoding or "utf-8"
        return response.text


class _DetailParser(HTMLParser):
    """Collect image candidates and supported download links."""

    def __init__(self, detail_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.detail_url = detail_url
        self.images: List[str] = []
        self.download_links: List[Dict[str, str]] = []
        self._active_download: Optional[Dict[str, str]] = None
        self._active_text: List[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = {key.lower(): value for key, value in attrs if value}

        if tag.lower() == "img":
            source = attributes.get("data-src") or attributes.get("src")
            if source:
                self.images.append(urljoin(self.detail_url, source.strip()))
            return

        if tag.lower() != "a":
            return

        href = attributes.get("href", "").strip()
        absolute_url = urljoin(self.detail_url, href)
        lower_url = absolute_url.lower()
        link_type = None

        if lower_url.startswith("magnet:"):
            link_type = "magnet"
        elif urlparse(absolute_url).scheme in {"http", "https"} and ".torrent" in lower_url:
            link_type = "torrent"

        if link_type:
            self._active_download = {"type": link_type, "url": absolute_url}
            self._active_text = []

    def handle_data(self, data: str) -> None:
        if self._active_download is not None:
            self._active_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._active_download is None:
            return

        title = " ".join("".join(self._active_text).split())
        self._active_download["title"] = title or (
            "磁力链接" if self._active_download["type"] == "magnet" else "种子文件"
        )
        self.download_links.append(self._active_download)
        self._active_download = None
        self._active_text = []


def _select_poster(images: List[str]) -> str:
    """Choose the first external content image, ignoring site chrome."""
    for image_url in images:
        parsed = urlparse(image_url)
        path = parsed.path.lower()
        if parsed.scheme not in {"http", "https"}:
            continue
        if path.endswith(("logo.gif", "logo.png", "logo.jpg")):
            continue
        if "/d/file/p/2011-12-11/" in path:
            continue
        return image_url
    return ""


def parse_movie_detail(detail_url: str) -> Dict[str, object]:
    """Parse one movie page into a poster URL and normalized download links."""
    parser = _DetailParser(detail_url)
    parser.feed(_fetch_html(detail_url))
    return {
        "posterUrl": _select_poster(parser.images),
        "downloadLinks": parser.download_links,
    }


def parse_magnet_links(detail_url: str) -> List[Dict[str, str]]:
    """Backward-compatible helper returning normalized download links."""
    return parse_movie_detail(detail_url)["downloadLinks"]


def format_results(results: List[Dict[str, str]]) -> str:
    """Format parsed download links for command-line display."""
    labels = {"magnet": "磁力", "torrent": "种子"}
    return "\n".join(
        f"{labels.get(item.get('type'), '链接')}：{item['title']} -- {item['url']}"
        for item in results
    )


if __name__ == "__main__":
    url = input("Enter dygang movie detail URL: ").strip()
    if not url:
        print("No URL provided")
    else:
        try:
            detail = parse_movie_detail(url)
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to parse: {exc}")
        else:
            print(f"Poster: {detail['posterUrl'] or 'not found'}")
            links = detail["downloadLinks"]
            print(format_results(links) if links else "No download links found")
