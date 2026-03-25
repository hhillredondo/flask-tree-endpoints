"""Tests for media endpoints (/member/pic, /member/photos, /member/pic-url, etc.)."""

import io
from unittest.mock import patch

from flask import jsonify


class TestUploadPic:
    def test_unauthenticated(self, client):
        resp = client.post("/member/pic")
        assert resp.status_code == 401

    def test_upload_pic_with_lock(self, client, mock_auth, partition_headers, mock_partition, mock_role_editor, mock_editor_lock_held):
        def fake_handler(g, req):
            return jsonify({"pic": "key.jpg", "pic_url": "https://cdn/key.jpg"}), 200

        with patch("app.upload_member_pic", side_effect=fake_handler):
            data = {
                "member_id": "m1",
                "file": (io.BytesIO(b"fake-image"), "photo.jpg"),
            }
            resp = client.post(
                "/member/pic",
                headers=partition_headers,
                data=data,
                content_type="multipart/form-data",
            )
        assert resp.status_code == 200
        assert "pic" in resp.get_json()


class TestUploadPhotos:
    def test_upload_photos_with_lock(self, client, mock_auth, partition_headers, mock_partition, mock_role_editor, mock_editor_lock_held):
        def fake_handler(g, req):
            return jsonify({"photos": "keys", "urls": ["u1"], "keys": ["k1"]}), 200

        with patch("app.upload_member_photos", side_effect=fake_handler):
            data = {
                "member_id": "m1",
                "files": (io.BytesIO(b"img"), "pic.jpg"),
            }
            resp = client.post(
                "/member/photos",
                headers=partition_headers,
                data=data,
                content_type="multipart/form-data",
            )
        assert resp.status_code == 200


class TestGetPicUrl:
    def test_get_pic_url(self, client, mock_auth, partition_headers, mock_partition, mock_role_viewer):
        def fake_handler(g, req):
            return jsonify({"pic": "key.jpg", "url": "https://presigned"}), 200

        with patch("app.get_member_pic_url", side_effect=fake_handler):
            resp = client.get("/member/pic-url?member_id=m1", headers=partition_headers)
        assert resp.status_code == 200


class TestGetPhotoUrls:
    def test_get_photo_urls(self, client, mock_auth, partition_headers, mock_partition, mock_role_viewer):
        def fake_handler(g, req):
            return jsonify({"photos": "k", "urls": ["u1"], "keys": ["k1"], "expires_in": 3600}), 200

        with patch("app.get_member_photo_urls", side_effect=fake_handler):
            resp = client.get("/member/photos-urls?member_id=m1", headers=partition_headers)
        assert resp.status_code == 200


class TestUploadDocuments:
    def test_upload_documents_with_lock(self, client, mock_auth, partition_headers, mock_partition, mock_role_editor, mock_editor_lock_held):
        def fake_handler(g, req):
            return jsonify({"documents": "k", "uploaded": ["f1"], "uploaded_keys": ["k1"]}), 200

        with patch("app.upload_member_documents", side_effect=fake_handler):
            data = {
                "member_id": "m1",
                "files": (io.BytesIO(b"doc"), "file.pdf"),
            }
            resp = client.post(
                "/member/documents",
                headers=partition_headers,
                data=data,
                content_type="multipart/form-data",
            )
        assert resp.status_code == 200


class TestGetDocumentUrls:
    def test_get_document_urls(self, client, mock_auth, partition_headers, mock_partition, mock_role_viewer):
        def fake_handler(g, req):
            return jsonify({"documents": "k", "urls": ["u1"], "keys": ["k1"], "expires_in": 3600}), 200

        with patch("app.get_member_document_urls", side_effect=fake_handler):
            resp = client.get("/member/documents-urls?member_id=m1", headers=partition_headers)
        assert resp.status_code == 200
