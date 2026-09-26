"""loader tail64保護と、原本由来の自動2/通常1 Saveを厳密に区別する。"""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=load('coldboot','scripts/pr16_circus_coldboot.py')
p=load('coldprobe',m.PROBE)
legacy=load('legacy_tests','tests/test_pr16_circus_interruption.py')

def fixture():
    rows,result=legacy.fixture()
    for row in rows[8:]:row['save_counter']+=2
    result['save_counter_after']=5;result['automatic_recovery_saves']=2
    return rows,result

def validate(rows,result):return p.validate(json.dumps(result).encode(),legacy.stderr(rows),0,p.CASE)

class ColdBootTests(unittest.TestCase):
    def test_actual_c_bridge_512_corruptions_256_returns_and_lifecycle(self):
        with tempfile.TemporaryDirectory() as folder:
            exe=Path(folder)/'test'
            args=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-DCIRCUS_COLD_LOAD_HOST_TEST',str(ROOT/m.FIXTURE),str(ROOT/m.SOURCE),str(ROOT/m.OWNER),str(ROOT/'overlays/circus_streak/circus_streak_io.c'),'-o',str(exe)]
            subprocess.run(args,check=True,capture_output=True)
            result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            self.assertIn('single_bit_corruptions=512 delegate_results=256',result.stdout)
    def test_legacy_autosave_two_phase_source(self):
        text=(ROOT/m.AUTOSAVE_SOURCE).read_text()
        self.assertEqual(m.autosave_contract(text)['automatic_recovery_saves'],2)
        for changed in (text.replace('if (!persist_current())','if (1)'),text.replace('VEGA_FACTORY_RESTORE_PENDING','VEGA_FACTORY_OUTSIDE')):
            with self.assertRaises(ValueError):m.autosave_contract(changed)
    def test_new_probe_only_changes_explicit_save_accounting(self):
        old=(ROOT/'scripts/pr16_circus_interruption_probe.py').read_text()
        expected=old.replace('第2戦中断: CRC64・実1勝・破棄→復旧・保存後3coreを原本から検証。','Cold boot修復: 自動復旧Save2回/通常Save1回/CRC64/未完戦非加算を検証。')
        expected=expected.replace("(3 if e['label'] in ('saved','reloaded') else 2)","(5 if e['label'] in ('saved','reloaded') else 4 if e['label']=='recovered' else 2)")
        expected=expected.replace('normal_saves=1,fresh_cores=3,','normal_saves=1,automatic_recovery_saves=2,fresh_cores=3,')
        expected=expected.replace('save_counter_before=2,save_counter_after=3,manual_saves=1,fresh_cores=3,','save_counter_before=2,save_counter_after=5,manual_saves=1,automatic_recovery_saves=2,fresh_cores=3,')
        self.assertEqual((ROOT/m.PROBE).read_text(),expected)
    def test_synthetic_contract_never_used_as_native_evidence(self):
        rows,result=fixture();self.assertEqual(validate(rows,result),result)
        summary=p.analyze(p.parse(legacy.stderr(rows)),result)
        self.assertEqual((summary['normal_saves'],summary['automatic_recovery_saves'],summary['best_after']),(1,2,1))
    def test_wrong_auto_manual_or_load_saves_rejected(self):
        for i,counter in ((7,4),(8,2),(8,3),(8,5),(9,4),(9,6),(10,7)):
            rows,result=fixture();rows[i]['save_counter']=counter
            with self.assertRaises(ValueError):validate(rows,result)
        for key,value in (('automatic_recovery_saves',0),('automatic_recovery_saves',True),('manual_saves',3),('save_counter_after',3)):
            rows,result=fixture();result[key]=value
            with self.assertRaises(ValueError):validate(rows,result)
    def test_empty_best_or_double_abort_still_rejected(self):
        for changes in ({'best':0},{'best':2},{'current':1},{'generation':7},{'outcome':1},{'session':0}):
            rows,result=fixture()
            for row in rows[8:]:row['owner']=legacy.crc_owner(row['owner'],**changes)
            with self.assertRaises(ValueError):validate(rows,result)
    def test_old_failed_native_not_reclassified(self):
        path=ROOT/'evidence/pr16_circus_interruption/35420622910/circus-interrupt-second-battle.stderr'
        with self.assertRaises(ValueError):p.parse(path.read_bytes())
    def test_controller_only_counter_expectations_change(self):
        old=(ROOT/'tools/mgba_pr16_circus_recovery_trace.c').read_text()
        expected=old.replace('/* 新規の第2戦中断ケース。3勝単体や受入済み敗北を再実行しない。 */','/* Cold boot bridgeの影響検査。既存Factoryの自動復旧Save2回と通常Save1回を区別。 */')
        expected=expected.replace('memcmp(armed,recovered,sizeof(armed)) && read32(c,P03_SAVE_COUNTER)==sc_counter\n','memcmp(armed,recovered,sizeof(armed)) && read32(c,P03_SAVE_COUNTER)==sc_counter+2U\n')
        expected=expected.replace('&& read32(c,P03_SAVE_COUNTER)==sc_counter+1U,','&& read32(c,P03_SAVE_COUNTER)==sc_counter+3U,')
        quote=chr(92)+'"'
        expected=expected.replace(quote+'manual_saves'+quote+':1,',quote+'manual_saves'+quote+':1,'+quote+'automatic_recovery_saves'+quote+':2,')
        self.assertEqual((ROOT/m.CONTROLLER).read_text(),expected)
        active=expected.split('a_guard(c);',1)[1]
        for bad in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'create_mon(', 'loadState('):self.assertNotIn(bad,active)
    def test_runtime_delegate_once_and_only_tail64(self):
        text=(ROOT/m.SOURCE).read_text()
        self.assertEqual(text.count('COLD_DELEGATE(save_type)'),1)
        self.assertEqual(text.count('COLD_READ(31u,CIRCUS_STREAK_SECTOR_OFFSET,&saved,CIRCUS_STREAK_SIZE)'),1)
        self.assertIn('CircusStreakValid(&saved)',text)
        for bad in ('TrySaving','0x03000EB8','0x02023BE4','gVegaModernSaveData','static CircusStreakOwner'):self.assertNotIn(bad,text)
if __name__=='__main__':unittest.main()
