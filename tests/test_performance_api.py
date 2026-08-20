import time
import unittest
from unittest.mock import patch

from backend import app as app_module


class PerformanceApiTests(unittest.TestCase):
    def setUp(self):
        app_module._search_cache.clear()
        app_module._detail_cache.clear()
        self.client = app_module.app.test_client()

    def test_search_returns_lightweight_results_without_detail_fetches(self):
        movies = [
            {"title": "电影一", "url": "https://www.dygangs.me/ys/one.htm"},
            {"title": "电影二", "url": "https://www.dygangs.me/ys/two.htm"},
        ]
        with (
            patch.object(app_module, "search_dygang", return_value="https://www.dygangs.me/e/search/result/?searchid=1"),
            patch.object(app_module, "parse_search_results", return_value=movies),
            patch.object(app_module, "parse_movie_detail") as detail_parser,
        ):
            response = self.client.get("/api/search?q=复仇者联盟")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["count"], 2)
        self.assertFalse(payload["results"][0]["detailsLoaded"])
        detail_parser.assert_not_called()

    def test_search_cache_avoids_repeating_upstream_work(self):
        movies = [{"title": "电影", "url": "https://www.dygangs.me/ys/one.htm"}]
        with (
            patch.object(app_module, "search_dygang", return_value="https://www.dygangs.me/e/search/result/?searchid=1") as search_mock,
            patch.object(app_module, "parse_search_results", return_value=movies),
        ):
            first = self.client.get("/api/search?q=电影").get_json()
            second = self.client.get("/api/search?q=电影").get_json()

        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        search_mock.assert_called_once()

    def test_details_endpoint_fetches_visible_page_concurrently(self):
        urls = [f"https://www.dygangs.me/ys/{index}.htm" for index in range(6)]

        def parse_detail(url):
            time.sleep(0.05)
            return {"posterUrl": url + ".jpg", "downloadLinks": []}

        started = time.perf_counter()
        with patch.object(app_module, "parse_movie_detail", side_effect=parse_detail):
            response = self.client.post("/api/details", json={"urls": urls})
        elapsed = time.perf_counter() - started

        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 0.2)
        payload = response.get_json()
        self.assertEqual([item["detailUrl"] for item in payload["results"]], urls)
        self.assertTrue(all(item["detailsLoaded"] for item in payload["results"]))

    def test_details_rejects_large_or_untrusted_batches(self):
        too_many = [f"https://www.dygangs.me/ys/{index}.htm" for index in range(7)]
        self.assertEqual(self.client.post("/api/details", json={"urls": too_many}).status_code, 400)
        self.assertEqual(
            self.client.post("/api/details", json={"urls": ["https://127.0.0.1/private.htm"]}).status_code,
            400,
        )


if __name__ == "__main__":
    unittest.main()
