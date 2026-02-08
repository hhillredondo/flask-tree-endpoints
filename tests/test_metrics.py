import unittest

from metrics import increment, snapshot


class MetricsTests(unittest.TestCase):
    def test_increment_and_snapshot(self):
        increment("auth_failure", {"reason": "missing_token"})
        increment("auth_failure", {"reason": "missing_token"})
        increment("auth_failure", {"reason": "role_denied", "role": "viewer"})

        data = snapshot()
        self.assertGreaterEqual(data.get("auth_failure|reason=missing_token", 0), 2)
        self.assertGreaterEqual(
            data.get("auth_failure|reason=role_denied,role=viewer", 0),
            1,
        )



