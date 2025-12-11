import typer
from concurrent import futures
from typing_extensions import Annotated

from linuxmusterTools.ldapconnector import LMNLdapReader as lr
from linuxmusterTools.quotas import get_user_quotas
from rich.console import Console
from rich.table import Table
from .state import state
from .format import printf, error


console = Console(emoji=False)
app = typer.Typer()

@app.callback(
    invoke_without_command=True,
    help="""Display quotas of users."""
)
def ls(
        #school: Annotated[str, typer.Option("--school", "-s", help="Select the users from a specific school.")] = 'default-school',
        schoolclass: Annotated[str, typer.Option("--class", "-c", help="Only show the students of the specified schoolclass.")] = '',
        teachers: Annotated[bool, typer.Option("--teachers", "-t", help="Only show the teachers.")] = False,
        #user: Annotated[bool, typer.Option("--user", "-u", help="Only show the specified.")] = False,
        ):


    # Seems to be a TODO
    if schoolclass and teachers:
        error("Options --schoolclass and --teachers are mutually exclusives! Please pick only one of them.")
        raise typer.Exit()
    school = 'default-school'

    if teachers:
        title_suffix = "of teachers"
        users = lr.getval('/roles/teacher', 'cn')
    elif schoolclass:
        title_suffix = f"of schoolclass {schoolclass}"
        users = lr.getval(f'/schoolclasses/{schoolclass}', 'sophomorixMembers')

    table_quotas = Table(title=f"Quotas {title_suffix}")
    table_quotas.add_column("User", style="cyan")
    table_quotas.add_column("Used global", style="yellow")
    table_quotas.add_column(f"Used {school}", style="green")
    table_quotas.add_column("Cloud", style="blue")
    table_quotas.add_column("Mail", style="blue")

    data = [[c.header for c in table_quotas.columns]]

    def add_quotas(user):
        quotas = get_user_quotas(user)

        data.append([
            user,
            f"{quotas['linuxmuster-global']['used']}/{quotas['linuxmuster-global']['hard_limit']}",
            f"{quotas[school]['used']}/{quotas[school]['hard_limit']}",
            quotas['cloud'],
            quotas['mail']
        ])

        global_level = "[green]"
        school_level = "[green]"
        school_percent = 0

        if quotas['linuxmuster-global']['hard_limit'] != "NO LIMIT":
            global_percent = 100 * quotas['linuxmuster-global']['used'] / quotas['linuxmuster-global']['hard_limit']
            if global_percent > 90:
                global_level = "[red]"
            elif global_percent > 75:
                global_level = "[yellow]"

        if quotas[school]['hard_limit'] != "NO LIMIT":
            school_percent = 100 * quotas[school]['used'] / quotas[school]['hard_limit']
            if school_percent > 90:
                school_level = "[red]"
            elif school_percent > 75:
                school_level = "[yellow]"

        return (
            user,
            f"{global_level}{quotas['linuxmuster-global']['used']:>9.2f} / {quotas['linuxmuster-global']['hard_limit']}",
            f"{school_level}{quotas[school]['used']:>9.2f} / {quotas[school]['hard_limit']}",
            quotas['cloud'],
            quotas['mail'],
            school_percent
        )

    with futures.ThreadPoolExecutor() as executor:
        infos = executor.map(add_quotas, users)

    # Sort by school_percent
    results = sorted(list(infos), key=lambda l: -l[-1])

    for result in results:
        table_quotas.add_row(*result[:-1])

    if state.format:
        printf.format(data)
    else:
        console.print(table_quotas)
