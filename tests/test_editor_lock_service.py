import time
import unittest

import editor_lock.service as lock_service


class FakeLockStore:
    def __init__(self):
        self.locks = {}

    def get_lock(self, tree_id):
        return self.locks.get(tree_id)

    def try_acquire(self, tree_id, user_id, expires_at, now):
        existing = self.locks.get(tree_id)
        if existing and int(existing.get("expiresAt", 0)) > now:
            return None
        lock = {
            "treeId": tree_id,
            "lockOwner": user_id,
            "acquiredAt": "now",
            "expiresAt": expires_at,
        }
        self.locks[tree_id] = lock
        return lock

    def release_lock(self, tree_id, user_id):
        existing = self.locks.get(tree_id)
        if not existing:
            return False
        if existing.get("lockOwner") != user_id:
            return False
        del self.locks[tree_id]
        return True

    def force_release(self, tree_id):
        if tree_id in self.locks:
            del self.locks[tree_id]
        return True


class EditorLockServiceTests(unittest.TestCase):
    def setUp(self):
        self.original_store = lock_service.editor_lock_store
        lock_service.editor_lock_store = FakeLockStore()

    def tearDown(self):
        lock_service.editor_lock_store = self.original_store

    def test_acquire_and_release(self):
        tree_id = "tree1"
        user_id = "user1"
        acquired, lock = lock_service.acquire_editor_lock(tree_id, user_id)
        self.assertTrue(acquired)
        self.assertEqual(lock.get("lockOwner"), user_id)

        released = lock_service.release_editor_lock(tree_id, user_id)
        self.assertTrue(released)

    def test_lock_conflict(self):
        tree_id = "tree2"
        user_id = "user1"
        other_user = "user2"
        lock_service.acquire_editor_lock(tree_id, user_id)
        acquired, lock = lock_service.acquire_editor_lock(tree_id, other_user)
        self.assertFalse(acquired)
        self.assertEqual(lock.get("lockOwner"), user_id)

    def test_expired_lock(self):
        tree_id = "tree3"
        user_id = "user1"
        now = int(time.time())
        lock_service.editor_lock_store.locks[tree_id] = {
            "treeId": tree_id,
            "lockOwner": user_id,
            "expiresAt": now - 1,
        }
        self.assertIsNone(lock_service.get_editor_lock(tree_id))



