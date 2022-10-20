import logging
import warnings
from pathlib import Path

import pandas as pd
from napkon_string_matching.types.dataset_definition import DatasetDefinition
from napkon_string_matching.types.dataset_table.dataset_table import (
    COLUMN_TEMP_TABLE,
    DATASETTABLE_COLUMN_QUESTION,
    DATASETTABLE_COLUMN_TYPE,
    DATASETTABLE_COLUMN_VARIABLE,
    DATASETTABLE_TYPE_HEADER,
    SheetParser,
)
from napkon_string_matching.types.dataset_table.definitions import (
    DatasetTableDefinitions,
    DatasetTablesDefinitions,
)

logger = logging.getLogger(__name__)


class DatasetTableExcelDefinitions(DatasetTableDefinitions):
    @classmethod
    def from_file(cls, file_name: str | Path, *args, **kwargs):
        """
        Read a xlsx file

        The contents are returned as a list of dictionaries containing the row contents
        and meta information.

        attr
        ---
            xlsx_file (str|Path): file to read

        returns
        ---
            Questionnaire: parsed result
        """

        logger.info("read from file %s...", str(file_name))

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            file = pd.ExcelFile(file_name, engine="openpyxl")
        sheet_names = file.sheet_names[2:]

        logger.info("...reading %i sheets...", len(sheet_names))

        parser = DefinitionsSheetParser()
        sheets = []
        for sheet_name in sheet_names:
            data_list = parser.parse(file, sheet_name, *args, **kwargs)
            if data_list is not None:
                sheets.append(data_list)

        if not sheets:
            logger.warn("...dit not get any entries")
            return None

        result = cls().concat(sheets)

        logger.info("...got entries")

        return result


class DatasetTablesExcelDefinitions(DatasetTablesDefinitions):
    def add_from_file(self, cohort: str, file_name: str | Path, *args, **kwargs):
        self[cohort] = DatasetTableExcelDefinitions.from_file(file_name, *args, **kwargs)


class DefinitionsSheetParser(SheetParser):
    def parse_rows(
        self,
        sheet: pd.DataFrame,
        sheet_name: str,
        main_table: str | None = None,
        dataset_definitions: DatasetDefinition | None = None,
        *args,
        **kwargs,
    ) -> DatasetTableExcelDefinitions:
        # Generate column with database table names
        sheet[COLUMN_TEMP_TABLE] = [
            main_table
            if pd.notna(type_) and type_ == DATASETTABLE_TYPE_HEADER
            else type_
            if pd.notna(type_) and all(entry not in type_ for entry in ["Group", "Matrix"])
            else None
            for type_ in sheet[DATASETTABLE_COLUMN_TYPE]
        ]
        sheet[COLUMN_TEMP_TABLE] = sheet[COLUMN_TEMP_TABLE].ffill()
        if main_table:
            sheet[COLUMN_TEMP_TABLE] = sheet[COLUMN_TEMP_TABLE].fillna(value=main_table)

        if dataset_definitions:
            # Update table name from dataset definitions
            sheet[COLUMN_TEMP_TABLE] = [
                dataset_definitions.get_correct_full_table_names(table, item)
                for table, item in zip(
                    sheet[COLUMN_TEMP_TABLE], sheet[DATASETTABLE_COLUMN_VARIABLE]
                )
            ]

        subgroup_map = {}
        for table in sheet[COLUMN_TEMP_TABLE].unique():
            if table and len(parts := table.split(":")) > 1:
                group = parts[0]
                if group not in subgroup_map:
                    subgroup_map[group] = []
                subgroup_map[group].append(parts[1])

        subgroups = {
            type_: question
            for question, type_ in zip(
                sheet[DATASETTABLE_COLUMN_QUESTION], sheet[DATASETTABLE_COLUMN_TYPE]
            )
            if pd.notna(type_) and type_.startswith("emnp")
        }

        result = DatasetTableExcelDefinitions(subgroup_names=subgroups, subgroups=subgroup_map)
        if main_table:
            result.groups[main_table] = sheet_name

        return result
