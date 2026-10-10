"""新bubbleだけの独立source・有限Thumb・拒否試験。ROM/旧suite再走なし。"""
import copy
import io
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from PIL import Image
import pr16_weather_bubble as v
import pr16_weather_bubble_sources as s
from pr16_dex_hof_callback_party import Ins, encoded


def fixture():
    """公開Cの意味から組み立てた陽性開発fixture。現ROM byteを保存しない。"""
    raw = bytearray(0x3A0000)
    def put(address, data):
        raw[address-v.BASE:address-v.BASE+len(data)] = data
    def code(at, specs):
        result = []
        for kind, args in specs:
            ins = Ins(at, kind, args)
            put(at, encoded(ins)); result.append(ins); at += ins.size
        return result
    E, L = v.ENTRY, v.LOAD
    root = code(E, [
        ('push', (16, True)), ('call', (v.FOG,)), ('literal', (0, E+0x30)),
        ('mem', (True, 'word', 0, 0, 0)), ('literal', (1, E+0x34)), ('add', (0, 0, 1)),
        ('mem', (True, 'byte', 0, 0, 0)), ('imm', ('cmp', 0, 0)), ('branch', (1, E+26)),
        ('literal', (0, E+0x38)), ('call', (L,)), ('pop', (16, True))])
    loader = code(L, [
        ('push', (48, True)), ('movhi', (4, 0)), ('mem', (True, 'half', 0, 4, 4)),
        ('shift', ('lsr', 0, 0, 5)), ('call', (v.ALLOC,)), ('shift', ('lsl', 0, 0, 16)),
        ('shift', ('asr', 5, 0, 16)), ('imm', ('cmp', 5, 0)), ('branch', (11, L+52)),
        ('mem', (True, 'half', 0, 4, 6)), ('movhi', (1, 5)), ('mem', (True, 'half', 2, 4, 4)),
        ('shift', ('lsr', 2, 2, 5)), ('call', (v.REGISTER,)), ('mem', (True, 'half', 2, 4, 4)),
        ('shift', ('lsr', 2, 2, 1)), ('mem', (True, 'word', 0, 4, 0)),
        ('shift', ('lsl', 1, 5, 5)), ('literal', (3, L+64)), ('add', (1, 1, 3)),
        ('call', (v.CPU,)), ('movhi', (0, 5)), ('pop', (48, True)),
        ('imm', ('mov', 0, 0)), ('pop', (48, True))])
    for a, value in ((E+0x30, v.WEATHER_PTR), (E+0x34, v.CREATED_OFFSET), (E+0x38, v.SHEET),
                     (L+64, v.VRAM), (v.WEATHER_PTR, 0x02018000)):
        put(a, struct.pack('<I', value))
    put(v.SHEET, struct.pack('<IHH', v.ASSET, 64, v.TAG))
    put(v.CPU, b'\x0b\xdf\x70\x47')
    tiles = s.tiles(s.load_sources()[s.PNG])
    put(v.ASSET, tiles)
    return bytes(raw), root, loader


class Sources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = s.load_sources()

    def test_fixed_full_sources(self):
        self.assertEqual(len(s.bind_sources(self.sources)), 14)

    def test_png_independent_pillow_all_indices(self):
        png = self.sources[s.PNG]
        image = Image.open(io.BytesIO(png))
        self.assertEqual(image.size, (8, 16))
        pixels = [image.getpixel((x, y)) for y in range(16) for x in range(8)]
        expected = bytes(pixels[y*8+x] | pixels[y*8+x+1] << 4 for y in range(16) for x in range(0, 8, 2))
        self.assertEqual(s.tiles(png), expected)
        self.assertEqual(s.identity(expected), s.ASSET_ID)

    def test_every_source_mutation(self):
        for name, raw in self.sources.items():
            with self.subTest(path=name):
                bad = dict(self.sources); bad[name] = raw[:-1] + bytes([raw[-1] ^ 1])
                with self.assertRaises(ValueError): s.bind_sources(bad)

    def test_closed_source_set_and_immutable_bytes(self):
        for bad in ({}, {**self.sources, 'extra': b'x'}, {**self.sources, s.PNG: bytearray(self.sources[s.PNG])}):
            with self.assertRaises(ValueError): s.bind_sources(bad)

    def test_png_suffix_crc_truncation(self):
        raw = self.sources[s.PNG]
        for bad in (raw+b'x', raw[:-1], raw[:50]+bytes([raw[50]^1])+raw[51:]):
            with self.assertRaises(ValueError): s.tiles(bad)

    def test_source_cache_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            link = Path(d)/'link'; link.symlink_to(s.CACHE, target_is_directory=True)
            with self.assertRaises(ValueError): s.load_sources(link)

    def test_source_cache_missing(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): s.load_sources(d)

    def test_target_whole_four_bytes(self):
        self.assertEqual(v.HIT-v.ASSET, 43)
        self.assertLessEqual(v.HIT+4, v.ASSET+64)


class Reader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.root, cls.loader = fixture()

    def mutate(self, address, data):
        raw = bytearray(self.raw); raw[address-v.BASE:address-v.BASE+len(data)] = data
        return bytes(raw)

    def test_source_fixture_positive(self):
        report = v.compose(self.raw)
        self.assertEqual(report['consumed_bytes'], 64)
        self.assertEqual(report['output_identity'], s.ASSET_ID)
        self.assertEqual(len(report['asset_reads']), 32)
        self.assertEqual(report['claims'], v.CLAIMS)

    def test_allocation_failure_does_not_read(self):
        report = v.compose(self.raw, tile_start=-1)
        self.assertEqual(report['consumed_bytes'], 0)
        self.assertEqual([r['target'] for r in report['calls']], [v.FOG, v.LOAD, v.ALLOC])

    def test_already_created_does_not_load(self):
        report = v.compose(self.raw, created=True)
        self.assertEqual(report['consumed_bytes'], 0)
        self.assertEqual([r['target'] for r in report['calls']], [v.FOG])

    def test_all_valid_allocation_edges(self):
        for start in (0, 1, 1021, 1022):
            with self.subTest(start=start):
                report = v.compose(self.raw, tile_start=start)
                self.assertEqual(report['events'][-1]['destination'], v.VRAM+start*32)

    def test_invalid_inputs(self):
        for kwargs in ({'tile_start': True}, {'tile_start': 1.0}, {'tile_start': -2},
                       {'tile_start': 1023}, {'created': 0}, {'invalidated': ['heap']},
                       {'contract': {}}):
            with self.assertRaises(ValueError): v.compose(self.raw, **kwargs)

    def test_every_sheet_byte_rejected(self):
        for offset in range(8):
            a=v.SHEET+offset; old=self.raw[a-v.BASE]
            with self.assertRaises(ValueError): v.compose(self.mutate(a, bytes([old^1])))

    def test_cpu_stub_all_bytes(self):
        for offset in range(4):
            a=v.CPU+offset; old=self.raw[a-v.BASE]
            with self.assertRaises(ValueError): v.compose(self.mutate(a, bytes([old^1])))

    def test_weather_pointer_bounds_alignment(self):
        for ptr in (0, 0x02018001, 0x0203FF00, v.SHEET, v.VRAM):
            with self.assertRaises(ValueError): v.compose(self.mutate(v.WEATHER_PTR, struct.pack('<I', ptr)))

    def test_bubble_flag_offset_must_match(self):
        with self.assertRaises(ValueError): v.compose(self.mutate(v.ENTRY+0x34, struct.pack('<I', v.CREATED_OFFSET+1)))

    def test_wrong_sheet_literal(self):
        with self.assertRaises(ValueError): v.compose(self.mutate(v.ENTRY+0x38, struct.pack('<I', v.SHEET+8)))

    def test_wrong_vram_literal(self):
        with self.assertRaises(ValueError): v.compose(self.mutate(v.LOAD+64, struct.pack('<I', v.VRAM+32)))

    def test_cpu_read_width_not_32bit_or_fill(self):
        op = next(i for i in self.loader if i.kind == 'shift' and i.args == ('lsr', 2, 2, 1))
        for amount in (0, 2, 3):
            data = encoded(Ins(op.address, 'shift', ('lsr', 2, 2, amount)))
            with self.assertRaises(ValueError): v.compose(self.mutate(op.address, data))

    def test_no_fog_or_unregistered_call(self):
        for target in (v.ALLOC, 0x08000000):
            data=encoded(Ins(v.ENTRY+2, 'call', (target,)))
            with self.assertRaises(ValueError): v.compose(self.mutate(v.ENTRY+2, data))

    def test_caller_saved_poison_is_not_synthetic_zero(self):
        op=next(i for i in self.loader if i.kind=='mem' and i.args==(True,'half',2,4,4) and i.address>v.LOAD+30)
        data=encoded(Ins(op.address, 'movhi', (2, 0)))
        with self.assertRaises(ValueError): v.compose(self.mutate(op.address, data))

    def test_bounded_loop(self):
        data=encoded(Ins(v.ENTRY, 'jump', (v.ENTRY,)))
        with self.assertRaises(ValueError): v.compose(self.mutate(v.ENTRY, data))

    def test_removed_or_duplicate_root_loader_call(self):
        call=next(i for i in self.root if i.kind=='call' and i.args==(v.LOAD,))
        with self.assertRaises(ValueError): v.compose(self.mutate(call.address, b'\xc0\x46'*2))
        with self.assertRaises(ValueError): v.compose(self.mutate(v.ENTRY+0x40, encoded(Ins(v.ENTRY+0x40,'call',(v.LOAD,)))))

    def test_private_identity_required_for_current_measurement(self):
        with self.assertRaises(ValueError): v.measure(self.raw, {}, {})

    def test_rom_read_outside_closed_windows(self):
        machine=v.Machine(self.raw, 0x02018000, 7, False)
        with self.assertRaises(ValueError): machine.read(v.SHEET+12, 4)
        with self.assertRaises(ValueError): machine.read(v.ASSET+64, 2)

    def test_proof_has_no_asset_byte_payload(self):
        report=v.compose(self.raw)
        encoded_report=v.canonical(report)
        self.assertNotIn(b'raw_hex', encoded_report)
        self.assertNotIn(b'base64', encoded_report)
        self.assertFalse(report['claims']['actual_bios_cpu_executed'])

if __name__ == '__main__': unittest.main()
