import builtins

from linuxmusterCli.typers import user
from linuxmusterCli.typers.state import state


SAMBA = ['sAMAccountType', 'sophomorixAdminFile', 'sophomorixComment', 'sophomorixCreationDate',
         'sophomorixDeactivationDate', 'sophomorixExamMode', 'sophomorixExitAdminClass',
         'sophomorixFirstnameASCII', 'sophomorixFirstnameInitial', 'sophomorixFirstPassword',
         'sophomorixIntrinsic2', 'sophomorixSchoolname', 'sophomorixSchoolPrefix', 'sophomorixStatus',
         'sophomorixSurnameASCII', 'sophomorixSurnameInitial', 'sophomorixTolerationDate',
         'sophomorixUnid', 'sophomorixUserToken', 'sophomorixWebuiDashboard', 'unixHomeDirectory',
         'homeDrive']
CUSTOM = ['proxyAddresses', 'sophomorixCustom1', 'sophomorixCustom2', 'sophomorixCustom3',
          'sophomorixCustom4', 'sophomorixCustom5', 'sophomorixCustomMulti1', 'sophomorixCustomMulti2',
          'sophomorixCustomMulti3', 'sophomorixCustomMulti4', 'sophomorixCustomMulti5']
PERSON = ['sophomorixRole', 'sophomorixBirthdate', 'sn', 'cn', 'displayName', 'givenName', 'mail',
          'name', 'sophomorixAdminClass', 'sAMAccountName']
PATHS = ['dn', 'homeDirectory']
GROUPS = ['printers', 'projects', 'schoolclasses']
QUOTA = ['sophomorixCloudQuotaCalculated', 'sophomorixMailQuotaCalculated', 'sophomorixQuota']
MANAGEMENT = ['internet', 'intranet', 'wifi', 'isAdmin', 'printing', 'webfilter']

ALL_FULL_FIELDS = SAMBA + CUSTOM + PERSON + PATHS + GROUPS + QUOTA + MANAGEMENT


def make_full_user_data(**overrides):
    data = {field: '' for field in ALL_FULL_FIELDS}
    data.update(overrides)
    return data


class FakeUserObj:
    """Stand-in for the dataclass-like object LMNLdapReader.get(as_dict=False) returns."""

    def __init__(self, data, first_password_ok=True):
        self._data = data
        self._first_password_ok = first_password_ok

    def as_dict(self):
        return self._data

    def test_first_password(self):
        return self._first_password_ok


class TestLs:

    def test_default_full_false_renders_full_layout(self, runner, monkeypatch):
        # NOTE: despite the flag being named "--full", the *default* (full=False)
        # is the branch that renders the big multi-table Rich Layout requiring
        # every field below; passing --full actually switches to a plain pprint()
        # (see test_full_flag_uses_plain_pprint). This looks like an inverted /
        # mixed-up naming bug in user.py, not something introduced by this test.
        data = make_full_user_data(sAMAccountName='johndoe')
        monkeypatch.setattr(user.lr, 'get', lambda url, **kw: FakeUserObj(data))

        result = runner.invoke(user.app, ['johndoe'])

        assert result.exit_code == 0
        assert 'johndoe' in result.output
        assert 'sAMAccountName' in result.output

    def test_full_flag_uses_plain_pprint(self, runner, monkeypatch):
        data = {'sAMAccountName': 'johndoe', 'sophomorixFirstPassword': 'secretpw'}
        monkeypatch.setattr(user.lr, 'get', lambda url, **kw: FakeUserObj(data))

        # option must precede the positional USER argument, otherwise typer
        # misparses '--full' as an attempted subcommand name.
        result = runner.invoke(user.app, ['--full', 'johndoe'])

        assert result.exit_code == 0
        assert "'sAMAccountName': 'johndoe'" in result.output
        assert "'sophomorixFirstPassword': 'secretpw'" in result.output

    def test_user_not_found_shows_both_fallback_messages(self, runner, monkeypatch):
        monkeypatch.setattr(user.lr, 'get', lambda url, **kw: FakeUserObj({}))

        def raising_open(*args, **kwargs):
            raise FileNotFoundError(2, 'No such file or directory', args[0] if args else None)

        monkeypatch.setattr(builtins, 'open', raising_open)

        result = runner.invoke(user.app, ['ghostuser'])

        assert result.exit_code == 0
        # Current (slightly odd) behavior: the exception from the missing
        # killlog is printed, and execution still falls through to print the
        # generic "not found" message too (no early return in the except branch).
        assert 'No such file or directory' in result.output
        assert 'User ghostuser not found.' in result.output

    def test_raw_state_pprints_and_returns_early(self, runner, monkeypatch):
        data = {'sAMAccountName': 'johndoe'}
        monkeypatch.setattr(user.lr, 'get', lambda url, **kw: FakeUserObj(data))
        state.format = True
        state.raw = True

        result = runner.invoke(user.app, ['johndoe'])

        assert result.exit_code == 0
        assert "'sAMAccountName': 'johndoe'" in result.output

    def test_check_first_password_still_set_suffix(self, runner, monkeypatch):
        data = {'sAMAccountName': 'johndoe', 'sophomorixFirstPassword': 'secretpw'}
        monkeypatch.setattr(user.lr, 'get', lambda url, **kw: FakeUserObj(data, first_password_ok=True))
        state.raw = True

        result = runner.invoke(user.app, ['--check-first-pw', 'johndoe'])

        assert result.exit_code == 0
        assert 'still set' in result.output

    def test_check_first_password_changed_suffix(self, runner, monkeypatch):
        data = {'sAMAccountName': 'johndoe', 'sophomorixFirstPassword': 'secretpw'}
        monkeypatch.setattr(user.lr, 'get', lambda url, **kw: FakeUserObj(data, first_password_ok=False))
        state.raw = True

        result = runner.invoke(user.app, ['--check-first-pw', 'johndoe'])

        assert result.exit_code == 0
        assert 'changed' in result.output

    def test_exam_suffix_routes_to_exam_url(self, runner, monkeypatch):
        seen = {}

        def fake_get(url, **kw):
            seen['url'] = url
            return FakeUserObj({'sAMAccountName': 'x'})

        monkeypatch.setattr(user.lr, 'get', fake_get)

        runner.invoke(user.app, ['johndoe-exam'])

        assert seen['url'] == '/users/exam/johndoe-exam'

    def test_plain_user_routes_to_users_url(self, runner, monkeypatch):
        seen = {}

        def fake_get(url, **kw):
            seen['url'] = url
            return FakeUserObj({'sAMAccountName': 'x'})

        monkeypatch.setattr(user.lr, 'get', fake_get)

        runner.invoke(user.app, ['johndoe'])

        assert seen['url'] == '/users/johndoe'

    def test_user_argument_is_lowercased(self, runner, monkeypatch):
        seen = {}

        def fake_get(url, **kw):
            seen['url'] = url
            return FakeUserObj({'sAMAccountName': 'x'})

        monkeypatch.setattr(user.lr, 'get', fake_get)

        runner.invoke(user.app, ['JohnDoe'])

        assert seen['url'] == '/users/johndoe'

    def test_school_option_is_forwarded_in_kwargs(self, runner, monkeypatch):
        seen = {}

        def fake_get(url, **kw):
            seen['kwargs'] = kw
            return FakeUserObj({'sAMAccountName': 'x'})

        monkeypatch.setattr(user.lr, 'get', fake_get)

        runner.invoke(user.app, ['--school', 'other-school', 'johndoe'])

        assert seen['kwargs'] == {'school': 'other-school', 'as_dict': False}

    def test_no_school_option_omits_school_kwarg(self, runner, monkeypatch):
        seen = {}

        def fake_get(url, **kw):
            seen['kwargs'] = kw
            return FakeUserObj({'sAMAccountName': 'x'})

        monkeypatch.setattr(user.lr, 'get', fake_get)

        runner.invoke(user.app, ['johndoe'])

        assert seen['kwargs'] == {'as_dict': False}
