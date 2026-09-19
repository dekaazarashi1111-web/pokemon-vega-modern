"""Stage83 candidate boundary preserves all historical domain validation."""
from contextlib import contextmanager
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('stage83_adapter',ROOT/'scripts/run_modernization_stage83_github_domain.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
@contextmanager
def changed(name,data):
    p=a.safe(name);old=p.read_bytes()
    try:p.write_bytes(data);yield
    finally:p.write_bytes(old)
class AdapterContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        a.prepare();cls.config=a.derived_config();cls.plan=a.load_engine().build_plan(Path(a.CONFIG))
    def test_exact_candidate(self):
        self.assertEqual(self.plan['input']['stage'],83)
        self.assertEqual(self.plan['input']['rom']['sha256'],a.SHA)
        self.assertEqual(self.plan['input']['changed_bytes_from_parent'],3)
        self.assertEqual(self.plan['input']['adopted_species_count'],2)
        self.assertEqual(self.plan['input']['parent']['stage'],82)
        self.assertEqual(len(self.plan['domain_order']),7)
    def test_historical_contracts_unchanged(self):
        c=deepcopy(self.config);del c['stage83_decided_species'];parent=json.loads(a.raw(a.BASE))
        c['execution']['state_root']=parent['execution']['state_root'];self.assertEqual(c,parent)
    def test_plan_read_only_and_deterministic(self):
        names=[a.CONFIG,a.ROM,a.REPORT,a.GATE,a.BASE]
        before={p:a.identity(p) for p in names}
        self.assertEqual(self.plan,a.load_engine().build_plan(Path(a.CONFIG)))
        self.assertEqual(before,{p:a.identity(p) for p in names})
    def test_parent_cache_cannot_be_reused(self):
        engine=a.load_engine()
        records=list((ROOT/'content/modernization/stage79_evidence/34314414289').rglob('result.json'))
        self.assertEqual(len(records),7)
        for p in records:
            row=json.loads(p.read_bytes());d=next(d for d in self.config['domains'] if d['id']==row['id'])
            with self.subTest(domain=d['id']),self.assertRaises(RuntimeError):
                engine._validate_result_record(d,row,self.plan['plan_fingerprint'],self.plan['input']['rom'],a.SHA)
    def test_wrong_rom_byte(self):
        data=bytearray(a.raw(a.ROM));data[100]^=1
        with changed(a.ROM,data),self.assertRaises(RuntimeError):a.load_engine().build_plan(Path(a.CONFIG))
    def test_wrong_report(self):
        with changed(a.REPORT,a.raw(a.REPORT)+b' '),self.assertRaises(RuntimeError):a.load_engine().build_plan(Path(a.CONFIG))
    def test_config_cannot_skip_domain(self):
        c=deepcopy(self.config);c['domains'].pop()
        with changed(a.CONFIG,a.stable(c)),self.assertRaises(RuntimeError):a.load_engine()
    def test_config_duplicate_key(self):
        with changed(a.CONFIG,a.raw(a.CONFIG).replace(b'{',b'{"schema_version":1,',1)),self.assertRaises(RuntimeError):a.load_engine()
    def test_original_parent_validator_runs(self):
        with self.assertRaises((ValueError,RuntimeError)):a.load_engine()._validate_runtime_candidate(self.config,b'not Stage78',{})
    def test_adoption_source_change_rejected(self):
        p=next(iter(a.delta.specification()['sources'].values()))['path']
        with changed(p,a.raw(p)+b'\n'),self.assertRaises(ValueError):a.derived_config()
    def test_gate_preserved_after_exception(self):
        b=a.raw(a.GATE);mtime=a.safe(a.GATE).stat().st_mtime_ns
        with self.assertRaises(RuntimeError):
            with a.preserve_gate():a.safe(a.GATE).write_bytes(b'bad');raise RuntimeError('simulated')
        self.assertEqual(b,a.raw(a.GATE));self.assertEqual(mtime,a.safe(a.GATE).stat().st_mtime_ns)
    def test_failed_prepare_removes_stale_pass_inputs(self):
        try:
            with mock.patch.object(a,'rebuild',side_effect=ValueError('failure')),self.assertRaises(ValueError):a.prepare()
            self.assertFalse(a.safe(a.CONFIG).exists());self.assertFalse(a.safe(a.ROM).exists())
        finally:a.prepare()
    def test_no_full_stage_acceptance(self):
        self.assertIs(self.config['stage83_decided_species']['full_p06_acceptance'],False)
        self.assertIs(self.config['stage83_decided_species']['release_ready'],False)
    def test_no_arbitrary_config_or_mode(self):
        self.assertEqual(a.main(['plan','--config',a.BASE]),1);self.assertEqual(a.main(['skip']),1)
if __name__=='__main__':unittest.main()
