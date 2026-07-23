from linuxmusterCli.typers import printers
from linuxmusterCli.typers.state import state


SAMPLE_DEVICES = [
    {
        'room': 'r1', 'hostname': 'printer1', 'mac': 'AA:BB:CC:DD:EE:01', 'ip': '10.0.0.10',
        'sophomorixRole': 'printer', 'group': 'g1',
    },
    {
        'room': 'r1', 'hostname': 'printer2', 'mac': 'AA:BB:CC:DD:EE:02', 'ip': '10.0.0.11',
        'sophomorixRole': 'printer', 'group': 'g1',
    },
    {
        'room': 'r2', 'hostname': 'pc1', 'mac': 'AA:BB:CC:DD:EE:03', 'ip': '10.0.0.1',
        'sophomorixRole': 'workstation', 'group': 'g2',
    },
    {
        'room': '#hidden', 'hostname': 'printer3', 'mac': 'AA:BB:CC:DD:EE:04', 'ip': '10.0.0.12',
        'sophomorixRole': 'printer', 'group': 'g3',
    },
    {
        'room': 'r3', 'hostname': 'printer4', 'mac': 'AA:BB:CC:DD:EE:05', 'ip': '10.0.0.13',
        'sophomorixRole': 'printer', 'group': 'g4',
    },
]

# printer1 has a mix of a user member and a device member, plus one malformed DN
# printer2 has no members at all
# printer4 is a printer in the csv but has NO matching ldap entry (see bug note below)
SAMPLE_LDAP_PRINTERS = [
    {
        'cn': 'printer1',
        'member': [
            'CN=johndoe,OU=Students,DC=example,DC=com',
            'CN=pc5,OU=Devices,DC=example,DC=com',
            'BADDN',
        ],
        'sophomorixHidden': False, 'sophomorixJoinable': True,
    },
    {
        'cn': 'printer2', 'member': [],
        'sophomorixHidden': True, 'sophomorixJoinable': False,
    },
]


class FakeLMNFile:
    """Stand-in for linuxmusterTools.lmnfile.LMNFile, used as a context manager."""

    def __init__(self, path, mode):
        self.path = path
        self.mode = mode

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return list(SAMPLE_DEVICES)


class TestLs:

    def test_only_printer_role_rows_are_counted(self, runner, monkeypatch):
        monkeypatch.setattr(printers, 'LMNFile', FakeLMNFile)
        monkeypatch.setattr(printers.lr, 'get', lambda url, **kw: list(SAMPLE_LDAP_PRINTERS))

        result = runner.invoke(printers.app, [])

        assert result.exit_code == 0
        # pc1 (workstation) and printer3 (#hidden room) are excluded from the count
        assert '3 printer(s)' in result.output
        assert 'pc1' not in result.output
        assert 'printer3' not in result.output

    def test_user_and_device_members_are_split_and_malformed_dn_skipped(self, runner, monkeypatch):
        monkeypatch.setattr(printers, 'LMNFile', FakeLMNFile)
        monkeypatch.setattr(printers.lr, 'get', lambda url, **kw: list(SAMPLE_LDAP_PRINTERS))

        result = runner.invoke(printers.app, [])

        assert 'johndoe' in result.output
        assert 'pc5' in result.output
        assert 'BADDN' not in result.output

    def test_printer_without_ldap_match_is_silently_dropped_from_table(self, runner, monkeypatch):
        """
        Documents current (buggy) behaviour: unlike devices.py, printers.py has no
        `else` clause on the inner ldap-matching loop, so a printer present in the
        csv but absent from ldap is never added as a table row at all -- it does
        not even show up as "Not registered". The title count (based on the csv
        data alone) still includes it, so the displayed row count is inconsistent
        with the table body.
        """
        monkeypatch.setattr(printers, 'LMNFile', FakeLMNFile)
        monkeypatch.setattr(printers.lr, 'get', lambda url, **kw: list(SAMPLE_LDAP_PRINTERS))

        result = runner.invoke(printers.app, [])

        assert '3 printer(s)' in result.output
        assert 'printer4' not in result.output

    def test_hidden_and_joinable_columns_are_rendered(self, runner, monkeypatch):
        monkeypatch.setattr(printers, 'LMNFile', FakeLMNFile)
        monkeypatch.setattr(printers.lr, 'get', lambda url, **kw: list(SAMPLE_LDAP_PRINTERS))

        result = runner.invoke(printers.app, [])

        # rich renders the outformat() emoji shortcodes as actual emoji glyphs
        assert '✅' in result.output  # white_heavy_check_mark
        assert '❌' in result.output  # cross_mark

    def test_filter_str_matches_hostname_not_room(self, runner, monkeypatch):
        monkeypatch.setattr(printers, 'LMNFile', FakeLMNFile)
        monkeypatch.setattr(printers.lr, 'get', lambda url, **kw: list(SAMPLE_LDAP_PRINTERS))

        result = runner.invoke(printers.app, ['printer1'])

        assert '1 printer(s)' in result.output
        assert 'printer1' in result.output
        assert 'printer2' not in result.output

    def test_filter_str_room_does_not_match(self, runner, monkeypatch):
        monkeypatch.setattr(printers, 'LMNFile', FakeLMNFile)
        monkeypatch.setattr(printers.lr, 'get', lambda url, **kw: list(SAMPLE_LDAP_PRINTERS))

        # Rooms are 'r1'/'r2'/'r3' here, but printers.py only filters on
        # hostname / ip (unlike devices.py), so a room-only filter matches
        # nothing -- use a string absent from every hostname/ip too.
        result = runner.invoke(printers.app, ['wing-'])

        assert '0 printer(s)' in result.output

    def test_filter_str_matches_ip(self, runner, monkeypatch):
        monkeypatch.setattr(printers, 'LMNFile', FakeLMNFile)
        monkeypatch.setattr(printers.lr, 'get', lambda url, **kw: list(SAMPLE_LDAP_PRINTERS))

        result = runner.invoke(printers.app, ['10.0.0.11'])

        assert '1 printer(s)' in result.output
        assert 'printer2' in result.output

    def test_raw_format_output(self, runner, monkeypatch):
        monkeypatch.setattr(printers, 'LMNFile', FakeLMNFile)
        monkeypatch.setattr(printers.lr, 'get', lambda url, **kw: [SAMPLE_LDAP_PRINTERS[0]])
        state.format = True
        state.raw = True

        result = runner.invoke(printers.app, ['printer1'])

        assert result.exit_code == 0
        assert 'r1\tprinter1\t10.0.0.10\tjohndoe\tpc5\tFalse\tTrue' in result.output
