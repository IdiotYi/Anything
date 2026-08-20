import time
import unittest

from backend.services import MovieService


class FakeClient:
    search_calls = 0
    detail_calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def search(self, _keyword):
        type(self).search_calls += 1
        return [{"title": "电影", "url": "https://www.dygangs.me/ys/movie.htm"}]

    def fetch_detail(self, url):
        type(self).detail_calls += 1
        time.sleep(0.01)
        return {"posterUrl": url + ".jpg", "downloadLinks": []}


class MovieServiceTests(unittest.TestCase):
    def setUp(self):
        FakeClient.search_calls = 0
        FakeClient.detail_calls = 0
        self.service = MovieService(client_factory=FakeClient)

    def test_search_cache_avoids_repeated_upstream_calls(self):
        first, first_cached = self.service.search("电影")
        second, second_cached = self.service.search("  电影  ")
        self.assertEqual(first, second)
        self.assertFalse(first_cached)
        self.assertTrue(second_cached)
        self.assertEqual(FakeClient.search_calls, 1)

    def test_detail_loading_preserves_order_and_caches_results(self):
        urls = [
            "https://www.dygangs.me/ys/one.htm",
            "https://www.dygangs.me/ys/two.htm",
        ]
        first, first_hits = self.service.load_details(urls)
        second, second_hits = self.service.load_details(urls)
        self.assertEqual([item["detailUrl"] for item in first], urls)
        self.assertEqual(first_hits, 0)
        self.assertEqual(second_hits, 2)
        self.assertEqual(FakeClient.detail_calls, 2)


if __name__ == "__main__":
    unittest.main()
