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
  compare_column: Item | Sheet | File | Categories | Question | Options | Term | Tokens | TokenIds | TokenMatch | Identifier | Matches
  score_func: intersection_vs_union

files:
  - file1.xlsx
  - file2.xlsx

```