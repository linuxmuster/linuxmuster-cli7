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
        schoolclass: Annotated[str, typer.Option("--class", "-c", help="Only show the students of the specified schoolclass.")] = False,
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

    quotas = Table(title=f"Quotas {title_suffix}")
    quotas.add_column("User", style="cyan")
    quotas.add_column("Global", style="yellow")
    quotas.add_column(school, style="green")
    quotas.add_column("Cloud", style="green")
    quotas.add_column("Mail", style="green")

    data = [[c.header for c in quotas.columns]]

    def add_quotas(user):
        user_quotas = get_user_quotas(user)

        data.append([user, user_quotas['linuxmuster-global']['used'], user_quotas[school]['used'], user_quotas['cloud'], user_quotas['mail']])
        quotas.add_row(user, str(user_quotas['linuxmuster-global']['used']), str(user_quotas[school]['used']), user_quotas['cloud'], user_quotas['mail'])

    with futures.ThreadPoolExecutor() as executor:
        infos = executor.map(add_quotas, users)

    if state.format:
        printf.format(data)
    else:
        console.print(quotas)
