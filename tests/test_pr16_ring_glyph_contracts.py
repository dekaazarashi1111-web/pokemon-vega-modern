"""字形の独立期待値・明示RAM・9 LDM限定と原本境界を検証。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_glyph_contracts as t


class GlyphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes,_,cls.context=t.saved_inputs();cls.a=t.s.load(t.PRIOR)['analysis']
    def reject(self,edit):
        a=copy.deepcopy(self.a);edit(a)
        with self.assertRaises(ValueError):t.validate_inputs(self.nodes,a)
    def transfer(self):
        pc=0x08003380;n=copy.deepcopy(next(n for n in self.nodes if n['address']==pc))
        m=t.Machine([n],[(t.PIXELS,b'\x78\x56\x34\x12',False)]);m.r[2]=t.PIXELS
        return m,pc,f'未対応保存命令 {pc:08X}'
    def test_all_contracts(self):
        cases,groups=t.evaluated();self.assertEqual(groups,{'translation':64,'expand':60,'draw':480,'callback':480,'boundaries':38})
        self.assertEqual(len(cases.rows),1122);self.assertEqual(sum(r['returned']for r in cases.rows),1084)
    def test_exact_ldm_coverage(self):self.assertTrue(set(t.TRANSFERS)<=t.evaluated()[0].sites)
    def test_live_stack_budget(self):self.assertLessEqual(max(r['maximum_stack_bytes']for r in t.evaluated()[0].rows),512)
    def test_distinct_cases(self):self.assertEqual(len({r['case']for r in t.evaluated()[0].rows}),1122)
    def test_translation_extremes(self):
        self.assertEqual([t.translation_index(v)for v in(0,1,2,3,0x55,0xaa,0xff)],[0,1,2,0,40,80,0])
    def test_translation_bool(self):
        with self.assertRaises(ValueError):t.translation_index(True)
    def test_translation_negative(self):
        with self.assertRaises(ValueError):t.translation_index(-1)
    def test_translation_overflow(self):
        with self.assertRaises(ValueError):t.translation_index(256)
    def test_palette_count(self):
        with self.assertRaises(ValueError):t.palette((1,2))
    def test_palette_bool(self):
        with self.assertRaises(ValueError):t.palette((True,0,2))
    def test_palette_overflow(self):
        with self.assertRaises(ValueError):t.palette((16,0,2))
    def test_halfword_orientation(self):self.assertEqual(t.expanded_halfword(1,(7,8,9)),0x7888)
    def test_reserved_code_maps_background(self):self.assertEqual(t.expanded_halfword(255,(7,8,9)),0x8888)
    def test_space_order(self):
        _,w,image=t.glyph_model(self.a,2,0,(7,8,9));self.assertEqual(w[:3],[(t.GLYPH,1,0x88),(t.GLYPH+128,1,10),(t.GLYPH+129,1,12)])
        self.assertEqual(image,b'\x88'*128+b'\x0a\x0c');self.assertEqual(len(w),384)
    def test_unknown_glyph(self):
        with self.assertRaises(ValueError):t.glyph_model(self.a,2,2,(7,8,9))
    def test_unknown_font(self):
        with self.assertRaises(ValueError):t.glyph_model(self.a,3,1,(7,8,9))
    def test_zero_width(self):
        self.assertEqual(t.glyph_model(self.a,2,247,(7,8,9))[2][128],0)
    def test_pixel_layout(self):
        self.assertEqual([t.pixel_offset(x,y,3)for x,y in((0,0),(7,7),(8,0),(0,8),(23,23))],[0,31,32,96,287])
    def test_transparent_no_write(self):self.assertEqual(t.draw_writes(bytes(128)+b'\x0a\x0c',(0,0),(3,3),bytes(288)),[])
    def test_outside_no_write(self):self.assertEqual(t.draw_writes(b'\xff'*128+b'\x0a\x0c',(255,255),(3,3),bytes(288)),[])
    def test_clip_last_nibble(self):self.assertEqual(t.draw_writes(b'\xff'*128+b'\x0a\x0c',(23,23),(3,3),bytes(288)),[(t.PIXELS+287,1,0xf0)])
    def test_image_length(self):
        with self.assertRaises(ValueError):t.draw_writes(bytes(129),(0,0),(3,3),bytes(288))
    def test_buffer_length(self):
        with self.assertRaises(ValueError):t.draw_writes(bytes(130),(0,0),(3,3),bytes(287))
    def test_glyph_limit(self):
        with self.assertRaises(ValueError):t.draw_writes(bytes(128)+b'\x11\x0c',(0,0),(3,3),bytes(288))
    def test_ring_boundary(self):self.reject(lambda a:a.update(ring_acquisition_accepted=True))
    def test_release_boundary(self):self.reject(lambda a:a.update(release_ready=True))
    def test_font_boundary(self):self.reject(lambda a:a['selected_fonts'].pop())
    def test_glyph_boundary(self):self.reject(lambda a:a['selected_glyphs'].append(2))
    def test_translation_hash(self):self.reject(lambda a:a['glyph_translation'].update(hex='ff'*256))
    def test_translation_definition(self):
        def edit(a):a['glyph_translation'].update(hex='ff'*256,identity=t.s.identity(b'\xff'*256))
        self.reject(edit)
    def test_data_order(self):self.reject(lambda a:a['output_data'].reverse())
    def test_data_hash(self):self.reject(lambda a:a['output_data'][0]['identity'].update(size=0))
    def test_node_count(self):
        with self.assertRaises(ValueError):t.validate_inputs(self.nodes[:-1],self.a)
    def test_node_duplicate(self):
        with self.assertRaises(ValueError):t.validate_inputs([*self.nodes[:-1],self.nodes[0]],self.a)
    def test_transfer(self):
        m,pc,error=self.transfer();flags=m.flags;self.assertEqual(m.transfer_output(pc,error),pc+2)
        self.assertEqual((m.r[0],m.r[2],m.flags,m.nonstack_writes()),(0x12345678,t.PIXELS+4,flags,[]))
    def test_transfer_alignment(self):
        m,pc,error=self.transfer();m.r[2]+=1
        with self.assertRaises(ValueError):m.transfer_output(pc,error)
    def test_transfer_unmapped(self):
        m,pc,error=self.transfer();m.r[2]+=4
        with self.assertRaises(ValueError):m.transfer_output(pc,error)
    def test_transfer_opcode(self):
        m,pc,error=self.transfer();m.nodes[pc]['hex']='c046'
        with self.assertRaises(ValueError):m.transfer_output(pc,error)
    def test_transfer_error(self):
        m,pc,error=self.transfer()
        with self.assertRaises(ValueError):m.transfer_output(pc,'未map read')
    def test_transfer_site(self):
        m,pc,error=self.transfer()
        with self.assertRaises(ValueError):m.transfer_output(pc+2,error)
    def test_unwritten_stack(self):
        m,_,_=self.transfer();m.r[13]-=4
        with self.assertRaises(ValueError):m.read(m.r[13],4)
    def test_readonly_output(self):
        m,_,_=self.transfer()
        with self.assertRaises(ValueError):m.write(t.PIXELS,4,0)
    def test_canonical_inputs_unchanged(self):
        old=copy.deepcopy(self.a);t.validate_inputs(self.nodes,self.a);self.assertEqual(self.a,old)


if __name__=='__main__':unittest.main()
