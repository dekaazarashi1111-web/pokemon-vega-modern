import sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_scheduler as s
source=s.generated_source(host=True)
for n in s.placement.EXPORTS:
 import re
 source=re.sub(r'#define DEX_ENTRY_'+n+r' 0x[0-9a-f]+u', '#define DEX_ENTRY_'+n+' ((uintptr_t)&'+n+')',source)
block='static volatile u8 *host_save1,*host_save2,*host_storage;\n#undef G_SAVE_BLOCK1_PTR\n#define G_SAVE_BLOCK1_PTR host_save1\n#undef G_SAVE_BLOCK2_PTR\n#define G_SAVE_BLOCK2_PTR host_save2\n#undef G_POKEMON_STORAGE_PTR\n#define G_POKEMON_STORAGE_PTR host_storage\n'
for n,v in [('FN_READ_FLASH_SECTION','host_read'),('FN_SAVE_CHECKSUM','host_checksum'),('FN_TRY_WRITE_SECTOR','host_try'),('FN_UPDATE_SAVE_ADDRESSES','host_update'),('FN_SAVE_SERIALIZED_GAME','host_serialize'),('FN_STOCK_HANDLE_SAVING_DATA','host_stock')]:block+='#undef '+n+'\n#define '+n+' '+v+'\n'
source=source.replace('static u8 stage61_factory_prepare_fault_is_armed',block+'\nstatic u8 stage61_factory_prepare_fault_is_armed')
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
p=out/'host-generated.c';p.write_text(source)
cmd=['cc','-std=c11','-O0','-g','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-const-variable','-Wno-unused-parameter','-I'+str(ROOT/'overlays/dex_owner'),'-DSCHEDULER_SOURCE="'+str(p)+'"',str(ROOT/'tools/pr16_dex_scheduler_host.c'),*[str(ROOT/x)for x in s.placement.SOURCES],'-o',str(out/'host')]
cmd[1:1]=[x for x in s.proof()['compile_argv_canonical']if x.startswith('-D')]
r=subprocess.run(cmd,capture_output=True,text=True);s.need(r.returncode==0 and not r.stdout and not r.stderr,'strict synthetic host compile')
r=subprocess.run([str(out/'host')],capture_output=True,text=True);s.need(r.returncode==0 and not r.stderr,'synthetic scheduler runtime '+r.stderr[-1000:]);print(r.stdout,end='')
