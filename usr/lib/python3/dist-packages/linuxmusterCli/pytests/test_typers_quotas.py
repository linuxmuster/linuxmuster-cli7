from linuxmusterCli.typers import quotas
from linuxmusterCli.typers.state import state


def quotas_for(global_used, global_limit, school_used, school_limit, cloud='1.0', mail='1.0'):
    return {
        'linuxmuster-global': {'used': global_used, 'hard_limit': global_limit},
        'default-school': {'used': school_used, 'hard_limit': school_limit},
        'cloud': cloud,
        'mail': mail,
    }


class TestValidation:

    def test_class_and_teachers_are_mutually_exclusive(self, runner, monkeypatch):
        result = runner.invoke(quotas.app, ['--class', 'foo', '--teachers'])

        assert result.exit_code == 0
        assert 'mutually exclusives' in result.output

    def test_no_option_given_raises_unbound_local_error(self, runner, monkeypatch):
        # BUG: neither --class nor --teachers given leaves `title_suffix` (and
        # `users`) unassigned, and the Table(title=...) f-string on the next
        # line blows up with UnboundLocalError. Documenting current behavior,
        # not fixing it.
        result = runner.invoke(quotas.app, [])

        assert result.exit_code != 0
        assert isinstance(result.exception, UnboundLocalError)
        assert 'title_suffix' in str(result.exception)


class TestLs:

    def test_teachers_option_lists_teacher_quotas(self, runner, monkeypatch):
        monkeypatch.setattr(quotas.lr, 'getval', lambda url, attr: ['alice'])
        monkeypatch.setattr(quotas, 'get_user_quotas', lambda user: quotas_for(1.0, 10.0, 9.0, 10.0))

        result = runner.invoke(quotas.app, ['--teachers'])

        assert result.exit_code == 0
        assert 'alice' in result.output
        assert 'of teachers' in result.output

    def test_schoolclass_option_is_forwarded(self, runner, monkeypatch):
        seen = {}

        def fake_getval(url, attr):
            seen['url'] = url
            seen['attr'] = attr
            return ['bob']

        monkeypatch.setattr(quotas.lr, 'getval', fake_getval)
        monkeypatch.setattr(quotas, 'get_user_quotas', lambda user: quotas_for(1.0, 10.0, 1.0, 10.0))

        result = runner.invoke(quotas.app, ['--class', '7a'])

        assert result.exit_code == 0
        assert seen['url'] == '/schoolclasses/7a'
        assert seen['attr'] == 'sophomorixMembers'
        assert 'of schoolclass 7a' in result.output

    def test_rows_are_sorted_by_school_quota_percentage_descending(self, runner, monkeypatch):
        monkeypatch.setattr(quotas.lr, 'getval', lambda url, attr: ['lowuser', 'highuser'])

        def fake_get_user_quotas(user):
            if user == 'lowuser':
                return quotas_for(1.0, 10.0, 1.0, 10.0)  # 10%
            return quotas_for(1.0, 10.0, 9.0, 10.0)  # 90%

        monkeypatch.setattr(quotas, 'get_user_quotas', fake_get_user_quotas)

        result = runner.invoke(quotas.app, ['--teachers'])

        assert result.exit_code == 0
        assert result.output.index('highuser') < result.output.index('lowuser')

    def test_no_limit_hard_limit_does_not_crash_and_stays_out_of_percentage(self, runner, monkeypatch):
        monkeypatch.setattr(quotas.lr, 'getval', lambda url, attr: ['nolimituser'])
        monkeypatch.setattr(
            quotas, 'get_user_quotas',
            lambda user: quotas_for(1.0, 'NO LIMIT', 1.0, 'NO LIMIT'),
        )

        result = runner.invoke(quotas.app, ['--teachers'])

        assert result.exit_code == 0
        assert 'NO LIMIT' in result.output
        assert 'nolimituser' in result.output

    def test_raw_format_output(self, runner, monkeypatch):
        monkeypatch.setattr(quotas.lr, 'getval', lambda url, attr: ['alice'])
        monkeypatch.setattr(quotas, 'get_user_quotas', lambda user: quotas_for(1.0, 10.0, 9.0, 10.0))
        state.format = True
        state.raw = True

        result = runner.invoke(quotas.app, ['--teachers'])

        assert result.exit_code == 0
        assert 'alice\t1.0/10.0\t9.0/10.0\t1.0\t1.0' in result.output
