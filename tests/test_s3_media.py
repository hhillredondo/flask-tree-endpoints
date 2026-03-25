import unittest

from storage.s3_media import (
    build_member_base_prefix,
    build_photos_prefix,
    build_pic_key,
    build_public_url,
    build_s3_url,
    parse_s3_url,
)


class S3MediaTests(unittest.TestCase):
    def test_key_builders(self):
        prefix = "trees"
        partition_key = "user_tree"
        member_id = "123"
        base = build_member_base_prefix(prefix, partition_key, member_id)
        self.assertEqual(base, "trees/user_tree/members/123")
        self.assertEqual(
            build_pic_key(prefix, partition_key, member_id, ext="png"),
            "trees/user_tree/members/123/pic.png",
        )
        self.assertEqual(
            build_photos_prefix(prefix, partition_key, member_id),
            "trees/user_tree/members/123/photos/",
        )

    def test_urls(self):
        bucket = "my-bucket"
        key = "path/to/object.png"
        self.assertEqual(build_s3_url(bucket, key), "s3://my-bucket/path/to/object.png")
        url = build_public_url(bucket, key, region="eu-central-1")
        self.assertTrue(url.startswith("https://my-bucket.s3.eu-central-1.amazonaws.com/"))

    def test_parse_s3_url(self):
        bucket, key = parse_s3_url("s3://my-bucket/path/to/object.png")
        self.assertEqual(bucket, "my-bucket")
        self.assertEqual(key, "path/to/object.png")
        self.assertIsNone(parse_s3_url("http://example.com/object"))



