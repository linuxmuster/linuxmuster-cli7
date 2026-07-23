from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

# typers/__init__.py eagerly imports every typer submodule as soon as any single
# one of them is imported (`from .samba import *` runs first). samba.py in turn
# instantiates GPOManager() at module level, which opens the real Samba/AD
# database. Neutralize it here, before anything imports linuxmusterCli.typers,
# so the test suite never depends on (or mutates) a live domain.
import linuxmusterTools.samba_util as samba_util
samba_util.GPOManager = lambda: MagicMock(gpos={})


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def reset_cli_state():
    """
    typers.state.state is a process-wide singleton flipped by the top-level
    --raw/--csv callback in main.py. Tests invoke each typer's own `app`
    directly (bypassing that callback), so reset it around every test.
    """

    from linuxmusterCli.typers.state import state
    state.raw = False
    state.csv = False
    state.format = False
    yield
    state.raw = False
    state.csv = False
    state.format = False
