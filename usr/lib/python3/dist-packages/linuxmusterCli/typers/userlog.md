# userlog

Parse sophomorix userlogs and list users added, killed, or updated over the past year.

## Usage

```
lmncli userlog [OPTIONS]
```

| Option | Description |
|---|---|
| `--school`, `-s` | Target school (default: `default-school`) |
| `--added`, `-a` | Show added users |
| `--killed`, `-k` | Show killed users |
| `--updated`, `-u` | Show updated users |
| `--today`, `-t` | Only today's changes |
| `--lastweek`, `-lw` | Only last week's changes |
| `--last`, `-l` | Only the most recent logged run (requires `-a`/`-k`/`-u`) |
| `--list-changes`, `-c` | Include the detailed list of changed attributes (slower) |
| `--all` | Show the full log history |

Passing none of `--added`/`--killed`/`--updated` shows all three. `--all`, `--today`, and `--lastweek` are mutually exclusive.

```
lmncli userlog --killed --today
lmncli userlog --updated --list-changes
```
