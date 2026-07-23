# samba

Manage samba shares and connections: GPOs, drives, live connections, DNS, last logins.

## Usage

```
lmncli samba COMMAND [OPTIONS]
```

## Commands

### `gpos`

Display all GPOs configured on the system (name, GPO GUID, sysvol path).

```
lmncli samba gpos
```

### `drives`

Display the drives configured for a school's GPO drive manager.

| Option | Description |
|---|---|
| `--school`, `-s` | Target school (default: `default-school`) |

```
lmncli samba drives --school default-school
```

### `status`

Display current samba connections (users and/or machines).

| Option | Description |
|---|---|
| `--school`, `-s` | Target school (default: `default-school`) |
| `--users`, `-u` | Only show user connections |
| `--machines`, `-m` | Only show machine connections |

Passing neither `--users` nor `--machines` (or both together) shows both tables.

```
lmncli samba status --users
```

### `dns`

Display DNS entries (root zone records and/or sub-records).

| Option | Description |
|---|---|
| `--school`, `-s` | Target school (default: `default-school`) |
| `--root` | Only show root zone entries |
| `--sub` | Only show sub-records |

Passing neither flag shows both tables.

```
lmncli samba dns --root
```

### `lastlogin`

Display the last login of a user or a computer matching PATTERN.

| Option | Description |
|---|---|
| `PATTERN` (argument) | User or hostname fragment to search for |
| `--all`, `-a` | Include archived (`.gz`) logs |

```
lmncli samba lastlogin johndoe
```
