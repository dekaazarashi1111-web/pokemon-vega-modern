"""初回new-gameの証拠改変/fixture混入を拒否。旧受入テストは呼ばない。"""
import json
from pathlib import Path
import re
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_research_new_game as m

def sample():
    rows=[dict(m.trace(),new_game_boot='erased-flash-input-only',settle_frames=600,initial_save_sha256=m.ERASED['sha256'])]
    for i,stage in enumerate(m.STAGES):
        b=m.initial_ledger(2);other=bytearray(b);other[4:6]=bytes(2);other[8:12]=bytes(4);other[0x73f:0x77f]=bytes(64)
        rows.extend([m.field(stage),{'event':stage,'counter':int(i>0),'item_quantity':0,'inventory_sha256':'a'*64,'other_inventory_sha256':'a'*64,'party_sha256':'b'*64,'party_count':0,'owner':b[0x73f:0x77f].hex()},
          {'ledger_event':stage,'version':2,'size':2048,'checksum_valid':True,'ledger_sha256':m.identity(b)['sha256'],'unrelated_ledger_sha256':m.identity(other)['sha256'],'migration_dirty':0,'recovery_blocked':0},
          {'flash_event':stage,'size':131072,'sha256':m.ERASED['sha256'] if not i else 'c'*64}])
    rows.append(m.result());return rows

def encode(rows):return ('\n'.join(json.dumps(r) for r in rows)+'\n').encode()

class NewGameTests(unittest.TestCase):
    def test_closed_trace_accepted(self):self.assertTrue(m.validate(encode(sample()))['normal_new_game_accepted'])
    def test_entire_source_default_ledger(self):
        b=m.initial_ledger(0);self.assertEqual(b[:8],b'VGS1\x02\0\0\x08');self.assertEqual(b[29],1);self.assertEqual(b[30],0)
        expected={0,1,2,3,4,7,8,9,10,11,29,0x73f,0x740,0x745,0x763}
        self.assertFalse({i for i,x in enumerate(b) if x}-expected);self.assertEqual(m.old.checksum(b),int.from_bytes(b[8:12],'little'))
    def test_minute_bool_rejected(self):
        with self.assertRaises(ValueError):m.initial_ledger(True)
    def test_minute_over_bound_rejected(self):
        with self.assertRaises(ValueError):m.initial_ledger(11)
    def test_erased_flash_identity(self):self.assertEqual(m.ERASED,{'size':131072,'sha256':'b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'})
    def test_normalized_trace_identity(self):self.assertEqual(m.trace(),{'trace_segments':233,'trace_frames':13490,'trace_sha256':'bd45eea1007e7e5edf8e180446618e581cdf242cf7f70ea9d799beaf6ea1e72d'})
    def test_single_main_generation(self):
        code=m.generate().decode();self.assertEqual(code.count('int main(int argc,char**argv){'),1);self.assertIn('int accepted_save_impact_main',code);self.assertIn('int accepted_lifecycle_main',code);self.assertIn(m.CANDIDATE['sha256'],code)
    def test_no_game_state_injection_calls(self):
        own=(ROOT/m.C).read_text();forbidden=r'\b(call_preserving|qol_call5_preserving|si_call|si_transaction|lc_fixture|write8|write32_bytes|write_register|si_write16|si_restore|qol_run_field_trace|qol_prepare_loaded_field)\s*\('
        self.assertIsNone(re.search(forbidden,own));self.assertEqual(own.count('si_guard(c);'),2)
    def test_short_trace_rejected(self):
        with self.assertRaises(ValueError):m.trace('static const struct Segment BOOT_TRACE[] = {{1,0}};')
    def test_unknown_trace_syntax_rejected(self):
        with self.assertRaises(ValueError):m.trace((ROOT/m.TRACE).read_text().replace('{600, 0}', 'EVAL(600)',1))
    def test_unknown_key_rejected(self):
        with self.assertRaises(ValueError):m.trace((ROOT/m.TRACE).read_text().replace('{600, 0}', '{600, 1024}',1))
    def test_duplicate_json_rejected(self):
        raw=encode(sample()).replace(b'"manual_saves": 1',b'"manual_saves": 1, "manual_saves": 1')
        with self.assertRaises(ValueError):m.validate(raw)

MUTATIONS={
 'missing_row':lambda r:r.pop(5),
 'extra_row':lambda r:r.append(r[-1]),
 'out_of_order':lambda r:r.reverse(),
 'wrong_erased_input':lambda r:r[0].update(initial_save_sha256='0'*64),
 'wrong_trace':lambda r:r[0].update(trace_sha256='0'*64),
 'wrong_frame_total':lambda r:r[0].update(trace_frames=13491),
 'wrong_extent':lambda r:r[0].update(trace_segments=234),
 'fixture_boot':lambda r:r[0].update(new_game_boot='seed-continue'),
 'wrong_candidate':lambda r:r[-1].update(candidate_sha256='0'*64),
 'starter_overclaim':lambda r:r[-1].update(starter_acquisition_accepted=True),
 'supply_overclaim':lambda r:r[-1].update(research_natural_supply_accepted=True),
 'fixture_call':lambda r:r[-1].update(fixture_calls=1),
 'ram_write':lambda r:r[-1].update(ram_fixture_writes=1),
 'register_write':lambda r:r[-1].update(register_fixture_writes=1),
 'speed_write':lambda r:r[-1].update(text_speed_writes=1),
 'missing_guard':lambda r:r[-1].update(host_write_barriers=6),
 'guarded_write':lambda r:r[-1].update(guarded_host_writes=1),
 'missing_core':lambda r:r[-1].update(fresh_cores=2),
 'warning':lambda r:r[-1].update(warnings_errors=1),
 'wrong_spawn':lambda r:r[1].update(map_group=98),
 'inactive_player':lambda r:r[1].update(player_active=False),
 'locked_field':lambda r:r[1].update(script_locked=True),
 'bool_counter':lambda r:r[2].update(counter=False),
 'hidden_intro_save':lambda r:r[2].update(counter=1),
 'party_injection':lambda r:r[2].update(party_count=1),
 'item_injection':lambda r:r[2].update(item_quantity=5),
 'owner_earning':lambda r:r[6].update(owner='00'*64),
 'other_ledger_change':lambda r:r[7].update(unrelated_ledger_sha256='0'*64),
 'forged_ledger':lambda r:r[7].update(ledger_sha256='0'*64),
 'invalid_checksum':lambda r:r[7].update(checksum_valid=False),
 'recovery_blocked':lambda r:r[7].update(recovery_blocked=1),
 'continue_extra_save':lambda r:r[10].update(counter=2),
 'bag_changed':lambda r:r[10].update(inventory_sha256='d'*64),
 'party_changed':lambda r:r[14].update(party_sha256='d'*64),
 'intro_flash_written':lambda r:r[4].update(sha256='d'*64),
 'first_save_absent':lambda r:r[8].update(sha256=m.ERASED['sha256']),
 'continue_flash_written':lambda r:r[12].update(sha256='d'*64),
 'second_continue_flash_written':lambda r:r[16].update(sha256='d'*64),
 'flash_wrong_size':lambda r:r[16].update(size=131088),
 'extra_ledger_key':lambda r:r[15].update(ignored=True),
}
for name,mutate in MUTATIONS.items():
    def check(self,mutate=mutate):
        rows=sample();mutate(rows)
        with self.assertRaises((ValueError,KeyError,TypeError)):m.validate(encode(rows))
    setattr(NewGameTests,'test_reject_'+name,check)
if __name__=='__main__':unittest.main()
