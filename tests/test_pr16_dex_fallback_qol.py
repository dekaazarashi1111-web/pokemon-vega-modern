import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Fallback(unittest.TestCase):
 def test_host_contract(self):
  source=r'''
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "overlays/dex_owner/dex_save_bridge.h"
#include "overlays/save_migration/save_migration.h"
static uint16_t status;static uint8_t live[522],buffer[4096],flash[4096];
static VegaModernSaveData ledger;static unsigned calls,reads,invalidations,types,retval,global;
static uint8_t load(uint8_t type){calls++;if(type!=types)return 17;status=global;return retval;}
static void readflash(uint16_t sector,uint32_t off,void *out,uint32_t n){if(sector!=31||off!=0x64||out!=buffer||n!=0xF9C)return;reads++;memcpy(out,flash+0x64,0xF9C);}
static VegaDexStatus invalidate(uint8_t*p,size_t n){invalidations++;return VegaDexInvalidateSession(p,n);}
#define DEX_FALLBACK_HOST 1
#define FALLBACK_STATUS status
#define FALLBACK_LIVE live
#define FALLBACK_LEDGER (&ledger)
#define FALLBACK_BUFFER buffer
#define FALLBACK_LOAD load
#define FALLBACK_VALIDATE VegaSaveValidate
#define FALLBACK_DEX_VALIDATE VegaDexValidate
#define FALLBACK_INVALIDATE invalidate
#define FALLBACK_READ readflash
#include "overlays/dex_owner/dex_fallback_qol.c"
static void init(void){memset(&ledger,0x77,sizeof(ledger));memset(buffer,0x55,sizeof(buffer));memset(flash,0,sizeof(flash));VegaSaveInitNew((VegaModernSaveData*)(flash+0x64),0);VegaDexInitNew(live,522);calls=reads=invalidations=0;}
int main(void){unsigned cases=0;VegaModernSaveData before;uint8_t b[4096],f[4096],mdx[522];
 for(unsigned t=0;t<256;t++)for(unsigned r=0;r<256;r++)for(unsigned g=0;g<5;g++){
  unsigned globals[]={0,1,2,4,255};init();types=t;retval=r;global=globals[g];before=ledger;memcpy(b,buffer,4096);memcpy(f,flash,4096);memcpy(mdx,live,522);
  unsigned active=t!=3&&r==255&&global==255;unsigned got=VegaDexFallbackQolLoad(t);
  if(got!=r||calls!=1||reads!=active||invalidations||status!=global||memcmp(f,flash,4096)||memcmp(mdx,live,522))return 1;
  if(active?memcmp(&ledger,flash+0x64,2048):memcmp(&ledger,&before,2048))return 2;
  if(!active&&memcmp(b,buffer,4096))return 3;cases++;
 }
 for(unsigned kind=0;kind<13;kind++){
  init();types=0;retval=global=255;VegaModernSaveData *q=(VegaModernSaveData*)(flash+0x64);
  if(kind==0)memset(q,0,2048);if(kind==1)memset(q,255,2048);if(kind==2)q->checksum^=1;
  if(kind==3)q->version=1;if(kind==4)q->reserved[0]=1;
  if(kind==5)q->factory.marker=1;if(kind==6)q->factory.snapshot_valid=1;if(kind==7)q->factory.reward_pending=1;
  if(kind==8)q->pending_encounter.valid=1;if(kind==9)q->research_economy.pending_kind=1;
  if(kind==10)q->raid_in_progress[15]=1;if(kind==11)q->raid_retry_pending[0]=1;if(kind==12)live[4]^=1;
  if(kind>=5&&kind<12)VegaSaveFinalize(q);
  before=ledger;memcpy(f,flash,4096);
  if(VegaDexFallbackQolLoad(0)!=255||status!=2||invalidations!=1||reads!=(kind!=12)||memcmp(&ledger,&before,2048)||memcmp(f,flash,4096))return 4;
  for(unsigned j=0;j<522;j++)if(live[j])return 5;cases++;
 }
 printf("{\"status\":\"PASS_HOST_FALLBACK_CONTRACT\",\"cases\":%u}\n",cases);return 0;}
'''
  with tempfile.TemporaryDirectory() as d:
   c=Path(d)/'test.c';c.write_text(source);exe=Path(d)/'test'
   r=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT),str(c),str(ROOT/'overlays/dex_owner/dex_owner.c'),str(ROOT/'overlays/dex_owner/dex_save_bridge.c'),str(ROOT/'overlays/save_migration/save_migration.c'),'-o',str(exe)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stderr,'')
   r=subprocess.run([str(exe)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout)['cases'],327693)
if __name__=='__main__':unittest.main()
