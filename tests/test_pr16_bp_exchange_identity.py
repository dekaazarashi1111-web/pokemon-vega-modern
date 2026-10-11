"""交換個体のread-only境界証拠。既受入のnative caseは再実行しない。"""
import copy
import json
from pathlib import Path
import sys
import unittest
sys.path[:0] = [str(Path(__file__).resolve().parents[1]/'scripts')]
import pr16_bp_exchange_identity as p

class IdentityTests(unittest.TestCase):
    def fixture(self):
        party=bytearray(600)
        for i in range(3):
            at=i*100
            for offset,size,value in [(0,4,100+i),(4,4,500+i),(0x20,2,63+i),(0x2c,2,94+i)]:
                party[at+offset:at+offset+size]=value.to_bytes(size,'little')
        battle=bytearray(88)
        for src,dst,size in [(0,0x48,4),(4,0x54,4),(0x20,0,2),(0x2c,0x0c,8)]:
            battle[dst:dst+size]=party[src:src+size]
        script=bytearray(40);script[8]=0x23;script[36]=0x5d
        e=dict(frame=10,slot=2,party=party.hex(),script_bytes=script.hex())
        base=dict(label='before-confirm',frame=10,script=0x092cf72c,native=0,callback2=0x0811f3a9,
                  battle_struct=0,count=3,active_index=0,party=party.hex(),battle_mon=battle.hex(),order='010203000000')
        samples=[base,dict(base,label='committed',frame=20,script=0x092cf68d,callback2=0x08055e75),
                 dict(base,label='transition',frame=30,script=0x092cf6a4),
                 dict(base,label='action',frame=40,script=0x092cf6a5,battle_struct=0x02017634,callback2=0x080109c1)]
        row=dict(exchange_slot=2,total_frames=40,exchange_confirm_frame=11,exchange_commit_frame=20,next_battle_action_frame=40)
        return e,samples,row
    def call(self,e,samples,row):
        raw=b'BP_IDENTITY_EXPECTED '+json.dumps(e).encode()+b'\n'
        raw+=b'\n'.join(b'BP_IDENTITY '+json.dumps(s).encode() for s in samples)
        return p.analyze(raw,row)
    def test_preserved_exact600_and_individuals(self):
        r=self.call(*self.fixture())
        for k in ('exact600_retained','all_three_individuals_retained','exchanged_individual_retained'):self.assertTrue(r[k])
        self.assertIsNone(r['first_changed']);self.assertFalse(r['native_bp_earning_accepted'])
    def test_same_species_different_pid_is_not_retention(self):
        e,s,row=self.fixture();raw=bytearray.fromhex(s[-1]['party']);raw[200]^=1;s[-1]['party']=raw.hex()
        r=self.call(e,s,row);self.assertFalse(r['exchanged_individual_retained']);self.assertFalse(r['all_three_individuals_retained'])
        self.assertEqual(r['first_changed']['frame'],40)
    def test_ot_and_moves_are_individual_components(self):
        for at in (204,232,244):
            e,s,row=self.fixture();raw=bytearray.fromhex(s[-1]['party']);raw[at]^=1;s[-1]['party']=raw.hex()
            self.assertFalse(self.call(e,s,row)['exchanged_individual_retained'])
    def test_full_bytes_and_identity_are_separate(self):
        e,s,row=self.fixture();raw=bytearray.fromhex(s[-1]['party']);raw[0x56]^=1;s[-1]['party']=raw.hex()
        r=self.call(e,s,row);self.assertFalse(r['exact600_retained']);self.assertTrue(r['all_three_individuals_retained'])
    def test_missing_duplicate_and_wrong_phase_fail(self):
        for index in (0,1,3):
            e,s,row=self.fixture();del s[index]
            with self.assertRaises(ValueError):self.call(e,s,row)
        e,s,row=self.fixture();s.insert(2,copy.deepcopy(s[1]))
        with self.assertRaises(ValueError):self.call(e,s,row)
    def test_boolean_frame_bad_hex_count_and_extra_fail(self):
        for key,value in [('frame',True),('frame',41),('count',7),('party','00'),('order','00'),('label','invented'),('extra',0)]:
            e,s,row=self.fixture();s[-1][key]=value
            with self.assertRaises(ValueError):self.call(e,s,row)
    def test_duplicate_json_and_script_abi_fail(self):
        with self.assertRaises(ValueError):p.strict('{"frame":1,"frame":1}')
        e,s,row=self.fixture();e['script_bytes']='00'*40
        with self.assertRaises(ValueError):self.call(e,s,row)
    def test_battle_individual_must_match_party(self):
        e,s,row=self.fixture();raw=bytearray.fromhex(s[-1]['battle_mon']);raw[0x48]^=1;s[-1]['battle_mon']=raw.hex()
        with self.assertRaises(ValueError):self.call(e,s,row)
    def test_ambiguous_expected_and_missing_chooser_fail(self):
        e,s,row=self.fixture();e['party']=('00'*600)
        with self.assertRaises(ValueError):self.call(e,s,row)
        e,s,row=self.fixture();s[2]['callback2']=0x08055e75
        with self.assertRaises(ValueError):self.call(e,s,row)
    def test_source_has_only_read_observers_and_preserves_parent(self):
        text=p.assemble_controller();source=(p.ROOT/p.SOURCE).read_text()
        for term in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'busWrite', 'rawWrite','setKeys','runFrame'):
            self.assertNotIn(term,source)
        self.assertIn('memcmp(expected,actual,sizeof(actual))',text)
        self.assertIn('ei_samples<512U',text);self.assertIn('b_frames-w.start<90000U',text)
        self.assertEqual(text.count('ei_begin(c,expected,w.slot)'),1)
        self.assertIn('c->setKeys(c,key);c->runFrame(c);++b_frames;ei_observe(c);',p.instrument_driver((p.ROOT/'scripts/pr16_bp_selection_native.py').read_text()))
        compile(p.instrument_driver((p.ROOT/'scripts/pr16_bp_selection_native.py').read_text()),'derived-driver','exec')
    def test_transform_anchors_fail_closed(self):
        with self.assertRaises(ValueError):p.instrument_driver('')
        with self.assertRaises(ValueError):p.replace_once('xx','x','y')

if __name__ == '__main__':unittest.main()
