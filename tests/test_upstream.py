import unittest

from backend.upstream import UpstreamClient


class Response:
    def __init__(self, location):
        self.headers = {"Location": location}


class Session:
    def post(self, url, **_kwargs):
        if url == "https://www.dygangs.me/e/search/index.php":
            return Response("result/?searchid=179847")
        return Response("")


class UpstreamClientTests(unittest.TestCase):
    def test_search_uses_active_domain_and_returns_result_url(self):
        client = UpstreamClient(session=Session())
        result = client._create_search_url("复仇者联盟")
        self.assertEqual(
            result,
            "https://www.dygangs.me/e/search/result/?searchid=179847",
        )


if __name__ == "__main__":
    unittest.main()
