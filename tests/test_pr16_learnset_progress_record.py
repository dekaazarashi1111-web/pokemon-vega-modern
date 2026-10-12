"""New evidence recorder boundaries only. No accepted C/ARM/native re-execution."""
import copy
import io
import json
import os
from pathlib import Path
import unittest
import warnings
import zipfile
from scripts import pr16_learnset_progress_record as r


class ProgressRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = r.inputs()
        folder = Path(os.environ.get('PR16_PROGRESS_PROOF_DIR', r.ROOT/r.EVIDENCE))
        cls.files = {name:(folder/name).read_bytes() for name in cls.config['proof_files']}

    def altered(self, file_name, change):
        files = dict(self.files)
        config = copy.deepcopy(self.config)
        data = json.loads(files[file_name]); change(data); files[file_name] = r.encode(data)
        if file_name != 'verification.json':
            v = json.loads(files['verification.json'])
            v['proof_files'][file_name] = r.identity(files[file_name])
            files['verification.json'] = r.encode(v)
        for name in (file_name, 'verification.json'):
            config['proof_files'][name] = r.identity(files[name])
        return files, config

    def test_completed_evidence_pass(self):
        self.assertEqual(r.validate(self.files,self.config)['native_results'][0]['calls'],111)

    def test_modified_member_rejected(self):
        files=dict(self.files);files['unit.txt']+=b' '
        with self.assertRaises(ValueError):r.validate(files,self.config)

    def test_scope_promotion_rejected(self):
        files,config=self.altered('verification.json',lambda v:v.update(scope='GAMEPLAY_E2E'))
        with self.assertRaises(ValueError):r.validate(files,config)

    def test_unaccepted_flags_rejected(self):
        for key in ('conditional_consumers_connected','gameplay_e2e_accepted','release_ready','issue19_complete'):
            with self.subTest(key=key):
                files,config=self.altered('verification.json',lambda v:v.update({key:True}))
                with self.assertRaises(ValueError):r.validate(files,config)

    def test_source_head_rejected(self):
        files,config=self.altered('verification.json',lambda v:v.update(source_head='0'*40))
        with self.assertRaises(ValueError):r.validate(files,config)

    def test_host_rerun_rejected(self):
        files,config=self.altered('verification.json',lambda v:v.update(host_queries_executed=318186))
        with self.assertRaises(ValueError):r.validate(files,config)

    def test_wrong_legacy_entry_rejected(self):
        files,config=self.altered('link.json',lambda v:v['hooks'][0].update(offset=0x3e174))
        with self.assertRaises(ValueError):r.validate(files,config)

    def test_changed_evolution_dispatch_rejected(self):
        files,config=self.altered('link.json',lambda v:v.update(p03_evolution_dispatch_unchanged=False))
        with self.assertRaises(ValueError):r.validate(files,config)

    def test_prior_failure_not_rewritten(self):
        files,config=self.altered('inherited-host.json',lambda v:v.update(run_conclusion='success'))
        with self.assertRaises(ValueError):r.validate(files,config)

    def test_native_source_mismatch_rejected(self):
        files,config=self.altered('native29.json',lambda v:v.update(candidate_sha256='f'*64))
        with self.assertRaises(ValueError):r.validate(files,config)

    def test_duplicate_zip_rejected(self):
        buffer=io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(buffer,'w') as z:
                for name,raw in self.files.items():z.writestr(name,raw)
                z.writestr('unit.txt',self.files['unit.txt'])
        with self.assertRaises(ValueError):r.unpack(buffer.getvalue(),self.config['proof_files'])

    def test_zip_escape_rejected(self):
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w') as z:
            for name,raw in self.files.items():z.writestr('../unit.txt' if name=='unit.txt' else name,raw)
        with self.assertRaises(ValueError):r.unpack(buffer.getvalue(),self.config['proof_files'])


if __name__=='__main__':unittest.main()
