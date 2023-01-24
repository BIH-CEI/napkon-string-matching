# The script calculates the similarity ratio using the Levenshtein
# distance between the item names from SUEP, HAP and POP.

import logging
from argparse import ArgumentParser
from pathlib import Path

import yaml

from napkon_string_matching import matching
from napkon_string_matching.constants import LOG_FORMAT
from napkon_string_matching.misc import (
    convert_validated_mapping_to_json,
    generate_combined_mapping,
    generate_mapping_result_table,
    print_statistics,
)

logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def get_args():
    parser = ArgumentParser()

    parser.add_argument("--config", default="config.yml")
    parser.add_argument("--no-cache", action="store_true", default=False)

    parser.add_argument("--convert-validated-mapping", help="XLSX file to be converted")
    parser.add_argument("--id-reference", help="file to look up ids for mappings")
    parser.add_argument(
        "--generate-combined-mapping", help="generate a combination of all mappings"
    )
    parser.add_argument("--generate-mapping-result-table", help="mapping file used to generation")
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--output-name")

    parser.add_argument("--print-statistics", action="store_true")

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = get_args()

    config = yaml.safe_load(Path(args.config).read_text())

    if args.convert_validated_mapping:
        logger.info("convert validated matching to JSON")
        convert_validated_mapping_to_json(
            args.convert_validated_mapping, args.id_reference, args.output_dir, args.output_name
        )
    elif args.generate_combined_mapping:
        logger.info("generate combined mapping")
        generate_combined_mapping(args.generate_combined_mapping, args.output_dir)
    elif args.generate_mapping_result_table:
        logger.info("generate mapping result table")
        generate_mapping_result_table(
            args.generate_mapping_result_table, config, args.output_dir, args.output_name
        )
    elif args.print_statistics:
        print_statistics(config)
    else:
        logger.info("generate matching")
        matching.match(config, use_cache=not args.no_cache)
