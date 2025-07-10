import typer
from typing_extensions import Annotated
import sys

from rich.console import Console
from linuxmusterTools.samba_util import GroupManager


console = Console(emoji=False)
app = typer.Typer()

@app.callback(
    invoke_without_command=True,
    help="""Manage the management groups."""
)
def manage(
        group: Annotated[str, typer.Argument(help="The group to modify, like internet, wifi, intranet, ...")],
        add_members: Annotated[str, typer.Option("--add-members", help="Comma separated list of users to add to GROUP")] = '',
        remove_members: Annotated[str, typer.Option("--remove-members", help="Comma separated list of users to remove from GROUP")] = '',
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        ):


    if add_members is None and remove_members is None:
        typer.secho("Please choose at least one of the option --add-members or --remove-members", fg=typer.colors.RED)
        sys.exit(0)

    groupmanager = GroupManager(school=school)

    if add_members:
        to_add = add_members.split(',')
        try:
            groupmanager.add_members(group, to_add)
        except Exception as e:
            sys.exit(str(e))

    if remove_members:
        to_remove = remove_members.split(',')
        try:
            groupmanager.remove_members(group, to_remove)
        except Exception as e:
            sys.exit(str(e))
