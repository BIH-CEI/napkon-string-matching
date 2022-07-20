import unittest

from napkon_string_matching.prepare import MatchPreparator


class TestMatchPreparator(unittest.TestCase):
    def setUp(self):
        dbConfig = {
            "host": "localhost",
            "port": 5432,
            "db": "mesh",
            "user": "postgres",
            "passwd": "meshterms",
        }

        self.preparator = MatchPreparator(dbConfig)

    @unittest.skip("requires active db contianer")
    def test_load_terms(self):
        self.preparator.load_terms()
        self.assertIsNotNone(self.preparator.terms)
        self.assertIsNotNone(self.preparator.headings)
