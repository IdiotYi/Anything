"""Pure HTML parsers for upstream search and movie detail pages."""

import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

RESULT_LINK_PATTERN = re.compile(
    r'href="(/[^\"]+\.htm)"[^>]*class="classlinkclass"[^>]*>([^<]+)'
)


def parse_search_page(page_html, search_url):
    results = []
    for href, raw_title in RESULT_LINK_PATTERN.findall(page_html):
        results.append({
            "title": raw_title.strip(),
            "url": urljoin(search_url, href),
        })
    return results


class MovieDetailParser(HTMLParser):
    def __init__(self, detail_url):
        super().__init__(convert_charrefs=True)
        self.detail_url = detail_url
        self.images = []
        self.download_links = []
        self._active_download = None
        self._active_text = []

    def handle_starttag(self, tag, attrs):
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

    def handle_data(self, data):
        if self._active_download is not None:
            self._active_text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() != "a" or self._active_download is None:
            return
        title = " ".join("".join(self._active_text).split())
        self._active_download["title"] = title or (
            "磁力链接" if self._active_download["type"] == "magnet" else "种子文件"
        )
        self.download_links.append(self._active_download)
        self._active_download = None
        self._active_text = []


def select_poster(images):
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


def parse_movie_page(page_html, detail_url):
    parser = MovieDetailParser(detail_url)
    parser.feed(page_html)
    return {
        "posterUrl": select_poster(parser.images),
        "downloadLinks": parser.download_links,
    }
