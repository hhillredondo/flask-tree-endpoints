import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from flask import current_app

ROLE_OWNER = "owner"
ROLE_EDITOR = "editor"
ROLE_VIEWER = "viewer"
ROLE_VALUES = {ROLE_OWNER, ROLE_EDITOR, ROLE_VIEWER}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AclStore:
    """DynamoDB-backed ACL store for tree permissions."""

    def __init__(self):
        self._resource = None
        self._table = None
        self._table_name = os.getenv("ACL_TABLE_NAME", "TreeAcl")
        self._region = os.getenv("AWS_REGION", "eu-central-1")

    @property
    def table(self):
        if self._table is None:
            self._resource = boto3.resource("dynamodb", region_name=self._region)
            self._table = self._resource.Table(self._table_name)
        return self._table

    def get_role(self, tree_id: str, user_id: str) -> Optional[str]:
        try:
            response = self.table.get_item(
                Key={"treeId": tree_id, "userId": user_id}
            )
            item = response.get("Item")
            if not item:
                return None
            return item.get("role")
        except ClientError as exc:
            current_app.logger.error(f"ACL get_role failed: {exc}")
            return None

    def get_entry(self, tree_id: str, user_id: str) -> Optional[Dict[str, str]]:
        try:
            response = self.table.get_item(
                Key={"treeId": tree_id, "userId": user_id}
            )
            return response.get("Item")
        except ClientError as exc:
            current_app.logger.error(f"ACL get_entry failed: {exc}")
            return None

    def put_role(self, tree_id: str, user_id: str, role: str) -> bool:
        if role not in ROLE_VALUES:
            raise ValueError("Invalid role value")
        try:
            self.table.put_item(
                Item={
                    "treeId": tree_id,
                    "userId": user_id,
                    "role": role,
                    "createdAt": _utc_now_iso(),
                }
            )
            return True
        except ClientError as exc:
            current_app.logger.error(f"ACL put_role failed: {exc}")
            return False

    def delete_role(self, tree_id: str, user_id: str) -> bool:
        try:
            self.table.delete_item(Key={"treeId": tree_id, "userId": user_id})
            return True
        except ClientError as exc:
            current_app.logger.error(f"ACL delete_role failed: {exc}")
            return False

    def list_roles(self, tree_id: str) -> List[Dict[str, str]]:
        try:
            response = self.table.query(
                KeyConditionExpression=Key("treeId").eq(tree_id)
            )
            return response.get("Items", [])
        except ClientError as exc:
            current_app.logger.error(f"ACL list_roles failed: {exc}")
            return []

    def delete_roles_for_tree(self, tree_id: str) -> bool:
        try:
            response = self.table.query(
                KeyConditionExpression=Key("treeId").eq(tree_id)
            )
            items = response.get("Items", [])
            if not items:
                return True
            with self.table.batch_writer() as batch:
                for item in items:
                    user_id = item.get("userId")
                    if user_id:
                        batch.delete_item(Key={"treeId": tree_id, "userId": user_id})
            return True
        except ClientError as exc:
            current_app.logger.error(f"ACL delete_roles_for_tree failed: {exc}")
            return False

    def list_roles_for_user(self, user_id: str) -> List[Dict[str, str]]:
        try:
            items = []
            scan_kwargs = {"FilterExpression": Attr("userId").eq(user_id)}
            while True:
                response = self.table.scan(**scan_kwargs)
                items.extend(response.get("Items", []))
                last_key = response.get("LastEvaluatedKey")
                if not last_key:
                    break
                scan_kwargs["ExclusiveStartKey"] = last_key
            return items
        except ClientError as exc:
            current_app.logger.error(f"ACL list_roles_for_user failed: {exc}")
            return []

    def delete_roles_for_user(self, user_id: str) -> bool:
        try:
            scan_kwargs = {"FilterExpression": Attr("userId").eq(user_id)}
            with self.table.batch_writer() as batch:
                while True:
                    response = self.table.scan(**scan_kwargs)
                    items = response.get("Items", [])
                    for item in items:
                        tree_id = item.get("treeId")
                        if tree_id:
                            batch.delete_item(Key={"treeId": tree_id, "userId": user_id})
                    last_key = response.get("LastEvaluatedKey")
                    if not last_key:
                        break
                    scan_kwargs["ExclusiveStartKey"] = last_key
            return True
        except ClientError as exc:
            current_app.logger.error(f"ACL delete_roles_for_user failed: {exc}")
            return False


acl_store = AclStore()



