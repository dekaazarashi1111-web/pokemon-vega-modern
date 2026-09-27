"""2API/上余白・64byteの後処理を閉じたpatch集合として検査する。"""
import copy
import os
from pathlib import Path
import struct
import unittest
from scripts import pr16_research_shop_ui as m

class PatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=Path(os.environ['PR16_SHOP_UI_PARENT']).read_bytes()
        cls.out,cls.recipe=m.apply(cls.raw)

    def test_candidate(self):self.assertEqual(m.identity(self.out),m.CANDIDATE)
    def test_whole_reverse(self):
        reverse=[dict(offset=r['offset'],before=r['after'],after=r['before']) for r in m.patch_rows()]
        self.assertEqual(m.edit(self.out,reverse),self.raw)
    def test_change_count(self):self.assertEqual(self.recipe['changed_bytes'],71)
    def test_only_two_apis_top_and_payload(self):self.assertEqual(len(m.patch_rows()),4)
    def test_input_is_pure(self):self.assertEqual(struct.unpack_from('<I',self.out,0x13bf61c)[0],0x08110539)
    def test_existing_pixel_base_unchanged(self):self.assertEqual(self.out[0x13bf05a:0x13bf05e],bytes.fromhex('3820c046'));self.assertEqual(self.out[0x13bf1e4:0x13bf1e8],self.raw[0x13bf1e4:0x13bf1e8])
    def test_frame_preserves_r4_r5_r6_lr(self):self.assertEqual(m.CODE[:6],bytes.fromhex('70b504000d00'))
    def test_frame_returns_preserved_registers(self):self.assertEqual(m.CODE[44:48],bytes.fromhex('70bd1847'))
    def test_frame_delegates(self):self.assertEqual(struct.unpack_from('<IIII',m.CODE,48),(0x080f7fb5,0x080f89cd,0x081530e1,0x080f7f7d))
    def test_pixels_do_not_overlap_frame(self):self.assertLessEqual(0x38+21*16,0x198);self.assertLessEqual(0x198+26*4,0x214)
    def test_visible_top_border(self):self.assertEqual(self.out[0x13bf1e0:0x13bf1e4],bytes.fromhex('00080115'))
    def test_modal_hides_without_window_free(self):self.assertEqual(m.CODE[6:10],bytes.fromhex('00200021'));self.assertNotIn(bytes.fromhex('093e0008'),m.CODE)
    def test_earlier_list_unchanged(self):self.assertEqual(self.raw[0x1f4a800:0x1f4b000],self.out[0x1f4a800:0x1f4b000])
    def test_catalog_and_transactions_unchanged(self):self.assertEqual(self.raw[0x13bf9ec:0x13c0700],self.out[0x13bf9ec:0x13c0700])
    def reject(self,change):
        # A positive input check prevents vacuous rejection successes.
        self.assertEqual(m.identity(self.raw),m.PARENT)
        rows=copy.deepcopy(m.patch_rows());change(rows)
        with self.assertRaises((ValueError,KeyError,TypeError)):m.edit(self.raw,rows)
    def test_reject_overlap(self):self.reject(lambda r:r.append(r[0]))
    def test_reject_negative(self):self.reject(lambda r:r[0].update(offset=-1))
    def test_reject_outside(self):self.reject(lambda r:r[0].update(offset=len(self.raw)))
    def test_reject_resize(self):self.reject(lambda r:r[0].update(after='01'))
    def test_reject_same(self):self.reject(lambda r:r[0].update(after=r[0]['before']))
    def test_reject_wrong_before(self):self.reject(lambda r:r[0].update(before='00000000'))
    def test_reject_bool_offset(self):self.reject(lambda r:r[0].update(offset=True))
    def test_reject_reapply(self):
        self.assertEqual(m.identity(self.raw),m.PARENT)
        with self.assertRaises(ValueError):m.apply(self.out)
    def test_reject_wrong_parent(self):
        self.assertEqual(m.identity(self.raw),m.PARENT)
        with self.assertRaises(ValueError):m.apply(self.raw[:-1])

if __name__=='__main__':unittest.main()
