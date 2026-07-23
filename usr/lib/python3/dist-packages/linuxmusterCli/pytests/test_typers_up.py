from linuxmusterCli.typers import up
from linuxmusterCli.typers.state import state


SAMPLE_RESULTS = {
    '10.0.0.1': 'Off',
    '10.0.0.2': 'OS Linux',
}


class FakeUPChecker:
    """Stand-in for linuxmusterTools.devices.UPChecker, tracked per instance."""

    instances = []

    def __init__(self, school='default-school'):
        self.school = school
        self.check_args = None
        FakeUPChecker.instances.append(self)

    def check(self, **kwargs):
        self.check_args = kwargs
        return dict(SAMPLE_RESULTS)


class TestCheckOnline:

    def setup_method(self):
        FakeUPChecker.instances = []

    def test_golden_path_table_shows_ip_and_status(self, runner, monkeypatch):
        monkeypatch.setattr(up, 'UPChecker', FakeUPChecker)

        result = runner.invoke(up.app, [])

        assert result.exit_code == 0
        assert '10.0.0.1' in result.output
        assert 'Off' in result.output
        assert '10.0.0.2' in result.output
        assert '2 device(s)' in result.output

    def test_raw_format_prints_tab_separated_rows(self, runner, monkeypatch):
        monkeypatch.setattr(up, 'UPChecker', FakeUPChecker)
        state.format = True
        state.raw = True

        result = runner.invoke(up.app, [])

        assert result.exit_code == 0
        assert '10.0.0.1\tOff' in result.output
        assert '10.0.0.2\tOS Linux' in result.output

    def test_group_argument_is_wrapped_in_a_list(self, runner, monkeypatch):
        monkeypatch.setattr(up, 'UPChecker', FakeUPChecker)

        result = runner.invoke(up.app, ['robotics'])

        assert result.exit_code == 0
        assert FakeUPChecker.instances[0].check_args == {'groups': ['robotics']}

    def test_no_group_calls_check_without_arguments(self, runner, monkeypatch):
        monkeypatch.setattr(up, 'UPChecker', FakeUPChecker)

        result = runner.invoke(up.app, [])

        assert result.exit_code == 0
        assert FakeUPChecker.instances[0].check_args == {}

    def test_school_option_is_forwarded(self, runner, monkeypatch):
        monkeypatch.setattr(up, 'UPChecker', FakeUPChecker)

        runner.invoke(up.app, ['--school', 'other-school'])

        assert FakeUPChecker.instances[0].school == 'other-school'
