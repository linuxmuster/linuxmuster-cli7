from linuxmusterCli.typers import students


class FakeSpinner:
    """No-op stand-in for linuxmusterTools.common.Spinner (avoids cursor-control noise)."""

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def print(self, *a, **kw):
        pass


class FakeStudentEntry:
    """Stand-in for the LDAP objects returned by lr.get(..., as_dict=False)."""

    def __init__(self, cn, internet, sophomorixAdminClass='7a'):
        self.cn = cn
        self.internet = internet
        self.sophomorixAdminClass = sophomorixAdminClass


class FakeMgmtGroup:
    """Stand-in for linuxmusterTools.ldapconnector.LMNMgmtGroup, tracked per instance."""

    instances = []

    def __init__(self, name):
        self.name = name
        self.added = []
        FakeMgmtGroup.instances.append(self)

    def add_member(self, cn):
        self.added.append(cn)


class TestResetInternet:
    """
    Note: the command function is named reset_internet and Typer converts it to
    the "reset-internet" command name, but this app only ever registers this one
    @app.command() and no group callback. Empirically, a single-command Typer app
    with no other commands is invoked WITHOUT the command name itself (passing
    'reset-internet' as an explicit arg makes click treat it as an unexpected
    extra positional argument). So tests below invoke students.app with [] or
    just the options, never with a leading 'reset-internet' token.
    """

    def setup_method(self):
        FakeMgmtGroup.instances = []

    def test_only_students_without_internet_are_added(self, runner, monkeypatch):
        monkeypatch.setattr(students, 'Spinner', FakeSpinner)
        monkeypatch.setattr(students, 'LMNMgmtGroup', FakeMgmtGroup)
        monkeypatch.setattr(
            students.lr, 'get',
            lambda url, **kw: [
                FakeStudentEntry('nointernet1', False),
                FakeStudentEntry('hasinternet', True),
                FakeStudentEntry('nointernet2', False),
            ],
        )

        result = runner.invoke(students.app, [])

        assert result.exit_code == 0
        assert FakeMgmtGroup.instances[0].added == ['nointernet1', 'nointernet2']

    def test_student_with_internet_is_never_added(self, runner, monkeypatch):
        monkeypatch.setattr(students, 'Spinner', FakeSpinner)
        monkeypatch.setattr(students, 'LMNMgmtGroup', FakeMgmtGroup)
        monkeypatch.setattr(
            students.lr, 'get',
            lambda url, **kw: [FakeStudentEntry('hasinternet', True)],
        )

        result = runner.invoke(students.app, [])

        assert result.exit_code == 0
        assert FakeMgmtGroup.instances[0].added == []

    def test_schoolclass_option_filters_students(self, runner, monkeypatch):
        monkeypatch.setattr(students, 'Spinner', FakeSpinner)
        monkeypatch.setattr(students, 'LMNMgmtGroup', FakeMgmtGroup)
        monkeypatch.setattr(
            students.lr, 'get',
            lambda url, **kw: [
                FakeStudentEntry('a', False, sophomorixAdminClass='7a'),
                FakeStudentEntry('b', False, sophomorixAdminClass='8b'),
                FakeStudentEntry('c', False, sophomorixAdminClass='7a'),
            ],
        )

        result = runner.invoke(students.app, ['--schoolclass', '7a'])

        assert result.exit_code == 0
        assert FakeMgmtGroup.instances[0].added == ['a', 'c']

    def test_schoolclass_option_accepts_comma_separated_list(self, runner, monkeypatch):
        monkeypatch.setattr(students, 'Spinner', FakeSpinner)
        monkeypatch.setattr(students, 'LMNMgmtGroup', FakeMgmtGroup)
        monkeypatch.setattr(
            students.lr, 'get',
            lambda url, **kw: [
                FakeStudentEntry('a', False, sophomorixAdminClass='7a'),
                FakeStudentEntry('b', False, sophomorixAdminClass='8b'),
                FakeStudentEntry('c', False, sophomorixAdminClass='9c'),
            ],
        )

        result = runner.invoke(students.app, ['--schoolclass', '7a,8b'])

        assert result.exit_code == 0
        assert FakeMgmtGroup.instances[0].added == ['a', 'b']

    def test_school_option_is_forwarded(self, runner, monkeypatch):
        monkeypatch.setattr(students, 'Spinner', FakeSpinner)
        monkeypatch.setattr(students, 'LMNMgmtGroup', FakeMgmtGroup)
        seen = {}

        def fake_get(url, school='default-school', **kw):
            seen['school'] = school
            return []

        monkeypatch.setattr(students.lr, 'get', fake_get)

        runner.invoke(students.app, ['--school', 'other-school'])

        assert seen['school'] == 'other-school'
