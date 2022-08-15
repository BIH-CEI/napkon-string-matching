import unittest

from napkon_string_matching.prepare.generate import gen_term


class TestGenTerm(unittest.TestCase):
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

            result = gen_term(
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

            result = gen_term(
                categories,
                question,
                item,
                language="german",
            )

            self.assertEqual(expected, result)


if __name__ == "__main__":
    unittest.main()
