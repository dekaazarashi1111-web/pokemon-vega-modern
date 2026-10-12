#!/usr/bin/env python3
"""QOL空/破損の混同修復。既存136byte ensure_save窓のみを置換。"""
import struct
from pathlib import Path
import pr16_research_v1_load_followup as root
need=root.need;identity=root.identity
SOURCE='overlays/qol_production/qol_production.c'
SOURCE_BEFORE={'size':164678,'sha256':'fc69ca2ff94e98ffb46f1b4117c73156683e83bbc777e9f8527c027c70399423'}
START=0x09378DAC
SIZE=136
PARENT=root.prior.CANDIDATE
FUNCTION='''static VegaSaveStatus restore_durable_ledger(void)
{
    VegaModernSaveData *candidate;
    VegaSaveStatus status;
    FN_READ_FLASH(31u, 0u, PTR(void *, SAVE_BUFFER), SAVE_SECTOR_SIZE);
    candidate = (VegaModernSaveData *)(void *)(
        PTR(u8 *, SAVE_BUFFER)
        + (VEGA_SAVE_EWRAM_ADDRESS - SECTOR31_IMAGE));
    status = FN_SAVE_VALIDATE(candidate, VEGA_SAVE_LEDGER_SIZE);
    /* Only an empty durable ledger permits new-save initialization.  Keep
     * a corrupt preimage for the caller's validation; never normalize it. */
    if (status != VEGA_SAVE_EMPTY_OR_LEGACY)
        copy_bytes(gVegaModernSaveData, candidate, VEGA_SAVE_LEDGER_SIZE);
    return status;
}

static u8 ensure_save(void)
{
    VegaSaveStatus status = FN_SAVE_VALIDATE(gVegaModernSaveData,
                                             VEGA_SAVE_LEDGER_SIZE);
    if (status == VEGA_SAVE_EMPTY_OR_LEGACY)
        status = restore_durable_ledger();
    if (status == VEGA_SAVE_OK)
        return 1u;
    if (status == VEGA_SAVE_EMPTY_OR_LEGACY) {
        FN_SAVE_INIT(gVegaModernSaveData, FN_FLAG_GET(FLAG_BADGE_1));
        return 1u;
    }
    return 0u;
}
'''

def correct_source(raw):
    need(identity(raw)==SOURCE_BEFORE,'exact canonical QOL source')
    text=raw.decode();a=text.index('static u8 restore_durable_ledger(void)\n');b=text.index('\n/* Cross-store transactions',a)
    return (text[:a]+FUNCTION+text[b:]).encode()

PREFIX='''typedef unsigned char u8; typedef unsigned short u16; typedef unsigned u32;
typedef u32 VegaSaveStatus;
typedef struct {u8 bytes[2048];} VegaModernSaveData;
#define PTR(type, address) ((type)(unsigned)(address))
#define SAVE_BUFFER 0x020399B0u
#define SAVE_SECTOR_SIZE 4096u
#define SECTOR31_IMAGE 0x0203CF9Cu
#define VEGA_SAVE_EWRAM_ADDRESS 0x0203D000u
#define VEGA_SAVE_LEDGER_SIZE 2048u
#define VEGA_SAVE_OK 0u
#define VEGA_SAVE_EMPTY_OR_LEGACY 1u
#define FLAG_BADGE_1 0x0820u
#define gVegaModernSaveData PTR(VegaModernSaveData *, VEGA_SAVE_EWRAM_ADDRESS)
#define FN_SAVE_VALIDATE PTR(VegaSaveStatus (*)(const VegaModernSaveData *,u32), 0x092D12E1u)
#define FN_SAVE_INIT PTR(void (*)(VegaModernSaveData *,u8), 0x092D2979u)
#define FN_READ_FLASH PTR(void (*)(u16,u32,void *,u32), 0x081C2A55u)
#define FN_FLAG_GET PTR(u8 (*)(u16), 0x0806DEC5u)
extern void copy_bytes(void *,const void *,u32);
'''

def translation_unit():
    return (PREFIX+FUNCTION.replace('static u8 ensure_save','__attribute__((section(".text.ensure_save"),used)) u8 ensure_save',1)).encode()

def linker_script():
    return '''ENTRY(ensure_save)
SECTIONS {
 . = 0x09378DAC;
 .text : { *(.text.ensure_save) *(.text*) *(.rodata*) }
 /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) }
 ASSERT(SIZEOF(.text) <= 136, "existing QOL ensure_save window overflow")
}
copy_bytes = 0x09378B95;
'''

def apply(parent,code):
    need(identity(parent)==PARENT,'exact accepted parent')
    require_code(code)
    need(0<len(code)<=SIZE and len(code)%2==0,'bounded aligned code')
    off=START-0x08000000;before=parent[off:off+SIZE]
    # Audited adapter BL and literal addresses from the parent disassembly.
    need(before[:6].hex()=='802170b51748','ensure_save prologue binding')
    for loc,value in {0x09378E10:0x0203D000,0x09378E14:0x092D12E1,0x09378E18:0x020399B0,0x09378E1C:0x081C2A55,0x09378E20:0x02039A14,0x09378E24:0x0806DEC5,0x09378E28:0x092D2979}.items():
        need(struct.unpack_from('<I',parent,loc-0x08000000)[0]==value,'rooted QOL literal')
    after=code+b'\xc0\x46'*((SIZE-len(code))//2)
    output=parent[:off]+after+parent[off+SIZE:]
    need(output[:off]+before+output[off+SIZE:]==parent and output!=parent,'exact window/rollback')
    return output,{'schema_version':1,'parent':PARENT,'candidate':identity(output),'offset':off,'size':SIZE,'before':before.hex(),'after':after.hex(),'compiled_code':identity(code),'changed_bytes':sum(a!=b for a,b in zip(before,after)),'outside_declared_changes':0,'rollback_verified':True,'source':SOURCE,'source_functions':['restore_durable_ledger','ensure_save'],'active_baseline_changed':False,'release_ready':False}

CODE={'size':132,'sha256':'752e8aef5af11bf8b0709a5120204803297a86e86f4978fa87121d3bf3bf7809'}
CANDIDATE={'size':33554432,'sha256':'5d1fc9c47225ae8c0a369514b899a062af3699fa3c9a2f617e94ffd5f7dcc1ab'}

def require_code(code):
    need(identity(code)==CODE,'exact reviewed compiled function')

def validate(raw,case,save,baseline):
    """候補identityを先に固定し、旧oracleの期待ROM名だけを局所変換する。"""
    rows=raw.decode().splitlines();need(bool(rows),'nonempty native observations')
    result=root.prior.old.load(rows[-1]);need(result['candidate_sha256']==CANDIDATE['sha256'],'successor identity')
    need(raw.count(CANDIDATE['sha256'].encode())==1,'one candidate receipt')
    rebound=raw.replace(CANDIDATE['sha256'].encode(),PARENT['sha256'].encode(),1)
    value=root.validate(rebound,case,save,baseline)
    return dict(value,candidate_sha256=CANDIDATE['sha256'],stdout=identity(raw),oracle_candidate_rebinding_only=True)
