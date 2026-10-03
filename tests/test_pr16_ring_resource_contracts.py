"""新規resource期待値・予約と実転送の区別・有限allocationの拒否条件。"""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_resource_contracts as f
TABLE=bytes(32)


class InputTests(unittest.TestCase):
    def test_uint_bool(self):
        with self.assertRaises(ValueError):f.uint(True,8,'x')
    def test_uint_negative(self):
        with self.assertRaises(ValueError):f.uint(-1,32,'x')
    def test_uint_upper(self):
        with self.assertRaises(ValueError):f.uint(256,8,'x')
    def test_uint_boundary(self):self.assertEqual(f.uint(65535,16,'x'),65535)
    def test_flags_short(self):
        with self.assertRaises(ValueError):f.attribute(0,1,b'\1')
    def test_flags_mutable(self):
        with self.assertRaises(ValueError):f.attribute(0,1,bytearray(2))
    def test_invalid_id(self):self.assertEqual(f.attribute(4,1,b'\xff\xff'),255)
    def test_masked_id(self):self.assertEqual(f.attribute(256,1,b'\1\0'),1)
    def test_masked_selector(self):self.assertEqual(f.attribute(0,257,b'\1\0'),1)
    def test_disabled(self):self.assertEqual(f.attribute(0,2,b'\0\xff'),255)
    def test_selector_zero(self):self.assertEqual(f.attribute(0,0,b'\xff\xff'),255)
    def test_selector_nine(self):self.assertEqual(f.attribute(0,9,b'\xff\xff'),255)
    def test_selectors(self):self.assertEqual([f.attribute(0,i,b'\xfd\xeb')for i in range(1,9)],[1,3,26,3,1,3,1,1])
    def test_short_table(self):
        with self.assertRaises(ValueError):f.fixture(TABLE[:-1])
    def test_invalid_dimension(self):
        with self.assertRaises(ValueError):f.fixture(TABLE,dims=(256,1))
    def test_invalid_pointer(self):
        with self.assertRaises(ValueError):f.fixture(TABLE,pointer=1<<32)
    def test_invalid_queue_member(self):
        with self.assertRaises(ValueError):f.queue_image([128])
    def test_bool_queue_member(self):
        with self.assertRaises(ValueError):f.queue_image([True])
    def test_queue_size(self):self.assertEqual(len(f.queue_image()),2048)
    def test_queue_occupied(self):self.assertEqual(f.queue_image([127])[2040:2042],b'\1\0')


class ExpectedTests(unittest.TestCase):
    def model(self,**kwargs):return f.Expected(f.fixture(TABLE,**kwargs)['segments'])
    def test_alias(self):
        with self.assertRaises(ValueError):f.Expected([(0,b'x',True),(0,b'y',True)])
    def test_missing(self):
        with self.assertRaises(ValueError):self.model().read(0,1)
    def test_unmapped_write(self):
        with self.assertRaises(ValueError):self.model().write(0,1,0)
    def test_exact_queue_order(self):
        e=self.model();self.assertEqual(e.queue(3,5,32,0),0)
        self.assertEqual(e.writes,[(f.LOCK,1,1),(f.QBASE,4,3),(f.QBASE+4,4,5),
            (f.QBASE+8,2,32),(f.QBASE+10,2,3),(f.LOCK,1,0)])
    def test_queue_mode1(self):
        e=self.model();e.queue(0,0,1,1);self.assertEqual(e.read(f.QBASE+10,2),1)
    def test_queue_length_truncate(self):
        e=self.model();e.queue(0,0,65537,0);self.assertEqual(e.read(f.QBASE+8,2),1)
    def test_queue_wrap(self):self.assertEqual(self.model(head=127,occupied=[127]).queue(0,0,1,0),0)
    def test_queue_last_free(self):self.assertEqual(self.model(head=1,occupied=list(range(1,128))).queue(0,0,1,0),0)
    def test_queue_full(self):
        e=self.model(occupied=list(range(128)));self.assertEqual(e.queue(0,0,1,0),0xffffffff)
        self.assertEqual(e.writes,[(f.LOCK,1,1),(f.LOCK,1,0)])
    def test_queue_zero_reused(self):
        e=self.model();self.assertEqual(e.queue(0,0,0,0),0);self.assertEqual(e.queue(1,1,2,0),0)
    def test_queue_no_payload_access(self):self.assertEqual(self.model().queue(0xffffffff,0,1,0),0)
    def test_transfer_vram_wrap(self):
        e=self.model(flags=b'\1\3');self.assertEqual(e.transfer(0,0,1,65535,1),0)
        self.assertEqual(e.reservations[0]['destination'],0x0600bfff)
    def test_transfer_screen_base_31(self):
        e=self.model(flags=b'\1\x7c');e.transfer(0,0,1,0,2)
        self.assertEqual(e.reservations[0]['destination'],0x0600f800)
    def test_transfer_invalid_mode(self):
        e=self.model();self.assertEqual(e.transfer(0,0,1,0,0),255);self.assertEqual(e.writes,[])
    def test_transfer_disabled(self):
        e=self.model(flags=b'\0\0');self.assertEqual(e.transfer(0,0,1,0,1),255)
    def test_transfer_invalid_id(self):self.assertEqual(self.model().transfer(255,0,1,0,1),255)
    def test_display_dimension(self):self.assertEqual(f.size_for_copy(0,b'\x0d\0',0),8192)
    def test_display_affine(self):self.assertEqual(f.size_for_copy(2,b'\x0d\0',2),16384)
    def test_display_invalid(self):self.assertEqual(f.size_for_copy(3,b'\x0d\0',1),0)
    def test_record_length_wrap(self):
        e=self.model(dims=(255,255));e.resource(0,2)
        self.assertEqual(e.reservations[0]['length'],49184)
    def test_pointer_null_skips(self):
        e=self.model(pointer=0);e.resource(0,1);self.assertEqual(e.writes,[])
    def test_pointer_upper_skips(self):
        e=self.model(pointer=0x03008001);e.resource(0,1);self.assertEqual(e.writes,[])
    def test_pointer_unaligned_queues(self):
        e=self.model(pointer=1);e.resource(0,1);self.assertEqual(e.reservations[0]['source'],1)
    def test_record_mode3_two_reservations(self):
        e=self.model();self.assertEqual(e.resource(0,3),f.vm.RETURN);self.assertEqual([r['index']for r in e.reservations],[0,1])
    def test_record_zero_same_slot(self):
        e=self.model(dims=(0,0));e.resource(0,3);self.assertEqual([r['index']for r in e.reservations],[0,0])
    def test_record_mask(self):
        e=self.model(head=127);e.resource(0,2);self.assertEqual(e.read(f.MASK+12,4),0x80000000)


class BitmapTests(unittest.TestCase):
    def test_short(self):
        with self.assertRaises(ValueError):f.bitmap_search(b'',0,2)
    def test_zero(self):self.assertEqual(f.bitmap_search(bytes(256),0,0),0xffffffff)
    def test_one(self):self.assertEqual(f.bitmap_search(bytes(256),0,1),0xffffffff)
    def test_two(self):self.assertEqual(f.bitmap_search(bytes(256),0,2),0)
    def test_full(self):self.assertEqual(f.bitmap_search(b'\xff'*256,0,2),0xffffffff)
    def test_alternating(self):self.assertEqual(f.bitmap_search(b'\xaa'*256,0,2),0xffffffff)
    def test_last_bank_limit(self):self.assertEqual(f.bitmap_search(bytes(256),3,513),0xffffffff)
    def test_last_bank_exact(self):self.assertEqual(f.bitmap_search(bytes(256),3,512),0)
    def test_first_free(self):self.assertEqual(f.bitmap_search(b'\xff'*10+bytes(246),0,2),80)
    def test_set_order(self):
        e=f.Expected(f.fixture(TABLE)['segments']);e.bitmap(0,7,2,1)
        self.assertEqual(e.writes,[(f.BITS,1,128),(f.BITS+1,1,1)])
    def test_clear_order(self):
        e=f.Expected(f.fixture(TABLE,bitmap=b'\xff'*256)['segments']);e.bitmap(0,7,2,2)
        self.assertEqual(e.writes,[(f.BITS,1,127),(f.BITS+1,1,254)])
    def test_allocation_failure(self):
        e=f.Expected(f.fixture(TABLE,flags=b'\1\3')['segments'])
        with self.assertRaises(ValueError):e.bitmap(0,511,2,1)
    def test_mode_noop(self):
        e=f.Expected(f.fixture(TABLE)['segments']);self.assertEqual(e.bitmap(255,0xffffffff,0xffffffff,3),0);self.assertEqual(e.writes,[])


if __name__=='__main__':unittest.main()
