import sys
import typer
from typing_extensions import Annotated

from rich.console import Console
from rich.table import Table
from rich import print

from linuxmusterTools.ldapconnector import LMNLdapReader as lr, LMNGroup, find_legacy_groups
from .state import state
from .format import printf, outformat


console = Console(emoji=False)
app = typer.Typer()

@app.command(help="""List all lmngroups whose name contains FILTER_STR.""")
def ls(
        filter_str: Annotated[str, typer.Argument()] = '',
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        ):

    filter_str = filter_str.lower()

    groups_data = lr.get('/groups', school=school)
    groups_data = [g for g in groups_data if g['sophomorixType'] == 'lmngroup']
    groups_data = list(filter(lambda g: filter_str in g['cn'].lower(), groups_data))
    groups_data = sorted(groups_data, key=lambda g: g['cn'])

    groups = Table(title=f"{len(groups_data)} lmngroup(s)", show_lines=True)
    groups.add_column("Name", style="cyan")
    groups.add_column("Description", style="white")
    groups.add_column("Member(s)", style="yellow")
    groups.add_column("Hidden", justify="center")
    groups.add_column("Joinable", justify="center")

    output = [[c.header for c in groups.columns]]

    for group in groups_data:
        member_cns = []
        for member_dn in group['member']:
            parts = member_dn.split(',')[0].split('=')
            if len(parts) < 2:
                continue
            member_cns.append(parts[1])

        groups.add_row(
            group['cn'],
            group['description'],
            ','.join(member_cns),
            outformat(group['sophomorixHidden']),
            outformat(group['sophomorixJoinable']),
        )
        output.append([
            group['cn'],
            group['description'],
            ','.join(member_cns),
            group['sophomorixHidden'],
            group['sophomorixJoinable'],
        ])

    if state.format:
        printf.format(output)
    else:
        print(groups)

@app.command(help="""Manage a lmngroup's members.""")
def manage(
        group: Annotated[str, typer.Argument(help="The lmngroup to modify")],
        add_members: Annotated[str, typer.Option("--add-members", help="Comma separated list of users to add to GROUP")] = '',
        remove_members: Annotated[str, typer.Option("--remove-members", help="Comma separated list of users to remove from GROUP")] = '',
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        ):

    if not add_members and not remove_members:
        typer.secho("Please choose at least one of the option --add-members or --remove-members", fg=typer.colors.RED)
        sys.exit(0)

    try:
        lmngroup = LMNGroup(group, school=school)
    except Exception as e:
        sys.exit(str(e))

    if lmngroup.new:
        sys.exit(f"Group {group} does not exist in ldap.")

    if add_members:
        to_add = add_members.split(',')
        failures = lmngroup.add_members(to_add)
        added = [user for user in to_add if user not in dict(failures)]
        if added:
            typer.secho(f"Added: {', '.join(added)}", fg=typer.colors.GREEN)
        for user, error in failures:
            typer.secho(f"Could not add {user}: {error}", fg=typer.colors.RED)

    if remove_members:
        to_remove = remove_members.split(',')
        failures = lmngroup.remove_members(to_remove)
        removed = [user for user in to_remove if user not in dict(failures)]
        if removed:
            typer.secho(f"Removed: {', '.join(removed)}", fg=typer.colors.GREEN)
        for user, error in failures:
            typer.secho(f"Could not remove {user}: {error}", fg=typer.colors.RED)

@app.command(help="""Create a new lmngroup.""")
def create(
        group: Annotated[str, typer.Argument(help="The lmngroup to create")],
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        ):

    try:
        lmngroup = LMNGroup(group, school=school)
    except Exception as e:
        sys.exit(str(e))

    if not lmngroup.new:
        sys.exit(f"Group {group} already exists in ldap.")

    lmngroup.create()
    typer.secho(f"Group {group} created.", fg=typer.colors.GREEN)

@app.command(help="""Delete a lmngroup.""")
def delete(
        group: Annotated[str, typer.Argument(help="The lmngroup to delete")],
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        ):

    try:
        lmngroup = LMNGroup(group, school=school)
    except Exception as e:
        sys.exit(str(e))

    if lmngroup.new:
        sys.exit(f"Group {group} does not exist in ldap.")

    typer.confirm(f"Delete group {group}?", abort=True)
    lmngroup.delete()
    typer.secho(f"Group {group} deleted.", fg=typer.colors.GREEN)

@app.command(help="""List legacy sophomorix-groups not yet migrated to OU=LMNGroups.""")
def legacy(
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        ):

    groups_data = find_legacy_groups(school=school)
    groups_data = sorted(groups_data, key=lambda g: g['cn'])

    groups = Table(title=f"{len(groups_data)} legacy sophomorix-group(s)", show_lines=True)
    groups.add_column("Name", style="cyan")
    groups.add_column("Description", style="white")
    groups.add_column("Member(s)", style="yellow")

    output = [[c.header for c in groups.columns]]

    for group in groups_data:
        member_cns = []
        for member_dn in group['member']:
            parts = member_dn.split(',')[0].split('=')
            if len(parts) < 2:
                continue
            member_cns.append(parts[1])

        groups.add_row(group['cn'], group['description'], ','.join(member_cns))
        output.append([group['cn'], group['description'], ','.join(member_cns)])

    if state.format:
        printf.format(output)
    else:
        print(groups)

@app.command(help="""Migrate a legacy sophomorix-group (OU=Projects) to OU=LMNGroups.""")
def migrate(
        group: Annotated[str, typer.Argument(help="The group to migrate")],
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        ):

    try:
        lmngroup = LMNGroup(group, school=school)
    except Exception as e:
        sys.exit(str(e))

    if lmngroup.new:
        sys.exit(f"Group {group} does not exist in ldap.")

    if lmngroup.data['sophomorixType'] == 'lmngroup':
        sys.exit(f"Group {group} is already a lmngroup, nothing to migrate.")

    old_dn = lmngroup.data['distinguishedName']
    lmngroup.migrate()
    typer.secho(f"Group {group} migrated to OU=LMNGroups.", fg=typer.colors.GREEN)

    # migrate() is expected to move the entry, not copy it: this leftover
    # check is a safety net in case the move didn't clean up the old dn.
    if lr.get(f'/dn/{old_dn}'):
        typer.secho(f"Warning: a leftover entry still exists at {old_dn}.", fg=typer.colors.YELLOW)
        if typer.confirm(f"Delete the leftover entry at {old_dn}?"):
            lmngroup.lw._del(old_dn)
            typer.secho("Leftover entry deleted.", fg=typer.colors.GREEN)
        else:
            typer.secho(f"Leftover entry left in place at {old_dn}.", fg=typer.colors.YELLOW)
