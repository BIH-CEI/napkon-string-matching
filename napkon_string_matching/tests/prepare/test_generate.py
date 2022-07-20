import json
import unittest
from pathlib import Path

import pandas as pd
from napkon_string_matching.constants import (
    DATA_COLUMN_CATEGORIES,
    DATA_COLUMN_FILE,
    DATA_COLUMN_ITEM,
    DATA_COLUMN_OPTIONS,
    DATA_COLUMN_QUESTION,
    DATA_COLUMN_SHEET,
)
from napkon_string_matching.prepare import gen_term, gen_token


class TestGenToken(unittest.TestCase):
    def test_gen_token(self):
        data_dir = Path("napkon_string_matching/tests/prepare/data")

        references = pd.DataFrame(
            json.loads((data_dir / "references.json").read_text())
        )
        headings = pd.DataFrame(json.loads((data_dir / "headings.json").read_text()))

        term = "Dialyse nach Entlassung"
        result = gen_token(term, references, headings, score_threshold=90)
        self.assertIsNotNone(result)
        self.assertIn("terms", result)
        self.assertEqual(len(result["terms"]), 1)
        self.assertIn("Dialyse", result["terms"])

    def test_gen_term(self):
        input_list = [
            pd.Series(
                {
                    DATA_COLUMN_ITEM: "This is an item with options",
                    DATA_COLUMN_SHEET: "Test Sheet",
                    DATA_COLUMN_FILE: "Testfile",
                    DATA_COLUMN_CATEGORIES: ["Header", "Subheader"],
                    DATA_COLUMN_QUESTION: "This is a question",
                    DATA_COLUMN_OPTIONS: ["Option A", "Option B"],
                },
            ),
            pd.Series(
                {
                    DATA_COLUMN_ITEM: "An item without categories",
                    DATA_COLUMN_SHEET: "Test Sheet",
                    DATA_COLUMN_FILE: "Testfile",
                    DATA_COLUMN_CATEGORIES: None,
                    DATA_COLUMN_QUESTION: "This is another question",
                },
            ),
        ]
        expected_list = [
            "Header Subheader This is a question This is an item with options",
            "This is another question An item without categories",
        ]

        for input, expected in zip(input_list, expected_list):
            result = gen_term(input)
            self.assertEqual(expected, result)


if __name__ == "__main__":
    unittest.main()