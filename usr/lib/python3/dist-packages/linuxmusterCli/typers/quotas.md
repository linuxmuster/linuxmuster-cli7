# quotas

Display disk/mail/cloud quotas for teachers or a schoolclass's students.

## Usage

```
lmncli quotas [OPTIONS]
```

| Option | Description |
|---|---|
| `--class`, `-c` | Show quotas for this schoolclass's students |
| `--teachers`, `-t` | Show quotas for all teachers |

**One of `--class` or `--teachers` is required** — calling `lmncli quotas` with neither currently crashes instead of showing usage help. `--class` and `--teachers` are mutually exclusive.

Results are sorted by the school-quota usage percentage, highest first.

```
lmncli quotas --teachers
lmncli quotas --class 7a
```
