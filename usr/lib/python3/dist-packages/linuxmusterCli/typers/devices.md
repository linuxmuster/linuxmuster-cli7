# devices

List devices whose hostname, mac address, room, or IP contains FILTER_STR, cross-referenced with their LDAP registration status.

## Usage

```
lmncli devices [FILTER_STR] [OPTIONS]
```

| Option | Description |
|---|---|
| `FILTER_STR` (argument, optional) | Filter on hostname, mac, room, or IP (case-insensitive) |
| `--school`, `-s` | Target school (default: `default-school`) |

Each device is shown with a status: `Registered` (hostname + mac match LDAP), `Domain Controller`, `Unknown` (hostname matches but mac doesn't), or `Not registered` (no LDAP match at all).

```
lmncli devices --school default-school
lmncli devices pc-101
```
