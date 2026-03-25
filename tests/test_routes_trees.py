"""Tests for tree management endpoints (/trees)."""

from unittest.mock import patch

from flask import jsonify

from tests.conftest import FAKE_PARTITION_KEY, FAKE_TREE_ID


class TestListTrees:
    def test_unauthenticated(self, client):
        resp = client.get("/trees")
        assert resp.status_code == 401

    def test_list_trees(self, client, mock_auth, auth_headers):
        def fake_handler(g):
            return jsonify({"trees": [], "count": 0}), 200

        with patch("app.list_user_trees", side_effect=fake_handler):
            resp = client.get("/trees", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["count"] == 0


class TestCreateTree:
    def test_unauthenticated(self, client):
        resp = client.post("/trees", json={"name": "Test"})
        assert resp.status_code == 401

    def test_create_tree(self, client, mock_auth, auth_headers):
        def fake_handler(g, data):
            return jsonify({
                "message": "Tree created",
                "tree_id": FAKE_TREE_ID,
                "partition_key": FAKE_PARTITION_KEY,
                "member": {"id": "m1", "name": "John"},
            }), 201

        with patch("app.create_tree", side_effect=fake_handler):
            resp = client.post(
                "/trees",
                headers=auth_headers,
                json={"name": "Test", "surname": "User", "gender": "male",
                       "born": "2000-01-01", "description": "test", "pic": "", "photos": ""},
            )
        assert resp.status_code == 201
        assert resp.get_json()["tree_id"] == FAKE_TREE_ID


class TestDeleteTree:
    def test_missing_partition(self, client, mock_auth, auth_headers):
        resp = client.delete("/trees", headers=auth_headers)
        assert resp.status_code == 400

    def test_owner_can_delete(self, client, mock_auth, partition_headers, mock_partition, mock_role_owner):
        def fake_handler(g):
            return jsonify({"message": "Tree deleted"}), 200

        with patch("app.delete_tree", side_effect=fake_handler):
            resp = client.delete("/trees", headers=partition_headers)
        assert resp.status_code == 200

    def test_viewer_cannot_delete(self, client, mock_auth, partition_headers, mock_partition, mock_role_viewer):
        resp = client.delete("/trees", headers=partition_headers)
        assert resp.status_code == 403
