# printers

List printers whose hostname or IP contains FILTER_STR, along with their user/room access.

## Usage

```
lmncli printers [FILTER_STR] [OPTIONS]
```

| Option | Description |
|---|---|
| `FILTER_STR` (argument, optional) | Filter on hostname or IP (case-insensitive) |
| `--school`, `-s` | Target school (default: `default-school`) |

```
lmncli printers --school default-school
lmncli printers copier
```
