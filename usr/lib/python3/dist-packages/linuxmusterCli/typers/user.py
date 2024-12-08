import typer
from typing_extensions import Annotated
from math import ceil
from datetime import datetime
from rich import print, box
from rich.layout import Layout
from rich.table import Table
from rich.console import Console
from rich.pretty import pprint
from linuxmusterTools.ldapconnector import LMNLdapReader as lr


console = Console(emoji=False)
app = typer.Typer()

def convert_sophomorix_time(t):
    try:
        return  datetime.strptime(t, '%Y%m%d%H%M%S.%fZ').strftime("%d %b %Y %H:%M:%S")
    except Exception:
        return t

def outformat(value, fieldname=""):
    if "Date" in fieldname:
        return convert_sophomorix_time(value)

    if isinstance(value, list):
        return ','.join(value)
    if str(value) == 'True':
        return ":white_heavy_check_mark:"
    if str(value) == 'False':
        return ":cross_mark:"
    return value

@app.callback(
    invoke_without_command=True,
    help="""Show user details."""
)
def ls(
        user: Annotated[str, typer.Argument()] = '',
        school: Annotated[str, typer.Option("--school", "-s")] = None,
        full: Annotated[bool, typer.Option("--full", "-f")] = False,
        ):

    user = user.lower()

    if school is not None:
        kwargs = {"school": school}
    else:
        kwargs = {}

    if user.endswith("-exam"):
        users_data = lr.get(f'/users/exam/{user}', **kwargs)
    else:
        users_data = lr.get(f'/users/{user}', **kwargs)

    if not users_data:
        try:
            killlog = open("/var/log/sophomorix/userlog/user-kill.log", "r")
            for line in reversed(list(killlog)):
                if f'::{user}::' in line:
                    killdate = convert_sophomorix_time(line.split('::')[2])
                    console.print(f"Account of user {user} was killed at {killdate}")
                    break
            killlog.close()
            return
        except Exception as e:
            console.print(str(e))

        console.print(f"User {user} not found.")
        return

    if not full:
        samba = ['sAMAccountType', 'sophomorixAdminFile', 'sophomorixComment', 'sophomorixCreationDate', 'sophomorixDeactivationDate', 'sophomorixExamMode', 'sophomorixExitAdminClass', 'sophomorixFirstnameASCII', 'sophomorixFirstnameInitial', 'sophomorixFirstPassword', 'sophomorixIntrinsic2', 'sophomorixSchoolname', 'sophomorixSchoolPrefix', 'sophomorixStatus', 'sophomorixSurnameASCII', 'sophomorixSurnameInitial', 'sophomorixTolerationDate', 'sophomorixUnid', 'sophomorixUserToken', 'sophomorixWebuiDashboard', 'unixHomeDirectory', 'homeDrive', ]
        custom = ['proxyAddresses', 'sophomorixCustom1', 'sophomorixCustom2', 'sophomorixCustom3', 'sophomorixCustom4', 'sophomorixCustom5', 'sophomorixCustomMulti1', 'sophomorixCustomMulti2', 'sophomorixCustomMulti3', 'sophomorixCustomMulti4', 'sophomorixCustomMulti5']
        person = ['sophomorixRole', 'sophomorixBirthdate', 'sn', 'cn', 'displayName', 'givenName', 'mail', 'name', 'sophomorixAdminClass',  'sAMAccountName']
        paths = ['dn', 'homeDirectory']
        groups = ['printers', 'projects', 'schoolclasses']
        # management = ['internet', 'intranet', 'isAdmin', 'printing', 'webfilter', 'wifi']
        quota = ['sophomorixCloudQuotaCalculated', 'sophomorixMailQuotaCalculated', 'sophomorixQuota']

        output = {}

        for name, domain in {'Custom':custom, 'Person': person, 'Groups':groups, 'Quota':quota, 'Paths':paths}.items():
            if name in ['Person', 'Paths']:
                color = 'green'
            elif name == 'Custom':
                color = 'blue'
            else:
                color = "bright_magenta"
            output[name] = Table(show_header=False, title=f"[{color}]{name}", border_style=color, expand=True, box=box.ROUNDED)
            output[name].add_column(style="cyan")
            output[name].add_column(style="yellow")
            for field in domain:
                output[name].add_row(field, outformat(users_data[field]))

        output['Management'] = Table(show_header=False, title="[bright_magenta]Management", border_style="bright_magenta", expand=True, box=box.ROUNDED)
        output['Management'].add_row(f'{"internet":<12}' + outformat(users_data['internet']), f'{"intranet":<12}' + outformat(users_data['intranet']), f'{"wifi":<12}' + outformat(users_data['wifi']))
        output['Management'].add_row(f'{"isAdmin":<12}' + outformat(users_data['isAdmin']), f'{"printing":<12}' + outformat(users_data['printing']), f'{"webfilter":<12}' + outformat(users_data['webfilter']))

        output['Samba'] = Table(show_header=False, title="[bright_black]Samba", border_style="bright_black", expand=True, box=box.ROUNDED)
        output['Samba'].add_column(style="cyan")
        output['Samba'].add_column(style="yellow")
        output['Samba'].add_column(style="cyan")
        output['Samba'].add_column(style="yellow")
        half = ceil(len(samba)/2)
        for index in range(half):
            field1 = samba[index]
            field2 = samba[index + half] if index+half < len(samba) else None
            output['Samba'].add_row(
                field1,
                outformat(users_data.get(field1,''), fieldname=field1),
                field2,
                outformat(users_data.get(field2, ''), fieldname=field2)
            )

        layout = Layout()
        layout.split_column(
            Layout(name="upper"),
            Layout(name="middle"),
            Layout(name="lower")
        )
        layout["upper"].split_row(
            Layout(name="person"),
            Layout(name="right"),
        )
        layout["middle"].split_row(
            Layout(name="paths"),
            Layout(name="quota"),
        )
        layout["right"].split(
            Layout(name="groups"),
            Layout(name="management"),
        )
        layout["lower"].split_row(
            Layout(name="custom"),
            Layout(name="samba"),
        )

        layout["upper"].size = 13
        layout["middle"].size = 6
        layout["samba"].ratio = 2

        layout["samba"].update(output['Samba'])
        layout["groups"].update(output['Groups'])
        layout["management"].update(output['Management'])
        layout["person"].update(output['Person'])
        layout["paths"].update(output['Paths'])
        layout["custom"].update(output['Custom'])
        layout["quota"].update(output['Quota'])

        print(layout)
    else:
        # We can surely do better here
        pprint(users_data)
