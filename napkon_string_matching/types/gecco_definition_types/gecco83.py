from pathlib import Path

from napkon_string_matching.types.comparable_data import ComparableColumns
from napkon_string_matching.types.gecco_definition import Columns
from napkon_string_matching.types.gecco_definition_types.gecco_excel import GeccoExcelDefinition


class Gecco83Definition(GeccoExcelDefinition):
    @classmethod
    def read_original_format(cls, file: str | Path):
        column_mapping = {
            "ID": ComparableColumns.IDENTIFIER.value,
            "KATEGORIE": Columns.CATEGORY.value,
            "PARAMETER CASE REPORT FORM": Columns.PARAMETER.value,
            "ANTWORT-MÖGLICHKEITEN": Columns.CHOICES.value,
        }

        return super(cls, cls)._read_definition(
            file, column_mapping, choice_sep="|", id_prefix="gecco_"
        )
