"""BG検査専用の人工ROM。実ROM・配布・native受入の代用ではない。"""
from copy import deepcopy
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from pr16_collection_gift_bg import geometry, BASE


def fixture():
    rom = bytearray(0x56000)
    def ptr(at, target):
        struct.pack_into('<I', rom, at, BASE + target)
    ptr(0x54b0c, 0x100); ptr(0x104, 0x200); ptr(0x20c, 0x300)
    ptr(0x300, 0x700); ptr(0x304, 0x400)
    rom[0x403] = 1; ptr(0x410, 0x500)
    struct.pack_into('<HHBBHI', rom, 0x500, 21, 3, 3, 0, 0, BASE+0x600)
    rom[0x600:0x60b] = bytes((0x6a,0x16,4,0x80,0,0,0x23)) + struct.pack('<I',BASE+0x701)
    struct.pack_into('<II',rom,0x700,32,16);ptr(0x70c,0x800)
    for i in range(32*16):struct.pack_into('<H',rom,0x800+2*i,0x3000)
    config = dict(physical_hosts=[dict(service='GIFT',map_group=1,map_num=3,x=21,y=3,elevation=3)])
    return rom, config


class CollectionBGTests(unittest.TestCase):
    def test_regressions(self):
        rom, config = fixture(); before=bytes(rom); saved=deepcopy(config)
        geo=geometry(rom,config)
        self.assertEqual((geo['event_kind'],geo['bg_event_index'],geo['x'],geo['y']),('BG_NORMAL_FIELD_A',0,21,4))
        self.assertEqual(geo['approach'],'PRE_BARRIER_ONE_TILE_UP_THEN_A_ONLY')
        self.assertEqual(geo['local_id'],0);self.assertEqual(geo['object_hex'],'')
        self.assertEqual(bytes(rom),before);self.assertEqual(config,saved)
        def p32(r, at, value):struct.pack_into('<I',r,at,value)
        def p16(r, at, value):struct.pack_into('<H',r,at,value)
        mutations = {
            'BGなし':lambda r:r.__setitem__(0x403,0),
            'イベントpointer範囲外':lambda r:p32(r,0x410,BASE+len(r)-1),
            'BGではなくNPCだけ':lambda r:(r.__setitem__(0x403,0),r.__setitem__(0x400,1),p32(r,0x404,BASE+0x500)),
            '同座標二重BG':lambda r:(r.__setitem__(0x403,2),r.__setitem__(slice(0x50c,0x518),r[0x500:0x50c])),
            '隠し道具種別':lambda r:r.__setitem__(0x505,7),
            'BG高度違い':lambda r:r.__setitem__(0x504,2),
            '予約領域不正':lambda r:r.__setitem__(0x506,1),
            '別host':lambda r:r.__setitem__(0x604,1),
            'lock欠落':lambda r:r.__setitem__(0x600,0),
            'Thumb不正':lambda r:p32(r,0x607,BASE+0x700),
            'script切詰め':lambda r:p32(r,0x508,BASE+len(r)-12),
            'map高さ不足':lambda r:p32(r,0x704,5),
            '接近点壁':lambda r:p16(r,0x800+2*(4*32+21),0x3400),
            'spawn高度違い':lambda r:p16(r,0x800+2*(5*32+21),0x2000),
            '座標衝突':lambda r:(r.__setitem__(0x402,1),p32(r,0x40c,BASE+0x680),p16(r,0x680,21),p16(r,0x682,4)),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                altered=bytearray(rom);mutate(altered)
                with self.assertRaises(ValueError):geometry(altered,config)
        bad=deepcopy(config);bad['physical_hosts'][0]['map_group']=True
        with self.assertRaises(ValueError):geometry(rom,bad)

    def test_controller_uses_a_only_after_barrier(self):
        root=Path(__file__).resolve().parents[1]
        path=root/'tools/mgba_pr16_collection_gifts.c'
        if not path.exists():self.skipTest('current HEADのCはGitHub側integrationで検査')
        source=path.read_text()
        opened=source.split('static void cf_open(struct mCore *c) {',1)[1].split('\n}',1)[0]
        self.assertNotIn('QOL_KEY_UP',opened)
        self.assertIn('cf_press(c,QOL_KEY_A,30U)',opened)
        body=source.split('cf_t.boundary=b_frames;',1)[1]
        for forbidden in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'TestGift('):
            self.assertNotIn(forbidden,body)
        self.assertEqual(source.count('a_guard(c);'),4)


if __name__ == '__main__':unittest.main()
