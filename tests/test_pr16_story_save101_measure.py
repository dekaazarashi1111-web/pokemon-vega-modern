"""宣言済西地域接続の新規controllerだけ。"""
import pathlib,sys,json,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save101_measure as m
class Controller(unittest.TestCase):
    def prep(self):return json.loads((ROOT/m.PREP).read_bytes())
    def base(self):return dict(map=[3,2],xy=[4,17],live_xy=[11,24],facing=2,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=100,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11302156714,'9a4185c74f4906eb05de0167f082fa70de166caf42c5aa6bf7a9fe85bfee77ff'))
    def test_exact_bytes(self):b=(ROOT/'content/modernization/pr16_story_save100_next_route.json').read_bytes();self.assertEqual(self.prep()['parent_route_binding'],m.identity(b));self.assertNotEqual(self.prep()['parent_route_binding'],m.identity(b+b'\n'))
    def test_route(self):self.assertEqual(m.ROUTE,self.prep()['route']);self.assertEqual([m.direction(a,b)for a,b in zip(m.ROUTE,m.ROUTE[1:])],[32]*4)
    def test_terrain(self):self.assertEqual(len(self.prep()['terrain']),6);self.assertTrue(all(t['behavior']==0 and t['collision']==0 and t['elevation']==3 for t in self.prep()['terrain']))
    def test_owner(self):p=self.prep()['connection_owner'];self.assertEqual((p['source']['offset'],p['reciprocal']['offset'],p['button'],p['target_candidate']),(4,-4,32,[53,13]))
    def test_milestone_contract(self):p=self.prep()['milestone_contract'];self.assertEqual(p['kind'],'region_connection');self.assertFalse(p['ordinary_battle_checkpoint']);self.assertFalse(p['diagnostic_stop_is_milestone']);self.assertEqual(p['allowed_battles'],{})
    def test_start(self):m.start(self.base())
    def fake(self,mode=None):
        class Fake:
            def __init__(s):s.last=self.base();s.observations=[s.last];s.inputs=[];s.i=0
            def step(s,*keys):
                s.inputs.extend(keys);s.i+=1;xy=m.ROUTE[min(s.i,4)];where=m.ORIGIN;lock=0;cb=m.m.FIELD
                if s.i>=5:xy=m.ARRIVAL;where=m.DESTINATION
                if mode=='blocked':xy=m.START;where=m.ORIGIN
                if mode=='connection_blocked'and s.i>=5:xy=m.EDGE;where=m.ORIGIN
                if mode=='event'and s.i==1:lock=1
                if mode=='callback'and s.i==1:cb=999
                if mode=='battle'and s.i==1:cb=m.m.BATTLE
                if mode=='early_map'and s.i==1:xy=m.ARRIVAL;where=m.DESTINATION
                if mode=='wrong_arrival'and s.i>=5:xy=[52,13]
                s.last=dict(s.last,xy=xy,live_xy=[v+7 for v in xy],map=where,lock=lock,callback2=cb,facing=3);s.observations.append(s.last);return s.last
        return Fake()
    def test_reach_declared_endpoint(self):
        s=self.fake();route,ledger,f,w=m.progress(s,self.prep());self.assertEqual(route,m.ROUTE);self.assertEqual(ledger,[]);self.assertEqual(f['kind'],'milestone_reached');self.assertEqual(f['milestone']['kind'],'region_connection');self.assertEqual(f['observation'],5);self.assertEqual(w,[]);self.assertTrue(all(k in(0,32)for k,_ in s.inputs))
    def test_blocked_is_diagnostic_no_save(self):
        s=self.fake('blocked')
        with self.assertRaises(m.DiagnosticStop)as cm:m.progress(s,self.prep())
        self.assertFalse(cm.exception.report['milestone_reached']);self.assertTrue(all(k not in(1,8)for k,_ in s.inputs))
    def test_connection_bound(self):
        s=self.fake('connection_blocked')
        with self.assertRaises(m.DiagnosticStop):m.progress(s,self.prep())
        self.assertEqual(len(s.inputs),16)
for mode in['event','callback','battle','early_map','wrong_arrival']:
    def case(self,mode=mode):
        s=self.fake(mode)
        with self.assertRaises(ValueError):m.progress(s,self.prep())
        self.assertTrue(all(k not in(1,8)for k,_ in s.inputs))
    setattr(Controller,'test_reject_'+mode,case)
for key,value in[('save_counter',99),('map',[3,23]),('xy',[0,17]),('ledger_sha256','x'),('party_sha256','x'),('flash_sha256','x'),('rp',1),('party_count',3),('lock',1),('facing',3),('callback2',999),('live_xy',[0,0]),('battle_flags',8),('battle_outcome',1)]:
    def case(self,key=key,value=value):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    setattr(Controller,'test_parent_reject_'+key,case)
if __name__=='__main__':unittest.main()
