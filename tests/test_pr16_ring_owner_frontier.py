"""既知/共有/operand/literal/未読の区別と有限探索境界の新規テスト。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_owner_frontier as m
B=m.ROM_BASE


def decoder(raw,at):
    """fixture専用の最小語彙。本番では既存のtracked decoderを使用する。"""
    off=at-B;h=int.from_bytes(raw[off:off+2],'little')
    row={'address':at,'size':2,'hex':raw[off:off+2].hex(),'kind':'ordinary','memory_write':h==0xB500}
    if h==0xDEAD:raise ValueError('fixture未読命令')
    if h==0x4770:row['kind']='return'
    elif h==0x4718:row.update(kind='indirect',register=3)
    elif h&0xF800==0xE000:
        delta=h&2047;row.update(kind='jump',target=at+4+2*(delta-(2048 if delta&1024 else 0)))
    elif h&0xF000==0xD000:
        delta=h&255;row.update(kind='conditional',target=at+4+2*(delta-(256 if delta&128 else 0)))
    elif h&0xF800==0xF000:
        low=int.from_bytes(raw[off+2:off+4],'little')
        if low&0xF800!=0xF800:raise ValueError('fixture BL suffix')
        delta=((h&2047)<<12)|((low&2047)<<1)
        if h&1024:delta-=1<<23
        row.update(kind='call',target=at+4+delta,size=4,hex=raw[off:off+4].hex())
    elif h&0xF800==0x4800:
        pool=((at+4)&~3)+(h&255)*4
        row.update(literal_address=pool,literal_value=int.from_bytes(raw[pool-B:pool-B+4],'little'))
    return row


class OwnerFrontierTests(unittest.TestCase):
    def raw(self,hexcode):return bytes.fromhex(hexcode)+bytes(256-len(bytes.fromhex(hexcode)))
    def inspect(self,hexcode,roots=(B+1,),cached=None,**kwargs):
        return m.inspect_frontier(self.raw(hexcode),roots,cached or {},decoder,**kwargs)
    def kinds(self,value,index=0):return [e['kind'] for e in value['roots'][index]['boundaries']]
    def test_return_is_not_abi(self):
        result=self.inspect('7047');self.assertEqual(self.kinds(result),['return_opcode_not_abi_proof'])
        self.assertFalse(result['roots'][0]['side_effects_excluded']);self.assertFalse(result['roots'][0]['runtime_reachable'])
    def test_call_not_recursed(self):
        result=self.inspect('00f002f8704770477047')
        self.assertEqual([n['address'] for n in result['new_nodes']],[B,B+4])
        self.assertIn('unread_call',self.kinds(result));self.assertNotIn(B+8,result['points'])
    def test_conditional_both_paths(self):
        result=self.inspect('00d070477047');self.assertEqual(len(result['new_nodes']),3)
    def test_loop_terminates_without_return_claim(self):
        result=self.inspect('fee7');self.assertEqual(len(result['new_nodes']),1)
        self.assertEqual(self.kinds(result),['revisited_node_boundary'])
    def test_outside_branch_not_followed(self):
        result=self.inspect('00e0',window=2);self.assertEqual(self.kinds(result),['outside_branch'])
    def test_window_fallthrough(self):
        result=self.inspect('0020',window=2);self.assertEqual(self.kinds(result),['window_boundary'])
    def test_indirect_not_followed(self):
        result=self.inspect('1847');self.assertEqual(self.kinds(result),['indirect_boundary'])
    def test_node_budget_is_boundary(self):
        result=self.inspect('002001207047',limit=1);self.assertEqual(len(result['new_nodes']),1)
        self.assertEqual(self.kinds(result),['node_limit_boundary'])
    def test_saved_node_not_decoded(self):
        raw=self.raw('7047');node=decoder(raw,B)
        def forbidden(*args):raise AssertionError('旧node再解読')
        result=m.inspect_frontier(raw,[B+1],{B:node},forbidden)
        self.assertEqual(result['new_nodes'],[]);self.assertEqual(self.kinds(result),['saved_node_boundary'])
    def test_saved_identity_rejected(self):
        raw=self.raw('7047');node=decoder(raw,B);node['hex']='0020'
        with self.assertRaises(ValueError):m.inspect_frontier(raw,[B+1],{B:node},decoder)
    def test_shared_nodes_not_decoded_twice(self):
        calls=[]
        def counted(raw,at):calls.append(at);return decoder(raw,at)
        result=m.inspect_frontier(self.raw('00207047'),[B+1,B+3],{},counted)
        self.assertEqual(calls,[B,B+2]);self.assertEqual(self.kinds(result,1),['cohort_node_boundary'])
    def test_operand_entry_boundary(self):
        result=self.inspect('00f000f87047',roots=(B+1,B+3))
        self.assertEqual(self.kinds(result,1),['instruction_operand_boundary'])
    def test_truncated_bl_boundary(self):
        result=self.inspect('00f000f8',window=2);self.assertEqual(self.kinds(result),['truncated_instruction_boundary'])
        self.assertFalse(result['new_nodes'])
    def test_unknown_opcode_recorded(self):
        result=self.inspect('adde');self.assertEqual(self.kinds(result),['decoder_rejection'])
        self.assertEqual(result['points'],[B,B+1]);self.assertEqual(result['new_nodes'],[])
    def test_literal_preserved_not_executed(self):
        result=self.inspect('014870470000000044332211',roots=(B+1,B+9))
        self.assertEqual(result['new_nodes'][0]['literal_value'],0x11223344)
        self.assertEqual(self.kinds(result,1),['literal_data_boundary'])
        self.assertTrue(set(range(B+8,B+12))<=set(result['points']))
    def test_memory_write_stays_visible(self):
        result=self.inspect('00b57047');self.assertTrue(result['new_nodes'][0]['memory_write'])
        self.assertFalse(result['roots'][0]['side_effects_excluded'])
    def test_bad_decode_address_rejected(self):
        def bad(raw,at):return {**decoder(raw,at),'address':at+2}
        with self.assertRaises(ValueError):m.inspect_frontier(self.raw('7047'),[B+1],{},bad)
    def test_bad_decode_bytes_rejected(self):
        def bad(raw,at):return {**decoder(raw,at),'hex':'0020'}
        with self.assertRaises(ValueError):m.inspect_frontier(self.raw('7047'),[B+1],{},bad)
    def test_root_validation(self):
        for roots in ([],[B+1,B+1],[B],[True],[B+257]):
            with self.subTest(roots=roots),self.assertRaises(ValueError):self.inspect('7047',roots=roots)
    def test_resource_validation(self):
        for kwargs in ({'window':0},{'window':129},{'window':3},{'window':True},{'limit':0},{'limit':65},{'limit':True}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):self.inspect('7047',**kwargs)
    def test_raw_type_rejected(self):
        for raw in (b'',bytearray(256)):
            with self.subTest(raw=type(raw)),self.assertRaises(ValueError):m.inspect_frontier(raw,[B+1],{},decoder)
    def test_cache_duplicate_unchanged(self):
        node=decoder(self.raw('7047'),B);before=copy.deepcopy(node)
        found=m.cache_nodes([{'nodes':[node,node]}]);self.assertEqual(len(found),1);self.assertEqual(node,before)
    def test_cache_conflict_rejected(self):
        node=decoder(self.raw('7047'),B)
        with self.assertRaises(ValueError):m.cache_nodes([{'nodes':[node,{**node,'hex':'0020'}]}])
    def test_cache_overlap_rejected(self):
        raw=self.raw('00f000f87047');node=decoder(raw,B)
        with self.assertRaises(ValueError):m.cache_nodes([{'nodes':[node,decoder(raw,B+2)]}])
    def test_new_windows_only_missing(self):
        raw=self.raw('00207047');memory={B:0,B+1:32};before=memory.copy()
        rows,reused=m.new_windows(raw,[B,B+1,B+2,B+3],memory)
        self.assertEqual(reused,2);self.assertEqual(rows[0]['hex'],'7047');self.assertEqual(memory,before)
        self.assertEqual(rows[0]['identity'],m.identity(bytes.fromhex('7047')))
    def test_new_windows_conflict_rejected(self):
        with self.assertRaises(ValueError):m.new_windows(self.raw('7047'),[B],{B:0})
    def test_new_windows_split_and_reused(self):
        raw=self.raw('00207047');rows,reused=m.new_windows(raw,[B,B+1,B+2,B+3],{B+1:32})
        self.assertEqual([(r['start'],r['end']) for r in rows],[(B,B+1),(B+2,B+4)])
        self.assertEqual(reused,1)
    def test_points_validation(self):
        for points in ([B,B],[B-1],[B+256]):
            with self.subTest(points=points),self.assertRaises(ValueError):m.new_windows(self.raw('7047'),points,{})
    def test_known_literal_conflict_rejected(self):
        raw=self.raw('014870470000000044332211');node=decoder(raw,B);node['literal_value']=0
        with self.assertRaises(ValueError):m.inspect_frontier(raw,[B+1],{B:node},decoder)
    def test_old_targets_pinned(self):
        self.assertEqual(len(m.TARGETS),18);self.assertEqual(len(set(m.TARGETS)),18)
        self.assertEqual(m.TARGETS[9:12],(0x09378E2D,0x09378E2F,0x09378E31))

if __name__=='__main__':unittest.main()
