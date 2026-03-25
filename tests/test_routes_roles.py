"""Tests for roles/ACL endpoints (/roles)."""


from tests.conftest import FAKE_TREE_ID


class TestListRoles:
    def test_unauthenticated(self, client):
        resp = client.get("/roles")
        assert resp.status_code == 401

    def test_missing_partition(self, client, mock_auth, auth_headers):
        resp = client.get("/roles", headers=auth_headers)
        assert resp.status_code == 400

    def test_owner_can_list(self, client, mock_auth, partition_headers, mock_partition, mock_role_owner, mock_acl_store, mock_cognito):
        mock_acl_store.list_roles.return_value = [
            {"treeId": FAKE_TREE_ID, "userId": "u1", "role": "editor"}
        ]
        resp = client.get("/roles", headers=partition_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 1

    def test_viewer_forbidden(self, client, mock_auth, partition_headers, mock_partition, mock_role_viewer):
        resp = client.get("/roles", headers=partition_headers)
        assert resp.status_code == 403


class TestAddRole:
    def test_owner_adds_editor(self, client, mock_auth, partition_headers, mock_partition, mock_role_owner, mock_acl_store, mock_cognito):
        mock_acl_store.get_role.return_value = None
        mock_acl_store.put_role.return_value = True
        resp = client.post("/roles", headers=partition_headers, json={"email": "new@example.com", "role": "editor"})
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "Role assigned"

    def test_invalid_role_rejected(self, client, mock_auth, partition_headers, mock_partition, mock_role_owner, mock_acl_store, mock_cognito):
        resp = client.post("/roles", headers=partition_headers, json={"email": "new@example.com", "role": "superadmin"})
        assert resp.status_code == 400


class TestRemoveRole:
    def test_owner_removes_editor(self, client, mock_auth, partition_headers, mock_partition, mock_role_owner, mock_acl_store, mock_cognito):
        mock_acl_store.get_role.return_value = "editor"
        mock_acl_store.delete_role.return_value = True
        resp = client.delete("/roles", headers=partition_headers, json={"email": "old@example.com"})
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "Role removed"

    def test_cannot_remove_owner(self, client, mock_auth, partition_headers, mock_partition, mock_role_owner, mock_acl_store, mock_cognito):
        mock_acl_store.get_role.return_value = "owner"
        resp = client.delete("/roles", headers=partition_headers, json={"user_id": "owner-user"})
        assert resp.status_code == 400
