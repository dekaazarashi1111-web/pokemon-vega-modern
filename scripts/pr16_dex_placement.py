#!/usr/bin/env python3
"""Hash-bound donor transfer and actual-address linkage; no game hook or save writes."""
from __future__ import annotations
import copy, hashlib, json, struct, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
import pr16_dex_lease as lease
from tools.rom_allocator import RomRegion, build_allocation_report

EXPORTS = (
    'VegaDexChecksum', 'VegaDexValidate', 'VegaDexInitNew', 'VegaDexInitLegacy',
    'VegaDexAccess', 'VegaDexCount', 'VegaDexLoad', 'VegaDexSpeciesFlags',
    'VegaDexOfficialFlags', 'VegaDexOfficialRepresentative', 'VegaDexOfficialCount',
    'VegaDexSnapshotSpecies', 'VegaDexRestoreSpecies', 'VegaDexSnapshotSeen',
    'VegaDexRestoreSeen', 'VegaDexCompactSpeciesOwner', 'VegaDexCompactOfficialOwner',
    'VegaDexCompactOwnerRepresentative', 'VegaDexClassifyRecord', 'VegaDexCheckSector',
    'VegaDexInjectSector', 'VegaDexTailMatches', 'VegaDexLoadSelected', 'VegaDexInvalidateSession',
)
BASE = lease.BASE + lease.START
STRIDE = 16
OWNER = 'USER-20261004-DEX-PLACEMENT'
NAME = 'pr16_dex_runtime_reserved'
ALLOCATION = 'content/modernization/pr16_learnset_natural_checkpoint.json'
SOURCES = ['overlays/dex_owner/'+p for p in (
    'dex_owner.c', 'dex_compact_adapter.c', 'dex_compact_map.c', 'dex_save_bridge.c')]
FLAGS = ['-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-Os','-std=c11',
    '-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-unwind-tables',
    '-fno-asynchronous-unwind-tables','-fdata-sections','-ffunction-sections','-fno-common','-Wa,--noexecstack']
need, identity = lease.need, lease.identity

def allocation_source():
    return json.loads((ROOT/ALLOCATION).read_bytes())['wild_repair']['allocation']

def rebuild_allocation(source):
    regions = [RomRegion(**{k:r[k] for k in ('name','start','end_exclusive','alignment','kind','owner','purpose')}) for r in source['regions']]
    requests = []
    for row in source['allocations']:
        need(row['placement'] in ('EXPLICIT','FIRST_FIT'), 'known allocator placement policy')
        request={k:row[k] for k in ('name','region','size','alignment','owner','purpose','content_sha256')}
        if row['placement']=='EXPLICIT': request['start']=row['start']
        requests.append(request)
    return build_allocation_report(regions, requests)

def transfer_allocation(source, before, after):
    """Replace exactly one retired owner, retaining its unused bytes as reserved."""
    expected = allocation_source()
    need(source == expected, 'exact latest 107-owner allocation source')
    need(rebuild_allocation(source) == source, 'canonical original allocator report')
    need(len(source['allocations']) == 107, 'all previous allocator owners retained')
    need(len(before) == len(after) == lease.CANDIDATE['size'], 'fixed ROM length')
    donor = lease.proof()['donor']
    matches = [i for i,r in enumerate(source['allocations']) if r['name'] == donor['name']]
    need(len(matches) == 1 and source['allocations'][matches[0]] == donor, 'exact retired owner record')
    need(identity(before[lease.START:lease.END]) == dict(size=donor['size'],sha256=donor['content_sha256']), 'whole donor preimage')
    revised = copy.deepcopy(source)
    row = revised['allocations'][matches[0]]
    row.update(name=NAME, owner=OWNER, purpose='PR16 dex codec, typed mapping and fixed ABI veneers; unused suffix remains reserved', content_sha256=hashlib.sha256(after[lease.START:lease.END]).hexdigest())
    report = rebuild_allocation(revised)
    need(report['summaries'] == source['summaries'], 'no new free bytes or overlaps')
    for i,(old,new) in enumerate(zip(source['allocations'],report['allocations'])):
        if i != matches[0]: need(old == new, 'unrelated owner metadata changed')
    return report

def assembly():
    # ARMv4T AAPCS: preserve all four register arguments and stack arguments.
    # r12 is caller-saved. The temporary push is undone before the tail jump.
    lines = ['.syntax unified','.arch armv4t','.thumb','.section .dex_exports,"ax",%progbits','.balign 4']
    for name in EXPORTS:
        label = 'DexEntry_'+name
        lines += ['.global '+label, '.type '+label+', %function', '.thumb_func', label+':',
            'push {r3}', 'ldr r3, 1f', 'mov ip, r3', 'pop {r3}', 'bx ip', 'nop',
            '1: .word '+name, '.size '+label+', .-'+label]
    lines += ['.section .note.GNU-stack,"",%progbits']
    return '\n'.join(lines)+'\n'

def linker_script():
    return ('SECTIONS { . = '+hex(BASE)+'; .text : { KEEP(*(.dex_exports)) KEEP(*(.text*)) '
        'KEEP(*(.rodata*)) *(.v4_bx) *(.glue_7) *(.glue_7t) } '
        '.data : { *(.data*) *(.bss*) *(COMMON) } '
        '/DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) } }\n')

def parse_symbols(text):
    out = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) == 4:
            address,size,kind,name = fields
            need(kind not in 'BbCcDdGgSs', 'no new mutable linker owner')
            need(name not in out, 'unique linker symbols')
            out[name] = dict(address=int(address,16),size=int(size,16),kind=kind)
    return out

def validate_link(payload, symbols):
    need(type(payload) is bytes and len(EXPORTS)*STRIDE < len(payload) <= lease.END-lease.START, 'actual payload fits donor')
    expected = (0xB408,0x4B02,0x469C,0xBC08,0x4760,0x46C0)
    exported = []
    for i,name in enumerate(EXPORTS):
        target = symbols.get(name); entry = symbols.get('DexEntry_'+name)
        need(target is not None and target['kind'] == 'T' and target['size'] > 0, 'real linked API '+name)
        need(entry == dict(address=BASE+i*STRIDE,size=STRIDE,kind='T'), 'fixed ABI veneer slot '+name)
        need(BASE+len(EXPORTS)*STRIDE <= target['address'] < BASE+len(payload), 'implementation stays in owned payload')
        need(target['address']+target['size'] <= BASE+len(payload), 'whole implementation is bounded')
        need(struct.unpack_from('<6H',payload,i*STRIDE) == expected, 'exact register-preserving Thumb veneer')
        pointer = struct.unpack_from('<I',payload,i*STRIDE+12)[0]
        need(pointer == target['address']|1, 'Thumb destination literal matches actual linked implementation')
        exported.append(dict(name=name,entry=entry['address']|1,implementation=pointer,size=target['size']))
    return exported

def link(folder):
    need(not folder.exists(), 'fresh private linker output'); folder.mkdir(parents=True)
    def run(argv):
        p = subprocess.run(argv,cwd=ROOT,capture_output=True,text=True)
        need(p.returncode == 0 and not p.stderr, 'strict compiler/linker failure: '+Path(argv[0]).name+' '+p.stderr[-2000:])
        return p.stdout
    objects=[]
    for path in SOURCES:
        obj=folder/(Path(path).stem+'.o'); run(['arm-none-eabi-gcc',*FLAGS,'-c',str(ROOT/path),'-o',str(obj)]);objects.append(obj)
    asm=folder/'entries.S';asm.write_text(assembly());obj=folder/'entries.o'
    run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-c',str(asm),'-o',str(obj)]);objects.insert(0,obj)
    ld=folder/'placement.ld';ld.write_text(linker_script());elf=folder/'placement.elf'
    run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-nostdlib','-Wl,--build-id=none','-Wl,--gc-sections','-Wl,-e,DexEntry_VegaDexValidate','-Wl,-T,'+str(ld),*map(str,objects),'-lgcc','-o',str(elf)])
    need(not run(['arm-none-eabi-nm','-u',str(elf)]), 'no undefined ARM symbols')
    symbols=parse_symbols(run(['arm-none-eabi-nm','-n','-S','--defined-only',str(elf)]))
    data=folder/'placement.bin';run(['arm-none-eabi-objcopy','-j','.text','-O','binary',str(elf),str(data)])
    payload=data.read_bytes();exports=validate_link(payload,symbols)
    return payload, dict(base=BASE,payload=identity(payload),exports=exports,symbols=symbols,arm_translation_units=4,arm_assembly_units=1,arm_links=1,
        reserved_suffix_bytes=lease.END-lease.START-len(payload),compile_flags=FLAGS,
        toolchain=run(['arm-none-eabi-gcc','--version']).splitlines()[0],mutable_linker_owners=0)

def place(before, payload, symbols):
    preimage=lease.validate_preimage(before);exports=validate_link(payload,symbols)
    after=before[:lease.START]+payload+before[lease.START+len(payload):]
    need(after[lease.START+len(payload):lease.END] == before[lease.START+len(payload):lease.END], 'reserved suffix preserved exactly')
    diff=lease.validate_postimage(before,after)
    allocation=transfer_allocation(allocation_source(),before,after)
    # Independent exact reversal, including every non-owner byte and old learnsets.
    reverse=after[:lease.START]+before[lease.START:lease.END]+after[lease.END:]
    need(reverse==before, 'whole-ROM rollback exact')
    return after, dict(preimage=preimage,diff=diff,exports=exports,allocation=allocation,
        allocator_transferred=True,whole_rom_rollback_exact=True,old_learnset_data_unchanged=True,
        game_hooks_installed=False,save_scheduler_wired=False,consumer_wired=False,
        formal_rom_changed=False,formal_save_changed=False)
