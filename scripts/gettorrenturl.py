"""Utility to extract movie names and detail links from a dygang search page."""

import re
from typing import List, Dict
from urllib.parse import urljoin

import requests


# Match result links in the search page table; href is relative and uses .htm pages.
RESULT_LINK_PATTERN = re.compile(
	r'href="(/[^\"]+\.htm)"[^>]*class="classlinkclass"[^>]*>([^<]+)'
)


def _fetch_html(search_url: str, session=None) -> str:
	"""Download the search result page and return decoded HTML."""
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
	}
	client = session or requests
	resp = client.get(search_url, headers=headers, timeout=(4, 10))
	resp.raise_for_status()

	# Site declares gb2312; gbk handles it and is forgiving on mixed pages.
	try:
		return resp.content.decode("gbk")
	except UnicodeDecodeError:
		resp.encoding = resp.apparent_encoding or "utf-8"
		return resp.text


def parse_search_results(search_url: str, session=None) -> List[Dict[str, str]]:
	"""Parse a dygang search result page and return movie titles with detail links."""
	html = _fetch_html(search_url, session=session)
	results: List[Dict[str, str]] = []

	for href, raw_title in RESULT_LINK_PATTERN.findall(html):
		title = raw_title.strip()
		full_url = urljoin(search_url, href)
		results.append({"title": title, "url": full_url})

	return results


def format_results(results: List[Dict[str, str]]) -> str:
	"""Format parsed results into numbered lines for display."""
	return "\n".join(
		f"{idx}. {item['title']} -- {item['url']}" for idx, item in enumerate(results, 1)
	)


if __name__ == "__main__":
	search_url = input("Enter dygang search result URL: ").strip()
	if not search_url:
		print("No URL provided")
	else:
		try:
			parsed = parse_search_results(search_url)
		except Exception as exc:  # noqa: BLE001
			print(f"Failed to parse: {exc}")
		else:
			if not parsed:
				print("No results found")
			else:
				print(format_results(parsed))
