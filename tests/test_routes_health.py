"""Tests for the health-check endpoint (GET /)."""

from unittest.mock import patch


class TestHealthCheck:
    def test_healthy(self, client):
        """GET / returns 200 when Gremlin is reachable."""
        with patch("app.g") as mock_g:
            mock_g.V.return_value.limit.return_value.toList.return_value = []
            resp = client.get("/")

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert data["gremlin_connection"] == "connected"

    def test_unhealthy(self, client):
        """GET / returns 500 when Gremlin raises."""
        with patch("app.g") as mock_g:
            mock_g.V.return_value.limit.return_value.toList.side_effect = Exception("conn refused")
            resp = client.get("/")

        assert resp.status_code == 500
        data = resp.get_json()
        assert data["status"] == "unhealthy"
