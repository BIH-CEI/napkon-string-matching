# The script calculates the similarity ratio using the Levenshtein
# distance between the item names from SUEP, HAP and POP.

import logging
from pathlib import Path

import yaml

import napkon_string_matching
from napkon_string_matching.constants import LOG_FORMAT

logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    config = yaml.safe_load(Path("config.yml").read_text())

    napkon_string_matching.match(config)
