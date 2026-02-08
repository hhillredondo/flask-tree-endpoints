import unittest

from partition.manager import PartitionManager


class PartitionManagerTests(unittest.TestCase):
    def test_generate_and_parse_partition_key(self):
        user_id = "user_123"
        tree_id = "tree-456"
        key = PartitionManager.generate_partition_key(user_id, tree_id)
        parsed_user, parsed_tree = PartitionManager.parse_partition_key(key)
        self.assertEqual(parsed_user, user_id)
        self.assertEqual(parsed_tree, tree_id)

    def test_validate_partition_key(self):
        self.assertTrue(PartitionManager.validate_partition_key("user_tree"))
        self.assertFalse(PartitionManager.validate_partition_key(""))
        self.assertFalse(PartitionManager.validate_partition_key("no-underscore"))



