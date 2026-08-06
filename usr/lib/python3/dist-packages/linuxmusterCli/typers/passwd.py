import typer
from typing_extensions import Annotated

from linuxmusterTools.ldapconnector import LMNUser
from .format import error


app = typer.Typer()

@app.callback(
    invoke_without_command=True,
    help="""Manage a user's first (initial) and current login password."""
)
def manage(
        user: Annotated[str, typer.Argument(help="Login of the user to manage")],
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        set_first_password: Annotated[bool, typer.Option("--set-first-password", "-f", help="Prompt for a new password, and set it as both the first (initial) and the current login password")] = False,
        set_current_password: Annotated[bool, typer.Option("--set-current-password", "-p", help="Prompt for a new password and set it as the user's actual login password (first password left untouched)")] = False,
        set_random_password: Annotated[bool, typer.Option("--set-random-password", "-r", help="Generate a random password satisfying the current policy and set it as first and current password")] = False,
        reset_first_password: Annotated[bool, typer.Option("--reset-first-password", "-b", help="Reset the user's actual login password back to their existing stored first password")] = False,
        check_first_password: Annotated[bool, typer.Option("--check-first-pw", "-c", help="Report whether the first (initial) password is still the current one")] = False,
        ):

    user = user.lower()

    password_actions = (set_first_password, set_current_password, set_random_password, reset_first_password, check_first_password)
    if sum(bool(a) for a in password_actions) != 1:
        error("Choose exactly one of --set-first-password, --set-current-password, --set-random-password, --reset-first-password, --check-first-pw.")
        raise typer.Exit(code=1)

    try:
        user_writer = LMNUser(user, school=school)
    except Exception as e:
        error(str(e))
        raise typer.Exit(code=1)

    if user_writer.new:
        error(f"User {user} not found.")
        raise typer.Exit(code=1)

    if check_first_password:
        try:
            still_set = user_writer.test_first_password()
        except Exception as e:
            error(str(e))
            raise typer.Exit(code=1)
        if still_set:
            typer.secho(f"First password for {user} is still the current one.", fg=typer.colors.GREEN)
        else:
            typer.secho(f"First password for {user} is no longer the current one.", fg=typer.colors.YELLOW)
        return

    if reset_first_password:
        first_password = user_writer.data.get('sophomorixFirstPassword')
        if not first_password:
            error("No first password stored for this user, nothing to reset to.")
            raise typer.Exit(code=1)
        try:
            user_writer.set_actual_password(first_password)
        except Exception as e:
            error(f"Cannot reset current password: {e}")
            raise typer.Exit(code=1)
        typer.secho(f"Current password for {user} reset back to the stored first password.", fg=typer.colors.GREEN)
        return

    if set_random_password:
        try:
            random_password = user_writer.set_random_first_password()
        except Exception as e:
            error(f"Cannot set a random password: {e}")
            raise typer.Exit(code=1)
        typer.secho(f"New random password for {user}: {random_password}", fg=typer.colors.GREEN)
        return

    from linuxmusterTools.passwords import PasswordPolicyProvider
    password_policy_provider = PasswordPolicyProvider()

    if set_first_password:
        new_password = typer.prompt("New first password", hide_input=True, confirmation_prompt=True)
        result = password_policy_provider.validate(
            new_password, role=user_writer.data.get('sophomorixRole', ''), school=user_writer.school, username=user
        )
        if not result.ok:
            error(f"Password does not meet requirements: {'; '.join(result.violations)}")
            raise typer.Exit(code=1)
        user_writer.setattr(data={'sophomorixFirstPassword': new_password})
        try:
            user_writer.set_actual_password(new_password)
        except Exception as e:
            error(f"Cannot set current password: {e}")
            raise typer.Exit(code=1)
        typer.secho(f"First password set for {user} (also set as current password).", fg=typer.colors.GREEN)
        return

    if set_current_password:
        new_password = typer.prompt("New current password", hide_input=True, confirmation_prompt=True)
        result = password_policy_provider.validate(
            new_password, role=user_writer.data.get('sophomorixRole', ''), school=user_writer.school, username=user
        )
        if not result.ok:
            error(f"Password does not meet requirements: {'; '.join(result.violations)}")
            raise typer.Exit(code=1)
        try:
            user_writer.set_actual_password(new_password)
        except Exception as e:
            error(str(e))
            raise typer.Exit(code=1)
        typer.secho(f"Current password set for {user} (first password left untouched).", fg=typer.colors.GREEN)
        return
