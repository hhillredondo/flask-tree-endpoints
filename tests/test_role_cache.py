import unittest
from unittest import mock

import roles.service as role_service


class RoleCacheTests(unittest.TestCase):
    def test_role_cache_hit(self):
        tree_id = "tree1"
        user_id = "user1"

        with mock.patch.object(role_service, "acl_store") as store:
            store.get_role.return_value = "viewer"
            role = role_service.get_user_role(tree_id, user_id)
            self.assertEqual(role, "viewer")

            # Second call should hit cache
            role = role_service.get_user_role(tree_id, user_id)
            self.assertEqual(role, "viewer")
            store.get_role.assert_called_once_with(tree_id, user_id)

    def test_invalidate_role_cache(self):
        tree_id = "tree2"
        user_id = "user2"
        with mock.patch.object(role_service, "acl_store") as store:
            store.get_role.return_value = "editor"
            role_service.get_user_role(tree_id, user_id)
            role_service.invalidate_role_cache(tree_id, user_id)
            role_service.get_user_role(tree_id, user_id)
            self.assertEqual(store.get_role.call_count, 2)



