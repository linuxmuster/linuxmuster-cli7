import sys
import typer
from typing_extensions import Annotated

from rich.console import Console
from rich import print
from rich.table import Table

from linuxmusterTools.common import lprint
from linuxmusterTools.ldapconnector import LMNLdapReader as lr, LMNSchoolclass
from .state import state
from .format import printf, outformat, sort_schoolclasses


console = Console(emoji=False)
app = typer.Typer()

@app.command(help="""Manage schoolclasses' groups.""")
def sync(
        schoolclass: Annotated[str, typer.Option("--schoolclass", "-c", help="Comma separated list of schoolclasses to handle")] = '',
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

@app.command(help="""Print schoolclasses teacher's memberships.""")
def teachers(
    schoolclass: Annotated[str, typer.Option("--schoolclass", "-c", help="Comma separated list of schoolclasses to handle")] = '',
    school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
    ):

    if not schoolclass:
        schoolclasses = lr.get('/schoolclasses', school=school)
    else:
        schoolclasses = []
        for c in schoolclass.split(','):
            schoolclass = lr.get(f'/schoolclasses/{c}', school=school)
            if schoolclass:
                schoolclasses.append(schoolclass)

    schoolclasses = sort_schoolclasses(schoolclasses)

    table_results = Table(title=f"Schoolclasses teacher's memberships", show_lines=True)
    table_results.add_column("Schoolclass", style="green")
    table_results.add_column("Teachers", style="blue")
    table_results.add_column("Hidden", justify="center")
    table_results.add_column("Joinable", justify="center")

    data = [[c.header for c in table_results.columns]]

    teacher_cache = {}

    for schoolclass in schoolclasses:

        teachers_cn = schoolclass['sophomorixAdmins']
        teacher_list = []

        for cn in teachers_cn:
            # Avoid requesting the same teachers more than once
            if cn not in teacher_cache:
                teacher = lr.get(f'/users/{cn}')
                teacher_name = f"{teacher['sn']} {teacher['givenName']}"
                teacher_cache[cn] = teacher_name

            teacher_list.append(teacher_cache[cn])

        if state.format:
            data.append([
                schoolclass['cn'],
                ','.join(teacher_list),
                schoolclass['sophomorixHidden'],
                schoolclass['sophomorixJoinable']
            ])
        else:
            table_results.add_row(
                schoolclass['cn'],
                ','.join(teacher_list),
                outformat(schoolclass['sophomorixHidden']),
                outformat(schoolclass['sophomorixJoinable'])
            )

    if not state.format:
        print(table_results)
    else:
        printf.format(data)