"""Tests for the health-check endpoint (GET /).

The endpoint is unauthenticated, so the response body is deliberately minimal:
it must not disclose the exception, the exception type, or the Gremlin/Neptune
connection settings. The assertions below lock that in.
"""

from unittest.mock import patch


class TestHealthCheck:
    def test_healthy(self, client):
        """GET / returns 200 when Gremlin is reachable."""
        with patch("app.g") as mock_g:
            mock_g.V.return_value.limit.return_value.toList.return_value = []
            resp = client.get("/")

        assert resp.status_code == 200
        assert resp.get_json() == {"status": "healthy"}

    def test_unhealthy(self, client):
        """GET / returns 503 when Gremlin raises."""
        with patch("app.g") as mock_g:
            mock_g.V.return_value.limit.return_value.toList.side_effect = Exception(
                "conn refused"
            )
            resp = client.get("/")

        assert resp.status_code == 503
        assert resp.get_json() == {"status": "unhealthy"}

    def test_unhealthy_response_leaks_no_infrastructure_detail(self, client):
        """The public error path must not echo the endpoint or the exception."""
        with patch("app.g") as mock_g:
            mock_g.V.return_value.limit.return_value.toList.side_effect = Exception(
                "could not connect to neptune-cluster.eu-central-1.neptune.amazonaws.com"
            )
            resp = client.get("/")

        body = resp.get_data(as_text=True)
        assert "neptune" not in body.lower()
        assert "conn" not in body.lower()
        for leaked in ("gremlin_endpoint", "gremlin_port", "debug", "error_type"):
            assert leaked not in body.lower()
