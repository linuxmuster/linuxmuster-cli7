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


class FakeGroupManager:
    """Stand-in for linuxmusterTools.samba_util.GroupManager, tracked per instance."""

    instances = []
    raise_on_add = None
    fail_for = frozenset()

    def __init__(self, school='default-school'):
        self.school = school
        self.added = []
        FakeGroupManager.instances.append(self)

    def add_members(self, group, members):
        if FakeGroupManager.raise_on_add:
            raise FakeGroupManager.raise_on_add
        if any(m in FakeGroupManager.fail_for for m in members):
            raise Exception(f"unknown user in {members}")
        self.group = group
        self.added.extend(members)


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
        FakeGroupManager.instances = []
        FakeGroupManager.raise_on_add = None
        FakeGroupManager.fail_for = frozenset()

    def test_only_students_without_internet_are_added(self, runner, monkeypatch):
        monkeypatch.setattr(students, 'Spinner', FakeSpinner)
        monkeypatch.setattr(students, 'GroupManager', FakeGroupManager)
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
        assert FakeGroupManager.instances[0].added == ['nointernet1', 'nointernet2']

    def test_student_with_internet_is_never_added(self, runner, monkeypatch):
        monkeypatch.setattr(students, 'Spinner', FakeSpinner)
        monkeypatch.setattr(students, 'GroupManager', FakeGroupManager)
        monkeypatch.setattr(
            students.lr, 'get',
            lambda url, **kw: [FakeStudentEntry('hasinternet', True)],
        )

        result = runner.invoke(students.app, [])

        assert result.exit_code == 0
        # Nobody needs adding: GroupManager isn't even instantiated.
        assert FakeGroupManager.instances == []
        assert 'No student needs their internet access reset' in result.output

    def test_schoolclass_option_filters_students(self, runner, monkeypatch):
        monkeypatch.setattr(students, 'Spinner', FakeSpinner)
        monkeypatch.setattr(students, 'GroupManager', FakeGroupManager)
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
        assert FakeGroupManager.instances[0].added == ['a', 'c']

    def test_schoolclass_option_accepts_comma_separated_list(self, runner, monkeypatch):
        monkeypatch.setattr(students, 'Spinner', FakeSpinner)
        monkeypatch.setattr(students, 'GroupManager', FakeGroupManager)
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
        assert FakeGroupManager.instances[0].added == ['a', 'b']

    def test_school_option_is_forwarded(self, runner, monkeypatch):
        monkeypatch.setattr(students, 'Spinner', FakeSpinner)
        monkeypatch.setattr(students, 'GroupManager', FakeGroupManager)
        seen = {}

        def fake_get(url, school='default-school', **kw):
            seen['school'] = school
            return []

        monkeypatch.setattr(students.lr, 'get', fake_get)

        runner.invoke(students.app, ['--school', 'other-school'])

        assert seen['school'] == 'other-school'

    def test_group_manager_error_aborts_with_nonzero_exit(self, runner, monkeypatch):
        monkeypatch.setattr(students, 'Spinner', FakeSpinner)
        monkeypatch.setattr(students, 'GroupManager', FakeGroupManager)
        FakeGroupManager.raise_on_add = Exception("group internet not found")
        monkeypatch.setattr(
            students.lr, 'get',
            lambda url, **kw: [FakeStudentEntry('nointernet1', False)],
        )

        result = runner.invoke(students.app, [])

        assert result.exit_code != 0

    def test_one_failing_student_does_not_stop_the_others(self, runner, monkeypatch):
        monkeypatch.setattr(students, 'Spinner', FakeSpinner)
        monkeypatch.setattr(students, 'GroupManager', FakeGroupManager)
        FakeGroupManager.fail_for = frozenset({'broken'})
        monkeypatch.setattr(
            students.lr, 'get',
            lambda url, **kw: [
                FakeStudentEntry('nointernet1', False),
                FakeStudentEntry('broken', False),
                FakeStudentEntry('nointernet2', False),
            ],
        )

        result = runner.invoke(students.app, [])

        assert result.exit_code != 0
        assert FakeGroupManager.instances[0].added == ['nointernet1', 'nointernet2']
