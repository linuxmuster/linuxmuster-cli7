import typer
from datetime import datetime
from typing_extensions import Annotated

from rich.console import Console
from rich.table import Table
from linuxmusterTools.samba_util import smbstatus, SambaToolDNS
from linuxmusterTools.samba_util.log import last_login
from .state import state
from .format import printf, error


console = Console(emoji=False)
app = typer.Typer(help="Manage samba shares and connections.")

@app.command(help="Display all GPOS details on the system.")
def gpos():
    from linuxmusterTools.samba_util import GPOManager
    GPOS = GPOManager().gpos

    gpos = Table()
    gpos.add_column("Name", style="green")
    gpos.add_column("GPO", style="cyan")
    gpos.add_column("Path", style="bright_magenta")

    data = [[c.header for c in gpos.columns]]
    for name, details in GPOS.items():
        gpos.add_row(name, details.gpo, details.path)
        data.append([name, details.gpo, details.path])

    if state.format:
        printf.format(data)
    else:
        console.print(gpos)

@app.command(help="Display all configured drives in linuxmuster.net for the specified school.")
def drives(school: Annotated[str, typer.Option("--school", "-s")] = 'default-school'):
    from linuxmusterTools.samba_util import GPOManager
    GPOS = GPOManager().gpos

    drives = Table()
    drives.add_column("Name", style="green")
    drives.add_column("Letter", style="yellow")
    drives.add_column("Use letter", style="cyan")
    drives.add_column("Label", style="bright_magenta")
    drives.add_column("Disable", style="bright_magenta")
    # drives.add_column("Visible teachers", style="bright_magenta")
    # drives.add_column("Visible students", style="bright_magenta")

    gpo_key = f"sophomorix:school:{school}"
    if gpo_key not in GPOS:
        error(f"No GPO found for school '{school}'.")
        raise typer.Exit()

    data = [[c.header for c in drives.columns]]
    for drive in GPOS[gpo_key].drivemgr.drives:
        drives.add_row(
                drive.id, 
                drive.letter, 
                str(drive.userLetter), 
                drive.label, 
                str(drive.disabled),
                # str(drive.visible('teachers')),
                # str(drive.visible('students'))
        )
        data.append([
            drive.id,
            drive.letter,
            str(drive.userLetter),
            drive.label,
            str(drive.disabled),]
            # str(drive.visible('teachers')),
            # str(drive.visible('students'))
        )

    if state.format:
        printf.format(data)
    else:
        console.print(drives)

@app.command(help="Display all current samba connections.")
def status(
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        users: Annotated[bool, typer.Option("--users", "-u")] = False,
        machines: Annotated[bool, typer.Option("--machines", "-m")] = False
    ):

    show_all = not (users ^ machines)

    conn = smbstatus.SMBConnections(school)

    if show_all or users:
        users_connections = Table()
        users_connections.add_column("User", style="green")
        users_connections.add_column("IP", style="yellow")
        users_connections.add_column("Hostname", style="cyan")
        users_connections.add_column("Date")

        data = [[c.header for c in users_connections.columns]]
        for user, connections in conn.connections.items():
            for details in connections:
                date = datetime.fromisoformat(details.auth_time).strftime('%Y-%m-%d %H:%M:%S')
                users_connections.add_row(
                        user,
                        details.machine,
                        details.hostname,
                        date,
                )
                data.append([
                    user,
                    details.machine,
                    details.hostname,
                    date,
                ])

        if state.format:
            printf.format(data)
        else:
            console.print(users_connections)

    if show_all or machines:
        machines_connections = Table()
        machines_connections.add_column("Machine", style="green")
        machines_connections.add_column("IP", style="cyan")
        machines_connections.add_column("Date")

        conn.get_machines()
        data = [[c.header for c in machines_connections.columns]]
        for machine, details in conn.machines.items():
            date = datetime.fromisoformat(details.auth_time).strftime('%Y-%m-%d %H:%M:%S')
            machines_connections.add_row(
                    machine,
                    details.machine,
                    date,
            )
            data.append([
                machine,
                details.machine,
                date,
            ])

        if state.format:
            printf.format(data)
        else:
            console.print(machines_connections)


@app.command(help="Display all current DNS enries.")
def dns(
        school: Annotated[str, typer.Option("--school", "-s")] = 'default-school',
        root: Annotated[bool, typer.Option("--root")] = False,
        sub: Annotated[bool, typer.Option("--sub")] = False,
):
    
    DNS = SambaToolDNS().list()
    root_table = Table()
    root_table.add_column("Type", style="green")
    root_table.add_column("TTL", style="yellow")
    root_table.add_column("Value", style="cyan")

    dns_table = Table()
    dns_table.add_column("Host", style="green")
    dns_table.add_column("Type", style="green")
    dns_table.add_column("TTL", style="yellow")
    dns_table.add_column("Value", style="cyan")

    root_data = [[c.header for c in root_table.columns]]
    for entry in DNS['root']:
        root_table.add_row(entry['type'], entry['ttl'], entry['value'])
        root_data.append([entry['type'], entry['ttl'], entry['value']])

    dns_data = [[c.header for c in dns_table.columns]]
    for entry in DNS['sub']:
        dns_table.add_row(entry['host'], entry['type'], entry['ttl'], entry['value'])
        dns_data.append([entry['host'], entry['type'], entry['ttl'], entry['value']])

    if root or not sub:
        if state.format:
            printf.format(root_data)
        else:
            console.print(root_table)

    if sub or not root:
        if state.format:
            printf.format(dns_data)
        else:
            console.print(dns_table)

@app.command(help="Get the last login of an user or on a computer")
def lastlogin(
        pattern: Annotated[str, typer.Argument()] = '',
        all_logs: Annotated[bool, typer.Option("--all", "-a")] = False
    ):
    logins = Table()
    logins.add_column("User", style="green")
    logins.add_column("IP", style="cyan")
    logins.add_column("Hostname", style="yellow")
    logins.add_column("Date", style="bright_magenta")

    data = [[c.header for c in logins.columns]]
    for entry in last_login(pattern, include_gz=all_logs):
        row = [entry['user'], entry['ip'], entry['hostname'] or '', str(entry['datetime'])]
        logins.add_row(*row)
        data.append(row)

    if state.format:
        printf.format(data)
    else:
        console.print(logins)

