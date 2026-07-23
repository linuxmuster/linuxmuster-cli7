# lmngroup

Manage LMNGroups: sophomorix-independent LDAP groups living under `OU=LMNGroups`, plus migration of legacy sophomorix-groups (`OU=Projects`) into that OU.

## Usage

```
lmncli lmngroup COMMAND [OPTIONS]
```

## Commands

### `ls`

List all lmngroups whose name contains FILTER_STR.

| Option | Description |
|---|---|
| `FILTER_STR` (argument, optional) | Filter on group name (case-insensitive) |
| `--school`, `-s` | Target school (default: `default-school`) |

```
lmncli lmngroup ls
lmncli lmngroup ls robot
```

### `manage`

Add and/or remove members of a lmngroup.

| Option | Description |
|---|---|
| `GROUP` (argument, required) | The lmngroup to modify |
| `--add-members` | Comma separated list of users to add |
| `--remove-members` | Comma separated list of users to remove |
| `--school`, `-s` | Target school (default: `default-school`) |

Invalid logins in the list don't abort the rest of the batch: valid ones are still applied, and each failure is reported individually.

```
lmncli lmngroup manage robotics --add-members johndoe,janedoe
```

### `create`

Create a new (empty) lmngroup.

| Option | Description |
|---|---|
| `GROUP` (argument, required) | The lmngroup to create |
| `--school`, `-s` | Target school (default: `default-school`) |

```
lmncli lmngroup create robotics
```

### `delete`

Delete a lmngroup, after confirmation.

| Option | Description |
|---|---|
| `GROUP` (argument, required) | The lmngroup to delete |
| `--school`, `-s` | Target school (default: `default-school`) |

```
lmncli lmngroup delete robotics
```

### `legacy`

List legacy sophomorix-groups still living in `OU=Projects`, not yet migrated to `OU=LMNGroups`.

| Option | Description |
|---|---|
| `--school`, `-s` | Target school (default: `default-school`) |

```
lmncli lmngroup legacy
```

### `migrate`

Migrate a legacy sophomorix-group to `OU=LMNGroups` (moves the entry and relabels its `sophomorixType`; membership is untouched).

| Option | Description |
|---|---|
| `GROUP` (argument, required) | The group to migrate |
| `--school`, `-s` | Target school (default: `default-school`) |

If a leftover entry is still found at the old dn after the move, the command warns and offers to delete it.

```
lmncli lmngroup migrate p_robotics
```
