#!/usr/bin/env python3
"""下位generation writerの既存ROM全8入口に対する変更影響だけを検証する。"""
import json,os,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_storage_actions as prior
import pr16_dex_hof_successor as successor
import pr16_dex_hof_generation_source as generation
import pr16_dex_publication as publication
need,identity,write=prior.need,prior.identity,prior.write
BASE='098aa547795a202d7678d0b7f8f2bdb5e182d4de'
WF='.github/workflows/pr16-dex-hof-generation-writer.yml';SELF='scripts/pr16_dex_hof_generation_writer_actions.py'
GUIDE='docs/PR16_DEX_HOF_GENERATION_WRITER_JA.md'
CODE={WF,SELF,GUIDE,'scripts/pr16_dex_hof_generation_source.py'}
CP='content/modernization/pr16_dex_hof_controller_checkpoint.json'
OUT=ROOT/'.local/pr16-dex-hof-generation-writer';PUBLIC=ROOT/'public-dex-hof-generation-writer';ARTIFACT='pr16-dex-hof-generation-writer-text-only'
def guard():
 import pr16_learnset_runtime_record as g
 prior.current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 state=json.loads((ROOT/prior.STATE).read_bytes());need(state['pending_runs']==[]and prior.bindings(state['source_bindings'])==state['source_bindings'],'all earlier bound originals unchanged')
def command(argv):
 p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True);need(p.returncode==0 and not p.stderr,'strict command '+Path(argv[0]).name+': '+p.stderr[-2400:]);return p.stdout

def link(folder):
 # successorのcompile/packing/exports等を変更せず、検査済み新sourceだけを差す。
 old=successor.generated_source;base=old();body=generation.prior.generated_source();need(base.startswith(body),'exact predecessor prefix')
 source=generation.generated_source()+base[len(body):]
 try:successor.generated_source=lambda:source;return successor.link(folder)
 finally:successor.generated_source=old

def audit_retired_egg(current,cp):
 # root移行済みの旧Stage67表を容量候補として監査する。lease/書換はしない。
 rows={r['name']:r for r in cp['placement']['owner_byte_audit']}
 old=rows['modernization_p03_stage67_normal_egg_rows'];new=rows['modernization_p03_stage73_exact_egg_rows']
 live=rows['modernization-p07-preserved-egg']
 for r in(old,new,live):
  at=r['address']-0x08000000;need(identity(current[at:at+r['size']])==dict(size=r['size'],sha256=r['after_sha256']),'actual latest egg owner identity')
 need(old['address']==0x09FED0C4 and old['size']==15118 and new['address']==0x09FF0BD4 and new['size']==15018,'exact Stage67/73 egg owner extents')
 roots=[]
 for offset in(0x45214,0x4528C):
  raw=current[offset:offset+4];target=struct.unpack('<I',raw)[0]
  need(target==live['address']==0x095D9EFC,'actual P07 egg root')
  roots.append(dict(address=offset+0x08000000,**identity(raw),points_to=target))
 need(live['size']==15396 and struct.unpack_from('<I',current,0x45288)[0]==7696,'P07 fulltable scanlimit')
 words=struct.unpack_from('<7698H',current,live['address']-0x08000000);need(words[-1]==0xffff and words[0]>=20000 and all(x<22000 for x in words[:-1]),'P07 value-encoded egg table no row pointers')
 lo,hi=old['address'],old['address']+old['size'];hits=[]
 def canonical(value):
  return 0x08000000+((value&~1)-0x08000000)%0x02000000 if 0x08000000<=(value&~1)<0x0E000000 else -1
 def record(at,target,kind):
  if lo<=at<hi:return
  offset=at-0x08000000;hits.append(dict(address=at,target=target,kind=kind,**identity(current[offset:offset+4]),classification='UNCLASSIFIED'))
 for offset in range(0,len(current)-3):
  target=canonical(struct.unpack_from('<I',current,offset)[0])
  if lo<=target<hi:record(0x08000000+offset,target,'ALL_BYTE_START_U32_ALL_ROM_MIRRORS')
 for offset in range(0,len(current)-3,2):
  a,b=struct.unpack_from('<HH',current,offset)
  if a&0xF800==0xF000 and b&0xF800==0xF800:
   disp=((a&0x7FF)<<12)|((b&0x7FF)<<1)
   if disp&(1<<22):disp-=1<<23
   target=0x08000000+offset+4+disp
   if lo<=target<hi:record(0x08000000+offset,target,'THUMB_BL_SHAPE')
 return dict(status='AUDIT_ONLY_NO_DONOR_LEASE',candidate=identity(current),retired_candidate=old,replacement=new,current_replacement=live,active_roots=roots,current_scan_limit=7696,scan_scope='all32MiB every byte-start U32 ROM mirrors and Thumb BL shape, whole15118byte candidate',hits=hits,unclassified=len(hits),raw_rom_included=False,donor_leased=False,indirect_reference_completeness_claimed=False)

def audit_heap_bindings(current):
 rows=[]
 sources={'pr16_ring_ui_runtime_bytes.json':(2,3,4),'pr16_ring_ui_leaf_bytes.json':(0,1),'pr16_ring_story_resources_frontier.json':(25,26,30,31),'pr16_ring_story_resource_suppliers.json':(3,)}
 for filename,indices in sources.items():
  path='content/modernization/'+filename;data=json.loads((ROOT/path).read_bytes())
  for i in indices:
   r=data['analysis']['new_windows'][i];at=r['start']-0x08000000;need(identity(current[at:at+r['identity']['size']])==r['identity'],'retained actual allocator/reset window')
   rows.append(dict(source_path=path,selector='analysis.new_windows['+str(i)+']',address=r['start'],**r['identity']))
 need(len(rows)==10 and sum(r['size']for r in rows)==688,'ten exact historical heap windows')
 return dict(status='CURRENT_ROM_HEAP_WINDOWS_BOUND_NOT_RUNTIME_LEASE',candidate=identity(current),windows=rows,workspace_bytes=13352,raw_request_bytes=13359,rounded_request_bytes=13360,alignment=8,allocator_internal_entry=0x0800295D,free_internal_entry=0x08002A09,heap_root_pointer=0x03000A38,heap_size_pointer=0x03000A3C,allocator_scratch=[0x02020004,0x02020008,0x0202000C],lease_forbidden_entry=0x0804B85C,heap_ready_all_entries_proven=False,max_contiguous_free_proven=False,runtime_lease_enabled=False,raw_rom_included=False)

def run():
 import pr16_dex_hof_main_cow_actions as main
 import pr16_dex_scheduler as scheduler
 prior.current();need(not OUT.exists()and not PUBLIC.exists(),'fresh generation writer run');OUT.mkdir(parents=True);PUBLIC.mkdir();attempts=[]
 try:
  host=generation.verify_host();write(PUBLIC/'host.json',host)
  # 原本から旧候補を再構成し、受入済全section/全ROM SHAと照合。nativeは再走しない。
  main.OUT=OUT/'main-parent';main.OUT.mkdir();_,_,before,_,_=main.reconstruct()
  previous_patches,previous_link=successor.link(OUT/'reconstruct-link')
  current,old_place=successor.apply(before,previous_patches,previous_link)
  cp=json.loads((ROOT/CP).read_bytes());need(identity(current)==cp['candidate']and previous_link==cp['link'],'exact latest candidate/complete link reconstruction')
  write(PUBLIC/'egg-capacity-audit.json',audit_retired_egg(current,cp))
  write(PUBLIC/'heap-binding.json',audit_heap_bindings(current))
  patches,linked=link(OUT/'new-link');write(PUBLIC/'link.json',linked)
  # 選択窓/保存入口以外を最新12abから全byte保持する。
  old_checkpoint=successor.checkpoint;latest=dict(candidate=cp['candidate'],isolated=dict(placement=cp['placement'],link=dict(sections=cp['placement']['preserved_hof_sections'])))
  try:successor.checkpoint=lambda:latest;after,placed=successor.apply(current,patches,linked)
  finally:successor.checkpoint=old_checkpoint
  need(linked['free_bytes']>cp['link']['free_bytes'],'new lower generation writer reclaims measured ROM capacity')
  candidate=OUT/'candidate.gba';candidate.write_bytes(after)
  write(PUBLIC/'build.json',dict(candidate=identity(after),parent_candidate=identity(current),link=linked,placement=placed,capacity_reclaimed_bytes=linked['free_bytes']-cp['link']['free_bytes']))
  need(subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()=='0.10.2+dfsg-1.1build3'and identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'accepted mGBA runtime exact')
  exports=json.loads((ROOT/'content/modernization/pr16_dex_scheduler_checkpoint.json').read_bytes())['link']['exports'];header=OUT/'entries.h';header.write_text(''.join('#define '+n+' '+hex(a)+'u\n'for n,a in exports.items())+'#define HJ_VALIDATE_ENTRY '+hex(linked['symbols']['HJ_Validate']['address'])+'u\n')
  source=(ROOT/'tools/mgba_pr16_dex_scheduler.c').read_text();need(source.count('int main(int argc,char **argv)')==1 and source.count('mCoreConfigDeinit(&c->config);c->deinit(c);return 0;')==1,'unique native harness insertion')
  source=source.replace('int main(int argc,char **argv)','int accepted_scheduler_main_not_called(int argc,char **argv)').replace('mCoreConfigDeinit(&c->config);c->deinit(c);return 0;','return 0;')+'\n'+(ROOT/'tools/mgba_pr16_dex_hof_successor.h').read_text();src=OUT/'native.c';src.write_text(source);exe=OUT/'native';command(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT),'-DSCHEDULER_ENTRIES="'+str(header)+'"',str(src),str(ROOT/'overlays/dex_owner/dex_owner.c'),str(ROOT/'overlays/hof_journal/hof_journal.c'),'-lmgba','-lm','-o',str(exe)])
  attempts.append('changed-eight-entry-lower-generation-writer');write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts));r=subprocess.run([str(exe),str(candidate)],capture_output=True,text=True,timeout=600);(PUBLIC/'native.txt').write_text(r.stdout or 'no stdout\n')
  if r.stderr:(PUBLIC/'native-stderr.txt').write_text(r.stderr)
  need(r.returncode==0 and not r.stderr,'changed ARM native '+str(r.returncode)+' '+r.stderr[-2000:]);n=json.loads(r.stdout.splitlines()[-1]);need(n['save_owner_cases']==22 and n['new_journal_validator_cases']==257,'exact all8entry22+relocatedcodec257 receipt');need(candidate.read_bytes()==after,'private candidate unchanged')
  write(PUBLIC/'measurement.json',dict(status='PASS_ROM_LOWER_GENERATION_WRITER_CAPACITY',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=identity(after),parent_candidate=identity(current),host=host,native=n,link=linked,placement=placed,capacity_reclaimed_bytes=linked['free_bytes']-cp['link']['free_bytes'],native_processes=len(attempts),unaffected_native_reruns=0,controller_runtime_wired=False,controller_rom_placed=False,runtime_cross_store_atomicity=False,workspace_runtime_owned=False,formal_rom_changed=False,formal_save_changed=False,source_bindings=prior.bindings(CODE)))
 except Exception as e:
  diagnostic=OUT/'new-link/link-diagnostic.json'
  if diagnostic.exists():(PUBLIC/'link-diagnostic.json').write_bytes(diagnostic.read_bytes())
  write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e).replace(str(ROOT),'.'),native_processes=len(attempts)));raise

def export():
 publication.output(PUBLIC)
 allowed={'measurement.json','failure.json','host.json','link.json','build.json','attempts.json','native.txt','native-stderr.txt','link-diagnostic.json','egg-capacity-audit.json','heap-binding.json'}
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in allowed and not p.name.startswith('.'),'closed flat nonhidden nonsymlink text')
  raw=p.read_bytes();need(0<len(raw)<1000000 and raw.endswith(b'\n')and b'\0'not in raw,'bounded complete nonempty text');raw.decode('utf8')
  if p.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed generation workflow');globals()[sys.argv[1]]()
