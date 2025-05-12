import typer
import shutil
from typing_extensions import Annotated
from rich.console import Console
from rich.table import Table

from linuxmusterTools.ldapconnector import LMNParent


console = Console(emoji=False)
app = typer.Typer()

@app.callback(
    invoke_without_command=True,
    help="""Check unnecessary directories in attic."""
)
def check(
        school: Annotated[str, typer.Option("--school", "-s")] = None,
        ):


    pass

    ### Must be updated with new Writer methods
    #uw = LMNUser()
    #report = uw.check_parents_groups()

    #for student, parents_dn in report['move'].items():
    #    print(student, parents_dn)

    #for dn in report['delete']:
    #    print(f"To delete: {dn}")
