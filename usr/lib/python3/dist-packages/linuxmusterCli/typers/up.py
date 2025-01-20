import typer
from typing_extensions import Annotated

from rich.console import Console
from rich.table import Table
from linuxmusterTools.devices import UPChecker
from .state import state
from .format import printf


console = Console(emoji=False)
app = typer.Typer()

@app.callback(
    invoke_without_command=True,
    help="Check if the clients are online. Specify group to filter the results."
)
def check_online(
        group: Annotated[str, typer.Argument()] = '',
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        ):

    up_checker = UPChecker(school=school)

    if group:
        results = up_checker.check(groups=[group])
    else:
        results = up_checker.check()

    table_results = Table(title=f"{len(results)} device(s)")
    table_results.add_column("IP", style="yellow")
    table_results.add_column("Status")

    data = [[c.header for c in table_results.columns]]
    for ip, status in results.items():
        if state.format:
            data.append([ip, status])
        else:
            if status in ["Off", "No response"]:
                table_results.add_row(ip, f"[red]{status}")
            elif status == "Linbo":
                table_results.add_row(ip, f"[cyan]{status}")
            elif status == "OS Linux":
                table_results.add_row(ip, f"[green]{status}")
            elif status == "OS Windows":
                table_results.add_row(ip, f"[bright_magenta]{status}")
            elif status == "OS Unknown":
                table_results.add_row(ip, f"[bright_black]{status}")

    if not state.format:
        console.print(table_results)
    else:
        printf.format(data)