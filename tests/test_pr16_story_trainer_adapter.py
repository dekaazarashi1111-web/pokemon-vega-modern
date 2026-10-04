"""trainer視線ownerの新規検査。受入済み80試験は再実行しない。"""
from copy import deepcopy
from unittest.mock import patch
import struct,unittest
from test_pr16_story_clock import sample,bytechange
import pr16_story_trainer_adapter as t
import pr16_story_trainer_session as reader
from pr16_story_milestones import DiagnosticStop

def sight():
    a=sample();a['observation'].update(map=[3,24],xy=[38,7],callback2=t.FIELD,lock=0,battle_flags=4,battle_outcome=1,facing=2)
    p=bytearray(a['save1']);struct.pack_into('<HH',p,0,38,7);a['save1']=bytes(p)
    z=deepcopy(a);z['observation'].update(observe=1,frame=1446,xy=[38,6],lock=1)
    p=bytearray(z['save1']);struct.pack_into('<HH',p,0,38,6);z['save1']=bytes(p)
    s=bytearray(240);s[1]=1;struct.pack_into('<II',s,4,0x08068F09,0x08192DFE);z['route']=dict(trainer_id=131,script_contexts=bytes(s));z['flags']=z['save1'][0xEE0:0x1000]
    return a,z
def trainer_entry():
    _,a=sight();c=bytearray(a['route']['script_contexts']);c[1]=2;struct.pack_into('<II',c,4,0x0806B159,0x08192F0E);a['route']['script_contexts']=bytes(c)
    z=deepcopy(a);z['observation'].update(observe=2,frame=1628,callback2=t.BATTLE,battle_flags=12,battle_outcome=0);z['ui']['enemy_count']=4
    team=[dict(species=x,level=y,item=k,moves=m)for x,y,k,m in [(481,13,0,[150,33,175,0]),(528,14,139,[55,341,281,21]),(1537,15,141,[411,352,227,549]),(1147,16,139,[495,24,334,249])]]
    owner=dict(id=131,party=team);z['enemy_mons']=[dict(**x,status=0,hp=31,max_hp=31)for x in team]
    x,y=t.rekey_image(a['save1'],a['save2'],0x12345678)
    for index in (7,9):
        at=0x1200+4*index;struct.pack_into('<I',x,at,min(0xFFFFFF,(t.u32(x,at)^0x12345678)+1)^0x12345678)
    struct.pack_into('<H',x,0x1044,0);x[0x608]|=1;x[0x3A28]|=1;y[0x6C]|=1;z['save1']=bytes(x);z['save2']=bytes(y)
    return a,z,owner

class TrainerTests(unittest.TestCase):
    def test_entry_closed_plaintext_and_party(self):
        a,z,o=trainer_entry();r=t.entry(a,z,o);self.assertTrue(r['rekey_plaintext_preserved']);self.assertFalse(r['trainer_victory_accepted']);self.assertEqual(r['game_stats_incremented'],[7,9])

    def test_same_frame_script_pc(self):
        row=dict(trainer_live=4,frame=100,schema=1,battle_script=0x09009243)
        self.assertEqual(reader.parse(row,dict(observe=4,frame=100)),row)
        with self.assertRaises(ValueError):reader.parse(row,dict(observe=4,frame=101))
    def test_source_pc_read_only(self):
        with patch.object(reader.route,'generate',return_value=b'static struct mCore *st_open(\nrv_emit(c,n,st_frames);st_screen(n);fflush(stdout);'):
            s=reader.generate()
        self.assertIn(b'read32(c, 0x02023CD4U)',s)
        self.assertEqual(s.count(b'tv_emit(c,n,st_frames);'),1)
    def test_approach_template_only(self):
        _,a=sight();p=bytearray(a['save1']);p[0x910]=3;struct.pack_into('<HH',p,0x914,34,6);p[0x919]=10;a['save1']=bytes(p)
        z=deepcopy(a);z['observation'].update(observe=2,frame=1506);p=bytearray(z['save1']);struct.pack_into('<H',p,0x914,37);z['save1']=bytes(p)
        c=bytearray(z['route']['script_contexts']);c[1]=2;struct.pack_into('<II',c,4,0x0806B159,0x08192F0E);z['route']['script_contexts']=bytes(c)
        obj=bytearray(576);obj[188:191]=bytes([3,24,3]);struct.pack_into('<HH',obj,196,44,13);obj[204]=4;z['objects']=bytes(obj)
        t.field_preserved(a,z)
        bytechange(z,'save1',0x914,36)
        with self.assertRaises(DiagnosticStop):t.field_preserved(a,z)

    def test_sight_has_no_step_maintenance(self):
        a,z=sight();r=t.sight(a,z);self.assertEqual(r['position_step'],1);self.assertEqual(r['walking_counter_steps'],0);self.assertFalse(r['save_requested'])
    def test_approach_no_dialogue_button(self):
        _,z=sight()
        class Session:
            live=z;last=z['observation'];commands=[]
            def step(self,*pairs):self.commands.extend(pairs)
        s=Session()
        with self.assertRaises(DiagnosticStop):t.observe_approach(s)
        self.assertEqual(s.commands,[(0,180)]*12)
def bad(name,edit):
    def test(self):
        a,z=sight();edit(a,z)
        with self.assertRaises(DiagnosticStop):t.sight(a,z)
    setattr(TrainerTests,'test_reject_'+name,test)
for n,e in {
 'trainer':lambda a,z:z['route'].update(trainer_id=128),
 'stale_new_win':lambda a,z:z['observation'].update(battle_flags=8),
 'outcome':lambda a,z:z['observation'].update(battle_outcome=0),
 'callback':lambda a,z:z['observation'].update(callback2=t.BATTLE),
 'already_unlocked':lambda a,z:z['observation'].update(lock=0),
 'wrong_origin':lambda a,z:a['observation'].update(xy=[37,6]),
 'wrong_target':lambda a,z:z['observation'].update(xy=[39,6]),
 'save':lambda a,z:z['observation'].update(save_counter=102),
 'pp':lambda a,z:bytechange(z,'party',53,1),
 'bag':lambda a,z:bytechange(z,'save1',0x310,1),
 'step_counter':lambda a,z:bytechange(z,'save1',0x1042,1),
 'daycare':lambda a,z:bytechange(z,'save1',0x309A,1),
 'unknown_var':lambda a,z:bytechange(z,'expanded_vars',0,1),
 'trainer_flag':lambda a,z:bytechange(z,'flags',1411//8,1<<(1411%8)),
 'unknown_script':lambda a,z:bytechange(z['route'],'script_contexts',4,1),
 'identity':lambda a,z:bytechange(z,'save2',0,1),
 'ledger':lambda a,z:bytechange(z,'ledger',0x743,1)
}.items():bad(n,e)
if __name__=='__main__':unittest.main()

def bad_entry(name,edit):
    def test(self):
        a,z,o=trainer_entry();edit(a,z,o)
        with self.assertRaises(DiagnosticStop):t.entry(a,z,o)
    setattr(TrainerTests,'test_entry_reject_'+name,test)
for n,e in {
 'money':lambda a,z,o:bytechange(z,'save1',0x290,z['save1'][0x290]^1),
 'rematch_corruption':lambda a,z,o:bytechange(z,'save1',0x670,z['save1'][0x670]^4),
 'battle_tower_corruption':lambda a,z,o:bytechange(z,'save2',0xD4,z['save2'][0xD4]^4),
 'wrong_enemy':lambda a,z,o:z['enemy_mons'][2].update(species=963),
 'residual_win':lambda a,z,o:z['observation'].update(battle_outcome=1),
 'pp':lambda a,z,o:bytechange(z,'party',54,z['party'][54]^1),
 'unknown_stat':lambda a,z,o:bytechange(z,'save1',0x1228,z['save1'][0x1228]^1),
}.items():bad_entry(n,e)
