# Release Notes – linuxmuster-cli7 7.4

**Package version:** 7.4.1 – 7.4.10

---

## Overview

Version 7.4 rounds out the CLI with the last missing piece of password
management, a new group-management typer, a usable `linbo lastsync` report,
and a broad pass of small correctness fixes across existing typers — several
of them silent failures that had gone unnoticed until now.

---

## New typers

- `lmncli passwd <user>`: manages a user's first (initial) and current login
  password — brings parity with the webui/API password management.
- `lmncli lmngroup`: `ls`, `create`, `delete`, `legacy` (list
  sophomorix-groups not yet migrated to `OU=LMNGroups`), `migrate`.

---

## LINBO lastsync report

- `lmncli linbo lastsync` takes `-w`/`--warning` and `-d`/`--danger` to list
  only the devices in that state (yellow: not synchronised for more than 7
  days, red: never or more than 30 days). A host is kept as soon as one of
  its images matches, its other images still being displayed for the context,
  and a group left empty by the filter is skipped entirely.
- The report now names the hardware group it is listing: the console prints
  it as the table title, with the number of devices kept by the filters, and
  the csv/raw exports carry it as a last `Group` column. Their rows were
  concatenated group after group with nothing to tell them apart.
- The creation timestamp of the applied image is displayed next to each
  synchronisation date, in parentheses on the console and as an "Applied
  version of `<image>`" column in the exports: a host can be freshly
  synchronised and still be running an old image. This needs
  `linuxmuster-tools7` 7.4.18; the value stays empty with an older one.
- The csv and raw exports no longer print the raw Python dict of a
  synchronisation, which was unusable in a semicolon-separated file: the date
  is written as `YYYY-MM-DD HH:MM` or `Never`, and the status gets its own
  "Status for `<image>`" column, the console carrying it as a colour only.

---

## Schoolclasses, teachers and students

- Teachers are now written to `sophomorixAdmins` as well as to the member
  list, which is where sophomorix and the webui read them from.
- New command to clean up the orphan subgroups left behind by a killed
  schoolclass.
- The attic group is ignored when listing teachers, and the attic is ignored
  for every school when listing students.
- `students` no longer aborts on a single failure: every failure is collected
  and displayed, with a non-zero exit code.

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
- `samba` checks that the given school is a valid one.
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

## Packaging

- postinst: the deprecated venv migration is dropped,
  `create_linuxmuster_venv()` being a no-op when the venv is already there.
- New `linuxmuster-venv` dpkg trigger: the CLI requirements are reinstalled
  when `linuxmuster-tools7` rebuilds the shared venv after a Python upgrade.

---

## Miscellaneous

- `lastsync` adapted to `linuxmuster-tools`' new `last_sync_all()` return
  shape.
- README added for each typer; Samba/smbclient bindings lazy-imported in
  `check_smbclient`/`samba` to improve load time.
- The help of several parameters has been updated.

---

Author: Arnaud Kientz
Co-Author: Claude
