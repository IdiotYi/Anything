import unittest
from backend.book_service import BookService


class FakeBookClient:
    search_calls = 0

    def search(self, keyword):
        type(self).search_calls += 1
        return [
            {
                "title": f"Book {i}",
                "coverUrl": f"https://example.com/cover{i}.jpg",
                "author": f"Author {i}",
                "format": "EPUB",
                "filesize": "1 MB",
                "language": "中文",
                "downloadUrl": f"https://zh.z-library.sk/dl/{i}",
                "detailUrl": f"https://zh.z-library.sk/book/{i}",
            }
            for i in range(10)
        ]


class BookServiceTests(unittest.TestCase):
    def setUp(self):
        FakeBookClient.search_calls = 0
        self.service = BookService(client_factory=FakeBookClient)

    def test_search_returns_all_results_and_caches(self):
        first, first_cached = self.service.search("测试")
        second, second_cached = self.service.search("  测试  ")
        self.assertEqual(len(first), 10)
        self.assertEqual(len(second), 10)
        self.assertFalse(first_cached)
        self.assertTrue(second_cached)
        self.assertEqual(FakeBookClient.search_calls, 1)


if __name__ == "__main__":
    unittest.main()