"""Tests for relationship endpoints (/child, /parent, /spouse)."""

from unittest.mock import patch

from flask import jsonify

MEMBER_PAYLOAD = {
    "name": "Jane",
    "surname": "Doe",
    "gender": "female",
    "born": "1990-01-01",
    "description": "Test",
    "pic": "",
    "photos": "",
}


class TestCreateChild:
    def test_unauthenticated(self, client):
        resp = client.post("/child", json={**MEMBER_PAYLOAD, "parent_id": "p1"})
        assert resp.status_code == 401

    def test_no_lock_returns_409(self, client, mock_auth, partition_headers, mock_partition, mock_role_editor, mock_editor_lock_none):
        resp = client.post("/child", headers=partition_headers, json={**MEMBER_PAYLOAD, "parent_id": "p1"})
        assert resp.status_code == 409

    def test_create_child_with_lock(self, client, mock_auth, partition_headers, mock_partition, mock_role_editor, mock_editor_lock_held):
        def fake_handler(g, data):
            return jsonify({"id": "c1", "name": "Jane"}), 201

        with patch("app.create_child", side_effect=fake_handler):
            resp = client.post("/child", headers=partition_headers, json={**MEMBER_PAYLOAD, "parent_id": "p1"})
        assert resp.status_code == 201


class TestCreateParent:
    def test_create_parent_with_lock(self, client, mock_auth, partition_headers, mock_partition, mock_role_editor, mock_editor_lock_held):
        def fake_handler(g, data):
            return jsonify({"id": "p1", "name": "Jane"}), 201

        with patch("app.create_parent", side_effect=fake_handler):
            resp = client.post("/parent", headers=partition_headers, json={**MEMBER_PAYLOAD, "child_id": "c1"})
        assert resp.status_code == 201


class TestCreateSpouse:
    def test_create_spouse_with_lock(self, client, mock_auth, partition_headers, mock_partition, mock_role_editor, mock_editor_lock_held):
        def fake_handler(g, data):
            return jsonify({"id": "s1", "name": "Jane"}), 201

        with patch("app.create_spouse", side_effect=fake_handler):
            resp = client.post(
                "/spouse",
                headers=partition_headers,
                json={**MEMBER_PAYLOAD, "spouse_id": "s0", "married": "2020-06-15", "divorced": None},
            )
        assert resp.status_code == 201


class TestUpdateSpouseRelation:
    def test_update_spouse_relation_with_lock(self, client, mock_auth, partition_headers, mock_partition, mock_role_editor, mock_editor_lock_held):
        def fake_handler(g, data):
            return jsonify({"message": "Updated"}), 200

        with patch("app.update_spouse_relation", side_effect=fake_handler):
            resp = client.put(
                "/spouse",
                headers=partition_headers,
                json={"husband_id": "h1", "wife_id": "w1", "married": "2020-06-15", "divorced": "2023-01-01"},
            )
        assert resp.status_code == 200
