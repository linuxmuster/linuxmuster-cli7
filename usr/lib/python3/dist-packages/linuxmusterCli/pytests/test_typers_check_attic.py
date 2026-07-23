from linuxmusterCli.typers import check_attic
from linuxmusterCli.typers.state import state


KILLED_USER = {
    'killed_user': {
        'start': '2026-01-01', 'status': 'killed', 'end': '2026-06-01', 'school': 'default-school',
    },
}

KILLABLE_USER = {
    'killable_user': {
        'start': '2026-01-01', 'status': 'killable', 'end': '', 'school': 'default-school',
    },
}

NO_INFO_USER = {
    'unknown_user': {
        'start': '', 'status': '', 'end': '', 'school': 'default-school',
    },
}

OTHER_STATUS_USER = {
    'archived_user': {
        'start': '2026-01-01', 'status': 'archived', 'end': '2026-06-01', 'school': 'default-school',
    },
}


class FakeLMNSMBClient:
    """Stand-in for linuxmusterTools.smbclient.LMNSMBClient, tracked per instance."""

    instances = []

    def __init__(self):
        self.switched = []
        self.deltreed = []
        FakeLMNSMBClient.instances.append(self)

    def switch(self, school):
        self.switched.append(school)

    def deltree(self, path):
        self.deltreed.append(path)


class TestCheck:

    def setup_method(self):
        FakeLMNSMBClient.instances = []

    def test_no_information_found_for_falsy_start(self, runner, monkeypatch):
        monkeypatch.setattr(check_attic, 'check_attic_dir', lambda school=None: dict(NO_INFO_USER))

        result = runner.invoke(check_attic.app, [])

        assert result.exit_code == 0
        assert 'unknown_user' in result.output
        assert 'No information found' in result.output

    def test_other_status_message(self, runner, monkeypatch):
        monkeypatch.setattr(check_attic, 'check_attic_dir', lambda school=None: dict(OTHER_STATUS_USER))

        result = runner.invoke(check_attic.app, [])

        assert result.exit_code == 0
        assert 'archived_user' in result.output
        assert 'Account archived' in result.output
        assert '2026-01-01 to' in result.output
        assert '2026-06-01' in result.output

    def test_killable_status_produces_no_prompt(self, runner, monkeypatch):
        monkeypatch.setattr(check_attic, 'check_attic_dir', lambda school=None: dict(KILLABLE_USER))

        # No input= given: if a confirm() were triggered this would raise/hang.
        result = runner.invoke(check_attic.app, [])

        assert result.exit_code == 0
        assert 'killable_user' in result.output
        assert 'Account killable' in result.output
        assert 'since 2026-01-01' in result.output
        assert FakeLMNSMBClient.instances == []

    def test_killed_user_confirmed_deletes_attic_dir(self, runner, monkeypatch):
        monkeypatch.setattr(check_attic, 'check_attic_dir', lambda school=None: dict(KILLED_USER))
        monkeypatch.setattr(check_attic, 'LMNSMBClient', FakeLMNSMBClient)

        result = runner.invoke(check_attic.app, [], input='y\n')

        assert result.exit_code == 0
        assert 'killed_user' in result.output
        client = FakeLMNSMBClient.instances[0]
        assert client.switched == ['default-school']
        assert client.deltreed == ['students/attic/killed_user']

    def test_killed_user_aborted_does_not_delete(self, runner, monkeypatch):
        monkeypatch.setattr(check_attic, 'check_attic_dir', lambda school=None: dict(KILLED_USER))
        monkeypatch.setattr(check_attic, 'LMNSMBClient', FakeLMNSMBClient)

        result = runner.invoke(check_attic.app, [], input='n\n')

        assert result.exit_code != 0
        assert FakeLMNSMBClient.instances == []

    def test_exception_from_check_attic_dir_is_handled_gracefully(self, runner, monkeypatch):
        def raiser(school=None):
            raise Exception("School not found in ldap.")

        monkeypatch.setattr(check_attic, 'check_attic_dir', raiser)

        result = runner.invoke(check_attic.app, [])

        assert result.exit_code == 0
        assert 'School not found in ldap.' in result.output

    def test_raw_format_output(self, runner, monkeypatch):
        monkeypatch.setattr(check_attic, 'check_attic_dir', lambda school=None: dict(OTHER_STATUS_USER))
        state.format = True
        state.raw = True

        result = runner.invoke(check_attic.app, [])

        assert result.exit_code == 0
        assert 'archived_user\tAccount archived from 2026-01-01 to 2026-06-01\tdefault-school' in result.output
