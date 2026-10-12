"""Save50現残量、残経路、技選択と相手確定の新契約だけ。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save51_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[3,23],xy=[22,18],live_xy=[29,25],facing=2,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=50,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH)
    def test_parent50(self):self.assertEqual(m.a.ARTIFACT,11281112264);self.assertEqual(m.a.OUTPUT['sha256'],'b586055a74bd6b826d7ea8150e25954a9452718ad5b46e4926f0d01f9088022e')
    def test_start50(self):m.start(self.base())
    def test_reject_old_counter(self):
        o=self.base();o['save_counter']=49
        with self.assertRaises(ValueError):m.start(o)
    def test_reject_old_xy(self):
        o=self.base();o.update(xy=[33,0],live_xy=[40,7])
        with self.assertRaises(ValueError):m.start(o)
    def test_reject_wrong_facing(self):
        o=self.base();o['facing']=1
        with self.assertRaises(ValueError):m.start(o)
    def test_reject_old_party(self):
        o=self.base();o['party_sha256']=m.a.m.a.PARTY
        with self.assertRaises(ValueError):m.start(o)
    def test_reject_lock(self):
        o=self.base();o['lock']=1
        with self.assertRaises(ValueError):m.start(o)
    def test_destination51(self):
        o=self.base();o.update(map=[3,2],xy=[28,0],live_xy=[35,7],save_counter=51);m.idle(o,51)
    def test_current_pp50(self):self.assertEqual(m.PP,[11,10,15,18]);self.assertEqual(m.select([0]*4),3)
    def test_exhausted_slot(self):self.assertEqual(m.select([0,0,0,18]),0)
    def test_all_exhausted(self):
        with self.assertRaises(ValueError):m.select([11,10,15,18])
    def test_reject_old_pp_budget(self):
        with self.assertRaises(ValueError):m.select([0,0,0,19])
    def test_reject_negative(self):
        with self.assertRaises(ValueError):m.select([-1,0,0,0])
    def test_double_select_once(self):
        b=m.MoveBudget();b.selected(3,True);self.assertEqual(b.commands,[0,0,0,1]);self.assertEqual(b.pending,3)
    def test_target_not_pp_command(self):
        b=m.MoveBudget();b.selected(3,True);self.assertEqual(b.target(3),3);self.assertEqual(b.commands,[0,0,0,1]);self.assertEqual(b.targets,1);self.assertIsNone(b.pending)
    def test_single_no_target(self):
        b=m.MoveBudget();b.selected(3,False);self.assertIsNone(b.pending);self.assertEqual(b.targets,0)
    def test_target_without_selection_rejected(self):
        with self.assertRaises(ValueError):m.MoveBudget().target(3)
    def test_double_selection_rejected(self):
        b=m.MoveBudget();b.selected(3,True)
        with self.assertRaises(ValueError):b.selected(3,True)
    def test_mismatched_target_rejected(self):
        b=m.MoveBudget();b.selected(3,True)
        with self.assertRaises(ValueError):b.target(0)
    def test_three_commands_three_targets(self):
        b=m.MoveBudget()
        for _ in range(3):b.selected(3,True);b.target(3)
        self.assertEqual(b.commands,[0,0,0,3]);self.assertEqual(b.targets,3)
    def test_non_target_progress_resets_pending(self):
        b=m.MoveBudget();b.selected(3,True);b.advance();self.assertIsNone(b.pending);self.assertEqual(b.commands,[0,0,0,1])
    def test_reused_plan_only(self):
        self.assertEqual(m.PREP,'content/modernization/pr16_story_save50_evidence/inspection.json');self.assertEqual(m.START,[22,18]);self.assertEqual(m.direction([22,18],[23,18]),16)
if __name__=='__main__':unittest.main()
