from pathlib import Path

from napkon_string_matching.types.comparable_data import ComparableColumns
from napkon_string_matching.types.gecco_definition import Columns
from napkon_string_matching.types.gecco_definition_types.gecco_excel import \
    GeccoExcelDefinition


class GeccoPlusDefinition(GeccoExcelDefinition):
    """
    Hold definition read from GECCOplus definition files
    """

    @classmethod
    def read_original_format(cls, file: str | Path):
        column_mapping = {
            "ID": ComparableColumns.IDENTIFIER.value,
            "Kategorie": Columns.CATEGORY.value,
            "Data Item": Columns.PARAMETER.value,
            "Antwortausprägungen": Columns.CHOICES.value,
        }

        return super(cls, cls)._read_definition(
            file, column_mapping, choice_sep="\n", id_prefix="geccoplus_"
        )
