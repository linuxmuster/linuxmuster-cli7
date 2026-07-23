# user

Show a single user's details.

## Usage

```
lmncli user [OPTIONS] [USER]
```

Options must be given **before** the `USER` argument, or Typer will misparse a trailing `--option` as an unknown subcommand.

| Option | Description |
|---|---|
| `USER` (argument, optional) | Login of the user to show (append `-exam` for an exam account) |
| `--school`, `-s` | Target school (omit to search across the router's default scope) |
| `--full`, `-f` | Print the raw attribute dict instead of the default detailed table layout |
| `--check-first-pw`, `-c` | Also report whether the first (initial) password is still set |

By default (without `--full`) the command renders the detailed multi-table view (person info, groups, quotas, samba attributes, etc.); `--full` switches to a compact raw dump instead — the flag currently selects the *less* detailed view despite its name.

```
lmncli user johndoe
lmncli user --full johndoe
lmncli user --check-first-pw johndoe
```
