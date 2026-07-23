# check_smbclient

Interactive diagnostic to test a teacher's samba share access and Kerberos authentication against the Webui's configured domains (and optionally an extra domain of your choice).

## Usage

```
lmncli check_smbclient
```

No options — the command is fully interactive:

1. Optionally enter an extra domain to test (e.g. `server.linuxmuster.lan`).
2. Enter the teacher's login.
3. Enter the teacher's password (or leave empty to authenticate via an already-existing Kerberos ticket).

The command then drops privileges to that teacher's uid/gid and tries to list `students/attic/<teacher>` on each domain (netbios name, realm, configured samba domain, and the extra domain if given), reporting success or failure per host.

**Requires root** (it calls `os.setuid`/`os.setgid` to impersonate the teacher) and a real TTY for password entry.
