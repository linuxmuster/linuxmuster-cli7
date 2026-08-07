import sys

import typer
from typing_extensions import Annotated

from rich.console import Console
from rich.table import Table
from linuxmusterTools.ldapconnector import LMNLdapReader as lr
from linuxmusterTools.samba_util import GroupManager
from linuxmusterTools.common import Spinner, SHELL_COLOR_INFO


console = Console(emoji=False)
app = typer.Typer()

@app.command(help="""Give access back to internet for selected students.""")
def reset_internet(
        schoolclass: Annotated[str, typer.Option(
            "--schoolclass",
            "-c",
            help="Comma separated list of schoolclasses to handle"
        )] = '',
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school'
):


    if schoolclass:
        schoolclass_list = [s.strip() for s in schoolclass.split(',')]
        students = [student
                    for student in lr.get('/rawroles/student', school=school, as_dict=False)
                    if student.sophomorixAdminClass in schoolclass_list]
    else:
        students = lr.get('/rawroles/student', school=school, as_dict=False)

    to_add = [student.cn for student in students if not student.internet]

    if not to_add:
        console.print("No student needs their internet access reset.")
        return

    groupmanager = GroupManager(school=school)
    failures = []

    with Spinner() as s:
        total = len(to_add)
        for idx, cn in enumerate(to_add):
            s.print(f"[{idx + 1}/{total}] Updating internet membership of {cn}")
            try:
                groupmanager.add_members('internet', [cn])
            except Exception as e:
                failures.append((cn, str(e)))

    if failures:
        for cn, error in failures:
            console.print(f"Could not update {cn}: {error}", style="red")
        sys.exit(1)

