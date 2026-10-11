"""新C controllerの実32sector differential/fault検査。旧suiteの再実行なし。"""
import ctypes,json,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests')]
import pr16_dex_hof_storage as m
from test_pr16_dex_hof_storage import fixture,payload,append,shifted
METRICS={}
U8=ctypes.c_uint8;U32=ctypes.c_uint32
class Controller:
 def __init__(self,lib,data):self.lib=lib;self.reset(data)
 def reset(self,data):self.lib.HC_Reset((U8*len(data)).from_buffer_copy(data))
 def run(self,method=0,next=None,kind=m.SHIFT,slot=0,absence=False):
  b=None if next is None else (U8*len(next)).from_buffer_copy(next)
  return self.lib.HC_Run(method,b,kind,slot,int(absence))
 def data(self):
  b=(U8*m.CAPACITY)();self.lib.HC_Copy(b);return bytes(b)
 def payload(self):
  b=(U8*m.HOF_SIZE)();self.lib.HC_Payload(b);return bytes(b)
 def info(self):
  b=(U32*16)();self.lib.HC_Result(b);return list(b)
 def cut(self,n):self.lib.HC_Cut(n)
 def fault(self,type,n,mode=1,prefix=0):self.lib.HC_Fault(type,n,mode,prefix)
 def change(self,n):self.lib.HC_Change(n)
 def erases(self):
  a=(U32*128)();b=(U32*128)();self.lib.HC_Erases(a,b);return list(zip(a,b))[:self.info()[10]]
class CControllerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();out=Path(cls.tmp.name)/'controller.so'
  r=subprocess.run(['cc','-shared','-fPIC','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT),str(ROOT/'overlays/hof_journal/hof_transaction.c'),str(ROOT/'overlays/hof_journal/hof_journal.c'),str(ROOT/'tools/pr16_hof_controller_host.c'),'-o',str(out)],capture_output=True,text=True)
  if r.returncode or r.stderr:raise RuntimeError(r.stderr)
  cls.lib=ctypes.CDLL(str(out))
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def controller(self,data=None):return Controller(self.lib,fixture()if data is None else data)
 def test_resolve_matches_reference(self):
  n=0
  for first in range(14):
   for counter in(101,102,0xffffffff):
    data=fixture(counter,first);c=self.controller(data);self.assertEqual(c.run(),0);self.assertEqual(c.info()[:4],[counter,14*(counter&1),first,1]);self.assertEqual(c.payload(),payload());self.assertEqual(c.data(),data);self.assertEqual(c.info()[10:12],[0,0]);n+=1
  METRICS['resolve_rotation_parity_wrap']=n
 def test_commit_all_shapes_full_bytes(self):
  old=payload();shapes=[(m.APPEND,i,append(old,i))for i in range(50)]+[(m.SHIFT,0,shifted(old))]
  for kind,slot,next in shapes:
   data=fixture();c=self.controller(data);c.change(1);self.assertEqual(c.run(2,next,kind,slot),0);f=m.Flash(data);m.commit(f,next,kind,slot);self.assertEqual(c.data(),f.data);self.assertEqual(c.payload(),next)
  METRICS['whole_c_python_transactions']=len(shapes)
 def test_rotation_normal_inherits_token(self):
  for first in range(14):
   data=fixture(0xffffffff,first);c=self.controller(data);c.change(1);self.assertEqual(c.run(2,shifted(payload())),0);image=c.data();f=m.Flash(image);m.normal(f);c.reset(image);self.assertEqual(c.run(3),0);self.assertEqual(c.data(),f.data);self.assertEqual(c.info()[0],1);self.assertEqual(c.info()[7:9],[1,0])
  METRICS['normal_token_wrap_rotations']=14
 def test_unsupported_delta_writes_nothing(self):
  for kind,slot,next in((m.APPEND,50,append(payload())),(m.SHIFT,0,append(payload())),(m.APPEND,0,payload()[:-1]+b'\0')):
   c=self.controller();before=c.data();self.assertNotEqual(c.run(2,next,kind,slot),0);self.assertEqual(c.data(),before);self.assertEqual(c.info()[10:12],[0,0])
 def test_initial_requires_explicit_absence(self):
  old=fixture(absent=True);next=append(bytes(m.HOF_SIZE));c=self.controller(old);self.assertNotEqual(c.run(2,next,m.INITIAL),0);self.assertEqual(c.data(),old)
  c.reset(old);c.change(1);self.assertEqual(c.run(2,next,m.INITIAL,absence=True),0);f=m.Flash(old);m.commit(f,next,m.INITIAL,allow_initial=True);self.assertEqual(c.data(),f.data)
  c=self.controller();self.assertNotEqual(c.run(2,next,m.INITIAL,absence=True),0);self.assertEqual(c.info()[10:12],[0,0])
 def test_newest_bad_journal_never_falls_back(self):
  c=self.controller();self.assertEqual(c.run(2,shifted(payload())),0);data=c.data();main=m.select(data);at=(main.base+main.by_id[4])*4096+0xEC0
  for i in range(256):
   bad=bytearray(data);bad[at+i]^=1;c.reset(bad);self.assertNotEqual(c.run(),0);self.assertEqual(c.data(),bad)
  METRICS['selected_journal_corruptions']=256
 def test_cut_points_cold_and_normal(self):
  c=self.controller();c.change(1);self.assertEqual(c.run(2,shifted(payload())),0);points=set();trace=c.erases()
  for sector,op in trace:
   points.add(op)
   for off in(1,120,121,3776,3777,3968,4084,4088,4089,4092,4096):
    if op+off<=c.info()[13]:points.add(op+off)
  total=0
  for cut in sorted(points):
   c=self.controller();c.change(1);c.cut(cut);self.assertNotEqual(c.run(2,shifted(payload())),0);data=c.data();main,old,_=m.resolve(data);self.assertIn((main.counter,old),((101,payload()),(102,shifted(payload()))));c.reset(data);self.assertEqual(c.run(),0);self.assertEqual(c.info()[0],main.counter);self.assertEqual(c.payload(),old);c.reset(data);self.assertEqual(c.run(3),0);chosen,hof,_=m.resolve(c.data());self.assertEqual((chosen.counter,hof),((main.counter+1)&0xffffffff,old));total+=1
  METRICS['cut_restart_normal']=total
 def test_faults_readback_and_recover(self):
  c=self.controller();self.assertEqual(c.run(2,shifted(payload())),0);erases=c.info()[10];n=0
  for event in range(1,erases+1):
   for prefix in(0,120,2048,4096):
    c=self.controller();c.fault(1,event,2,prefix);self.assertNotEqual(c.run(2,shifted(payload())),0);data=c.data();self.assertEqual(m.resolve(data)[1],payload());c.reset(data);self.assertEqual(c.run(3),0);self.assertEqual(m.resolve(c.data())[1],payload());n+=1
  METRICS['partial_erase_then_normal']=n
 def test_recovery_restart_and_initial_erase_lies(self):
  c=self.controller();self.assertEqual(c.run(2,shifted(payload())),0);trace=c.erases();states={}
  for p,op in trace:
   c=self.controller();c.cut(op);c.run(2,shifted(payload()));data=c.data();route=m.resolve(data)[2]
   if route in('scratch','inverse'):states.setdefault(route,data)
  self.assertEqual(set(states),{'scratch','inverse'});total=0
  for state in states.values():
   c=self.controller(state);self.assertEqual(c.run(1),0);ops=c.erases()
   for p,op in ops:
    for delta in(0,1,120,3968,4096):
     c=self.controller(state);c.cut(op+delta);rc=c.run(1)
     if rc==0:continue
     data=c.data();self.assertEqual(m.resolve(data)[1],payload());c.reset(data);self.assertEqual(c.run(1),0);self.assertEqual(m.resolve(c.data())[1],payload());total+=1
  METRICS['recovery_cut_restarts']=total
  initial=fixture(absent=True);next=append(bytes(m.HOF_SIZE));c=self.controller(initial);self.assertEqual(c.run(2,next,m.INITIAL,absence=True),0);trace=c.erases()
  # HOF28/29完成直後でmain書込み前のerase境界を選ぶ。
  for index,(p,op)in enumerate(trace):
   if p==29:
    cut=op+4096;break
  c=self.controller(initial);c.cut(cut);self.assertNotEqual(c.run(2,next,m.INITIAL,absence=True),0);state=c.data();self.assertEqual(m.resolve(state)[2],'initial-absence')
  for event in(1,2):
   c=self.controller(state);c.fault(1,event,1);self.assertNotEqual(c.run(1),0);self.assertTrue(list(m.intents(c.data(),m.select(c.data()))));self.assertIsNone(m.resolve(c.data())[1])
 def test_omitted_tail_never_commits_signature(self):
  for method in(2,3):
   c=self.controller();self.assertEqual(c.run(method,shifted(payload())),0);trace=c.erases();sector,op=trace[-1];program_before=op-len(trace)
   c=self.controller();c.fault(2,program_before+0xFF0+1,1);self.assertEqual(c.run(method,shifted(payload())),-9);data=c.data();self.assertEqual(data[sector*4096+0xFF8],255);self.assertEqual(m.resolve(data)[1],payload());self.assertEqual(m.resolve(data)[0].counter,101)
  METRICS['omitted_tail_precommit_barriers']=2
 def test_prepare_mutation_rejected_before_bad_image(self):
  c=self.controller();c.change(2);self.assertNotEqual(c.run(2,shifted(payload())),0);self.assertEqual(m.resolve(c.data())[1],payload())
 def test_repeated_fiftyfive_updates(self):
  data=fixture();old=payload()
  for i in range(55):
   c=self.controller(data);new=shifted(old);self.assertEqual(c.run(2,new),0);data=c.data();self.assertEqual(m.resolve(data)[1],new);c.reset(data);self.assertEqual(c.run(3),0);data=c.data();old=new
  METRICS['continuous_updates']=55
