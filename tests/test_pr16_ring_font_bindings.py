"""保存setter・新規callerの型/境界/出自を検査。既受入ABI/nativeは起動しない。"""
from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_font_bindings as t
import pr16_ring_followup_v2 as s


def saved():
    # run35229107711の候補identityへ結合した84byte。ROM全体ではない。
    raw=bytes.fromhex('380a000300b5011c02480068fff7a2ff02bc0847380a000330b508480468051c2868211c1031fff795ff002808d0e46828688442f4d1012003e00000380a0003002030bc02bc08470149086070470000d03d0003')
    return {'window':{'start':t.prior.LO,'end':t.prior.HI,'hex':raw.hex(),'identity':s.identity(raw)},
        'gfonts_literal_sites':[t.SETTER&~1]}


def caller(value=None,reg=0,site=None):
    raw=bytearray(0x5000);site=t.ROM+0x200 if site is None else site
    pool=t.ROM+0x220;value=t.ROM+0x3000 if value is None else value
    ldr=0x4800|(reg<<8)|((pool-((site+2)&~3))//4)
    offset=((t.SETTER&~1)-site-4)&0x7fffff
    encoded=(0xf000|(offset>>12)).to_bytes(2,'little')+(0xf800|((offset>>1)&2047)).to_bytes(2,'little')
    raw[site-t.ROM-2:site-t.ROM]=ldr.to_bytes(2,'little');raw[site-t.ROM:site-t.ROM+4]=encoded
    raw[pool-t.ROM:pool-t.ROM+4]=value.to_bytes(4,'little')
    row={'site':site,'target':t.SETTER&~1,'kind':'thumb_bl_candidate','encoded':encoded.hex(),
        'runtime_reachable':False,'code_data_boundary_proven':False}
    return bytes(raw),[row]


class SetterTests(unittest.TestCase):
    def test_exact_three_saved_instructions(self):
        n=t.setter_nodes(saved());self.assertEqual([r['hex']for r in n],['0149','0860','7047'])
    def test_changed_hash_rejected(self):
        a=saved();a['window']['identity']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'identity'):t.setter_nodes(a)
    def test_changed_signature_rejected_even_with_new_hash(self):
        a=saved();raw=bytearray.fromhex(a['window']['hex']);raw[-12]=0
        a['window'].update(hex=raw.hex(),identity=s.identity(raw))
        with self.assertRaisesRegex(ValueError,'署名'):t.setter_nodes(a)
    def test_wrong_literal_rejected_even_with_new_hash(self):
        a=saved();raw=bytearray.fromhex(a['window']['hex']);raw[-1]^=1
        a['window'].update(hex=raw.hex(),identity=s.identity(raw))
        with self.assertRaisesRegex(ValueError,'global literal'):t.setter_nodes(a)
    def test_window_origin_rejected(self):
        a=saved();a['window']['start']-=2
        with self.assertRaisesRegex(ValueError,'identity'):t.setter_nodes(a)
    def test_missing_writer_reference_rejected(self):
        a=saved();a['gfonts_literal_sites']=[]
        with self.assertRaisesRegex(ValueError,'literal候補'):t.setter_nodes(a)
    def test_store_null_is_not_initialization_acceptance(self):
        m=t.b.Cases(t.setter_nodes(saved())).run('null',t.SETTER,[(t.GFONTS,b'\xcc'*4,True)],(0,),[(t.GFONTS,4,0)],0)
        self.assertEqual(m.r[1],t.GFONTS);self.assertEqual(m.low_sp,t.b.vm.SP)
    def test_store_does_not_validate_rom_pointer(self):
        value=0xffffffff
        m=t.b.Cases(t.setter_nodes(saved())).run('arbitrary',t.SETTER,[(t.GFONTS,b'\xcc'*4,True)],(value,),[(t.GFONTS,4,value)],value)
        self.assertEqual(m.r[4:12],list(m.original[4:12]))
    def test_readonly_write_fail_closed(self):
        m=t.b.Cases(t.setter_nodes(saved())).run('readonly',t.SETTER,[(t.GFONTS,bytes(4),False)],(1,),stop=('未許可 write',t.SETTER+1))
        self.assertEqual(m.nonstack_writes(),[])
    def test_partial_write_never_claimed_complete(self):
        m=t.b.Cases(t.setter_nodes(saved())).run('short',t.SETTER,[(t.GFONTS,bytes(3),True)],(1,),stop=('未許可 write',t.SETTER+1))
        self.assertEqual(m.nonstack_writes(),[])


class CallerTests(unittest.TestCase):
    def test_immediate_r0_literal_bound(self):
        a=t.caller_literals(*caller());self.assertEqual(a['caller_prefixes'][0]['value'],t.ROM+0x3000)
    def test_caller_prefix_executes_setter_and_stops_at_scope(self):
        a=t.caller_literals(*caller());r=t.prefix_contracts(t.setter_nodes(saved()),a['caller_prefixes'])
        self.assertEqual(len(r),1);self.assertFalse(r[0]['returned']);self.assertTrue(r[0]['scope_boundary_not_callee_failure'])
    def test_alignment_of_pc_relative_supplier(self):
        a=t.caller_literals(*caller(site=t.ROM+0x202));self.assertEqual(a['caller_prefixes'][0]['supplier']['literal_address'],t.ROM+0x220)
    def test_non_r0_supplier_unresolved(self):
        a=t.caller_literals(*caller(reg=1));self.assertEqual(a['caller_prefixes'],[]);self.assertEqual(len(a['unresolved_callers']),1)
    def test_reference_count_bound(self):
        raw,r=caller()
        with self.assertRaisesRegex(ValueError,'caller上限'):t.caller_literals(raw,r*65)
    def test_duplicate_reference_rejected(self):
        raw,r=caller()
        with self.assertRaisesRegex(ValueError,'caller重複'):t.caller_literals(raw,r+r)
    def test_wrong_reference_target_rejected(self):
        raw,r=caller();r[0]['target']+=2
        with self.assertRaisesRegex(ValueError,'target差分'):t.caller_literals(raw,r)
    def test_tampered_bl_rejected(self):
        raw,r=caller();r[0]['encoded']='00000000'
        with self.assertRaisesRegex(ValueError,'BL byte'):t.caller_literals(raw,r)
    def test_even_setter_rejected(self):
        with self.assertRaisesRegex(ValueError,'setter pointer'):t.caller_literals(*caller(),setter=t.SETTER&~1)
    def test_pointer_reference_is_not_bl(self):
        raw,r=caller();r[0]['kind']='aligned_pointer_candidate'
        a=t.caller_literals(raw,r);self.assertEqual(a['caller_prefixes'],[]);self.assertEqual(a['unresolved_callers'],r)
    def test_table_identity_is_finite_192_bytes(self):
        a=t.caller_literals(*caller());table=a['tables'][0]
        self.assertEqual(table['identity'],s.identity(bytes.fromhex(table['hex'])));self.assertEqual(table['size'],192)
    def test_table_sample_does_not_prove_length_or_live_init(self):
        table=t.caller_literals(*caller())['tables'][0]
        self.assertIs(table['actual_table_length_proven'],False);self.assertIs(table['initializer_runtime_observed'],False)
    def test_caller_is_not_runtime_observation(self):
        self.assertIs(t.caller_literals(*caller())['caller_prefixes'][0]['runtime_reachable'],False)
    def test_null_supplier_not_rom_table(self):
        a=t.caller_literals(*caller(value=0));self.assertEqual(a['tables'],[]);self.assertEqual(a['caller_prefixes'][0]['value'],0)
    def test_ram_supplier_not_rom_table(self):self.assertEqual(t.caller_literals(*caller(value=t.GFONTS))['tables'],[])
    def test_unaligned_supplier_not_rom_table(self):self.assertEqual(t.caller_literals(*caller(value=t.ROM+0x3001))['tables'],[])
    def test_truncated_sample_not_inferred(self):self.assertEqual(t.caller_literals(*caller(value=t.ROM+0x4ff0))['tables'],[])
    def test_no_references_no_fabricated_table(self):self.assertEqual(t.caller_literals(bytes(8),[])['tables'],[])
    def test_points_are_unique_sorted(self):
        p=t.caller_literals(*caller())['points'];self.assertEqual(p,sorted(set(p)))
    def test_short_render_table_rejected_before_execution(self):
        table={'address':t.ROM+0x3000,'hex':'00','actual_table_length_proven':False}
        with self.assertRaisesRegex(ValueError,'有限table'):t.render_contracts([], [table])
    def test_complete_table_length_claim_rejected(self):
        table={'address':t.ROM+0x3000,'hex':'00'*192,'actual_table_length_proven':True}
        with self.assertRaisesRegex(ValueError,'有限table'):t.render_contracts([], [table])
    def test_no_tables_no_callback_acceptance(self):self.assertEqual(t.render_contracts([],[]),([],[]))


if __name__=='__main__':unittest.main()
