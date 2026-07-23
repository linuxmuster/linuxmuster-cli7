# students

Bulk operations on students.

## Usage

```
lmncli students COMMAND [OPTIONS]
```

## Commands

### `reset-internet`

Give access back to the internet management group for students who currently don't have it.

| Option | Description |
|---|---|
| `--schoolclass`, `-c` | Comma separated list of schoolclasses to restrict to (default: all students) |
| `--school`, `-s` | Target school (default: `default-school`) |

```
lmncli students reset-internet --schoolclass 7a,7b
```
