import os
import typer
from datetime import datetime
from typing_extensions import Annotated

from rich.console import Console
from rich.table import Table
from linuxmusterTools.lmnfile import LMNFile
from linuxmusterTools.linbo import LinboImageManager, list_workstations, last_sync_all
from .state import state
from .format import printf


LINBO_PATH = '/srv/linbo'
console = Console(emoji=False)
app = typer.Typer(help="Manage linbo images and groups.")
lim = LinboImageManager()

@app.command(help="Display all available linbo groups.")
def groups(school: Annotated[str, typer.Option("--school", "-s")] = 'default-school'):
    groups = Table()
    groups.add_column("Groups", style="green")
    groups.add_column("Devices", style="cyan")
    if school != 'default-school':
        prefix = f'{school}.'
    else:
        prefix = ''

    with LMNFile(f'/etc/linuxmuster/sophomorix/{school}/{prefix}devices.csv', 'r') as f:
        devices = f.read()

    data = []
    for file in os.listdir(LINBO_PATH):
        path = os.path.join(LINBO_PATH, file)
        if (
            file.startswith('start.conf.')
            and not file.endswith('.vdi')
            and not os.path.islink(path)
            and os.path.isfile(path)
        ):
            group = file.split(".")[-1]
            devices_count = 0
            for device in devices:
                if device['group'] == group:
                    devices_count += 1
            groups.add_row(group, str(devices_count))
            data.append([group, str(devices_count)])

    if state.format:
        printf.format(data)
    else:
        console.print(groups)

@app.command(help="Display all available linbo images.")
def images():
    images = Table(show_lines=True)
    images.add_column("Name", style="green")
    images.add_column("Size (MiB)", style="cyan")
    images.add_column("Backups", style="bright_magenta")
    images.add_column("Differential image", style="cyan")
    # images.add_column("Used in groups", style="cyan")

    data = []
    for name,group in lim.groups.items():
        size = str(round(group.base.size / 1024 / 1024))
        diff = "No"
        if group.diff_image:
            diff_size = round(group.diff_image.size / 1024 / 1024)
            diff = f"Yes ({diff_size} MiB)"
        images.add_row(name, size, '\n'.join(group.backups.keys()), diff)
        data.append([name, size, ','.join(group.backups.keys()), diff])

    if state.format:
        printf.format(data)
    else:
        console.print(images)

@app.command(help="Display last synchronisation date for all devices or the selected group.")
def lastsync(
    group: Annotated[str, typer.Argument()] = '',
    school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
):
    # Temporary UGLY solution. The code in linuxmusterTools must be rewritten

    def format(sync_data):
        epoch = sync_data['date']
        status = sync_data['status']

        if epoch == 'Never':
            return '[red]No date found[/red]'
        color_map = {
            'danger': 'red',
            'warning': 'yellow',
            'success': 'green'
        }
        color = color_map[status]
        date = datetime.fromtimestamp(epoch).strftime('%c')
        return f'[{color}]{date}[/{color}]'

    if group:
        devices = list_workstations(groups=[group])
    else:
        devices = list_workstations()

    last_sync_all(devices)

    for grp, hosts in devices.items():
        images = []
        if len(hosts['hosts']) > 0:
            images = hosts['hosts'][0]['images']
        if not images:
            continue

        sync = Table()
        sync.add_column('Hostname', style="cyan")
        sync.add_column('IP', style="cyan")
        data = [['Hostname', 'IP']]
        for image in images:
            sync.add_column(f'Last synchronisation for {image}')
            data[0].append(f'Last synchronisation for {image}')

        for host in hosts['hosts']:
            sync.add_row(
                host['hostname'],
                host['ip'],
                *[format(host['sync'][image]) for image in images]
            )
            data.append([
                host['hostname'],
                host['ip'],
                *[host['sync'][image] for image in images]
            ])

        if state.format:
            printf.format(data)
            print()
        else:
            console.print(sync)


