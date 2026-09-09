import pytest

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


SCHOOLS = ['default-school', 'other-school']


class TestSync:

    def setup_method(self):
        FakeLMNSchoolclass.instances = []
        FakeLMNSchoolclass.raise_map = {}

    @pytest.fixture(autouse=True)
    def _schools(self, monkeypatch):
        # sync() validates its --school against ldap before doing anything
        monkeypatch.setattr(schoolclass, 'valid_schools', lambda: list(SCHOOLS))
        monkeypatch.setattr(schoolclass, 'is_valid_school', lambda school: school in SCHOOLS)

    def test_no_schoolclass_and_no_sync_all_prints_error_and_exits_zero(self, runner, monkeypatch):
        # NOTE: this branch is a plain `return`, not typer.Exit() -> exit_code stays 0
        # (verified empirically), even though it is an error path.
        monkeypatch.setattr(schoolclass, 'LMNSchoolclass', FakeLMNSchoolclass)

        result = runner.invoke(schoolclass.app, ['sync'])

        assert result.exit_code == 0
        assert 'Please select at least a schoolclass or the option --all' in result.output
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

    def test_school_option_is_forwarded_to_lmnschoolclass(self, runner, monkeypatch):
        monkeypatch.setattr(schoolclass, 'LMNSchoolclass', FakeLMNSchoolclass)

        result = runner.invoke(schoolclass.app, ['sync', '--schoolclass', 'a', '--students', '--school', 'other-school'])

        assert result.exit_code == 0
        assert FakeLMNSchoolclass.instances[0].school == 'other-school'

    def test_sync_all_forces_all_flags_and_excludes_attic(self, runner, monkeypatch):
        monkeypatch.setattr(schoolclass, 'LMNSchoolclass', FakeLMNSchoolclass)
        monkeypatch.setattr(schoolclass.lr, 'getval', lambda url, attr, **kw: ['7a', '8b', 'attic'])

        result = runner.invoke(schoolclass.app, ['sync', '--all'])

        assert result.exit_code == 0
        assert [i.cn for i in FakeLMNSchoolclass.instances] == ['7a', '8b']
        for inst in FakeLMNSchoolclass.instances:
            assert inst.teachers_group.filled
            assert inst.parents_group.filled
            assert inst.students_group.filled

    def test_sync_all_without_attic_in_list_syncs_everything(self, runner, monkeypatch):
        # 'attic' is not a real schoolclass and may be missing from the LDAP result:
        # its removal must stay optional instead of raising ValueError.
        monkeypatch.setattr(schoolclass, 'LMNSchoolclass', FakeLMNSchoolclass)
        monkeypatch.setattr(schoolclass.lr, 'getval', lambda url, attr, **kw: ['7a', '8b'])

        result = runner.invoke(schoolclass.app, ['sync', '--all'])

        assert result.exit_code == 0
        assert [i.cn for i in FakeLMNSchoolclass.instances] == ['7a', '8b']

    def test_sync_all_lists_only_the_selected_school(self, runner, monkeypatch):
        # /schoolclasses has no school-scoped subdn: without an explicit school
        # the reader returns the schoolclasses of every school, which then blow
        # up one by one in LMNSchoolclass(school=...).
        calls = []
        def mock_getval(url, attr, **kw):
            calls.append((url, attr, kw.get('school')))
            return ['7a']

        monkeypatch.setattr(schoolclass, 'LMNSchoolclass', FakeLMNSchoolclass)
        monkeypatch.setattr(schoolclass.lr, 'getval', mock_getval)

        result = runner.invoke(schoolclass.app, ['sync', '--all', '--school', 'other-school'])

        assert result.exit_code == 0
        assert calls == [('/schoolclasses', 'cn', 'other-school')]
        assert FakeLMNSchoolclass.instances[0].school == 'other-school'

    def test_unknown_school_exits_with_error(self, runner, monkeypatch):
        monkeypatch.setattr(schoolclass, 'LMNSchoolclass', FakeLMNSchoolclass)

        result = runner.invoke(schoolclass.app, ['sync', '--all', '--school', 'nonexistent'])

        assert result.exit_code == 1
        assert 'Unknown school nonexistent' in result.output
        assert 'default-school' in result.output
        assert FakeLMNSchoolclass.instances == []

    def test_global_is_rejected_as_a_school(self, runner, monkeypatch):
        # 'global' is a routing marker for global-administrators, not a school
        monkeypatch.setattr(schoolclass, 'LMNSchoolclass', FakeLMNSchoolclass)

        result = runner.invoke(schoolclass.app, ['sync', '--all', '--school', 'global'])

        assert result.exit_code == 1
        assert 'Unknown school global' in result.output
        assert FakeLMNSchoolclass.instances == []

    def test_fill_members_exception_does_not_abort_the_run(self, runner, monkeypatch):
        # A failing subgroup must not stop the command: the remaining subgroups
        # of that schoolclass and every following schoolclass are still synced,
        # and the failures are reported at the end with a non-zero exit code.
        monkeypatch.setattr(schoolclass, 'LMNSchoolclass', FakeLMNSchoolclass)
        FakeLMNSchoolclass.raise_map = {'a': {'teachers': 'boom'}}

        result = runner.invoke(schoolclass.app, ['sync', '--schoolclass', 'a,b', '--groups'])

        assert result.exit_code == 1
        assert [i.cn for i in FakeLMNSchoolclass.instances] == ['a', 'b']

        first, second = FakeLMNSchoolclass.instances
        assert not first.teachers_group.filled
        assert first.parents_group.filled
        assert first.students_group.filled
        assert second.teachers_group.filled
        assert second.parents_group.filled
        assert second.students_group.filled

        assert 'boom' in result.output
        assert 'Could not sync: a-teachers' in result.output

    def test_unknown_schoolclass_is_reported_and_skipped(self, runner, monkeypatch):
        class FakeMissingSchoolclass(FakeLMNSchoolclass):
            def __init__(self, cn, school='default-school'):
                if cn == 'nope':
                    raise Exception(f"The schoolclass {cn} was not found in ldap.")
                super().__init__(cn, school=school)

        monkeypatch.setattr(schoolclass, 'LMNSchoolclass', FakeMissingSchoolclass)

        result = runner.invoke(schoolclass.app, ['sync', '--schoolclass', 'nope,b', '--groups'])

        assert result.exit_code == 1
        assert [i.cn for i in FakeLMNSchoolclass.instances] == ['b']
        assert 'was not found in ldap' in result.output
        assert 'Could not sync: nope' in result.output

    def test_all_groups_synced_exits_zero(self, runner, monkeypatch):
        monkeypatch.setattr(schoolclass, 'LMNSchoolclass', FakeLMNSchoolclass)

        result = runner.invoke(schoolclass.app, ['sync', '--schoolclass', 'a,b', '--groups'])

        assert result.exit_code == 0
        assert 'Could not sync' not in result.output
        for inst in FakeLMNSchoolclass.instances:
            assert inst.teachers_group.filled
            assert inst.parents_group.filled
            assert inst.students_group.filled


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
