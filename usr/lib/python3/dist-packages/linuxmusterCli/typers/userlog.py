import typer
from datetime import datetime
from typing_extensions import Annotated

from linuxmusterTools.common import parse_update_log, parse_kill_log, parse_add_log
from linuxmusterTools.ldapconnector import LMNLdapReader as lr
from rich.console import Console
from rich.table import Table
from .state import state
from .format import printf, error


console = Console(emoji=False)
app = typer.Typer()

@app.callback(
    invoke_without_command=True,
    help="""Parse the userlogs of sophomorix and list the users added, killed or updated the last year."""
)
def ls(
        school: Annotated[str, typer.Option("--school", "-s", help="Select the users from a specific school.")] = 'default-school',
        show_added: Annotated[bool, typer.Option("--added", "-a", help="Show the users added")] = False,
        show_killed: Annotated[bool, typer.Option("--killed", "-k", help="Show the users killed.")] = False,
        show_updated: Annotated[bool, typer.Option("--updated", "-u", help="Show the users updated.")] = False,
        today: Annotated[bool, typer.Option("--today", "-t", help="Only show the users changed today (can not be used combined with --all or --lastweek).")] = False,
        lastweek: Annotated[bool, typer.Option("--lastweek", "-lw", help="Only show the users changed lastweek (can not be used combined with --all or --today).")] = False,
        last: Annotated[bool, typer.Option("--last", "-l", help="Only show the users changed at the last command (can only be used combined with -a or -k or -u).")] = False,
        list_changes: Annotated[bool, typer.Option("--list-changes", "-c", help="Get from the update log the list of changes attributes for each user. Disabled per default as it could take a lot of time.")] = False,
        all: Annotated[bool, typer.Option("--all", help="Show all users changes logged (can not be used combined with --today or --lastweek).")] = False,
        ):

    if (all and today) or (all and lastweek) or (today and lastweek) or (last and (today or all or lastweek)):
        error("Options --all, --last, --today and --lastweek are mutually exclusives! Please pick only one of them.")
        raise typer.Exit()

    # No option chosen, showing all entries
    if not (show_added or show_updated or show_killed):
        show_added, show_killed, show_updated = True, True, True
        if last:
            error("Option --last can only be used combined with -a or -k or -u ")
            raise typer.Exit()

    userlog_data = {"added":{}, "updated":{}, "killed":{}}

    if show_added:
        if last:
            entries = parse_add_log(all=all, today=today, lastweek=lastweek)
            timestamps = list(entries.keys())
            timestamps.sort()
            # Get only last timestamp entry
            userlog_data["added"] = {timestamps[-1]: entries[timestamps[-1]]}
        else:
            userlog_data["added"] = parse_add_log(all=all, today=today, lastweek=lastweek)

    if show_killed:
        if last:
            entries = parse_kill_log(all=all, today=today, lastweek=lastweek)
            timestamps = list(entries.keys())
            timestamps.sort()
            # Get only last timestamp entry
            userlog_data["killed"] = {timestamps[-1]: entries[timestamps[-1]]}
        else:
            userlog_data["killed"] = parse_kill_log(all=all, today=today, lastweek=lastweek)

    if show_updated:
        if last:
            entries = parse_update_log(all=all, today=today, lastweek=lastweek, list_changes=list_changes)
            timestamps = list(entries.keys())
            timestamps.sort()
            # Get only last timestamp entry
            userlog_data["updated"] = {timestamps[-1]: entries[timestamps[-1]]}
        else:
            userlog_data["updated"] = parse_update_log(all=all, today=today, lastweek=lastweek, list_changes=list_changes)

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
    for i, (timestamp, entries) in enumerate(userlog_data["added"].items()):
        date = str(datetime.fromtimestamp(timestamp))
        for entry in entries:
            data.append(["Added", entry['lastname'], entry['firstname'], entry['user'], entry['school'], entry['role'], entry['adminclass'], date, ""])
            userlog.add_row("Added", entry['lastname'], entry['firstname'], entry['user'], entry['school'], entry['role'], entry['adminclass'], date, "", end_section=i==len(userlog_data["added"])-1)

    for i, (timestamp, entries) in enumerate(userlog_data["killed"].items()):
        date = str(datetime.fromtimestamp(timestamp))
        for entry in entries:
            data.append(["Killed", entry['lastname'], entry['firstname'], entry['user'], entry['school'], entry['role'], entry['adminclass'], date, ""])
            userlog.add_row("Killed", entry['lastname'], entry['firstname'], entry['user'], entry['school'], entry['role'], entry['adminclass'], date, "", end_section=i==len(userlog_data["killed"])-1)

    for timestamp, entries in userlog_data["updated"].items():
        date = str(datetime.fromtimestamp(timestamp))
        for entry in entries:
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

