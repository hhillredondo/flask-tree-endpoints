import unittest

from flask import Flask

from validation.performValidations import perform_validations


class PerformValidationsTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.testing = True

    def test_perform_validations_success(self):
        with self.app.app_context():
            result = perform_validations([
                (lambda: (True, ""), []),
            ])
            self.assertIsNone(result)

    def test_perform_validations_failure(self):
        def failing():
            return False, "Bad input"

        with self.app.app_context():
            response, status = perform_validations([
                (failing, []),
            ])
            self.assertEqual(status, 400)
            self.assertEqual(response.get_json().get("error"), "Bad input")

