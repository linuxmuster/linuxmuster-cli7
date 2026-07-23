# users

List users whose name, login, or admin class contains FILTER_STR.

## Usage

```
lmncli users [FILTER_STR] [OPTIONS]
```

| Option | Description |
|---|---|
| `FILTER_STR` (argument, optional) | Filter on display name, login, or admin class (case-insensitive) |
| `--school`, `-s` | Target school (default: `default-school`) |
| `--status`, `-c` | Filter on sophomorix status (e.g. `A`, `U`, `D`) |
| `--admins`, `-a` | Only show admins |
| `--teachers`, `-t` | Only show teachers |
| `--students`, `-u` | Only show students |

```
lmncli users --teachers
lmncli users johndoe --status U
```
