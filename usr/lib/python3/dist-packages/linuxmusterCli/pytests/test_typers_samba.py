import datetime
from types import SimpleNamespace

import linuxmusterTools.samba_util as samba_util
from linuxmusterCli.typers import samba
from linuxmusterCli.typers.state import state


class FakeSMBConnections:
    """Stand-in for linuxmusterTools.samba_util.smbstatus.SMBConnections."""

    def __init__(self, school):
        self.school = school
        self.connections = {'johndoe': [
            SimpleNamespace(machine='10.0.0.1', hostname='pc01', auth_time='2026-10-26T19:27:40.168787+01:00'),
            SimpleNamespace(machine='10.0.0.2', hostname='pc02', auth_time='2026-10-26T19:02:43.717022+01:00'),
        ]}
        self.users = {'johndoe': self.connections['johndoe'][0]}
        self.machines = {}

    def get_machines(self):
        self.machines = {'pc01': SimpleNamespace(machine='10.0.0.1', auth_time='2026-10-26T11:32:17.720598+01:00')}


class FakeSmbstatusModule:
    SMBConnections = FakeSMBConnections


class FakeSambaToolDNS:
    """Stand-in for linuxmusterTools.samba_util.SambaToolDNS."""

    def list(self):
        return {
            'root': [{'type': 'A', 'ttl': '3600', 'value': '10.0.0.1'}],
            'sub': [{'host': 'pc01', 'type': 'A', 'ttl': '3600', 'value': '10.0.0.2'}],
        }


class TestGpos:

    def test_lists_gpo_details(self, runner, monkeypatch):
        # gpos()/drives() import and instantiate GPOManager locally (lazily)
        # now, instead of reading a module-level samba.GPOS built at import
        # time -- patch the class at its source instead.
        monkeypatch.setattr(samba_util, 'GPOManager', lambda: SimpleNamespace(gpos={
            'somename': SimpleNamespace(gpo='{GUID}', path='\\\\host\\sysvol\\path'),
        }))

        result = runner.invoke(samba.app, ['gpos'])

        assert result.exit_code == 0
        assert 'somename' in result.output
        assert '{GUID}' in result.output

    def test_empty_gpos_shows_empty_table(self, runner, monkeypatch):
        monkeypatch.setattr(samba_util, 'GPOManager', lambda: SimpleNamespace(gpos={}))

        result = runner.invoke(samba.app, ['gpos'])

        assert result.exit_code == 0
        assert 'Name' in result.output

    def test_raw_format_output(self, runner, monkeypatch):
        monkeypatch.setattr(samba_util, 'GPOManager', lambda: SimpleNamespace(gpos={
            'somename': SimpleNamespace(gpo='{GUID}', path='\\\\host\\sysvol'),
        }))
        state.format = True
        state.raw = True

        result = runner.invoke(samba.app, ['gpos'])

        assert result.exit_code == 0
        assert 'somename\t{GUID}\t\\\\host\\sysvol' in result.output


class TestDrives:

    def _fake_gpos(self, school='default-school'):
        return {
            f"sophomorix:school:{school}": SimpleNamespace(
                drivemgr=SimpleNamespace(drives=[
                    SimpleNamespace(id='H', letter='H:', userLetter=True, label='Home', disabled=False),
                ])
            )
        }

    def test_lists_drives_for_default_school(self, runner, monkeypatch):
        monkeypatch.setattr(samba_util, 'GPOManager', lambda: SimpleNamespace(gpos=self._fake_gpos()))

        result = runner.invoke(samba.app, ['drives'])

        assert result.exit_code == 0
        assert 'H:' in result.output
        assert 'Home' in result.output

    def test_school_option_is_used_as_gpos_key(self, runner, monkeypatch):
        monkeypatch.setattr(samba_util, 'GPOManager', lambda: SimpleNamespace(gpos=self._fake_gpos('other-school')))

        result = runner.invoke(samba.app, ['drives', '--school', 'other-school'])

        assert result.exit_code == 0
        assert 'H:' in result.output

    def test_unknown_school_shows_clear_error(self, runner, monkeypatch):
        monkeypatch.setattr(samba_util, 'GPOManager', lambda: SimpleNamespace(gpos=self._fake_gpos('default-school')))

        result = runner.invoke(samba.app, ['drives', '--school', 'unknown-school'])

        assert result.exit_code == 0
        assert result.exception is None
        assert "No GPO found for school 'unknown-school'" in result.output


class TestStatus:

    def test_default_shows_both_users_and_machines(self, runner, monkeypatch):
        monkeypatch.setattr(samba, 'smbstatus', FakeSmbstatusModule())

        result = runner.invoke(samba.app, ['status'])

        assert result.exit_code == 0
        assert 'johndoe' in result.output
        assert 'Machine' in result.output

    def test_users_only_hides_machines_table(self, runner, monkeypatch):
        monkeypatch.setattr(samba, 'smbstatus', FakeSmbstatusModule())

        result = runner.invoke(samba.app, ['status', '--users'])

        assert result.exit_code == 0
        assert 'johndoe' in result.output
        # All connections of a user, not only the most recent one
        assert 'pc01' in result.output
        assert 'pc02' in result.output
        assert '2026-10-26 19:27:40' in result.output
        assert 'Machine' not in result.output

    def test_machines_only_hides_users_table(self, runner, monkeypatch):
        monkeypatch.setattr(samba, 'smbstatus', FakeSmbstatusModule())

        result = runner.invoke(samba.app, ['status', '--machines'])

        assert result.exit_code == 0
        assert 'Machine' in result.output
        assert '2026-10-26 11:32:17' in result.output
        assert 'johndoe' not in result.output

    def test_both_flags_together_shows_all_again(self, runner, monkeypatch):
        # users ^ machines is False when both are True, so show_all becomes
        # True too: passing both flags behaves like passing neither.
        monkeypatch.setattr(samba, 'smbstatus', FakeSmbstatusModule())

        result = runner.invoke(samba.app, ['status', '--users', '--machines'])

        assert result.exit_code == 0
        assert 'johndoe' in result.output
        assert 'Machine' in result.output


class TestDns:

    def test_default_shows_root_and_sub_tables(self, runner, monkeypatch):
        monkeypatch.setattr(samba, 'SambaToolDNS', FakeSambaToolDNS)

        result = runner.invoke(samba.app, ['dns'])

        assert result.exit_code == 0
        assert '10.0.0.1' in result.output
        assert 'pc01' in result.output
        assert '10.0.0.2' in result.output

    def test_root_only_hides_sub_table(self, runner, monkeypatch):
        monkeypatch.setattr(samba, 'SambaToolDNS', FakeSambaToolDNS)

        result = runner.invoke(samba.app, ['dns', '--root'])

        assert result.exit_code == 0
        assert '10.0.0.1' in result.output
        assert 'pc01' not in result.output

    def test_sub_only_hides_root_table(self, runner, monkeypatch):
        monkeypatch.setattr(samba, 'SambaToolDNS', FakeSambaToolDNS)

        result = runner.invoke(samba.app, ['dns', '--sub'])

        assert result.exit_code == 0
        assert 'pc01' in result.output
        assert '10.0.0.1' not in result.output

    def test_both_flags_together_shows_both_tables(self, runner, monkeypatch):
        monkeypatch.setattr(samba, 'SambaToolDNS', FakeSambaToolDNS)

        result = runner.invoke(samba.app, ['dns', '--root', '--sub'])

        assert result.exit_code == 0
        assert '10.0.0.1' in result.output
        assert 'pc01' in result.output


class TestLastlogin:

    def test_golden_path(self, runner, monkeypatch):
        def fake_last_login(pattern, include_gz=False):
            return [{
                'user': 'johndoe', 'ip': '10.0.0.1', 'hostname': 'pc01',
                'datetime': datetime.datetime(2026, 1, 1, 12, 0, 0),
            }]

        monkeypatch.setattr(samba, 'last_login', fake_last_login)

        result = runner.invoke(samba.app, ['lastlogin'])

        assert result.exit_code == 0
        assert 'johndoe' in result.output
        assert 'pc01' in result.output
        assert '2026-01-01 12:00:00' in result.output

    def test_unknown_hostname_shows_empty_cell(self, runner, monkeypatch):
        def fake_last_login(pattern, include_gz=False):
            return [{
                'user': 'johndoe', 'ip': '10.0.0.99', 'hostname': None,
                'datetime': datetime.datetime(2026, 1, 1, 12, 0, 0),
            }]

        monkeypatch.setattr(samba, 'last_login', fake_last_login)

        result = runner.invoke(samba.app, ['lastlogin'])

        assert result.exit_code == 0
        assert 'None' not in result.output

    def test_empty_list_shows_empty_table(self, runner, monkeypatch):
        monkeypatch.setattr(samba, 'last_login', lambda pattern, include_gz=False: [])

        result = runner.invoke(samba.app, ['lastlogin'])

        assert result.exit_code == 0
        assert 'User' in result.output

    def test_pattern_and_all_flag_are_forwarded(self, runner, monkeypatch):
        seen = {}

        def fake_last_login(pattern, include_gz=False):
            seen['pattern'] = pattern
            seen['include_gz'] = include_gz
            return []

        monkeypatch.setattr(samba, 'last_login', fake_last_login)

        runner.invoke(samba.app, ['lastlogin', 'johndoe', '--all'])

        assert seen['pattern'] == 'johndoe'
        assert seen['include_gz'] is True
