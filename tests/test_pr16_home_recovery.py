"""母親fallback専用の新しい検証。既存受入caseは呼ばない。"""
import copy
import itertools
import os
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_home_recovery as m
from tools.regression import home_recovery as owner
from tools.regression import rom_runtime as runtime

class HomeRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 必須原本がない場合はSKIPや偽fixtureで通さず失敗する。
        folder=Path(os.environ['PR16_HOME_INPUTS'])
        cls.parent=(folder/'parent.gba').read_bytes()
        cls.original=(folder/'original.gba').read_bytes()
        cls.runner=(folder/'parent-runner').read_bytes()
        cls.candidate,cls.proof=m.apply(cls.parent,cls.original)

    def test_original_chain_and_previous_script(self):
        proof=m.audit(self.parent,self.original)
        self.assertEqual(proof['original_object']['script'],0x0817BCBB)
        self.assertEqual(proof['current_object']['script'],0x09220CD0)
        self.assertFalse(proof['npc_relocated'])

    def test_whole_candidate_identity(self):
        self.assertEqual(m.identity(self.candidate),dict(size=33554432,sha256='06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5'))

    def test_exact_15_changed_bytes(self):
        found=[i for i,(a,b) in enumerate(zip(self.parent,self.candidate)) if a!=b]
        expected=list(range(0x1220CF8,0x1220D02))+list(range(0x1220D17,0x1220D1C))
        self.assertEqual(found,expected)

    def test_full_rollback(self):
        reverse=[dict(offset=r['offset'],before=r['after'],after=r['before']) for r in m.rows()]
        self.assertEqual(m.edit(self.candidate,reverse),self.parent)

    def test_original_regions_unchanged(self):
        for off,size,digest in owner.REGIONS:
            self.assertEqual(self.original[off:off+size],self.candidate[off:off+size])
            self.assertEqual(m.identity(self.candidate[off:off+size])['sha256'],digest)

    def test_no_injected_heal_native_or_allocator(self):
        for row in m.rows():
            after=bytes.fromhex(row['after']);self.assertEqual(after[:5],b'\x05\xbb\xbc\x17\x08')
            self.assertFalse(any(after[5:]))
        self.assertFalse(self.proof['healing_injected'])
        self.assertFalse(self.proof['release_ready'])

    def test_gate_root_unchanged(self):
        self.assertEqual(self.parent[0x1220CD0:0x1220CF7],self.candidate[0x1220CD0:0x1220CF7])

    def test_travel_and_return_unchanged(self):
        self.assertEqual(self.parent[0x1220D1C:0x1220D47],self.candidate[0x1220D1C:0x1220D47])

    def test_original_wrong_hash_rejected(self):
        bad=bytearray(self.original);bad[0]^=1
        with self.assertRaises(ValueError):m.audit(self.parent,bytes(bad))

    def test_parent_wrong_hash_rejected(self):
        bad=bytearray(self.parent);bad[-1]^=1
        with self.assertRaises(ValueError):m.apply(bytes(bad),self.original)

    def test_reapply_rejected(self):
        with self.assertRaises(ValueError):m.apply(self.candidate,self.original)

    def test_mutable_input_rejected(self):
        with self.assertRaises(ValueError):m.apply(bytearray(self.parent),self.original)

    def test_unknown_previous_script_rejected(self):
        with self.assertRaises(ValueError):owner.original_mother_script(self.parent,owner.MOTHER+1)

    def test_previous_script_bool_rejected(self):
        with self.assertRaises(ValueError):owner.original_mother_script(self.parent,True)

    def test_wrong_mother_source_rejected(self):
        raw=bytearray(self.parent);raw[0x17BCBB]^=1
        with self.assertRaises(ValueError):owner.original_mother_script(bytes(raw),owner.MOTHER)

    def test_wrong_heal_source_rejected(self):
        raw=bytearray(self.parent);raw[0x1944F2]^=1
        with self.assertRaises(ValueError):owner.original_mother_script(bytes(raw),owner.MOTHER)

    def test_wrong_movement_source_rejected(self):
        raw=bytearray(self.parent);raw[0x194B8F]^=1
        with self.assertRaises(ValueError):owner.original_mother_script(bytes(raw),owner.MOTHER)

    def test_missing_region_rejected(self):
        with self.assertRaises(ValueError):owner.original_mother_script(self.parent[:20],owner.MOTHER)

    def test_fallback_reserved_bool_rejected(self):
        with self.assertRaises(ValueError):owner.fallback(owner.MOTHER,reserved=True)

    def test_fallback_undeclared_size_rejected(self):
        with self.assertRaises(ValueError):owner.fallback(owner.MOTHER,reserved=3)

    def test_patch_offset_bool_rejected(self):
        rows=m.rows();rows[0]['offset']=True
        with self.assertRaises(ValueError):m.edit(self.parent,rows)

    def test_patch_overlap_rejected(self):
        rows=m.rows();rows[1]['offset']=rows[0]['offset']
        with self.assertRaises(ValueError):m.edit(self.parent,rows)

    def test_patch_resize_rejected(self):
        rows=m.rows();rows[0]['after']+='00'
        with self.assertRaises(ValueError):m.edit(self.parent,rows)

    def test_patch_outside_rejected(self):
        rows=m.rows();rows[1]['offset']=len(self.parent)
        with self.assertRaises(ValueError):m.edit(self.parent,rows)

    def test_patch_preimage_rejected(self):
        rows=m.rows();rows[0]['before']='00'*10
        with self.assertRaises(ValueError):m.edit(self.parent,rows)

    def test_patch_unknown_schema_rejected(self):
        rows=m.rows();rows[0]['note']='unbound'
        with self.assertRaises(ValueError):m.edit(self.parent,rows)

    def test_patch_missing_row_rejected(self):
        with self.assertRaises(ValueError):m.edit(self.parent,m.rows()[:1])

    def test_gate_integer_flag_rejected(self):
        with self.assertRaises(ValueError):m.gate_destination(self.candidate,{0x082C:0,0x0824:False,0x114B:False},False)

    def test_gate_unknown_flag_rejected(self):
        with self.assertRaises(ValueError):m.gate_destination(self.candidate,{0x082C:False,0x0824:False,1:False},False)

    def test_gate_integer_answer_rejected(self):
        with self.assertRaises(ValueError):m.gate_destination(self.candidate,{0x082C:False,0x0824:False,0x114B:False},0)

    def test_gate_unknown_opcode_rejected(self):
        raw=bytearray(self.candidate);raw[m.PORTAL-0x8000000]=0xFE
        with self.assertRaises(ValueError):m.gate_destination(bytes(raw),{0x082C:False,0x0824:False,0x114B:False},False)

    def test_generated_candidate_definition(self):
        self.assertIn(m.CANDIDATE['sha256'].encode(),m.generate())
        self.assertNotIn(m.PARENT['sha256'].encode(),m.generate())

    def test_generated_outside_sha_unchanged(self):
        import pr16_research_story as story
        source=story.generate();actual=m.generate()
        self.assertEqual(actual.replace(m.CANDIDATE['sha256'].encode(),m.PARENT['sha256'].encode()),source)

    def test_generated_ambiguous_candidate_rejected(self):
        import pr16_research_story as story
        with patch.object(story,'generate',return_value=b'wrong'):
            with self.assertRaises(ValueError):m.generate()

    def test_canonical_generated_all_179_bytes_equal(self):
        base=0x1220C94;texts=[]
        for at in (0x1220C94,0x1220CAF,0x1220CBF):
            texts.append(self.parent[at:self.parent.index(b'\xff',at)+1])
        blob=runtime._Blob();blob.labels.update(probe=0x1220C5C-base,warp=0x1220C6C-base,back=0x1220C80-base)
        with patch.object(runtime,'_charmap',return_value=({},[])),patch.object(runtime,'_encode_text',side_effect=texts):
            runtime._script_main(ROOT,blob,'probe','warp','back',owner.MOTHER)
        actual=blob.finish(base)
        self.assertEqual(len(actual),179)
        self.assertEqual(actual,self.candidate[base:base+179])
        self.assertEqual(blob.labels['script_portal_travel']+base,0x1220D1C)

    def test_build_passes_validated_previous_script(self):
        source=(ROOT/m.BUILDER).read_text()
        self.assertIn('original_mother_script(stage, _find_portal_object(stage)[1])',source)
        self.assertIn('Vega mother local-id 1: original recovery and gated travel',source)


def make_gate(flags,answer):
    def test(self):
        destination=m.gate_destination(self.candidate,dict(zip((0x082C,0x0824,0x114B),flags)),answer)
        expected=m.TRAVEL if (flags[0] or (flags[1] and flags[2])) and answer else m.MOTHER
        self.assertEqual(destination,expected)
    return test
for bits in itertools.product((False,True),repeat=3):
    for answer in (False,True):
        name='test_gate_'+''.join(str(int(x)) for x in bits)+'_'+str(int(answer))
        setattr(HomeRecoveryTests,name,make_gate(bits,answer))

if __name__=='__main__':unittest.main()
