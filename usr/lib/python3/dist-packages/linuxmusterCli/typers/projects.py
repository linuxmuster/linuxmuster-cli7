import typer
from typing_extensions import Annotated

from rich.console import Console
from rich.table import Table
from rich import print
from linuxmusterTools.lmnfile import LMNFile
from linuxmusterTools.ldapconnector import LMNLdapReader as lr
from .state import state
from .format import printf, outformat


console = Console(emoji=False)
app = typer.Typer()

@app.callback(
    invoke_without_command=True,
    help="""List all projects which hostname, ip or user / room member containing FILTER_STR."""
)
def ls(
        filter_str: Annotated[str, typer.Argument()] = '',
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        ):

    filter_str = filter_str.lower()

    projects_data = lr.get('/projects', school=school)

    projects_data = list(filter(lambda p: filter_str in p['cn'].lower(), projects_data))
    projects_data = sorted(projects_data, key=lambda p: p['cn'])

    projects = Table(title=f"{len(projects_data)} project(s)", show_lines=True)
    projects.add_column("Name", style="cyan")
    projects.add_column("Member(s)", style="yellow")
    projects.add_column("Admin(s)", style="red")
    projects.add_column("Membergroup(s)", style="yellow")
    projects.add_column("Admingroup(s)", style="red")
    projects.add_column("Hidden", justify="center")
    projects.add_column("Joinable", justify="center")

    output = [[c.header for c in projects.columns]]

    for project in projects_data:
        projects.add_row(
            project['cn'],
            ','.join(project['sophomorixMembers']),
            ','.join(project['sophomorixAdmins']),
            ','.join(project['sophomorixMemberGroups']),
            ','.join(project['sophomorixAdminGroups']),
            outformat(project['sophomorixHidden']),
            outformat(project['sophomorixJoinable']),
        )
        output.append([
            project['cn'],
            ','.join(project['sophomorixMembers']),
            ','.join(project['sophomorixAdmins']),
            ','.join(project['sophomorixMemberGroups']),
            ','.join(project['sophomorixAdminGroups']),
            project['sophomorixHidden'],
            project['sophomorixJoinable'],
        ])

    if state.format:
        printf.format(output)
    else:
        print(projects)
