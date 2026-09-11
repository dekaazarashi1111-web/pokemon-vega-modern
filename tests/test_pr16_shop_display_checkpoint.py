"""Safe retention and typed, scoped projection. Synthetic tests are not native proof."""
from copy import deepcopy
import io
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
import zipfile
import zlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_shop_display_checkpoint as m

class DisplayCheckpointTests(unittest.TestCase):
    def zipped(self,entries):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
            for name,value in entries:z.writestr(name,value)
        return out.getvalue()
    def test_safe_text_pixels_nested_source_and_named_patch(self):
        raw=b'BPS1'+b'\0'*12;raw+=struct.pack('<I',zlib.crc32(raw)&0xffffffff)
        result=m.archive(self.zipped([('sources.zip',self.zipped([('x.c',b'int x;\n')])),('screen.ppm',b'P6\n240 160\n255\n'+bytes(240*160*3)),(m.PATCHES[0],raw)]))
        self.assertEqual(len(result),3)
    def test_raw_rom_save_binary_unsafe_and_fake_image_rejected(self):
        for name,value in [('a.gba',b'a'),('a.SRM',b'a'),('a.sav',b'a'),('a.elf',b'a'),('a.txt',b'\0'),('../x',b'x'),('/x',b'x'),('a\\x',b'x'),('a.ppm',b'not pixels')]:
            with self.subTest(name=name),self.assertRaises(ValueError):m.archive(self.zipped([(name,value)]))
    def test_patch_is_not_a_general_binary_escape(self):
        for name,value in [('unrecognized.bps',b'BPS1'+bytes(16)),(m.PATCHES[0],b'BPS1'+bytes(16)),(m.PATCHES[1],b'a'*20)]:
            with self.assertRaises(ValueError):m.archive(self.zipped([(name,value)]))
    def test_symlink_nested_rom_and_expansion_limit_rejected(self):
        info=zipfile.ZipInfo('link.txt');info.external_attr=0o120777<<16;info.create_system=3
        with self.assertRaises(ValueError):m.archive(self.zipped([(info,b'target')]))
        with self.assertRaises(ValueError):m.archive(self.zipped([('nested.zip',self.zipped([('rom.gba',b'a')]))]))
        with self.assertRaises(ValueError):m.archive(self.zipped([('nested.zip',self.zipped([('big.txt',b'x'*1024)]))]),budget=[512])
    def test_records_and_review_are_pinned_to_distinct_candidates(self):
        self.assertEqual(set(m.RECORDS),{'repaired','top1'});self.assertNotEqual(m.CANDIDATE,m.prior.CANDIDATE)
        review=m.load((ROOT/m.REVIEW).read_bytes());self.assertEqual(m.identity((ROOT/m.REVIEW).read_bytes())['sha256'],m.REVIEW_SHA)
        self.assertEqual(review['top1']['status'],'REJECTED');self.assertEqual(review['repaired']['status'],'PASS')
        self.assertEqual(len(review['repaired']['images']),31)
        self.assertEqual(m.RECORDS['repaired'][0],34571394609)
    def test_projection_keeps_historical_failure_and_other_successes(self):
        receipt={'status':'SCOPED_SHOP_REPAIR_ACCEPTED_FINAL_INTEGRATION_PENDING'}
        old={'p05_route_checkpoint':{'shop_visual_acceptance':False},'physical_route_checkpoint':{'new_native_processes':15},'shared_egg_checkpoint':{'new_native_processes':16},
             'full_p06_acceptance':True,'full_p03_acceptance':False,'full_p05_acceptance':False,'full_p07_acceptance':False,'release_ready':False,
             'final_integration':{'candidate_sha256':m.prior.CANDIDATE['sha256']},
             'remaining_conditions':[{'id':'NATURAL_CAPTURE_GEAR','display_repair_required':True},{'id':'FINAL_NATIVE_ACCEPTANCE'},{'id':'PHYSICAL_CIRCUS_ADMISSION','status':'open'}]}
        original=deepcopy(old)
        with patch.object(m,'build',return_value=receipt),patch.object(m.prior,'read',return_value=m.stable(receipt)):
            new=m.project(old)
        self.assertEqual(old,original);self.assertFalse(new['p05_route_checkpoint']['shop_visual_acceptance']);self.assertTrue(new['shop_display_repair_checkpoint']['shop_visual_acceptance'])
        self.assertFalse(new['remaining_conditions'][0]['display_repair_required']);self.assertEqual(new['remaining_conditions'][2],old['remaining_conditions'][2])
        for key in ('physical_route_checkpoint','shared_egg_checkpoint','full_p06_acceptance','full_p03_acceptance','full_p05_acceptance','full_p07_acceptance','release_ready','final_integration'):self.assertEqual(new[key],old[key])
        self.assertFalse(new['next_integration_candidate']['full_candidate_regression_complete'])
    def test_saved_receipt_cannot_promote_unverified_result(self):
        with patch.object(m,'build',return_value={'release_ready':False}),patch.object(m.prior,'read',return_value=b'{"release_ready":true}'),self.assertRaises(ValueError):m.project({})
    def test_review_requires_all_nine_pages_and_post_reload_inventory(self):
        images=m.load((ROOT/m.REVIEW).read_bytes())['repaired']['images']
        for page in range(9):self.assertIn(f'pr16-shop-display-native/repaired-cancel-last-page-{page}-observation-{page+1}.ppm',images)
        for name in m.native.CASES:
            self.assertIn(f'pr16-shop-display-native/repaired-{name}-returned.ppm',images)
            if name!='missing-ring':self.assertIn(f'pr16-shop-display-native/repaired-{name}-reloaded-catalogue.ppm',images)
if __name__=='__main__':unittest.main()
