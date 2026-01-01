import typer
from typing_extensions import Annotated

from rich.console import Console
from rich.table import Table
from linuxmusterTools.ldapconnector import LMNLdapReader as lr
from linuxmusterTools.common import convert_sophomorix_status
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
        status: Annotated[str, typer.Option("--status", "-c")] = '',
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
            'sophomorixAdminFile',
            'sophomorixExitAdminClass',
            'sophomorixRole',
            'sophomorixStatus'
        ],
        school = school,
    )

    users_data = list(filter(
        lambda u: filter_str in u['displayName'].lower() or filter_str in u['sAMAccountName'].lower() or filter_str in u['sophomorixAdminClass'].lower(), 
        users_data
    ))

    if status:
        users_data = list(filter(lambda u: status == u['sophomorixStatus'], users_data))

    users_data = sorted(users_data, key=lambda u: (u['sophomorixRole'], u['sn'], u['givenName']))

    users = Table(title=f"{len(users_data)} user(s)")
    users.add_column("Lastname", style="cyan")
    users.add_column("Firstname", style="cyan")
    users.add_column("Login", style="green")
    users.add_column("Adminclass", style="bright_magenta")
    users.add_column("Role", style="bright_magenta")
    users.add_column("Status", style="yellow", justify="center")

    data = [[c.header for c in users.columns]]
    for user in users_data:
        if user['sophomorixAdminClass'] == 'attic':
            adminclass = f"attic ({user['sophomorixExitAdminClass']})"
            plural_index = -4 if 'staff' in user['sophomorixAdminFile'] else -5
            role = f"student ({user['sophomorixAdminFile'][:plural_index]})"
        else:
            adminclass = user['sophomorixAdminClass']
            role = user['sophomorixRole']

        status = f"{convert_sophomorix_status(user['sophomorixStatus'])} ({user['sophomorixStatus']})"
        data.append([user['sn'], user['givenName'], user['sAMAccountName'], adminclass, role, status])
        users.add_row(user['sn'], user['givenName'], user['sAMAccountName'], adminclass, role, status)

    if state.format:
        printf.format(data)
    else:
        console.print(users)

