"""Tests for auth endpoints (/auth/me, /account)."""

from tests.conftest import FAKE_USER_INFO


class TestAuthMe:
    def test_no_token_returns_401(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_valid_token_returns_user(self, client, mock_auth, auth_headers):
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["user"]["user_id"] == FAKE_USER_INFO["user_id"]
        assert data["message"] == "Authentication successful"


class TestDeleteAccount:
    def test_no_token_returns_401(self, client):
        resp = client.delete("/account")
        assert resp.status_code == 401
