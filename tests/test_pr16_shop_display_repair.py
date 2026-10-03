"""Synthetic bounds/observer contracts, not visual or emulator acceptance."""
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_shop_display_native as m

class ShopDisplayRepairTests(unittest.TestCase):
    SHA='a'*64
    def sample(self,name,control=False):
        row=m.expected(name,self.SHA,control);row['total_frames']=10000
        row['witness']={k:(i+1)*100 for i,k in enumerate(m.shop.TRACE)}
        if name=='missing-ring':
            for key in ('menu','selection','revisit'):row['witness'][key]=0
        row['graphics']=dict(world_captures=2,world_checks=2 if name=='missing-ring' else row['pages']+5,
                             world_difference_bytes=100 if control else 0,layout_checks=0 if name=='missing-ring' else row['pages']+2,invalid_layouts=1 if control else 0)
        return row
    def check(self,row,name,control=False,code=0):return m.validate(json.dumps(row).encode(),name,code,self.SHA,control)
    def test_repaired_content_fits_below_message_frame_and_world(self):
        result=m.repair.validate_geometry(m.repair.GEOMETRY)
        self.assertEqual(result['content_bytes'],[0x8020,0xAA20]);self.assertEqual(result['content_tiles'],[1,337]);self.assertFalse(result['world_and_frame_overlap'])
        old_start=0x8000+532*32;old_end=old_start+21*16*32
        self.assertEqual((old_start,old_end),(0xC280,0xEC80));self.assertLess(old_start,0xE000);self.assertGreater(old_end,0xE000)
    def test_wrong_banks_dimensions_borders_or_boolean_numbers_rejected(self):
        for key,value in [('content_base_tile',532),('top',0),('top',True),('width',22),('height',17),('world_tilemaps',[0xD000,0xF800]),('message_tiles',[1,400]),('frame_tiles',[300,309])]:
            with self.subTest(key=key),self.assertRaises(ValueError):m.repair.validate_geometry(dict(m.repair.GEOMETRY,**{key:value}))
    def test_only_two_source_fields_change(self):
        original=(ROOT/m.probe.OVERLAY).read_text();changed=original
        for before,after in m.repair.CHANGES:self.assertEqual(changed.count(before),1);changed=changed.replace(before,after,1)
        self.assertEqual(len(m.repair.CHANGES),2)
        for before,after in reversed(m.repair.CHANGES):changed=changed.replace(after,before,1)
        self.assertEqual(changed,original)
    def test_eleven_cases_and_last_page_cancellation_are_exact(self):
        self.assertEqual(len(m.CASES),11);self.assertEqual(m.CASES['cancel-last'],(1043,2));self.assertEqual(len(m.CONTROLS),3)
        last=self.sample('cancel-last');self.assertEqual((last['pages'],last['result'],last['quantity'],last['graphics']['layout_checks']),(8,2,0,10))
        for name in m.CASES:self.assertEqual(self.check(self.sample(name),name),self.sample(name))
    def test_fresh_original_controls_must_reproduce_both_failures(self):
        for name in m.CONTROLS:
            self.check(self.sample(name,True),name,True)
            for key in ('world_difference_bytes','invalid_layouts'):
                bad=self.sample(name,True);bad['graphics'][key]=0
                with self.subTest(name=name,key=key),self.assertRaises(ValueError):self.check(bad,name,True)
    def test_repaired_world_damage_or_overlap_never_passes(self):
        for name in m.CASES:
            for key in ('world_difference_bytes','invalid_layouts'):
                row=self.sample(name);row['graphics'][key]=1
                with self.subTest(name=name,key=key),self.assertRaises(ValueError):self.check(row,name)
    def test_every_page_both_cores_and_cancellation_observations_required(self):
        for name in m.CASES:
            for key in ('world_captures','world_checks','layout_checks'):
                row=self.sample(name);row['graphics'][key]+=1
                with self.subTest(name=name,key=key),self.assertRaises(ValueError):self.check(row,name)
    def test_graphics_boolean_extra_or_missing_fields_rejected(self):
        row=self.sample('cancel-last');row['graphics']['world_difference_bytes']=False
        with self.assertRaises(ValueError):self.check(row,'cancel-last')
        row=self.sample('cancel-last');row['graphics']['extra']=0
        with self.assertRaises(ValueError):self.check(row,'cancel-last')
        row=self.sample('cancel-last');del row['graphics']['world_checks']
        with self.assertRaises(ValueError):self.check(row,'cancel-last')
    def test_data_and_physical_order_checks_still_required(self):
        for key,value in [('rom_sha256','b'*64),('scope',m.CONTROL_SCOPE),('quantity',1),('pages',7),('full_p05_acceptance',True),('release_ready',True)]:
            row=self.sample('cancel-last');row[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.check(row,'cancel-last')
        row=self.sample('cancel-last');row['witness']['saved']=row['witness']['returned']
        with self.assertRaises(ValueError):self.check(row,'cancel-last')
    def test_controller_only_observes_graphics_and_preserves_barrier(self):
        text=m.controller(self.SHA);after=text.split('/* The only actions after this boundary are physical input and reads. */',1)[1]
        for forbidden in ('call_preserving(', 'write8(', 'write16(', 'write32(', 'set_mon_data_u32('):self.assertNotIn(forbidden,after);self.assertNotIn(forbidden,m.GRAPHICS_C)
        self.assertIn('b_copy(c,0x0600E000U',m.GRAPHICS_C);self.assertIn('d_check_world(c);d_check_layout(c);',text)
        self.assertIn('{"cancel-last",1043,2}',text);self.assertIn('d_capture_world(c);d_check_world(c);',after)
        self.assertIn('page-%u-observation-%u',m.GRAPHICS_C)
    def test_control_labels_are_distinct_and_source_remains_immutable(self):
        path=ROOT/m.shop.SOURCE;before=path.read_bytes();control=m.controller(self.SHA,True);repaired=m.controller(self.SHA,False)
        self.assertIn(m.CONTROL_SCOPE,control);self.assertNotIn(m.SCOPE,control);self.assertIn(m.SCOPE,repaired);self.assertEqual(path.read_bytes(),before)
    def test_exit_type_and_unknown_control_case_rejected(self):
        for code in (False,0.0,None,1):
            with self.assertRaises(ValueError):self.check(self.sample('eelektross'),'eelektross',code=code)
        with self.assertRaises(ValueError):m.expected('missing-ring',self.SHA,True)
        with self.assertRaises(ValueError):m.expected('unknown',self.SHA,False)
if __name__=='__main__':unittest.main()
