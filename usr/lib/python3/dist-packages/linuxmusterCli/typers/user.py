import typer
from typing_extensions import Annotated

from rich.console import Console
from rich.pretty import pprint
from linuxmusterTools.ldapconnector import LMNLdapReader as lr


console = Console(emoji=False)
app = typer.Typer()

@app.callback(
    invoke_without_command=True,
    help="""Show user details."""
)
def ls(
        user: Annotated[str, typer.Argument()] = '',
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        full: Annotated[bool, typer.Option("--full", "-f")] = False,
        ):

    user = user.lower()

    users_data = lr.get(f'/users/{user}', school = school)

    if not full:
        del users_data['sophomorixWebuiPermissionsCalculated']
        del users_data['permissions']
        del users_data['sophomorixSessions']
        del users_data['lmnsessions']
        del users_data['memberOf']

    pprint(users_data)
