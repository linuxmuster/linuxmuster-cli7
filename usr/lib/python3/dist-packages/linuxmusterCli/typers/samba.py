import typer
from typing_extensions import Annotated

from rich.console import Console
from rich.table import Table
from linuxmusterTools.samba_util import GPOManager, smbstatus, SambaToolDNS
from linuxmusterTools.samba_util.log import last_login


gpomgr = GPOManager()
GPOS = gpomgr.gpos

conn = smbstatus.SMBConnections()

console = Console(emoji=False)
app = typer.Typer(help="Manage samba shares and connections.")

@app.command(help="Display all GPOS details on the system.")
def gpos():
    gpos = Table()
    gpos.add_column("Name", style="green")
    gpos.add_column("GPO", style="cyan")
    gpos.add_column("Path", style="bright_magenta")

    for name, details in GPOS.items():
        gpos.add_row(name, details.gpo, details.path)
    console.print(gpos)

@app.command(help="Display all configured drives in linuxmuster.net for the specified school.")
def drives(school: Annotated[str, typer.Option("--school", "-s")] = 'default-school'):
    drives = Table()
    drives.add_column("Name", style="green")
    drives.add_column("Letter", style="yellow")
    drives.add_column("Use letter", style="cyan")
    drives.add_column("Label", style="bright_magenta")
    drives.add_column("Disable", style="bright_magenta")
    # drives.add_column("Visible teachers", style="bright_magenta")
    # drives.add_column("Visible students", style="bright_magenta")

    for drive in GPOS[f"sophomorix:school:{school}"].drivemgr.drives:
        drives.add_row(
                drive.id, 
                drive.letter, 
                str(drive.userLetter), 
                drive.label, 
                str(drive.disabled),
                # str(drive.visible('teachers')),
                # str(drive.visible('students'))
        )
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

        for user,details in conn.users.items():
            users_connections.add_row(
                    user,
                    details.machine,
                    details.hostname,
            )

        console.print(users_connections)

    if show_all or machines:
        machines_connections = Table()
        machines_connections.add_column("Machine", style="green")
        machines_connections.add_column("IP", style="cyan")

        conn.get_machines()
        for machine, details in conn.machines.items():
            machines_connections.add_row(
                    machine,
                    details.machine,
            )

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

    for entry in DNS['root']:
        root_table.add_row(entry['type'], entry['ttl'], entry['value'])

    for entry in DNS['sub']:
        dns_table.add_row(entry['host'], entry['type'], entry['ttl'], entry['value'])

    if root or not sub:
        console.print(root_table)

    if sub or not root:
        console.print(dns_table)

@app.command(help="Get the last login of an user or on a computer")
def lastlogin(pattern: Annotated[str, typer.Argument()] = None):
    logins = Table()
    logins.add_column("User", style="green")
    logins.add_column("IP", style="cyan")
    logins.add_column("Date", style="bright_magenta")

    last_logins = last_login(pattern)

    for entry in sorted(last_logins, key=lambda d: d["datetime"], reverse=True):
        logins.add_row(entry['user'], entry['ip'], str(entry['datetime']))
    console.print(logins)

