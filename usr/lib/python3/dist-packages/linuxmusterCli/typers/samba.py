import typer
from typing_extensions import Annotated

from rich.console import Console
from rich.table import Table
from linuxmusterTools.samba import GPOManager, smbstatus


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
    gpos.add_column("Path", style="magenta")

    for name, details in GPOS.items():
        gpos.add_row(name, details.gpo, details.path)
    console.print(gpos)

@app.command(help="Display all configured drives in linuxmuster.net for the specified school.")
def drives(school: Annotated[str, typer.Option("--school", "-s")] = 'default-school'):
    drives = Table()
    drives.add_column("Name", style="green")
    drives.add_column("Letter", style="cyan")
    drives.add_column("Use letter", style="cyan")
    drives.add_column("Label", style="magenta")
    drives.add_column("Disable", style="magenta")
    # drives.add_column("Visible teachers", style="magenta")
    # drives.add_column("Visible students", style="magenta")

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
        users_connections.add_column("IP", style="cyan")
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

