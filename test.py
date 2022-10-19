import unittest

import main


# unit tests for the list_years function in main
class TestListYears(unittest.TestCase):

    # generates list from 1948 (minimum year in BLS data) to 2022
    def test_2022_default(self):
        self.assertEqual([1948, 1965, 1984, 2003, 2022], main.list_years(1948, 2022))

    # generates list from 1948 to 2048
    def test_2048_default(self):
        self.assertEqual([1948, 1953, 1972, 1991, 2010, 2029, 2048], main.list_years(1948, 2048))

    # generates list for case of 20 year difference
    def test_20_year_diff(self):
        self.assertEqual([2002, 2003, 2022], main.list_years(2002, 2022))

    # generates list for case of 19 year difference
    def test_19_year_diff(self):
        self.assertEqual([2003, 2022], main.list_years(2003, 2022))

    # generates list for case of 1 year difference
    def test_0_year_diff(self):
        self.assertEqual([2022], main.list_years(2022, 2022))

    # tests that a ValueError is raised when min_year > max_year
    def test_min_greater_than_max(self):
        try:
            main.list_years(2023, 2022)
        except ValueError as e:
            self.assertEqual("min_year must be less than or equal to max_year", str(e))
        else:
            raise AssertionError("ValueError was expected but not raised")


if __name__ == '__main__':
    unittest.main()
