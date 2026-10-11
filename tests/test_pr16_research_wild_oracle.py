"""New research wild receipts only. Never launch emulator or old acceptance suites."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_research_wild_oracle as m


class WildEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review = json.loads((m.PROOF / 'visual-review.json').read_text())['images']
        cls.raw = {method: (m.PROOF / (method + '.stdout.txt')).read_bytes() for method in m.METHODS}

    def reject(self, change, method='fishing'):
        rows = [json.loads(line) for line in self.raw[method].splitlines()]
        change(rows)
        with self.assertRaises(ValueError):
            m.validate(('\n'.join(json.dumps(r) for r in rows)+'\n').encode(), method, self.review[method])

    def test_fishing(self):
        self.assertEqual(m.validate(self.raw['fishing'], 'fishing', self.review['fishing'])['rp'], 4)

    def test_ecology(self):
        self.assertEqual(m.validate(self.raw['ecology'], 'ecology', self.review['ecology'])['rp'], 10)

    def test_drop_every_row(self):
        for method in m.METHODS:
            for index in range(len(self.raw[method].splitlines())):
                with self.subTest(method=method, index=index):
                    self.reject(lambda a, i=index: a.pop(i), method)

    def test_insert_duplicate_every_row(self):
        for method in m.METHODS:
            for index in range(len(self.raw[method].splitlines())):
                with self.subTest(method=method, index=index):
                    self.reject(lambda a, i=index: a.insert(i, copy.deepcopy(a[i])), method)

    def test_every_owner_byte(self):
        for method in m.METHODS:
            for index in range(64):
                def change(rows, i=index):
                    row = next(r for r in rows if r.get('stage') == 'earned' and r['kind'] == 'snapshot')
                    owner = bytearray.fromhex(row['owner']); owner[i] ^= 128
                    row['owner'] = owner.hex()
                with self.subTest(method=method, index=index):
                    self.reject(change, method)

    def test_boolean_numbers(self):
        for key in ('frame','counter','party_count','balls','generation','factory_transaction','credit_kind','typed_credit','wild_armed','result'):
            with self.subTest(key=key):
                self.reject(lambda rows, k=key: rows[0].update({k: True}))

    def test_duplicate_json_key(self):
        raw = self.raw['fishing'].replace(b'"kind":"snapshot"', b'"kind":"snapshot","kind":"snapshot"', 1)
        with self.assertRaises(ValueError): m.validate(raw, 'fishing', self.review['fishing'])

    def test_nonfinite(self):
        with self.assertRaises(ValueError): m.strict_load('{"n":NaN}')

    def test_missing_final_newline(self):
        with self.assertRaises(ValueError): m.validate(self.raw['fishing'].rstrip(), 'fishing', self.review['fishing'])

    def test_oversize(self):
        with self.assertRaises(ValueError): m.validate(b' ' * 24000, 'fishing', self.review['fishing'])

    def test_wrong_scope(self):
        with self.assertRaises(ValueError): m.validate(self.raw['fishing'], 'mining', self.review['fishing'])

    def test_screen_missing(self):
        review = dict(self.review['fishing']); review.pop(next(iter(review)))
        with self.assertRaises(ValueError): m.validate(self.raw['fishing'], 'fishing', review)

    def test_screen_unreviewed(self):
        review = dict(self.review['fishing']); review[next(iter(review))] = '0' * 64
        with self.assertRaises(ValueError): m.validate(self.raw['fishing'], 'fishing', review)

    def test_radar_retained_cursor(self):
        self.reject(lambda a: [r.update(down_presses=4) for r in a if r['kind']=='radar_menu' and r['from_mode']==4], 'ecology')

    def test_radar_mode_injected(self):
        self.reject(lambda a: [r.update(from_mode=0) for r in a if r['kind']=='radar_menu' and r['from_mode']==4], 'ecology')


def snapshot(stage):
    return lambda rows: next(r for r in rows if r['kind']=='snapshot' and r['stage']==stage)


MUTATIONS = {
    'extra_field': lambda a: a[0].update(unreviewed=True),
    'wrong_map': lambda a: a[0].update(map=[3,38,94,11]),
    'bool_map': lambda a: a[0].update(map=[True,38,94,10]),
    'wrong_credit_owner': lambda a: snapshot('earned')(a).update(credit_kind=3),
    'missing_typed_credit': lambda a: snapshot('earned')(a).update(typed_credit=0),
    'double_typed_credit': lambda a: snapshot('earned')(a).update(typed_credit=2),
    'wrong_generation': lambda a: snapshot('earned')(a).update(generation=2),
    'wrong_factory_transaction': lambda a: snapshot('earned')(a).update(factory_transaction=2),
    'missing_t24_save': lambda a: snapshot('earned')(a).update(counter=4),
    'hidden_manual_save': lambda a: snapshot('earned')(a).update(counter=6),
    'continued_save': lambda a: snapshot('continued')(a).update(counter=6),
    'escaped_save': lambda a: snapshot('escaped')(a).update(counter=3),
    'escaped_flash': lambda a: snapshot('escaped')(a).update(flash_sha256='0'*64),
    'initial_flash': lambda a: a[0].update(flash_sha256='0'*64),
    'ledger_checksum': lambda a: snapshot('earned')(a).update(checksum_valid=False),
    'ledger_masking': lambda a: snapshot('earned')(a).update(ledger_sha256='0'*64),
    'other_owner_masking': lambda a: snapshot('earned')(a).update(unrelated_ledger_sha256=a[0]['unrelated_ledger_sha256']),
    'party_loss': lambda a: snapshot('continued')(a).update(party_sha256='0'*64),
    'party_count': lambda a: snapshot('earned')(a).update(party_count=1),
    'no_ball_used': lambda a: snapshot('earned')(a).update(balls=20),
    'extra_ball_used': lambda a: snapshot('earned')(a).update(balls=18),
    'other_items_changed': lambda a: snapshot('earned')(a).update(other_inventory_sha256='0'*64),
    'continued_flash': lambda a: snapshot('continued')(a).update(flash_sha256='0'*64),
    'continued_inventory': lambda a: snapshot('continued')(a).update(inventory_sha256='0'*64),
    'owner_short': lambda a: a[0].update(owner=a[0]['owner'][:-2]),
    'owner_nonhex': lambda a: a[0].update(owner='z'*128),
    'armed_after_escape': lambda a: snapshot('escaped')(a).update(wild_armed=1),
    'wrong_result': lambda a: snapshot('earned')(a).update(result=3),
    'frame_backwards': lambda a: a[3].update(frame=0),
    'wrong_pid': lambda a: a[2].update(pid=a[2]['pid']+1),
    'wrong_species': lambda a: a[2].update(species=a[2]['species']+1),
    'prior_caught': lambda a: a[2].update(pre_caught=1),
    'wrong_activity': lambda a: a[2].update(activity=1),
    'wrong_attempt': lambda a: a[2].update(attempt=2),
    'enemy_short': lambda a: a[2].update(party=a[2]['party'][:-2]),
    'screen_order': lambda a: a[1].update(stage='earned'),
    'screen_name': lambda a: a[1].update(name='unreviewed.ppm'),
    'wrong_rom': lambda a: a[-1].update(candidate_sha256='0'*64),
    'wrong_reward': lambda a: a[-1].update(earned_rp=8),
    'wrong_save_split': lambda a: a[-1].update(transaction_saves=3),
    'wrong_total_saves': lambda a: a[-1].update(total_automatic_saves=2),
    'manual_save': lambda a: a[-1].update(manual_saves=1),
    'host_write': lambda a: a[-1].update(guarded_host_writes=1),
    'rng_injected': lambda a: a[-1].update(rng_injected=True),
    'target_injected': lambda a: a[-1].update(target_injected=True),
    'old_native_replay': lambda a: a[-1].update(accepted_case_reruns=1),
    'whole_game_promotion': lambda a: a[-1].update(all_activities_accepted=True),
    'natural_arrival_promotion': lambda a: a[-1].update(natural_arrival_accepted=True),
    'emulator_warning': lambda a: a[-1].update(warnings_errors=1),
    'summary_new_key': lambda a: a[-1].update(release_ready=True),
}
for name, mutation in MUTATIONS.items():
    def test(self, change=mutation): self.reject(change)
    setattr(WildEvidence, 'test_reject_' + name, test)

if __name__ == '__main__': unittest.main()
