import ctypes,json,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts')]
import pr16_dex_battle_consumers as b
class Consumers(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();out=Path(cls.temp.name);fixture=out/'live.c';fixture.write_text('#include <stdint.h>\nuint8_t dex_consumer_live[522];\n')
  command=['cc','-std=c11','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror','-DDEX_CONSUMER_HOST',str(fixture),*[str(ROOT/'overlays/dex_owner'/n)for n in ['dex_battle_consumers.c','dex_owner.c','dex_compact_adapter.c','dex_compact_map.c']],'-o',str(out/'consumer.so')]
  r=subprocess.run(command,capture_output=True);assert r.returncode==0 and not r.stdout and not r.stderr,r.stderr
  cls.lib=ctypes.CDLL(str(out/'consumer.so'));cls.live=(ctypes.c_ubyte*522).in_dll(cls.lib,'dex_consumer_live')
  cls.species=json.loads((ROOT/'content/modernization/pr16_dex_namespace.json').read_bytes())['species']
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def init(self):self.assertEqual(self.lib.VegaDexInitNew(self.live,522),0)
 def test_every_raw_species_matches_published_owner(self):
  for row in self.species:
   self.init();prior=bytes(self.live);self.lib.VegaDexBattleSeenC(row['species_id']);after=bytes(self.live);owner=row['owner']
   if not owner:self.assertEqual(after,prior)
   else:
    i=(owner-1)//8;self.assertEqual(after[12+i],1<<((owner-1)%8));self.assertEqual(sum(x.bit_count()for x in after[12:163]),1);self.assertEqual(after[163:],prior[163:]);self.assertEqual(self.lib.VegaDexValidate(self.live,522),0)
 def test_collision_and_stage75(self):
  self.init()
  for sid in [129,481,1670]:self.lib.VegaDexBattleSeenC(sid)
  owners={129,456,925};self.assertEqual({i*8+j+1 for i,v in enumerate(bytes(self.live)[12:163])for j in range(8)if v&(1<<j)},owners)
 def test_invalid_live_and_raw_sid_no_write(self):
  for sid in [0,253,1671,65535]:
   self.init();before=bytes(self.live);self.lib.VegaDexBattleSeenC(sid);self.assertEqual(bytes(self.live),before)
  self.init();self.live[4]^=1;before=bytes(self.live)
  for sid in [1,129,481,1620,1670]:self.assertEqual(self.lib.VegaDexBattleSeenC(sid),0);self.assertEqual(bytes(self.live),before)
 def test_official_count_and_bad_modes(self):
  self.init();value=ctypes.c_ubyte()
  for owner in range(1,1207):self.assertEqual(self.lib.VegaDexAccess(self.live,522,owner,3,ctypes.byref(value)),0)
  before=bytes(self.live)
  for mode,expected in [(0,1025),(1,1025),(2,0),(3,0),(255,0)]:self.assertEqual(self.lib.VegaDexBattleOfficialCountC(mode),expected);self.assertEqual(bytes(self.live),before)
  self.live[4]^=1;before=bytes(self.live);self.assertEqual(self.lib.VegaDexBattleOfficialCountC(1),0);self.assertEqual(bytes(self.live),before)
 def test_inline_continuation_and_lease_bounds(self):
  windows=[w for w in b.proof()['windows']if w['id'].startswith('battle_')];self.assertEqual(len(windows),5)
  for w in windows:
   a=w['address'];patch=b.seen_patch(a,b.BASE+1);self.assertEqual(len(patch),14)
   ins=struct.unpack('<5HI',patch);self.assertEqual(((a+4)&~3)+(ins[0]&255)*4+1,a+15);self.assertEqual(((a+8)&~3)+(ins[2]&255)*4,a+10);self.assertEqual(ins[-1],b.BASE+1)
  self.assertEqual(len(b.tail_patch(0x09131158,b.BASE+1)),8);self.assertEqual(b.BASE-b.p.BASE,5024);self.assertEqual(b.END-b.BASE,1460)
if __name__=='__main__':unittest.main()
