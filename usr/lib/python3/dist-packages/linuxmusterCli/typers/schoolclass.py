import sys
import typer
from typing_extensions import Annotated

from rich.console import Console
from rich import print
from rich.table import Table

from linuxmusterTools.common import lprint, SchoolclassExistsError
from linuxmusterTools.ldapconnector import (
    LMNLdapReader as lr,
    LMNSchoolclass,
    delete_schoolclass_subgroups,
    orphan_schoolclass_subgroups,
)
from linuxmusterTools.ldapconnector.checks import is_valid_school, valid_schools
from .state import state
from .format import printf, outformat, sort_schoolclasses, error


console = Console(emoji=False)
app = typer.Typer()

ATTIC_OU = ',OU=attic,'

@app.command(help="""Manage schoolclasses' groups.""")
def sync(
        schoolclass: Annotated[str, typer.Option("--schoolclass", "-c", help="Comma separated list of schoolclasses to handle")] = '',
        sync_teachers: Annotated[bool, typer.Option("--teachers", help="Update the teachers group and the sophomorixAdmins of this schoolclass")] = False,
        sync_students: Annotated[bool, typer.Option("--students", help="Update the students group of this schoolclass")] = False,
        sync_parents: Annotated[bool, typer.Option("--parents", help="Update the parents group of this schoolclass")] = False,
        sync_groups: Annotated[bool, typer.Option("--groups", help="Update the parents, teachers and students groups of this schoolclass")] = False,
        sync_all: Annotated[bool, typer.Option("--all", help="Update the parents, teachers and students groups of all schoolclasses")] = False,
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        ):


    if not sync_all and not schoolclass:
        typer.secho("Please select at least a schoolclass or the option --all", fg=typer.colors.RED)
        return

    if not is_valid_school(school):
        error(f"Unknown school {school}. Available schools: {', '.join(valid_schools())}")
        raise typer.Exit(code=1)

    if sync_all:
        sync_teachers, sync_students, sync_parents = True, True, True
        schoolclasses = [
            c['cn']
            for c in lr.getvalues('/schoolclasses', ['cn', 'dn'], school=school)
            if ATTIC_OU not in c['dn']
        ]
    else:

        schoolclasses = schoolclass.split(',')

        sync_teachers = True if sync_teachers or sync_groups else False
        sync_students = True if sync_students or sync_groups else False
        sync_parents = True if sync_parents or sync_groups else False

        if not (sync_parents or sync_teachers or sync_students):
            typer.secho("Please choose at least one of the option --teachers, --parents or --students", fg=typer.colors.RED)
            sys.exit(0)

    to_sync = [
        ('teachers', sync_teachers),
        ('parents', sync_parents),
        ('students', sync_students),
    ]
    failures = []

    for schoolclass in schoolclasses:
        lprint.lmn(f"lmncli: Checking groups of schoolclass {schoolclass} in {school}")

        try:
            schoolclass_group = LMNSchoolclass(schoolclass, school=school)
        except Exception as e:
            # Keep syncing the other schoolclasses, and report at the end
            error(f"\t--> {str(e)}")
            failures.append(schoolclass)
            continue

        for group_type, wanted in to_sync:
            if not wanted:
                continue

            try:
                lprint.lmn(f"\t--> {group_type} group", end="\r")
                getattr(schoolclass_group, f'{group_type}_group').fill_members()
                lprint.lmn(f"\t--> {group_type} group ✅")
            except Exception as e:
                error(f"\t--> {group_type} group ❌ {str(e)}")
                failures.append(f"{schoolclass}-{group_type}")

        if sync_teachers:
            # sophomorix stores the teachers of a class in sophomorixAdmins and
            # rebuilds member from it, so both views have to stay equal
            try:
                lprint.lmn(f"\t--> sophomorixAdmins", end="\r")
                schoolclass_group.fill_admins()
                lprint.lmn(f"\t--> sophomorixAdmins ✅")
            except Exception as e:
                error(f"\t--> sophomorixAdmins ❌ {str(e)}")
                failures.append(f"{schoolclass}-admins")

    if failures:
        error(f"Could not sync: {', '.join(failures)}")
        raise typer.Exit(code=1)

@app.command(help="""Delete the groups left behind by a deleted schoolclass.""")
def cleanup(
        schoolclass: Annotated[str, typer.Option("--schoolclass", "-c", help="Comma separated list of deleted schoolclasses to clean up")] = '',
        cleanup_all: Annotated[bool, typer.Option("--all", help="Clean up every schoolclass which does not exist anymore")] = False,
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        ):

    if not cleanup_all and not schoolclass:
        typer.secho("Please select at least a schoolclass or the option --all", fg=typer.colors.RED)
        return

    if not is_valid_school(school):
        error(f"Unknown school {school}. Available schools: {', '.join(valid_schools())}")
        raise typer.Exit(code=1)

    if cleanup_all:
        schoolclasses = orphan_schoolclass_subgroups(school=school)

        if not schoolclasses:
            lprint.lmn(f"lmncli: No group of a deleted schoolclass found in {school}")
            return
    else:
        schoolclasses = schoolclass.split(',')

    failures = []

    for schoolclass in schoolclasses:
        lprint.lmn(f"lmncli: Cleaning up the groups of the deleted schoolclass {schoolclass} in {school}")

        try:
            deleted = delete_schoolclass_subgroups(schoolclass, school=school)
        except SchoolclassExistsError as e:
            # Keep cleaning up the other schoolclasses, and report at the end
            error(f"\t--> {str(e)}")
            failures.append(schoolclass)
            continue
        except Exception as e:
            error(f"\t--> {str(e)}")
            failures.append(schoolclass)
            continue

        if not deleted:
            lprint.lmn(f"\t--> nothing left to delete")
            continue

        for dn in deleted:
            lprint.lmn(f"\t--> deleted {dn}")

    if failures:
        error(f"Could not clean up: {', '.join(failures)}")
        raise typer.Exit(code=1)

@app.command(help="""Print schoolclasses teacher's memberships.""")
def teachers(
    schoolclass: Annotated[str, typer.Option("--schoolclass", "-c", help="Comma separated list of schoolclasses to handle")] = '',
    school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
    ):

    if not is_valid_school(school):
        error(f"Unknown school {school}. Available schools: {', '.join(valid_schools())}")
        raise typer.Exit(code=1)

    if not schoolclass:
        schoolclasses = [
            c for c in lr.get('/schoolclasses', school=school)
            if ATTIC_OU not in c['dn']
        ]
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
