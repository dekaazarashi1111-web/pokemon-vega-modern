"""Save10の新証拠だけを検証。旧受入native/旧テスト群は起動しない。"""
import copy
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save10 as m

class StorySave10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if 'PR16_SAVE10_ROOT' not in os.environ:
            raise RuntimeError('PR16_SAVE10_ROOT に新区間の保存済み原本が必要。skipで成功にしない')
        cls.base=Path(os.environ['PR16_SAVE10_ROOT']);cls.pub=cls.base/'public'
        cls.raw=(cls.pub/'progress.stdout.txt').read_bytes();cls.cold_raw=(cls.pub/'continue.stdout.txt').read_bytes()
        cls.command=(cls.pub/'commands.txt').read_bytes();cls.cold_command=(cls.pub/'continue-commands.txt').read_bytes()
        cls.review=(cls.pub/'verification.json').read_bytes();cls.parent=json.loads((m.ROOT/m.PARENT).read_bytes())
        cls.before=(cls.base/'private/input.srm').read_bytes();cls.after=(cls.base/'private/training.srm').read_bytes()
        cls.cold=(cls.base/'private/cold.srm').read_bytes()
        cls.a=m.trace(cls.raw,cls.command,m.INPUT_SAVE);cls.b=m.trace(cls.cold_raw,cls.cold_command,m.OUTPUT_SAVE)
        cls.new={struct.unpack_from('<H',cls.after,off+0xff4)[0]:off for off in range(0,0xe000,0x1000)}
    def verify(self,where=None):
        return m.verify(self.raw,self.cold_raw,self.command,self.cold_command,self.parent,self.review,
                        where or self.base/'progress',self.base/'continue')
    def changed_trace(self,change):
        rows=[json.loads(x) for x in self.raw.splitlines()];change(rows)
        value=b''.join(json.dumps(x,separators=(',',':')).encode()+b'\n' for x in rows)
        with self.assertRaises(ValueError):m.trace(value,self.command,m.INPUT_SAVE)
    def changed_semantic(self,change,cold=False):
        a,b=copy.deepcopy(self.a),copy.deepcopy(self.b);change(b if cold else a)
        with self.assertRaises(ValueError):m.semantic(a,b,self.parent)
    def changed_save(self,offset,value,whole=False,rechecksum=False):
        raw=bytearray(self.after);raw[offset:offset+len(value)]=value
        if rechecksum:
            ledger=raw[0x1f064:0x1f864]
            struct.pack_into('<I',raw,0x1f064+8,m.prior.prior.prior.ledger_checksum(ledger))
        raw=bytes(raw)
        with self.assertRaises(ValueError):
            (m.saved_bytes if whole else m.save_structure)(self.before,raw,raw)
    def test_complete_new_supply_and_cold(self):
        result=self.verify();self.assertEqual(result['poke_balls'],5)
        self.assertEqual(result['screen_count'],77);self.assertEqual(result['full_image_comparisons'],12)
        self.assertTrue(result['gift_repeat_blocked_after_cold']);self.assertFalse(result['party_list_full_image_equal'])
        self.assertEqual(result['trainer_victories'],0);self.assertFalse(result['release_ready'])
    def test_decoded_save_structure_and_preservation(self):
        result=m.saved_bytes(self.before,self.after,self.cold)
        self.assertEqual(result['save_counters'],[9,10,10]);self.assertEqual(result['other_party_bytes_preserved'],599)
        self.assertEqual(result['poke_balls_after'],5);self.assertEqual(result['money_after'],2776)
        self.assertTrue(result['other_four_bag_pockets_unchanged'])
    def test_parent_rejects_wrong_acceptance(self):
        for key,value in [('status','WIP'),('actions_completion_confirmed',False),('run_id',0),
                          ('retained_artifact_id',0),('save_counter',True),('experience',451),
                          ('natural_research_arrival_accepted',True),('release_ready',True),
                          ('output_save',m.CANDIDATE),('candidate',m.INPUT_SAVE)]:
            with self.subTest(key=key):
                parent=copy.deepcopy(self.parent);parent[key]=value
                with self.assertRaises(ValueError):m.parent_boundary(parent)
    def test_review_is_immutable(self):
        with self.assertRaises(ValueError):m.review(self.review+b' ')
    def test_commands_reject_hidden_save_directive(self):
        with self.assertRaises(ValueError):m.commands(self.command.replace(b'quit\n',b'save\nquit\n'))
    def test_commands_reject_combined_key_mask(self):
        with self.assertRaises(ValueError):m.commands(self.command.replace(b'key 128 48',b'key 3 48',1))
    def test_trace_rejects_missing_observation(self):
        self.changed_trace(lambda rows:rows.pop(next(i for i,r in enumerate(rows) if r.get('observe')==4)))
    def test_trace_rejects_extra_input(self):
        self.changed_trace(lambda rows:rows.insert(-1,dict(input=218,frame=16486,key=1,frames=2)))
    def test_trace_rejects_time_rewind(self):
        self.changed_trace(lambda rows:rows[1].update(frame=1))
    def test_trace_rejects_native_guard_violations(self):
        for key,value in [('host_write_barriers',6),('guarded_host_writes',1),('fixture_calls',1),('warnings_errors',1),
                          ('natural_research_arrival_accepted',True),('inputs',True)]:
            with self.subTest(key=key):self.changed_trace(lambda rows:rows[-1].update({key:value}))
    def test_trace_rejects_wrong_seed_or_candidate(self):
        for key in ('initial_save_sha256','candidate_sha256'):
            with self.subTest(key=key):self.changed_trace(lambda rows:rows[0].update({key:'0'*64}))
    def test_trace_rejects_duplicate_json_key(self):
        raw=self.raw.replace(b'{"begin":',b'{"host_write_barriers":7,"begin":',1)
        with self.assertRaises(ValueError):m.trace(raw,self.command,m.INPUT_SAVE)
    def test_trace_rejects_missing_end_newline(self):
        with self.assertRaises(ValueError):m.trace(self.raw.rstrip(b'\n'),self.command,m.INPUT_SAVE)
    def test_semantic_rejects_ghost_victory(self):
        self.changed_semantic(lambda a:a['observations'][20].update(battle_flags=4,battle_outcome=1))
    def test_semantic_rejects_research_or_extra_map(self):
        self.changed_semantic(lambda a:a['observations'][6].update(map=[32,1]))
    def test_semantic_rejects_party_growth_or_rp(self):
        for key,value in [('party_count',2),('rp',5),('party_sha256','0'*64)]:
            with self.subTest(key=key):self.changed_semantic(lambda a:a['observations'][44].update({key:value}))
    def test_semantic_rejects_premature_save_counter(self):
        self.changed_semantic(lambda a:a['observations'][61].update(save_counter=10))
    def test_semantic_rejects_incomplete_flash(self):
        self.changed_semantic(lambda a:a['observations'][62].update(flash_sha256=m.FLASH_BEFORE))
    def test_semantic_rejects_wrong_cold_location(self):
        self.changed_semantic(lambda b:b['observations'][0].update(xy=[4,4]),cold=True)
    def test_semantic_rejects_locked_end(self):
        self.changed_semantic(lambda b:b['observations'][-1].update(lock=1),cold=True)
    def test_screen_set_rejects_missing_and_extra(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/'progress';shutil.copytree(self.base/'progress',folder)
            extra=folder/'screen-9999.ppm';extra.write_bytes((folder/'screen-0000.ppm').read_bytes())
            with self.assertRaises(ValueError):self.verify(folder)
            extra.unlink();(folder/'screen-0000.ppm').unlink()
            with self.assertRaises(ValueError):self.verify(folder)
    def test_screen_rejects_altered_quantity_pixels(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/'progress';shutil.copytree(self.base/'progress',folder)
            path=folder/'screen-0044.ppm';raw=bytearray(path.read_bytes());raw[15+(17*240+220)*3]^=1;path.write_bytes(raw)
            with self.assertRaises(ValueError):self.verify(folder)
    def test_save_rejects_length_or_cold_mismatch(self):
        with self.assertRaises(ValueError):m.saved_bytes(self.before,self.after,self.cold[:-1])
        with self.assertRaises(ValueError):m.saved_bytes(self.before,self.after,self.before)
    def test_save_rejects_sector_footer(self):
        for off,value in [(0xff4,struct.pack('<H',15)),(0xff8,b'\0'*4),(0xffc,struct.pack('<I',9))]:
            with self.subTest(offset=off):self.changed_save(off,value)
    def test_save_rejects_changed_old_bank(self):
        self.changed_save(0xe001,bytes([self.after[0xe001]^1]))
    def test_save_rejects_changed_party_attribute(self):
        self.changed_save(self.new[1]+0x38+90,b'\xff')
    def test_save_rejects_changed_ball_quantity(self):
        key=struct.unpack_from('<I',self.after,self.new[0]+0xf20)[0]&0xffff
        self.changed_save(self.new[1]+0x432,struct.pack('<H',6^key))
    def test_save_rejects_changed_ball_item(self):
        self.changed_save(self.new[1]+0x430,struct.pack('<H',1))
    def test_save_rejects_other_pocket_change(self):
        self.changed_save(self.new[1]+0x310,struct.pack('<H',13))
    def test_save_rejects_money_change(self):
        key=struct.unpack_from('<I',self.after,self.new[0]+0xf20)[0]
        self.changed_save(self.new[1]+0x290,struct.pack('<I',2777^key))
    def test_save_rejects_rechecksummed_other_ledger_owner(self):
        self.changed_save(0x1f064+0x100,bytes([self.after[0x1f064+0x100]^1]),rechecksum=True)
    def test_save_rejects_rtc_tail_change_even_if_structure_passes(self):
        self.changed_save(len(self.after)-1,bytes([self.after[-1]^1]),whole=True)

if __name__=='__main__':unittest.main()
