import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_lifecycle as m
class Lifecycle(unittest.TestCase):
 def test_parent_scope(self):
  p=m.checkpoint();self.assertFalse(p['gameplay_accepted']);self.assertEqual(p['link']['extra_lease_size'],1084)
 def test_gap(self):self.assertEqual(m.END-m.BASE,620);self.assertEqual(m.BASE%4,0)
 def test_fixed_codec_entries(self):
  s=m.abi_header();self.assertEqual(s.count('#define '),24);self.assertIn('DEX_ENTRY_VegaDexInitNew ',s)
 def test_signed_seams(self):
  rows={x['id']:x for x in m.signed_windows()}
  for n,_,_ in m.PATCHES:self.assertEqual(rows[n]['size'],4);self.assertEqual(len(rows[n]['sha256']),64)
 def test_tail_control(self):
  s=(ROOT/m.SOURCES[1]).read_text();self.assertIn('mov sp, r4',s);self.assertIn('bics r3, r2',s);self.assertIn('5: .word 0x0805432D',s);self.assertNotIn('bx lr',s)
 def test_host_boundary_matrix(self):
  source=r'''
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include "overlays/dex_owner/dex_save_bridge.h"
static uint8_t live[522],loaded[522];static uint16_t save_status;static unsigned calls,type,result,install,main_calls;
static uint8_t qol(uint8_t t){calls++;save_status=result;if(t!=type)return 254;if(t!=3){main_calls++;for(unsigned i=0;i<522;i++)if(live[i])return 253;if(install)memcpy(live,loaded,522);}return result;}
#define DEX_LIFECYCLE_HOST 1
#define DEX_LIFECYCLE_SAVE_STATUS save_status
#define DEX_LIFECYCLE_LIVE live
#define DEX_LIFECYCLE_QOL qol
#define DEX_LIFECYCLE_INVALIDATE VegaDexInvalidateSession
#define DEX_LIFECYCLE_VALIDATE VegaDexValidate
#include "overlays/dex_owner/dex_lifecycle.c"
int main(void){unsigned cases=0;uint8_t value;
 if(VegaDexInitNew(loaded,522)||VegaDexAccess(loaded,522,1205,3,&value))return 1;
 for(unsigned t=0;t<5;t++)for(unsigned r=0;r<5;r++)for(unsigned put=0;put<2;put++){
  static const unsigned statuses[]={0,1,2,4,255};uint8_t before[522];type=t;result=statuses[r];install=put;calls=main_calls=0;memcpy(live,loaded,522);memcpy(before,live,522);
  unsigned got=VegaDexPostQolLoad(t),want=t==3?result:result==1?(put?1:255):result;
  if(got!=want||calls!=1||main_calls!=(t!=3))return 2;
  if(save_status!=((t!=3&&(result==1||result==255)&&!put)?2:result))return 5;
  if(t==3||((got==1||got==255)&&put)){if(memcmp(live,before,522))return 3;}else for(unsigned i=0;i<522;i++)if(live[i])return 4;
  cases++;
 }
 printf("{\"status\":\"PASS_HOST_LOAD_BOUNDARY\",\"cases\":%u,\"game_boots\":0}\n",cases);return 0;}
'''
  with tempfile.TemporaryDirectory()as d:
   c=Path(d)/'host.c';c.write_text(source);exe=Path(d)/'host'
   p=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT),str(c),str(ROOT/'overlays/dex_owner/dex_owner.c'),str(ROOT/'overlays/dex_owner/dex_save_bridge.c'),'-o',str(exe)],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(p.stderr,'')
   p=subprocess.run([str(exe)],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout)['cases'],50)
if __name__=='__main__':unittest.main()
