import typer
from datetime import datetime
from typing_extensions import Annotated

from linuxmusterTools.common import parse_update_log, parse_kill_log, parse_add_log
from linuxmusterTools.ldapconnector import LMNLdapReader as lr
from rich.console import Console
from rich.table import Table
from .state import state
from .format import printf


console = Console(emoji=False)
app = typer.Typer()

@app.callback(
    invoke_without_command=True,
    help="""Parse the userlogs of sophomorix and list the users added, killed or updated the last year."""
)
def ls(
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        show_added: Annotated[bool, typer.Option("--added", "-a")] = False,
        show_killed: Annotated[bool, typer.Option("--killed", "-k")] = False,
        show_updated: Annotated[bool, typer.Option("--updated", "-u")] = False,
        today: Annotated[bool, typer.Option("--today", "-t")] = False,
        lastweek: Annotated[bool, typer.Option("--lastweek", "-lw")] = False,
        all: Annotated[bool, typer.Option("--all")] = False,
        ):

    # No option chosen, showing all entries
    if not (show_added or show_updated or show_killed):
        show_added, show_killed, show_updated = True, True, True

    userlog_data = {"added":{}, "updated":{}, "killed":{}}

    if show_added:
        userlog_data["added"] = parse_add_log(all=all, today=today, lastweek=lastweek)

    if show_killed:
        userlog_data["killed"] = parse_kill_log(all=all, today=today, lastweek=lastweek)

    if show_updated:
        userlog_data["updated"] = parse_update_log(all=all, today=today, lastweek=lastweek)

    userlog = Table(title=f"User log entries")
    userlog.add_column("Type", style="cyan")
    userlog.add_column("Lastname", style="cyan")
    userlog.add_column("Firstname", style="cyan")
    userlog.add_column("Login", style="green")
    userlog.add_column("School", style="green")
    userlog.add_column("Role", style="bright_magenta")
    userlog.add_column("Adminclass", style="bright_magenta")
    userlog.add_column("Date", style="yellow")
    userlog.add_column("Changes", style="yellow")

    data = [[c.header for c in userlog.columns]]
    for i, (timestamp, entry) in enumerate(userlog_data["added"].items()):
        date = str(datetime.fromtimestamp(timestamp))
        data.append(["Added", entry['lastname'], entry['firstname'], entry['user'], entry['school'], entry['role'], entry['adminclass'], date, ""])
        userlog.add_row("Added", entry['lastname'], entry['firstname'], entry['user'], entry['school'], entry['role'], entry['adminclass'], date, "", end_section=i==len(userlog_data["added"])-1)

    for i, (timestamp, entry) in enumerate(userlog_data["killed"].items()):
        date = str(datetime.fromtimestamp(timestamp))
        data.append(["Killed", entry['lastname'], entry['firstname'], entry['user'], entry['school'], entry['role'], entry['adminclass'], date, ""])
        userlog.add_row("Killed", entry['lastname'], entry['firstname'], entry['user'], entry['school'], entry['role'], entry['adminclass'], date, "", end_section=i==len(userlog_data["killed"])-1)

    for timestamp, entry in userlog_data["updated"].items():
        date = str(datetime.fromtimestamp(timestamp))
        user = lr.get(f'/users/{entry["user"]}')

        # Avoid displaying changes by killed users
        if user:
            changes = "\n".join([f"{k}:{v}" for k,v in entry['changes'].items()])
            changes_csv = ",".join([f"{k}:{v}" for k,v in entry['changes'].items()])

            data.append(["Updated", user['sn'], user['givenName'], entry['user'], user['school'], user['sophomorixRole'], user['sophomorixAdminClass'], date, changes_csv])
            userlog.add_row("Updated", user['sn'], user['givenName'], entry['user'], user['school'], user['sophomorixRole'], user['sophomorixAdminClass'], date, changes, end_section=True)

    if state.format:
        printf.format(data)
    else:
        console.print(userlog)

