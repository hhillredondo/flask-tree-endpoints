import os
import json
import requests
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from flask import current_app, g
from functools import wraps


class AmplifyAuthUtils:
    """Utilities for Amplify JWT token validation and user extraction"""
    
    def __init__(self):
        self.user_pool_id = os.getenv('AMPLIFY_USER_POOL_ID')
        self.region = os.getenv('AWS_REGION', 'eu-central-1')
        self.jwks_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
        self._jwks = None
    
    def get_jwks(self) -> Dict[str, Any]:
        """Get JSON Web Key Set from Cognito"""
        if self._jwks is None:
            try:
                response = requests.get(self.jwks_url, timeout=10)
                response.raise_for_status()
                self._jwks = response.json()
            except requests.RequestException as e:
                current_app.logger.error(f"Failed to fetch JWKS: {e}")
                raise Exception("Failed to fetch JWKS")
        return self._jwks
    
    def get_key_from_jwks(self, kid: str) -> Optional[Dict[str, Any]]:
        """Get the appropriate key from JWKS based on key ID"""
        jwks = self.get_jwks()
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                return key
        return None
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate Amplify JWT token and return payload"""
        try:
            # Log token preview for debugging
            token_preview = token[:20] + "..." if len(token) > 20 else token
            current_app.logger.debug(f"Validating token: {token_preview}")
            
            # Decode token header to get key ID
            try:
                header = jwt.get_unverified_header(token)
            except Exception as e:
                current_app.logger.error(f"Error decoding token headers: {e}")
                current_app.logger.error(f"Token length: {len(token)}, starts with: {token[:20]}")
                return None
            
            kid = header.get('kid')
            
            if not kid:
                current_app.logger.error(f"No key ID in token header. Header: {header}")
                return None
            
            current_app.logger.debug(f"Token key ID: {kid}")
            
            # Get the appropriate key from JWKS
            key = self.get_key_from_jwks(kid)
            if not key:
                current_app.logger.error(f"Key {kid} not found in JWKS")
                return None
            
            # Validate and decode token
            payload = jwt.decode(
                token,
                key,
                algorithms=['RS256'],
                audience=None,  # Cognito doesn't use audience
                issuer=f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}",
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_iat': True,
                    'verify_iss': True,
                }
            )
            
            current_app.logger.debug(f"Token validated successfully for user: {payload.get('sub')}")
            return payload
            
        except JWTError as e:
            current_app.logger.error(f"JWT validation error: {e}")
            current_app.logger.error(f"Token type: {type(token)}, length: {len(token)}")
            return None
        except Exception as e:
            current_app.logger.error(f"Token validation error: {e}")
            current_app.logger.error(f"Token type: {type(token)}, length: {len(token)}")
            return None
    
    def extract_user_info(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user information from JWT payload"""
        return {
            'user_id': payload.get('sub'),
            'email': payload.get('email'),
            'username': payload.get('cognito:username'),
            'email_verified': payload.get('email_verified', False),
            'token_use': payload.get('token_use'),
            'auth_time': payload.get('auth_time'),
            'exp': payload.get('exp'),
            'iat': payload.get('iat'),
        }


# Global instance
auth_utils = AmplifyAuthUtils()


def get_current_user_id() -> Optional[str]:
    """Get current user ID from Flask g context"""
    if hasattr(g, 'current_user'):
        return g.current_user.get('user_id')
    return None


def get_current_user_email() -> Optional[str]:
    """Get current user email from Flask g context"""
    if hasattr(g, 'current_user'):
        return g.current_user.get('email')
    return None


def get_current_user_info() -> Optional[Dict[str, Any]]:
    """Get current user info from Flask g context"""
    if hasattr(g, 'current_user'):
        return g.current_user
    return None
