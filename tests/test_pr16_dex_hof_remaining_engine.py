"""同一current0641からtyped dispatch/登録callback/switchの境界を検証。"""
import pathlib,sys,json,copy,unittest
P=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
import pr16_dex_hof_remaining_engine as v
FIXTURE=None
R=review=inherited=sources=None
class CurrentEngineTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  global R,review,inherited,sources
  if FIXTURE is None:raise RuntimeError('same-current-candidate fixture must be bound by scoped Actions')
  R,review,inherited,sources=FIXTURE
 def check(self,j):return v._regions(R,inherited,j,sources)
 def test_current_six(self):self.assertEqual(len(self.check(review)[0]),6)
 def test_current_reject_wrong_candidate(self):
  with self.assertRaises(ValueError):v.regions(b'not-current',dict(inherited,candidate=review['required_candidate']),review,sources)
 def reject(self,fn):
  j=copy.deepcopy(review);fn(j)
  with self.assertRaises(ValueError):self.check(j)
 def test_wrong_root(self):self.reject(lambda j:j['rows'][0]['root'].update(special_id=347))
 def test_skipped_instruction(self):self.reject(lambda j:j['rows'][0]['instruction_path'].pop(2))
 def test_bad_branch_target(self):
  def f(j):next(r for r in j['rows'][0]['instruction_path']if 'target'in r)['target']+=2
  self.reject(f)
 def test_out_of_bound_switch(self):self.reject(lambda j:j['rows'][2]['typed_indirect_edges'][0].update(index=34))
 def test_untyped_indirect(self):self.reject(lambda j:j['rows'][2].update(typed_indirect_edges=[]))
 def test_wrong_callback(self):self.reject(lambda j:j['rows'][1]['typed_indirect_edges'][0].update(target=0x080DF1BD))
 def test_literal_as_code(self):self.reject(lambda j:j['rows'][0].update(literal_pool_included=True))
 def test_blanket_function(self):self.reject(lambda j:j['rows'][0].update(whole_function_range_classified=True))
 def test_source_hash(self):
  s=dict(sources);s['BPRJ.ld']+=b'\n'
  with self.assertRaises(ValueError):v._regions(R,inherited,review,s)
 def test_switch_pc_write_must_be_one_halfword(self):
  j=copy.deepcopy(review)
  row=next(r for r in j['rows']if any(e['kind']=='switch_edge'for e in r['typed_indirect_edges']))
  edge=next(e for e in row['typed_indirect_edges']if e['kind']=='switch_edge')
  instruction=next(p for p in row['instruction_path']if p['address']==edge['from'])
  instruction.update(size=4,sha256=v.identity(v.chunk(R,instruction['address'],4))['sha256'])
  with self.assertRaises(ValueError):self.check(j)
if __name__=='__main__':unittest.main(verbosity=2)
