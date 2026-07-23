# check_attic

Check for unnecessary directories left behind in the attic (killed user accounts whose home directory hasn't been cleaned up).

## Usage

```
lmncli check_attic [OPTIONS]
```

| Option | Description |
|---|---|
| `--school`, `-s` | Target school (default: searches across schools) |

If killed accounts with a leftover attic directory are found, the command shows the equivalent `smbclient` cleanup command and asks for confirmation before deleting the directories itself.

```
lmncli check_attic --school default-school
```
