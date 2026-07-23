from linuxmusterCli.typers import schoolclass
from linuxmusterCli.typers.state import state


class FakeGroup:
    """Stand-in for a schoolclass's teachers_group/parents_group/students_group."""

    def __init__(self, raise_message=None):
        self.raise_message = raise_message
        self.filled = False

    def fill_members(self):
        if self.raise_message:
            raise Exception(self.raise_message)
        self.filled = True


class FakeLMNSchoolclass:
    """Stand-in for linuxmusterTools.ldapconnector.LMNSchoolclass, tracked per instance."""

    instances = []
    # per-cn dict of {'teachers': msg_or_None, 'parents': ..., 'students': ...}
    raise_map = {}

    def __init__(self, cn, school='default-school'):
        self.cn = cn
        self.school = school
        raises = FakeLMNSchoolclass.raise_map.get(cn, {})
        self.teachers_group = FakeGroup(raises.get('teachers'))
        self.parents_group = FakeGroup(raises.get('parents'))
        self.students_group = FakeGroup(raises.get('students'))
        FakeLMNSchoolclass.instances.append(self)


class TestSync:

    def setup_method(self):
        FakeLMNSchoolclass.instances = []
        FakeLMNSchoolclass.raise_map = {}

    def test_no_schoolclass_and_no_sync_all_prints_error_and_exits_zero(self, runner, monkeypatch):
        # NOTE: this branch is a plain `return`, not typer.Exit() -> exit_code stays 0
        # (verified empirically), even though it is an error path.
        monkeypatch.setattr(schoolclass, 'LMNSchoolclass', FakeLMNSchoolclass)

        result = runner.invoke(schoolclass.app, ['sync'])

        assert result.exit_code == 0
        assert 'Please select at least a schoolclass or the option --sync-all' in result.output
        assert FakeLMNSchoolclass.instances == []

    def test_explicit_schoolclass_without_any_sync_flag_also_exits_zero(self, runner, monkeypatch):
        # NOTE: this branch calls sys.exit(0) -- also exit_code 0, so (contrary to a naive
        # reading of the source) BOTH "nothing selected" validation branches behave the
        # same way from the CLI's point of view: an error message plus exit_code 0.
        monkeypatch.setattr(schoolclass, 'LMNSchoolclass', FakeLMNSchoolclass)

        result = runner.invoke(schoolclass.app, ['sync', '--schoolclass', 'foo'])

        assert result.exit_code == 0
        assert 'Please choose at least one of the option' in result.output
        assert FakeLMNSchoolclass.instances == []

    def test_explicit_schoolclass_with_groups_flag_syncs_all_three(self, runner, monkeypatch):
        monkeypatch.setattr(schoolclass, 'LMNSchoolclass', FakeLMNSchoolclass)

        result = runner.invoke(schoolclass.app, ['sync', '--schoolclass', 'a,b', '--groups'])

        assert result.exit_code == 0
        assert len(FakeLMNSchoolclass.instances) == 2
        for inst in FakeLMNSchoolclass.instances:
            assert inst.teachers_group.filled
            assert inst.parents_group.filled
            assert inst.students_group.filled
        assert 'a' in result.output
        assert 'teachers group' in result.output

    def test_explicit_schoolclass_single_flag_only_syncs_that_group(self, runner, monkeypatch):
        monkeypatch.setattr(schoolclass, 'LMNSchoolclass', FakeLMNSchoolclass)

        result = runner.invoke(schoolclass.app, ['sync', '--schoolclass', 'a', '--students'])

        assert result.exit_code == 0
        inst = FakeLMNSchoolclass.instances[0]
        assert inst.students_group.filled
        assert not inst.teachers_group.filled
        assert not inst.parents_group.filled

    def test_sync_all_forces_all_flags_and_excludes_attic(self, runner, monkeypatch):
        monkeypatch.setattr(schoolclass, 'LMNSchoolclass', FakeLMNSchoolclass)
        monkeypatch.setattr(schoolclass.lr, 'getval', lambda url, attr: ['7a', '8b', 'attic'])

        result = runner.invoke(schoolclass.app, ['sync', '--all'])

        assert result.exit_code == 0
        assert [i.cn for i in FakeLMNSchoolclass.instances] == ['7a', '8b']
        for inst in FakeLMNSchoolclass.instances:
            assert inst.teachers_group.filled
            assert inst.parents_group.filled
            assert inst.students_group.filled

    def test_sync_all_crashes_uncaught_if_attic_missing_from_list(self, runner, monkeypatch):
        # BUG (documented, not fixed): sync_all does `schoolclasses.remove('attic')`
        # unconditionally. If the LDAP result doesn't contain an 'attic' schoolclass,
        # this raises an uncaught ValueError before any schoolclass is processed.
        monkeypatch.setattr(schoolclass, 'LMNSchoolclass', FakeLMNSchoolclass)
        monkeypatch.setattr(schoolclass.lr, 'getval', lambda url, attr: ['7a', '8b'])

        result = runner.invoke(schoolclass.app, ['sync', '--all'])

        assert result.exit_code == 1
        assert isinstance(result.exception, ValueError)
        assert FakeLMNSchoolclass.instances == []

    def test_fill_members_exception_aborts_immediately(self, runner, monkeypatch):
        # Each fill_members() call is wrapped in its own try/except that does
        # sys.exit(e) on failure. sys.exit raises SystemExit (not Exception), so it
        # is NOT caught by the outer `except Exception` -- it propagates straight out,
        # aborting both the remaining sync steps for the current schoolclass AND any
        # further schoolclasses in the list.
        monkeypatch.setattr(schoolclass, 'LMNSchoolclass', FakeLMNSchoolclass)
        FakeLMNSchoolclass.raise_map = {'a': {'teachers': 'boom'}}

        result = runner.invoke(schoolclass.app, ['sync', '--schoolclass', 'a,b', '--groups'])

        assert result.exit_code == 1
        # only the first schoolclass was even instantiated
        assert len(FakeLMNSchoolclass.instances) == 1
        # and its own remaining steps (parents/students) never ran either
        assert not FakeLMNSchoolclass.instances[0].parents_group.filled
        assert not FakeLMNSchoolclass.instances[0].students_group.filled


SCHOOLCLASS_DATA = {
    '7a': {
        'cn': '7a', 'sophomorixAdmins': ['teacher1'],
        'sophomorixHidden': False, 'sophomorixJoinable': True,
    },
    '8b': {
        'cn': '8b', 'sophomorixAdmins': ['teacher1', 'teacher2'],
        'sophomorixHidden': True, 'sophomorixJoinable': False,
    },
}

USER_DATA = {
    'teacher1': {'sn': 'Doe', 'givenName': 'John'},
    'teacher2': {'sn': 'Smith', 'givenName': 'Anna'},
}


def make_fake_get(calls=None):
    """Dispatching fake for lr.get, handling both schoolclass and user lookups."""

    def fake_get(url, **kw):
        if calls is not None:
            calls.append(url)
        if url == '/schoolclasses':
            return list(SCHOOLCLASS_DATA.values())
        if url.startswith('/schoolclasses/'):
            cn = url.rsplit('/', 1)[-1]
            return SCHOOLCLASS_DATA.get(cn)
        if url.startswith('/users/'):
            cn = url.rsplit('/', 1)[-1]
            return USER_DATA[cn]
        raise AssertionError(f"unexpected url {url}")

    return fake_get


class TestTeachers:

    def test_no_schoolclass_lists_all_with_teacher_names(self, runner, monkeypatch):
        monkeypatch.setattr(schoolclass.lr, 'get', make_fake_get())

        result = runner.invoke(schoolclass.app, ['teachers'])

        assert result.exit_code == 0
        assert '7a' in result.output
        assert '8b' in result.output
        assert 'Doe John' in result.output
        assert 'Smith Anna' in result.output

    def test_teacher_shared_across_schoolclasses_is_looked_up_only_once(self, runner, monkeypatch):
        calls = []
        monkeypatch.setattr(schoolclass.lr, 'get', make_fake_get(calls))

        result = runner.invoke(schoolclass.app, ['teachers'])

        assert result.exit_code == 0
        assert calls.count('/users/teacher1') == 1

    def test_explicit_schoolclass_filters_selection(self, runner, monkeypatch):
        monkeypatch.setattr(schoolclass.lr, 'get', make_fake_get())

        result = runner.invoke(schoolclass.app, ['teachers', '--schoolclass', '7a'])

        assert result.exit_code == 0
        assert '7a' in result.output
        assert '8b' not in result.output

    def test_requested_schoolclass_that_does_not_exist_is_silently_skipped(self, runner, monkeypatch):
        monkeypatch.setattr(schoolclass.lr, 'get', make_fake_get())

        result = runner.invoke(schoolclass.app, ['teachers', '--schoolclass', '7a,ghost'])

        assert result.exit_code == 0
        assert '7a' in result.output
        assert 'ghost' not in result.output

    def test_school_option_is_forwarded(self, runner, monkeypatch):
        seen = {}

        def fake_get(url, school='default-school'):
            seen['school'] = school
            return []

        monkeypatch.setattr(schoolclass.lr, 'get', fake_get)

        runner.invoke(schoolclass.app, ['teachers', '--school', 'other-school'])

        assert seen['school'] == 'other-school'

    def test_raw_format_output(self, runner, monkeypatch):
        monkeypatch.setattr(schoolclass.lr, 'get', make_fake_get())
        state.format = True
        state.raw = True

        result = runner.invoke(schoolclass.app, ['teachers', '--schoolclass', '7a'])

        assert result.exit_code == 0
        assert 'Schoolclass\tTeachers\tHidden\tJoinable' in result.output
        assert '7a\tDoe John\tFalse\tTrue' in result.output
