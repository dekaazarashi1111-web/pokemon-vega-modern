"""New scoped battle adapter tests; previous 47 clock tests are reused."""
from copy import deepcopy
import struct,unittest
from test_pr16_story_clock import sample,clock,bytechange
import pr16_story_battle_adapter as b
from pr16_story_milestones import DiagnosticStop

def entry():
    a=sample();a['observation'].update(map=[3,24],xy=[32,10],callback2=0x08055E69,lock=1,battle_flags=0,battle_outcome=0)
    s=bytearray(a['save1']);struct.pack_into('<HH',s,0,32,10);a['save1']=bytes(s)
    e=bytearray(600);struct.pack_into('<H',e,32,32);struct.pack_into('<4H',e,44,40,43,64,116);e[84]=13;struct.pack_into('<HH',e,86,36,36);a['enemy_party']=bytes(e)
    z=deepcopy(a);z['observation'].update(observe=1,frame=1990,callback2=b.BATTLE,battle_flags=4)
    x,y=b.rekey_image(a['save1'],a['save2'],0x12345678);x[0x5FB]=x[0x3A1B]=y[0x5F]=128;struct.pack_into('<H',x,0x1044,0);y[14:19]=clock(b.u16(a['save2'],14)*216000+20*3600+26*60+50)[14:19]
    z['save1']=bytes(x);z['save2']=bytes(y);z['route']=dict(trainer_id=0)
    return a,z

def finish():
    _,a=entry();z=deepcopy(a);z['observation'].update(observe=2,frame=2050,callback2=b.FIELD,lock=0,battle_outcome=1);s=bytearray(z['save2']);s[17]+=1;z['save2']=bytes(s);bytechange(z,'party',53,8)
    z['party_mons'][0]['pp'][1]=8;return a,z

class BattleTests(unittest.TestCase):
    def test_entry_641_rekey_bytes_and_seen(self):a,z=entry();self.assertTrue(b.entry_evidence(a,z)['rekeyed']);self.assertEqual(b.u32(z['save1'],0x290),0x12345678);self.assertEqual(b.u16(z['save1'],0x312),0x5678)
    def test_rekey_roundtrip(self):a,_=entry();x,y=b.rekey_image(a['save1'],a['save2'],0xDEADBEEF);p,q=b.rekey_image(bytes(x),bytes(y),0);self.assertEqual(bytes(p),a['save1']);self.assertEqual(bytes(q),a['save2'])
    def test_no_save_on_victory(self):a,z=finish();v=b.finished(a,z);self.assertFalse(v['save_requested']);self.assertEqual(v['continuation'],'CONTINUE_TO_DECLARED_MILESTONE')
    def test_ui_text_owner(self):_,z=entry();z['ui'].update(execution=1,command=16,controller=0x0802FD91);self.assertEqual(b.ui(z),('text',None))
    def test_ui_action_owner(self):_,z=entry();z['ui'].update(execution=1,command=18,controller=0x0802DC15,action_cursor=0);self.assertEqual(b.ui(z),('action',0))
    def test_ui_move_owner(self):_,z=entry();z['ui'].update(execution=1,command=20,controller=0x0802E1ED,move_cursor=1);self.assertEqual(b.ui(z),('moves',1))
    def test_ui_noninteractive_command(self):_,z=entry();z['ui'].update(execution=1,command=4,controller=0x0802EE11);self.assertEqual(b.ui(z),('automatic',None))
    def test_ui_no_pending_player_command(self):_,z=entry();z['ui'].update(execution=0);self.assertEqual(b.ui(z),('automatic',None))
    def test_unknown_yesno_stops(self):
        _,z=entry();z['ui'].update(execution=1,command=19,controller=0x0802FD91)
        with self.assertRaises(DiagnosticStop):b.ui(z)
    def test_unknown_text_controller_stops(self):
        _,z=entry();z['ui'].update(execution=1,command=16,controller=0x0802FD93)
        with self.assertRaises(DiagnosticStop):b.ui(z)
    def test_catch_command_stops(self):
        _,z=entry();z['ui'].update(execution=1,command=13,controller=0x0802FD91)
        with self.assertRaises(DiagnosticStop):b.ui(z)
    def test_current_resource_move(self):
        _,z=entry();p=bytearray(352);struct.pack_into('<H',p,0,850);struct.pack_into('<4H',p,12,337,89,280,332);struct.pack_into('<H',p,40,277);p[36:40]=bytes([3,9,8,2]);struct.pack_into('<H',p,88,32);struct.pack_into('<H',p,128,36);p[130]=13;p[121:123]=bytes([3,3]);z['route'].update(battle_mons=bytes(p),party_indexes=bytes(8));self.assertEqual(b.move_plan(z),1)
        p[37]=0;z['route']['battle_mons']=bytes(p)
        with self.assertRaises(DiagnosticStop):b.move_plan(z)
    def test_navigation(self):self.assertEqual(b.navigation(0,1),[16]);self.assertEqual(b.navigation(3,0),[64,32])

def bad(name,edit):
    def test(self):
        a,z=entry();b.entry_evidence(a,z);edit(a,z)
        with self.assertRaises(DiagnosticStop):b.entry_evidence(a,z)
    setattr(BattleTests,'test_reject_'+name,test)
for n,e in {
 'money':lambda a,z:bytechange(z,'save1',0x290,1),
 'bag_item':lambda a,z:bytechange(z,'save1',0x310,1),
 'bag_quantity':lambda a,z:bytechange(z,'save1',0x312,1),
 'unknown_flag':lambda a,z:bytechange(z,'save1',0xEE0,1),
 'seen_wrong_species':lambda a,z:bytechange(z,'save2',0x60,1),
 'identity':lambda a,z:bytechange(z,'save2',0,1),
 'berry_powder':lambda a,z:bytechange(z,'save2',0xAF8,1),
 'unknown_tail':lambda a,z:bytechange(z,'save1',0x3D20,1),
 'expanded_qol':lambda a,z:bytechange(z,'expanded_vars',850,1),
 'rp_ledger':lambda a,z:bytechange(z,'ledger',0x743,1),
 'party_change':lambda a,z:bytechange(z,'party',52,2),
 'unexpected_save':lambda a,z:z['observation'].update(save_counter=102),
 'wrong_enemy':lambda a,z:bytechange(z,'enemy_party',32,29),
}.items():bad(n,e)
if __name__=='__main__':unittest.main()
