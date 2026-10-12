"""実測入口32bytes・P07委譲先・共有12byte veneerの新規拒否試験。"""
import copy
import unittest
from scripts import pr16_learnset_compact_native as m


class BoundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.abi=m.s.read_json(m.ROOT/m.ABI_INPUTS)['abi']
        raw=bytearray(b'\xff'*33554432)
        for entry in cls.abi['entries'].values():
            at=entry['offset'];raw[at:at+32]=bytes.fromhex(entry['preimage'])
            if 'thumb_veneer_target' in entry:
                at=(entry['thumb_veneer_target']&~1)-m.BASE
                raw[at:at+64]=bytes.fromhex(entry['target_preimage'])
        cls.raw=bytes(raw);cls.abi=copy.deepcopy(cls.abi);cls.abi['candidate']=m.identity(cls.raw)

    def test_exact_abi(self):
        self.assertEqual(m.validate_abi(self.raw,self.abi),self.abi['entries'])
    def test_wrong_parent(self):
        abi=copy.deepcopy(self.abi);abi['candidate']['sha256']='0'*64
        with self.assertRaises(ValueError):m.validate_abi(self.raw,abi)
    def test_wrong_address(self):
        abi=copy.deepcopy(self.abi);abi['entries']['egg']['address']+=4
        with self.assertRaises(ValueError):m.validate_abi(self.raw,abi)
    def test_stale_reminder_stub(self):
        abi=copy.deepcopy(self.abi);abi['entries']['reminder']['preimage']='004b184781b25409'+abi['entries']['reminder']['preimage'][16:]
        with self.assertRaises(ValueError):m.validate_abi(self.raw,abi)
    def test_wrong_delegate(self):
        abi=copy.deepcopy(self.abi);abi['entries']['reminder']['thumb_veneer_target']-=1
        with self.assertRaises(ValueError):m.validate_abi(self.raw,abi)
    def test_shared_literal_preserved(self):
        raw=bytearray(self.raw);raw[0x10EB978]^=2;raw=bytes(raw)
        abi=copy.deepcopy(self.abi);abi['candidate']=m.identity(raw)
        abi['entries']['all_egg']['preimage']=raw[0x10EB970:0x10EB990].hex()
        with self.assertRaises(ValueError):m.validate_abi(raw,abi)


if __name__=='__main__':unittest.main()
