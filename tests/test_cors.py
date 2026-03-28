import unittest

from app import create_app


class CorsConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_v2_preflight_returns_cors_headers(self):
        response = self.client.open(
            "/v2/orders",
            method="OPTIONS",
            headers={
                "Origin": "http://localhost:4200",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type,x-requested-with",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "http://localhost:4200")
        self.assertIn("POST", response.headers.get("Access-Control-Allow-Methods", ""))
        allow_headers = response.headers.get("Access-Control-Allow-Headers", "").lower()
        self.assertIn("authorization", allow_headers)
        self.assertIn("content-type", allow_headers)
        self.assertIn("x-requested-with", allow_headers)

    def test_auth_preflight_returns_cors_headers(self):
        response = self.client.open(
            "/auth/login",
            method="OPTIONS",
            headers={
                "Origin": "http://localhost:4200",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "http://localhost:4200")
        self.assertIn("POST", response.headers.get("Access-Control-Allow-Methods", ""))


if __name__ == "__main__":
    unittest.main()
