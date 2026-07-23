from linuxmusterCli.typers import devices
from linuxmusterCli.typers.state import state


SAMPLE_DEVICES = [
    {
        'room': 'r1', 'hostname': 'pc1', 'mac': 'AA:BB:CC:DD:EE:01', 'ip': '10.0.0.1',
        'sophomorixRole': 'workstation', 'group': 'g1',
    },
    {
        'room': 'r1', 'hostname': 'pc2', 'mac': 'AA:BB:CC:DD:EE:02', 'ip': '10.0.0.2',
        'sophomorixRole': 'workstation', 'group': 'g1',
    },
    {
        'room': 'r2', 'hostname': 'dc1', 'mac': 'AA:BB:CC:DD:EE:03', 'ip': '10.0.0.3',
        'sophomorixRole': 'server', 'group': 'g2',
    },
    {
        'room': 'r2', 'hostname': 'nomatch', 'mac': 'AA:BB:CC:DD:EE:04', 'ip': '10.0.0.4',
        'sophomorixRole': 'workstation', 'group': 'g2',
    },
    {
        'room': '#excluded', 'hostname': 'hiddenhost', 'mac': 'AA:BB:CC:DD:EE:05', 'ip': '10.0.0.5',
        'sophomorixRole': 'workstation', 'group': 'g3',
    },
]

# pc1 matches ldap by hostname AND mac (case-insensitive) -> Registered
# pc2 matches ldap by hostname but mac differs, dn not a DC -> Unknown
# dc1 matches ldap by hostname, mac differs, dn is a Domain Controller -> Domain Controller
# unknownhost has no ldap counterpart at all -> Not registered
SAMPLE_LDAP_DEVICES = [
    {'cn': 'pc1', 'sophomorixComputerMAC': 'aa:bb:cc:dd:ee:01', 'dn': 'CN=pc1,OU=Devices,DC=example,DC=com'},
    {'cn': 'pc2', 'sophomorixComputerMAC': 'AA:BB:CC:DD:EE:99', 'dn': 'CN=pc2,OU=Devices,DC=example,DC=com'},
    {'cn': 'dc1', 'sophomorixComputerMAC': 'AA:BB:CC:DD:EE:99', 'dn': 'CN=dc1,OU=Domain Controllers,DC=example,DC=com'},
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

    def test_status_matches_mac_hostname_dc_and_unregistered(self, runner, monkeypatch):
        monkeypatch.setattr(devices, 'LMNFile', FakeLMNFile)
        monkeypatch.setattr(devices.lr, 'get', lambda url, **kw: list(SAMPLE_LDAP_DEVICES))

        result = runner.invoke(devices.app, [])

        assert result.exit_code == 0
        assert '4 device(s)' in result.output
        assert 'Registered' in result.output
        assert 'Unknown' in result.output
        assert 'Domain' in result.output and 'Controller' in result.output
        assert 'Not' in result.output and 'registered' in result.output
        assert 'nomatch' in result.output

    def test_excludes_rooms_starting_with_hash(self, runner, monkeypatch):
        monkeypatch.setattr(devices, 'LMNFile', FakeLMNFile)
        monkeypatch.setattr(devices.lr, 'get', lambda url, **kw: list(SAMPLE_LDAP_DEVICES))

        result = runner.invoke(devices.app, [])

        assert 'hiddenhost' not in result.output
        assert 'excluded' not in result.output

    def test_filter_str_matches_hostname(self, runner, monkeypatch):
        monkeypatch.setattr(devices, 'LMNFile', FakeLMNFile)
        monkeypatch.setattr(devices.lr, 'get', lambda url, **kw: list(SAMPLE_LDAP_DEVICES))

        result = runner.invoke(devices.app, ['pc'])

        assert '2 device(s)' in result.output
        assert 'pc1' in result.output
        assert 'pc2' in result.output
        assert 'dc1' not in result.output

    def test_filter_str_matches_room(self, runner, monkeypatch):
        monkeypatch.setattr(devices, 'LMNFile', FakeLMNFile)
        monkeypatch.setattr(devices.lr, 'get', lambda url, **kw: list(SAMPLE_LDAP_DEVICES))

        result = runner.invoke(devices.app, ['r2'])

        assert '2 device(s)' in result.output
        assert 'dc1' in result.output
        assert 'nomatch' in result.output
        assert 'pc1' not in result.output

    def test_filter_str_matches_ip(self, runner, monkeypatch):
        monkeypatch.setattr(devices, 'LMNFile', FakeLMNFile)
        monkeypatch.setattr(devices.lr, 'get', lambda url, **kw: list(SAMPLE_LDAP_DEVICES))

        result = runner.invoke(devices.app, ['10.0.0.3'])

        assert '1 device(s)' in result.output
        assert 'dc1' in result.output

    def test_school_option_changes_csv_prefix(self, runner, monkeypatch):
        seen = {}

        class RecordingFakeLMNFile(FakeLMNFile):
            def __init__(self, path, mode):
                seen['path'] = path
                super().__init__(path, mode)

        monkeypatch.setattr(devices, 'LMNFile', RecordingFakeLMNFile)
        monkeypatch.setattr(devices.lr, 'get', lambda url, **kw: [])

        runner.invoke(devices.app, ['--school', 'other-school'])

        assert seen['path'] == '/etc/linuxmuster/sophomorix/other-school/other-school.devices.csv'

    def test_default_school_has_no_prefix(self, runner, monkeypatch):
        seen = {}

        class RecordingFakeLMNFile(FakeLMNFile):
            def __init__(self, path, mode):
                seen['path'] = path
                super().__init__(path, mode)

        monkeypatch.setattr(devices, 'LMNFile', RecordingFakeLMNFile)
        monkeypatch.setattr(devices.lr, 'get', lambda url, **kw: [])

        runner.invoke(devices.app, [])

        assert seen['path'] == '/etc/linuxmuster/sophomorix/default-school/devices.csv'

    def test_raw_format_output(self, runner, monkeypatch):
        monkeypatch.setattr(devices, 'LMNFile', FakeLMNFile)
        monkeypatch.setattr(devices.lr, 'get', lambda url, **kw: list(SAMPLE_LDAP_DEVICES))
        state.format = True
        state.raw = True

        result = runner.invoke(devices.app, [])

        assert result.exit_code == 0
        assert 'r1\tpc1\tg1\t10.0.0.1\tAA:BB:CC:DD:EE:01\tworkstation\tRegistered' in result.output
        assert 'r2\tnomatch\tg2\t10.0.0.4\tAA:BB:CC:DD:EE:04\tworkstation\tNot registered' in result.output
