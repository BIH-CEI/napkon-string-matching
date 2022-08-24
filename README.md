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
  score_threshold: <threshold>
  cache_threshold: <threshold used for caching>
  compare_column: Item | Sheet | File | Categories | Question | Options | Term | Tokens | TokenIds | TokenMatch | Identifier | Matches
  score_func: intersection_vs_union | fuzzy_match
  calculate_tokens: True | False
  filter_column: <column to filter by>
  filter_prefix: <prefix to be filtered by>
  tokens:
    timeout: <threshold>
    score_threshold: <timeout>

gecco_definitions:
  - gecco_definition.json

files:
  - file1.xlsx
  - file2.xlsx
```

## Docker

Run with

```bash
docker run --rm \
  -v $(pwd):/configs \
  -v $(pwd)/compared:/app/compared \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/prepared:/app/prepared \
  ghcr.io/bih-cei/napkon-string-matching:main \
  --config /configs/config.yml
```