import os
import boto3
from botocore.exceptions import ClientError
from flask import current_app
from urllib.parse import urlparse


def get_s3_client():
    region = current_app.config.get("AWS_REGION") or os.getenv("AWS_REGION")
    return boto3.client("s3", region_name=region)


def get_media_bucket():
    return current_app.config.get("S3_MEDIA_BUCKET") or os.getenv("S3_MEDIA_BUCKET")


def get_media_prefix():
    prefix = current_app.config.get("S3_MEDIA_PREFIX") or os.getenv("S3_MEDIA_PREFIX", "trees")
    return prefix.strip("/")


def build_member_base_prefix(prefix, partition_key, member_id):
    return f"{prefix}/{partition_key}/members/{member_id}"


def build_pic_key(prefix, partition_key, member_id, ext="png"):
    return f"{build_member_base_prefix(prefix, partition_key, member_id)}/pic.{ext}"


def build_photos_prefix(prefix, partition_key, member_id):
    return f"{build_member_base_prefix(prefix, partition_key, member_id)}/photos/"


def build_public_url(bucket, key, region=None, base_url=None):
    if base_url:
        return f"{base_url.rstrip('/')}/{key}"
    if region:
        return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
    return f"https://{bucket}.s3.amazonaws.com/{key}"


def build_s3_url(bucket, key):
    return f"s3://{bucket}/{key}"


def parse_s3_url(value):
    if not isinstance(value, str) or not value.startswith("s3://"):
        return None
    parsed = urlparse(value)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    if not bucket or not key:
        return None
    return bucket, key


def upload_bytes(bucket, key, data, content_type=None):
    s3_client = get_s3_client()
    extra_args = {}
    if content_type:
        extra_args["ContentType"] = content_type
    try:
        s3_client.put_object(Bucket=bucket, Key=key, Body=data, **extra_args)
    except ClientError as exc:
        raise RuntimeError(f"Failed to upload to S3: {exc}") from exc


def generate_presigned_get_url(bucket, key, expires_in):
    s3_client = get_s3_client()
    try:
        return s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
    except ClientError as exc:
        raise RuntimeError(f"Failed to generate presigned URL: {exc}") from exc


def list_objects(bucket, prefix):
    s3_client = get_s3_client()
    keys = []
    paginator = s3_client.get_paginator("list_objects_v2")
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj.get("Key")
                if key:
                    keys.append(key)
        return keys
    except ClientError as exc:
        raise RuntimeError(f"Failed to list S3 objects: {exc}") from exc

