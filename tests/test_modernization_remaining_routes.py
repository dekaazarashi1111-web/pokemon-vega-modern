"""Fail-closed contracts for remaining native routes; synthetic records are not acceptance."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import run_modernization_remaining_routes as r

PROCESS={'schema_version':1,'returncode':0,'timed_out':False,'spawn_error':None}

def record(c):
    d=r.expected(c)
    w=dict(bag=1,mode=2,party=3,summary=0,selection=0,warning=0,confirm=0,denied=0,deleted=0,field=20)
    if c['action']!=4:w.update(summary=4,selection=5)
    if c['action'] not in (3,4,5) and ((c['bonus']>>(2*c['slot']))&3):w['warning']=6
    if c['action'] in (0,2):w['confirm']=7
    if c['action'] in (4,5):w['denied']=8
    if c['action']==0:w['deleted']=9
    d['witness']=w
    return d

def check(d,c,p=None,stderr=b''):
    return r.validate(json.dumps(d).encode(),c,PROCESS if p is None else p,stderr)

class RemainingRoutesTests(unittest.TestCase):
    def test_twelve_distinct_reviewed_routes(self):
        rows=r.cases()
        self.assertEqual(len(rows),12)
        self.assertEqual(len({c['name'] for c in rows}),12)
        self.assertEqual([c['after_bonus'] for c in rows[:4]],[57,56,52,36])
        self.assertEqual(rows[-1]['after_species'],881)
        self.assertEqual(rows[-1]['after'],[33,45,57,0])
        self.assertEqual(rows[-1]['after_bonus'],6)

    def test_every_reviewed_case_validates(self):
        for c in r.cases():
            with self.subTest(case=c['name']):check(record(c),c)

    def test_all_results_reject_changed_contract(self):
        for c in r.cases():
            for key,value in r.expected(c).items():
                d=record(c)
                d[key]=not value if type(value) is bool else (value+1 if type(value) is int else ([] if type(value) is list else 'wrong'))
                with self.subTest(case=c['name'],key=key),self.assertRaises(ValueError):check(d,c)

    def test_missing_each_required_witness_fails(self):
        for c in r.cases():
            for key,value in record(c)['witness'].items():
                if not value:continue
                d=record(c);d['witness'][key]=0
                with self.subTest(case=c['name'],key=key),self.assertRaises(ValueError):check(d,c)

    def test_invented_witness_fails(self):
        for c in r.cases():
            for key,value in record(c)['witness'].items():
                if value:continue
                d=record(c);d['witness'][key]=8
                with self.subTest(case=c['name'],key=key),self.assertRaises(ValueError):check(d,c)

    def test_exact_types_and_bounds(self):
        c=r.cases()[0]
        for bad in (True,1.0,-1,24000,'1',None):
            d=record(c);d['witness']['bag']=bad
            with self.subTest(bad=bad),self.assertRaises(ValueError):check(d,c)
        for key in ('schema_version','slot','save_counter_delta','species_before'):
            d=record(c);d[key]=bool(d[key])
            with self.subTest(key=key),self.assertRaises(ValueError):check(d,c)

    def test_time_order_rejected(self):
        c=r.cases()[1]
        for early,late in [('bag','mode'),('mode','party'),('party','summary'),('selection','warning'),('warning','confirm'),('confirm','deleted'),('deleted','field')]:
            d=record(c);d['witness'][early]=d['witness'][late]
            with self.subTest(early=early),self.assertRaises(ValueError):check(d,c)

    def test_unknown_missing_keys(self):
        c=r.cases()[0]
        d=record(c);d['extra']=True
        with self.assertRaises(ValueError):check(d,c)
        d=record(c);del d['normal_save_menu']
        with self.assertRaises(ValueError):check(d,c)
        d=record(c);d['witness']['extra']=1
        with self.assertRaises(ValueError):check(d,c)

    def test_process_failure_and_emulator_warning(self):
        c=r.cases()[0]
        for key,bad in [('returncode',1),('returncode',False),('returncode',None),('timed_out',True),('spawn_error','failed')]:
            p=PROCESS.copy();p[key]=bad
            with self.subTest(key=key,bad=bad),self.assertRaises(ValueError):check(record(c),c,p)
        with self.assertRaises(ValueError):check(record(c),c,stderr=b'mGBA[error]')

    def test_duplicate_nonfinite_json_rejected(self):
        c=r.cases()[0]
        for raw in (b'{"status":"PASS","status":"PASS"}',b'{"x":NaN}',b'{"x":Infinity}'):
            with self.assertRaises(ValueError):r.validate(raw,c,PROCESS)

    def test_header_checks_real_rom_labels(self):
        names=('text_pp_up_warning','text_forget_confirm','text_forgot','text_last_move','text_form_rejected')
        labels={n:0x09200000+i*16 for i,n in enumerate(names)}
        text=r.header(r.cases(),labels)
        self.assertIn('R_TEXT_LAST_MOVE',text)
        self.assertIn('keldeo-form-revert',text)
        for bad in (True,'0x09200000',0x02000000,0x0a000000):
            invalid=labels.copy();invalid[names[0]]=bad
            with self.assertRaises(ValueError):r.header(r.cases(),invalid)

    def test_embedded_sources_preserve_content_except_entry_name(self):
        for src,_ in r.EMBED:
            text=(ROOT/src).read_text()
            embedded=r.embed(text,'isolated_old_main')
            self.assertEqual(embedded.replace('int isolated_old_main(', 'int main('),text)
        for invalid in ('void main(void){}','int main(void){}\nint main(){}'):
            with self.assertRaises(ValueError):r.embed(invalid,'old')

    def test_guard_set_and_three_observation_phases(self):
        self.assertEqual(r.GUARDS,('bus8','bus16','bus32','raw8','raw16','raw32','register'))
        text=(ROOT/r.SOURCE).read_text()
        self.assertEqual(text.count('a_guard(c);'),3)
        self.assertIn('a_save(c)',text)
        self.assertIn('a_continue(c)',text)
        self.assertIn('!memcmp(after,loaded,100)',text)
        self.assertIn('!memcmp(before,after,100)',text)

    def test_whole_phase_release_and_acquisition_not_claimed(self):
        for c in r.cases():
            e=r.expected(c)
            for key in ('full_p03_acceptance','full_p05_acceptance','release_ready'):self.assertIs(e[key],False)

    def test_stale_success_removed_before_missing_input(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);out=root/'.local/results';out.mkdir(parents=True)
            (out/'result.json').write_text('{"status":"PASS"}')
            with mock.patch.object(r,'ROOT',root),self.assertRaises(ValueError):r.run(out)
            self.assertFalse((out/'result.json').exists())

    def test_missing_truncated_or_wrong_script_fails_closed(self):
        for rom in (b'',b'\0'*64,b'\0'*0x12D0A80):
            with self.assertRaises(ValueError):r.route_labels.resolve(rom)

    def test_original_rom_seed_not_rewritten_by_runner(self):
        text=(ROOT/r.SELF).read_text()
        self.assertIn('shutil.copyfile(seed,save)',text)
        self.assertIn("identity(rom)==rid and identity(seed)==sid,'ROM/seed modified'",text)
        self.assertNotIn('rom.write_',text)
        self.assertNotIn('seed.write_',text)

class SentinelRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import struct
        raw=bytearray(r.repair.SIZE)
        struct.pack_into('<I',raw,0x1cc,r.repair.TABLE)
        for p in r.repair.LITERALS:struct.pack_into('<I',raw,p,r.repair.TABLE+4)
        raw[r.repair.OFFSET]=35
        cls.fixture=bytes(raw)

    def test_one_sentinel_byte_only(self):
        after=r.repair.patch(self.fixture)
        o=r.repair.OFFSET
        self.assertEqual(after[:o],self.fixture[:o])
        self.assertEqual(after[o+1:],self.fixture[o+1:])
        self.assertEqual(after[o],0)
        self.assertEqual(len(after),len(self.fixture))

    def test_unknown_real_parent_is_rejected(self):
        with self.assertRaises(ValueError):r.repair.build(self.fixture)

    def test_mutated_root_literal_and_pp_are_rejected(self):
        for offset in (0x1cc,*r.repair.LITERALS,r.repair.OFFSET):
            raw=bytearray(self.fixture);raw[offset]^=1
            with self.subTest(offset=offset),self.assertRaises(ValueError):r.repair.patch(bytes(raw))

    def test_bad_rom_size_or_mutable_input_rejected(self):
        for raw in (b'',self.fixture[:-1],bytearray(self.fixture)):
            with self.assertRaises(ValueError):r.repair.patch(raw)

    def test_candidate_recipe_is_not_runtime_acceptance(self):
        with mock.patch.object(r.repair,'PARENT_SHA',r.repair.identity(self.fixture)['sha256']):
            after,report=r.repair.build(self.fixture)
        self.assertEqual(report['candidate'],r.repair.identity(after))
        self.assertEqual(report['changed_byte_count'],1)
        self.assertEqual(report['status'],'BUILT_NOT_ACCEPTED')
        for flag in ('full_p03_acceptance','full_p05_acceptance','release_ready','active_baseline_changed'):
            self.assertIs(report[flag],False)

    def test_selected_case_keeps_original_native_index(self):
        rows=r.cases()
        self.assertEqual(r.select_cases(rows,'keldeo-form-revert'),[(11,rows[11])])
        self.assertEqual(r.select_cases(rows,None),list(enumerate(rows)))
        with self.assertRaises(ValueError):r.select_cases(rows,'unknown')

    def test_child_identity_is_independently_required(self):
        c=r.cases()[0];d=record(c);child='a'*64
        with self.assertRaises(ValueError):r.validate(json.dumps(d).encode(),c,PROCESS,rom_sha=child)
        d['rom_sha256']=child
        r.validate(json.dumps(d).encode(),c,PROCESS,rom_sha=child)

if __name__=='__main__':unittest.main()
