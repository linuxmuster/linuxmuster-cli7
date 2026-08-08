# Release Notes – linuxmuster-cli7 7.4

**Package version:** 7.4.1 – 7.4.7

---

## Overview

Version 7.4 rounds out the CLI with the last missing piece of password
management, a new group-management typer, and a broad pass of small
correctness fixes across existing typers — several of them silent failures
that had gone unnoticed until now.

---

## New typers

- `lmncli passwd <user>`: manages a user's first (initial) and current login
  password — brings parity with the webui/API password management.
- `lmncli lmngroup`: `ls`, `create`, `delete`, `legacy` (list
  sophomorix-groups not yet migrated to `OU=LMNGroups`), `migrate`.

---

## Bug fixes

- Fixed a shell injection in `lmncli version` (`dpkg -l` via `shell=True`).
- Fixed several crashes: `student manage` (invalid `typer.Colors.RED`),
  `IndexError` on malformed DNs in printers/devices listing, `KeyError` on
  an unknown `--school` in `samba drives()`, `UnboundLocalError` in
  `quotas ls` without `--class`/`--teachers`.
- Fixed `reset-internet` matching a schoolclass by substring instead of
  exact name; fixed `--school` accepted but never forwarded in `linbo
  lastsync()`/`schoolclass sync()`; fixed `mgmtgroup manage()` silently
  doing nothing when neither `--add-members` nor `--remove-members` is
  given.
- `printers` now shows "Not registered" instead of silently dropping a
  printer with no matching LDAP entry; `student manage()` now handles each
  `--add-parents`/`--remove-parents` entry independently instead of
  aborting the whole list on the first failure.

---

## GroupManager migration (breaking change for direct consumers)

`students reset-internet` now uses `samba_util.GroupManager` instead of the
deprecated `LMNMgmtGroup`: only students actually missing internet access
are updated, and a failure on one student no longer aborts silently — all
failures are collected and reported at the end, with a non-zero exit code.

---

## Miscellaneous

- `lastsync` adapted to `linuxmuster-tools`' new `last_sync_all()` return
  shape.
- README added for each typer; Samba/smbclient bindings lazy-imported in
  `check_smbclient`/`samba` to improve load time.

---

Author: Arnaud Kientz
Co-Author: Claude
