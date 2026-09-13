#!/usr/bin/env python3
"""New read-only evidence for the previously unobserved rental-chooser wait.

No key timing, fixture, ROM, game function, guard or acceptance assertion changes.
Raw context offsets remain raw until checked against the pinned upstream layout.
"""
from __future__ import annotations
import json
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
SELF='scripts/pr16_bp_chooser_trace.py'
C_TRACE=r'''
/* Linker anchors: pinned CFRU-JP/BPRJ.ld. These are raw bytes, not guessed fields. */
static void bp_read_span(struct mCore *c,const char *name,uint32_t address,unsigned size){
    fprintf(stderr,"BP_READ name=%s frame=%u address=%08x size=%u hex=",name,b_frames,address,size);
    for(unsigned i=0;i<size;++i)fprintf(stderr,"%02x",read8(c,address+i));
    fputc('\n',stderr);
}
static void bp_context_snapshot(struct mCore *c){
    bp_read_span(c,"script_env1_raw",0x03000EB0U,120U);
    bp_read_span(c,"script_env2_raw",0x03000F28U,120U);
    bp_read_span(c,"special_vars_raw",0x02036FECU,30U);
    bp_read_span(c,"task_table_raw",0x030050D0U,640U);
    bp_read_span(c,"legacy_choose_script",0x092CF620U,32U);
    for(unsigned offset=4U;offset<=8U;offset+=4U){
        uint32_t pointer=read32(c,0x03000EB0U+offset)&~1U;
        if(pointer>=0x08000000U && pointer<=0x09FFFFA0U)
            bp_read_span(c,offset==4U?"env1_raw_offset4_target":"env1_raw_offset8_target",pointer,96U);
    }
}
'''

def instrument(text,transform):
    changes=[]
    for before,after in (
        ('static struct BPTrace bt;\n','static struct BPTrace bt;\n'+C_TRACE),
        ('    for(unsigned f=0;f<12000U;++f){\n',
         '    for(unsigned f=0;f<12000U;++f){\n'
         '        if(f==0U || f==60U || f==180U || f==600U || f==1200U || f==6000U || f==11999U)bp_context_snapshot(c);\n')):
        text=transform(text,before,after)
        changes.append(dict(source='tools/mgba_pr16_bp_native_controls.c',before=before,after=after,scope='READ_ONLY_TRACE_NO_CONTROLLER_CHANGE'))
    return text,changes

def prepare(raw,out,identity,need,stable):
    cfg=json.loads((ROOT/'config/github_private_environment.json').read_bytes())
    name='pokemon-vega-private-env-v1-state.zip';bound=next(a for a in cfg['archives'] if a['name']==name)
    archive=ROOT/'.local/pr16-bp-trial-native-inputs'/name;data=archive.read_bytes()
    need(identity(data)=={k:bound[k] for k in ('size','sha256')},'upstream archive identity differs')
    wanted={'script.h','script.c','event_data.h','event_data.c','field_specials.h','field_specials.c',
        'party_menu.h','party_menu.c','task.h','scrcmd.c','specials.h','specials.s','script_cmd_table.s','BPRJ.ld'}
    members={}
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            path=Path(info.filename)
            if info.filename.startswith('vendor/upstream/CFRU-JP/') and path.name in wanted:
                need(not info.is_dir() and info.file_size<2_000_000,'upstream source bound')
                source=z.read(info);source.decode('utf-8');need(b'\0' not in source,'upstream source binary')
                members[info.filename]=source
    need(1<=len(members)<=64 and sum(map(len,members.values()))<8_000_000,'upstream snapshot bound')
    linker=members.get('vendor/upstream/CFRU-JP/BPRJ.ld',b'')
    for anchor in (b'gScriptEnv1 = 0x03000EB0;',b'gScriptEnv2 = 0x03000F28;',b'gTasks = 0x30050D0;',b'InitChooseHalfPartyForBattle = 0x8127DE0 | 1;'):
        need(anchor in linker,'linker observation anchor differs')
    with zipfile.ZipFile(out/'chooser-upstream-sources.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name,source in sorted(members.items()):z.writestr(name,source)
    report=dict(schema_version=1,status='READ_ONLY_CHOOSER_BINDING_DIAGNOSTIC',candidate=identity(raw),
        private_archive={k:bound[k] for k in ('name','size','sha256')},sources={name:identity(data) for name,data in sorted(members.items())},
        snapshot_budget=7,key_timing_changed=False,rom_changes=0,post_observation_host_writes=0,
        context_layout_not_inferred_from_old_trace=True,
        bounded_rom_ranges=[dict(address=address,size=size,hex=raw[address-0x08000000:address-0x08000000+size].hex())
            for address,size in ((0x08127DE0,128),(0x092CF620,64))],native_rental_accepted=False,p05_native_bp_gap_closed=False,release_ready=False)
    (out/'chooser-bindings.json').write_bytes(stable(report));return report
