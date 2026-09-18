import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_native as native


def result(case):
    factory=case==native.CASES[1];battle=case==native.CASES[2];saved=not factory and not battle
    w={k:0 for k in native.TRACE}
    seq=('gateway','cancel','field') if factory else (('gateway','rentals','selected','second','confirm','draw','action','turn') if battle else ('gateway','rentals','cancel','field','saved','reloaded'))
    w.update({k:i+1 for i,k in enumerate(seq)})
    return dict(schema_version=1,status='PASS_CIRCUS_SCOPED_NATIVE',case=case,candidate_sha256=native.SHA,
        new_circus_question=True,factory_fallback=factory,rental_entry=not factory,battle_started=battle,cancelled=not battle,
        party_bytes_verified=600,save_counter_before=2,save_counter_after=3 if saved else 2,
        manual_saves=1 if saved else 0,fresh_cores=2 if saved else 1,host_write_barriers=7,input_only_after_guard=True,
        initial_fixture_is_not_admission=True,bp_earned=0,physical_admission_accepted=False,suppression_accepted=False,
        release_ready=False,warnings_errors=0,effect_flags=1 if battle else 0,total_frames=len(seq),witness=w)


def trace(case):
    return b'CIRCUS label=fixture frame=1\nCIRCUS label=circus-question frame=2\n'+(b'CIRCUS label=circus-action frame=3\n' if case==native.CASES[2] else b'CIRCUS label=returned frame=3\n')


class NativeResultContracts(unittest.TestCase):
    def check(self,r,case=None,stderr=None,code=0):
        case=case or r['case'];return native.validate(json.dumps(r).encode(),trace(case) if stderr is None else stderr,code,case)
    def test_three_new_case_contracts(self):
        for case in native.CASES:self.assertEqual(self.check(result(case)),result(case))
    def test_reject_failed_and_bool_exit(self):
        for code in (1,-1,False):
            with self.assertRaises(ValueError):self.check(result(native.CASES[0]),code=code)
    def test_reject_wrong_candidate_or_case(self):
        for key,v in (('candidate_sha256','0'*64),('case','old-accepted-case')):
            r=result(native.CASES[0]);r[key]=v
            with self.assertRaises(ValueError):self.check(r,case=native.CASES[0])
    def test_reject_missing_extra_and_duplicate_keys(self):
        r=result(native.CASES[0]);del r['host_write_barriers']
        with self.assertRaises(ValueError):self.check(r)
        r=result(native.CASES[0]);r['extra']=True
        with self.assertRaises(ValueError):self.check(r)
        with self.assertRaises(ValueError):native.strict(b'{"a":1,"a":1}')
    def test_reject_nonfinite(self):
        for value in (b'NaN',b'Infinity',b'-Infinity'):
            with self.assertRaises(ValueError):native.strict(b'{"a":'+value+b'}')
    def test_reject_weak_guards_or_unsupported_acceptance(self):
        for key,v in (('host_write_barriers',6),('input_only_after_guard',False),('initial_fixture_is_not_admission',False),
                      ('physical_admission_accepted',True),('suppression_accepted',True),('release_ready',True),('bp_earned',1)):
            r=result(native.CASES[0]);r[key]=v
            with self.assertRaises(ValueError):self.check(r)
    def test_reject_full_save_or_core_misaccount(self):
        for key,v in (('save_counter_before',1),('save_counter_after',4),('manual_saves',0),('fresh_cores',1)):
            r=result(native.CASES[0]);r[key]=v
            with self.assertRaises(ValueError):self.check(r)
    def test_reject_integer_bools(self):
        for key in ('schema_version','save_counter_before','manual_saves','total_frames','effect_flags'):
            r=result(native.CASES[0]);r[key]=True
            with self.assertRaises(ValueError):self.check(r)
    def test_reject_invalid_effect_draw(self):
        for value in (0,3,1<<20,1<<24,1<<31,-1,2**32):
            r=result(native.CASES[2]);r['effect_flags']=value
            with self.assertRaises(ValueError):self.check(r)
    def test_reject_effects_on_cancel(self):
        for case in native.CASES[:2]:
            r=result(case);r['effect_flags']=1
            with self.assertRaises(ValueError):self.check(r)
    def test_reject_out_of_order_or_missing_witness(self):
        for key,value in (('gateway',0),('cancel',1),('reloaded',999),('rentals',True)):
            r=result(native.CASES[0]);r['witness'][key]=value
            with self.assertRaises(ValueError):self.check(r)
    def test_reject_unrequested_stage(self):
        r=result(native.CASES[1]);r['witness']['rentals']=1
        with self.assertRaises(ValueError):self.check(r)
    def test_reject_missing_original_or_warning(self):
        for stderr in (b'',trace(native.CASES[0])+b'mGBA[warning]'):
            with self.assertRaises(ValueError):self.check(result(native.CASES[0]),stderr=stderr)
    def test_same_frame_draw_and_action_are_allowed_but_not_reversed(self):
        r=result(native.CASES[2]);r['witness']['draw']=r['witness']['confirm'];self.check(r)
        r['witness']['draw']=r['witness']['confirm']-1
        with self.assertRaises(ValueError):self.check(r)

if __name__=='__main__':unittest.main()
