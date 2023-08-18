import os
import typer
from typing_extensions import Annotated

from rich.console import Console
from rich.table import Table
from linuxmusterTools.lmnfile import LMNFile
from linuxmusterTools.ldapconnector import LMNLdapReader as lr


console = Console(emoji=False)
app = typer.Typer()

@app.command()
def ls(school: Annotated[str, typer.Option("--school", "-s")] = 'default-school'):
    if school != 'default-school':
        prefix = f'{school}.'
    else:
        prefix = ''

    with LMNFile(f'/etc/linuxmuster/sophomorix/{school}/{prefix}devices.csv', 'r') as f:
        devices_data = sorted(f.read(), key=lambda d: (d['room'], d['hostname']))

    devices = Table(title=f"{len(devices_data)} devices")
    devices.add_column("Room", style="cyan")
    devices.add_column("Hostname", style="green")
    devices.add_column("IP", style="magenta")
    devices.add_column("Mac", style="magenta")
    for device in devices_data:
        devices.add_row(device['room'], device['hostname'], device['ip'], device['mac'])
    console.print(devices)

