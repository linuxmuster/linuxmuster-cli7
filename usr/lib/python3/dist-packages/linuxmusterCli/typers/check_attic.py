import typer
import shutil
from typing_extensions import Annotated
from rich.console import Console
from rich.table import Table

from linuxmusterTools.common.attic import check_attic_dir


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
    attic.add_column("Status", style="yellow")
    attic.add_column("Directory path", style="green")

    commands = ""
    cmd_count = 0
    to_delete = []
    for user,killdate in result.items():
        if killdate is not None:
            to_delete.append(f"{attic_dir}/{user}")
            commands += f"\trm -rf {attic_dir}/{user}\n"
            status = f"Account killed at {killdate}"
            cmd_count += 1
        else:
            status = "No information found"

        attic.add_row(user, status, f"{attic_dir}/{user}")

    console.print(attic)
    if cmd_count > 0:
        console.rule(style="blue")

    delete_msg = typer.style(commands, fg=typer.colors.RED, bold=True)
    if cmd_count == 1:
        typer.confirm(f"You can delete the unnecessary directory by running:\n\n{delete_msg}\nRun all this command now ?", abort=True)
        for d in to_delete:
            shutil.rmtree(d)
            typer.echo(typer.style(f"{d} deleted!", fg=typer.colors.RED))
    elif cmd_count > 1:
        typer.confirm(f"You can delete the unnecessary directories by running:\n\n{delete_msg}\nRun all these commands now ?", abort=True)
        for d in to_delete:
            shutil.rmtree(d)
            typer.echo(typer.style(f"{d} deleted!", fg=typer.colors.RED))