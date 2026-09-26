"""通常戦闘bridgeの命令移設・固定owner・限定編集の拒否契約。"""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]

class PolicyBuildContracts(unittest.TestCase):
    def test_trampoline_preserves_exact_displaced_instructions(self):
        from scripts import pr16_ring_policy_successor as b
        import struct
        code=b.trampoline(b.PROLOGUE)
        self.assertEqual(code[:8],b.PROLOGUE)
        self.assertEqual(struct.unpack('<HHI',code[8:]),(0x4B00,0x4718,(b.BEGIN+8)|1))
        self.assertEqual(len(code),16)

    def test_trampoline_rejects_instruction_drift(self):
        from scripts import pr16_ring_policy_successor as b
        for value in (b'',b.PROLOGUE[:-1],b'\0'*8,b.PROLOGUE[:2]+b'\0\0'+b.PROLOGUE[4:]):
            with self.assertRaises(ValueError):b.trampoline(value)

    def test_thumb_jump_rejects_even_outside_or_noninteger(self):
        from scripts import pr16_ring_policy_successor as b
        for value in (0,True,b.BASE,b.BASE+b.SIZE+1,0x091266F4,'0x091266f5'):
            with self.subTest(value=value),self.assertRaises(ValueError):b.jump(value)

    def test_saved_owner_bl_targets_match_original_evidence(self):
        from scripts import pr16_ring_policy_successor as b
        for address,raw,target in ((0x09126702,'e8f745f9',0x0910E990),
            (0x091268CA,'e8f76bfb',0x0910EFA4),(0x091267CA,'e8f7cffd',0x0910F36C)):
            self.assertEqual(b.decode_bl(address,bytes.fromhex(raw)),target)

    def test_invalid_bl_is_not_guessed(self):
        from scripts import pr16_ring_policy_successor as b
        for value in (b'',b'\0'*4,bytes.fromhex('e8f77047')):
            with self.assertRaises(ValueError):b.decode_bl(b.BEGIN,value)

    def test_only_entry_and_allocated_payload_change(self):
        from scripts import pr16_ring_policy_successor as b
        raw=bytearray(b'\xff'*b.SIZE);raw[b.BEGIN-b.BASE:b.BEGIN-b.BASE+8]=b.PROLOGUE;raw=bytes(raw)
        offset=b.SIZE-1024;payload=b'policy-test-payload';entry=(b.BASE+offset)|1
        new=b.patch(raw,offset,payload,entry)
        self.assertEqual(len(new),len(raw))
        self.assertEqual(new[:b.BEGIN-b.BASE],raw[:b.BEGIN-b.BASE])
        self.assertEqual(new[b.BEGIN-b.BASE+8:offset],raw[b.BEGIN-b.BASE+8:offset])
        self.assertEqual(new[offset:offset+len(payload)],payload)
        self.assertEqual(new[offset+len(payload):],raw[offset+len(payload):])
        self.assertEqual(raw[offset:offset+len(payload)],b'\xff'*len(payload))

    def test_second_patch_and_nonempty_allocation_rejected(self):
        from scripts import pr16_ring_policy_successor as b
        raw=bytearray(b'\xff'*b.SIZE);raw[b.BEGIN-b.BASE:b.BEGIN-b.BASE+8]=b.PROLOGUE;raw=bytes(raw)
        offset=b.SIZE-1024;entry=(b.BASE+offset)|1
        new=b.patch(raw,offset,b'candidate',entry)
        with self.assertRaises(ValueError):b.patch(new,offset,b'candidate',entry)
        occupied=bytearray(raw);occupied[offset]=0
        with self.assertRaises(ValueError):b.patch(bytes(occupied),offset,b'candidate',entry)

    def test_parent_identity_fails_before_owner_guessing(self):
        from scripts import pr16_ring_policy_successor as b
        with self.assertRaises(ValueError):b.verify_owners(b'not the accepted candidate')

    def test_no_gift_or_save_write_in_production_fallback(self):
        text=(ROOT/'overlays/ring_policy/ring_policy.c').read_text()
        self.assertNotIn('ConfigureNext',text)
        self.assertNotIn('FlagSet',text)
        self.assertNotIn('AddBagItem',text)
        self.assertNotIn('SaveGame',text)
        self.assertIn('CFRU_MECHANIC_MEGA',text)

class ReservedOwnerContracts(unittest.TestCase):
    def regions(self):
        return [dict(name='cfru_payload',kind='reserved',owner='CFRU-JP',
                     start='0x01000000',end_exclusive='0x01200000')]

    def test_reserved_core_is_not_an_added_allocation(self):
        from scripts import pr16_ring_policy_successor as b
        result=b.reserved_owner(self.regions(),{'allocations':[]})
        self.assertEqual(result['patch_start'],b.BEGIN-b.BASE)
        self.assertEqual(result['patch_size'],8)

    def test_wrong_owner_or_kind_fails_closed(self):
        from scripts import pr16_ring_policy_successor as b
        for key,value in (('owner','project'),('kind','allocatable'),('start','0x01100000')):
            rows=self.regions();rows[0][key]=value
            with self.assertRaises(ValueError):b.reserved_owner(rows,{'allocations':[]})
        for rows in ([],self.regions()*2):
            with self.assertRaises(ValueError):b.reserved_owner(rows,{'allocations':[]})

    def test_allocator_cannot_claim_original_function(self):
        from scripts import pr16_ring_policy_successor as b
        with self.assertRaises(ValueError):
            b.reserved_owner(self.regions(),{'allocations':[dict(start=b.BEGIN-b.BASE,end_exclusive=b.END-b.BASE)]})

if __name__=='__main__':unittest.main()
