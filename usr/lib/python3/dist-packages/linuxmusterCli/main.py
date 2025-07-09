#!/opt/linuxmuster/bin/python3

import sys
import typer
import subprocess
import logging
import logging.handlers
from termcolor import colored

from rich.console import Console
from rich.table import Table
from typers import (
    samba,
    linbo,
    devices,
    users,
    up,
    user,
    check_attic,
    userlog,
    check_parents,
    quotas,
    student
)
from typers.format import *
from typing_extensions import Annotated


class CLILogHandler(logging.StreamHandler):
    def __init__(self, stream):
        logging.StreamHandler.__init__(self, stream)

    def handle(self, record):

        msg = record.msg % record.args

        if record.levelname == 'DEBUG':
            s = colored(f'DEBUG:  {msg}\n', 'white')
        if record.levelname == 'INFO':
            s = colored(f'INFO:  {msg}\n', 'green', attrs=['bold'])
        if record.levelname == 'WARNING':
            s = colored(f'WARNING:  {msg}\n', 'yellow', attrs=['bold'])
        if record.levelname == 'ERROR':
            s = colored(f'ERROR !  {msg}\n', 'red', attrs=['bold'])

        s += "\n"

        self.stream.write(s)

# Reduce log level for linuxmusterTools
for name, logger in logging.root.manager.loggerDict.items():
    if 'linuxmusterTools' in name:
        logging.getLogger(name).setLevel(logging.WARNING)

log = logging.getLogger()
log.setLevel(logging.INFO)
stdout = CLILogHandler(sys.stdout)
stdout.setLevel(logging.INFO)
log.handlers = [stdout]

console = Console()
app = typer.Typer(no_args_is_help=True, add_completion=False, context_settings={"help_option_names": ["-h", "--help"]},)
app.add_typer(samba.app, name='samba')
app.add_typer(linbo.app, name='linbo')
app.add_typer(devices.app, name='devices')
app.add_typer(users.app, name='users')
app.add_typer(user.app, name='user')
app.add_typer(up.app, name='up')
app.add_typer(check_attic.app, name='check_attic')
app.add_typer(check_parents.app, name='check_parents')
app.add_typer(userlog.app, name='userlog')
app.add_typer(quotas.app, name='quotas')
app.add_typer(student.app, name='student')

@app.callback()
def output(
        raw: Annotated[bool, typer.Option(help="Print the values without color and tab separated on the output.")] = False,
        csv: Annotated[bool, typer.Option(help="Print the values without color and separated by semicolon on the output.")] = False):
    if raw + csv == 0:
        return
    elif raw + csv > 1:
        error("You can not combine the options --raw, --json and --csv !")
        raise typer.Exit()

    state.format = True

    if raw:
        state.raw = True
    if csv:
        state.csv = True

@app.command(help="Lists linuxmuster.net packages installed.")
def version():
    packages = Table()
    packages.add_column("Status", style="green")
    packages.add_column("Packages", style="cyan")
    packages.add_column("Version", style="bright_magenta")

    command = "dpkg -l | grep 'linuxmuster\\|sophomorix'"
    p = subprocess.Popen(command, shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    for package in p.stdout.readlines():
        details = package.decode().split()
        status, name, version  = details[:3]
        packages.add_row(status, name, version)
    console.print(packages)

if __name__ == "__main__":
    app()
