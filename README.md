# NAPKON String Matching

[![Python application](https://github.com/BIH-CEI/napkon-string-matching/actions/workflows/python-app.yml/badge.svg)](https://github.com/BIH-CEI/napkon-string-matching/actions/workflows/python-app.yml)
[![Docker](https://github.com/BIH-CEI/napkon-string-matching/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/BIH-CEI/napkon-string-matching/actions/workflows/docker-publish.yml)

## Usage

The script can be started from the command line like

```bash
python main.py [MODE] [OPTS..]
```

### Mode

The `MODE` argument allows to run the script in different modes. The default mode (if left out) is to generate matches between the cohorts specified in the configuration file (see below).

`--convert-validated-mapping XLSX_FILE` generates a mapping file from a validated mapping in `XLSX_FILE`. This generates a whitelist and blacklist file. The whitelist file contains all mappings marked valid with `1`. The blacklist respective contains all invalid mappings marked with `0`.

`--generate-mapping-result-table JSON_FILE` generates a tabular version of a mapping. The mapping is read from `JSON_FILE` and written as an XLSX file.

### Options

Options (`OPTS`) can change the default behavoir.

`--config CONFIG_FILE` sets the file to be used as configuration file (see below). If not specified `config.yml` is used.

`--output-dir OUTPUT_DIR` sets the output directory to `OUTPUT_DIR`. This defaults to the current directory. Depending on the mode this can generate additional sub-direcories.

`--output-name OUTPUT_NAME` configures the name of the output. Modes may use this to determine the file name of the output file.

## Docker

The script may be executed as a Docker container like:

```bash
docker run --rm \
  -v $(pwd):/configs \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/cache:/app/cache \
  ghcr.io/bih-cei/napkon-string-matching:main \
  [MODE] \
  --config /configs/config.yml \
  [OPTS..]
```

## Configuration

File format:

```yaml
prepare:
  terminology:
    mesh:
      db:
        host: <host>
        port: <port>
        db: <db name>
        user: <user>
        passwd: <password>

matching:
  score_threshold: <threshold (0.1,1.0]>
  cache_threshold: <threshold used for caching (0.1,1.0]>
  compare_column: Item | Sheet | File | Categories | Question | Options | Term | Tokens | TokenIds | TokenMatch | Identifier | Matches
  score_func: intersection_vs_union | fuzzy_match
  calculate_tokens: True | False
  filter_column: <column to filter by>
  filter_prefix: <prefix to be filtered by>
  tokens:
    timeout: <threshold>
    score_threshold: <timeout>
  variable_score_threshold: <threshold (0.1,1.0]>
  filter_categories: True | False

steps:
  - variables
  - gecco
  - questionnaires

input:
  base_dir: /base/dir

  gecco_definition:
    gecco83: $input_base_dir/gecco83_definition.xlsx
    geccoplus: $input_base_dir/geccoplus_definition.xlsx
    json: $input_base_dir/gecco_definition.json

  kds_definition:
    json: $input_base_dir/kds_definition.json
    simplifier:
      modules:
        - canonical_URL_moduleA
        - canonical_URL_moduleB

  dataset_definition: $input_base_dir/dataset_definition.json
  categories_file: $input_base_dir/categories.json
  categories_excel_file: $input_base_dir/categories.xlsx

  files:
    hap: $input_base_dir/file1.xlsx
    pop: $input_base_dir/file2.xlsx
    suep: $input_base_dir/file3.xlsx

  table_definitions: $input_base_dir/table_definitions.json
  mappings: <folder to existing mappings>

output_dir: output
cache_dir: cache
```
