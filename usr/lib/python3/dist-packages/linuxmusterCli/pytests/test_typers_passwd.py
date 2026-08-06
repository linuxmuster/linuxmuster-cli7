from linuxmusterCli.typers import passwd


class FakeResult:
    def __init__(self, ok, violations=()):
        self.ok = ok
        self.violations = violations


class FakePolicyProvider:
    """
    Stand-in for linuxmusterTools.passwords.PasswordPolicyProvider. Rejects
    the literal password 'weak', accepts anything else — passwd.py imports
    the real class locally inside manage(), so tests patch it at its source
    (linuxmusterTools.passwords.PasswordPolicyProvider), not on the passwd module.
    """

    def validate(self, password, role='', school='default-school', username=None):
        if password == 'weak':
            return FakeResult(False, ('too weak',))
        return FakeResult(True)


class FakeUser:
    """Stand-in for linuxmusterTools.ldapconnector.LMNUser."""

    new = False

    def __init__(self, cn, school='default-school'):
        self.cn = cn
        self.school = school
        self.data = {'sophomorixFirstPassword': 'OldFirstPw1!', 'sophomorixRole': 'teacher'}
        self.calls = []
        self._first_password_still_set = True

    def setattr(self, data):
        self.data.update(data)
        self.calls.append(('setattr', data))

    def set_actual_password(self, password):
        self.calls.append(('set_actual_password', password))

    def set_random_first_password(self):
        self.calls.append(('set_random_first_password',))
        return 'GeneRat3dPw!'

    def test_first_password(self):
        return self._first_password_still_set


class TestManage:

    # Note: same click/typer quirk as student.py/user.py — options must come
    # before the positional USER argument, otherwise it's misparsed as an
    # attempted (unresolvable) subcommand. All invocations below put options
    # first, user login last.

    def test_no_action_flag_errors(self, runner, monkeypatch):
        monkeypatch.setattr(passwd, 'LMNUser', FakeUser)

        result = runner.invoke(passwd.app, ['johndoe'])

        assert result.exit_code == 1
        assert 'Choose exactly one of' in result.output

    def test_two_action_flags_errors(self, runner, monkeypatch):
        monkeypatch.setattr(passwd, 'LMNUser', FakeUser)

        result = runner.invoke(passwd.app, ['--set-first-password', '--set-current-password', 'johndoe'])

        assert result.exit_code == 1
        assert 'Choose exactly one of' in result.output

    def test_user_not_found(self, runner, monkeypatch):
        class FakeNewUser(FakeUser):
            new = True

        monkeypatch.setattr(passwd, 'LMNUser', FakeNewUser)

        result = runner.invoke(passwd.app, ['--set-random-password', 'ghost'])

        assert result.exit_code == 1
        assert 'User ghost not found.' in result.output

    def test_lookup_failure_prints_message_and_exits_nonzero(self, runner, monkeypatch):
        class FakeRaisingUser:
            def __init__(self, cn, school='default-school'):
                raise Exception(f"{cn} is not a valid CN")

        monkeypatch.setattr(passwd, 'LMNUser', FakeRaisingUser)

        result = runner.invoke(passwd.app, ['--set-random-password', 'bad cn'])

        assert result.exit_code == 1
        assert 'bad cn is not a valid CN' in result.output

    def test_school_option_is_forwarded(self, runner, monkeypatch):
        seen = {}

        def make(cn, school='default-school'):
            seen['school'] = school
            return FakeUser(cn, school)

        monkeypatch.setattr(passwd, 'LMNUser', make)

        runner.invoke(passwd.app, ['--reset-first-password', '--school', 'other-school', 'johndoe'])

        assert seen['school'] == 'other-school'

    # --- --check-first-pw ---------------------------------------------------

    def test_check_first_password_still_set(self, runner, monkeypatch):
        class FakeUserStillSet(FakeUser):
            def __init__(self, cn, school='default-school'):
                super().__init__(cn, school)
                self._first_password_still_set = True

        monkeypatch.setattr(passwd, 'LMNUser', FakeUserStillSet)

        result = runner.invoke(passwd.app, ['--check-first-pw', 'johndoe'])

        assert result.exit_code == 0
        assert 'is still the current one' in result.output

    def test_check_first_password_changed(self, runner, monkeypatch):
        class FakeUserChanged(FakeUser):
            def __init__(self, cn, school='default-school'):
                super().__init__(cn, school)
                self._first_password_still_set = False

        monkeypatch.setattr(passwd, 'LMNUser', FakeUserChanged)

        result = runner.invoke(passwd.app, ['--check-first-pw', 'johndoe'])

        assert result.exit_code == 0
        assert 'is no longer the current one' in result.output

    def test_check_first_password_raises(self, runner, monkeypatch):
        class FakeUserFailingCheck(FakeUser):
            def test_first_password(self):
                raise Exception('ldap.SERVER_DOWN')

        monkeypatch.setattr(passwd, 'LMNUser', FakeUserFailingCheck)

        result = runner.invoke(passwd.app, ['--check-first-pw', 'johndoe'])

        assert result.exit_code == 1
        assert 'ldap.SERVER_DOWN' in result.output

    # --- --reset-first-password -------------------------------------------

    def test_reset_first_password_success(self, runner, monkeypatch):
        monkeypatch.setattr(passwd, 'LMNUser', FakeUser)

        result = runner.invoke(passwd.app, ['--reset-first-password', 'johndoe'])

        assert result.exit_code == 0
        assert 'reset back to the stored first password' in result.output

    def test_reset_first_password_none_stored(self, runner, monkeypatch):
        class FakeUserNoFirst(FakeUser):
            def __init__(self, cn, school='default-school'):
                super().__init__(cn, school)
                self.data['sophomorixFirstPassword'] = ''

        monkeypatch.setattr(passwd, 'LMNUser', FakeUserNoFirst)

        result = runner.invoke(passwd.app, ['--reset-first-password', 'johndoe'])

        assert result.exit_code == 1
        assert 'nothing to reset to' in result.output

    def test_reset_first_password_set_actual_password_raises(self, runner, monkeypatch):
        class FakeUserFailingReset(FakeUser):
            def set_actual_password(self, password):
                raise Exception('requires root')

        monkeypatch.setattr(passwd, 'LMNUser', FakeUserFailingReset)

        result = runner.invoke(passwd.app, ['--reset-first-password', 'johndoe'])

        assert result.exit_code == 1
        assert 'Cannot reset current password: requires root' in result.output

    # --- --set-random-password ---------------------------------------------

    def test_set_random_password_success(self, runner, monkeypatch):
        monkeypatch.setattr(passwd, 'LMNUser', FakeUser)

        result = runner.invoke(passwd.app, ['--set-random-password', 'johndoe'])

        assert result.exit_code == 0
        assert 'New random password for johndoe: GeneRat3dPw!' in result.output

    def test_set_random_password_raises(self, runner, monkeypatch):
        class FakeUserFailingRandom(FakeUser):
            def set_random_first_password(self):
                raise RuntimeError('Could not generate a password satisfying the current policy after 100 attempts.')

        monkeypatch.setattr(passwd, 'LMNUser', FakeUserFailingRandom)

        result = runner.invoke(passwd.app, ['--set-random-password', 'johndoe'])

        assert result.exit_code == 1
        assert 'Cannot set a random password' in result.output

    # --- --set-first-password (always also sets the current password) -----

    def test_set_first_password_rejected_by_policy(self, runner, monkeypatch):
        monkeypatch.setattr(passwd, 'LMNUser', FakeUser)
        monkeypatch.setattr('linuxmusterTools.passwords.PasswordPolicyProvider', FakePolicyProvider)

        result = runner.invoke(passwd.app, ['--set-first-password', 'johndoe'], input='weak\nweak\n')

        assert result.exit_code == 1
        assert 'does not meet requirements: too weak' in result.output

    def test_set_first_password_success_sets_both(self, runner, monkeypatch):
        captured = {}

        def make(cn, school='default-school'):
            u = FakeUser(cn, school)
            captured['user'] = u
            return u

        monkeypatch.setattr(passwd, 'LMNUser', make)
        monkeypatch.setattr('linuxmusterTools.passwords.PasswordPolicyProvider', FakePolicyProvider)

        result = runner.invoke(passwd.app, ['--set-first-password', 'johndoe'], input='Str0ngPassw0rd!\nStr0ngPassw0rd!\n')

        assert result.exit_code == 0
        assert 'also set as current password' in result.output
        assert ('setattr', {'sophomorixFirstPassword': 'Str0ngPassw0rd!'}) in captured['user'].calls
        assert ('set_actual_password', 'Str0ngPassw0rd!') in captured['user'].calls

    def test_set_first_password_set_actual_password_raises(self, runner, monkeypatch):
        class FakeUserFailingActual(FakeUser):
            def set_actual_password(self, password):
                raise Exception('samba rejected it')

        monkeypatch.setattr(passwd, 'LMNUser', FakeUserFailingActual)
        monkeypatch.setattr('linuxmusterTools.passwords.PasswordPolicyProvider', FakePolicyProvider)

        result = runner.invoke(passwd.app, ['--set-first-password', 'johndoe'], input='Str0ngPassw0rd!\nStr0ngPassw0rd!\n')

        assert result.exit_code == 1
        assert 'Cannot set current password: samba rejected it' in result.output

    # --- --set-current-password (never touches the first password) --------

    def test_set_current_password_rejected_by_policy(self, runner, monkeypatch):
        monkeypatch.setattr(passwd, 'LMNUser', FakeUser)
        monkeypatch.setattr('linuxmusterTools.passwords.PasswordPolicyProvider', FakePolicyProvider)

        result = runner.invoke(passwd.app, ['--set-current-password', 'johndoe'], input='weak\nweak\n')

        assert result.exit_code == 1
        assert 'does not meet requirements: too weak' in result.output

    def test_set_current_password_success_leaves_first_untouched(self, runner, monkeypatch):
        captured = {}

        def make(cn, school='default-school'):
            u = FakeUser(cn, school)
            captured['user'] = u
            return u

        monkeypatch.setattr(passwd, 'LMNUser', make)
        monkeypatch.setattr('linuxmusterTools.passwords.PasswordPolicyProvider', FakePolicyProvider)

        result = runner.invoke(passwd.app, ['--set-current-password', 'johndoe'], input='Str0ngPassw0rd!\nStr0ngPassw0rd!\n')

        assert result.exit_code == 0
        assert 'first password left untouched' in result.output
        assert captured['user'].calls == [('set_actual_password', 'Str0ngPassw0rd!')]

    def test_set_current_password_set_actual_password_raises(self, runner, monkeypatch):
        class FakeUserFailingActual(FakeUser):
            def set_actual_password(self, password):
                raise Exception('samba rejected it')

        monkeypatch.setattr(passwd, 'LMNUser', FakeUserFailingActual)
        monkeypatch.setattr('linuxmusterTools.passwords.PasswordPolicyProvider', FakePolicyProvider)

        result = runner.invoke(passwd.app, ['--set-current-password', 'johndoe'], input='Str0ngPassw0rd!\nStr0ngPassw0rd!\n')

        assert result.exit_code == 1
        assert 'samba rejected it' in result.output


class TestShortOptions:
    """Each short flag must trigger the exact same branch as its long form."""

    def test_dash_f_is_set_first_password(self, runner, monkeypatch):
        captured = {}

        def make(cn, school='default-school'):
            u = FakeUser(cn, school)
            captured['user'] = u
            return u

        monkeypatch.setattr(passwd, 'LMNUser', make)
        monkeypatch.setattr('linuxmusterTools.passwords.PasswordPolicyProvider', FakePolicyProvider)

        result = runner.invoke(passwd.app, ['-f', 'johndoe'], input='Str0ngPassw0rd!\nStr0ngPassw0rd!\n')

        assert result.exit_code == 0
        assert 'also set as current password' in result.output
        assert ('set_actual_password', 'Str0ngPassw0rd!') in captured['user'].calls

    def test_dash_p_is_set_current_password(self, runner, monkeypatch):
        monkeypatch.setattr(passwd, 'LMNUser', FakeUser)
        monkeypatch.setattr('linuxmusterTools.passwords.PasswordPolicyProvider', FakePolicyProvider)

        result = runner.invoke(passwd.app, ['-p', 'johndoe'], input='Str0ngPassw0rd!\nStr0ngPassw0rd!\n')

        assert result.exit_code == 0
        assert 'first password left untouched' in result.output

    def test_dash_r_is_set_random_password(self, runner, monkeypatch):
        monkeypatch.setattr(passwd, 'LMNUser', FakeUser)

        result = runner.invoke(passwd.app, ['-r', 'johndoe'])

        assert result.exit_code == 0
        assert 'New random password for johndoe: GeneRat3dPw!' in result.output

    def test_dash_b_is_reset_first_password(self, runner, monkeypatch):
        monkeypatch.setattr(passwd, 'LMNUser', FakeUser)

        result = runner.invoke(passwd.app, ['-b', 'johndoe'])

        assert result.exit_code == 0
        assert 'reset back to the stored first password' in result.output

    def test_dash_c_is_check_first_password(self, runner, monkeypatch):
        monkeypatch.setattr(passwd, 'LMNUser', FakeUser)

        result = runner.invoke(passwd.app, ['-c', 'johndoe'])

        assert result.exit_code == 0
        assert 'is still the current one' in result.output

    def test_dash_s_forwards_school(self, runner, monkeypatch):
        seen = {}

        def make(cn, school='default-school'):
            seen['school'] = school
            return FakeUser(cn, school)

        monkeypatch.setattr(passwd, 'LMNUser', make)

        runner.invoke(passwd.app, ['-b', '-s', 'other-school', 'johndoe'])

        assert seen['school'] == 'other-school'
