"""末尾ABIと5工程集約の限定回帰。先行ABIを再実行しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_external1_exit_abi as m


def fixture():
    return {'candidate':copy.deepcopy(m.s.CANDIDATE),'target':m.START|1,'next_saved_abi_target':m.START|1,
        'graph':{'entry':m.START|1,'window':64,'window_identity':{'size':64,'sha256':'fb1ba4e1aa1ffca56c5afeb35034230da65dfa84c91ad56bcd664b953fd7cee6'},
        'nodes':m.expected_nodes(),'memory_write_sites':[],'external_edges':copy.deepcopy(m.EDGES),
        'saved_instruction_bytes_redecoded':0,'deferred_roots_decoded':0},
        'sampled_ranges':[dict(address=m.START+2*i,hex=h,**m.s.identity(bytes.fromhex(h))) for i,h in enumerate(m.CODE)],
        'sampled_instruction_bytes':6,'inherited_frame_bytes_live':16,'unresolved_indirect_edges':copy.deepcopy(m.EDGES),
        'old_unread_targets':list(range(1,36,2)),'remaining_unread_targets':[*range(1,36,2),0x0806DD1D,0x081138F9],
        **{k:False for k in ('callee_return_proven','callee_return_observed','saved_slot_preservation_proven','return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready')}}


def analyses():
    rows=[]
    for i in range(5):
        a={'candidate':copy.deepcopy(m.s.CANDIDATE),'rom_changes':0,'new_emulator_processes':0,
           'accepted_native_cases_replayed':0,'candidate_reconstructions':int(i in (1,3)),
           'new_graph_decodes':int(i in (1,3)),'prior_abi_classifications_replayed':0,
           'ring_acquisition_accepted':False,'release_ready':False,'old_unread_targets':list(range(18))}
        if i in (1,3):a['sampled_instruction_bytes']=36 if i==1 else 6
        else:a['instruction_bytes_verified']={0:46,2:36,4:6}[i]
        rows.append(a)
    return rows


def frame(words=(1,2,3,0x08101235)):return b''.join(x.to_bytes(4,'little') for x in words)

class ExitABI(unittest.TestCase):
    def test_program(self):self.assertEqual(len(m.program(fixture())),3)
    def test_all_opcode_mutations(self):
        for i in range(3):
            a=fixture();a['graph']['nodes'][i]['hex']='0000'
            with self.assertRaises(ValueError):m.program(a)
    def test_graph_branch_register_mutation(self):
        a=fixture();a['graph']['nodes'][2]['register']=0
        with self.assertRaises(ValueError):m.program(a)
    def test_sample_hash_mutation(self):
        a=fixture();a['sampled_ranges'][0]['sha256']='0'*64
        with self.assertRaises(ValueError):m.program(a)
    def test_return_edge_not_resolved_by_invention(self):
        a=fixture();a['unresolved_indirect_edges'][0]['target']=0x08100001
        with self.assertRaises(ValueError):m.program(a)
    def test_inherited_frame_mutation(self):
        a=fixture();a['inherited_frame_bytes_live']=12
        with self.assertRaises(ValueError):m.program(a)
    def test_old_frontier_cannot_disappear(self):
        a=fixture();a['remaining_unread_targets'].remove(1)
        with self.assertRaises(ValueError):m.program(a)
    def test_unconditional_acceptance_rejected(self):
        a=fixture();a['callee_return_proven']=True
        with self.assertRaises(ValueError):m.program(a)
    def test_exact_restore(self):self.assertEqual(m.execute(9,0x3006000,frame())['restored_r4_r5_r6'],[1,2,3])
    def test_r0_all_bit_positions_preserved(self):
        for value in (0,m.MASK,*[1<<i for i in range(32)]):self.assertEqual(m.execute(value,0x3006000,frame())['r0'],value)
    def test_sp_and_read_addresses(self):
        r=m.execute(0,0x3006000,frame());self.assertEqual(r['exit_sp'],0x3006010);self.assertEqual(r['local_sp_delta'],16)
        self.assertEqual([x['address'] for x in r['stack_reads']],[0x3006000,0x3006004,0x3006008,0x300600c])
    def test_lr_word_becomes_bx_operand(self):self.assertEqual(m.execute(0,0x3006000,frame())['branch_operand'],0x08101235)
    def test_even_lr_not_forced_thumb(self):
        r=m.execute(0,0x3006000,frame((1,2,3,0x08101234)));self.assertEqual(r['selected_isa'],'ARM');self.assertFalse(r['branch_target_executed'])
    def test_odd_lr_selects_thumb(self):self.assertEqual(m.execute(0,0x3006000,frame())['selected_isa'],'THUMB')
    def test_no_store_or_prior_code(self):
        r=m.execute(0,0x3006000,frame());self.assertEqual(r['local_memory_writes'],0);self.assertFalse(r['prior_code_executed'])
    def test_frame_width_rejected(self):
        for data in (b'',bytes(12),bytes(20)):
            with self.assertRaises(ValueError):m.execute(0,0x3006000,data)
    def test_sp_alignment_and_overflow_rejected(self):
        for sp in (-4,2,0xfffffffc):
            with self.assertRaises(ValueError):m.execute(0,sp,frame())
    def test_counter_alias_changes_branch_not_r0(self):
        a=m.alias_diagnostic();self.assertFalse(a['observed']);self.assertNotEqual(a['before_branch_operand'],a['after_branch_operand'])
    def test_non_lr_word_change_is_visible(self):
        r=m.execute(0,0x3006000,frame((0xffffffff,2,3,0x08101235)));self.assertEqual(r['restored_r4_r5_r6'][0],0xffffffff)
    def test_aggregate_totals(self):
        a=m.aggregate(analyses());self.assertEqual(a['sampled_instruction_bytes'],42);self.assertEqual(a['verified_instruction_bytes'],88)
    def test_aggregate_requires_five(self):
        with self.assertRaises(ValueError):m.aggregate(analyses()[:4])
    def test_aggregate_rejects_replay(self):
        rows=analyses();rows[0]['accepted_native_cases_replayed']=1
        with self.assertRaises(ValueError):m.aggregate(rows)
    def test_aggregate_rejects_scope_promotion(self):
        rows=analyses();rows[3]['ring_acquisition_accepted']=True
        with self.assertRaises(ValueError):m.aggregate(rows)
    def test_aggregate_rejects_old_owner_loss(self):
        rows=analyses();rows[3]['old_unread_targets'].pop()
        with self.assertRaises(ValueError):m.aggregate(rows)

if __name__=='__main__':unittest.main()
