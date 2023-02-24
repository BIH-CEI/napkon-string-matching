import logging
from enum import Enum
from pathlib import Path

import pandas as pd

import napkon_string_matching.types.comparable as comp
from napkon_string_matching.types.base.writable_excel import WritableExcel
from napkon_string_matching.types.category import Category
from napkon_string_matching.types.comparable_data import ComparableColumns, ComparableData


class Columns(Enum):
    CATEGORY = "Category"
    PARAMETER = "Parameter"


logger = logging.getLogger(__name__)


class KdsBase:
    __columns__ = list(ComparableColumns) + list(Columns)
    __category_column__ = Columns.CATEGORY.value


class KdsCategory(KdsBase, Category):
    pass


class KdsDefinition(KdsBase, ComparableData, WritableExcel):
    __column_mapping__ = {ComparableColumns.IDENTIFIER.value: comp.Columns.VARIABLE.value}
    __category_type__ = KdsCategory

    def concat(self, other):
        if not isinstance(other, KdsDefinition):
            raise TypeError(
                "'other' should be of type '{}' but is of type '{}'".format(
                    type(self).__name__, type(other).__name__
                )
            )

        return KdsDefinition(pd.concat([self._data, other._data], ignore_index=True))

    def add_terms(self, language: str = "german"):
        logger.info("add terms...")
        result = [
            self.gen_term(category, parameter)
            for category, parameter in zip(self.category, self.parameter)
        ]
        self.term = result
        logger.info("...done")

    @classmethod
    def read_original_format(cls, file_name: str | Path, *args, **kwargs):
        return cls.read_json(file_name, *args, **kwargs)

    def to_csv(self) -> str:
        return self.stringify_list_columns()

    def get_items(self):
        return [("Sheet1", self.stringify_list_columns())]

    def stringify_list_columns(self):
        gecco = KdsDefinition(self.dataframe().copy(deep=True))
        gecco.choices = [
            " | ".join(choice) if isinstance(choice, list) else choice for choice in gecco.choices
        ]
        return gecco
