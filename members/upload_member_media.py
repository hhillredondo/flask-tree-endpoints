import io
import os
import uuid

from flask import jsonify, current_app
from PIL import Image

from partition.middleware import get_current_partition
from storage.s3_media import (
    build_photos_prefix,
    build_pic_key,
    build_public_url,
    build_s3_url,
    generate_presigned_get_url,
    get_media_bucket,
    get_media_prefix,
    list_objects,
    parse_s3_url,
    upload_bytes,
)


_FORMAT_TO_MIME = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}

_FORMAT_TO_EXT = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}

_ERR_MISSING_MEMBER_ID = "Missing member_id"
_ERR_PARTITION_REQUIRED = "Partition key is required"


def _ensure_member_exists(g, member_id, partition_key):
    return g.V(member_id).has("_partitionKey", partition_key).hasNext()


def _get_presigned_ttl_seconds(request):
    default_ttl = int(
        current_app.config.get("S3_PRESIGNED_TTL_SECONDS")
        or os.getenv("S3_PRESIGNED_TTL_SECONDS", "3600")
    )
    raw_ttl = request.args.get("expires_in")
    if not raw_ttl:
        return default_ttl
    try:
        ttl = int(raw_ttl)
    except (TypeError, ValueError):
        return default_ttl
    if ttl <= 0:
        return default_ttl
    return min(ttl, 86400)


def _get_member_property(g, member_id, partition_key, property_key):
    traversal = g.V(member_id).has("_partitionKey", partition_key)
    element_traversal = traversal.elementMap()
    if element_traversal.hasNext():
        element = element_traversal.next()
        if property_key in element:
            return _coerce_property_value(element.get(property_key))
    value_traversal = traversal.values(property_key)
    if value_traversal.hasNext():
        return value_traversal.next()
    return None


def _coerce_property_value(value):
    if isinstance(value, list):
        if len(value) == 1:
            return _coerce_property_value(value[0])
        return [_coerce_property_value(item) for item in value]
    if isinstance(value, dict) and "value" in value:
        return value.get("value")
    return value


def _get_upload_files(request):
    files = request.files.getlist("files")
    if not files:
        single_file = request.files.get("file")
        if single_file:
            files = [single_file]
    return files


def _validate_image_bytes(file_bytes):
    try:
        image = Image.open(io.BytesIO(file_bytes))
        image_format = image.format
        image.verify()
    except OSError:
        return None, "One or more files are not valid images"
    if image_format not in _FORMAT_TO_MIME:
        return None, f"Unsupported image format: {image_format}"
    return image_format, None


def _upload_photo_files(files, bucket, photos_prefix, base_url, region, request):
    uploaded_urls = []
    uploaded_keys = []
    for upload_file in files:
        if not upload_file:
            continue
        file_bytes = upload_file.read()
        if not file_bytes:
            continue

        image_format, error_message = _validate_image_bytes(file_bytes)
        if error_message:
            return None, None, error_message

        extension = _FORMAT_TO_EXT[image_format]
        object_name = f"{uuid.uuid4().hex}{extension}"
        key = f"{photos_prefix}{object_name}"

        upload_bytes(bucket, key, file_bytes, content_type=_FORMAT_TO_MIME[image_format])
        uploaded_keys.append(key)
        if base_url:
            uploaded_urls.append(build_public_url(bucket, key, region=region, base_url=base_url))
        else:
            uploaded_urls.append(
                generate_presigned_get_url(bucket, key, _get_presigned_ttl_seconds(request))
            )

    if not uploaded_urls:
        return None, None, "No valid image files provided"

    return uploaded_urls, uploaded_keys, None

def upload_member_pic(g, request):
    try:
        member_id = request.form.get("member_id") or request.form.get("id")
        if not member_id:
            return jsonify({"error": _ERR_MISSING_MEMBER_ID}), 400

        upload_file = request.files.get("file")
        if not upload_file:
            return jsonify({"error": "Missing file"}), 400

        partition_key = get_current_partition()
        if not partition_key:
            return jsonify({"error": _ERR_PARTITION_REQUIRED}), 400
        if not _ensure_member_exists(g, member_id, partition_key):
            return (
                jsonify({"error": f"Member with ID {member_id} does not exist in this tree"}),
                404,
            )

        bucket = get_media_bucket()
        if not bucket:
            return jsonify({"error": "S3_MEDIA_BUCKET is not configured"}), 500

        prefix = get_media_prefix()
        region = current_app.config.get("AWS_REGION") or os.getenv("AWS_REGION")
        base_url = current_app.config.get("S3_PUBLIC_BASE_URL") or os.getenv("S3_PUBLIC_BASE_URL")
        pic_size = int(current_app.config.get("S3_PIC_SIZE", 24))

        try:
            image = Image.open(upload_file.stream)
        except OSError:
            return jsonify({"error": "Invalid image file"}), 400

        image = image.convert("RGB")
        image = image.resize((pic_size, pic_size), Image.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        key = build_pic_key(prefix, partition_key, member_id, ext="png")
        upload_bytes(bucket, key, buffer.getvalue(), content_type="image/png")

        s3_url = build_s3_url(bucket, key)
        g.V(member_id).property("pic", s3_url).next()

        response = {"pic": s3_url}
        if base_url:
            response["pic_url"] = build_public_url(bucket, key, region=region, base_url=base_url)
        else:
            response["pic_url"] = generate_presigned_get_url(bucket, key, _get_presigned_ttl_seconds(request))
        return jsonify(response), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


def upload_member_photos(g, request):
    try:
        member_id = request.form.get("member_id") or request.form.get("id")
        if not member_id:
            return jsonify({"error": _ERR_MISSING_MEMBER_ID}), 400

        files = _get_upload_files(request)

        if not files:
            return jsonify({"error": "No files provided"}), 400

        partition_key = get_current_partition()
        if not partition_key:
            return jsonify({"error": _ERR_PARTITION_REQUIRED}), 400
        if not _ensure_member_exists(g, member_id, partition_key):
            return (
                jsonify({"error": f"Member with ID {member_id} does not exist in this tree"}),
                404,
            )

        bucket = get_media_bucket()
        if not bucket:
            return jsonify({"error": "S3_MEDIA_BUCKET is not configured"}), 500

        prefix = get_media_prefix()
        region = current_app.config.get("AWS_REGION") or os.getenv("AWS_REGION")
        base_url = current_app.config.get("S3_PUBLIC_BASE_URL") or os.getenv("S3_PUBLIC_BASE_URL")
        photos_prefix = build_photos_prefix(prefix, partition_key, member_id)

        uploaded_urls, uploaded_keys, error_message = _upload_photo_files(
            files, bucket, photos_prefix, base_url, region, request
        )
        if error_message:
            return jsonify({"error": error_message}), 400

        photos_path = f"s3://{bucket}/{photos_prefix}"
        g.V(member_id).property("photos", photos_path).next()

        return jsonify({"photos": photos_path, "uploaded": uploaded_urls, "uploaded_keys": uploaded_keys}), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


def get_member_pic_url(g, request):
    try:
        debug = request.args.get("debug") == "1"
        member_id = request.args.get("member_id") or request.args.get("id")
        if not member_id:
            return jsonify({"error": _ERR_MISSING_MEMBER_ID}), 400

        partition_key = get_current_partition()
        if not partition_key:
            return jsonify({"error": _ERR_PARTITION_REQUIRED}), 400
        if not _ensure_member_exists(g, member_id, partition_key):
            return (
                jsonify({"error": f"Member with ID {member_id} does not exist in this tree"}),
                404,
            )

        pic_value = _get_member_property(g, member_id, partition_key, "pic")
        if not pic_value:
            if debug:
                element = g.V(member_id).has("_partitionKey", partition_key).elementMap().next()
                return jsonify({"error": "No pic found for member", "debug": {"element": element}}), 404
            return jsonify({"error": "No pic found for member"}), 404

        if isinstance(pic_value, str) and pic_value.startswith("http"):
            return jsonify({"pic": pic_value, "url": pic_value}), 200

        s3_parts = parse_s3_url(pic_value)
        if not s3_parts:
            return jsonify({"error": "Invalid pic storage value"}), 500

        bucket, key = s3_parts
        ttl = _get_presigned_ttl_seconds(request)
        url = generate_presigned_get_url(bucket, key, ttl)
        return jsonify({"pic": pic_value, "url": url, "expires_in": ttl}), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


def get_member_photo_urls(g, request):
    try:
        member_id = request.args.get("member_id") or request.args.get("id")
        if not member_id:
            return jsonify({"error": _ERR_MISSING_MEMBER_ID}), 400

        partition_key = get_current_partition()
        if not partition_key:
            return jsonify({"error": _ERR_PARTITION_REQUIRED}), 400
        if not _ensure_member_exists(g, member_id, partition_key):
            return (
                jsonify({"error": f"Member with ID {member_id} does not exist in this tree"}),
                404,
            )

        photos_value = _get_member_property(g, member_id, partition_key, "photos")
        if not photos_value:
            return jsonify({"error": "No photos found for member"}), 404

        s3_parts = parse_s3_url(photos_value)
        if not s3_parts:
            return jsonify({"error": "Invalid photos storage value"}), 500

        bucket, prefix = s3_parts
        ttl = _get_presigned_ttl_seconds(request)
        keys = list_objects(bucket, prefix)
        urls = [generate_presigned_get_url(bucket, key, ttl) for key in keys]
        return jsonify(
            {"photos": photos_value, "urls": urls, "keys": keys, "expires_in": ttl}
        ), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

