import unittest

from backend.parsers import parse_movie_page, parse_search_page


class ParserTests(unittest.TestCase):
    def test_extracts_search_results(self):
        html = '<a href="/ys/movie.htm" class="classlinkclass">电影标题</a>'
        self.assertEqual(
            parse_search_page(html, "https://www.dygangs.me/e/search/result/?searchid=1"),
            [{"title": "电影标题", "url": "https://www.dygangs.me/ys/movie.htm"}],
        )

    def test_extracts_first_content_poster_and_magnet(self):
        detail = parse_movie_page(
            """
            <img src='/images/logo.gif'>
            <img src='https://www.66tutup.com/2025/6973.jpg'>
            <a href='magnet:?xt=urn:btih:ABC&amp;dn=Avatar'>阿凡达：火与烬</a>
            """,
            "https://www.dygangs.me/ys/movie.htm",
        )
        self.assertEqual(detail["posterUrl"], "https://www.66tutup.com/2025/6973.jpg")
        self.assertEqual(detail["downloadLinks"][0]["type"], "magnet")
        self.assertEqual(detail["downloadLinks"][0]["url"], "magnet:?xt=urn:btih:ABC&dn=Avatar")

    def test_extracts_multiple_ed2k_links(self):
        first = "ed2k://|file|movie[www.66e.cc].mp4|2099577975|78FBDEFE0CFC5AEFDA6C22F8EE353A70|/"
        second = "ed2k://|file|movie[www.66e.cc].mkv|1665897903|696A30A01CD539908B321B8246381C62|/"
        detail = parse_movie_page(
            f"<a href='{first}'>斯隆女士.mp4</a><a href='{second}'>斯隆女士.mkv</a>",
            "https://www.dygangs.me/bd/20170313/36866.htm",
        )

        self.assertEqual(
            detail["downloadLinks"],
            [
                {"type": "ed2k", "url": first, "title": "斯隆女士.mp4"},
                {"type": "ed2k", "url": second, "title": "斯隆女士.mkv"},
            ],
        )

    def test_normalizes_relative_torrent_url(self):
        detail = parse_movie_page(
            "<a href='../downloads/avatar.torrent'>下载种子</a>",
            "https://www.dygangs.me/ys/2026/movie.htm",
        )
        self.assertEqual(
            detail["downloadLinks"][0]["url"],
            "https://www.dygangs.me/ys/downloads/avatar.torrent",
        )

    def test_uses_data_src_when_present(self):
        detail = parse_movie_page(
            "<img src='/placeholder.gif' data-src='//cdn.example.com/poster.webp'>",
            "https://www.dygangs.me/ys/movie.htm",
        )
        self.assertEqual(detail["posterUrl"], "https://cdn.example.com/poster.webp")


if __name__ == "__main__":
    unittest.main()
