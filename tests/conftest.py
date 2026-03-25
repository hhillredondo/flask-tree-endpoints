"""Shared pytest fixtures for Flask route integration tests.

All external services (Cognito, Neptune/Gremlin, DynamoDB, S3) are mocked so
that tests exercise HTTP routing, middleware ordering, and JSON responses
without network access.
"""

import time
from unittest.mock import MagicMock, patch

import pytest
from flask import g

from config.settings import TestingConfig

FAKE_USER_ID = "test-user-id-000"
FAKE_EMAIL = "test@example.com"
FAKE_TREE_ID = "test-tree-id-000"
FAKE_PARTITION_KEY = f"{FAKE_USER_ID}_{FAKE_TREE_ID}"

FAKE_USER_INFO = {
    "user_id": FAKE_USER_ID,
    "email": FAKE_EMAIL,
    "username": "testuser",
    "email_verified": True,
    "token_use": "id",
    "auth_time": int(time.time()),
    "exp": int(time.time()) + 3600,
    "iat": int(time.time()),
}


def _fake_authenticate_request():
    """Side-effect for the auth mock that also sets g.current_user."""
    g.current_user = FAKE_USER_INFO
    return True, FAKE_USER_INFO


@pytest.fixture()
def app():
    """Create a Flask app configured for testing with the Gremlin global
    replaced by a MagicMock so that ``import app`` doesn't need a live
    Neptune instance."""

    with patch("gremlin_connection.create_gremlin_connection") as mock_gremlin:
        mock_g = MagicMock(name="gremlin_traversal")
        mock_gremlin.return_value = mock_g
        import importlib

        import app as app_module

        importlib.reload(app_module)

        app_module.app.config.from_object(TestingConfig)
        yield app_module.app


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture()
def mock_auth():
    """Patch authentication so requests are treated as coming from FAKE_USER_INFO.

    Uses a side_effect so that ``g.current_user`` is populated just like the
    real ``authenticate_request`` does.
    """
    with patch("auth.middleware.authenticate_request", side_effect=_fake_authenticate_request) as mock_fn:
        yield mock_fn


@pytest.fixture()
def auth_headers():
    """Minimal headers that include a Bearer token placeholder."""
    return {"Authorization": "Bearer fake-jwt-token"}


@pytest.fixture()
def partition_headers(auth_headers):
    """Headers with both auth token and partition key."""
    return {**auth_headers, "X-Partition-Key": FAKE_PARTITION_KEY}


@pytest.fixture()
def mock_partition():
    """Patch partition validation so any well-formed key is accepted."""
    with patch("partition.middleware.validate_partition_access", return_value=True), \
         patch("partition.manager.partition_manager.validate_partition_key", return_value=True), \
         patch("partition.manager.partition_manager.parse_partition_key", return_value=(FAKE_USER_ID, FAKE_TREE_ID)):
        yield


@pytest.fixture()
def mock_role_owner():
    """Patch role service to return 'owner' for any lookup."""
    with patch("roles.middleware.get_user_role", return_value="owner"), \
         patch("roles.service.get_user_role", return_value="owner"):
        yield


@pytest.fixture()
def mock_role_editor():
    """Patch role service to return 'editor' for any lookup."""
    with patch("roles.middleware.get_user_role", return_value="editor"), \
         patch("roles.service.get_user_role", return_value="editor"):
        yield


@pytest.fixture()
def mock_role_viewer():
    """Patch role service to return 'viewer' for any lookup."""
    with patch("roles.middleware.get_user_role", return_value="viewer"), \
         patch("roles.service.get_user_role", return_value="viewer"):
        yield


@pytest.fixture()
def mock_role_none():
    """Patch role service to return None (no access)."""
    with patch("roles.middleware.get_user_role", return_value=None), \
         patch("roles.service.get_user_role", return_value=None):
        yield


@pytest.fixture()
def mock_editor_lock_held():
    """Patch editor-lock service so current user holds the lock."""
    lock = {
        "treeId": FAKE_TREE_ID,
        "lockOwner": FAKE_USER_ID,
        "acquiredAt": "2025-01-01T00:00:00Z",
        "expiresAt": int(time.time()) + 300,
    }
    with patch("editor_lock.service.get_editor_lock", return_value=lock), \
         patch("editor_lock.middleware.get_editor_lock", return_value=lock), \
         patch("editor_lock.handlers.get_editor_lock", return_value=lock):
        yield lock


@pytest.fixture()
def mock_editor_lock_none():
    """Patch editor-lock service so no lock is held."""
    with patch("editor_lock.service.get_editor_lock", return_value=None), \
         patch("editor_lock.middleware.get_editor_lock", return_value=None), \
         patch("editor_lock.handlers.get_editor_lock", return_value=None):
        yield


@pytest.fixture()
def mock_acl_store():
    """Provide a MagicMock for roles.acl_store.acl_store."""
    with patch("roles.handlers.acl_store") as mock_store:
        yield mock_store


@pytest.fixture()
def mock_cognito():
    """Patch Cognito lookup helpers."""
    with patch("roles.handlers.get_user_sub_by_email") as mock_sub, \
         patch("roles.handlers.get_user_email_by_sub") as mock_email:
        mock_sub.return_value = "target-user-id"
        mock_email.return_value = "target@example.com"
        yield {"get_user_sub_by_email": mock_sub, "get_user_email_by_sub": mock_email}
