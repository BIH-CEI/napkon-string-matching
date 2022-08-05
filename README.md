# NAPKON String Matching

## Configuration

File format:

```yaml
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

files:
  - file1.xlsx
  - file2.xlsx
```