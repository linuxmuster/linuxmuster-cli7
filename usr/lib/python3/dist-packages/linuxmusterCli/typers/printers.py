import typer
from typing_extensions import Annotated

from rich.console import Console
from rich.table import Table
from rich import print
from linuxmusterTools.lmnfile import LMNFile
from linuxmusterTools.ldapconnector import LMNLdapReader as lr
from .state import state
from .format import printf, outformat


console = Console(emoji=False)
app = typer.Typer()

@app.callback(
    invoke_without_command=True,
    help="""List all printers which hostname, ip or user / room member containing FILTER_STR."""
)
def ls(
        filter_str: Annotated[str, typer.Argument()] = '',
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        ):
    if school != 'default-school':
        prefix = f'{school}.'
    else:
        prefix = ''
   
    filter_str = filter_str.lower()

    with LMNFile(f'/etc/linuxmuster/sophomorix/{school}/{prefix}devices.csv', 'r') as f:
        devices_data = list(filter(lambda d:d['room'][0] != "#", f.read()))
        devices_data = sorted(devices_data, key=lambda d: (d['room'], d['hostname']))

    devices_data = list(filter(
        lambda d: \
            d['sophomorixRole'] == 'printer' and \
            (filter_str in d['hostname'].lower() \
            or filter_str in d['ip']),
        devices_data
    ))

    ldap_data = lr.get('/printers', attributes=['cn', 'member', 'sophomorixHidden', 'sophomorixJoinable'])

    printers = Table(title=f"{len(devices_data)} printer(s)")
    printers.add_column("Room", style="cyan")
    printers.add_column("Hostname", style="green")
    printers.add_column("IP", style="blue")
    printers.add_column("User(s) access", style="yellow")
    printers.add_column("Room(s) access", style="yellow")
    printers.add_column("Hidden", justify="center")
    printers.add_column("Joinable", justify="center")

    output = [[c.header for c in printers.columns]]

    for device in devices_data:
        for ldap_device in ldap_data:
            if device['hostname'].lower() == ldap_device['cn'].lower():
                computer_members = []
                user_members = []

                for member_dn in ldap_device['member']:
                    cn = member_dn.split(',')[0].split('=')[1]
                    if ',OU=Devices,' in member_dn:
                        computer_members.append(cn)
                    else:
                        user_members.append(cn)

                printers.add_row(
                    device['room'],
                    device['hostname'],
                    device['ip'],
                    ','.join(user_members),
                    ','.join(computer_members),
                    outformat(ldap_device['sophomorixHidden']),
                    outformat(ldap_device['sophomorixJoinable']),
                )
                output.append([
                    device['room'],
                    device['hostname'],
                    device['ip'],
                    ','.join(user_members),
                    ','.join(computer_members),
                    ldap_device['sophomorixHidden'],
                    ldap_device['sophomorixJoinable'],
                ])
                break

    if state.format:
        printf.format(output)
    else:
        print(printers)
