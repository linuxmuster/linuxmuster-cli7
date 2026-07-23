from linuxmusterCli.typers import mgmtgroup


class FakeGroupManager:
    """Stand-in for linuxmusterTools.samba_util.GroupManager, tracked per instance."""

    instances = []

    def __init__(self, school='default-school'):
        self.school = school
        self.added = []
        self.removed = []
        FakeGroupManager.instances.append(self)

    def add_members(self, group, members):
        self.added.append((group, members))

    def remove_members(self, group, members):
        self.removed.append((group, members))


class TestManage:
    """
    Note: this app is a Typer callback-only group (invoke_without_command=True)
    with a required positional Argument (group). Empirically, click/typer only
    parses correctly here when OPTIONS come before the GROUP positional; passing
    the positional first makes click try to resolve it as a subcommand and fail
    with "Missing argument 'GROUP'". So all invocations below put options
    first, group name last.
    """

    def setup_method(self):
        FakeGroupManager.instances = []

    def test_add_members_forwards_group_and_parsed_list(self, runner, monkeypatch):
        monkeypatch.setattr(mgmtgroup, 'GroupManager', FakeGroupManager)

        result = runner.invoke(mgmtgroup.app, ['--add-members', 'johndoe,janedoe', 'internet'])

        assert result.exit_code == 0
        assert FakeGroupManager.instances[0].added == [('internet', ['johndoe', 'janedoe'])]
        assert FakeGroupManager.instances[0].removed == []

    def test_remove_members_forwards_group_and_parsed_list(self, runner, monkeypatch):
        monkeypatch.setattr(mgmtgroup, 'GroupManager', FakeGroupManager)

        result = runner.invoke(mgmtgroup.app, ['--remove-members', 'johndoe', 'internet'])

        assert result.exit_code == 0
        assert FakeGroupManager.instances[0].removed == [('internet', ['johndoe'])]
        assert FakeGroupManager.instances[0].added == []

    def test_add_and_remove_can_be_combined(self, runner, monkeypatch):
        monkeypatch.setattr(mgmtgroup, 'GroupManager', FakeGroupManager)

        result = runner.invoke(
            mgmtgroup.app,
            ['--add-members', 'johndoe', '--remove-members', 'janedoe', 'internet'],
        )

        assert result.exit_code == 0
        assert FakeGroupManager.instances[0].added == [('internet', ['johndoe'])]
        assert FakeGroupManager.instances[0].removed == [('internet', ['janedoe'])]

    def test_school_option_is_forwarded_to_group_manager(self, runner, monkeypatch):
        monkeypatch.setattr(mgmtgroup, 'GroupManager', FakeGroupManager)

        runner.invoke(mgmtgroup.app, ['--add-members', 'johndoe', '--school', 'other-school', 'internet'])

        assert FakeGroupManager.instances[0].school == 'other-school'

    def test_add_members_exception_causes_sys_exit_with_message(self, runner, monkeypatch):
        class FakeRaisingGroupManager(FakeGroupManager):
            def add_members(self, group, members):
                raise Exception(f"Group {group} does not exist")

        monkeypatch.setattr(mgmtgroup, 'GroupManager', FakeRaisingGroupManager)

        result = runner.invoke(mgmtgroup.app, ['--add-members', 'johndoe', 'internet'])

        assert result.exit_code == 1
        assert 'Group internet does not exist' in result.output

    def test_remove_members_exception_causes_sys_exit_with_message(self, runner, monkeypatch):
        class FakeRaisingGroupManager(FakeGroupManager):
            def remove_members(self, group, members):
                raise Exception(f"Cannot remove from {group}")

        monkeypatch.setattr(mgmtgroup, 'GroupManager', FakeRaisingGroupManager)

        result = runner.invoke(mgmtgroup.app, ['--remove-members', 'johndoe', 'internet'])

        assert result.exit_code == 1
        assert 'Cannot remove from internet' in result.output

    def test_no_options_given_does_nothing_current_buggy_behavior(self, runner, monkeypatch):
        # CONFIRMED BUG (documented here, not fixed): the guard
        # `if add_members is None and remove_members is None:` in mgmtgroup.py
        # can never trigger because both options default to '' (empty string),
        # not None. So calling `mgmtgroup manage <group>` with no options at
        # all currently does nothing silently: exit_code 0, no output, and
        # neither add_members() nor remove_members() is ever called -- even
        # though GroupManager itself IS still instantiated.
        monkeypatch.setattr(mgmtgroup, 'GroupManager', FakeGroupManager)

        result = runner.invoke(mgmtgroup.app, ['internet'])

        assert result.exit_code == 0
        assert result.output == ''
        assert len(FakeGroupManager.instances) == 1
        assert FakeGroupManager.instances[0].added == []
        assert FakeGroupManager.instances[0].removed == []
