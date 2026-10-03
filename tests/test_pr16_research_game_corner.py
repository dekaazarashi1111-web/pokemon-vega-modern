"""新規GAME_CORNERの保存原本だけを検査。ROM/native/旧受入は再実行しない。"""
from __future__ import annotations
import base64
import copy
import json
from pathlib import Path
import sys
import unittest
import zlib
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_research_game_corner as gc

E = gc.ROOT / 'content/modernization/pr16_research_game_corner_evidence'

def dumps(rows):
    return b''.join(json.dumps(row, separators=(',', ':')).encode() + b'\n' for row in rows)

class GameCornerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = gc.load((E/'projection.json').read_bytes())
        cls.encoded = b''.join((E/f'events.part{i}.txt').read_bytes() for i in (1, 2, 3))
        cls.raw = gc.unpack_text(cls.encoded, cls.meta['events'])
        cls.rows = [gc.load(x) for x in cls.raw.splitlines()]
        cls.trace = gc.validate_events(cls.raw)
        cls.cold = (E/'continue.stdout.txt').read_bytes()
        cls.coldrows = [gc.load(x) for x in cls.cold.splitlines()]

    def test_saved_events(self):
        self.assertEqual(self.trace['commands'], 1144)
        self.assertEqual(self.trace['payout'], 300)
        self.assertEqual(self.trace['rp_earned'], 3)
        self.assertEqual(self.trace['transaction_saves'], 2)
        self.assertEqual(self.trace['final_unsaved_coins'], 1188)
        self.assertEqual(self.trace, gc.load((E/'events-oracle.json').read_bytes()))

    def test_saved_continue(self):
        self.assertEqual(gc.validate_continue(self.cold, None, self.trace),
                         gc.load((E/'continue-oracle.json').read_bytes()))

    def test_original_stop_not_relabelled(self):
        rows = copy.deepcopy(self.rows); rows[-1]['status'] = 'PASS'
        with self.assertRaises(ValueError): gc.validate_events(dumps(rows))

    def test_transport_sha(self):
        self.assertEqual(gc.identity(self.encoded), self.meta['transport'])

    def test_transport_bad_digest(self):
        m = dict(self.meta['events']); m['sha256'] = '0'*64
        with self.assertRaises(ValueError): gc.unpack_text(self.encoded, m)

    def test_transport_wrong_size(self):
        for offset in (-1, 1):
            m = dict(self.meta['events']); m['size'] += offset
            with self.assertRaises(ValueError): gc.unpack_text(self.encoded, m)

    def test_transport_boolean_size(self):
        m = dict(self.meta['events']); m['size'] = True
        with self.assertRaises(ValueError): gc.unpack_text(self.encoded, m)

    def test_transport_two_streams(self):
        b = base64.b85encode(zlib.compress(self.raw) + zlib.compress(b'{}'))
        with self.assertRaises(ValueError): gc.unpack_text(b, self.meta['events'])

    def test_transport_truncated(self):
        b = base64.b85encode(zlib.compress(self.raw)[:-2])
        with self.assertRaises(ValueError): gc.unpack_text(b, self.meta['events'])

    def test_transport_bomb(self):
        b = base64.b85encode(zlib.compress(b'a'*1200001))
        with self.assertRaises(ValueError): gc.unpack_text(b, {'size':10,'sha256':'0'*64})

    def test_transport_rejects_binary(self):
        for raw in (b'\x00', b'\xff'):
            with self.assertRaises(ValueError):
                gc.unpack_text(base64.b85encode(zlib.compress(raw)), gc.identity(raw))

    def test_duplicate_json_key(self):
        with self.assertRaises(ValueError): gc.load(b'{"coins":0,"coins":1223}')

    def test_nonfinite_json(self):
        for raw in (b'{"coins":NaN}', b'{"coins":Infinity}'):
            with self.assertRaises(ValueError): gc.load(raw)

    def test_projection_scope(self):
        self.assertEqual(len(self.rows), 2295)
        self.assertEqual(self.meta['original_rows'] - len(self.rows), 1145)
        self.assertFalse(self.meta['values_rewritten'])
        self.assertTrue(self.meta['all_native_input_and_state_rows_retained'])
        self.assertFalse(self.meta['private_save_bytes_published'])

    def test_omitted_observation(self):
        with self.assertRaises(ValueError): gc.validate_events(dumps(self.rows[:100] + self.rows[101:]))

    def test_omitted_whole_group(self):
        with self.assertRaises(ValueError): gc.validate_events(dumps(self.rows[:100] + self.rows[102:]))

    def test_duplicate_group(self):
        with self.assertRaises(ValueError): gc.validate_events(dumps(self.rows[:100] + self.rows[98:]))

    def test_final_group_missing(self):
        with self.assertRaises(ValueError): gc.validate_events(dumps(self.rows[:-5] + self.rows[-3:]))

    def test_only_summary_rejected(self):
        with self.assertRaises(ValueError): gc.validate_events(dumps([self.rows[-1]]))

    def test_all_inventory_pockets(self):
        rows = copy.deepcopy(self.rows)
        for row in (rows[1], rows[-3]): row['inventory_sha256'] = '0'*64
        with self.assertRaises(ValueError): gc.validate_events(dumps(rows))

    def test_party_all_bytes(self):
        rows = copy.deepcopy(self.rows)
        for row in (rows[1], rows[-3]): row['party_sha256'] = '0'*64
        with self.assertRaises(ValueError): gc.validate_events(dumps(rows))

    def test_unrelated_owner(self):
        rows = copy.deepcopy(self.rows); rows[-2]['unrelated_ledger_sha256'] = '0'*64
        with self.assertRaises(ValueError): gc.validate_events(dumps(rows))

    def test_full_ledger_digest(self):
        rows = copy.deepcopy(self.rows); rows[-2]['ledger_sha256'] = '0'*64
        with self.assertRaises(ValueError): gc.validate_events(dumps(rows))

    def test_credit_before_payout(self):
        rows = copy.deepcopy(self.rows)
        row = next(x for x in rows if 'observation' in x and 1023 <= x['coins'] < 1223 and x['rp'] == 0)
        owner = bytes.fromhex(row['owner']); row['owner'] = gc._owner(owner[7], 'credited').hex()
        row['rp'], row['counter'] = 3, 3
        with self.assertRaises(ValueError): gc.validate_events(dumps(rows))

    def test_partial_payout_conservation(self):
        rows = copy.deepcopy(self.rows)
        row = next(x for x in rows if 'observation' in x and bytes.fromhex(x['volatile'])[25] == 1)
        row['coins'] += 1
        with self.assertRaises(ValueError): gc.validate_events(dumps(rows))

    def test_no_phase1(self):
        rows = copy.deepcopy(self.rows)
        row = next(x for x in rows if 'observation' in x and bytes.fromhex(x['owner'])[49] == 1)
        owner = bytes.fromhex(row['owner']); row['owner'] = gc._owner(owner[7], 'credited').hex()
        row['rp'], row['counter'] = 3, 3
        with self.assertRaises(ValueError): gc.validate_events(dumps(rows))

    def test_continue_no_new_earning(self):
        rows = copy.deepcopy(self.coldrows); rows[-1]['new_earning_processes'] = 1
        with self.assertRaises(ValueError): gc.validate_continue(dumps(rows), None, self.trace)

    def test_continue_flash_not_rtc_file(self):
        rows = copy.deepcopy(self.coldrows); rows[-1]['flash_sha256'] = gc.SAVE['sha256']
        with self.assertRaises(ValueError): gc.validate_continue(dumps(rows), None, self.trace)

    def test_continue_not_unsaved_end_bet(self):
        rows = copy.deepcopy(self.coldrows); rows[0]['coins'] = 1188
        with self.assertRaises(ValueError): gc.validate_continue(dumps(rows), None, self.trace)

    def test_continue_no_manual_save(self):
        rows = copy.deepcopy(self.coldrows); rows[-1]['manual_saves'] = 1
        with self.assertRaises(ValueError): gc.validate_continue(dumps(rows), None, self.trace)

    def test_continue_no_host_write(self):
        rows = copy.deepcopy(self.coldrows); rows[-1]['guarded_host_writes'] = 1
        with self.assertRaises(ValueError): gc.validate_continue(dumps(rows), None, self.trace)

    def test_continue_missing_idle(self):
        with self.assertRaises(ValueError): gc.validate_continue(dumps(self.coldrows[:4]+self.coldrows[-1:]), None, self.trace)

    def test_guard_record(self):
        rows = gc.load((E/'guard.json').read_bytes())
        self.assertEqual([x['method'] for x in rows], ['bus8','bus16','bus32','raw8','raw16','raw32','register'])
        for row in rows:
            self.assertEqual(row['returncode'], 1)
            self.assertEqual(row['stdout'], '')
            self.assertEqual(row['stderr'], 'research-save-impact: host write after observation barrier\n')

    def test_diagnostic_reachable_source_reused(self):
        original = (E/'diagnostic-source.c.txt').read_text()
        current = (gc.ROOT/gc.C).read_text()
        prefix = current.split('/* 実配当済みFlashだけ')[0]
        prefix = prefix.replace('static int gc_diagnostic_main(int argc,char**argv){', 'int main(int argc,char**argv){')
        self.assertEqual(prefix.rstrip(), original.rstrip())
        self.assertEqual(gc.identity(original.encode())['sha256'],
                         '52ce522d1ab9a5c89dbb8e6ac484a563585a07b32f4ee6d68caf8f4c5088507e')

    def test_no_previous_acceptance_promotion(self):
        for key in ('bulk_payout_native_accepted','daily_cap_native_accepted','natural_arrival_accepted','all_activities_accepted'):
            self.assertIs(self.trace[key], False)
        self.assertEqual(self.trace['accepted_case_reruns'], 0)

# 独立した64試験として各owner byteの不正変更を拒否。
def owner_test(offset):
    def test(self):
        event, ledger = copy.deepcopy(self.rows[-3:-1]); b = bytearray.fromhex(event['owner']); b[offset] ^= 0x80
        event['owner'] = b.hex()
        with self.assertRaises(ValueError): gc._event(event, ledger, None, 'credited', 4)
    return test
for _offset in range(64):
    setattr(GameCornerTests, f'test_owner_byte_{_offset:02d}_mutation', owner_test(_offset))

# 型・境界・observerのサービス偽装をそれぞれ拒否。
def observation_test(key, value):
    def test(self):
        row = copy.deepcopy(self.rows[3]); row[key] = value
        with self.assertRaises(ValueError): gc._observation(row)
    return test
for _name, _key, _value in [('bool_counter','counter',True),('bool_frame','frame',True),('negative_coins','coins',-1),
    ('overflow_coins','coins',10000),('wrong_map','map',[98,3,1,7]),('wrong_callback','callback',0),
    ('pointer_overrun','state_address',0x0203ffff),('wrong_field_type','field',1),('short_owner','owner',''),
    ('odd_hex','state','0')]:
    setattr(GameCornerTests, 'test_observation_'+_name, observation_test(_key,_value))

def volatile_test(offset):
    def test(self):
        row=copy.deepcopy(self.rows[3]); b=bytearray.fromhex(row['volatile']);b[offset]=1;row['volatile']=b.hex()
        with self.assertRaises(ValueError): gc._observation(row)
    return test
for _offset in (4,22,26,27,28,29,34,35):
    setattr(GameCornerTests, f'test_service_injection_{_offset}', volatile_test(_offset))

if __name__ == '__main__': unittest.main()
