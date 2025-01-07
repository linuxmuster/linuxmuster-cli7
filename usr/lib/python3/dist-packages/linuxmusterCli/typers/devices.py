import typer
from typing_extensions import Annotated

from rich.console import Console
from rich.table import Table
from linuxmusterTools.lmnfile import LMNFile
from linuxmusterTools.ldapconnector import LMNLdapReader as lr
from .state import state
from .format import printf


console = Console(emoji=False)
app = typer.Typer()

@app.callback(
    invoke_without_command=True,
    help="""List all devices which hostname, mac or room containing FILTER_STR."""
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
            filter_str in d['hostname'].lower() \
            or filter_str in d['mac'].lower() \
            or filter_str in d['room'].lower()\
            or filter_str in d['ip'],
        devices_data
    ))

    ldap_data = lr.get('/devices', attributes=['cn', 'sophomorixComputerMAC'])

    devices = Table(title=f"{len(devices_data)} device(s)")
    devices.add_column("Room", style="cyan")
    devices.add_column("Hostname", style="green")
    devices.add_column("Group", style="green")
    devices.add_column("IP", style="yellow")
    devices.add_column("Mac", style="bright_magenta")
    devices.add_column("Role", style="bright_magenta")
    devices.add_column("LDAP", style="bright_magenta")

    output = []

    for device in devices_data:
        for ldap_device in ldap_data:
            if device['hostname'].lower() == ldap_device['cn'].lower() and device['mac'].lower() == ldap_device['sophomorixComputerMAC'].lower():
                devices.add_row(device['room'], device['hostname'], device['group'], device['ip'], device['mac'], device['sophomorixRole'], "Registered")
                output.append([device['room'], device['hostname'], device['group'], device['ip'], device['mac'], device['sophomorixRole'], "Registered"])
                break
        else:
            devices.add_row(device['room'], device['hostname'], device['group'], device['ip'], device['mac'], device['sophomorixRole'], "Not registered")
            output.append([device['room'], device['hostname'], device['group'], device['ip'], device['mac'], device['sophomorixRole'], "Not registered"])

    if state.format:
        printf.format(output)
    else:
        console.print(devices)
