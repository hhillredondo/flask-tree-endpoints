import os
from typing import Any, Dict, Optional

import jwt
from flask import current_app, g
from jwt import PyJWKClient

# Cognito id tokens are what the browser sends (see trees-amplify flaskService).
# Access tokens are signed by the same keys with the same issuer, so `token_use`
# must be checked explicitly or one is accepted in place of the other.
_EXPECTED_TOKEN_USE = "id"

# PyJWKClient caches keys and refetches when it sees an unknown `kid`, which is
# what makes Cognito key rotation a non-event. The previous implementation cached
# the JWKS for the process lifetime, so rotation broke auth until a redeploy and a
# revoked key stayed trusted by long-lived tasks.
_JWKS_CACHE_KEYS = 16
_JWKS_LIFESPAN_SECONDS = 3600


class AmplifyAuthUtils:
    """Validates Cognito JWTs and extracts the user identity from them."""

    def __init__(self):
        self.user_pool_id = os.getenv("AMPLIFY_USER_POOL_ID")
        self.client_id = os.getenv("AMPLIFY_USER_POOL_CLIENT_ID")
        self.region = os.getenv("AWS_REGION", "eu-central-1")
        self.issuer = (
            f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"
        )
        self._jwk_client: Optional[PyJWKClient] = None

    def _get_jwk_client(self) -> PyJWKClient:
        if self._jwk_client is None:
            self._jwk_client = PyJWKClient(
                f"{self.issuer}/.well-known/jwks.json",
                cache_keys=True,
                max_cached_keys=_JWKS_CACHE_KEYS,
                lifespan=_JWKS_LIFESPAN_SECONDS,
            )
        return self._jwk_client

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Return the token's claims, or None if it fails any check.

        Verifies the RS256 signature against the pool's JWKS plus issuer, expiry,
        audience (app client) and `token_use`. Returns None rather than raising so
        callers cannot accidentally treat a failure as success.
        """
        if not self.user_pool_id:
            current_app.logger.error("AMPLIFY_USER_POOL_ID is not configured")
            return None

        try:
            signing_key = self._get_jwk_client().get_signing_key_from_jwt(token)

            # `aud` is only enforced when the client id is configured; a missing
            # client id is logged loudly rather than silently skipping the check.
            if not self.client_id:
                current_app.logger.warning(
                    "AMPLIFY_USER_POOL_CLIENT_ID is not set; skipping audience check"
                )

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=self.issuer,
                audience=self.client_id if self.client_id else None,
                options={
                    "require": ["exp", "iat", "iss", "sub"],
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_iss": True,
                    "verify_aud": bool(self.client_id),
                },
            )
        except jwt.PyJWTError as exc:
            current_app.logger.warning("JWT validation failed: %s", exc)
            return None
        except Exception as exc:  # JWKS fetch failures, malformed input
            current_app.logger.error("JWT validation error: %s", exc)
            return None

        token_use = payload.get("token_use")
        if token_use != _EXPECTED_TOKEN_USE:
            current_app.logger.warning(
                "Rejected token with token_use=%r (expected %r)",
                token_use,
                _EXPECTED_TOKEN_USE,
            )
            return None

        return payload

    def extract_user_info(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user information from JWT payload"""
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "username": payload.get("cognito:username"),
            "email_verified": payload.get("email_verified", False),
            "groups": payload.get("cognito:groups", []),
            "token_use": payload.get("token_use"),
            "auth_time": payload.get("auth_time"),
            "exp": payload.get("exp"),
            "iat": payload.get("iat"),
        }


# Global instance
auth_utils = AmplifyAuthUtils()


def get_current_user_id() -> Optional[str]:
    """Get current user ID from Flask g context"""
    if hasattr(g, "current_user"):
        return g.current_user.get("user_id")
    return None


def get_current_user_email() -> Optional[str]:
    """Get current user email from Flask g context"""
    if hasattr(g, "current_user"):
        return g.current_user.get("email")
    return None


def get_current_user_info() -> Optional[Dict[str, Any]]:
    """Get current user info from Flask g context"""
    if hasattr(g, "current_user"):
        return g.current_user
    return None
