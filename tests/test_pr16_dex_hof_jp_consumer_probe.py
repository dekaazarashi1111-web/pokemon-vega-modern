"""新規scopeの合成fixtureだけ。受入済みROM/nativeを再走しない。"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import pr16_dex_hof_jp_consumer_probe as p
import pr16_dex_hof_jp_consumer_probe_actions as a


def rom(data, start=p.BASE):
    return b'\0'*(start-p.BASE)+bytes(data)


class TextGrammar(unittest.TestCase):
    def test_literal_eos(self):
        r=p.lexical_text(rom([1,2,255]),p.BASE)
        self.assertEqual((r['size'],r['eos_address']), (3,p.BASE+2))
        self.assertFalse(r['runtime_read_proven'])
    def test_pause_control(self):
        r=p.lexical_text(rom([1,252,9,255]),p.BASE)
        self.assertEqual(r['tokens'][-2],dict(offset=1,size=2,role='pause_until_press'))
    def test_placeholders_use_actual_public_numbering(self):
        r=p.lexical_text(rom([253,2,253,3,253,4,255]),p.BASE)
        self.assertEqual([t['role'] for t in r['tokens']],['string_var_1','string_var_2','string_var_3','eos'])
    def test_newline_paragraph_scroll(self):
        r=p.lexical_text(rom([254,251,250,255]),p.BASE)
        self.assertEqual([t['role'] for t in r['tokens']],['newline','paragraph','scroll','eos'])
    def test_fc_operand_ff_is_not_eos(self):
        with self.assertRaises(ValueError): p.lexical_text(rom([252,255]),p.BASE)
    def test_fd_operand_ff_is_not_eos(self):
        with self.assertRaises(ValueError): p.lexical_text(rom([253,255]),p.BASE)
    def test_unsupported_ext_control(self):
        with self.assertRaises(ValueError): p.lexical_text(rom([252,1,255]),p.BASE)
    def test_unproven_special_character(self):
        with self.assertRaises(ValueError): p.lexical_text(rom([247,255]),p.BASE)
    def test_missing_eos(self):
        with self.assertRaises(ValueError): p.lexical_text(rom([1]*128),p.BASE)
    def test_truncated_placeholder(self):
        with self.assertRaises(ValueError): p.lexical_text(rom([253,2,255]),p.BASE,1)
    def test_truncated_control(self):
        with self.assertRaises(ValueError): p.lexical_text(rom([252,9,255]),p.BASE,1)
    def test_empty_text(self):
        self.assertEqual(p.lexical_text(rom([255]),p.BASE)['size'],1)
    def test_budget_not_neighbor_extent(self):
        self.assertEqual(p.lexical_text(rom([1,255]+[2]*126),p.BASE,128)['size'],2)
    def test_oversized_budget(self):
        with self.assertRaises(ValueError): p.lexical_text(rom([255]),p.BASE,129)
    def test_negative_read(self):
        with self.assertRaises(ValueError): p.chunk(b'abc',p.BASE-1,1)
    def test_zero_read(self):
        with self.assertRaises(ValueError): p.chunk(b'abc',p.BASE,0)
    def test_no_payload_in_output(self):
        r=p.lexical_text(rom([1,2,3,255]),p.BASE)
        self.assertEqual(set(r),{'address','size','sha256','eos_address','tokens','lexical_complete','runtime_read_proven'})
        self.assertTrue(all(set(t)=={'offset','size','role'}for t in r['tokens']))


class ControlFlow(unittest.TestCase):
    def test_return(self):
        r=p.observe_cfg(bytes.fromhex('7047'),p.BASE,2,{})
        self.assertEqual(r['instruction_count'],1)
        self.assertEqual(r['stops'][0]['reason'],'indirect_or_return')
    def test_conditional_both_successors(self):
        r=p.observe_cfg(bytes.fromhex('00d070477047'),p.BASE,6,{})
        self.assertEqual(r['instruction_count'],3)
    def test_loop_is_finite(self):
        self.assertEqual(p.observe_cfg(bytes.fromhex('fee7'),p.BASE,2,{})['instruction_count'],1)
    def test_budget_exit(self):
        r=p.observe_cfg(bytes.fromhex('00e0'),p.BASE,2,{})
        self.assertEqual(r['stops'][0]['reason'],'budget_exit')
    def test_unknown_instruction_is_unaccepted(self):
        r=p.observe_cfg(bytes.fromhex('00de'),p.BASE,2,{})
        self.assertEqual(r['stops'][0]['reason'],'unsupported_instruction')
        self.assertFalse(r['registered_root_proven'])
    def test_literal_hook_reports_no_execution(self):
        data=bytes.fromhex('004b1847')+(p.BASE+9).to_bytes(4,'little')+bytes.fromhex('7047')
        r=p.observe_cfg(data,p.BASE,8,{})
        self.assertEqual(r['stops'][0]['reason'],'literal_thumb_hook')
        self.assertFalse(r['api_arguments_proven'])
    def test_literal_values_are_not_dumped(self):
        data=bytes.fromhex('004b7047')+(12345678).to_bytes(4,'little')
        r=p.observe_cfg(data,p.BASE,8,{})
        self.assertNotIn('target',r['named_literal_reads'][0])
        self.assertNotIn('12345678',json.dumps(r))
    def test_incomplete_bl(self):
        self.assertEqual(p.observe_cfg(bytes.fromhex('00f0'),p.BASE,2,{})['stops'][0]['reason'],'truncated_instruction')
    def test_direct_call_is_not_return_proof(self):
        r=p.observe_cfg(bytes.fromhex('00f000f87047'),p.BASE,6,{p.BASE+4:'named'})
        self.assertEqual(r['calls'][0]['target_name'],'named')
        self.assertFalse(r['calls'][0]['return_assumed'])
    def test_oversized_cfg_budget(self):
        with self.assertRaises(ValueError):p.observe_cfg(b'xx',p.BASE,0x402,{})
    def test_candidate_mismatch_before_observation(self):
        with self.assertRaisesRegex(ValueError,'全ROM'): p.measure(b'bad',{})


class Publication(unittest.TestCase):
    def test_manifest_is_independently_frozen(self):
        self.assertEqual(json.loads((ROOT/a.SOURCE_MANIFEST).read_bytes()),p.EXTRA)
    def test_workflow_publication_contract(self):
        self.assertEqual(a.publication.contract(ROOT,a.WF,a.PUBLIC,a.ARTIFACT,a.SELF)['artifact'],a.ARTIFACT)
    def test_missing_success_report_rejected(self):
        with tempfile.TemporaryDirectory() as td, patch.object(a,'PUBLIC',Path(td)):
            (Path(td)/'probe-tests.json').write_text('pass\n')
            with self.assertRaises(ValueError):a.export()
    def test_hidden_file_rejected(self):
        with tempfile.TemporaryDirectory() as td, patch.object(a,'PUBLIC',Path(td)):
            for name,data in [('measurement.json','{}\n'),('probe-tests.json','ok\n'),('.secret','no\n')]: (Path(td)/name).write_text(data)
            with self.assertRaises(ValueError):a.export()
    def test_unknown_extension_rejected(self):
        with tempfile.TemporaryDirectory() as td, patch.object(a,'PUBLIC',Path(td)):
            for name,data in [('measurement.json','{}\n'),('probe-tests.json','ok\n'),('rom.bin','no\n')]: (Path(td)/name).write_text(data)
            with self.assertRaises(ValueError):a.export()
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as td, patch.object(a,'PUBLIC',Path(td)):
            (Path(td)/'measurement.json').write_text('{}\n');(Path(td)/'probe-tests.json').symlink_to('measurement.json')
            with self.assertRaises(ValueError):a.export()
    def test_empty_test_output_rejected(self):
        with tempfile.TemporaryDirectory() as td, patch.object(a,'PUBLIC',Path(td)):
            (Path(td)/'measurement.json').write_text('{}\n');(Path(td)/'probe-tests.json').write_bytes(b'')
            with self.assertRaises(ValueError):a.export()

class ClosedReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw=bytearray(p.CANDIDATE['size'])
        for address,budget in p.FUNCTIONS.values():raw[address-p.BASE:address-p.BASE+2]=bytes.fromhex('7047')
        for name,address in p.TEXTS:raw[address-p.BASE:address-p.BASE+2]=bytes((1,255))
        for name,address,target in p.CELLS:raw[address-p.BASE:address-p.BASE+4]=target.to_bytes(4,'little')
        raw=bytes(raw);real_identity=p.identity
        with patch.object(p,'identity',lambda b:p.CANDIDATE if b is raw else real_identity(b)):
            cls.base=p.measure(raw,json.loads((ROOT/p.cross.CONTRACT).read_bytes()))
        p.validate_report(cls.base)
    def reject(self,change):
        report=copy.deepcopy(self.base);change(report)
        with self.assertRaises((ValueError,KeyError,TypeError)):p.validate_report(report)
    def test_whole_report_passes(self):self.assertTrue(p.validate_report(self.base))
    def test_new_classification_refused(self):self.reject(lambda r:r.update(newly_classified=1))
    def test_native_bool_refused(self):self.reject(lambda r:r.update(native_processes=False))
    def test_root_claim_refused(self):self.reject(lambda r:r['functions']['CursorCB_Enter'].update(registered_root_proven=True))
    def test_api_claim_refused(self):self.reject(lambda r:r.update(all_api_arguments_proven=True))
    def test_serializer_claim_refused(self):self.reject(lambda r:r.update(serializer_execution_proven=True))
    def test_donor_claim_refused(self):self.reject(lambda r:r.update(donor_eligible=True))
    def test_unknown_top_payload_refused(self):self.reject(lambda r:r.update(raw_hex='aabb'))
    def test_unknown_function_payload_refused(self):self.reject(lambda r:r['functions']['CursorCB_Enter'].update(raw_hex='aabb'))
    def test_unknown_text_payload_refused(self):self.reject(lambda r:r['texts']['gText_SwitchedPkmnItem'].update(raw_hex='aabb'))
    def test_text_reader_claim_refused(self):self.reject(lambda r:r['texts']['gText_SwitchedPkmnItem'].update(runtime_read_proven=True))
    def test_text_token_gap_refused(self):self.reject(lambda r:r['texts']['gText_SwitchedPkmnItem']['tokens'][0].update(offset=1))
    def test_extent_from_neighbor_refused(self):self.reject(lambda r:r['texts']['gText_SwitchedPkmnItem'].update(size=24))
    def test_thumb_mismatch_refused(self):self.reject(lambda r:r['cells'][0].update(actual_thumb_target=0x08124930))
    def test_hit_owner_invention_refused(self):self.reject(lambda r:r['hits'][0]['byte_roles'][0]['owners'].append(dict(text='gText_CantUseUntilNewBadge',role='glyph')))
    def test_formal_save_mutation_refused(self):self.reject(lambda r:r.update(formal_save_changed=True))

class PublishedReport(unittest.TestCase):
    def verify_export(self,report_change=None,test_change=None,env_change=None,head=None,dirty=False):
        report=copy.deepcopy(ClosedReport.base)
        sha='a'*40; run=123
        report.update(source_head=sha,run_id=run,current_rom_reconstructions=1,unit_tests=59,current_owner_count=115,source_bindings={name:p.identity((ROOT/name).read_bytes())for name in sorted(a.CODE)},fixed_crosswalk_identity=p.cross.CONTRACT_ID,extra_source_bindings=p.EXTRA)
        tests=dict(status='PASS_NEW_SYNTHETIC_TESTS',tests=59,failures=0,errors=0,skipped=0)
        if report_change:report_change(report)
        if test_change:test_change(tests)
        env=dict(GITHUB_SHA=sha,GITHUB_RUN_ID=str(run),PROBE_MEASUREMENT_OUTCOME='success')
        if env_change:env_change(env)
        with tempfile.TemporaryDirectory()as td,patch.object(a,'PUBLIC',Path(td)),patch.dict(a.os.environ,env),patch.object(a.subprocess,'check_output',return_value=head or sha),patch.object(a.subprocess,'run',return_value=a.subprocess.CompletedProcess([],1 if dirty else 0)):
            (Path(td)/'measurement.json').write_text(json.dumps(report)+'\n')
            (Path(td)/'probe-tests.json').write_text(json.dumps(tests)+'\n')
            a.export()
    def test_successful_bound_export(self):self.verify_export()
    def test_wrong_source_rejected(self):
        with self.assertRaises(ValueError):self.verify_export(report_change=lambda r:r.update(source_head='b'*40))
    def test_wrong_run_rejected(self):
        with self.assertRaises(ValueError):self.verify_export(report_change=lambda r:r.update(run_id=456))
    def test_changed_binding_rejected(self):
        with self.assertRaises(ValueError):self.verify_export(report_change=lambda r:r['source_bindings'][a.SELF].update(size=1))
    def test_wrong_head_rejected(self):
        with self.assertRaises(ValueError):self.verify_export(head='b'*40)
    def test_dirty_checkout_rejected(self):
        with self.assertRaises(ValueError):self.verify_export(dirty=True)
    def test_failed_measurement_rejected(self):
        with self.assertRaises(ValueError):self.verify_export(env_change=lambda e:e.update(PROBE_MEASUREMENT_OUTCOME='failure'))
    def test_arbitrary_test_payload_rejected(self):
        with self.assertRaises(ValueError):self.verify_export(test_change=lambda t:t.update(raw_hex='aabb'))

if __name__=='__main__':unittest.main()
