import logging
from pathlib import Path
from typing import Dict

import pandas as pd

from napkon_string_matching.matcher import Matcher
from napkon_string_matching.matching import create_matcher
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


def generate_combined_mapping(mapping_dir: str | Path, output_dir: str | Path):
    mapping_dir = Path(mapping_dir)
    output_file = Path(output_dir) / "mapping_combined.json"

    mappings = Mapping()
    for file in mapping_dir.glob("*.json"):
        mapping = Mapping.read_json(file)
        mappings.update(mapping)

    mappings.write_json(output_file)


def generate_mapping_result_table(
    mappings_file: str, config: Dict, output_dir: str, output_name: str = "mapping"
):
    """
    Generate a XLSX file containing a tabular version of the mapping of `mappings_file`.
    """
    matcher = create_matcher(config, use_cache=True)
    output_file = Path(output_dir) / (output_name + ".xlsx")
    with pd.ExcelWriter(output_file) as writer:
        result = get_match_result_table(
            matcher,
            mappings_file,
        )
        logger.info("write mappings to file %s", str(output_file))
        result.to_excel(writer, sheet_name=output_name, index=False)


def get_match_result_table(matcher: Matcher, mappings_file: str | Path):
    mapping = Mapping.read_json(mappings_file)
    return _expand_matches(mapping, matcher)


def _expand_matches(mapping: Mapping, matcher: Matcher):
    group_names = mapping.get_group_names()

    rows = []
    for group_name in group_names:
        rows.append(_fill_from_questionnaire(group_name, mapping, matcher))

    result = pd.concat(rows, ignore_index=True)
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
    validated_mapping: str,
    id_reference_file: str | Path | None,
    output_dir: str | Path | None,
    name: str = "mapping",
):
    """
    Convert a validated mapping from a XLSX file and produce the JSON version. The validated
    mapping has columns for each potential mapping that states if this is a valid mapping (=1)
    or not (=0). The JSON output consits of a `whitelist` and a `blacklist` that contains valid
    mappings resp. invalid mappings.
    """

    id_reference = Mapping()
    if id_reference_file:
        id_reference = Mapping.read_json(id_reference_file)

    output_dir = Path(output_dir) if output_dir else Path()

    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    # Read validated mapping from file
    blacklist = MatchedMapping.read_excel(validated_mapping, match_value=0, combine_entries=False)
    whitelist = MatchedMapping.read_excel(validated_mapping, id_reference=id_reference)

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


def print_statistics(config: Dict):
    matcher = create_matcher(config)

    cohorts = {name: len(questionnaire) for name, questionnaire in matcher.questionnaires.items()}
    num_per_cohort_str = ", ".join(
        [f"{name.upper()}: {length}" for name, length in cohorts.items()]
    )

    # Calcualte the total by getting all combinations excluding combinations
    # with it own and duplicates related to order, e.g. (A,B) and (B,A).
    total_number_cohorts = []
    list_ = cohorts.copy()
    while len(list_) > 1:
        # Avoid comparison against the same item multiple times by popping
        # it from the list
        cur_name, cur_length = list_.popitem()
        total_number_cohorts += [cur_length * length for length in list_.values()]
    total_number_cohorts = sum(total_number_cohorts)

    verified_mappings = matcher.mappings_whitelist.num_entries_repr()
    excluded_mappings = matcher.mappings_blacklist.num_entries_repr()
    num_verified_mappings = matcher.mappings_whitelist.num_entries_groups()

    # Calcualte the number of comparisons after mappings have been excluded
    comps_reduced = []
    while len(cohorts) > 1:
        cur_name, cur_length = cohorts.popitem()
        for name, length in cohorts.items():
            # The number of reduced entries is calculated by multiplying the
            # number of reduced entries for one questionnaire with the total
            # number of entries in the other questionnaire. This is done in
            # both directions
            reduced = (
                cur_length * num_verified_mappings.get(name, 0)
                + num_verified_mappings.get(cur_name, 0) * length
            )
            comps_reduced.append(reduced)
    comps_reduced = sum(comps_reduced)

    longest_entry = f"entries in Datensatztabelle: {num_per_cohort_str}"
    devider = len(longest_entry) * "-"

    print(devider)
    print(longest_entry)
    print(f"potential number of comparisons: {total_number_cohorts:,}")
    print(devider)
    print(f"verified {verified_mappings}")
    print(f"excluded {excluded_mappings}")
    print(devider)
    print(f"reduced no. of comparisons about {comps_reduced:,}")
    print(f"no. of potential comparisons: {total_number_cohorts-comps_reduced:,}")
    print(devider)
