# mgmtgroup

Manage management groups (internet, wifi, intranet, ...) via samba-tool.

## Usage

```
lmncli mgmtgroup GROUP [OPTIONS]
```

Options must be given **before** the `GROUP` argument, or Typer will misparse a trailing `--option` as an unknown subcommand.

| Option | Description |
|---|---|
| `GROUP` (argument, required) | The management group to modify (e.g. `internet`, `wifi`, `intranet`) |
| `--add-members` | Comma separated list of users to add |
| `--remove-members` | Comma separated list of users to remove |
| `--school`, `-s` | Target school (default: `default-school`) |

```
lmncli mgmtgroup --add-members johndoe,janedoe internet
```
