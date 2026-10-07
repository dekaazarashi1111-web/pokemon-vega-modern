import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_hof_jp_consumer_receipt as r

class Receipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cp=json.loads((ROOT/r.CP).read_bytes());cls.raw=(ROOT/r.EVIDENCE/'measurement.json').read_bytes();cls.tests=(ROOT/r.EVIDENCE/'probe-tests.json').read_bytes()
    def reject(self,change):
        cp=copy.deepcopy(self.cp);change(cp)
        with self.assertRaises((ValueError,KeyError,TypeError)):r.validate(cp,self.raw,self.tests)
    def test_saved_original(self):self.assertEqual(r.validate(self.cp,self.raw,self.tests)['newly_classified'],0)
    def test_source(self):self.reject(lambda x:x.update(source_head='f'*40))
    def test_run(self):self.reject(lambda x:x.update(run_id=1))
    def test_attempt(self):self.reject(lambda x:x.update(run_attempt=2))
    def test_in_progress(self):self.reject(lambda x:x['job'].update(status='in_progress'))
    def test_missing_step(self):self.reject(lambda x:x['job']['steps'].pop())
    def test_failed_upload(self):self.reject(lambda x:x['job']['steps'][6].update(conclusion='failure'))
    def test_artifact(self):self.reject(lambda x:x['artifact'].update(id=1))
    def test_artifact_digest(self):self.reject(lambda x:x['artifact'].update(digest='sha256:'+'0'*64))
    def test_output_directory(self):self.reject(lambda x:x.update(measurement_path='measurement.json'))
    def test_classification(self):self.reject(lambda x:x.update(newly_classified=2))
    def test_native(self):self.reject(lambda x:x.update(native_processes=1))
    def test_lexical_is_not_runtime(self):self.reject(lambda x:x.update(serializer_execution_proven=True))
    def test_api_arguments(self):self.reject(lambda x:x.update(all_api_arguments_proven=True))
    def test_english_extent(self):self.reject(lambda x:x.update(lexical_eos_extents=[48,42,75,62]))
    def test_altered_measurement(self):
        with self.assertRaises(ValueError):r.validate(self.cp,self.raw+b' ',self.tests)
    def test_altered_tests(self):
        with self.assertRaises(ValueError):r.validate(self.cp,self.raw,self.tests.replace(b'59',b'60'))
if __name__=='__main__':unittest.main()
