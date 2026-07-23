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

    def test_admins_flag_selects_admins_url(self, runner, monkeypatch):
        seen = {}

        def fake_get(url, **kw):
            seen['url'] = url
            return []

        monkeypatch.setattr(users.lr, 'get', fake_get)

        runner.invoke(users.app, ['--admins'])

        assert seen['url'] == '/users/search/admins/'

    def test_teachers_flag_selects_teacher_url(self, runner, monkeypatch):
        seen = {}

        def fake_get(url, **kw):
            seen['url'] = url
            return []

        monkeypatch.setattr(users.lr, 'get', fake_get)

        runner.invoke(users.app, ['--teachers'])

        assert seen['url'] == '/users/search/teacher/'

    def test_students_flag_selects_student_url(self, runner, monkeypatch):
        seen = {}

        def fake_get(url, **kw):
            seen['url'] = url
            return []

        monkeypatch.setattr(users.lr, 'get', fake_get)

        runner.invoke(users.app, ['--students'])

        assert seen['url'] == '/users/search/student/'

    def test_default_selects_rawusers_url(self, runner, monkeypatch):
        seen = {}

        def fake_get(url, **kw):
            seen['url'] = url
            return []

        monkeypatch.setattr(users.lr, 'get', fake_get)

        runner.invoke(users.app, [])

        assert seen['url'] == '/rawusers'

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
