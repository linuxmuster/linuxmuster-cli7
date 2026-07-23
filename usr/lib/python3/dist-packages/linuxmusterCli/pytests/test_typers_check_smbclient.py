from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from linuxmusterCli.typers import check_smbclient


class FakeDirEntry:
    def __init__(self, name, is_dir):
        self._name = name
        self._is_dir = is_dir

    def is_dir(self):
        return self._is_dir

    @property
    def name(self):
        return self._name


@pytest.fixture(autouse=True)
def _never_touch_real_privileges(monkeypatch):
    """
    check() legitimately calls os.setuid/os.setgid/os.chown/pexpect/pwd/pwinput
    to drop privileges to a real teacher account and authenticate via Kerberos.
    None of that may ever run for real in a test process: os.setuid is
    irreversible within this interpreter and would corrupt every later test
    (and this sandbox is attached to a live domain). Patch all of it
    unconditionally for every test in this file, regardless of which branch
    the individual test means to exercise.
    """

    monkeypatch.setattr(check_smbclient.os, 'setuid', MagicMock())
    monkeypatch.setattr(check_smbclient.os, 'setgid', MagicMock())
    monkeypatch.setattr(check_smbclient.os, 'chown', MagicMock())
    monkeypatch.setattr(check_smbclient.time, 'sleep', MagicMock())
    monkeypatch.setattr(check_smbclient.pwd, 'getpwnam', lambda name: SimpleNamespace(pw_uid=1000))
    monkeypatch.setattr(check_smbclient.pexpect, 'spawn', lambda *a, **kw: MagicMock())
    monkeypatch.setattr(check_smbclient, 'pwinput', lambda prompt='': 'secret')
    monkeypatch.setattr(check_smbclient.os.path, 'isfile', lambda path: True)
    monkeypatch.setattr(check_smbclient.smbclient, 'scandir', lambda path: iter([]))


class TestCheck:

    def test_empty_teacher_login_exits_without_touching_privileges(self, runner, monkeypatch):
        setuid = MagicMock()
        monkeypatch.setattr(check_smbclient.os, 'setuid', setuid)

        result = runner.invoke(check_smbclient.app, [], input='\n\n')

        assert result.exit_code == 0
        assert 'Please enter a valid user login' in result.output
        assert not setuid.called

    def test_golden_path_drops_privileges_and_reports_success_per_host(self, runner, monkeypatch):
        setuid = MagicMock()
        setgid = MagicMock()
        chown = MagicMock()
        spawn = MagicMock()
        monkeypatch.setattr(check_smbclient.os, 'setuid', setuid)
        monkeypatch.setattr(check_smbclient.os, 'setgid', setgid)
        monkeypatch.setattr(check_smbclient.os, 'chown', chown)
        monkeypatch.setattr(check_smbclient.pexpect, 'spawn', lambda *a, **kw: spawn)
        monkeypatch.setattr(
            check_smbclient.smbclient, 'scandir',
            lambda path: iter([FakeDirEntry('file1.txt', False), FakeDirEntry('subdir', True)]),
        )

        result = runner.invoke(check_smbclient.app, [], input='\ntdoe\n')

        assert result.exit_code == 0
        assert setuid.call_args[0] == (1000,)
        assert setgid.call_args[0] == (100,)
        assert chown.called
        # A password was supplied, so the kerberos child is fed it.
        assert spawn.expect.called
        assert spawn.sendline.called
        # One SUCCESS per tried host (netbios, realm, domain), printed twice
        # (once inline, once again in the final accumulated report).
        assert result.output.count('SUCCESS') == 6
        assert 'FAILED' not in result.output

    def test_no_password_falls_back_to_existing_kerberos_ticket(self, runner, monkeypatch):
        spawn = MagicMock()
        monkeypatch.setattr(check_smbclient.pexpect, 'spawn', lambda *a, **kw: spawn)
        monkeypatch.setattr(check_smbclient, 'pwinput', lambda prompt='': '')

        result = runner.invoke(check_smbclient.app, [], input='\ntdoe\n')

        assert result.exit_code == 0
        assert 'No password given' in result.output
        # `if pw:` guards the kinit interaction, so an empty password must
        # never feed anything to the pexpect child.
        assert not spawn.expect.called
        assert not spawn.sendline.called

    def test_missing_kerberos_ticket_exits_before_dropping_privileges(self, runner, monkeypatch):
        setuid = MagicMock()
        monkeypatch.setattr(check_smbclient.os, 'setuid', setuid)
        monkeypatch.setattr(check_smbclient.os.path, 'isfile', lambda path: False)

        result = runner.invoke(check_smbclient.app, [], input='\ntdoe\n')

        assert result.exit_code == 0
        assert 'No valid Kerberos ticket found' in result.output
        assert not setuid.called

    def test_scandir_failure_is_reported_as_failed_for_that_host_only(self, runner, monkeypatch):
        calls = []

        def fake_scandir(path):
            calls.append(path)
            if len(calls) == 1:
                raise Exception('boom')
            return iter([])

        monkeypatch.setattr(check_smbclient.smbclient, 'scandir', fake_scandir)

        result = runner.invoke(check_smbclient.app, [], input='\ntdoe\n')

        assert result.exit_code == 0
        assert 'FAILED' in result.output
        assert 'SUCCESS' in result.output

    def test_extra_domain_is_tried_as_a_fourth_host(self, runner, monkeypatch):
        seen_paths = []

        def fake_scandir(path):
            seen_paths.append(path)
            return iter([])

        monkeypatch.setattr(check_smbclient.smbclient, 'scandir', fake_scandir)

        result = runner.invoke(check_smbclient.app, [], input='server.linuxmuster.lan\ntdoe\n')

        assert result.exit_code == 0
        assert len(seen_paths) == 4
        assert any('server.linuxmuster.lan' in p for p in seen_paths)
