"""同一current0641のmap/tileset/LZ型境界の新規反証。"""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_hof_remaining_tileset as m
FIXTURE=None
class CurrentTilesetTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('same-current-candidate fixture must be bound by scoped Actions')
  cls.raw,cls.inherited,cls.review=FIXTURE
 def reject(self,fn):
  review=copy.deepcopy(self.review);fn(review)
  with self.assertRaises(ValueError):m._regions(self.raw,self.inherited,review,ROOT)
 def test_current_one(self):self.assertEqual(len(m.regions(self.raw,self.inherited,self.review,ROOT)[0]),1)
 def test_wrong_candidate(self):
  with self.assertRaises(ValueError):m.regions(b'not-current',self.inherited,self.review,ROOT)
 def test_wrong_map(self):self.reject(lambda r:r['map'].update(number=6))
 def test_wrong_layout_id(self):self.reject(lambda r:r['map']['header'].update(layout_id=13))
 def test_wrong_compression_flag(self):self.reject(lambda r:r['tileset'].update(is_compressed=0))
 def test_changed_decoded_identity(self):self.reject(lambda r:r['asset']['decoded'].update(sha256='0'*64))
 def test_partial_encoded_extent(self):self.reject(lambda r:r['asset'].update(size=4598))
 def test_other_unknown(self):self.reject(lambda r:r['hit'].update(address=r['hit']['address']+4))
if __name__=='__main__':unittest.main()
