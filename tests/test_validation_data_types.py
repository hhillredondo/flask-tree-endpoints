import unittest

from validation import dataTypes


class DataTypesValidationTests(unittest.TestCase):
    def test_validate_member_name(self):
        ok, _ = dataTypes.validate_member_name("name", "O'Neil")
        self.assertTrue(ok)
        ok, msg = dataTypes.validate_member_name("name", "123")
        self.assertFalse(ok)
        self.assertIn("invalid characters", msg)

    def test_validate_boolean(self):
        ok, _ = dataTypes.validate_boolean("flag", True)
        self.assertTrue(ok)
        ok, _ = dataTypes.validate_boolean("flag", "true")
        self.assertFalse(ok)

    def test_validate_member_description(self):
        ok, _ = dataTypes.validate_member_description("hello", max_length=10)
        self.assertTrue(ok)
        ok, msg = dataTypes.validate_member_description("x" * 11, max_length=10)
        self.assertFalse(ok)
        self.assertIn("maximum", msg)

    def test_validate_date_format(self):
        ok, parsed = dataTypes.validate_date_format("2020-01-02T03:04:05Z")
        self.assertTrue(ok)
        self.assertEqual(parsed.year, 2020)
        ok, msg = dataTypes.validate_date_format("bad-date")
        self.assertFalse(ok)
        self.assertIn("invalid", msg.lower())

    def test_validate_gender(self):
        ok, _ = dataTypes.validate_gender("male")
        self.assertTrue(ok)
        ok, _ = dataTypes.validate_gender("unknown")
        self.assertFalse(ok)

    def test_validate_url(self):
        ok, _ = dataTypes.validate_url("pic", "https://example.com/a.png")
        self.assertTrue(ok)
        ok, msg = dataTypes.validate_url("pic", "notaurl")
        self.assertFalse(ok)
        self.assertIn("Invalid pic URL", msg)

    def test_validate_relation_type(self):
        ok, _ = dataTypes.validate_relation_type("parent")
        self.assertTrue(ok)
        ok, _ = dataTypes.validate_relation_type("child")
        self.assertFalse(ok)

    def test_validate_vertex_ids_differ(self):
        ok, _ = dataTypes.validate_vertex_ids_differ(1, 2)
        self.assertTrue(ok)
        ok, msg = dataTypes.validate_vertex_ids_differ(3, 3)
        self.assertFalse(ok)
        self.assertIn("same id", msg)

