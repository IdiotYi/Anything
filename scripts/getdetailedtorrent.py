"""Utility to extract magnet torrent links from a dygang movie detail page."""

import html as html_module
import re
from typing import Dict, List

import requests


def _fetch_html(detail_url: str) -> str:
    """Download the detail page and return decoded HTML."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    resp = requests.get(detail_url, headers=headers, timeout=10)
    resp.raise_for_status()

    try:
        return resp.content.decode("gbk")
    except UnicodeDecodeError:
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text


def parse_magnet_links(detail_url: str) -> List[Dict[str, str]]:
    """Parse a dygang detail page and extract all magnet torrent links."""
    page_html = _fetch_html(detail_url)
    results: List[Dict[str, str]] = []

    # Pattern: <a ... href="magnet:...">text</a> - href can be any attribute position
    pattern = re.compile(r'<a\s+[^>]*href="(magnet:[^"]+)"[^>]*>([^<]+)</a>', re.IGNORECASE)

    for magnet, raw_title in pattern.findall(page_html):
        # Unescape HTML entities (&amp; -> &, etc.)
        title = html_module.unescape(raw_title).strip()
        magnet = html_module.unescape(magnet)
        results.append({"title": title, "magnet": magnet, "type": "magnet"})

    # If no magnet links found, try to find torrent file links
    if not results:
        # Pattern: <a ... href="...torrent">text</a> - matches .torrent files
        torrent_pattern = re.compile(r'<a\s+[^>]*href="([^"]*\.torrent)"[^>]*>([^<]*)</a>', re.IGNORECASE)
        
        for torrent_url, raw_title in torrent_pattern.findall(page_html):
            # Unescape HTML entities (&amp; -> &, etc.)
            title = html_module.unescape(raw_title).strip()
            torrent_url = html_module.unescape(torrent_url)
            results.append({"title": title, "torrent": torrent_url, "type": "torrent"})

    return results


def format_results(results: List[Dict[str, str]]) -> str:
    """Format parsed magnet links or torrent files for display."""
    output = []
    for item in results:
        if item.get("type") == "magnet":
            output.append(f"磁力：{item['title']} -- {item['magnet']}")
        elif item.get("type") == "torrent":
            output.append(f"种子：{item['title']} -- {item['torrent']}")
    return "\n".join(output)


if __name__ == "__main__":
    detail_url = input("Enter dygang movie detail URL: ").strip()
    if not detail_url:
        print("No URL provided")
    else:
        try:
            parsed = parse_magnet_links(detail_url)
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to parse: {exc}")
        else:
            if not parsed:
                print("No magnet links found")
            else:
                print(format_results(parsed))
