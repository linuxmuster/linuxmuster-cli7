from linuxmusterCli.typers import users
from linuxmusterCli.typers.state import state


SAMPLE_USERS = [
    {
        'displayName': 'Jane Teach', 'sn': 'Teach', 'givenName': 'Jane',
        'sAMAccountName': 'janeteach', 'sophomorixAdminClass': 'teachers',
        'sophomorixAdminFile': 'teachers.csv', 'sophomorixExitAdminClass': '',
        'sophomorixRole': 'teacher', 'sophomorixStatus': 'A',
    },
    {
        'displayName': 'John Doe', 'sn': 'Doe', 'givenName': 'John',
        'sAMAccountName': 'johndoe', 'sophomorixAdminClass': '5a',
        'sophomorixAdminFile': 'students.csv', 'sophomorixExitAdminClass': '',
        'sophomorixRole': 'student', 'sophomorixStatus': 'A',
    },
    {
        'displayName': 'Old Student', 'sn': 'Old', 'givenName': 'Stu',
        'sAMAccountName': 'oldstu', 'sophomorixAdminClass': 'attic',
        'sophomorixAdminFile': 'students.csv', 'sophomorixExitAdminClass': '5a',
        'sophomorixRole': 'student', 'sophomorixStatus': 'D',
    },
]


class TestLs:

    def test_golden_path_listing(self, runner, monkeypatch):
        monkeypatch.setattr(users.lr, 'get', lambda url, **kw: list(SAMPLE_USERS))

        result = runner.invoke(users.app, [])

        assert result.exit_code == 0
        assert 'Doe' in result.output
        assert 'johndoe' in result.output
        assert 'Teach' in result.output
        assert 'janeteach' in result.output
        assert 'Old' in result.output
        # attic special-cased adminclass / role rendering (role column wraps
        # across two lines in the narrow captured table, so check separately)
        assert 'attic (5a)' in result.output
        assert 'student' in result.output
        assert '(student)' in result.output
        assert '3 user(s)' in result.output

    def test_role_flags_always_use_rawusers(self, runner, monkeypatch):
        # /users/search/<role>/ builds full LMNUserModel objects, with one
        # ldap request per student for its parents: ~1000 requests for -u.
        seen = []

        def fake_get(url, **kw):
            seen.append(url)
            return []

        monkeypatch.setattr(users.lr, 'get', fake_get)

        for flags in ([], ['--admins'], ['--teachers'], ['--students']):
            runner.invoke(users.app, flags)

        assert seen == ['/rawusers'] * 4

    def test_students_flag_keeps_only_students(self, runner, monkeypatch):
        monkeypatch.setattr(users.lr, 'get', lambda url, **kw: list(SAMPLE_USERS))

        result = runner.invoke(users.app, ['--students'])

        assert result.exit_code == 0
        assert 'johndoe' in result.output
        assert 'oldstu' in result.output
        assert 'janeteach' not in result.output
        assert '2 user(s)' in result.output

    def test_teachers_flag_keeps_only_teachers(self, runner, monkeypatch):
        monkeypatch.setattr(users.lr, 'get', lambda url, **kw: list(SAMPLE_USERS))

        result = runner.invoke(users.app, ['--teachers'])

        assert 'janeteach' in result.output
        assert 'johndoe' not in result.output
        assert '1 user(s)' in result.output

    def test_admins_flag_keeps_global_and_school_admins(self, runner, monkeypatch):
        admins = [
            dict(SAMPLE_USERS[0], sAMAccountName='globadm', sophomorixRole='globaladministrator'),
            dict(SAMPLE_USERS[0], sAMAccountName='schooladm', sophomorixRole='schooladministrator'),
        ]
        monkeypatch.setattr(users.lr, 'get', lambda url, **kw: list(SAMPLE_USERS) + admins)

        result = runner.invoke(users.app, ['--admins'])

        assert 'globadm' in result.output
        assert 'schooladm' in result.output
        assert 'janeteach' not in result.output
        assert '2 user(s)' in result.output

    def test_status_filters_users(self, runner, monkeypatch):
        monkeypatch.setattr(users.lr, 'get', lambda url, **kw: list(SAMPLE_USERS))

        result = runner.invoke(users.app, ['--status', 'A'])

        assert result.exit_code == 0
        assert 'johndoe' in result.output
        assert 'janeteach' in result.output
        assert 'oldstu' not in result.output
        assert '2 user(s)' in result.output

    def test_filter_str_matches_login_case_insensitively(self, runner, monkeypatch):
        monkeypatch.setattr(users.lr, 'get', lambda url, **kw: list(SAMPLE_USERS))

        result = runner.invoke(users.app, ['JOHNDOE'])

        assert result.exit_code == 0
        assert 'johndoe' in result.output
        assert 'janeteach' not in result.output
        assert '1 user(s)' in result.output

    def test_filter_str_matches_adminclass(self, runner, monkeypatch):
        monkeypatch.setattr(users.lr, 'get', lambda url, **kw: list(SAMPLE_USERS))

        result = runner.invoke(users.app, ['teachers'])

        assert result.exit_code == 0
        assert 'janeteach' in result.output
        assert 'johndoe' not in result.output

    def test_sort_order_by_role_then_sn_then_givenname(self, runner, monkeypatch):
        monkeypatch.setattr(users.lr, 'get', lambda url, **kw: list(SAMPLE_USERS))

        result = runner.invoke(users.app, [])

        # sophomorixRole: 'student' sorts before 'teacher'; among students, sn 'Doe' < 'Old'
        pos_doe = result.output.find('Doe')
        pos_old = result.output.find('Old')
        pos_teach = result.output.find('Teach')

        assert pos_doe != -1 and pos_old != -1 and pos_teach != -1
        assert pos_doe < pos_old < pos_teach

    def test_school_option_is_forwarded(self, runner, monkeypatch):
        seen = {}

        def fake_get(url, attributes=None, school='default-school'):
            seen['school'] = school
            return []

        monkeypatch.setattr(users.lr, 'get', fake_get)

        runner.invoke(users.app, ['--school', 'other-school'])

        assert seen['school'] == 'other-school'

    def test_status_column_shows_readable_status_and_code(self, runner, monkeypatch):
        monkeypatch.setattr(users.lr, 'get', lambda url, **kw: [SAMPLE_USERS[1]])

        result = runner.invoke(users.app, [])

        assert result.exit_code == 0
        assert 'Activated' in result.output
        assert '(A)' in result.output

    def test_raw_format_output(self, runner, monkeypatch):
        monkeypatch.setattr(users.lr, 'get', lambda url, **kw: [SAMPLE_USERS[1]])
        state.format = True
        state.raw = True

        result = runner.invoke(users.app, [])

        assert result.exit_code == 0
        assert 'Doe\tJohn\tjohndoe\t5a\tstudent\tActivated (A)' in result.output
