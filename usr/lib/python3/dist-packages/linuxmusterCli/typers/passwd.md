# passwd

Manage a user's first (initial) and current login password — the same operations linuxmuster-api exposes over HTTP (`/users/{user}/set-first-password`, `/users/{user}/set-current-password`, `/users/{user}/set-random-first-password`), calling `linuxmusterTools` directly instead.

## Usage

```
lmncli passwd [OPTIONS] USER
```

Options must be given **before** the `USER` argument, or Typer will misparse a trailing `--option` as an unknown subcommand.

| Option | Description |
|---|---|
| `USER` (argument, required) | Login of the user to manage |
| `--school`, `-s` | Target school (default: `default-school`) |
| `--set-first-password`, `-f` | Prompt for a new password, and set it as **both** the first (initial) and the current login password |
| `--set-current-password`, `-p` | Prompt for a new password and set it as the user's actual login password — the first password is left untouched |
| `--set-random-password`, `-r` | Generate a random password satisfying the current policy and set it as first and current password |
| `--reset-first-password`, `-b` (**b**ack to first) | Reset the user's actual login password back to their existing stored first password |
| `--check-first-pw`, `-c` | Report whether the first (initial) password is still the current one |

Exactly one of the five options above must be given — these mirror the five password actions the webui exposes (via linuxmuster-api) exactly, action for action, so there's no independent "also update the other one" choice: `--set-first-password` always touches the current password too, `--set-current-password` never touches the first one.

- The **first password** (`sophomorixFirstPassword`) is the readable, stored default password — the one you can fall back to with `--reset-first-password` if the user loses their current password.
- The **current password** is the one actually used to log in, never stored in the clear.
- `--set-first-password`/`--set-current-password` prompt interactively (hidden input, confirmation required) and validate the new value against the current password policy (same `PasswordPolicyProvider` as linuxmuster-api) before writing anything.
- `--set-random-password` generates a value that already satisfies the policy — no prompt, no separate validation step.

**Requires root** (writes the account's password directly via Samba's `SamDB`, see `LMNUser.set_actual_password`).

```
lmncli passwd --set-random-password johndoe
lmncli passwd --set-first-password johndoe
lmncli passwd --set-current-password --school other-school johndoe
lmncli passwd --reset-first-password johndoe
lmncli passwd --check-first-pw johndoe
```
