"""Positive controls and single-fault rejection for time/walking owners."""
from copy import deepcopy
from pathlib import Path
import json,struct,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_clock as c
import pr16_story_route_session as r
import pr16_story_live_observer as l
from pr16_story_milestones import DiagnosticStop

def clock(t):
    b=bytearray(0xF24);h,t=divmod(t,216000);m,t=divmod(t,3600);s,v=divmod(t,60)
    struct.pack_into('<HBBB',b,14,h,m,s,v);return bytes(b)
def ledger(minute=20,day=3):
    b=bytearray(2048);b[:8]=bytes.fromhex('5647533102000008');o=c.OWNER
    b[o:o+2]=bytes([1,64]);b[o+6]=1;b[o+7]=minute;struct.pack_into('<H',b,o+8,day);b[o+36]=1
    struct.pack_into('<I',b,8,c.ledger_checksum(b));return bytes(b)
def sample():
    areas={k:bytes(v)for k,v in l.SIZES.items()};v=bytearray(1024);v[768:776]=bytes.fromhex('4c4f5051b3b0afae');areas['expanded_vars']=bytes(v);areas['save2']=clock(3*216000+20*3600+16*60+50);areas['ledger']=ledger()
    b=bytearray(areas['save1']);struct.pack_into('<HH',b,0,53,13);struct.pack_into('<HH',b,0x1042,98,3);areas['save1']=bytes(b)
    p=bytearray(600)
    for i in range(4):
        at=i*100;struct.pack_into('<HHI',p,at+32,850+i,0,1250000);p[at+41]=49
        struct.pack_into('<4H',p,at+44,337,89,280,332);p[at+52:at+56]=bytes([3,9,8,2]);p[at+84]=100;struct.pack_into('<HH',p,at+86,277,294)
    areas['party']=bytes(p)
    row={k:v.hex()for k,v in areas.items()};row.update({k:0 for k in l.SCALARS});row.update(live=0,frame=1390,schema=1,save1_pointer=0x02025000,save2_pointer=0x02029000)
    o=dict(observe=0,frame=1390,map=[3,24],xy=[53,13],callback2=l.FIELD,lock=0,party_count=4,save_counter=101,rp=0,party_sha256=l.sha(areas['party']),ledger_sha256=l.sha(areas['ledger']),flash_sha256='a'*64)
    return l.parse(row,o)
def walking():
    a=sample();b=deepcopy(a);b['observation'].update(observe=1,frame=1446,xy=[52,13]);p=bytearray(b['save1']);struct.pack_into('<HH',p,0,52,13);struct.pack_into('<HH',p,0x1042,99,4);struct.pack_into('<I',p,0x1214,1);p[0x309A]=1;b['save1']=bytes(p);b['variables'][33:35]=[99,4];b['save2']=clock(c.clock_value(a['save2'])+56);return a,b
class ClockTests(unittest.TestCase):
    def test_normal_120_ticks(self):self.assertEqual(c.clock_delta(clock(1000),clock(1120),120)['ticks'],120)
    def test_rollover_second(self):self.assertEqual(c.clock_value(clock(3599)),3599)
    def test_rollover_minute(self):self.assertEqual(c.clock_delta(clock(3550),clock(3670),120)['minute_rollovers'],1)
    def test_rollover_hour(self):self.assertEqual(c.clock_delta(clock(215950),clock(216070),120)['minute_rollovers'],1)
    def test_stopped_time(self):self.assertEqual(c.clock_delta(clock(1000),clock(1000),120)['ticks'],0)
    def test_sampling_phase_bound(self):self.assertEqual(c.clock_delta(clock(1000),clock(1121),120)['ticks'],121)
    def test_ledger_no_rollover(self):self.assertEqual(c.ledger_after_minutes(ledger(),0),ledger())
    def test_ledger_minute(self):self.assertEqual(c.ledger_after_minutes(ledger(),1),ledger(21))
    def test_ledger_day(self):self.assertEqual(c.ledger_after_minutes(ledger(59),1),ledger(0,4))
    def test_ledger_day_serial_wrap(self):self.assertEqual(c.ledger_after_minutes(ledger(59,65535),1),ledger(0,0))
    def test_ledger_only_daily_resets(self):
        b=bytearray(ledger(59));b[c.OWNER+14:c.OWNER+26]=bytes(range(12));b[c.OWNER+27:c.OWNER+32]=bytes(range(5));b[c.OWNER+26]=3;b[c.OWNER+32]=7
        struct.pack_into('<I',b,8,c.ledger_checksum(b));x=c.ledger_after_minutes(bytes(b),1)
        self.assertEqual(x[c.OWNER+14:c.OWNER+26],bytes(12));self.assertEqual(x[c.OWNER+27:c.OWNER+32],bytes(5));self.assertEqual(x[c.OWNER+26],3);self.assertEqual(x[c.OWNER+32],7)
    def test_walk_step(self):a,b=walking();self.assertEqual(c.walking_evidence(a,b,[52,13])['walking_steps'],1)
    def test_rotation(self):
        a=sample();b=deepcopy(a);b['observation'].update(observe=1,frame=1446);b['save2']=clock(c.clock_value(a['save2'])+56);self.assertEqual(c.walking_evidence(a,b,[52,13])['walking_steps'],0)
    def test_friendship_wrap(self):
        a,b=walking()
        for live,value in [(a,127),(b,0)]:
            p=bytearray(live['save1']);struct.pack_into('<H',p,0x1042,value);live['save1']=bytes(p);live['variables'][33]=value
        p=bytearray(b['party']);p[41]+=1;p[241]+=1;b['party']=bytes(p);b['party_mons']=[l.mon(bytes(p[i*100:(i+1)*100]))for i in range(4)]
        self.assertEqual(c.walking_evidence(a,b,[52,13])['friendship'],[[0,49,50],[2,49,50]])
    def test_empty_daycare_counter_wrap(self):
        a,b=walking();bytechange(a,'save1',0x309A,255);bytechange(b,'save1',0x309A,0)
        self.assertEqual(c.walking_evidence(a,b,[52,13])['walking_steps'],1)
    def test_observed_transition_step(self):
        a,b=walking()
        for live,xy in [(a,[32,11]),(b,[32,10])]:
            live['observation']['xy']=xy;p=bytearray(live['save1']);struct.pack_into('<HH',p,0,*xy);live['save1']=bytes(p)
        enemy=bytearray(600);struct.pack_into('<I',enemy,0,0x12345678);struct.pack_into('<H',enemy,32,32);enemy[84]=13;struct.pack_into('<4H',enemy,44,40,43,64,116);b['enemy_party']=bytes(enemy)
        v=bytearray(b['expanded_vars']);v[858]=1;struct.pack_into('<II',v,860,0x12345678,0x12345678);b['expanded_vars']=bytes(v)
        v=bytearray(b['save1']);struct.pack_into('<II',v,0x121c,1,1);b['save1']=bytes(v)
        b['observation'].update(callback2=0x08055E69,lock=1,battle_flags=0,battle_outcome=0);b['route']=dict(trainer_id=0)
        self.assertEqual(c.walking_evidence(a,b,[32,10],observed_transition=True)['walking_steps'],1)
        b['route']['trainer_id']=131
        with self.assertRaises(DiagnosticStop):c.walking_evidence(a,b,[32,10],observed_transition=True)
    def test_unowned_transition_rejected(self):
        a,b=walking()
        with self.assertRaises(DiagnosticStop):c.walking_evidence(a,b,[52,13],observed_transition=True)
    def test_cannot_supply_arbitrary_save2_exemption(self):
        with self.assertRaises(TypeError):c.clock_delta(clock(1),clock(2),1,extra_save2={20:1})
    def test_route_reader_readonly(self):r.source_check((r.ROOT/'tools/mgba_pr16_story_route_observer.h').read_text())
    def test_route_reader_reject_write(self):
        with self.assertRaises(ValueError):r.source_check((r.ROOT/'tools/mgba_pr16_story_route_observer.h').read_text()+'write32(c,0,0);')

def badclock(name,a,b,frames=120):
    def test(self):
        c.clock_delta(clock(1000),clock(1120),120)
        with self.assertRaises(DiagnosticStop):c.clock_delta(a(),b(),frames)
    setattr(ClockTests,'test_reject_clock_'+name,test)
for name,a,b,frames in [
 ('backwards',lambda:clock(1000),lambda:clock(999),120),('too_fast',lambda:clock(1000),lambda:clock(1122),120),
 ('zero_frames',lambda:clock(1000),lambda:clock(1000),0),('bool_frames',lambda:clock(1000),lambda:clock(1000),True),
 ('saturation',lambda:clock(c.CLOCK_MAX-10),lambda:clock(c.CLOCK_MAX),120),
 ('unrelated_byte',lambda:clock(1000),lambda:b'\x01'+clock(1120)[1:],120),
 ('bad_minute',lambda:clock(1000),lambda:clock(1120)[:16]+b'\x3c'+clock(1120)[17:],120),
 ('short',lambda:clock(1000),lambda:clock(1120)[:-1],120),
]:badclock(name,a,b,frames)

def badwalk(name,edit):
    def test(self):
        a,b=walking();c.walking_evidence(a,b,[52,13]);edit(a,b)
        with self.assertRaises(DiagnosticStop):c.walking_evidence(a,b,[52,13])
    setattr(ClockTests,'test_reject_walk_'+name,test)
def bytechange(x,k,at,v):p=bytearray(x[k]);p[at]=v;x[k]=bytes(p)
for name,edit in {
 'occupied_daycare':lambda a,b:bytechange(a,'save1',0x2F80,1),
 'party_egg':lambda a,b:bytechange(a,'party',75,64),
 'money':lambda a,b:bytechange(b,'save1',0x290,1),
 'flag':lambda a,b:bytechange(b,'save1',0xEE0,1),
 'storyvar':lambda a,b:bytechange(b,'save1',0x10E4,10),
 'counter':lambda a,b:b['variables'].__setitem__(33,100),
 'position':lambda a,b:b['observation'].update(xy=[51,13]),
 'map':lambda a,b:b['observation'].update(map=[3,37]),
 'lock':lambda a,b:b['observation'].update(lock=1),
 'callback':lambda a,b:b['observation'].update(callback2=l.BATTLE),
 'save':lambda a,b:b['observation'].update(save_counter=102),
 'flash':lambda a,b:b['observation'].update(flash_sha256='b'*64),
 'hp':lambda a,b:bytechange(b,'party',86,1),
 'friendship_without_wrap':lambda a,b:bytechange(b,'party',41,50),
 'expanded_flag':lambda a,b:bytechange(b,'expanded_flags',0,1),
 'coins':lambda a,b:bytechange(b,'coins',0,1),
 'bad_ledger_checksum':lambda a,b:bytechange(b,'ledger',8,1),
 'unchecked_save1_tail':lambda a,b:bytechange(b,'save1',0x3D20,1),
 'save2_tail':lambda a,b:bytechange(b,'save2',0xF00,1),
}.items():badwalk(name,edit)
if __name__=='__main__':unittest.main()
