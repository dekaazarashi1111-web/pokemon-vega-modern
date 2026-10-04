#!/usr/bin/env python3
"""Stage61 save-only replacement inside the existing hash-bound code owner.

Original source/data and non-save code are immutable. This generator produces
an isolated candidate, never the formal story ROM or any input save.
"""
from __future__ import annotations
import functools,hashlib,json,re,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_placement as placement
need,identity=placement.need,placement.identity
SOURCE='overlays/stage61_display_npc_event_audit/stage61_display_npc_event_audit.c'
PROOF='content/modernization/pr16_dex_stage61_relink_inputs.json'
EXPORTS=tuple(x['name'] for x in json.loads((ROOT/PROOF).read_bytes())['symbols'] if x['name'].startswith('Stage61State_'))
RETAIN=('stage61_read32','stage61_crc_byte','stage61_state_crc','stage61_state_record_byte',
 'stage61_save_expected_chunk_data','stage61_save_chunk_descriptor_is_valid',
 'stage61_save_all_descriptors_are_valid','stage61_save_validations_match',
 'stage61_save_physical_sector_for_id','stage61_save_section_crc32',
 'stage61_save_reject_written_target_sector','stage61_save_mark_damaged','stage61_save_clear_damaged')

def proof():return json.loads((ROOT/PROOF).read_bytes())
def function_span(source,name):
    matches=list(re.finditer(r'(?m)^(?:static\s+(?:__attribute__\(\(noinline\)\)\s+)?)?(?:u8|u16|u32|void|volatile u8 \*)\s*'+re.escape(name)+r'\(',source))
    need(len(matches)==1,'one source function '+name)
    start=matches[0].start();brace=source.index('{',start);level=1;i=brace+1
    # This fixed source has no braces in strings within the selected functions.
    while level:
        if source[i]=='{':level+=1
        elif source[i]=='}':level-=1
        i+=1
    return start,brace,i

def change_function(source,name,change):
    a,b,c=function_span(source,name);body=source[a:c];changed=change(body)
    need(changed!=body,'effective bounded change '+name)
    return source[:a]+changed+source[c:]
def once(source,old,new):
    need(source.count(old)==1,'unique anchored source transform '+old[:70]);return source.replace(old,new)

def generated_source(host=False):
    p=proof();source=(ROOT/SOURCE).read_text()
    need(identity(source.encode())=={k:p['source'][k]for k in ('size','sha256')},'exact original source')
    source=source[:source.index('static u8 stage61_summary_has_project_name_provenance')]
    # Calls bind to the accepted 24-entry ABI, never to inferred implementation addresses.
    header='\n'.join('#define DEX_ENTRY_'+n+' '+hex(placement.BASE+i*placement.STRIDE+1)+'u' for i,n in enumerate(placement.EXPORTS))+'\n'+(ROOT/'overlays/dex_owner/dex_stage61_scheduler.h').read_text()
    source=source.replace('#include "../factory_high_modes_v2/factory_high_modes_v2.h"',
        '#include "'+str(ROOT/'overlays/factory_high_modes_v2/factory_high_modes_v2.h')+'"')
    source=once(source,'static void stage61_save_mark_damaged(u16 sector)',header+'\nstatic void stage61_save_mark_damaged(u16 sector)')
    source=change_function(source,'stage61_save_validate_slot',lambda s:once(s,
        '        result->valid_mask |= bit;',
        '        if (id == 13u && stage61_dex_check(section, counter) == 0u) {\n            malformed = 1u;\n            continue;\n        }\n        result->valid_mask |= bit;'))
    source=change_function(source,'stage61_state_inject_tail',lambda s:s[:-1]+"""
    for (index = 0u; index < VEGA_DEX_OWNER_SIZE; ++index)
        section[VEGA_DEX_CHUNK13_OFFSET + index] = DEX_LIVE[index];
}""")
    source=change_function(source,'stage61_save_expected_prepared_byte',lambda s:once(s,
        '    if (index == STAGE61_SAVE_ID_OFFSET)',
        '    if (id == 13u && index >= VEGA_DEX_CHUNK13_OFFSET && index < STAGE61_SAVE_TAIL_END)\n        return DEX_LIVE[index - VEGA_DEX_CHUNK13_OFFSET];\n    if (index == STAGE61_SAVE_ID_OFFSET)'))
    source=change_function(source,'stage61_state_tail_matches_live_crc',lambda s:once(s,
        '    return 1u;',
        '    for (index = 0u; index < VEGA_DEX_OWNER_SIZE; ++index)\n        if (section[VEGA_DEX_CHUNK13_OFFSET + index] != DEX_LIVE[index]) return 0u;\n    return 1u;'))
    # Invalid data is refused before ANY flash callback, including direct ABI entries.
    for name in EXPORTS:
        if name in ('Stage61State_HandleLoadSector','Stage61State_GetSaveValidStatus'):continue
        def gate(s):
            brace=s.index('{')
            return s[:brace+1]+'\n    if (!stage61_dex_live_valid()) return stage61_dex_fail_live();'+s[brace+1:]
        source=change_function(source,name,gate)
    source=change_function(source,'Stage61State_CommitSignatureByte',lambda s:once(s,
        '    stage61_save_mark_damaged(sector);',
        '    (void)FN_READ_FLASH_SECTION((u8)sector, (void *)section);\n    if (stage61_save_readback_matches_prepared(section, id, size, chunks[id].data, G_SAVE_COUNTER, record_crc, 0xFFu) == 0u)\n        return stage61_save_fail_with_sector(sector);\n    stage61_save_mark_damaged(sector);'))
    source=change_function(source,'stage61_state_clear',lambda s:s[:-1]+'    stage61_dex_invalidate();\n}')
    source=change_function(source,'Stage61State_HandleLoadSector',lambda s:once(s,
        '    stage61_state_load_compatible_record(chunks);',
        '    stage61_state_load_compatible_record(chunks);\n    (void)FN_READ_FLASH_SECTION((u8)(physical_base + confirmed.physical_by_id[13]), (void *)G_FAST_SAVE_SECTION);\n    if (!stage61_dex_load(G_FAST_SAVE_SECTION, G_SAVE_BLOCK1_PTR, G_SAVE_BLOCK2_PTR, G_SAVE_COUNTER)) {\n        stage61_dex_invalidate();\n        return STAGE61_SAVE_STATUS_ERROR;\n    }'))
    # Consolidate only the identical byte-programming bodies. Commit barriers
    # and readback stay with their original callers.
    for name,sector,mark in (
        ('Stage61State_HandleReplaceSector','sector',True),
        ('stage61_save_clone_record_sector','target_sector',True),
        ('stage61_save_write_normal_live_sector','target_sector',False),
        ('stage61_save_rewrite_source_record_sector','source_sector',False)):
        def shrink(body):
            start=body.index('    for (index = 0u; index < STAGE61_SAVE_SIGNATURE_OFFSET; ++index) {')
            second=body.index('    for (index = STAGE61_SAVE_SIGNATURE_OFFSET + 1u;',start)
            brace=body.index('{',second);level=1;end=brace+1
            while level:
                if body[end]=='{':level+=1
                elif body[end]=='}':level-=1
                end+=1
            replacement='    if (!stage61_dex_program_body(program_byte, '+sector+', section)) {\n'
            if mark:replacement+='        stage61_save_mark_damaged('+sector+');\n'
            replacement+='        return STAGE61_SAVE_STATUS_ERROR;\n    }'
            out=body[:start]+replacement+body[end:]
            if out.count('index')==1:out=out.replace('    u32 index;\n','')
            return out
        source=change_function(source,name,shrink)
    for name in ('stage61_save_clone_record_sector','stage61_save_write_normal_live_sector',
                 'stage61_save_rewrite_source_record_sector','stage61_state_load_compatible_record'):
        source=once(source,'static u8 '+name+'(' if name!='stage61_state_load_compatible_record' else 'static void '+name+'(',
            'static __attribute__((noinline)) '+('void'if name=='stage61_state_load_compatible_record'else 'u8')+' '+name+'(')
    # On a pre-write rejection publish damage only in the bank opposite a
    # fully validated authority. SaveFailed must never erase an arbitrary
    # sector31 or the sole recoverable generation just because RAM is invalid.
    source += r"""
static __attribute__((noinline)) u8 stage61_dex_fail_live(void)
{
    struct Stage61SaveBlockChunk chunks[STAGE61_SAVE_SLOT_SECTORS];
    struct Stage61SaveSlotValidation selected;
    u32 counter = G_SAVE_COUNTER;
    u16 first = G_FIRST_SAVE_SECTOR;
    u8 base = 0xFFu;
    u16 target = 0xFFFFu;
    if (stage61_save_build_live_descriptors(chunks)) {
        (void)stage61_save_select_generation(chunks, &base);
        if (base != 0xFFu) {
            stage61_save_validate_slot(base, chunks, &selected);
            if (selected.status == STAGE61_SAVE_STATUS_OK)
                target = (u16)((base == 0u ? 14u : 0u) + selected.physical_by_id[13]);
        }
    }
    G_SAVE_COUNTER = counter;
    G_FIRST_SAVE_SECTOR = first;
    if (target == 0xFFFFu) return STAGE61_SAVE_STATUS_ERROR;
    return stage61_save_fail_with_sector(target);
}
"""
    # Shared original helpers/data retain their physical addresses and bytes.
    for name in (() if host else RETAIN):
        a,b,c=function_span(source,name)
        decl=' '.join(source[a:b].replace('static ','',1).strip().split())
        ret,params=decl.split(name,1)
        address=next(x['address']for x in p['symbols']if x['name']==name)|1
        macro='#define '+name+' (('+ret.strip()+' (*)'+params+') (uintptr_t)'+hex(address)+'u)'
        source=source[:a]+macro+source[c:]
    for name in (() if host else ('sStage61SaveChunkOffsets','sStage61SaveChunkSizes')):
        pattern=r'static const u16 '+name+r'\[STAGE61_SAVE_SLOT_SECTORS\] = \{.*?\};'
        source,n=re.subn(pattern,'extern const u16 '+name+'[STAGE61_SAVE_SLOT_SECTORS];',source,flags=re.S);need(n==1,'exact retained data '+name)
    for name in EXPORTS:source=source.replace(name,'DexImpl_'+name)
    return source

def windows():
    rows=proof()['symbols'];out=[]
    for row in rows:
        name=row['name']
        if name in RETAIN or not name.startswith(('Stage61State_','stage61_save_','stage61_state_')):continue
        start=row['address'];size=row['size']
        if name in EXPORTS:start+=16;size-=16
        if size>0:out.append((start,start+size))
    out.append((placement.BASE+5024,placement.lease.BASE+placement.lease.END))
    return out

def elf_sections(raw):
    need(raw[:7]==b'\x7fELF\x01\x01\x01','ELF32 little-endian')
    off=struct.unpack_from('<I',raw,32)[0];entsize,count,names=struct.unpack_from('<HHH',raw,46)
    rows=[struct.unpack_from('<10I',raw,off+i*entsize)for i in range(count)]
    s=rows[names];strings=raw[s[4]:s[4]+s[5]];result=[]
    for r in rows:
        name=strings[r[0]:].split(b'\0',1)[0].decode()
        result.append(dict(name=name,type=r[1],flags=r[2],address=r[3],offset=r[4],size=r[5],alignment=r[8]))
    return result

def assign_sections(sections,free):
    rows=sorted(sections,key=lambda x:(-x['size'],x['name']))
    calls=0
    @functools.lru_cache(None)
    def solve(i,ends):
        nonlocal calls
        calls+=1;need(calls<=2000000,'bounded exact section packing')
        if i==len(rows):return ()
        x=rows[i];candidates=[]
        for b,(lo,hi)in enumerate(ends):
            at=(lo+x['alignment']-1)&-x['alignment']
            if at+x['size']<=hi:candidates.append((hi-at-x['size'],b,at))
        seen=set()
        for _,b,at in sorted(candidates):
            key=(ends[b][0]%8,ends[b][1]-ends[b][0])
            if key in seen:continue
            seen.add(key);n=list(ends);n[b]=(at+x['size'],n[b][1]);result=solve(i+1,tuple(n))
            if result is not None:return ((i,at),)+result
        return None
    result=solve(0,tuple(free));need(result is not None,'save windows and already-owned codec reserve cannot fit '+str(sum(s['size']for s in rows))+' bytes')
    assigned=sorted([dict(rows[i],address=a)for i,a in result],key=lambda x:x['address'])
    remainder=[]
    for lo,hi in free:
        at=lo
        for x in assigned:
            if lo<=x['address']<hi:
                if at<x['address']:remainder.append((at,x['address']))
                at=x['address']+x['size']
        if at<hi:remainder.append((at,hi))
    return assigned,remainder

def link(folder):
    need(not folder.exists(),'fresh scheduler link');folder.mkdir(parents=True)
    def run(argv):
        r=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True)
        need(r.returncode==0 and not r.stderr,'strict ARM operation '+Path(argv[0]).name+': '+r.stderr[-3000:]);return r.stdout
    src=folder/'scheduler.c';src.write_text(generated_source());obj=folder/'scheduler.o'
    flags=proof()['compile_argv_canonical'][1:]
    flags=flags[:flags.index('-c')]+['-Wno-unused-function','-Wno-unused-const-variable','-Wa,--noexecstack','-I'+str(ROOT/'overlays/dex_owner')]
    run(['arm-none-eabi-gcc',*flags,'-c',str(src),'-o',str(obj)])
    syms={x['name']:x for x in proof()['symbols']};defs=[];imports=['.syntax unified','.arch armv4t','.thumb']
    for name in RETAIN:imports.extend(['.global '+name,'.type '+name+', %function','.thumb_set '+name+', '+hex(syms[name]['address']|1)])
    for name in ('sStage61SaveChunkOffsets','sStage61SaveChunkSizes'):defs.append(name+' = '+hex(syms[name]['address'])+';')
    for name in ('__aeabi_uidiv','__aeabi_uidivmod','__aeabi_idiv','__aeabi_idivmod'):
        row=syms.get(name)or next(x for x in proof()['unsized_aliases']if x['name']==name)
        defs.append(name+' = '+hex(row['address'])+';')
    imports.append('.section .note.GNU-stack,\"\",%progbits')
    asm=folder/'imports.S';asm.write_text('\n'.join(imports)+'\n');import_obj=folder/'imports.o'
    run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-c',str(asm),'-o',str(import_obj)])
    common='\n'.join(defs)+'\n'
    discard='/DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }'
    ld=folder/'probe.ld';ld.write_text(common+'SECTIONS { . = 0x09448000; .text : { KEEP(*(.text.DexImpl_Stage61State_*)) *(.text*) *(.rodata*) *(.v4_bx) *(.glue_7*) } .data : { *(.data*) *(.bss*) *(COMMON) } '+discard+' }\n')
    elf=folder/'probe.elf';args=['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-nostdlib','-Wl,--build-id=none','-Wl,--gc-sections','-Wl,-e,DexImpl_Stage61State_HandleSavingData']
    run([*args,'-Wl,-T,'+str(ld),str(obj),str(import_obj),'-lgcc','-o',str(elf)])
    # Output sections individually in a second reachability link, preserving GC.
    sect=[s for s in elf_sections(obj.read_bytes())if s['flags']&2 and s['size']]
    need(all(s['name'].startswith(('.text','.rodata'))for s in sect),'no mutable new data')
    ld.write_text(common+'SECTIONS { . = 0x09448000; '+''.join(s['name']+' : { '+('KEEP(*('+s['name']+'))'if s['name'].startswith('.text.DexImpl_Stage61State_')else '*('+s['name']+')')+' }\n'for s in sect)+discard+' }\n')
    run([*args,'-Wl,-T,'+str(ld),str(obj),str(import_obj),'-lgcc','-o',str(elf)])
    live=[s for s in elf_sections(elf.read_bytes())if s['flags']&2 and s['size']]
    need(all(s['name'].startswith(('.text','.rodata'))for s in live),'no synthetic unowned link sections')
    (folder/'link-diagnostic.json').write_text(json.dumps(dict(live_sections=live,available_bytes=sum(b-a for a,b in windows()),required_bytes=sum(x['size']for x in live)),indent=2)+'\n')
    final=folder/'scheduler.elf';ld=folder/'scheduler.ld'
    # Far Thumb calls acquire link stubs when a helper uses the already-owned
    # codec suffix. Probe their exact growth, then perform a normal strict link.
    for attempt in range(8):
        assigned,free=assign_sections(live,windows())
        ld.write_text(common+'SECTIONS { '+''.join(s['name']+' '+hex(s['address'])+' : { KEEP(*('+s['name']+')) }\n'for s in assigned)+discard+' }\n')
        run([*args,'-Wl,--no-check-sections','-Wl,-T,'+str(ld),str(obj),str(import_obj),'-lgcc','-o',str(final)])
        raw=final.read_bytes();actual=[s for s in elf_sections(raw)if s['flags']&2 and s['size']]
        need({s['name']for s in actual}=={s['name']for s in assigned},'no unexpected allocated sections')
        grow=False;previous={s['name']:s for s in live}
        for sec in actual:
            old=previous[sec['name']]
            if sec['size']>old['size']or sec['alignment']>old['alignment']:
                old['size']=max(old['size'],sec['size']);old['alignment']=max(old['alignment'],sec['alignment']);grow=True
        (folder/'link-diagnostic.json').write_text(json.dumps(dict(live_sections=live,available_bytes=sum(b-a for a,b in windows()),required_bytes=sum(x['size']for x in live),sizing_attempt=attempt),indent=2)+'\n')
        if not grow:break
    else:raise ValueError('far-call section placement did not stabilize')
    run([*args,'-Wl,-T,'+str(ld),str(obj),str(import_obj),'-lgcc','-o',str(final)])
    need(not run(['arm-none-eabi-nm','-u',str(final)]),'no undefined scheduler symbols')
    raw=final.read_bytes();actual=[s for s in elf_sections(raw)if s['flags']&2 and s['size']]
    reserved={s['name']:s for s in assigned}
    need(all(s['address']==reserved[s['name']]['address']and s['size']<=reserved[s['name']]['size']for s in actual),'strict bounded final section placement')
    symbols=placement.parse_symbols(run(['arm-none-eabi-nm','-n','-S','--defined-only',str(final)]))
    patches=[(s['address'],raw[s['offset']:s['offset']+s['size']])for s in actual]
    for name in EXPORTS:
        target=symbols['DexImpl_'+name]['address']|1
        patches.append((syms[name]['address'],struct.pack('<6HI',0xB408,0x4B02,0x469C,0xBC08,0x4760,0x46C0,target)))
    return patches,dict(status='LINKED_SAVE_ONLY',sections=[{k:s[k]for k in('name','address','size','alignment')}for s in assigned],payload_bytes=sum(s['size']for s in assigned)+len(EXPORTS)*16,free_bytes=sum(b-a for a,b in free),exports={n:syms[n]['address']for n in EXPORTS},source=identity(src.read_bytes()),symbols=symbols)

def apply(before,patches):
    p=proof();start=p['original_code']['address']-0x08000000;end=start+p['original_code']['size']
    need(identity(before[start:end])==dict(size=p['original_code']['size'],sha256=p['original_code']['sha256']),'original whole Stage61 owner')
    allowed=windows()+[(x['address'],x['address']+16)for x in p['symbols']if x['name']in EXPORTS]
    after=bytearray(before);occupied=set()
    for address,data in patches:
        need(any(a<=address and address+len(data)<=b for a,b in allowed),'patch inside declared save-only subowner')
        covered=set(range(address,address+len(data)));need(not covered&occupied,'nonoverlapping patch');occupied|=covered
        at=address-0x08000000;after[at:at+len(data)]=data
    for x in p['symbols']:
        if x['name'].startswith(('Stage61State_','stage61_save_','stage61_state_'))and x['name']not in RETAIN:continue
        at=x['address']-0x08000000;need(after[at:at+x['size']]==before[at:at+x['size']],'retained original symbol '+x['name'])
    reserve=placement.BASE+5024-0x08000000;reserve_end=placement.lease.END
    need(after[:start]==before[:start]and after[end:reserve]==before[end:reserve]and after[reserve_end:]==before[reserve_end:],'all other owners including next hotfix and accepted codec exact')
    return bytes(after)
