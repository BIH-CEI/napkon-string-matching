import json
import unittest
from pathlib import Path

import pandas as pd
from napkon_string_matching.constants import (
    DATA_COLUMN_CATEGORIES,
    DATA_COLUMN_FILE,
    DATA_COLUMN_ITEM,
    DATA_COLUMN_QUESTION,
    DATA_COLUMN_SHEET,
    DATA_COLUMN_TERM,
)
from napkon_string_matching.files.dataset_table import read
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
        self.test_file = Path("hap_test.xlsx")

    @unittest.skip("requires active db contianer")
    def test_load_terms(self):
        self.preparator.load_terms()
        self.assertIsNotNone(self.preparator.terms)
        self.assertIsNotNone(self.preparator.headings)

    def test_add_terms(self):
        QUESTION = "This is another question"
        ITEM = "An item without categories"

        data = pd.DataFrame(
            [
                {
                    DATA_COLUMN_ITEM: ITEM,
                    DATA_COLUMN_SHEET: "Test Sheet",
                    DATA_COLUMN_FILE: "Testfile",
                    DATA_COLUMN_CATEGORIES: None,
                    DATA_COLUMN_QUESTION: QUESTION,
                },
                {
                    DATA_COLUMN_ITEM: ITEM + "1",
                    DATA_COLUMN_SHEET: "Test Sheet",
                    DATA_COLUMN_FILE: "Testfile",
                    DATA_COLUMN_CATEGORIES: None,
                    DATA_COLUMN_QUESTION: QUESTION + "1",
                },
            ]
        )

        self.preparator.add_terms(data)

        self.assertIn(DATA_COLUMN_TERM, data)
        self.assertEqual(2, len(data[DATA_COLUMN_TERM].values))
        self.assertEqual(f"{QUESTION} {ITEM}", data[DATA_COLUMN_TERM].values[0])
        self.assertEqual(f"{QUESTION}1 {ITEM}1", data[DATA_COLUMN_TERM].values[1])

    @unittest.skip("requires active db contianer and test file")
    def test_add_terms_live(self):
        data = read(self.test_file)

        self.preparator.add_terms(data)
        self.assertIn(DATA_COLUMN_TERM, data)
