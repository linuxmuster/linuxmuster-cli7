import typer
import shutil
from typing_extensions import Annotated
from rich.console import Console
from rich.table import Table

from linuxmusterTools.ldapconnector import LMNUserWriter


console = Console(emoji=False)
app = typer.Typer()

@app.callback(
    invoke_without_command=True,
    help="""Check unnecessary directories in attic."""
)
def check(
        school: Annotated[str, typer.Option("--school", "-s")] = None,
        ):


    uw = LMNUserWriter()
    uw.check_parents_groups()