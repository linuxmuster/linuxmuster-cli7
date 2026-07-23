from linuxmusterCli.typers import lmngroup
from linuxmusterCli.typers.state import state


SAMPLE_GROUPS = [
    {
        'cn': 'robotics', 'description': 'robotics club',
        'member': [
            'CN=johndoe,OU=Students,OU=default-school,OU=SCHOOLS,DC=linuxmuster,DC=lan',
            'CN=janedoe,OU=Teachers,OU=default-school,OU=SCHOOLS,DC=linuxmuster,DC=lan',
        ],
        'sophomorixHidden': False, 'sophomorixJoinable': True, 'sophomorixType': 'lmngroup',
    },
    {
        'cn': 'chess', 'description': 'chess club', 'member': [],
        'sophomorixHidden': True, 'sophomorixJoinable': False, 'sophomorixType': 'lmngroup',
    },
    {
        'cn': 'legacy-group', 'description': 'old sophomorix group',
        'member': ['CN=alice,OU=Students,OU=default-school,OU=SCHOOLS,DC=linuxmuster,DC=lan'],
        'sophomorixHidden': False, 'sophomorixJoinable': False, 'sophomorixType': 'sophomorix-group',
    },
]


class FakeLMNGroup:
    """
    Stand-in for linuxmusterTools.ldapconnector.LMNGroup, tracked per
    instance. Mirrors the real add_members()/remove_members() contract:
    invalid cn in `invalid_users` don't abort the batch, they're reported
    back as (user, error) tuples instead.
    """

    instances = []

    def __init__(self, cn, school='default-school'):
        self.cn = cn
        self.school = school
        self.new = False
        self.added = []
        self.removed = []
        self.invalid_users = set()
        FakeLMNGroup.instances.append(self)

    def add_members(self, userlist):
        failures = []
        for user in userlist:
            if user in self.invalid_users:
                failures.append((user, f"The user {user} was not found in ldap."))
            else:
                self.added.append(user)
        return failures

    def remove_members(self, userlist):
        failures = []
        for user in userlist:
            if user in self.invalid_users:
                failures.append((user, f"The object {user} was not found in ldap."))
            else:
                self.removed.append(user)
        return failures


class TestLs:

    def test_filters_out_non_lmngroup_entries(self, runner, monkeypatch):
        monkeypatch.setattr(lmngroup.lr, 'get', lambda url, **kw: list(SAMPLE_GROUPS))

        result = runner.invoke(lmngroup.app, ['ls'])

        assert result.exit_code == 0
        assert 'robotics' in result.output
        assert 'chess' in result.output
        assert 'legacy-group' not in result.output
        assert '2 lmngroup(s)' in result.output

    def test_filter_str_matches_case_insensitively(self, runner, monkeypatch):
        monkeypatch.setattr(lmngroup.lr, 'get', lambda url, **kw: list(SAMPLE_GROUPS))

        result = runner.invoke(lmngroup.app, ['ls', 'ROBOT'])

        assert 'robotics' in result.output
        assert 'chess' not in result.output

    def test_school_option_is_forwarded(self, runner, monkeypatch):
        seen = {}

        def fake_get(url, school='default-school'):
            seen['school'] = school
            return []

        monkeypatch.setattr(lmngroup.lr, 'get', fake_get)

        runner.invoke(lmngroup.app, ['ls', '--school', 'other-school'])

        assert seen['school'] == 'other-school'

    def test_member_cns_are_displayed(self, runner, monkeypatch):
        monkeypatch.setattr(lmngroup.lr, 'get', lambda url, **kw: list(SAMPLE_GROUPS))

        result = runner.invoke(lmngroup.app, ['ls'])

        assert 'johndoe' in result.output
        assert 'janedoe' in result.output

    def test_member_dn_with_unexpected_rdn_is_skipped(self, runner, monkeypatch):
        data = [dict(SAMPLE_GROUPS[0])]
        data[0]['member'] = ['not-a-valid-rdn']
        monkeypatch.setattr(lmngroup.lr, 'get', lambda url, **kw: data)

        result = runner.invoke(lmngroup.app, ['ls'])

        assert result.exit_code == 0

    def test_raw_format_output(self, runner, monkeypatch):
        monkeypatch.setattr(lmngroup.lr, 'get', lambda url, **kw: list(SAMPLE_GROUPS))
        state.format = True
        state.raw = True

        result = runner.invoke(lmngroup.app, ['ls'])

        assert result.exit_code == 0
        assert 'robotics\trobotics club\tjohndoe,janedoe' in result.output


class TestManage:

    def setup_method(self):
        FakeLMNGroup.instances = []

    def test_requires_add_or_remove_option(self, runner, monkeypatch):
        monkeypatch.setattr(lmngroup, 'LMNGroup', FakeLMNGroup)

        result = runner.invoke(lmngroup.app, ['manage', 'robotics'])

        assert result.exit_code == 0
        assert 'Please choose at least one' in result.output
        assert FakeLMNGroup.instances == []

    def test_add_members_splits_comma_separated_list(self, runner, monkeypatch):
        monkeypatch.setattr(lmngroup, 'LMNGroup', FakeLMNGroup)

        result = runner.invoke(lmngroup.app, ['manage', 'robotics', '--add-members', 'johndoe,janedoe'])

        assert result.exit_code == 0
        assert FakeLMNGroup.instances[0].added == ['johndoe', 'janedoe']
        assert FakeLMNGroup.instances[0].removed == []

    def test_remove_members_splits_comma_separated_list(self, runner, monkeypatch):
        monkeypatch.setattr(lmngroup, 'LMNGroup', FakeLMNGroup)

        result = runner.invoke(lmngroup.app, ['manage', 'robotics', '--remove-members', 'johndoe'])

        assert result.exit_code == 0
        assert FakeLMNGroup.instances[0].removed == ['johndoe']
        assert FakeLMNGroup.instances[0].added == []

    def test_add_members_reports_success_message(self, runner, monkeypatch):
        monkeypatch.setattr(lmngroup, 'LMNGroup', FakeLMNGroup)

        result = runner.invoke(lmngroup.app, ['manage', 'robotics', '--add-members', 'johndoe,janedoe'])

        assert result.exit_code == 0
        assert 'Added: johndoe, janedoe' in result.output

    def test_add_members_invalid_cn_does_not_abort_the_rest_of_the_batch(self, runner, monkeypatch):
        monkeypatch.setattr(lmngroup, 'LMNGroup', FakeLMNGroup)

        def fake_group(cn, school='default-school'):
            g = FakeLMNGroup(cn, school=school)
            g.invalid_users = {'ghost1', 'ghost2'}
            return g

        monkeypatch.setattr(lmngroup, 'LMNGroup', fake_group)

        result = runner.invoke(
            lmngroup.app,
            ['manage', 'robotics', '--add-members', 'ghost1,janedoe,ghost2,bobdoe'],
        )

        assert result.exit_code == 0
        # Valid entries were still added despite the invalid ones in the list.
        assert FakeLMNGroup.instances[0].added == ['janedoe', 'bobdoe']
        assert 'Added: janedoe, bobdoe' in result.output
        assert 'Could not add ghost1' in result.output
        assert 'Could not add ghost2' in result.output

    def test_remove_members_invalid_cn_does_not_abort_the_rest_of_the_batch(self, runner, monkeypatch):
        def fake_group(cn, school='default-school'):
            g = FakeLMNGroup(cn, school=school)
            g.invalid_users = {'ghost'}
            return g

        monkeypatch.setattr(lmngroup, 'LMNGroup', fake_group)

        result = runner.invoke(lmngroup.app, ['manage', 'robotics', '--remove-members', 'ghost,janedoe'])

        assert result.exit_code == 0
        assert FakeLMNGroup.instances[0].removed == ['janedoe']
        assert 'Removed: janedoe' in result.output
        assert 'Could not remove ghost' in result.output

    def test_add_and_remove_can_be_combined(self, runner, monkeypatch):
        monkeypatch.setattr(lmngroup, 'LMNGroup', FakeLMNGroup)

        result = runner.invoke(
            lmngroup.app,
            ['manage', 'robotics', '--add-members', 'johndoe', '--remove-members', 'janedoe'],
        )

        assert result.exit_code == 0
        assert FakeLMNGroup.instances[0].added == ['johndoe']
        assert FakeLMNGroup.instances[0].removed == ['janedoe']

    def test_exits_when_group_does_not_exist(self, runner, monkeypatch):
        class FakeNewGroup(FakeLMNGroup):
            def __init__(self, cn, school='default-school'):
                super().__init__(cn, school=school)
                self.new = True

        monkeypatch.setattr(lmngroup, 'LMNGroup', FakeNewGroup)

        result = runner.invoke(lmngroup.app, ['manage', 'ghost', '--add-members', 'johndoe'])

        assert result.exit_code == 1
        assert 'does not exist in ldap' in result.output
        assert FakeNewGroup.instances[0].added == []

    def test_exits_with_message_on_constructor_error(self, runner, monkeypatch):
        class FakeRaisingGroup:
            def __init__(self, cn, school='default-school'):
                raise Exception(f"School {school} was not found in ldap.")

        monkeypatch.setattr(lmngroup, 'LMNGroup', FakeRaisingGroup)

        result = runner.invoke(lmngroup.app, ['manage', 'robotics', '--add-members', 'johndoe'])

        assert result.exit_code == 1
        assert 'was not found in ldap' in result.output
