from linuxmusterCli.typers import student
from linuxmusterCli.typers.state import state


class FakeStudent:
    """Stand-in for linuxmusterTools.ldapconnector.LMNStudent."""

    def __init__(self, cn, school='default-school'):
        self.cn = cn
        self.school = school
        self.data = {'givenName': 'John', 'sn': 'Doe'}
        self.parents = []
        self.added = []
        self.removed = []

    def add_parent(self, parent):
        if parent == 'bad':
            raise Exception(f"cannot add {parent}")
        self.added.append(parent)

    def remove_parent(self, parent):
        if parent == 'bad':
            raise Exception(f"cannot remove {parent}")
        self.removed.append(parent)


class TestManage:

    # Note: this app is a Typer callback-only group (invoke_without_command=True)
    # with a required positional Argument. Empirically, click/typer only parses
    # correctly here when OPTIONS come before the STUDENT positional; passing
    # the positional first makes click treat it as an (unresolvable) subcommand
    # lookup and fail with "Missing argument 'STUDENT'". So all invocations
    # below put options first, student cn last.

    def test_lookup_failure_prints_message_and_does_not_crash(self, runner, monkeypatch):
        class FakeRaisingStudent:
            def __init__(self, cn, school='default-school'):
                raise Exception(f"Student {cn} not found in {school}")

        monkeypatch.setattr(student, 'LMNStudent', FakeRaisingStudent)

        result = runner.invoke(student.app, ['ghost'])

        # No sys.exit in this except branch: exit_code stays 0 even on failure.
        assert result.exit_code == 0
        assert 'Student ghost not found in default-school' in result.output

    def test_add_parents_splits_comma_separated_list(self, runner, monkeypatch):
        monkeypatch.setattr(student, 'LMNStudent', FakeStudent)

        result = runner.invoke(student.app, ['--add-parents', 'p1,p2', 'johndoe'])

        assert result.exit_code == 0
        assert 'Parents p1,p2 added!' in result.output

    def test_remove_parents_splits_comma_separated_list(self, runner, monkeypatch):
        monkeypatch.setattr(student, 'LMNStudent', FakeStudent)

        result = runner.invoke(student.app, ['--remove-parents', 'p1,p2', 'johndoe'])

        assert result.exit_code == 0
        assert 'Parents p1,p2 removed!' in result.output

    def test_add_and_remove_parents_both_shown_and_force_parents_listing(self, runner, monkeypatch):
        monkeypatch.setattr(student, 'LMNStudent', FakeStudent)

        result = runner.invoke(
            student.app,
            ['--add-parents', 'p1', '--remove-parents', 'p2', 'johndoe'],
        )

        assert result.exit_code == 0
        assert 'Parents p1 added!' in result.output
        assert 'Parents p2 removed!' in result.output
        # get_parents was never explicitly requested but is implied by add/remove:
        assert 'No parent found!' in result.output

    def test_add_parent_failure_aborts_the_rest_of_the_loop(self, runner, monkeypatch):
        # BUG-like current behavior (documented, not fixed): the try/except in
        # student.py wraps the WHOLE for-loop, not each iteration. So a single
        # failing add_parent() call aborts processing of any parents after it
        # in the same --add-parents list.
        monkeypatch.setattr(student, 'LMNStudent', FakeStudent)

        result = runner.invoke(student.app, ['--add-parents', 'good1,bad,good2', 'johndoe'])

        assert result.exit_code == 0
        assert 'cannot add bad' in result.output
        # "Parents ... added!" success message is never printed since the
        # exception happened inside the try, before reaching typer.secho(...).
        assert 'added!' not in result.output

    def test_get_parents_shows_table(self, runner, monkeypatch):
        class FakeStudentWithParents(FakeStudent):
            def __init__(self, cn, school='default-school'):
                super().__init__(cn, school=school)
                self.parents = [{'cn': 'parent1', 'displayName': 'Parent One'}]

        monkeypatch.setattr(student, 'LMNStudent', FakeStudentWithParents)

        result = runner.invoke(student.app, ['--parents', 'johndoe'])

        assert result.exit_code == 0
        assert 'parent1' in result.output
        assert 'Parent One' in result.output
        assert '1 parent(s)' in result.output

    def test_get_parents_with_no_parents_shows_message(self, runner, monkeypatch):
        monkeypatch.setattr(student, 'LMNStudent', FakeStudent)

        result = runner.invoke(student.app, ['--parents', 'johndoe'])

        assert result.exit_code == 0
        assert 'No parent found!' in result.output

    def test_raw_format_output(self, runner, monkeypatch):
        class FakeStudentWithParents(FakeStudent):
            def __init__(self, cn, school='default-school'):
                super().__init__(cn, school=school)
                self.parents = [{'cn': 'parent1', 'displayName': 'Parent One'}]

        monkeypatch.setattr(student, 'LMNStudent', FakeStudentWithParents)
        state.format = True
        state.raw = True

        result = runner.invoke(student.app, ['--parents', 'johndoe'])

        assert result.exit_code == 0
        assert 'Login\tDisplayname' in result.output
        assert 'parent1\tParent One' in result.output
