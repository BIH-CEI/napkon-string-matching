# The script calculates the similarity ratio using the Levenshtein
# distance between the item names from SUEP, HAP and POP.

import logging
from argparse import ArgumentParser
from pathlib import Path

import yaml

from napkon_string_matching import matching
from napkon_string_matching.constants import LOG_FORMAT

logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def get_args():
    parser = ArgumentParser()

    parser.add_argument("--config", default="config.yml")

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = get_args()

    config = yaml.safe_load(Path(args.config).read_text())

    matching.match(config)
