import unittest
from backend.book_upstream import parse_zlib_html, build_search_url


SAMPLE_HTML = """
<html>
<body>
<z-bookcard extension="epub" filesize="3.10 MB" language="中文" download="/dl/m5ZK6VEbw3" href="/book/P0vp6rmnRr.html">
    <div slot="title">明朝那些事儿</div>
    <div slot="author">当年明月</div>
    <img class="image" src="https://covers.cdn-zlib.sk/1.jpg" />
</z-bookcard>
<z-bookcard extension="pdf" filesize="15.2 MB" language="English" download="/dl/abc123" href="/book/def456.html">
    <div class="title">Test English Book</div>
    <div class="author">John Doe</div>
    <img data-src="/covers/2.jpg" />
</z-bookcard>
</body>
</html>
"""


class BookParserTests(unittest.TestCase):
    def test_build_search_url(self):
        url = build_search_url("明朝那些事儿")
        self.assertIn("https://zh.z-library.sk/s/", url)
        self.assertTrue(url.endswith("?"))

    def test_parse_zlib_html(self):
        books = parse_zlib_html(SAMPLE_HTML)
        self.assertEqual(len(books), 2)

        book1 = books[0]
        self.assertEqual(book1["title"], "明朝那些事儿")
        self.assertEqual(book1["author"], "当年明月")
        self.assertEqual(book1["format"], "EPUB")
        self.assertEqual(book1["filesize"], "3.10 MB")
        self.assertEqual(book1["language"], "中文")
        self.assertEqual(book1["downloadUrl"], "https://zh.z-library.sk/dl/m5ZK6VEbw3")
        self.assertEqual(book1["coverUrl"], "https://covers.cdn-zlib.sk/1.jpg")

        book2 = books[1]
        self.assertEqual(book2["title"], "Test English Book")
        self.assertEqual(book2["author"], "John Doe")
        self.assertEqual(book2["format"], "PDF")
        self.assertEqual(book2["filesize"], "15.2 MB")
        self.assertEqual(book2["language"], "English")
        self.assertEqual(book2["downloadUrl"], "https://zh.z-library.sk/dl/abc123")
        self.assertEqual(book2["coverUrl"], "https://zh.z-library.sk/covers/2.jpg")


if __name__ == "__main__":
    unittest.main()
