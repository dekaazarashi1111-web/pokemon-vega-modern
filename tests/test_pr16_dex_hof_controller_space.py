"""新root統合の境界だけを検証する。旧受入suiteの再走はしない。"""
import copy,json,unittest
from unittest.mock import patch
import pr16_dex_hof_controller_space as m
FIXTURE=None
class ControllerSpaceTests(unittest.TestCase):
 def setUp(self):
  if FIXTURE is None:raise RuntimeError('explicit new-scope fixture required')
  self.raw,self.latest,self.inherited,self.sources=FIXTURE
 def test_new_window_and_no_lease(self):
  regions,proof=m.measured_regions(self.raw,self.latest,self.inherited,self.sources)
  self.assertEqual(len(regions),2);self.assertFalse(proof['donor_leased']);self.assertFalse(proof['indirect_reference_completeness_claimed'])
 def test_prior_frontier_rejected(self):
  audit=copy.deepcopy(self.inherited);audit.update(classified=723,unclassified=151)
  with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,audit,self.sources)
 def test_old_unknown_kept(self):
  before=copy.deepcopy(self.inherited);m.measured_regions(self.raw,self.latest,self.inherited,self.sources);self.assertEqual(self.inherited,before)
 def test_current_whole_identity_required(self):
  audit=copy.deepcopy(self.inherited);audit['candidate']={'size':len(self.raw),'sha256':'0'*64}
  with self.assertRaises(ValueError):m.regions(self.raw,self.latest,audit,self.sources)
 def test_owner_checkpoint_candidate_required(self):
  latest=copy.deepcopy(self.latest);latest['candidate']={'size':len(self.raw),'sha256':'0'*64}
  with self.assertRaises(ValueError):m.regions(self.raw,latest,self.inherited,self.sources)
 def test_protected_new_root_roles_retained(self):
  before={(w['address'],w['size'],w['sha256'])for w in m.previous.protected_windows()};after={(w['address'],w['size'],w['sha256'])for w in m.protected_windows()};self.assertTrue(before<=after);self.assertGreater(len(after),len(before))
 def test_expected_hit_set_not_inferred(self):
  with patch.object(m,'EXPECTED_HITS',[]):
   with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,self.inherited,self.sources)
 def test_review_identity_is_independent(self):
  with patch.dict(m.REVIEWS,{m.ROOTS:{'size':1,'sha256':'0'*64}}):
   with self.assertRaises(ValueError):m.read_review(m.ROOTS)

class RootRoleBoundaryTests(unittest.TestCase):
 def test_prior_sound_payload_is_not_relabelled_as_nonaudio_root(self):
  roots=m.protected_windows()
  for a,n in((0x0846EB7C,4928),(0x084BA11C,5042),(0x084CB8A8,13022),(0x084CFFEC,6972)):
   self.assertFalse(any(a<w['address']+w['size']and w['address']<a+n for w in roots))
 def test_all_selected_animation_read_roots_are_preserved(self):
  prior=json.loads((m.ROOT/m.assets.PRIOR['path']).read_bytes());roots={(w['address'],w['size'],w['sha256'])for w in m.protected_windows()}
  selected=[w for w in prior['windows']if w['name']in m.assets.W_NAMES]+[w for w in prior['roots']if w['name']in m.assets.R_NAMES]
  self.assertEqual(len(selected),14)
  self.assertTrue(all((w['address'],w['size'],w['sha256'])in roots for w in selected))
