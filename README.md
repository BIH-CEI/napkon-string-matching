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
  score_func: intersection_vs_union
  calculate_tokens: True | False

files:
  - file1.xlsx
  - file2.xlsx
```