# NAPKON String Matching

[![Python application](https://github.com/BIH-CEI/napkon-string-matching/actions/workflows/python-app.yml/badge.svg)](https://github.com/BIH-CEI/napkon-string-matching/actions/workflows/python-app.yml)
[![Docker](https://github.com/BIH-CEI/napkon-string-matching/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/BIH-CEI/napkon-string-matching/actions/workflows/docker-publish.yml)

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

steps:
  - variables
  - gecco
  - questionnaires

gecco_definition:
  gecco83: gecco83_definition.xlsx
  geccoplus: geccoplus_definition.xlsx
  json: gecco_definition.json

files:
  hap: file1.xlsx
  pop: file2.xlsx
  suep: file3.xlsx

mappings: <folder to existing mappings>
```

## Docker

Run with

```bash
docker run --rm \
  -v $(pwd):/configs \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/cache:/app/cache \
  ghcr.io/bih-cei/napkon-string-matching:main \
  --config /configs/config.yml
```