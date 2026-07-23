from linuxmusterCli.typers import linbo
from linuxmusterCli.typers.state import state


class FakeLMNFile:
    """Stand-in for linuxmusterTools.lmnfile.LMNFile, tracks the path it was opened with."""

    seen_path = None
    devices = []

    def __init__(self, path, mode):
        FakeLMNFile.seen_path = path

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return FakeLMNFile.devices


class FakeBase:
    def __init__(self, size):
        self.size = size


class FakeDiffImage:
    def __init__(self, size):
        self.size = size


class FakeGroupImage:
    def __init__(self, base_size, backups=None, diff_image=None):
        self.base = FakeBase(base_size)
        self.backups = backups or {}
        self.diff_image = diff_image


class FakeLinboImageManager:
    """Stand-in for linuxmusterTools.linbo.LinboImageManager.

    Tests set the class attribute directly (FakeLinboImageManager.groups = {...})
    before invoking, and the instance created inside images() picks it up.
    """

    groups = {}


class TestGroups:

    def test_counts_devices_per_group_and_excludes_non_matching_files(self, runner, monkeypatch, tmp_path):
        FakeLMNFile.devices = [
            {'group': 'win10'}, {'group': 'win10'}, {'group': 'win11'}, {'group': 'other'},
        ]
        monkeypatch.setattr(linbo, 'LMNFile', FakeLMNFile)
        monkeypatch.setattr(linbo, 'LINBO_PATH', str(tmp_path))

        (tmp_path / 'start.conf.win10').write_text('')
        (tmp_path / 'start.conf.win11').write_text('')
        (tmp_path / 'start.conf.decoy.vdi').write_text('')  # excluded: ends with .vdi
        (tmp_path / 'start.conf.dir').mkdir()  # excluded: not a file
        (tmp_path / 'start.conf.win10_target').write_text('')
        (tmp_path / 'start.conf.linked').symlink_to(tmp_path / 'start.conf.win10_target')  # excluded: symlink
        (tmp_path / 'readme.txt').write_text('')  # excluded: wrong prefix

        result = runner.invoke(linbo.app, ['groups'])

        assert result.exit_code == 0
        assert 'win10' in result.output
        assert '2' in result.output
        assert 'win11' in result.output
        assert '1' in result.output

    def test_school_option_changes_devices_csv_path(self, runner, monkeypatch, tmp_path):
        FakeLMNFile.devices = []
        monkeypatch.setattr(linbo, 'LMNFile', FakeLMNFile)
        monkeypatch.setattr(linbo, 'LINBO_PATH', str(tmp_path))

        result = runner.invoke(linbo.app, ['groups', '--school', 'other-school'])

        assert result.exit_code == 0
        assert FakeLMNFile.seen_path == '/etc/linuxmuster/sophomorix/other-school/other-school.devices.csv'

    def test_default_school_devices_csv_path_has_no_prefix(self, runner, monkeypatch, tmp_path):
        FakeLMNFile.devices = []
        monkeypatch.setattr(linbo, 'LMNFile', FakeLMNFile)
        monkeypatch.setattr(linbo, 'LINBO_PATH', str(tmp_path))

        result = runner.invoke(linbo.app, ['groups'])

        assert result.exit_code == 0
        assert FakeLMNFile.seen_path == '/etc/linuxmuster/sophomorix/default-school/devices.csv'


class TestImages:

    def test_size_is_rounded_to_mib(self, runner, monkeypatch):
        size_bytes = 15 * 1024 * 1024 + 500000  # rounds to 15 MiB
        FakeLinboImageManager.groups = {
            'win10': FakeGroupImage(size_bytes),
        }
        monkeypatch.setattr(linbo, 'LinboImageManager', FakeLinboImageManager)

        result = runner.invoke(linbo.app, ['images'])

        assert result.exit_code == 0
        assert 'win10' in result.output
        assert '15' in result.output

    def test_no_diff_image_shows_no(self, runner, monkeypatch):
        FakeLinboImageManager.groups = {
            'win10': FakeGroupImage(1024 * 1024, diff_image=None),
        }
        monkeypatch.setattr(linbo, 'LinboImageManager', FakeLinboImageManager)

        result = runner.invoke(linbo.app, ['images'])

        assert result.exit_code == 0
        assert 'No' in result.output
        assert 'Yes' not in result.output

    def test_diff_image_shows_yes_with_rounded_size(self, runner, monkeypatch):
        FakeLinboImageManager.groups = {
            'win11': FakeGroupImage(1024 * 1024, diff_image=FakeDiffImage(3 * 1024 * 1024)),
        }
        monkeypatch.setattr(linbo, 'LinboImageManager', FakeLinboImageManager)

        result = runner.invoke(linbo.app, ['images'])

        assert result.exit_code == 0
        assert 'Yes' in result.output
        assert '3' in result.output

    def test_backups_keys_are_listed(self, runner, monkeypatch):
        FakeLinboImageManager.groups = {
            'win10': FakeGroupImage(1024 * 1024, backups={'2024-01-01': 1, '2024-02-01': 1}),
        }
        monkeypatch.setattr(linbo, 'LinboImageManager', FakeLinboImageManager)

        result = runner.invoke(linbo.app, ['images'])

        assert result.exit_code == 0
        assert '2024-01-01' in result.output
        assert '2024-02-01' in result.output


class TestLastsync:

    def _devices(self):
        return {
            'win10': {
                'hosts': [
                    {
                        'hostname': 'pc01', 'ip': '10.0.0.1',
                        'images': ['win10.image'],
                        'sync': {'win10.image': {'date': 1700000000, 'status': 'success'}},
                    },
                    {
                        'hostname': 'pc02', 'ip': '10.0.0.2',
                        'images': ['win10.image'],
                        'sync': {'win10.image': {'date': 'Never', 'status': 'success'}},
                    },
                ]
            },
            'empty-group': {'hosts': []},
            'no-images-group': {'hosts': [{'hostname': 'pc99', 'ip': '10.0.0.9', 'images': [], 'sync': {}}]},
        }

    def test_groups_with_no_hosts_or_no_images_are_skipped(self, runner, monkeypatch):
        devices = self._devices()
        monkeypatch.setattr(linbo, 'list_workstations', lambda **kw: devices)
        monkeypatch.setattr(linbo, 'last_sync_all', lambda devices: None)

        result = runner.invoke(linbo.app, ['lastsync'])

        assert result.exit_code == 0
        assert 'pc01' in result.output
        assert 'pc99' not in result.output

    def test_never_synced_shows_no_date_found(self, runner, monkeypatch):
        devices = self._devices()
        monkeypatch.setattr(linbo, 'list_workstations', lambda **kw: devices)
        monkeypatch.setattr(linbo, 'last_sync_all', lambda devices: None)

        result = runner.invoke(linbo.app, ['lastsync'])

        assert result.exit_code == 0
        assert 'No date found' in result.output

    def test_real_epoch_is_formatted_as_date(self, runner, monkeypatch):
        devices = self._devices()
        monkeypatch.setattr(linbo, 'list_workstations', lambda **kw: devices)
        monkeypatch.setattr(linbo, 'last_sync_all', lambda devices: None)

        result = runner.invoke(linbo.app, ['lastsync'])

        assert result.exit_code == 0
        assert '2023' in result.output

    def test_group_argument_is_forwarded_as_a_filter_list(self, runner, monkeypatch):
        seen = {}

        def fake_list_workstations(groups=None):
            seen['groups'] = groups
            return self._devices()

        monkeypatch.setattr(linbo, 'list_workstations', fake_list_workstations)
        monkeypatch.setattr(linbo, 'last_sync_all', lambda devices: None)

        runner.invoke(linbo.app, ['lastsync', 'win10'])

        assert seen['groups'] == ['win10']

    def test_no_group_argument_calls_list_workstations_without_filter(self, runner, monkeypatch):
        seen = {}

        def fake_list_workstations(**kwargs):
            seen['kwargs'] = kwargs
            return self._devices()

        monkeypatch.setattr(linbo, 'list_workstations', fake_list_workstations)
        monkeypatch.setattr(linbo, 'last_sync_all', lambda devices: None)

        runner.invoke(linbo.app, ['lastsync'])

        assert seen['kwargs'] == {}

    def test_school_option_is_accepted_but_not_forwarded_anywhere(self, runner, monkeypatch):
        # Documents current (buggy?) behavior: --school is a declared option on
        # lastsync but the function body never references it, so it has no
        # effect on the list_workstations() call or anything else.
        seen = {}

        def fake_list_workstations(**kwargs):
            seen['kwargs'] = kwargs
            return self._devices()

        monkeypatch.setattr(linbo, 'list_workstations', fake_list_workstations)
        monkeypatch.setattr(linbo, 'last_sync_all', lambda devices: None)

        result = runner.invoke(linbo.app, ['lastsync', 'win10', '--school', 'other-school'])

        assert result.exit_code == 0
        assert seen['kwargs'] == {'groups': ['win10']}

    def test_raw_format_prints_unformatted_sync_dict(self, runner, monkeypatch):
        devices = self._devices()
        monkeypatch.setattr(linbo, 'list_workstations', lambda **kw: devices)
        monkeypatch.setattr(linbo, 'last_sync_all', lambda devices: None)
        state.format = True
        state.raw = True

        result = runner.invoke(linbo.app, ['lastsync'])

        assert result.exit_code == 0
        # Raw output uses the unformatted sync dict, not the colored/rendered string.
        assert "{'date': 1700000000, 'status': 'success'}" in result.output
        assert 'No date found' not in result.output
