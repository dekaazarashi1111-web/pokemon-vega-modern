"""実geometry新方式。旧34sector試験や既受入nativeを再実行しない。"""
import ctypes,hashlib,json,random,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_hof_storage as m
METRICS={}

def payload(salt=0):
 r=random.Random(400+salt);b=bytearray(r.randbytes(m.HOF_SIZE))
 for i in range(50):struct.pack_into('<H',b,i*120+8,(i+1)|100<<9)
 return bytes(b)

def append(old,slot=0):return old[:slot*120]+bytes((i*19+47)&255 for i in range(120))+old[(slot+1)*120:]
def shifted(old):return old[120:6000]+bytes((i*19+47)&255 for i in range(120))+old[6000:]
def fixture(counter=101,first=7,absent=False):
 data=bytearray(b'\xff'*m.CAPACITY)
 for count in((counter-1)&0xffffffff,counter):
  base=14*(count&1)
  for sid,size in enumerate(m.SIZES):
   b=bytearray(4096);b[:size]=bytes((i+sid*5+count)&255 for i in range(size))
   # logical13のS61E/MDXはopaque既存owner。fullbyte保持を要求する。
   if sid==13:b[size:0xFF0]=bytes((i*29+17)&255 for i in range(0xFF0-size))
   struct.pack_into('<HHII',b,0xFF4,sid,m.checksum(b[:size]),m.SIGN,count)
   p=base+(first+sid)%14;data[p*4096:(p+1)*4096]=b
 if not absent:
  for p,b in zip((28,29),m.make_hof(payload())):data[p*4096:(p+1)*4096]=b
 data[30*4096:]=bytes((i*31+19)&255 for i in range(8192))
 return data

def pair(data):
 main,p,_=m.resolve(data);return main.counter,p

class StorageTests(unittest.TestCase):
 def test_geometry_and_source_preservation(self):
  for first in range(14):
   for counter in(101,102,0xffffffff):
    b=fixture(counter,first);old=m.select(b);f=m.Flash(b);next=shifted(payload());new=m.commit(f,next,m.SHIFT)
    self.assertEqual((new.counter,new.token.epoch),((counter+1)&0xffffffff,1));self.assertEqual(pair(f.data),(new.counter,next))
    self.assertEqual(f.data[old.base*4096:(old.base+14)*4096],b[old.base*4096:(old.base+14)*4096]);self.assertEqual(f.data[30*4096:],b[30*4096:])
    self.assertEqual(len(f.data),131072);self.assertEqual(len(new.journal.encode()),256)
    self.assertEqual(sum(phase=='journal'for phase,_ in f.writes),1)
  METRICS['rotation_parity_wrap']=42
 def test_all_append_and_shift_inverse(self):
  old=payload();total=0
  for slot in range(50):
   new=append(old,slot);j=m.journal(old,new,101,4,b'0'*32,m.APPEND,slot)
   self.assertEqual(m.undo(new,j),old);self.assertEqual(m.Journal.parse(j.encode()),j);total+=1
  j=m.journal(old,shifted(old),101,4,b'0'*32,m.SHIFT,0);self.assertEqual(m.undo(shifted(old),j),old)
  METRICS['inverse_shapes']=total+1
 def test_all_journal_single_byte_corruption(self):
  j=m.journal(payload(),shifted(payload()),101,4,b'0'*32,m.SHIFT,0).encode()
  for i in range(256):
   b=bytearray(j);b[i]^=1
   with self.assertRaises(ValueError):m.Journal.parse(b)
  METRICS['journal_corruptions']=256
 def test_preflight_unsupported_delta_and_epoch(self):
  for kind,slot,delta in((m.APPEND,50,append(payload())),(m.SHIFT,0,append(payload())),(m.APPEND,0,payload()[:-1]+b'\x00')):
   f=m.Flash(fixture());before=bytes(f.data)
   with self.assertRaises(ValueError):m.commit(f,delta,kind,slot)
   self.assertEqual(bytes(f.data),before);self.assertEqual(f.operations,0)
  with self.assertRaises(ValueError):m.journal(payload(),shifted(payload()),0,m.MAX_EPOCH,b'0'*32,m.SHIFT,0).encode()
  with self.assertRaises(ValueError):m.Flash(bytes(34*4096))
 def test_selected_authority_never_falls_back_to_wrong_hof(self):
  f=m.Flash(fixture());m.commit(f,shifted(payload()),m.SHIFT)
  f.data[28*4096]^=1
  with self.assertRaises(ValueError):m.resolve(f.data)
 def test_every_destructive_boundary_restarts_and_normal_save(self):
  f=m.Flash(fixture());old=payload();new=shifted(old);states=[]
  offsets={0,119,120,3775,3776,3967,3968,4083,4084,4087,4088,4091,4092,4095}
  def observe(f,kind,sector,offset):
   if kind in('before_erase','after_erase','verified')or(kind=='program'and offset in offsets):
    got=pair(f.data);self.assertIn(got,((101,old),(102,new)));states.append((f.phase,kind,sector,offset,bytes(f.data)))
  f.observe=observe;m.commit(f,new,m.SHIFT)
  # 各phase/sectorから保存再開。単なるread-only再構成で終わらせない。
  chosen={}
  for phase,kind,sec,off,data in states:
   if kind in('after_erase','verified'):chosen[(phase,kind,sec)]=data
  resumed=0
  for data in chosen.values():
   before=pair(data);g=m.Flash(data);m.normal(g);after=pair(g.data)
   self.assertEqual(after,((before[0]+1)&0xffffffff,before[1]));resumed+=1
  METRICS['durable_boundary_samples']=len(states);METRICS['restart_then_normal']=resumed
 def test_partial_erase_and_program_failure(self):
  observed=[];f=m.Flash(fixture());f.observe=lambda f,k,s,o:observed.append((f.phase,s))if k=='before_erase'else None;m.commit(f,shifted(payload()),m.SHIFT)
  cases=0
  for phase,sector in observed:
   for prefix in(0,120,2048,4096):
    g=m.Flash(fixture());hit=[]
    def fail(g,kind,s,o):
     if not hit and g.phase==phase and kind=='erase'and s==sector:hit.append(True);return prefix
    g.fault=fail
    with self.assertRaises(m.PowerCut):m.commit(g,shifted(payload()),m.SHIFT)
    self.assertTrue(hit);self.assertEqual(pair(g.data),(101,payload()));g.fault=None;m.normal(g);self.assertEqual(pair(g.data),(102,payload()));cases+=1
  for phase,sector in observed[1:]:
   g=m.Flash(fixture());hit=[]
   def fail(g,kind,s,o):
    if not hit and g.phase==phase and kind=='program'and s==sector and o==10:hit.append(True);return 'raise'
   g.fault=fail
   with self.assertRaises(m.FlashError):m.commit(g,shifted(payload()),m.SHIFT)
   self.assertEqual(pair(g.data),(101,payload()));g.fault=None;m.normal(g);self.assertEqual(pair(g.data),(102,payload()));cases+=1
  METRICS['fault_then_normal']=cases
 def test_recovery_is_restartable(self):
  cuts={};f=m.Flash(fixture())
  def observe(f,k,s,o):
   if k=='after_erase'and f.phase in('hof','main'):cuts.setdefault(m.resolve(f.data)[2],bytes(f.data))
  f.observe=observe;m.commit(f,shifted(payload()),m.SHIFT)
  self.assertEqual(set(cuts),{'scratch','inverse'})
  samples=0
  for state in cuts.values():
   g=m.Flash(state)
   def inspect(g,k,s,o):
    nonlocal samples
    if k in('before_erase','after_erase','verified')or(k=='program'and o in(0,119,3967,4084,4088,4095)):
     self.assertEqual(pair(g.data),(101,payload()));samples+=1
   g.observe=inspect;m.recover(g);self.assertFalse(list(m.intents(g.data,m.select(g.data))))
  METRICS['recovery_boundary_samples']=samples
 def test_source_binding_rejects_same_counter_other_main(self):
  f=m.Flash(fixture());found=[]
  def observe(f,k,s,o):
   if f.phase=='journal'and k=='verified':found.append(bytes(f.data));raise m.PowerCut()
  f.observe=observe
  with self.assertRaises(m.PowerCut):m.commit(f,shifted(payload()),m.SHIFT)
  b=bytearray(found[0]);a=m.select(b);pos=(a.base+a.by_id[1])*4096;b[pos]^=1;struct.pack_into('<H',b,pos+0xFF6,m.checksum(b[pos:pos+m.SIZES[1]]))
  self.assertEqual(list(m.intents(b,m.select(b))),[])
 def test_initial_absence_requires_external_owner_permission(self):
  f=m.Flash(fixture(absent=True));new=append(bytes(m.HOF_SIZE))
  with self.assertRaises(ValueError):m.commit(f,new,m.INITIAL)
  self.assertEqual(f.operations,0);m.commit(f,new,m.INITIAL,allow_initial=True);self.assertEqual(pair(f.data),(102,new))
 def test_initial_recovery_omitted_erases_never_retire_journal(self):
  f=m.Flash(fixture(absent=True));new=append(bytes(m.HOF_SIZE))
  def cut(f,k,s,o):
   if f.phase=='hof'and k=='verified'and s==29:raise m.PowerCut()
  f.observe=cut
  with self.assertRaises(m.PowerCut):m.commit(f,new,m.INITIAL,allow_initial=True)
  for omitted in((28,),(29,),(28,29)):
   g=m.Flash(f.data);g.fault=lambda g,k,s,o:'omit'if g.phase=='recover-absence'and k=='erase'and s in omitted else None
   with self.assertRaises(ValueError):m.recover(g)
   self.assertTrue(list(m.intents(g.data,m.select(g.data))));self.assertEqual(pair(g.data),(101,None))
   g.fault=None;m.recover(g);self.assertEqual(pair(g.data),(101,None))
  METRICS['initial_omitted_erase_rejections']=3
 def test_newest_main_journal_damage_is_fail_closed_not_fallback(self):
  f=m.Flash(fixture());main=m.commit(f,shifted(payload()),m.SHIFT)
  start=(main.base+main.by_id[4])*4096+m.JOURNAL_OFFSET
  for i in range(256):
   data=bytearray(f.data);data[start+i]^=1
   with self.assertRaises(ValueError):m.resolve(data)
  METRICS['selected_journal_damage_rejections']=256
 def test_many_transactions_keep_full50_history_and_normal_tokens(self):
  f=m.Flash(fixture());p=payload()
  for epoch in range(1,56):
   p=p[120:6000]+bytes((epoch+i*23)&255 for i in range(120))+p[6000:]
   main=m.commit(f,p,m.SHIFT);self.assertEqual(main.token.epoch,epoch)
   prior=main.token;main=m.normal(f);self.assertEqual(main.token,prior);self.assertEqual(pair(f.data)[1],p)
  METRICS['successive_full_history_transactions']=55

class CodecTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();so=Path(cls.temp.name)/'codec.so'
  subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',str(ROOT/'overlays/hof_journal/hof_journal.c'),'-o',str(so)],check=True,capture_output=True)
  cls.c=ctypes.CDLL(str(so));u8p=ctypes.POINTER(ctypes.c_uint8)
  cls.c.HJ_Build.argtypes=[u8p,u8p,u8p,ctypes.c_uint32,ctypes.c_uint64,u8p,u8p,u8p,ctypes.c_uint,ctypes.c_uint]
  cls.c.HJ_Validate.argtypes=[u8p];cls.c.HJ_Rollback.argtypes=[u8p,u8p,u8p]
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 @staticmethod
 def buf(b):return(ctypes.c_uint8*len(b)).from_buffer_copy(b)
 def test_c_python_fullbyte_crosscheck(self):
  cases=[(m.APPEND,i,payload(),append(payload(),i))for i in range(50)]+[(m.SHIFT,0,payload(),shifted(payload())),(m.INITIAL,0,bytes(m.HOF_SIZE),append(bytes(m.HOF_SIZE)))]
  for kind,slot,old,new in cases:
   j=m.journal(old,new,0xffffffff,123,b'9'*32,kind,slot);out=self.buf(bytes(256))
   self.assertEqual(self.c.HJ_Build(out,self.buf(old),self.buf(new),0xffffffff,123,self.buf(m.sha(old)),self.buf(m.sha(new)),self.buf(b'9'*32),kind,slot),1)
   self.assertEqual(bytes(out),j.encode());self.assertEqual(self.c.HJ_Validate(out),1)
   restored=self.buf(new);self.assertEqual(self.c.HJ_Rollback(restored,restored,out),1);self.assertEqual(bytes(restored),old)
  METRICS['c_python_codec_shapes']=len(cases)
 def test_c_rejects_all_journal_corruption(self):
  j=m.journal(payload(),shifted(payload()),101,4,b'0'*32,m.SHIFT,0).encode()
  for i in range(256):
   b=bytearray(j);b[i]^=1;out=self.buf(b'Q'*m.HOF_SIZE)
   self.assertEqual(self.c.HJ_Validate(self.buf(b)),0);self.assertEqual(self.c.HJ_Rollback(out,self.buf(payload()),self.buf(b)),0);self.assertEqual(bytes(out),b'Q'*m.HOF_SIZE)
 def test_c_invalid_delta_keeps_output(self):
  out=self.buf(b'Q'*256);old=payload();new=old[:-1]+bytes([old[-1]^1])
  self.assertEqual(self.c.HJ_Build(out,self.buf(old),self.buf(new),101,4,self.buf(m.sha(old)),self.buf(m.sha(new)),self.buf(b'0'*32),m.APPEND,0),0);self.assertEqual(bytes(out),b'Q'*256)

if __name__=='__main__':unittest.main()
