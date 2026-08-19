import unittest
from unittest.mock import patch

from backend.app import search_dygang


class SearchDygangTests(unittest.TestCase):
    def test_search_uses_active_domain_and_returns_result_url(self):
        class Response:
            def __init__(self, location):
                self.headers = {"Location": location}

        def post(url, **_kwargs):
            if url == "https://www.dygangs.me/e/search/index.php":
                return Response("result/?searchid=179847")
            return Response("https://www.dygang.tv/e/search/index.php")

        with patch("backend.app.requests.post", side_effect=post):
            result = search_dygang("复仇者联盟")

        self.assertEqual(
            result,
            "https://www.dygangs.me/e/search/result/?searchid=179847",
        )


if __name__ == "__main__":
    unittest.main()
