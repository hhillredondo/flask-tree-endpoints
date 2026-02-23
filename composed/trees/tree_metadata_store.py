import os
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from flask import current_app


class TreeMetadataStore:
    """Read-only access to the Amplify-managed Tree DynamoDB table."""

    def __init__(self):
        self._resource = None
        self._table = None
        self._table_name = os.getenv("TREE_TABLE_NAME", "Tree")
        self._logged_table_name = False
        self._region = (
            os.getenv("AWS_REGION")
            or os.getenv("AWS_DEFAULT_REGION")
            or "eu-central-1"
        )

    @property
    def _dynamo(self):
        if self._resource is None:
            self._resource = boto3.resource("dynamodb", region_name=self._region)
        return self._resource

    @property
    def table(self):
        if not self._logged_table_name:
            try:
                current_app.logger.info(
                    "TreeMetadataStore TREE_TABLE_NAME env=%s resolved table=%s",
                    os.getenv("TREE_TABLE_NAME"),
                    self._table_name,
                )
            except Exception:
                pass
            self._logged_table_name = True
        if self._table is None:
            self._table = self._dynamo.Table(self._table_name)
        return self._table

    def get_tree(self, tree_id: str) -> Optional[Dict]:
        """Fetch a single tree record by id."""
        try:
            response = self.table.get_item(Key={"id": tree_id})
            return response.get("Item")
        except ClientError as exc:
            current_app.logger.error(f"TreeMetadata get_tree failed: {exc}")
            return None

    def batch_get_trees(self, tree_ids: List[str]) -> Dict[str, Dict]:
        """
        Fetch multiple tree records in one BatchGetItem call.

        Returns a dict mapping tree_id -> item.
        DynamoDB BatchGetItem supports up to 100 keys per call;
        this method handles pagination for larger lists.
        """
        if not tree_ids:
            return {}

        result: Dict[str, Dict] = {}
        table_name = self.table.name
        # Deduplicate while preserving order
        unique_ids = list(dict.fromkeys(tree_ids))

        try:
            # BatchGetItem accepts max 100 keys at a time
            for i in range(0, len(unique_ids), 100):
                batch = unique_ids[i : i + 100]
                request_items = {
                    table_name: {
                        "Keys": [{"id": tid} for tid in batch],
                        "ConsistentRead": False,
                    }
                }

                response = self._dynamo.batch_get_item(
                    RequestItems=request_items
                )

                for item in response.get("Responses", {}).get(table_name, []):
                    result[item["id"]] = item

                # Handle unprocessed keys (throttling)
                unprocessed = response.get("UnprocessedKeys", {})
                while unprocessed.get(table_name):
                    response = self._dynamo.batch_get_item(
                        RequestItems=unprocessed
                    )
                    for item in response.get("Responses", {}).get(table_name, []):
                        result[item["id"]] = item
                    unprocessed = response.get("UnprocessedKeys", {})

        except ClientError as exc:
            current_app.logger.error(f"TreeMetadata batch_get_trees failed: {exc}")

        return result


tree_metadata_store = TreeMetadataStore()

