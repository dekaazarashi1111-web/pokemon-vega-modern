"""The Stage81 adapter must add validation, never weaken historical contracts."""
from contextlib import contextmanager
from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('stage81_adapter', ROOT / 'scripts/run_modernization_stage81_github_domain.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


@contextmanager
def changed(relative, data):
    path = a.safe_path(relative)
    old = path.read_bytes()
    try:
        path.write_bytes(data)
        yield
    finally:
        path.write_bytes(old)


class AdapterContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        a.prepare()
        cls.config = a.derived_config()
        cls.plan = a.load_engine().build_plan(Path(a.CONFIG))

    def test_real_plan_has_exact_stage81_and_seven_domains(self):
        self.assertEqual(self.plan['input']['stage'], 81)
        self.assertEqual(self.plan['input']['rom']['sha256'], a.SHA)
        self.assertEqual(len(self.plan['domain_order']), 7)
        self.assertEqual(self.plan['input']['parent']['stage'], 80)
        self.assertEqual(self.plan['input']['parent']['parent']['stage'], 78)
        self.assertEqual(self.plan['input']['changed_bytes_from_parent'], 20)

    def test_parent_contracts_are_unchanged(self):
        cfg = deepcopy(self.config)
        del cfg['stage81_native_pp']
        import json
        parent = json.loads(a.raw(a.BASE))
        cfg['execution']['state_root'] = parent['execution']['state_root']
        self.assertEqual(a.stable(cfg), a.stable(parent))

    def test_plan_is_read_only(self):
        paths = (a.CONFIG, a.ROM, a.REPORT, a.GATE, a.BASE)
        before = {p: a.identity(p) for p in paths}
        a.load_engine().build_plan(Path(a.CONFIG))
        self.assertEqual(before, {p: a.identity(p) for p in paths})

    def test_plan_is_deterministic(self):
        self.assertEqual(self.plan, a.load_engine().build_plan(Path(a.CONFIG)))

    def test_old_stage80_cache_is_not_reused(self):
        engine = a.load_engine()
        old = a.load(a.ENGINE).build_plan(Path(a.BASE))
        self.assertNotEqual(old['plan_fingerprint'], self.plan['plan_fingerprint'])
        import json
        paths = list((ROOT / 'content/modernization/stage79_evidence/34314414289').rglob('result.json'))
        self.assertEqual(len(paths), 7)
        for path in paths:
            record = json.loads(path.read_bytes())
            domain = next(d for d in self.config['domains'] if d['id'] == record['id'])
            with self.subTest(domain=record['id']), self.assertRaises(RuntimeError):
                engine._validate_result_record(domain, record, self.plan['plan_fingerprint'],
                                               self.plan['input']['rom'], a.SHA)

    def test_wrong_child_byte_rejected(self):
        data = bytearray(a.raw(a.ROM)); data[100] ^= 1
        with changed(a.ROM, data), self.assertRaisesRegex(RuntimeError, 'candidate identity'):
            a.load_engine().build_plan(Path(a.CONFIG))

    def test_wrong_child_report_rejected(self):
        with changed(a.REPORT, a.raw(a.REPORT) + b' '), self.assertRaisesRegex(RuntimeError, 'report identity'):
            a.load_engine().build_plan(Path(a.CONFIG))

    def test_original_stage80_repair_validation_still_runs(self):
        with self.assertRaises((RuntimeError, ValueError)):
            a.load_engine()._validate_runtime_candidate(self.config, b'not the Stage78 parent', {})

    def test_duplicate_config_json_rejected(self):
        data = a.raw(a.CONFIG).replace(b'{', b'{"schema_version":1,', 1)
        with changed(a.CONFIG, data), self.assertRaises(RuntimeError):
            a.load_engine()

    def test_different_config_rejected(self):
        self.assertEqual(a.main(['plan', '--config', a.BASE]), 1)

    def test_unknown_command_rejected(self):
        self.assertEqual(a.main(['skip']), 1)

    def test_gate_restored_after_exception(self):
        before = a.raw(a.GATE)
        with self.assertRaisesRegex(RuntimeError, 'simulated'):
            with a.preserve_historical_gate():
                a.safe_path(a.GATE).write_bytes(b'new temporary gate')
                raise RuntimeError('simulated merge failure')
        self.assertEqual(before, a.raw(a.GATE))

    def test_gate_restored_after_success(self):
        before = a.raw(a.GATE)
        with a.preserve_historical_gate():
            a.safe_path(a.GATE).write_bytes(b'new temporary gate')
        self.assertEqual(before, a.raw(a.GATE))

    def test_failed_prepare_removes_stale_config(self):
        try:
            recipe = mock.Mock()
            recipe.PARENT_PATH = 'build/stages/80_modernization_runtime_boundary_repair.gba'
            recipe.build.side_effect = RuntimeError('build failed')
            with mock.patch.object(a, 'load', return_value=recipe), self.assertRaises(RuntimeError):
                a.prepare()
            self.assertFalse(a.safe_path(a.CONFIG).exists())
        finally:
            a.prepare()

    def test_symlink_parent_rejected(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(a, 'ROOT', Path(directory)):
            (Path(directory) / 'link').symlink_to(ROOT, target_is_directory=True)
            with self.assertRaises(RuntimeError):
                a.safe_path('link/config/active_play_baseline.json')

    def test_escape_path_rejected(self):
        for path in ('../out', '/tmp/out'):
            with self.subTest(path=path), self.assertRaises(RuntimeError):
                a.safe_path(path)

    def test_no_full_acceptance_or_release_claim(self):
        row = self.config['stage81_native_pp']
        self.assertIs(row['full_p03_acceptance'], False)
        self.assertIs(row['release_ready'], False)


def config_mutation(name, mutate):
    def test(self):
        cfg = deepcopy(self.config)
        mutate(cfg)
        with changed(a.CONFIG, a.stable(cfg)), self.assertRaises(RuntimeError):
            a.load_engine()
    setattr(AdapterContracts, 'test_config_rejects_' + name, test)


for name, mutate in {
    'missing_domain': lambda c: c['domains'].pop(),
    'skipped_domain': lambda c: c['domains'][0].update(state='PENDING'),
    'timeout_change': lambda c: c['domains'][0].update(timeout_seconds=1),
    'runner_change': lambda c: c['domains'][0]['runner'].update(sha256='0' * 64),
    'compiler_change': lambda c: c['domains'][0]['compile'].update(flags=[]),
    'child_hash_change': lambda c: c['stage81_native_pp']['rom'].update(sha256='0' * 64),
    'release_promotion': lambda c: c['stage81_native_pp'].update(release_ready=True),
    'boolean_stage': lambda c: c.update(stage=True),
    'unknown_field': lambda c: c.update(skip_failures=True),
    'old_state_directory': lambda c: c['execution'].update(state_root='.local/modernization_stage79_cumulative_mgba'),
}.items():
    config_mutation(name, mutate)

for index, path in enumerate(a.PINS):
    def pin_test(self, path=path):
        original = a.identity
        def identity(relative):
            result = original(relative)
            return {**result, 'sha256': '0' * 64} if relative == path else result
        with mock.patch.object(a, 'identity', side_effect=identity), self.assertRaises(RuntimeError):
            a.derived_config()
    setattr(AdapterContracts, f'test_historical_source_pin_{index}', pin_test)


if __name__ == '__main__':
    unittest.main()
