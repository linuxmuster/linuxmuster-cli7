import typer
from typing_extensions import Annotated

from rich.console import Console
from rich.table import Table
from linuxmusterTools.ldapconnector import LMNLdapReader as lr, LMNMgmtGroup
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
        students = [student
                    for student in lr.get('/rawroles/student', school=school, dict=False)
                    if student.sophomorixAdminClass in schoolclass]
    else:
        students = lr.get('/rawroles/student', school=school, dict=False)

    internet_group = LMNMgmtGroup('internet')

    with Spinner() as s:
        total = len(students)
        for idx, student in enumerate(students):
            s.print(f"[{idx + 1}/{total}] Updating internet membership of {student.cn}")
            if not student.internet:
                internet_group.add_member(student.cn)

