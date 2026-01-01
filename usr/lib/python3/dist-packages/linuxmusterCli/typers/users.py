import typer
from typing_extensions import Annotated

from rich.console import Console
from rich.table import Table
from linuxmusterTools.ldapconnector import LMNLdapReader as lr
from .state import state
from .format import printf


console = Console(emoji=False)
app = typer.Typer()

@app.callback(
    invoke_without_command=True,
    help="""List all users which name, login or role containing FILTER_STR."""
)
def ls(
        filter_str: Annotated[str, typer.Argument()] = '',
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        admins: Annotated[bool, typer.Option("--admins", "-a")] = False,
        teachers: Annotated[bool, typer.Option("--teachers", "-t")] = False,
        students: Annotated[bool, typer.Option("--students", "-u")] = False,
        ):

    filter_str = filter_str.lower()

    if admins:
        url = '/users/search/admins/'
    elif teachers:
        url = '/users/search/teacher/'
    elif students:
        url = '/users/search/student/'
    else:
        url = '/rawusers'

    users_data = lr.get(
        url,
        attributes=[
            'displayName',
            'sn',
            'givenName',
            'sAMAccountName',
            'sophomorixAdminClass',
            'sophomorixRole',
            'sophomorixStatus'
        ],
        school = school,
    )

    users_data = list(filter(
        lambda u: filter_str in u['displayName'].lower() or filter_str in u['sAMAccountName'].lower() or filter_str in u['sophomorixAdminClass'].lower(), 
        users_data
    ))

    users_data = sorted(users_data, key=lambda u: (u['sophomorixRole'], u['sn'], u['givenName']))

    users = Table(title=f"{len(users_data)} user(s)")
    users.add_column("Lastname", style="cyan")
    users.add_column("Firstname", style="cyan")
    users.add_column("Login", style="green")
    users.add_column("Adminclass", style="bright_magenta")
    users.add_column("Role", style="bright_magenta")
    users.add_column("Status", style="yellow")

    data = [[c.header for c in users.columns]]
    for user in users_data:
        data.append([user['sn'], user['givenName'], user['sAMAccountName'], user['sophomorixAdminClass'], user['sophomorixRole'], user['sophomorixStatus']])
        users.add_row(user['sn'], user['givenName'], user['sAMAccountName'], user['sophomorixAdminClass'], user['sophomorixRole'], user['sophomorixStatus'])

    if state.format:
        printf.format(data)
    else:
        console.print(users)

