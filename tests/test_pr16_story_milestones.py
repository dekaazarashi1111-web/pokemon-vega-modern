"""新規milestone制御のみ。旧native再走なし。"""
import copy,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from pr16_story_milestones import MilestoneEpisode,DiagnosticStop

def contract():return dict(schema_version=1,id='TEST_FACILITY',kind='important_facility',reason_ja='重要施設到着',origin=dict(map=[3,24],xy=[53,13]),endpoint=dict(map=[35,0],xy=[5,5],facing=2),ordinary_battle_checkpoint=False,diagnostic_stop_is_milestone=False,owner_plan='docs/PR16_STORY_ACCELERATED_ACCEPTANCE_PLAN_JA.md',resource_floor=dict(hp=10,usable_pp=3),max_battles=4,allowed_battles={'ordinary_single_wild':dict(owner='FIXED_ROM_WILD_OWNER',callbacks=[20],battle_flags=[0],field_battle_flags=[0],field_callback=10,outcomes=[1],story_effects=[],max_decisions=6,ui_inputs={'moves':dict(callbacks=[20],keys=[1]),'dialogue':dict(callbacks=[20],keys=[1]),'animation':dict(callbacks=[20],keys=[0])})})
def field():return dict(map=[3,24],xy=[53,13],lock=0,callback2=10,battle_flags=0,battle_outcome=0)
def battle():return dict(field(),callback2=20)
def resource():return dict(hp=277,pp=[3,9,8,2])
def evidence():return dict(field_return=True,owners_resolved=True,observation_match=True,resources=dict(hp=274,pp=[3,9,7,2]),owner='FIXED_ROM_WILD_OWNER',story_effects=[])
class Continuation(unittest.TestCase):
    def episode(self):e=MilestoneEpisode(contract());e.begin(field());return e
    def enter(self,e=None):e=e or self.episode();e.enter_battle(battle(),'ordinary_single_wild','FIXED_ROM_WILD_OWNER',resource(),1);return e
    def test_two_battles_continue_without_save(self):
        e=self.episode()
        for n in range(2):
            r=resource()if n==0 else dict(hp=274,pp=[3,9,7,2]);v=evidence();v['resources']=dict(hp=270,pp=[3,9,6,2])if n else v['resources']
            e.enter_battle(battle(),'ordinary_single_wild','FIXED_ROM_WILD_OWNER',r,1+n*3);self.assertEqual(e.input_for(battle(),'moves',1+n*3),[1]);row=e.finish_battle(dict(field(),battle_outcome=1),v,2+n*3)
            self.assertEqual(row['continuation'],'CONTINUE_TO_DECLARED_MILESTONE');self.assertFalse(row['save_requested']);self.assertFalse(e.reached)
        result=e.reach(dict(field(),map=[35,0],xy=[5,5],facing=2),evidence(),8);self.assertTrue(result['ordinary_save_authorized']);self.assertEqual(result['battles'],2);self.assertEqual([r['pp_used']for r in e.ledger],[[0,0,1,0]]*2)
    def test_no_battle_endpoint(self):e=self.episode();self.assertTrue(e.reach(dict(field(),map=[35,0],xy=[5,5],facing=2),evidence(),1)['ordinary_save_authorized'])
    def test_unknown_ui_no_input(self):
        e=self.enter()
        with self.assertRaises(DiagnosticStop):e.input_for(battle(),'unknown',1)
        self.assertEqual(e.active['decisions'],0)
    def test_unknown_callback_no_input(self):
        e=self.enter()
        with self.assertRaises(DiagnosticStop):e.input_for(dict(battle(),callback2=999),'moves',1)
        self.assertEqual(e.active['decisions'],0)
    def test_nested_battle(self):
        e=self.enter()
        with self.assertRaises(DiagnosticStop):self.enter(e)
    def test_endpoint_during_battle(self):
        with self.assertRaises(DiagnosticStop):self.enter().reach(dict(field(),map=[35,0],xy=[5,5],facing=2),evidence(),3)
    def test_resource_before_battle(self):
        for r in[dict(hp=0,pp=[3]*4),dict(hp=100,pp=[0]*4),{},dict(hp=100,pp=[-1,9,8,2])]:
            e=self.episode()
            with self.assertRaises(DiagnosticStop):e.enter_battle(battle(),'ordinary_single_wild','FIXED_ROM_WILD_OWNER',r,1)
            self.assertEqual(e.ledger,[]);self.assertIsNone(e.active)
    def test_unknown_type(self):
        with self.assertRaises(DiagnosticStop):self.episode().enter_battle(battle(),'double','FIXED_ROM_WILD_OWNER',resource(),1)
    def test_unknown_owner(self):
        with self.assertRaises(DiagnosticStop):self.episode().enter_battle(battle(),'ordinary_single_wild','UNKNOWN',resource(),1)
    def test_no_per_battle_contract(self):
        c=contract();c['ordinary_battle_checkpoint']=True
        with self.assertRaises(DiagnosticStop):MilestoneEpisode(c)
    def test_frontier_not_endpoint_kind(self):
        c=contract();c['kind']='diagnostic_frontier'
        with self.assertRaises(DiagnosticStop):MilestoneEpisode(c)
    def test_battle_budget(self):
        c=contract();c['max_battles']=0;e=MilestoneEpisode(c);e.begin(field())
        with self.assertRaises(DiagnosticStop):self.enter(e)
    def test_decision_budget(self):
        e=self.enter()
        for i in range(6):e.input_for(battle(),'animation',i+1)
        with self.assertRaises(DiagnosticStop):e.input_for(battle(),'moves',7)
    def test_contract_copy(self):c=contract();e=MilestoneEpisode(c);c['endpoint']['xy'][0]=9;self.assertEqual(e.contract['endpoint']['xy'],[5,5])
    def test_actual_pp_not_command_count(self):e=self.enter();e.input_for(battle(),'moves',1);v=evidence();v['resources']['pp']=[3,9,5,2];self.assertEqual(e.finish_battle(dict(field(),battle_outcome=1),v,2)['pp_used'],[0,0,3,0])
    def test_ledger_copy(self):e=self.enter();v=e.finish_battle(dict(field(),battle_outcome=1),evidence(),2);v['after']['hp']=0;self.assertEqual(e.ledger[0]['after']['hp'],274)
    def test_no_second_endpoint(self):
        e=self.episode();o=dict(field(),map=[35,0],xy=[5,5],facing=2);e.reach(o,evidence(),2)
        with self.assertRaises(DiagnosticStop):e.reach(o,evidence(),3)
def mutation(k,v,is_evidence=False):
    def case(self):
        e=self.enter();o=dict(field(),battle_outcome=1);a=evidence();(a if is_evidence else o)[k]=copy.deepcopy(v)
        with self.assertRaises(DiagnosticStop)as cm:e.finish_battle(o,a,2)
        self.assertFalse(cm.exception.report['milestone_reached']);self.assertFalse(cm.exception.report['ordinary_save_authorized']);self.assertEqual(e.ledger,[])
    return case
for k,v in[('callback2',999),('lock',1),('battle_outcome',2),('battle_flags',8),('map',[3,25]),('xy',[0,0])]:setattr(Continuation,'test_return_reject_'+k,mutation(k,v))
for i,(k,v)in enumerate([('owner','UNKNOWN'),('story_effects',[['4072',4]]),('owners_resolved',False),('field_return',False),('observation_match',False),('resources',dict(hp=0,pp=[3]*4)),('resources',dict(hp=100,pp=[4,9,8,2]))]):setattr(Continuation,'test_evidence_reject_'+str(i),mutation(k,v,True))
for k,v in[('map',[3,24]),('xy',[4,4]),('facing',3),('lock',1)]:
    def case(self,k=k,v=v):
        e=self.episode();o=dict(field(),map=[35,0],xy=[5,5],facing=2);o[k]=v
        with self.assertRaises(DiagnosticStop):e.reach(o,evidence(),1)
        self.assertFalse(e.reached)
    setattr(Continuation,'test_endpoint_reject_'+k,case)
if __name__=='__main__':unittest.main()
