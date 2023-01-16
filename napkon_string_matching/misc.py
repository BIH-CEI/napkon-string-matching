import logging
from pathlib import Path
from typing import Dict

import pandas as pd

from napkon_string_matching.matcher import Matcher
from napkon_string_matching.types.comparable_data import Columns
from napkon_string_matching.types.dataset_table.dataset_table import DatasetTable
from napkon_string_matching.types.mapping import Mapping
from napkon_string_matching.types.mapping_types.matched_mapping import MatchedMapping

LABEL_ID = "Id"
LABEL_COHORT = "Kohorte"

logger = logging.getLogger(__name__)


def get_all_table_subgroup_name_combinations(dataset_tables: Dict[str, DatasetTable]):
    """
    Get a dictionary containing all subgroups and their groups a human readable name
    for each DatasetTable.
    """
    result = {}
    for name, dataset_table in dataset_tables.items():
        result[name] = {}
        for group, subgroups in dataset_table.subgroups.items():
            result[name][dataset_table.groups[group]] = [
                dataset_table.subgroup_names[subgroup] for subgroup in subgroups
            ]
    return result


def get_match_result_table(
    matcher: Matcher, mappings_file: str | Path, left_name: str, right_name: str
):
    mapping = Mapping.read_json(mappings_file)
    return _expand_matches(mapping, matcher, left_name, right_name)


def _expand_matches(mapping: Mapping, matcher: Matcher, left_name: str, right_name: str):
    rows_left = _fill_from_questionnaire(left_name, mapping, matcher)
    rows_right = _fill_from_questionnaire(right_name, mapping, matcher)

    result = pd.concat([rows_left, rows_right], ignore_index=True)
    result = result.sort_values(by=[LABEL_ID, LABEL_COHORT])

    return result


def _fill_from_questionnaire(name: str, mapping: Mapping, matcher: Matcher) -> pd.DataFrame:
    df = _generate_mapping_id_df(mapping, name)

    questionnaire = matcher.questionnaires[name]
    columns = [Columns.IDENTIFIER.value, Columns.SHEET.value, Columns.PARAMETER.value]
    questionnaire = questionnaire[columns]

    return df.merge(
        questionnaire, left_on=Columns.IDENTIFIER.value, right_on=Columns.IDENTIFIER.value
    )


def _generate_mapping_id_df(mapping: Mapping, name: str) -> pd.DataFrame:
    id_mappings = []
    for id, group in mapping:
        try:
            for entry in group[name]:
                id_mappings.append(
                    {LABEL_ID: id, LABEL_COHORT: name.upper(), Columns.IDENTIFIER.value: entry}
                )
        except KeyError:
            logger.warning("could not find group '%s' for id '%s'", name, id)
            continue
    return pd.DataFrame(id_mappings)


def convert_validated_mapping_to_json(
    validated_mapping: str, output_dir: str | Path | None, name: str = "mapping"
):
    """
    Convert a validated mapping from a XLSX file and produce the JSON version. The validated
    mapping has columns for each potential mapping that states if this is a valid mapping (=1)
    or not (=0). The JSON output consits of a `whitelist` and a `blacklist` that contains valid
    mappings resp. invalid mappings.
    """

    output_dir = Path(output_dir) if output_dir else Path()

    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    # Read validated mapping from file
    blacklist = MatchedMapping.read_excel(validated_mapping, match_value=0, combine_entries=False)
    whitelist = MatchedMapping.read_excel(validated_mapping)

    outputdir_black = output_dir / "blacklist"
    outputdir_white = output_dir / "whitelist"

    if not outputdir_black.exists():
        outputdir_black.mkdir()
    if not outputdir_white.exists():
        outputdir_white.mkdir()

    outputfile_black = outputdir_black / (name + ".json")
    outputfile_white = outputdir_white / (name + ".json")

    # Update the existing mapping if exists
    if outputfile_black.exists():
        mapping = Mapping.read_json(outputfile_black)
        mapping.add_values(blacklist)
        blacklist = mapping
    if outputfile_white.exists():
        mapping = Mapping.read_json(outputfile_white)
        mapping.update_values(whitelist)
        whitelist = mapping

    blacklist.write_json(outputfile_black)
    whitelist.write_json(outputfile_white)
