"""Checkpoint security and non-promotion tests; no synthetic ROM acceptance."""
from copy import deepcopy
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_p05_route_checkpoint as m

class P05CheckpointTests(unittest.TestCase):
    def zipped(self,entries):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
            for name,value in entries:z.writestr(name,value)
        return out.getvalue()
    def test_safe_utf8_nested_original_and_exact_ppm(self):
        inner=self.zipped([('source.py',b'x=1\n')]);image=b'P6\n240 160\n255\n'+bytes(240*160*3)
        outer=self.zipped([('sources.zip',inner),('view.ppm',image),('result.json',b'{}')])
        self.assertEqual(set(m.archive(outer)),{'sources.zip','view.ppm','result.json'})
    def test_rom_save_disguised_binary_and_unsafe_paths_rejected(self):
        for name,value in [('a.gba',b'a'),('a.SRM',b'a'),('a.sav',b'a'),('a.elf',b'a'),('a.txt',b'\0'),('../a.txt',b'a'),('/a.txt',b'a'),('a\\b.txt',b'a'),('a.ppm',b'not pixels')]:
            with self.subTest(name=name),self.assertRaises(ValueError):m.archive(self.zipped([(name,value)]))
    def test_symlink_rejected(self):
        info=zipfile.ZipInfo('link.txt');info.external_attr=(0o120777<<16);info.create_system=3
        with self.assertRaises(ValueError):m.archive(self.zipped([(info,b'target')]))
    def test_nested_rom_and_depth_rejected(self):
        with self.assertRaises(ValueError):m.archive(self.zipped([('nested.zip',self.zipped([('rom.gba',b'a')]))]))
        raw=self.zipped([('a.txt',b'a')])
        for _ in range(3):raw=self.zipped([('nested.zip',raw)])
        with self.assertRaises(ValueError):m.archive(raw)
    def test_aggregate_expansion_budget_is_shared(self):
        raw=self.zipped([('nested.zip',self.zipped([('large.txt',b'x'*1024)]))])
        with self.assertRaises(ValueError):m.archive(raw,budget=[512])
    def test_rejected_visual_projection_retains_existing_successes(self):
        receipt={'status':'PARTIAL_P05_DATA_PASS_DISPLAY_REPAIR_REQUIRED','shop_visual_acceptance':False}
        old={'remaining_conditions':[{'id':'NATURAL_CAPTURE_GEAR'},{'id':'PHYSICAL_CIRCUS_ADMISSION'},{'id':'P07_REMAINING_ROUTE_ACCEPTANCE','success_evidence':'retained'}],
             'physical_route_checkpoint':{'new_native_processes':15},'shared_egg_checkpoint':{'new_native_processes':16},
             'full_p03_acceptance':False,'full_p05_acceptance':False,'full_p06_acceptance':True,'full_p07_acceptance':False,'release_ready':False}
        before=deepcopy(old)
        with patch.object(m,'build',return_value=receipt),patch.object(m.prior,'read',return_value=m.prior.stable(receipt)):
            actual=m.project(old)
        self.assertEqual(old,before)
        self.assertFalse(actual['p05_route_checkpoint']['shop_visual_acceptance']);self.assertTrue(actual['p05_route_checkpoint']['shop_data_path_pass'])
        self.assertTrue(actual['remaining_conditions'][0]['display_repair_required'])
        for key in ('physical_route_checkpoint','shared_egg_checkpoint','full_p03_acceptance','full_p05_acceptance','full_p06_acceptance','full_p07_acceptance','release_ready'):self.assertEqual(actual[key],old[key])
        self.assertEqual(actual['remaining_conditions'][2],old['remaining_conditions'][2])
    def test_saved_receipt_cannot_promote_rebuilt_rejection(self):
        receipt={'shop_visual_acceptance':False}
        with patch.object(m,'build',return_value=receipt),patch.object(m.prior,'read',return_value=b'{"shop_visual_acceptance":true}'),self.assertRaises(ValueError):m.project({'remaining_conditions':[]})
    def test_originals_pin_distinct_run_heads_and_hashes(self):
        self.assertEqual(set(m.RECORDS),{'roots','shop'})
        self.assertEqual(len({r[0] for r in m.RECORDS.values()}),2)
        for r in m.RECORDS.values():self.assertEqual(len(r[3]),64);self.assertEqual(len(r[4]),40)
        self.assertEqual(m.RECORDS['shop'][0],34568373963)
if __name__=='__main__':unittest.main()
