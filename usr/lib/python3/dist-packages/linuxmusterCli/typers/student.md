# student

Manage a student's linked parent accounts.

## Usage

```
lmncli student STUDENT [OPTIONS]
```

Options must be given **before** the `STUDENT` argument, or Typer will misparse a trailing `--option` as an unknown subcommand.

| Option | Description |
|---|---|
| `STUDENT` (argument, required) | Login of the student |
| `--parents` | List the student's linked parents |
| `--add-parents` | Comma separated list of parent logins to link |
| `--remove-parents` | Comma separated list of parent logins to unlink |
| `--school`, `-s` | Target school (default: `default-school`) |

`--add-parents`/`--remove-parents` imply `--parents` (the resulting parent list is shown after the change). If one parent in the list fails, the remaining ones in that same batch are not processed.

```
lmncli student --add-parents johndoe-parent johndoe
lmncli student --parents johndoe
```
