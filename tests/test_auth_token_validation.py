"""Tests for Cognito JWT validation.

The previous implementation verified the signature, issuer and expiry but not
`token_use` or `aud`, so an access token was accepted in place of an id token and
a token minted for any app client in the pool was accepted. These tests pin both
checks, plus the signature and issuer checks they sit alongside.
"""

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from auth.utils import AmplifyAuthUtils

REGION = "eu-central-1"
POOL_ID = "eu-central-1_TESTPOOL"
CLIENT_ID = "test-client-id"
ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{POOL_ID}"
KID = "test-key-id"


@pytest.fixture(scope="module")
def signing_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="module")
def other_key():
    """A key that is *not* in the pool's JWKS."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def auth_utils(monkeypatch, signing_key):
    monkeypatch.setenv("AMPLIFY_USER_POOL_ID", POOL_ID)
    monkeypatch.setenv("AMPLIFY_USER_POOL_CLIENT_ID", CLIENT_ID)
    monkeypatch.setenv("AWS_REGION", REGION)
    utils = AmplifyAuthUtils()

    class _StubKey:
        key = signing_key.public_key()

    class _StubJwkClient:
        def get_signing_key_from_jwt(self, token):
            return _StubKey()

    utils._jwk_client = _StubJwkClient()
    return utils


def make_token(key, **overrides):
    now = int(time.time())
    claims = {
        "sub": "user-123",
        "email": "user@example.com",
        "token_use": "id",
        "aud": CLIENT_ID,
        "iss": ISSUER,
        "iat": now,
        "exp": now + 3600,
    }
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": KID})


class TestValidateToken:
    def test_accepts_a_valid_id_token(self, auth_utils, signing_key, app):
        with app.app_context():
            payload = auth_utils.validate_token(make_token(signing_key))
        assert payload is not None
        assert payload["sub"] == "user-123"

    def test_rejects_an_access_token(self, auth_utils, signing_key, app):
        """Access tokens are signed by the same keys with the same issuer."""
        token = make_token(signing_key, token_use="access")
        with app.app_context():
            assert auth_utils.validate_token(token) is None

    def test_rejects_a_token_for_a_different_app_client(self, auth_utils, signing_key, app):
        token = make_token(signing_key, aud="some-other-client")
        with app.app_context():
            assert auth_utils.validate_token(token) is None

    def test_rejects_a_token_from_a_different_issuer(self, auth_utils, signing_key, app):
        token = make_token(signing_key, iss="https://evil.example.com")
        with app.app_context():
            assert auth_utils.validate_token(token) is None

    def test_rejects_an_expired_token(self, auth_utils, signing_key, app):
        now = int(time.time())
        token = make_token(signing_key, iat=now - 7200, exp=now - 3600)
        with app.app_context():
            assert auth_utils.validate_token(token) is None

    def test_rejects_a_token_signed_by_an_unknown_key(self, auth_utils, other_key, app):
        token = make_token(other_key)
        with app.app_context():
            assert auth_utils.validate_token(token) is None

    def test_rejects_an_unsigned_token(self, auth_utils, app):
        """The `alg: none` classic: a payload with no signature at all."""
        token = jwt.encode({"sub": "attacker", "token_use": "id"}, None, algorithm="none")
        with app.app_context():
            assert auth_utils.validate_token(token) is None

    def test_rejects_garbage(self, auth_utils, app):
        with app.app_context():
            assert auth_utils.validate_token("not-a-jwt") is None


class TestExtractUserInfo:
    def test_carries_groups_through(self, auth_utils):
        info = auth_utils.extract_user_info(
            {"sub": "u1", "email": "e@x.com", "cognito:groups": ["admin"]}
        )
        assert info["user_id"] == "u1"
        assert info["groups"] == ["admin"]
