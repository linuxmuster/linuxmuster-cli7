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
                        'image': [{'image': 'win10.image', 'date': 1700000000, 'status': 'success'}],
                    },
                    {
                        'hostname': 'pc02', 'ip': '10.0.0.2',
                        'image': [{'image': 'win10.image', 'date': 'Never', 'status': 'success'}],
                    },
                ]
            },
            'empty-group': {'hosts': []},
            'no-images-group': {'hosts': [{'hostname': 'pc99', 'ip': '10.0.0.9', 'image': []}]},
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

        def fake_list_workstations(groups=None, **kwargs):
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

        assert 'groups' not in seen['kwargs']
        assert seen['kwargs']['school'] == 'default-school'

    def test_school_option_is_forwarded_to_list_workstations(self, runner, monkeypatch):
        seen = {}

        def fake_list_workstations(**kwargs):
            seen['kwargs'] = kwargs
            return self._devices()

        monkeypatch.setattr(linbo, 'list_workstations', fake_list_workstations)
        monkeypatch.setattr(linbo, 'last_sync_all', lambda devices: None)

        result = runner.invoke(linbo.app, ['lastsync', 'win10', '--school', 'other-school'])

        assert result.exit_code == 0
        assert seen['kwargs'] == {'school': 'other-school', 'groups': ['win10']}

    def test_raw_format_prints_unformatted_sync_dict(self, runner, monkeypatch):
        devices = self._devices()
        monkeypatch.setattr(linbo, 'list_workstations', lambda **kw: devices)
        monkeypatch.setattr(linbo, 'last_sync_all', lambda devices: None)
        state.format = True
        state.raw = True

        result = runner.invoke(linbo.app, ['lastsync'])

        assert result.exit_code == 0
        # Raw output uses the unformatted sync dict, not the colored/rendered string.
        assert "{'image': 'win10.image', 'date': 1700000000, 'status': 'success'}" in result.output
        assert 'No date found' not in result.output

    def test_group_name_is_shown_as_table_title(self, runner, monkeypatch):
        devices = self._devices()
        monkeypatch.setattr(linbo, 'list_workstations', lambda **kw: devices)
        monkeypatch.setattr(linbo, 'last_sync_all', lambda devices: None)

        result = runner.invoke(linbo.app, ['lastsync'])

        assert result.exit_code == 0
        # Only the win10 group is displayed, with its two kept hosts.
        assert 'Group win10 (2 device(s))' in result.output

    def test_group_is_appended_to_exported_rows(self, runner, monkeypatch):
        devices = self._devices()
        monkeypatch.setattr(linbo, 'list_workstations', lambda **kw: devices)
        monkeypatch.setattr(linbo, 'last_sync_all', lambda devices: None)
        state.format = True
        state.raw = True

        result = runner.invoke(linbo.app, ['lastsync'])

        assert result.exit_code == 0
        lines = [line for line in result.output.splitlines() if line.strip()]
        # Exported rows of every group are concatenated, so the group is the
        # last field of the header and of each row.
        assert lines[0].split('\t')[-1] == 'Group'
        assert [line.split('\t')[-1] for line in lines[1:]] == ['win10', 'win10']

    def _devices_with_version(self):
        return {
            'win10': {
                'hosts': [
                    {
                        'hostname': 'pc01', 'ip': '10.0.0.1',
                        'image': [{
                            'image': 'win10.image', 'date': 1700000000,
                            'imageVersion': '202601271107', 'status': 'success',
                        }],
                    },
                    {
                        'hostname': 'pc02', 'ip': '10.0.0.2',
                        'image': [{
                            'image': 'win10.image', 'date': 'Never',
                            'imageVersion': None, 'status': 'danger',
                        }],
                    },
                    {
                        'hostname': 'pc03', 'ip': '10.0.0.3',
                        'image': [{
                            'image': 'win10.image', 'date': 1700000000,
                            'imageVersion': 'not-a-timestamp', 'status': 'success',
                        }],
                    },
                ]
            },
        }

    def test_applied_image_version_is_shown_next_to_the_sync_date(self, runner, monkeypatch):
        devices = self._devices_with_version()
        monkeypatch.setattr(linbo, 'list_workstations', lambda **kw: devices)
        monkeypatch.setattr(linbo, 'last_sync_all', lambda devices: None)

        result = runner.invoke(linbo.app, ['lastsync'])

        assert result.exit_code == 0
        # Rich wraps inside the cell when the terminal is too narrow, so the
        # assertion is on the text, not on its layout.
        assert '(image 2026-01-27 11:07)' in ' '.join(result.output.split())

    def test_applied_image_version_is_exported_as_its_own_field(self, runner, monkeypatch):
        devices = self._devices_with_version()
        monkeypatch.setattr(linbo, 'list_workstations', lambda **kw: devices)
        monkeypatch.setattr(linbo, 'last_sync_all', lambda devices: None)
        state.format = True
        state.raw = True

        result = runner.invoke(linbo.app, ['lastsync'])

        assert result.exit_code == 0
        rows = [line.split('\t') for line in result.output.splitlines() if line.strip()]
        assert rows[0][3] == 'Applied version of win10.image'
        assert rows[1][3] == '2026-01-27 11:07'
        # A host which never synced the image has no version at all.
        assert rows[2][3] == ''
        # An unparsable timestamp is shown as it is rather than dropped.
        assert rows[3][3] == 'not-a-timestamp'

    def _devices_by_status(self):
        return {
            'win10': {
                'hosts': [
                    {
                        'hostname': 'pc-ok', 'ip': '10.0.0.1',
                        'image': [{'image': 'win10.image', 'date': 1700000000, 'status': 'success'}],
                    },
                    {
                        'hostname': 'pc-warn', 'ip': '10.0.0.2',
                        'image': [{'image': 'win10.image', 'date': 1600000000, 'status': 'warning'}],
                    },
                    {
                        'hostname': 'pc-danger', 'ip': '10.0.0.3',
                        'image': [{'image': 'win10.image', 'date': 'Never', 'status': 'danger'}],
                    },
                ]
            },
            'ubuntu': {
                'hosts': [
                    {
                        'hostname': 'pc-ubuntu', 'ip': '10.0.0.4',
                        'image': [{'image': 'ubuntu.image', 'date': 1700000000, 'status': 'success'}],
                    },
                ]
            },
        }

    def _patch_devices(self, monkeypatch):
        devices = self._devices_by_status()
        monkeypatch.setattr(linbo, 'list_workstations', lambda **kw: devices)
        monkeypatch.setattr(linbo, 'last_sync_all', lambda devices: None)

    def test_without_status_filter_all_hosts_are_shown(self, runner, monkeypatch):
        self._patch_devices(monkeypatch)

        result = runner.invoke(linbo.app, ['lastsync'])

        assert result.exit_code == 0
        for hostname in ['pc-ok', 'pc-warn', 'pc-danger', 'pc-ubuntu']:
            assert hostname in result.output

    def test_warning_option_keeps_only_warning_hosts(self, runner, monkeypatch):
        self._patch_devices(monkeypatch)

        result = runner.invoke(linbo.app, ['lastsync', '--warning'])

        assert result.exit_code == 0
        assert 'pc-warn' in result.output
        assert 'pc-ok' not in result.output
        assert 'pc-danger' not in result.output

    def test_danger_option_keeps_only_danger_hosts(self, runner, monkeypatch):
        self._patch_devices(monkeypatch)

        result = runner.invoke(linbo.app, ['lastsync', '-d'])

        assert result.exit_code == 0
        assert 'pc-danger' in result.output
        assert 'pc-ok' not in result.output
        assert 'pc-warn' not in result.output

    def test_both_options_keep_warning_and_danger_hosts(self, runner, monkeypatch):
        self._patch_devices(monkeypatch)

        result = runner.invoke(linbo.app, ['lastsync', '-w', '-d'])

        assert result.exit_code == 0
        assert 'pc-warn' in result.output
        assert 'pc-danger' in result.output
        assert 'pc-ok' not in result.output

    def test_group_without_matching_host_is_skipped(self, runner, monkeypatch):
        self._patch_devices(monkeypatch)

        result = runner.invoke(linbo.app, ['lastsync', '--danger'])

        assert result.exit_code == 0
        # The ubuntu group only holds a successfully synced host, its table is not printed.
        assert 'pc-ubuntu' not in result.output
        assert 'ubuntu.image' not in result.output

    def test_host_matching_on_one_image_keeps_all_its_images(self, runner, monkeypatch):
        devices = {
            'win10': {
                'hosts': [
                    {
                        'hostname': 'pc-mixed', 'ip': '10.0.0.5',
                        'image': [
                            {'image': 'win10.image', 'date': 1700000000, 'status': 'success'},
                            {'image': 'ubuntu.image', 'date': 1600000000, 'status': 'warning'},
                        ],
                    },
                ]
            },
        }
        monkeypatch.setattr(linbo, 'list_workstations', lambda **kw: devices)
        monkeypatch.setattr(linbo, 'last_sync_all', lambda devices: None)

        result = runner.invoke(linbo.app, ['lastsync', '--warning'])

        assert result.exit_code == 0
        assert 'pc-mixed' in result.output
        assert 'win10.image' in result.output
        assert 'ubuntu.image' in result.output
