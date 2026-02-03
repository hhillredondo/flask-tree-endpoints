import os
from datetime import datetime, timezone
from typing import Dict, Optional

import boto3
from botocore.exceptions import ClientError
from flask import current_app


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EditorLockStore:
    """DynamoDB-backed editor lock store (one lock per tree)."""

    def __init__(self):
        self._resource = None
        self._table = None
        self._table_name = os.getenv("LOCK_TABLE_NAME", "TreeEditorLocks")
        self._region = (
            os.getenv("AWS_REGION")
            or os.getenv("AWS_DEFAULT_REGION")
            or "eu-central-1"
        )

    @property
    def table(self):
        if self._table is None:
            self._resource = boto3.resource("dynamodb", region_name=self._region)
            self._table = self._resource.Table(self._table_name)
        return self._table

    def get_lock(self, tree_id: str) -> Optional[Dict[str, str]]:
        try:
            response = self.table.get_item(Key={"treeId": tree_id})
            return response.get("Item")
        except ClientError as exc:
            current_app.logger.error(f"Lock get failed: {exc}")
            return None

    def try_acquire(
        self,
        tree_id: str,
        user_id: str,
        expires_at: int,
        now: int,
    ) -> Optional[Dict[str, str]]:
        """Attempt to acquire a lock. Returns lock record if acquired."""
        lock_item = {
            "treeId": tree_id,
            "lockOwner": user_id,
            "acquiredAt": _utc_now_iso(),
            "expiresAt": expires_at,
        }
        try:
            self.table.put_item(
                Item=lock_item,
                ConditionExpression=(
                    "attribute_not_exists(treeId) "
                    "OR attribute_not_exists(expiresAt) "
                    "OR expiresAt <= :now"
                ),
                ExpressionAttributeValues={":now": now},
            )
            return lock_item
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code == "ConditionalCheckFailedException":
                return None
            current_app.logger.error(f"Lock acquire failed: {exc}")
            return None

    def release_lock(self, tree_id: str, user_id: str) -> bool:
        """Release a lock if owned by user_id."""
        try:
            self.table.delete_item(
                Key={"treeId": tree_id},
                ConditionExpression="lockOwner = :user_id",
                ExpressionAttributeValues={":user_id": user_id},
            )
            return True
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code == "ConditionalCheckFailedException":
                return False
            current_app.logger.error(f"Lock release failed: {exc}")
            return False

    def force_release(self, tree_id: str) -> bool:
        """Release a lock without ownership check (owner-only use)."""
        try:
            self.table.delete_item(Key={"treeId": tree_id})
            return True
        except ClientError as exc:
            current_app.logger.error(f"Lock force release failed: {exc}")
            return False


editor_lock_store = EditorLockStore()

