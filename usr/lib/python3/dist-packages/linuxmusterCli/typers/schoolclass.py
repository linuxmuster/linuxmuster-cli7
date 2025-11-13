import sys
import typer
from typing_extensions import Annotated

from rich.console import Console
from rich.table import Table

from linuxmusterTools.common import lprint
from linuxmusterTools.ldapconnector import LMNLdapReader as lr, LMNSchoolclass
from .state import state
from .format import printf


console = Console(emoji=False)
app = typer.Typer()

@app.command(help="""Manage schoolclasses' groups.""")
def sync(
        schoolclass: Annotated[str, typer.Option("--scholclass", "-c", help="Comma separated list of schoolclasses to handle")] = '',
        sync_teachers: Annotated[bool, typer.Option("--teachers", help="Update the teachers group of this schoolclass")] = False,
        sync_students: Annotated[bool, typer.Option("--students", help="Update the students group of this schoolclass")] = False,
        sync_parents: Annotated[bool, typer.Option("--parents", help="Update the parents group of this schoolclass")] = False,
        sync_groups: Annotated[bool, typer.Option("--groups", help="Update the parents, teachers and students groups of this schoolclass")] = False,
        sync_all: Annotated[bool, typer.Option("--all", help="Update the parents, teachers and students groups of all schoolclasses")] = False,
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        ):


    if not sync_all and not schoolclass:
        typer.secho("Please select at least a schoolclass or the option --sync-all", fg=typer.colors.RED)
        return

    if sync_all:
        sync_teachers, sync_students, sync_parents = True, True, True
        schoolclasses = lr.getval('/schoolclasses','cn')
        schoolclasses.remove('attic')
    else:

        schoolclasses = schoolclass.split(',')

        sync_teachers = True if sync_teachers or sync_groups else False
        sync_students = True if sync_students or sync_groups else False
        sync_parents = True if sync_parents or sync_groups else False

        if not (sync_parents or sync_teachers or sync_students):
            typer.secho("Please choose at least one of the option --sync-teachers, --sync-parents or --sync-students", fg=typer.colors.RED)
            sys.exit(0)

    try:
        for schoolclass in schoolclasses:
            lprint.lmn(f"lmncli: Checking groups of schoolclass {schoolclass} in {school}")
            schoolclass_group = LMNSchoolclass(schoolclass)

            if sync_teachers:
                try:
                    lprint.lmn(f"\t--> teachers group", end="\r")
                    schoolclass_group.teachers_group.fill_members()
                    lprint.lmn(f"\t--> teachers group ✅")
                except Exception as e:
                    sys.exit(e)

            if sync_parents:
                try:
                    lprint.lmn(f"\t--> parents group", end="\r")
                    schoolclass_group.parents_group.fill_members()
                    lprint.lmn(f"\t--> parents group  ✅")
                except Exception as e:
                    sys.exit(e)

            if sync_students:
                try:
                    lprint.lmn(f"\t--> students group", end="\r")
                    schoolclass_group.students_group.fill_members()
                    lprint.lmn(f"\t--> students group ✅")
                except Exception as e:
                    sys.exit(e)

    except Exception as e:
        print(str(e))
        sys.exit(1)
