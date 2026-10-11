"""Save16後継専用の新しい境界テスト。旧native/受入試験は呼ばない。"""
import copy
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_story_after_maori as m

class BoundaryTests(unittest.TestCase):
    def meta(self):
        return dict(id=m.PARENT_ARTIFACT, expired=False, size_in_bytes=m.PARENT_ARCHIVE['size'],
                    digest='sha256:' + m.PARENT_ARCHIVE['sha256'],
                    workflow_run=dict(id=m.PARENT_RUN, head_sha=m.PARENT_HEAD))
    def validate(self, value):
        m.validate_archive(value, m.PARENT_ARTIFACT, m.PARENT_RUN, m.PARENT_HEAD, m.PARENT_ARCHIVE)
    def test_parent(self):
        self.validate(self.meta())
    def test_expired(self):
        v=self.meta(); v['expired']=True
        with self.assertRaises(ValueError): self.validate(v)
    def test_wrong_parent(self):
        v=self.meta(); v['id']+=1
        with self.assertRaises(ValueError): self.validate(v)
    def test_wrong_run(self):
        v=self.meta(); v['workflow_run']['id']+=1
        with self.assertRaises(ValueError): self.validate(v)
    def test_wrong_head(self):
        v=self.meta(); v['workflow_run']['head_sha']='0'*40
        with self.assertRaises(ValueError): self.validate(v)
    def test_wrong_size(self):
        v=self.meta(); v['size_in_bytes']-=1
        with self.assertRaises(ValueError): self.validate(v)
    def test_wrong_digest(self):
        v=self.meta(); v['digest']='sha256:'+'0'*64
        with self.assertRaises(ValueError): self.validate(v)
    def test_bool_pointer(self):
        with self.assertRaises(ValueError): m.pointer(b'x', True, 0)
    def test_before_rom(self):
        with self.assertRaises(ValueError): m.pointer(b'x', 0x07ffffff, 1)
    def test_overflow(self):
        with self.assertRaises(ValueError): m.pointer(b'x', 0x08000000, 2)
    def test_negative_size(self):
        with self.assertRaises(ValueError): m.pointer(b'x', 0x08000000, -1)
    def test_identity_requires_bytes(self):
        with self.assertRaises(ValueError): m.identity(bytearray(b'x'))
    def test_identity(self):
        self.assertEqual(m.identity(b'')['sha256'], 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')

class MapTests(unittest.TestCase):
    def fixture(self):
        raw=bytearray(2048)
        def put(offset, fmt, *v): struct.pack_into('<'+fmt, raw, offset, *v)
        put(0, 'I', 0x08000010); put(0x10, 'I', 0x08000020)
        put(0x20, 'IIII', 0x08000040, 0x08000080, 0, 0x08000100)
        put(0x40, 'IIII', 3, 2, 0, 0x08000060)
        put(0x60, '6H', 0, 0x400, 0, 0, 0, 0xc00)
        put(0x80, 'BBBBIIII', 1, 1, 0, 0, 0x080000a0, 0x080000c0, 0, 0)
        put(0xa0, 'B', 3); put(0xa4, 'hh', 0, 0); put(0xb0, 'I', 0x08000180)
        put(0xc0, 'hhBBBB', 1, 1, 0, 2, 4, 5)
        put(0x100, 'II', 1, 0x08000110); put(0x110, 'IiBBH', 4, -3, 3, 1, 0)
        return raw
    def test_layout_object_warp_connection(self):
        v=m.map_view(bytes(self.fixture()), 0x08000000, 0, 0)
        self.assertEqual(v['collision_grid'], ['O#.', '.W#'])
        self.assertEqual(v['objects'][0]['xy'], [0,0])
        self.assertEqual(v['warps'][0]['target_map'], [5,4])
        self.assertEqual(v['connections'][0], dict(direction=4, offset=-3, target_map=[3,1]))
        self.assertEqual(v['scope'], 'STATIC_COLLISION_ONLY_NOT_REACHABILITY_ACCEPTANCE')
    def test_dimensions_bounded(self):
        raw=self.fixture(); struct.pack_into('<I',raw,0x40,257)
        with self.assertRaises(ValueError): m.map_view(bytes(raw),0x08000000,0,0)
    def test_truncated_layout(self):
        with self.assertRaises(ValueError): m.map_view(bytes(self.fixture()[:0x65]),0x08000000,0,0)
    def test_invalid_connection(self):
        raw=self.fixture(); struct.pack_into('<I',raw,0x110,7)
        with self.assertRaises(ValueError): m.map_view(bytes(raw),0x08000000,0,0)
    def test_boolean_map(self):
        with self.assertRaises(ValueError): m.map_view(bytes(self.fixture()),0x08000000,False,0)
    def test_event_count_limit(self):
        raw=self.fixture(); raw[0x80]=65
        with self.assertRaises(ValueError): m.map_view(bytes(raw),0x08000000,0,0)

if __name__=='__main__': unittest.main()
