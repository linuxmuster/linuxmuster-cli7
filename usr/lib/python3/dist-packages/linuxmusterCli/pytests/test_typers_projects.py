from linuxmusterCli.typers import projects
from linuxmusterCli.typers.state import state


SAMPLE_PROJECTS = [
    {
        'cn': 'p_robotics', 'sophomorixMembers': ['johndoe'], 'sophomorixAdmins': ['teacher1'],
        'sophomorixMemberGroups': ['7a'], 'sophomorixAdminGroups': [],
        'sophomorixHidden': False, 'sophomorixJoinable': True,
    },
    {
        'cn': 'p_chess', 'sophomorixMembers': [], 'sophomorixAdmins': ['teacher2'],
        'sophomorixMemberGroups': [], 'sophomorixAdminGroups': ['staff'],
        'sophomorixHidden': True, 'sophomorixJoinable': False,
    },
]


class TestLs:

    def test_lists_all_projects(self, runner, monkeypatch):
        monkeypatch.setattr(projects.lr, 'get', lambda url, **kw: list(SAMPLE_PROJECTS))

        result = runner.invoke(projects.app, [])

        assert result.exit_code == 0
        assert 'p_robot' in result.output
        assert 'p_chess' in result.output
        assert '2 project(s)' in result.output

    def test_filter_str_matches_case_insensitively(self, runner, monkeypatch):
        monkeypatch.setattr(projects.lr, 'get', lambda url, **kw: list(SAMPLE_PROJECTS))

        result = runner.invoke(projects.app, ['ROBOT'])

        assert 'p_robot' in result.output
        assert 'p_chess' not in result.output
        assert '1 project(s)' in result.output

    def test_school_option_is_forwarded(self, runner, monkeypatch):
        seen = {}

        def fake_get(url, school='default-school'):
            seen['school'] = school
            return []

        monkeypatch.setattr(projects.lr, 'get', fake_get)

        runner.invoke(projects.app, ['--school', 'other-school'])

        assert seen['school'] == 'other-school'

    def test_no_match_shows_zero_projects(self, runner, monkeypatch):
        monkeypatch.setattr(projects.lr, 'get', lambda url, **kw: list(SAMPLE_PROJECTS))

        result = runner.invoke(projects.app, ['doesnotexist'])

        assert result.exit_code == 0
        assert '0 project(s)' in result.output

    def test_members_and_admins_are_comma_joined(self, runner, monkeypatch):
        monkeypatch.setattr(projects.lr, 'get', lambda url, **kw: [SAMPLE_PROJECTS[0]])

        result = runner.invoke(projects.app, [])

        assert 'johndoe' in result.output
        assert 'teacher1' in result.output

    def test_raw_format_output(self, runner, monkeypatch):
        monkeypatch.setattr(projects.lr, 'get', lambda url, **kw: [SAMPLE_PROJECTS[0]])
        state.format = True
        state.raw = True

        result = runner.invoke(projects.app, [])

        assert result.exit_code == 0
        assert 'p_robotics\tjohndoe\tteacher1\t7a\t\tFalse\tTrue' in result.output
