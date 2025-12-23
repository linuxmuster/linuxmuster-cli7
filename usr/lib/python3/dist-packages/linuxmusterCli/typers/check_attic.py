import typer
import shutil
from typing_extensions import Annotated
from rich.console import Console
from rich.table import Table

from linuxmusterTools.common.attic import check_attic_dir
from linuxmusterTools.smbclient import LMNSMBClient
from linuxmusterTools.lmnconfig import SAMBA_DOMAIN
from .state import state
from .format import printf


console = Console(emoji=False)
app = typer.Typer()

@app.callback(
    invoke_without_command=True,
    help="""Check unnecessary directories in attic."""
)
def check(
        check_attic: Annotated[str, typer.Argument()] = '',
        school: Annotated[str, typer.Option("--school", "-s")] = None,
        ):

    result = check_attic_dir()
    attic_dir = "/srv/samba/schools/default-school/students/attic"

    attic = Table(title=f"User's status in attic")
    attic.add_column("Username", style="cyan")
    attic.add_column("School", style="cyan")
    attic.add_column("Status", style="yellow")
    attic.add_column("Directory path", style="green")

    to_delete = []
    cmd = ''

    data = [[c.header for c in attic.columns]]
    for user,details in result.items():
        if details['start']:
            if details['status'] == "killed":
                to_delete.append({'user': user, 'school':details['school']})
                status = f"Account killed at {details['end']}"
                cmd += "smbclient" \
                       " -U administrator %$(cat /etc/linuxmuster/.secret/administrator)" \
                       f" //{SAMBA_DOMAIN}/{details['school']} -c 'deltree \"students/attic/{user}\";'\n"
            elif details['status'] != 'killable':
                status = f"Account {details['status']} from {details['start']} to {details['end']}"
            else:
                status = f"Account {details['status']} since {details['start']}"
        else:
            status = "No information found"

        data.append([user, status, details['school'], f"{attic_dir}/{user}"])
        attic.add_row(user, status, details['school'], f"{attic_dir}/{user}")

    if state.format:
        printf.format(data)
    else:
        console.print(attic)
        if len(to_delete) > 0:
            console.rule(style="blue")

            typer.confirm(f"You can delete the unnecessary directory by running:\n\n{cmd}\nRun this command now ?", abort=True)
            client = LMNSMBClient()
            for entry in to_delete:
                print(entry)
                client.switch(entry['school'])
                client.deltree(f"students/attic/{entry['user']}")
                typer.echo(typer.style(f"Attic directory of {user} deleted!", fg=typer.colors.RED))