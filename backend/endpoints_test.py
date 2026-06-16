import json
import unittest
import urllib.error
import urllib.request

# Regression tests for issue #4: "Extra long blooms?"
# The backend must reject bloom content exceeding 280 characters.
# Requires the stack to be running (docker compose up) with seed data loaded.

BASE_URL = "http://localhost:3000"
BLOOM_MAX_LENGTH = 280


def _post(path, body, headers=None):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        finally:
            e.close()


class TestBloomLengthValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        status, data = _post("/login", {"username": "sample", "password": "sosecret"})
        if status != 200:
            raise RuntimeError(f"Login failed ({status}): {data}")
        cls.auth = {"Authorization": f"Bearer {data['token']}"}

    def test_bloom_at_limit_is_accepted(self):
        status, data = _post(
            "/bloom", {"content": "a" * BLOOM_MAX_LENGTH}, self.auth
        )
        self.assertEqual(status, 200)
        self.assertTrue(data["success"])

    def test_bloom_one_over_limit_is_rejected(self):
        status, _data = _post(
            "/bloom", {"content": "a" * (BLOOM_MAX_LENGTH + 1)}, self.auth
        )
        self.assertEqual(status, 400)

    def test_bloom_over_limit_returns_error_message(self):
        status, data = _post(
            "/bloom", {"content": "a" * (BLOOM_MAX_LENGTH + 1)}, self.auth
        )
        self.assertEqual(status, 400)
        self.assertFalse(data["success"])
        self.assertIn("280", data["message"])


if __name__ == "__main__":
    unittest.main()
