# linbo

Manage LINBO images and groups.

## Usage

```
lmncli linbo COMMAND [OPTIONS]
```

## Commands

### `groups`

List LINBO groups (`start.conf.*` files under `/srv/linbo`) and the number of devices assigned to each.

| Option | Description |
|---|---|
| `--school`, `-s` | Target school (default: `default-school`) |

```
lmncli linbo groups --school default-school
```

### `images`

List all available LINBO images: size, backups, and differential image info.

```
lmncli linbo images
```

### `lastsync`

Display the last synchronisation date of all devices, or only those in GROUP.

| Option | Description |
|---|---|
| `GROUP` (argument, optional) | Restrict to a single LINBO group |
| `--school`, `-s` | Accepted but currently has no effect on the result |

```
lmncli linbo lastsync win10
```
