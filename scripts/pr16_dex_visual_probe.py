#!/usr/bin/env python3
"""保存済み候補Save1の黒画面を無入力だけで診断。再Save/intro再走はしない。"""
import json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_gameplay_actions as game
need,identity,write=game.need,game.identity,game.write
BASE='d7052a19a0c2991c48de3826278dc9a5c665da5f'
CODE={'scripts/pr16_dex_visual_probe.py','.github/workflows/pr16-dex-visual-probe.yml'}
ARCHIVE=(11313698590,37231996230,41838,'1a6cb98a5d90431aa1355f27682b4b58974a174f82b83be6d7e7705c79987283')
OUT=ROOT/'.local/pr16-dex-visual';PUBLIC=ROOT/'public-dex-visual'
def guard():
 game.BASE=BASE;game.CODE=CODE;game.guard()
def run():
 import pr16_story_live_probe as transport
 need(not OUT.exists()and not PUBLIC.exists(),'fresh visual diagnosis');OUT.mkdir(parents=True);PUBLIC.mkdir()
 game.OUT=OUT;candidate=game.reconstruct()
 z,_=transport.archive(ARCHIVE)
 with z:seed=z.read('newgame-candidate-only.srm')
 need(identity(seed)==dict(size=131088,sha256='5f8c0e489f7f14fa46ed5b3f01403668b3274c989dd33bf87d04cc89851e3fb9'),'retained first Save1')
 save=OUT/'story.srm';save.write_bytes(seed)
 source=game.game.generate().decode();anchor='st_screen(n);fflush(stdout);';need(source.count(anchor)==1,'one render observation')
 visual=r'''unsigned visible=0;for(unsigned i=0;i<240*160;i++)if(si_video[i]&0xFFFFFFu)visible++;
 printf("{\"display\":%u,\"frame\":%u,\"nonblack_pixels\":%u,\"dispcnt\":%u,\"blendcnt\":%u,\"blendalpha\":%u,\"blendbright\":%u,\"cpu_pc\":%u}\n",n,st_frames,visible,read16(c,0x04000000),read16(c,0x04000050),read16(c,0x04000052),read16(c,0x04000054),(unsigned)read_register(c,"pc"));
 '''
 source=source.replace(anchor,visual+anchor);src=OUT/'probe.c';src.write_text(source);exe=OUT/'probe'
 built=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),str(src),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)],capture_output=True,text=True)
 need(built.returncode==0 and not built.stdout and not built.stderr,'strict visual compiler: '+built.stderr[-1000:])
 commands='key 0 120\nobserve 1\nkey 0 300\nobserve 2\nkey 0 600\nobserve 3\nquit\n';write(PUBLIC/'attempt.json',dict(native_processes=1,ordinary_saves=0,status='DIAGNOSTIC_ATTEMPT'))
 r=subprocess.run([str(exe),str(candidate),str(save),'continue-story',identity(seed)['sha256']],cwd=OUT,input=commands,capture_output=True,text=True,timeout=180)
 (PUBLIC/'stdout.txt').write_text(r.stdout);(PUBLIC/'stderr.txt').write_text(r.stderr);(PUBLIC/'commands.txt').write_text(commands)
 for f in OUT.glob('screen-*.ppm'):shutil.copyfile(f,PUBLIC/f.name)
 need(r.returncode==0 and not r.stderr and save.read_bytes()==seed,'clean input-only no-save probe with all SaveRTC exact')
 rows=[json.loads(x)for x in r.stdout.splitlines()];displays=[x for x in rows if 'display'in x];need(len(displays)==4,'four render observations')
 write(PUBLIC/'measurement.json',dict(status='READ_ONLY_VISUAL_DIAGNOSIS_NOT_ACCEPTED',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),native_processes=1,candidate=game.game.CANDIDATE,seed=identity(seed),display=displays,ordinary_saves=0,formal_save_changed=False))
def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated visual directory')
 for f in PUBLIC.iterdir():
  need(f.is_file()and not f.is_symlink()and f.name in {'stdout.txt','stderr.txt','commands.txt','attempt.json','measurement.json','screen-0000.ppm','screen-0001.ppm','screen-0002.ppm','screen-0003.ppm'},'only exact public regular files')
  b=f.read_bytes()
  if f.suffix=='.ppm':need(len(b)==115215 and b.startswith(b'P6\n240 160\n255\n'),'actual whole image')
  else:
   need(len(b)<50000 and b'\0'not in b and (not b or b.endswith(b'\n')),'bounded full text');b.decode('utf-8')
   if f.suffix=='.json':json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'bounded probe');globals()[sys.argv[1]]()
