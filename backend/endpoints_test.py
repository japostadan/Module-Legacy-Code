import json
import unittest
import urllib.error
import urllib.request

# Integration tests for backend endpoints.
# Requires the stack to be running (docker compose up) with seed data loaded.

BASE_URL = "http://localhost:3000"
BLOOM_MAX_LENGTH = 280


def _request(method, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else b""
    req_headers = {**(headers or {})}
    if body is not None:
        req_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers=req_headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            body = e.read()
            try:
                return e.code, json.loads(body)
            except json.JSONDecodeError:
                return e.code, {"_raw": body.decode(errors="replace")}
        finally:
            e.close()


def _post(path, body=None, headers=None):
    return _request("POST", path, body, headers)


def _get(path, headers=None):
    return _request("GET", path, headers=headers)


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


class TestUnfollow(unittest.TestCase):
    # Uses sample (follows TechInfluencer/Swiz/AS from seed).
    # Tests follow/unfollow OtherUser who sample does not follow by default.

    @classmethod
    def setUpClass(cls):
        status, data = _post("/login", {"username": "sample", "password": "sosecret"})
        if status != 200:
            raise RuntimeError(f"Login failed ({status}): {data}")
        cls.auth = {"Authorization": f"Bearer {data['token']}"}
        # Ensure we start in a known state: not following OtherUser.
        _post("/unfollow/OtherUser", headers=cls.auth)

    def test_unfollow_returns_success(self):
        _post("/follow", {"follow_username": "OtherUser"}, self.auth)
        status, data = _post("/unfollow/OtherUser", headers=self.auth)
        self.assertEqual(status, 200)
        self.assertTrue(data["success"])

    def test_unfollow_removes_following_relationship(self):
        _post("/follow", {"follow_username": "OtherUser"}, self.auth)
        _post("/unfollow/OtherUser", headers=self.auth)
        _, profile = _get("/profile/OtherUser", self.auth)
        self.assertFalse(profile["is_following"])

    def test_unfollow_nonexistent_user_returns_404(self):
        status, _data = _post("/unfollow/nobody_exists_xyz", headers=self.auth)
        self.assertEqual(status, 404)

    def test_unfollow_is_idempotent(self):
        # Unfollowing someone you don't follow should not error.
        _post("/unfollow/OtherUser", headers=self.auth)
        status, data = _post("/unfollow/OtherUser", headers=self.auth)
        self.assertEqual(status, 200)
        self.assertTrue(data["success"])


class TestRebloom(unittest.TestCase):
    # sample reblooms a bloom originally posted by TechInfluencer (from seed).
    # JustSomeGuy is used as the original poster for controlled tests.

    @classmethod
    def setUpClass(cls):
        status, data = _post("/login", {"username": "sample", "password": "sosecret"})
        if status != 200:
            raise RuntimeError(f"Login failed ({status}): {data}")
        cls.sample_auth = {"Authorization": f"Bearer {data['token']}"}

        status, data = _post("/login", {"username": "JustSomeGuy", "password": "mysterious"})
        if status != 200:
            raise RuntimeError(f"Login failed ({status}): {data}")
        cls.jsg_auth = {"Authorization": f"Bearer {data['token']}"}

        # JustSomeGuy posts a bloom we can rebloom.
        status, data = _post("/bloom", {"content": "Rebloom me!"}, cls.jsg_auth)
        if status != 200:
            raise RuntimeError(f"Could not post bloom ({status}): {data}")
        blooms_resp = _get("/blooms/JustSomeGuy")
        cls.original_bloom_id = blooms_resp[1][0]["id"]

    def test_rebloom_returns_success(self):
        status, data = _post(f"/rebloom/{self.original_bloom_id}", headers=self.sample_auth)
        self.assertEqual(status, 200)
        self.assertTrue(data["success"])

    def test_rebloom_appears_in_rebloomer_profile(self):
        _post(f"/rebloom/{self.original_bloom_id}", headers=self.sample_auth)
        _, profile = _get("/profile/sample", self.sample_auth)
        rebloom_ids = {b["rebloom_of"] for b in profile["recent_blooms"] if b.get("rebloom_of")}
        self.assertIn(self.original_bloom_id, rebloom_ids)

    def test_rebloom_carries_original_sender(self):
        _post(f"/rebloom/{self.original_bloom_id}", headers=self.sample_auth)
        _, profile = _get("/profile/sample", self.sample_auth)
        reblooms = [b for b in profile["recent_blooms"] if b.get("rebloom_of") == self.original_bloom_id]
        self.assertTrue(any(rb["original_sender"] == "JustSomeGuy" for rb in reblooms))

    def test_rebloom_of_rebloom_is_rejected(self):
        _post(f"/rebloom/{self.original_bloom_id}", headers=self.sample_auth)
        _, profile = _get("/profile/sample", self.sample_auth)
        rebloom = next(b for b in profile["recent_blooms"] if b.get("rebloom_of") == self.original_bloom_id)
        status, _ = _post(f"/rebloom/{rebloom['id']}", headers=self.sample_auth)
        self.assertEqual(status, 400)

    def test_rebloom_count_on_original(self):
        _post(f"/rebloom/{self.original_bloom_id}", headers=self.sample_auth)
        _, bloom = _get(f"/bloom/{self.original_bloom_id}")
        self.assertGreaterEqual(bloom["rebloom_count"], 1)

    def test_rebloom_nonexistent_bloom_returns_404(self):
        status, _ = _post("/rebloom/999999999999", headers=self.sample_auth)
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
