# keepass_diff

Compare two KeePass (`.kdbx`) databases entry by entry, with field-level diffs.

## How it works

1. Opens both KDBX files (supports KDBX3 and KDBX4, including Argon2d/AES-KDF)
2. Skips entries in the recycle bin
3. Matches entries by UUID first, then falls back to title+username for entries with different UUIDs
4. Produces a field-level diff for matched entries (title, username, password, URL, notes, tags, custom fields)
5. Reports entries unique to each database and group-level differences

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic comparison (prompted for passwords)

```bash
python keepass_diff.py personal.kdbx backup.kdbx
```

### Same password for both databases

```bash
python keepass_diff.py old.kdbx new.kdbx -p "MyMasterPassword"
```

### Different passwords

```bash
python keepass_diff.py work.kdbx home.kdbx --password-a "WorkPW" --password-b "HomePW"
```

### With key files

```bash
python keepass_diff.py db1.kdbx db2.kdbx --keyfile-a keys/db1.key --keyfile-b keys/db2.key
```

### Show actual password values (default: masked with `****`)

```bash
python keepass_diff.py old.kdbx new.kdbx -p "pw" --show-passwords
```

### Export as JSON

```bash
python keepass_diff.py old.kdbx new.kdbx -p "pw" -f json -o report.json
```

### Export as HTML report

```bash
python keepass_diff.py old.kdbx new.kdbx -p "pw" -f html -o report.html
```

## Output formats

| Format    | Flag           | Description                                    |
|-----------|----------------|------------------------------------------------|
| `console` | `-f console`   | Colored terminal output (default)              |
| `json`    | `-f json`      | Machine-readable JSON                          |
| `html`    | `-f html`      | Self-contained dark-themed HTML report         |

## Entry matching strategy

Entries are matched in two passes:

1. **UUID match** — the most reliable, since KeePass assigns a unique UUID to each entry at creation time. Two entries with the same UUID are definitively the same entry, even if title/username changed.
2. **Title+Username fallback** — for entries not matched by UUID (e.g., comparing databases that were created independently rather than forked from the same file). Case-insensitive.

## Compared fields

- Title, Username, Password, URL, Notes
- Tags, Icon, Expiry time, OTP
- All custom string fields (prefixed with `custom:`)

## Security notes

- Passwords are masked by default in all output formats
- The tool operates read-only on both databases — nothing is modified
- Credentials are never written to disk or logged
- If passing passwords via CLI args, be aware they may appear in shell history
