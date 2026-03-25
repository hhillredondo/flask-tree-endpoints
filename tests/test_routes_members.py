"""Tests for member CRUD endpoints (/member, /members)."""

from unittest.mock import patch

from flask import jsonify


class TestGetMember:
    def test_unauthenticated(self, client):
        resp = client.get("/member?id=m1")
        assert resp.status_code == 401

    def test_get_member(self, client, mock_auth, partition_headers, mock_partition, mock_role_viewer, mock_editor_lock_none):
        def fake_handler(g, data):
            return jsonify({"id": "m1", "name": "Alice"}), 200

        with patch("app.get_member_query", side_effect=fake_handler):
            resp = client.get("/member?id=m1", headers=partition_headers)
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "Alice"


class TestGetAllMembers:
    def test_list_members(self, client, mock_auth, partition_headers, mock_partition, mock_role_viewer):
        def fake_handler(g):
            return jsonify([{"id": "m1"}, {"id": "m2"}]), 200

        with patch("app.get_all_members_query", side_effect=fake_handler):
            resp = client.get("/members", headers=partition_headers)
        assert resp.status_code == 200
        assert len(resp.get_json()) == 2


class TestUpdateMember:
    def test_no_lock_returns_409(self, client, mock_auth, partition_headers, mock_partition, mock_role_editor, mock_editor_lock_none):
        resp = client.put("/member", headers=partition_headers, json={"id": "m1", "name": "Updated"})
        assert resp.status_code == 409

    def test_update_with_lock(self, client, mock_auth, partition_headers, mock_partition, mock_role_editor, mock_editor_lock_held):
        def fake_handler(g, data):
            return jsonify({"id": "m1", "name": "Updated"}), 200

        with patch("app.update_member_query", side_effect=fake_handler):
            resp = client.put("/member", headers=partition_headers, json={"id": "m1", "name": "Updated"})
        assert resp.status_code == 200


class TestDeleteMember:
    def test_viewer_cannot_delete(self, client, mock_auth, partition_headers, mock_partition, mock_role_viewer, mock_editor_lock_none):
        resp = client.delete("/member", headers=partition_headers, json={"member_id": "m1"})
        assert resp.status_code == 403

    def test_editor_with_lock_can_delete(self, client, mock_auth, partition_headers, mock_partition, mock_role_editor, mock_editor_lock_held):
        def fake_handler(g, data):
            return jsonify({"message": "Deleted"}), 200

        with patch("app.delete_member_query", side_effect=fake_handler):
            resp = client.delete("/member", headers=partition_headers, json={"member_id": "m1"})
        assert resp.status_code == 200
