import unittest
from pathlib import Path

from napkon_string_matching.types.questionnaire import Columns, Questionnaire


class TestQuestionnaire(unittest.TestCase):
    def test_read_write(self):
        quest = Questionnaire(
            {
                "Identifier": ["1", "2", "3"],
                "words": ["one", "two", "three"],
                "arrays": [[1, "one"], [2, "two"], [3, "three"]],
            },
        )

        file = Path("test_" + __name__ + ".json")
        if file.exists():
            file.unlink()

        quest.write_json(file)
        result = Questionnaire.read_json(file)

        file.unlink()

        self.assertDictEqual(quest.to_dict(), result.to_dict())

    def test_gen_term(self):
        input_list = [
            (
                ["Header", "Subheader"],
                "This is a question",
                "This is an item with options",
            ),
            ([], "This is another question", "An item without categories"),
        ]
        expected_list = [
            [["Header", "Subheader"], "This is a question", "This is an item with options"],
            ["This is another question", "An item without categories"],
        ]

        for input, expected in zip(input_list, expected_list):
            categories, question, item = input

            result = Questionnaire.gen_term(
                categories,
                question,
                item,
            )
            self.assertEqual(expected, result)

    def test_add_terms(self):
        data = Questionnaire(
            [
                {
                    Columns.PARAMETER.value: "An item without categories",
                    Columns.SHEET.value: "Test Sheet",
                    Columns.FILE.value: "Testfile",
                    Columns.HEADER.value: None,
                    Columns.QUESTION.value: "This is a question",
                },
                {
                    Columns.PARAMETER.value: "An item without categories 1",
                    Columns.SHEET.value: "Test Sheet",
                    Columns.FILE.value: "Testfile",
                    Columns.HEADER.value: None,
                    Columns.QUESTION.value: "This is another question 1",
                },
            ]
        )

        data.add_terms()

        self.assertIsNotNone(data.term)
        self.assertEqual(2, len(data.term))
        self.assertEqual(["This is a question", "An item without categories"], data.term[0])
        self.assertEqual(
            ["This is another question 1", "An item without categories 1"], data.term[1]
        )
