import typer
from typing_extensions import Annotated

from rich.console import Console
from rich.table import Table
from linuxmusterTools.ldapconnector import LMNLdapReader as lr, LMNStudent
from .state import state
from .format import printf


console = Console(emoji=False)
app = typer.Typer()

@app.callback(
    invoke_without_command=True,
    help="""Manage student's data."""
)
def manage(
        student: Annotated[str, typer.Argument(help="Cn of the student to handle")],
        get_parents: Annotated[bool, typer.Option("--parents", help="Get the parents")] = False,
        add_parents: Annotated[str, typer.Option("--add-parents", help="Comma separated list of the cn of the parents to assign")] = '',
        remove_parents: Annotated[str, typer.Option("--remove-parents", help="Comma separated list of the cn of the parents to remove")] = '',
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        ):

    cn = student.lower()
    try:
        student = LMNStudent(cn, school=school)
        student_name = f"{student.data['givenName']} {student.data['sn']}"
    except Exception as e:
        console.print(str(e))
        return

    if add_parents:
        get_parents = True
        try:
            for parent in add_parents.split(','):
                student.add_parent(parent)
            typer.secho(f"Parents {add_parents} added!\n", fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(str(e), fg=typer.Colors.RED)

    if remove_parents:
        get_parents = True
        try:
            for parent in remove_parents.split(','):
                student.remove_parent(parent)
            typer.secho(f"Parents {remove_parents} removed!\n", fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(str(e, fg=typer.colors.RED))

    if get_parents:
        if student.parents:

            parents = Table(title=f"{len(student.parents)} parent(s) of {student_name}")
            parents.add_column("Login", style="green")
            parents.add_column("Displayname", style="cyan")

            data = [[c.header for c in parents.columns]]
            for parent in student.parents:
                data.append([parent['cn'], parent['displayName']])
                parents.add_row(parent['cn'], parent['displayName'])

            if state.format:
                printf.format(data)
            else:
                console.print(parents)
        else:
            console.print('No parent found!')
