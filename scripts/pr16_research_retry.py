#!/usr/bin/env python3
"""phase0再試行修正。単一C関数を既存188byte窓へ限定linkする。"""
from __future__ import annotations
import re
import struct
import subprocess
from pathlib import Path
import pr16_research_lifecycle as lc
import pr16_research_bag_delegate as bag
need, identity = bag.need, bag.identity
SOURCE = bag.SOURCE
BEFORE_SOURCE = bag.SOURCE_AFTER
OFFSET, WINDOW = 0x13BF7C8, 188
BEFORE_CODE = 'ddc9c31a8de2e74bdaa2eee6a42cc25ea9adb57e4e5162c9e5fbb72faecd8fda'
ROOTS = {'ensure_volatile_state':0x093BEE79, 'ResearchEconomy_SaveValidate':0x093BD9A9,
         'ResearchEconomy_SaveInitNew':0x093BDE81, 'flag_get':0x093BF2D5,
         'persist_phase':0x093BF631, 'ResearchEconomy_MigrateV1':0x093BDEF1,
         'recover_internal':0x093BF6A9, 'copy_bytes':0x093BEE0B}
FUNCTION = '''static u8 ensure_save_idle(void)
{
    u32 status;
    ensure_volatile_state();
    status = ResearchEconomy_SaveValidate((const void *)G_LEDGER,
                                           RESEARCH_ECONOMY_LEDGER_SIZE);
    if (status == SAVE_EMPTY) {
        /* 未保存V2を有効扱いして再試行を素通りさせない。
         * 初期化前の全byteを保持し、失敗時はV1と同じく復元する。 */
        copy_bytes(G_SAVE_ROLLBACK, G_LEDGER,
                   RESEARCH_ECONOMY_LEDGER_SIZE);
        ResearchEconomy_SaveInitNew((void *)G_LEDGER, flag_get(FLAG_BADGE_1));
    } else if (status != SAVE_OK) {
        return 0u;
    } else if (read_u16(G_LEDGER + LEDGER_VERSION_OFFSET)
                    != LEDGER_VERSION_V1) {
        goto recover;
    } else if (ResearchEconomy_MigrateV1((void *)G_LEDGER,
                                        RESEARCH_ECONOMY_LEDGER_SIZE)
                    != SAVE_OK) {
        goto failed;
    }
    if (!persist_phase(0u))
        goto failed;
    G_VOLATILE->migration_dirty = 0u;
recover:
    if (G_OWNER[OWNER_PENDING_KIND] != PENDING_NONE
        || G_VOLATILE->recovery_blocked) {
        u16 recovery = recover_internal();
        if (recovery != RESEARCH_RESULT_SUCCESS
            && recovery != RESEARCH_RESULT_EFFECTLESS)
            return 0u;
    }
    return 1u;
failed:
    if (status == SAVE_EMPTY || G_VOLATILE->migration_dirty)
        copy_bytes(G_LEDGER, G_SAVE_ROLLBACK,
                   RESEARCH_ECONOMY_LEDGER_SIZE);
    G_VOLATILE->migration_dirty = 0u;
    G_VOLATILE->recovery_blocked = 1u;
    return 0u;
}
'''


def function_span(text):
    token = 'static u8 ensure_save_idle(void)\n'
    need(text.count(token) == 1, 'unique canonical idle function')
    start = text.index(token)
    end = text.index('\n}\n', start) + 3
    return start, end


def correct_source(raw):
    need(identity(raw) == BEFORE_SOURCE, 'exact canonical preimage')
    text = raw.decode('utf-8'); start, end = function_span(text)
    result = (text[:start] + FUNCTION + text[end:]).encode('utf-8')
    need(result != raw, 'actual source correction')
    return result


def translation_unit(corrected):
    """canonical関数本文とvolatile型はそのまま採用。外部呼出しだけ既存symbolへ結合。"""
    text = corrected.decode('utf-8'); start, end = function_span(text)
    need(text[start:end] == FUNCTION, 'exact corrected function body')
    a = text.index('typedef struct ResearchEconomyVolatileState {')
    b = text.index('_Static_assert(sizeof(struct Task)', a)
    prefix = '''#include <stddef.h>
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned u32;
#define RESEARCH_ECONOMY_SHOP_COUNT 23
''' + text[a:b] + '''
_Static_assert(sizeof(ResearchEconomyVolatileState) == 96, "volatile ABI");
_Static_assert(offsetof(ResearchEconomyVolatileState, migration_dirty) == 26, "dirty ABI");
_Static_assert(offsetof(ResearchEconomyVolatileState, recovery_blocked) == 27, "blocked ABI");
#define G_VOLATILE ((volatile ResearchEconomyVolatileState*)0x0203F0A0u)
#define G_LEDGER ((volatile u8*)0x0203D000u)
#define G_OWNER ((volatile u8*)0x0203D73Fu)
#define G_SAVE_ROLLBACK ((volatile u8*)0x0203E400u)
#define RESEARCH_ECONOMY_LEDGER_SIZE 2048u
#define OWNER_PENDING_KIND 48
#define PENDING_NONE 0
#define SAVE_OK 0
#define SAVE_EMPTY 1
#define LEDGER_VERSION_OFFSET 4
#define LEDGER_VERSION_V1 1
#define FLAG_BADGE_1 0x0820
#define RESEARCH_RESULT_SUCCESS 0
#define RESEARCH_RESULT_EFFECTLESS 1
extern void ensure_volatile_state(void);
extern u32 ResearchEconomy_SaveValidate(const void*,u32);
extern void ResearchEconomy_SaveInitNew(void*,u8);
extern u8 flag_get(u16);
extern u8 persist_phase(u8);
extern u32 ResearchEconomy_MigrateV1(void*,u32);
extern u16 recover_internal(void);
extern void copy_bytes(volatile void*,const volatile void*,u32);
static inline u16 read_u16(const volatile u8*p){return p[0]|((u16)p[1]<<8);}
'''
    function = FUNCTION.replace('static u8 ensure_save_idle',
        '__attribute__((section(".text.ensure_save_idle"),used)) u8 ensure_save_idle', 1)
    return (prefix + function).encode('utf-8')


def linker_script():
    return '''ENTRY(ensure_save_idle)
SECTIONS {
 . = 0x093BF7C8;
 .text : { *(.text.ensure_save_idle) *(.text*) *(.rodata*) }
 /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) }
 ASSERT(SIZEOF(.text) <= 188, "existing idle function window overflow")
}
''' + ''.join(f'{k} = {v:#010x};\n' for k,v in ROOTS.items())


def direct_calls(code, address=0x093BF7C8):
    result = []
    for i in range(0, len(code)-3, 2):
        a,b = struct.unpack_from('<HH',code,i)
        if a & 0xF800 == 0xF000 and b & 0xF800 == 0xF800:
            delta = ((a & 2047)<<12) | ((b & 2047)<<1)
            if delta & 0x400000: delta -= 0x800000
            result.append({'address':address+i,'target':address+i+4+delta})
    return result


def apply(parent, code):
    need(identity(parent) == bag.CANDIDATE, 'exact accepted parent')
    before = parent[OFFSET:OFFSET+WINDOW]
    need(identity(before)['sha256'] == BEFORE_CODE, 'old function extent')
    need(0 < len(code) <= WINDOW and len(code)%2 == 0, 'bounded Thumb code')
    old_calls = direct_calls(before); calls = direct_calls(code)
    targets = {v&~1 for v in ROOTS.values()}
    need({x['target'] for x in old_calls} == targets, 'rooted parent callees')
    need({x['target'] for x in calls} == targets, 'no new/unrooted callee')
    need(sum(x['target'] == (ROOTS['copy_bytes']&~1) for x in calls) == 2,
         'snapshot and rollback both linked')
    after = code + b'\xc0\x46' * ((WINDOW-len(code))//2)
    output = parent[:OFFSET] + after + parent[OFFSET+WINDOW:]
    need(output != parent and len(output) == len(parent), 'actual bounded ROM delta')
    need(output[:OFFSET] == parent[:OFFSET] and output[OFFSET+WINDOW:] == parent[OFFSET+WINDOW:],
         'all-ROM outside-window invariant')
    need(output[:OFFSET]+before+output[OFFSET+WINDOW:] == parent, 'full rollback')
    return output, {'schema_version':1, 'parent':identity(parent),'candidate':identity(output),
        'offset':OFFSET,'size':WINDOW,'before':before.hex(),'after':after.hex(),
        'compiled_code':identity(code),'changed_bytes':sum(a!=b for a,b in zip(before,after)),
        'calls':calls,'rooted_helpers':ROOTS,'outside_declared_changes':0,'rollback_verified':True,
        'source':SOURCE,'source_function':'ensure_save_idle',
        'scope_ja':'単一canonical C関数を既存188byte窓にlink。新規配置/旧overlay再buildなし。研究idle初期化/移行/拒否/回復の影響だけを検証。',
        'active_baseline_changed':False,'release_ready':False}


CASES = ('retry-zero','retry-erased','retry-v1','reject-v1-checksum','reject-v1-tail','valid-v2-idle','valid-v2-blocked')
STAGES = ('baseline','fixture','failed_first','failed_second','retried','idle','continued','continued_again')
SCOPE = 'SAME_CORE_PHASE0_RETRY_SCOPED_NOT_NORMAL_UI'


def expected_calls(case):
    if case.startswith('retry-'):
        return [dict(result=7,saves=1,phase0=1,native_result=255,counter_delta=0),
                dict(result=7,saves=1,phase0=1,native_result=255,counter_delta=0),
                dict(result=5,saves=1,phase0=1,native_result=1,counter_delta=1),
                dict(result=5,saves=0,phase0=0,native_result=0,counter_delta=1)]
    result = 7 if case.startswith('reject-') else 5
    return [dict(result=result,saves=0,phase0=0,native_result=0,counter_delta=0)]*4


def validate(raw, case, candidate):
    need(case in CASES and len(raw) <= 40000, 'bounded declared retry case')
    rows = [lc.old.load(line) for line in raw.decode('utf-8').splitlines()]
    need(len(rows) == 21, 'eight paired observations/four calls/result')
    events,ledgers,calls = [],[],[]
    for i,stage in enumerate(STAGES):
        at = 2*i + max(0,min(i-2,4))
        event,ledger = rows[at:at+2]
        need(set(event)==lc.EVENT_FIELDS and event['event']==stage,'event schema/order')
        need(set(ledger)==lc.LEDGER_FIELDS and ledger['ledger_event']==stage,'ledger schema/order')
        events.append(event);ledgers.append(ledger)
        if 2 <= i <= 5: calls.append(rows[at+2])
    expected = expected_calls(case);retry = case.startswith('retry-');reject = case.startswith('reject-')
    for n,(call,want) in enumerate(zip(calls,expected)):
        fields=dict(call=n+1,loads=0,phase1=0,phase2=0,native_returns=want['saves'],destroy_calls=1,
                    host_task_writes_during_observation=0,**want)
        need(set(call)==set(fields),'call schema')
        for k,v in fields.items():need(type(call[k]) is type(v) and call[k]==v,'call '+k)
    first=events[0]
    for i,(event,ledger) in enumerate(zip(events,ledgers)):
        lc.old.integer(event['counter'],1,100,'counter');lc.old.integer(event['item_quantity'],0,999,'quantity')
        lc.old.integer(event['party_count'],1,6,'party count')
        for k in ('inventory_sha256','other_inventory_sha256','party_sha256'):
            lc.old.digest(event[k]);need(event[k]==first[k],'unchanged '+k)
        need(event['item_quantity']==first['item_quantity'] and event['party_count']==first['party_count'],'Bag/party count')
        need(event['counter']==first['counter']+int(retry and i>=4),'only recovered retry commits once')
        need(isinstance(event['owner'],str) and re.fullmatch('[0-9a-f]{128}',event['owner']),'complete owner')
        for k in ('ledger_sha256','unrelated_ledger_sha256'):lc.old.digest(ledger[k])
        lc.old.integer(ledger['version'],0,65535,'version');lc.old.integer(ledger['size'],0,65535,'size')
        need(type(ledger['checksum_valid']) is bool,'checksum bool')
        need(type(ledger['migration_dirty']) is int and ledger['migration_dirty']==0,'dirty clear')
        blocked = int((retry and i in (2,3)) or (case=='valid-v2-blocked' and i==1))
        need(type(ledger['recovery_blocked']) is int and ledger['recovery_blocked']==blocked,'blocked transition')
        if retry and i in (2,3) or reject and i in (2,3,4,5):
            need(ledger['ledger_sha256']==ledgers[1]['ledger_sha256'] and event['owner']==events[1]['owner'], 'complete preimage rollback/rejection')
        if retry and i>=4:
            lc.owner_initial(event['owner'])
            need(ledger['version']==2 and ledger['size']==2048 and ledger['checksum_valid'],'persisted valid V2')
        if case=='retry-v1' and i>=4:
            need(ledger['unrelated_ledger_sha256']==ledgers[1]['unrelated_ledger_sha256'],'migration unrelated bytes')
        if case.startswith('valid-v2') and i>=1:
            need(ledger['ledger_sha256']==ledgers[0]['ledger_sha256'] and event['owner']==first['owner'],'valid V2 unchanged')
    for i in (6,7):
        ref=0 if reject else 5
        need({k:v for k,v in events[i].items() if k!='event'}=={k:v for k,v in events[ref].items() if k!='event'},'durable owner/Bag/party')
        need({k:v for k,v in ledgers[i].items() if k!='ledger_event'}=={k:v for k,v in ledgers[ref].items() if k!='ledger_event'},'full durable ledger idempotence')
    result=rows[-1]
    want={'status':'PASS','scope':SCOPE,'case':case,'candidate_sha256':candidate['sha256'],
          'same_core_calls':4,'fresh_cores':3,'host_write_barriers':7,'normal_ui_accepted':False,
          'physical_flash_fault_accepted':False,'v1_load_adapter_accepted':False,'warnings_errors':0}
    need(set(result)==set(want),'result schema')
    for k,v in want.items():need(type(result[k]) is type(v) and result[k]==v,'result '+k)
    return dict(result,calls=calls,observations=events,ledger_observations=ledgers,stdout=identity(raw))
