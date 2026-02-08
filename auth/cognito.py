import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from flask import current_app

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "cognito-idp",
            region_name=os.getenv("AWS_REGION", "eu-central-1")
        )
    return _client


def get_user_sub_by_email(email: str) -> Optional[str]:
    """Lookup Cognito user sub by email address."""
    if not email:
        return None

    try:
        response = _get_client().list_users(
            UserPoolId=os.getenv("AMPLIFY_USER_POOL_ID"),
            Filter=f'email = "{email}"',
            Limit=1
        )
        users = response.get("Users", [])
        if not users:
            return None

        for attr in users[0].get("Attributes", []):
            if attr.get("Name") == "sub":
                return attr.get("Value")
        return None
    except (ClientError, BotoCoreError) as exc:
        current_app.logger.error(f"Cognito lookup failed for {email}: {exc}")
        return None
    except Exception as exc:
        current_app.logger.exception(f"Unexpected Cognito error for {email}: {exc}")
        return None


def delete_user_by_sub(user_id: str) -> bool:
    """Delete a Cognito user by sub (admin delete)."""
    if not user_id:
        return False

    try:
        _get_client().admin_delete_user(
            UserPoolId=os.getenv("AMPLIFY_USER_POOL_ID"),
            Username=user_id,
        )
        return True
    except (ClientError, BotoCoreError) as exc:
        current_app.logger.error(f"Cognito delete failed for {user_id}: {exc}")
        return False
    except Exception as exc:
        current_app.logger.exception(f"Unexpected Cognito delete error for {user_id}: {exc}")
        return False



