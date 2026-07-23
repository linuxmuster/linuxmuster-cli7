from linuxmusterCli.typers import check_parents


class TestCheck:

    def test_is_currently_a_no_op(self, runner):
        # check_parents.check() body is `pass` — all real logic is commented
        # out below it (dead code referencing a non-existent LMNUser writer
        # method). This documents the current no-op behavior, not a fix.
        result = runner.invoke(check_parents.app, [])

        assert result.exit_code == 0
        assert result.output == ''

    def test_school_option_is_accepted_but_has_no_effect(self, runner):
        result = runner.invoke(check_parents.app, ['--school', 'other-school'])

        assert result.exit_code == 0
        assert result.output == ''
