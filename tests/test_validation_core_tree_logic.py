import unittest

from validation import coreTreeLogic as ctl


class ValidationCoreTreeLogicTests(unittest.TestCase):
    def test_validate_life_date_order(self):
        self.assertTrue(ctl.validate_life_date_order("2000-01-01T00:00:00Z", "2020-01-01T00:00:00Z")[0])
        self.assertFalse(ctl.validate_life_date_order("2020-01-01T00:00:00Z", "2000-01-01T00:00:00Z")[0])

    def test_validate_max_lifespan(self):
        self.assertTrue(ctl.validate_max_lifespan("1900-01-01T00:00:00Z", "2000-01-01T00:00:00Z")[0])
        self.assertFalse(ctl.validate_max_lifespan("1800-01-01T00:00:00Z", "2000-01-01T00:00:00Z")[0])

    def test_validate_parents_number(self):
        self.assertTrue(ctl.validate_parents_number(0)[0])
        self.assertFalse(ctl.validate_parents_number(1)[0])
        self.assertFalse(ctl.validate_parents_number(2)[0])

    def test_validate_parent_is_alive_and_fertile(self):
        ok, _ = ctl.validate_parent_is_alive_and_fertile(
            "female",
            "1980-01-01T00:00:00Z",
            "",
            "2010-01-01T00:00:00Z",
        )
        self.assertTrue(ok)

        ok, _ = ctl.validate_parent_is_alive_and_fertile(
            "female",
            "1980-01-01T00:00:00Z",
            "1990-01-01T00:00:00Z",
            "2010-01-01T00:00:00Z",
        )
        self.assertFalse(ok)

    def test_validate_heterosexual_marriage(self):
        self.assertTrue(ctl.validate_heterosexual_marriage("male", "female")[0])
        self.assertFalse(ctl.validate_heterosexual_marriage("male", "male")[0])

    def test_validate_siblings_birth_dates(self):
        ok, _ = ctl.validate_siblings_birth_dates(
            "2020-01-01T00:00:00Z",
            ["2010-01-01T00:00:00Z", "2012-01-01T00:00:00Z"],
        )
        self.assertTrue(ok)

        ok, _ = ctl.validate_siblings_birth_dates(
            "2020-01-01T00:00:00Z",
            ["2019-08-01T00:00:00Z"],
        )
        self.assertFalse(ok)

    def test_validate_groom_and_bride_single_status(self):
        ok, _ = ctl.validate_groom_and_bride_single_status(
            "2020-01-01T00:00:00Z",
            [],
            [],
        )
        self.assertTrue(ok)

        ok, _ = ctl.validate_groom_and_bride_single_status(
            "2020-01-01T00:00:00Z",
            [{"married": "2010-01-01T00:00:00Z", "divorced": None}],
            [],
        )
        self.assertFalse(ok)

    def test_verify_legal_marriage_age(self):
        self.assertTrue(ctl.verify_legal_marriage_age("2000-01-01T00:00:00Z", "2018-01-01T00:00:00Z")[0])
        self.assertFalse(ctl.verify_legal_marriage_age("2010-01-01T00:00:00Z", "2018-01-01T00:00:00Z")[0])

    def test_verify_marriage_divorce_date_order(self):
        self.assertTrue(ctl.verify_marriage_divorce_date_order("2010-01-01T00:00:00Z", "2020-01-01T00:00:00Z")[0])
        self.assertFalse(ctl.verify_marriage_divorce_date_order("2020-01-01T00:00:00Z", "2010-01-01T00:00:00Z")[0])

    def test_verify_common_children_born_in_marriage(self):
        ok, _ = ctl.verify_common_children_born_in_marriage(
            ["2015-01-01T00:00:00Z"],
            "2010-01-01T00:00:00Z",
            None,
        )
        self.assertTrue(ok)

        ok, _ = ctl.verify_common_children_born_in_marriage(
            ["2005-01-01T00:00:00Z"],
            "2010-01-01T00:00:00Z",
            None,
        )
        self.assertFalse(ok)

    def test_verify_member_is_deletable(self):
        self.assertTrue(ctl.verify_member_is_deletable(0)[0])
        self.assertFalse(ctl.verify_member_is_deletable(2)[0])

