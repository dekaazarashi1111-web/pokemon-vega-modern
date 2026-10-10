"""新しいfrontier選択/誤昇格防止の境界試験。ROM・既受入試験は使用しない。"""
import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_capacity_08397492 as m


def fixture():
    rows = [{'hit': dict(copy.deepcopy(m.HIT), address=m.TARGET-400+i*4), 'owners': []} for i in range(89)]
    rows.append({'hit': copy.deepcopy(m.HIT), 'owners': []})
    return {'candidate': copy.deepcopy(m.CANDIDATE), 'total': 90, 'owner_unknown': 0,
            'unowned_unknown': 90, 'rows': rows, 'donor_eligible': False,
            'indirect_reference_completeness_claimed': False}


class FrontierTests(unittest.TestCase):
    def test_exact_target_and_input_read_only(self):
        f = fixture(); before = m.encode(f)
        out = m.select_target(f); out['hit']['address'] = 0
        self.assertEqual(m.encode(f), before)
    def test_wrong_candidate(self):
        f=fixture();f['candidate']['sha256']='0'*64
        with self.assertRaises(ValueError):m.select_target(f)
    def test_bool_is_not_counter(self):
        f=fixture();f['owner_unknown']=False
        with self.assertRaises(ValueError):m.select_target(f)
    def test_int_is_not_acceptance_flag(self):
        f=fixture();f['rows'][0]['hit']['accepted']=0
        with self.assertRaises(ValueError):m.select_target(f)
    def test_duplicate_address(self):
        f=fixture();f['rows'][0]=copy.deepcopy(f['rows'][1])
        with self.assertRaises(ValueError):m.select_target(f)
    def test_missing_row(self):
        f=fixture();f['rows'].pop()
        with self.assertRaises(ValueError):m.select_target(f)
    def test_reordered_rows(self):
        f=fixture();f['rows'].reverse()
        with self.assertRaises(ValueError):m.select_target(f)
    def test_changed_target_digest(self):
        f=fixture();f['rows'][-1]['hit']['sha256']='0'*64
        with self.assertRaises(ValueError):m.select_target(f)
    def test_changed_target_word(self):
        f=fixture();f['rows'][-1]['hit']['target']+=1
        with self.assertRaises(ValueError):m.select_target(f)
    def test_owner_invention(self):
        f=fixture();f['rows'][-1]['owners']=['nearest-label']
        with self.assertRaises(ValueError):m.select_target(f)
    def test_claim_promotion(self):
        f=fixture();f['donor_eligible']=True
        with self.assertRaises(ValueError):m.select_target(f)
    def test_extra_hit_field(self):
        f=fixture();f['rows'][-1]['hit']['asset_size']=9999
        with self.assertRaises(ValueError):m.select_target(f)
    def test_invalid_address_type(self):
        f=fixture();f['rows'][0]['hit']['address']=True
        with self.assertRaises(ValueError):m.select_target(f)
    def test_no_new_acceptance(self):
        self.assertEqual(m.CLAIMS['newly_classified'],0)
        self.assertFalse(m.CLAIMS['formal_classification_accepted'])
        self.assertEqual(m.CLAIMS['donor_safe_bytes'],0)


class SymbolTests(unittest.TestCase):
    def fixture(self):
        return ('line\taddress\tname\tsize\n' + ''.join(f'{i}\t{m.TARGET+d:08X}\tlabel{i}\t99999\n' for i,d in enumerate((-128,-64,64,128)))).encode()
    def test_neighbors_are_only_hints(self):
        result=m.symbol_neighbors(self.fixture())
        self.assertEqual(len(result['rows']),4)
        self.assertFalse(result['neighbor_distance_is_asset_size'])
        self.assertNotIn('asset_size',result)
    def test_aliases_preserved(self):
        raw=self.fixture()+f'5\t{m.TARGET-64:08X}\talias\t1\n'.encode()
        self.assertEqual(len(m.symbol_neighbors(raw)['rows']),5)
    def test_unbound_source_rejected(self):
        with self.assertRaises(ValueError):m.bind_symbols(self.fixture())
    def test_missing_side_rejected(self):
        with self.assertRaises(ValueError):m.symbol_neighbors(self.fixture().split(b'label2')[0])
    def test_nul_rejected(self):
        with self.assertRaises(ValueError):m.symbol_neighbors(self.fixture()+b'\0')
    def test_invalid_utf8_rejected(self):
        with self.assertRaises(ValueError):m.symbol_neighbors(self.fixture()+b'\xff')
    def test_scope_expansion_rejected(self):
        with self.assertRaises(ValueError):m.symbol_neighbors(self.fixture(),m.TARGET+1)
    def test_bool_not_int(self):
        self.assertFalse(m.exact(False,0))
        self.assertFalse(m.exact({'x':[False]},{'x':[0]}))
    def test_deterministic(self):
        self.assertEqual(m.encode(m.symbol_neighbors(self.fixture())),m.encode(m.symbol_neighbors(self.fixture())))


if __name__=='__main__':unittest.main()
