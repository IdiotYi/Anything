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
        lower_href = href.lower()
        link_type = None
        if lower_href.startswith("magnet:"):
            # Keep custom protocol URLs verbatim. urljoin/urlparse can misread
            # brackets inside ED2K file names as an IPv6 host.
            absolute_url = href
            link_type = "magnet"
        elif lower_href.startswith("ed2k://"):
            absolute_url = href
            link_type = "ed2k"
        else:
            absolute_url = urljoin(self.detail_url, href)
            lower_url = absolute_url.lower()
            if urlparse(absolute_url).scheme in {"http", "https"} and ".torrent" in lower_url:
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
        default_titles = {
            "magnet": "磁力链接",
            "ed2k": "ED2K 链接",
            "torrent": "种子文件",
        }
        self._active_download["title"] = title or default_titles[self._active_download["type"]]
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
