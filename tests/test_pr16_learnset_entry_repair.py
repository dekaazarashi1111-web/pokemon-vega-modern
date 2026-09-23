"""CFRU初回入口修復の8byte/preimage/表混在/非再実行境界。旧31件は呼ばない。"""
from __future__ import annotations
import copy
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_learnset_entry_repair as r
p=r.p


class EntryRepairTests(unittest.TestCase):
    def specimen(self):
        return bytes(range(8))+r.BEFORE+bytes(range(8,24))
    def test_exact_eight_byte_change(self):
        raw=self.specimen();out=r.replace_span(raw,8,r.BEFORE,r.AFTER)
        self.assertEqual(len(out),len(raw));self.assertEqual(out[:8],raw[:8]);self.assertEqual(out[8:16],r.AFTER);self.assertEqual(out[16:],raw[16:])
    def test_wrong_preimage_rejected(self):
        with self.assertRaises(ValueError):r.replace_span(bytes(32),8,r.BEFORE,r.AFTER)
    def test_idempotent_rerun_rejected(self):
        raw=r.replace_span(self.specimen(),8,r.BEFORE,r.AFTER)
        with self.assertRaises(ValueError):r.replace_span(raw,8,r.BEFORE,r.AFTER)
    def test_unaligned_rejected(self):
        with self.assertRaises(ValueError):r.replace_span(self.specimen(),9,r.BEFORE,r.AFTER)
    def test_negative_rejected(self):
        with self.assertRaises(ValueError):r.replace_span(self.specimen(),-4,r.BEFORE,r.AFTER)
    def test_boolean_offset_rejected(self):
        with self.assertRaises(ValueError):r.replace_span(self.specimen(),False,r.BEFORE,r.AFTER)
    def test_truncated_rejected(self):
        with self.assertRaises(ValueError):r.replace_span(self.specimen()[:15],8,r.BEFORE,r.AFTER)
    def test_size_change_rejected(self):
        with self.assertRaises(ValueError):r.replace_span(self.specimen(),8,r.BEFORE,r.AFTER+b'\0')
    def test_noop_rejected(self):
        with self.assertRaises(ValueError):r.replace_span(self.specimen(),8,r.BEFORE,r.BEFORE)
    def test_parent_binding_rejected(self):
        with self.assertRaises(ValueError):r.apply(bytes(32))
    def test_entry_identity(self):
        self.assertEqual(r.ENTRY,0x09114038);self.assertEqual(r.ENTRY%4,0);self.assertEqual(r.BEFORE.hex(),'f0b5c64600b5038c')
    def test_thumb_literal_veneer(self):
        self.assertEqual(struct.unpack('<HHI',r.AFTER),(0x4b00,0x4718,0x09377729));self.assertEqual(r.TARGET&1,1)
    def test_mixed_original_tables_reproduces_missing_middle(self):
        modern=p.LEVELS[414];legacy=[(16,0)]+modern
        self.assertEqual(r.first_sequence(legacy,modern,12),[77,79]);self.assertEqual([x for x,lv in modern if lv==12],[77,78,79])
    def test_consistent_modern_first_keeps_all_three(self):
        rows=p.LEVELS[414];self.assertEqual(r.first_sequence(rows,rows,12),[77,78,79])
    def test_no_level_row_does_not_invent(self):
        self.assertEqual(r.first_sequence(p.LEVELS[414],p.LEVELS[414],13),[])
    def test_new_candidate_requires_all_impacted_cases(self):
        vv=p.vectors({i:20 for i in range(1063)});todo,old=r.select_pending(vv,None,{'sha256':'new'})
        self.assertEqual(len(todo),11);self.assertEqual(old,[])
    def test_repair_success_skipped(self):
        vv=p.vectors({i:20 for i in range(1063)});one=p.expected(vv[0]);todo,old=r.select_pending(vv,{'candidate':r.PARENT,'results':[one]},r.PARENT)
        self.assertEqual(len(todo),10);self.assertEqual(old,[one]);self.assertNotIn(one['case'],[x['name'] for x in todo])
    def test_cross_candidate_success_not_inherited(self):
        with self.assertRaises(ValueError):r.select_pending([],{'candidate':r.PARENT,'results':[]},{'sha256':'other'})
    def test_duplicate_prior_rejected(self):
        vv=p.vectors({i:20 for i in range(1063)});one=p.expected(vv[0])
        with self.assertRaises(ValueError):r.select_pending(vv,{'candidate':r.PARENT,'results':[one,one]},r.PARENT)
    def test_unknown_prior_rejected(self):
        with self.assertRaises(ValueError):r.select_pending([],{'candidate':r.PARENT,'results':[{'case':'invented'}]},r.PARENT)
    def test_changed_accepted_moves_rejected(self):
        vv=p.vectors({i:20 for i in range(1063)});one=copy.deepcopy(p.expected(vv[0]));one['moves_after'][0]=1
        with self.assertRaises(ValueError):r.select_pending(vv,{'candidate':r.PARENT,'results':[one]},r.PARENT)
    def test_native_scope_remains_limited(self):
        e=p.expected(p.vectors({i:20 for i in range(1063)})[0])
        for name in ('initial_creation_accepted','battle_exp_accepted','issue19_complete','release_ready'):self.assertFalse(e[name])
    def test_passive_trace_has_no_host_state_injection(self):
        text=(ROOT/p.C).read_text();phase=text[text.index('static void p_frame'):text.index('static void p_check')]
        for name in ('write8(','write16(','write32(','write_register(','call_rom_args(','call_preserving(','p02s_data('):self.assertNotIn(name,phase)
        self.assertEqual(text.count('a_guard(c);'),3);self.assertIn('c->step(c)',phase)
    def test_assembler_is_only_tail_jump(self):
        text=(ROOT/r.ASM).read_text();body=text.split('pr16_cfru_normal_entry:',1)[1].split('.size',1)[0]
        self.assertEqual([s.strip() for s in body.splitlines() if s.strip()],['ldr r3, [pc, #0]','bx r3','.word 0x09377729'])
    def test_diagnosis_artifact_is_locked(self):
        self.assertEqual(r.DIAG_RUN,35853096160);self.assertEqual(r.DIAG_ARTIFACT['size_in_bytes'],94324);self.assertEqual(len(r.DIAG_ARTIFACT['digest']),71)
    def test_active_baseline_not_written(self):
        text=(ROOT/r.SELF).read_text();self.assertNotIn("state['candidate']=",text);self.assertIn("'active_baseline_changed':False",text)


if __name__=='__main__':unittest.main()
