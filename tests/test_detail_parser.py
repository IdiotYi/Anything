import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from getdetailedtorrent import parse_movie_detail  # noqa: E402


class MovieDetailParserTests(unittest.TestCase):
    def parse_html(self, html, detail_url="https://www.dygangs.me/ys/movie.htm"):
        response = Mock()
        response.content = html.encode("gbk")
        response.raise_for_status = Mock()

        with patch("getdetailedtorrent.requests.get", return_value=response):
            return parse_movie_detail(detail_url)

    def test_extracts_first_content_poster_and_magnet(self):
        detail = self.parse_html(
            """
            <img src='/images/logo.gif'>
            <img src='https://www.66tutup.com/2025/6973.jpg'>
            <a href='magnet:?xt=urn:btih:ABC&amp;dn=Avatar'>阿凡达：火与烬</a>
            """
        )

        self.assertEqual(
            detail["posterUrl"],
            "https://www.66tutup.com/2025/6973.jpg",
        )
        self.assertEqual(
            detail["downloadLinks"],
            [{
                "type": "magnet",
                "url": "magnet:?xt=urn:btih:ABC&dn=Avatar",
                "title": "阿凡达：火与烬",
            }],
        )

    def test_normalizes_relative_torrent_url(self):
        detail = self.parse_html(
            "<a href='../downloads/avatar.torrent'>下载种子</a>",
            "https://www.dygangs.me/ys/2026/movie.htm",
        )

        self.assertEqual(
            detail["downloadLinks"][0]["url"],
            "https://www.dygangs.me/ys/downloads/avatar.torrent",
        )
        self.assertEqual(detail["downloadLinks"][0]["type"], "torrent")

    def test_uses_data_src_when_present(self):
        detail = self.parse_html(
            "<img src='/placeholder.gif' data-src='//cdn.example.com/poster.webp'>"
        )

        self.assertEqual(detail["posterUrl"], "https://cdn.example.com/poster.webp")


if __name__ == "__main__":
    unittest.main()
