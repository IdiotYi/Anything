import unittest

from backend.app import create_app


class FakeService:
    def __init__(self):
        self.search_calls = 0

    def search(self, keyword):
        self.search_calls += 1
        return [{
            "title": keyword,
            "detailUrl": "https://www.dygangs.me/ys/movie.htm",
            "posterUrl": "",
            "downloadLinks": [],
            "detailsLoaded": False,
        }], False

    def load_details(self, urls):
        return [{
            "detailUrl": url,
            "posterUrl": "https://cdn.example/poster.jpg",
            "downloadLinks": [],
            "detailsLoaded": True,
        } for url in urls], 0



class FakeBookService:
    def __init__(self):
        self.search_calls = 0

    def search(self, keyword):
        self.search_calls += 1
        return [{
            "title": keyword,
            "coverUrl": "https://example.com/cover.jpg",
            "author": "测试作者",
            "format": "EPUB",
            "filesize": "2.5 MB",
            "language": "中文",
            "downloadUrl": "https://zh.z-library.sk/dl/12345",
            "detailUrl": "https://zh.z-library.sk/book/12345",
        }], False

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.service = FakeService()
        self.client = create_app(self.service).test_client()

    def test_index_serves_frontend_from_api_origin(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<!DOCTYPE html>", response.data)
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        response.close()

    def test_static_assets_are_served(self):
        response = self.client.get("/assets/app.js")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"const API_BASE_URL = '/api'", response.data)
        self.assertIn(b"ftp: { protocols: ['ftp:']", response.data)
        self.assertIn(b"Show More", response.data)
        response.close()

    def test_health_check_is_dependency_free(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})
        self.assertEqual(self.service.search_calls, 0)

    def test_version_check_reports_development_by_default(self):
        response = self.client.get("/versionz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"revision": "development"})

    def test_search_returns_lightweight_results(self):
        response = self.client.get("/api/search?q=复仇者联盟")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["count"], 1)
        self.assertFalse(payload["results"][0]["detailsLoaded"])

    def test_details_preserves_duplicate_order(self):
        url = "https://www.dygangs.me/ys/movie.htm"
        response = self.client.post("/api/details", json={"urls": [url, url]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["detailUrl"] for item in response.get_json()["results"]], [url, url])

    def test_details_rejects_large_or_untrusted_batches(self):
        too_many = [f"https://www.dygangs.me/ys/{index}.htm" for index in range(7)]
        self.assertEqual(self.client.post("/api/details", json={"urls": too_many}).status_code, 400)
        self.assertEqual(
            self.client.post("/api/details", json={"urls": ["https://127.0.0.1/private.htm"]}).status_code,
            400,
        )



    def test_book_search_returns_results(self):
        book_service = FakeBookService()
        client = create_app(self.service, book_service=book_service).test_client()
        response = client.get("/api/books/search?q=明朝那些事儿")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["count"], 1)
        book = data["results"][0]
        self.assertEqual(book["title"], "明朝那些事儿")
        self.assertEqual(book["author"], "测试作者")
        self.assertEqual(book["format"], "EPUB")
        self.assertEqual(book["filesize"], "2.5 MB")
        self.assertEqual(book["language"], "中文")
        self.assertEqual(book["downloadUrl"], "https://zh.z-library.sk/dl/12345")
        self.assertEqual(book["coverUrl"], "https://example.com/cover.jpg")
        self.assertEqual(len(book["downloadLinks"]), 1)

if __name__ == "__main__":
    unittest.main()