from linuxmusterCli.typers import userlog
from linuxmusterCli.typers.state import state


ADD_ENTRY = {
    'lastname': 'Doe', 'firstname': 'John', 'user': 'johndoe',
    'school': 'default-school', 'role': 'student', 'adminclass': '7a',
}
KILL_ENTRY = {
    'lastname': 'Roe', 'firstname': 'Jane', 'user': 'janeroe',
    'school': 'default-school', 'role': 'student', 'adminclass': '8b',
}
UPDATED_USER = {
    'sn': 'Ok', 'givenName': 'Alice', 'school': 'default-school',
    'sophomorixRole': 'teacher', 'sophomorixAdminClass': 'staff',
}

TIMESTAMP = 1700000000


def patch_logs(monkeypatch, add=None, kill=None, updated=None):
    monkeypatch.setattr(userlog, 'parse_add_log', lambda **kw: dict(add or {}))
    monkeypatch.setattr(userlog, 'parse_kill_log', lambda **kw: dict(kill or {}))
    monkeypatch.setattr(userlog, 'parse_update_log', lambda **kw: dict(updated or {}))


class TestValidation:

    def test_mutually_exclusive_options_reject_all_and_today(self, runner, monkeypatch):
        patch_logs(monkeypatch)

        result = runner.invoke(userlog.app, ['--all', '--today'])

        assert result.exit_code == 0
        assert 'mutually exclusives' in result.output

    def test_mutually_exclusive_options_reject_last_with_today(self, runner, monkeypatch):
        patch_logs(monkeypatch)

        result = runner.invoke(userlog.app, ['--last', '--today'])

        assert result.exit_code == 0
        assert 'mutually exclusives' in result.output

    def test_last_without_show_flag_is_rejected(self, runner, monkeypatch):
        patch_logs(monkeypatch)

        result = runner.invoke(userlog.app, ['--last'])

        assert result.exit_code == 0
        assert 'Option --last can only be used combined with -a or -k or -u' in result.output

    def test_last_combined_with_show_flag_is_accepted(self, runner, monkeypatch):
        patch_logs(monkeypatch, add={TIMESTAMP: [ADD_ENTRY]})

        result = runner.invoke(userlog.app, ['--added', '--last'])

        assert result.exit_code == 0
        assert 'mutually exclusives' not in result.output
        assert "can only be used combined" not in result.output


class TestLs:

    def test_default_shows_added_killed_and_updated(self, runner, monkeypatch):
        patch_logs(
            monkeypatch,
            add={TIMESTAMP: [ADD_ENTRY]},
            kill={TIMESTAMP: [KILL_ENTRY]},
            updated={TIMESTAMP: [{'user': 'aliceok', 'changes': {'sophomorixRole': 'teacher'}}]},
        )
        monkeypatch.setattr(userlog.lr, 'get', lambda url: dict(UPDATED_USER))
        state.format = True
        state.raw = True

        result = runner.invoke(userlog.app, [])

        assert result.exit_code == 0
        assert 'Added\tDoe\tJohn\tjohndoe' in result.output
        assert 'Killed\tRoe\tJane\tjaneroe' in result.output
        assert 'Updated\tOk\tAlice\taliceok' in result.output
        assert 'sophomorixRole:teacher' in result.output

    def test_only_added_flag_omits_killed_and_updated(self, runner, monkeypatch):
        patch_logs(
            monkeypatch,
            add={TIMESTAMP: [ADD_ENTRY]},
            kill={TIMESTAMP: [KILL_ENTRY]},
            updated={TIMESTAMP: [{'user': 'aliceok', 'changes': {}}]},
        )
        monkeypatch.setattr(userlog.lr, 'get', lambda url: dict(UPDATED_USER))
        state.format = True
        state.raw = True

        result = runner.invoke(userlog.app, ['--added'])

        assert result.exit_code == 0
        assert 'Added\tDoe\tJohn\tjohndoe' in result.output
        assert 'Killed' not in result.output
        assert 'Updated' not in result.output

    def test_last_keeps_only_latest_timestamp_entries(self, runner, monkeypatch):
        add_entry_old = dict(ADD_ENTRY, lastname='Old', firstname='Timer', user='olduser')
        add_entry_new = dict(ADD_ENTRY, lastname='New', firstname='Comer', user='newuser')
        patch_logs(monkeypatch, add={TIMESTAMP: [add_entry_old], TIMESTAMP + 100000000: [add_entry_new]})
        state.format = True
        state.raw = True

        result = runner.invoke(userlog.app, ['--added', '--last'])

        assert result.exit_code == 0
        assert 'newuser' in result.output
        assert 'olduser' not in result.output

    def test_updated_entry_dropped_when_user_lookup_fails(self, runner, monkeypatch):
        ok_entry = {'user': 'aliceok', 'changes': {'sophomorixRole': 'teacher'}}
        dropped_entry = {'user': 'killeduser', 'changes': {'sophomorixRole': 'student'}}
        patch_logs(monkeypatch, updated={TIMESTAMP: [ok_entry, dropped_entry]})

        def fake_lr_get(url):
            if 'killeduser' in url:
                return None
            return dict(UPDATED_USER)

        monkeypatch.setattr(userlog.lr, 'get', fake_lr_get)
        state.format = True
        state.raw = True

        result = runner.invoke(userlog.app, ['--updated'])

        assert result.exit_code == 0
        assert 'aliceok' in result.output
        assert 'killeduser' not in result.output
