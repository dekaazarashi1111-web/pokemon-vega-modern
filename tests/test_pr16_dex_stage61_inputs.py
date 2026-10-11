"""New recovered-metadata verification only; no compiler, emulator or input edits."""
import copy,json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_stage61_inputs as m
class Inputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(os.environ['VEGA_STAGE61_METADATA_DIR']);cls.metadata=(p/'61_critical_release_candidate_original.json').read_bytes();cls.symbols=(p/'stage61_critical_release_candidate_symbols.json').read_bytes();cls.rom=Path(os.environ['VEGA_DEX_ROM_PATH']).read_bytes();cls.proof=json.loads((ROOT/m.PROOF).read_bytes())
    def check(self,p=None,metadata=None,symbols=None,rom=None):return m.validate(self.proof if p is None else p,self.metadata if metadata is None else metadata,self.symbols if symbols is None else symbols,self.rom if rom is None else rom)
    def reject(self,change):
        p=copy.deepcopy(self.proof);change(p)
        with self.assertRaises(ValueError):self.check(p)
    def test_exact_original_metadata(self):self.assertEqual(self.check()['sized_symbols'],99)
    def test_macro_drift_rejected(self):self.reject(lambda p:p['runtime_macros'].__setitem__('STAGE61_KANTO_NAME_TABLE',0))
    def test_missing_macro_rejected(self):self.reject(lambda p:p['runtime_macros'].pop('STAGE61_KANTO_NAME_TABLE'))
    def test_symbol_address_drift_rejected(self):self.reject(lambda p:p['symbols'][0].__setitem__('address',0))
    def test_symbol_size_drift_rejected(self):self.reject(lambda p:p['symbols'][0].__setitem__('size',8))
    def test_symbol_preimage_drift_rejected(self):self.reject(lambda p:p['symbols'][0].__setitem__('preimage_sha256','0'*64))
    def test_lost_unsized_alias_rejected(self):self.reject(lambda p:p['unsized_aliases'].pop())
    def test_invented_alias_size_rejected(self):self.reject(lambda p:p['unsized_aliases'][0].__setitem__('size',8))
    def test_toolchain_drift_rejected(self):self.reject(lambda p:p.__setitem__('toolchain_manifest_sha256','0'*64))
    def test_metadata_change_rejected(self):
        with self.assertRaises(ValueError):self.check(metadata=self.metadata+b' ')
    def test_symbol_member_change_rejected(self):
        with self.assertRaises(ValueError):self.check(symbols=self.symbols+b' ')
    def test_wrong_rom_rejected(self):
        with self.assertRaises(ValueError):self.check(rom=self.rom[:-1])
if __name__=='__main__':unittest.main()
