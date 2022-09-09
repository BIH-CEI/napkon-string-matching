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
            "Header item options question Subheader".split(),
            "another categories item question without".split(),
        ]

        for input, expected in zip(input_list, expected_list):
            categories, question, item = input

            result = Questionnaire.gen_term(
                categories,
                question,
                item,
                language="english",
            )
            self.assertEqual(expected, result)

    def test_gen_term_german(self):
        input_list = [
            (["Einschlusskriterien!"], "[Ursache]", "Andere Ursache, bitte angeben:"),
            (
                ["Patienteninformationen"],
                "Hatte der/die Patient*in in den letzten 14 Tagen vor Beginn seiner/ihrer \
                    Beschwerden wissentlich Kontakt mit einer wahrscheinlich oder \
                    nachgewiesenermaßen mit SARS-CoV-2 infizierten Person?",
                "Hatte der/die Patient*in in den letzten 14 Tagen vor Beginn seiner/ihrer \
                    Beschwerden wissentlich Kontakt mit einer wahrscheinlich oder \
                    nachgewiesenermaßen mit SARS-CoV-2 infizierten Person?",
            ),
            (
                ["Patienteninformationen"],
                "Welche Altersgruppen gibt es im Haushalt?",
                "Wieviele Kinder <1",
            ),
        ]

        expected_list = [
            "angeben bitte Einschlusskriterien Ursache".split(),
            "14 Beginn Beschwerden der/die infizierten Kontakt letzten nachgewiesenermaßen Patient \
                Patienteninformationen Person SARS-CoV-2 seiner/ihrer Tagen wahrscheinlich \
                wissentlich".split(),
            "1 < Altersgruppen gibt Haushalt Kinder Patienteninformationen Wieviele".split(),
        ]

        for input, expected in zip(input_list, expected_list):
            categories, question, item = input

            result = Questionnaire.gen_term(
                categories,
                question,
                item,
                language="german",
            )

            self.assertEqual(expected, result)

    def test_add_terms(self):
        data = Questionnaire(
            [
                {
                    Columns.ITEM.value: "An item without categories",
                    Columns.SHEET.value: "Test Sheet",
                    Columns.FILE.value: "Testfile",
                    Columns.HEADER.value: None,
                    Columns.QUESTION.value: "This is a question",
                },
                {
                    Columns.ITEM.value: "An item without categories 1",
                    Columns.SHEET.value: "Test Sheet",
                    Columns.FILE.value: "Testfile",
                    Columns.HEADER.value: None,
                    Columns.QUESTION.value: "This is another question 1",
                },
            ]
        )

        data.add_terms(language="english")

        self.assertIsNotNone(data.term)
        self.assertEqual(2, len(data.term))
        self.assertEqual("categories item question without".split(), data.term[0])
        self.assertEqual("1 another categories item question without".split(), data.term[1])
