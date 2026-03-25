"""Tests for editor lock endpoints (/editor-lock)."""

import time
from unittest.mock import patch

from tests.conftest import FAKE_TREE_ID, FAKE_USER_ID


class TestGetLockStatus:
    def test_unauthenticated(self, client):
        resp = client.get("/editor-lock")
        assert resp.status_code == 401

    def test_missing_partition(self, client, mock_auth, auth_headers):
        resp = client.get("/editor-lock", headers=auth_headers)
        assert resp.status_code == 400

    def test_unlocked(self, client, mock_auth, partition_headers, mock_partition, mock_role_owner, mock_editor_lock_none):
        resp = client.get("/editor-lock", headers=partition_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["locked"] is False

    def test_locked(self, client, mock_auth, partition_headers, mock_partition, mock_role_owner, mock_editor_lock_held):
        resp = client.get("/editor-lock", headers=partition_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["locked"] is True


class TestAcquireLock:
    def test_acquire_success(self, client, mock_auth, partition_headers, mock_partition, mock_role_editor):
        lock = {
            "treeId": FAKE_TREE_ID,
            "lockOwner": FAKE_USER_ID,
            "acquiredAt": "now",
            "expiresAt": int(time.time()) + 300,
        }
        with patch("editor_lock.handlers.acquire_editor_lock", return_value=(True, lock)):
            resp = client.post("/editor-lock", headers=partition_headers)
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "Editor lock acquired"

    def test_acquire_conflict(self, client, mock_auth, partition_headers, mock_partition, mock_role_editor):
        existing_lock = {"treeId": FAKE_TREE_ID, "lockOwner": "other-user"}
        with patch("editor_lock.handlers.acquire_editor_lock", return_value=(False, existing_lock)):
            resp = client.post("/editor-lock", headers=partition_headers)
        assert resp.status_code == 409


class TestReleaseLock:
    def test_release_success(self, client, mock_auth, partition_headers, mock_partition, mock_role_editor):
        lock = {"treeId": FAKE_TREE_ID, "lockOwner": FAKE_USER_ID}
        with patch("editor_lock.handlers.get_editor_lock", return_value=lock), \
             patch("editor_lock.handlers.release_editor_lock", return_value=True):
            resp = client.delete("/editor-lock", headers=partition_headers)
        assert resp.status_code == 200

    def test_release_no_lock(self, client, mock_auth, partition_headers, mock_partition, mock_role_editor):
        with patch("editor_lock.handlers.get_editor_lock", return_value=None):
            resp = client.delete("/editor-lock", headers=partition_headers)
        assert resp.status_code == 404


class TestForceRelease:
    def test_owner_force_release(self, client, mock_auth, partition_headers, mock_partition, mock_role_owner):
        lock = {"treeId": FAKE_TREE_ID, "lockOwner": "other-user"}
        with patch("editor_lock.handlers.get_editor_lock", return_value=lock), \
             patch("editor_lock.handlers.force_release_editor_lock", return_value=True):
            resp = client.post("/editor-lock/force", headers=partition_headers)
        assert resp.status_code == 200

    def test_viewer_cannot_force_release(self, client, mock_auth, partition_headers, mock_partition, mock_role_viewer):
        resp = client.post("/editor-lock/force", headers=partition_headers)
        assert resp.status_code == 403
