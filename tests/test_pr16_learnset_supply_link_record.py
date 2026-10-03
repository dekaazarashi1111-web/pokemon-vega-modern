"""保存供給リンクの昇格・入力改作・hook破損を拒否する新規試験。"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('supply_link_record', ROOT / 'scripts/pr16_learnset_supply_link_record.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class SupplyLinkRecordTests(unittest.TestCase):
    def setUp(self):
        self.config = m.inputs()
        self.files = {n: (ROOT / m.EVIDENCE / n).read_bytes() for n in self.config['proof_files']}

    def replace(self, name, edit):
        value = json.loads(self.files[name])
        edit(value)
        self.files[name] = m.encode(value)
        if name != 'verification.json':
            v = json.loads(self.files['verification.json'])
            v['proof_files'][name] = m.identity(self.files[name])
            self.files['verification.json'] = m.encode(v)
        self.config['proof_files'] = {n: m.identity(raw) for n, raw in self.files.items()}

    def reject(self):
        with self.assertRaises(ValueError):
            m.validate(self.files, self.config)

    def test_saved_success_is_rom_link_only(self):
        self.assertEqual(m.validate(self.files, self.config)['new_native_processes'], 0)

    def test_missing_evidence(self):
        del self.files['inherited-unit.json']
        self.reject()

    def test_changed_evidence_hash(self):
        self.files['unit.txt'] += b'\n'
        self.reject()

    def test_gameplay_promotion(self):
        self.replace('verification.json', lambda v: v.update(gameplay_e2e_accepted=True))
        self.reject()

    def test_scope_promotion(self):
        self.replace('verification.json', lambda v: v.update(scope='GAMEPLAY_ACCEPTED'))
        self.reject()

    def test_duplicate_old_native(self):
        self.replace('verification.json', lambda v: v.update(accepted_native_reruns=1))
        self.reject()

    def test_boolean_is_not_count(self):
        self.replace('verification.json', lambda v: v.update(new_native_processes=False))
        self.reject()

    def test_failure_not_rewritten(self):
        self.replace('verification.json', lambda v: v['failed_predecessor'].update(conclusion='success'))
        self.reject()

    def test_candidate_not_substituted(self):
        self.replace('verification.json', lambda v: v['candidate'].update(sha256='0'*64))
        self.reject()

    def test_inherited_source_not_substituted(self):
        self.replace('inherited-unit.json', lambda v: v.update(source_head='0'*40))
        self.reject()

    def test_hook_set_not_extended(self):
        self.replace('link.json', lambda v: v['hooks'].append(copy.deepcopy(v['hooks'][0])))
        self.reject()

    def test_hook_target_outside_module(self):
        self.replace('link.json', lambda v: v['hooks'][0].update(target=0x08000001))
        self.reject()

    def test_special_tutor_not_flattened(self):
        self.replace('link.json', lambda v: v.update(special_tutor_ids=list(range(9))))
        self.reject()

    def test_parent_plc2_is_protected(self):
        self.replace('link.json', lambda v: v.update(parent_compact_segments_unchanged=False))
        self.reject()

    def test_link_not_native_acceptance(self):
        self.replace('link.json', lambda v: v.update(physical_supply_verified=True))
        self.reject()


if __name__ == '__main__':
    unittest.main()
