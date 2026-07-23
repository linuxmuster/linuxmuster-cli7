import datetime
from types import SimpleNamespace

from linuxmusterCli.typers import samba
from linuxmusterCli.typers.state import state


class FakeSMBConnections:
    """Stand-in for linuxmusterTools.samba_util.smbstatus.SMBConnections."""

    def __init__(self, school):
        self.school = school
        self.users = {'johndoe': SimpleNamespace(machine='10.0.0.1', hostname='pc01')}
        self.machines = {}

    def get_machines(self):
        self.machines = {'pc01': SimpleNamespace(machine='10.0.0.1')}


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
        monkeypatch.setattr(samba, 'GPOS', {
            'somename': SimpleNamespace(gpo='{GUID}', path='\\\\host\\sysvol\\path'),
        })

        result = runner.invoke(samba.app, ['gpos'])

        assert result.exit_code == 0
        assert 'somename' in result.output
        assert '{GUID}' in result.output

    def test_empty_gpos_shows_empty_table(self, runner, monkeypatch):
        monkeypatch.setattr(samba, 'GPOS', {})

        result = runner.invoke(samba.app, ['gpos'])

        assert result.exit_code == 0
        assert 'Name' in result.output

    def test_raw_format_output(self, runner, monkeypatch):
        monkeypatch.setattr(samba, 'GPOS', {
            'somename': SimpleNamespace(gpo='{GUID}', path='\\\\host\\sysvol'),
        })
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
        monkeypatch.setattr(samba, 'GPOS', self._fake_gpos())

        result = runner.invoke(samba.app, ['drives'])

        assert result.exit_code == 0
        assert 'H:' in result.output
        assert 'Home' in result.output

    def test_school_option_is_used_as_gpos_key(self, runner, monkeypatch):
        monkeypatch.setattr(samba, 'GPOS', self._fake_gpos('other-school'))

        result = runner.invoke(samba.app, ['drives', '--school', 'other-school'])

        assert result.exit_code == 0
        assert 'H:' in result.output

    def test_unknown_school_raises_keyerror(self, runner, monkeypatch):
        # Documents current (buggy) behavior: an unknown/mismatched school
        # crashes with an uncaught KeyError instead of a friendly error message.
        monkeypatch.setattr(samba, 'GPOS', self._fake_gpos('default-school'))

        result = runner.invoke(samba.app, ['drives', '--school', 'unknown-school'])

        assert result.exit_code == 1
        assert isinstance(result.exception, KeyError)


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
        assert 'Machine' not in result.output

    def test_machines_only_hides_users_table(self, runner, monkeypatch):
        monkeypatch.setattr(samba, 'smbstatus', FakeSmbstatusModule())

        result = runner.invoke(samba.app, ['status', '--machines'])

        assert result.exit_code == 0
        assert 'Machine' in result.output
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
                'user': 'johndoe', 'ip': '10.0.0.1',
                'datetime': datetime.datetime(2026, 1, 1, 12, 0, 0),
            }]

        monkeypatch.setattr(samba, 'last_login', fake_last_login)

        result = runner.invoke(samba.app, ['lastlogin'])

        assert result.exit_code == 0
        assert 'johndoe' in result.output
        assert '2026-01-01 12:00:00' in result.output

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
