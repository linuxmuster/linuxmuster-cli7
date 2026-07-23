# schoolclass

Manage schoolclasses' teacher/student/parent subgroups.

## Usage

```
lmncli schoolclass COMMAND [OPTIONS]
```

## Commands

### `sync`

Update the `-teachers`, `-students`, and/or `-parents` subgroups of one or more schoolclasses from their current membership.

| Option | Description |
|---|---|
| `--schoolclass`, `-c` | Comma separated list of schoolclasses to sync |
| `--teachers` | Sync the teachers subgroup |
| `--students` | Sync the students subgroup |
| `--parents` | Sync the parents subgroup |
| `--groups` | Sync all three subgroups |
| `--all` | Sync all three subgroups for every schoolclass |
| `--school`, `-s` | Target school (default: `default-school`) |

Requires either `--schoolclass` or `--all`, and at least one of `--teachers`/`--students`/`--parents`/`--groups` when using `--schoolclass`.

```
lmncli schoolclass sync --schoolclass 7a --groups
lmncli schoolclass sync --all
```

### `teachers`

Print schoolclasses' teacher memberships.

| Option | Description |
|---|---|
| `--schoolclass`, `-c` | Comma separated list of schoolclasses (default: all) |
| `--school`, `-s` | Target school (default: `default-school`) |

```
lmncli schoolclass teachers --schoolclass 7a,7b
```
