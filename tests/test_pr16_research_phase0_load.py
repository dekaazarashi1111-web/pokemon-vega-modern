"""通常load内phase0の新規oracleとcanonical adapter境界だけを検証。"""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_research_phase0_load as m
BASE = {'inventory_sha256':'a'*64, 'other_inventory_sha256':'b'*64,
        'party_sha256':'c'*64, 'item_quantity':0, 'party_count':1}


def seed():
    ledger=bytearray(2048);ledger[:8]=b'VGS1\x02\0\0\x08'
    ledger[m.OWNER],ledger[m.OWNER+1],ledger[m.OWNER+6],ledger[m.OWNER+36]=1,64,1,1
    data=bytearray(131072);data[m.OFFSET:m.OFFSET+2048]=m.old.seal(ledger)
    return bytes(data)


def sample(case=m.CASES[0]):
    source=seed()
    with patch.object(m.old.old,'SEED',m.identity(source)):
        save,receipt=m.fixture(source,case)
    ledger=save[m.OFFSET:m.OFFSET+2048];target=m.recovered(ledger,case)
    root={'diagnostic_root':True,'type':0,'research':1,'mirage':1,'qol':1,
          'result':2,'counter':0,'version':0,'last':65535,'root_lr':0x080ED736}
    fixture={'fault_fixture':'availability_word_only','address':0x03005044,'pc':0x093BF630,
             'before':1,'after':0,'word_writes':1,'byte_writes':4,'ewram_unchanged':True,
             'iwram_except_word_unchanged':True,'registers_unchanged':True,'flash_unchanged':True,'guard_rearmed':True}
    rows=[root.copy(),fixture]
    for stage,body,counter,last in (('failed',ledger,2,13),('recovered',target,3,0)):
        failed=stage=='failed'
        if not failed:rows.append(root.copy())
        rows.append(dict(root,result=int(not failed),counter=counter,version=body[4],last=last,root_lr=0x080789FE))
        rows.append({'load_state':stage,'counter':counter,'version':body[4],'checksum_valid':True,
                     'migration_dirty':0,'recovery_blocked':int(failed),'last_result':last,'ledger_sha256':m.identity(body)['sha256']})
        rows.append({'phase0_load_trace':stage,'root_calls':1,'research_calls':1,'mirage_calls':1,'qol_calls':1,
                     'save_calls':1,'phase0':1,'phase1':0,'phase2':0,'native_returns':1,'native_result':255 if failed else 1,
                     'research_result':0 if failed else 1,'root_result':0 if failed else 1,'counter_at_save':2,
                     'available_at_save':0 if failed else 1,'save_type':0,'root_return_pc':0x080789FE,'guarded_host_writes':0,'steps':10000})
        rows.append({'phase0_load_invariants':stage,'input_ledger_restored':failed,'full_flash_unchanged':failed,
                     'other_private_owners_unchanged':True,'durable_matches_ram':True,
                     'flash_sha256':m.identity(save)['sha256'] if failed else 'd'*64})
        if failed:rows.append(dict(BASE,event='failed',counter=2,owner=body[m.OWNER:m.OWNER+64].hex()))
    other=bytearray(target);other[4:6]=bytes(2);other[8:12]=bytes(4);other[m.OWNER:m.OWNER+64]=bytes(64)
    for stage in ('continued','continued_again','continued_third'):
        rows.append(dict(BASE,event=stage,counter=3,owner=target[m.OWNER:m.OWNER+64].hex()))
        rows.append({'ledger_event':stage,'version':2,'size':2048,'checksum_valid':True,'ledger_sha256':m.identity(target)['sha256'],
                     'unrelated_ledger_sha256':m.identity(other)['sha256'],'migration_dirty':0,'recovery_blocked':0})
    rows.append({'cold_recovery':'PASS','normal_loads_after_failure':3,'additional_saves_after_recovery':0,
                 'complete_ledger_equal':True,'availability_restored_by_cold_boot':True})
    rows.append({'status':'PASS','scope':'ORDINARY_LOAD_PHASE0_AVAILABILITY_FIXTURE_AND_COLD_RECOVERY','case':case,
                 'candidate_sha256':m.CANDIDATE['sha256'],'fresh_cores':4,'availability_fixture_words':1,'availability_fixture_byte_writes':4,
                 'host_write_barriers':7,'guarded_host_writes':0,'ram_ledger_fixture_writes':0,'register_fixture_writes':0,
                 'physical_flash_fault_accepted':False,'same_core_menu_retry_accepted':False,'normal_new_game_accepted':False,
                 'transaction_ui_accepted':False,'warnings_errors':0})
    return save,receipt,rows


def encoded(rows):return ('\n'.join(json.dumps(r,separators=(',',':')) for r in rows)+'\n').encode()


class Phase0LoadTests(unittest.TestCase):
    def bad(self,change,case=m.CASES[0]):
        save,_,rows=sample(case);change(rows)
        with self.assertRaises((ValueError,TypeError,KeyError)):
            m.validate(encoded(rows),case,save,BASE)
    def test_both_complete_cases(self):
        for case in m.CASES:
            save,_,rows=sample(case)
            self.assertEqual(m.validate(encoded(rows),case,save,BASE)['fresh_cores'],4)
    def test_only_private_ledger_changes(self):
        for case in m.CASES:
            data,receipt,_=sample(case);original=seed()
            self.assertEqual(data[:m.OFFSET],original[:m.OFFSET]);self.assertEqual(data[m.OFFSET+2048:],original[m.OFFSET+2048:])
            self.assertEqual(receipt['outside_ledger_changes'],0)
    def test_pending_recovery_credits_once(self):
        data,_,_=sample(m.CASES[1]);ledger=data[m.OFFSET:m.OFFSET+2048];target=m.recovered(ledger,m.CASES[1])
        self.assertEqual(struct.unpack_from('<H',target,m.OWNER+4)[0],5)
        self.assertEqual(struct.unpack_from('<I',target,m.OWNER+10)[0],5)
        self.assertEqual(struct.unpack_from('<H',target,m.OWNER+14)[0],5)
        self.assertEqual(target[m.OWNER+44:m.OWNER+60],bytes(16))
        with self.assertRaises(ValueError):m.recovered(target,m.CASES[1])
    def test_unknown_case(self):
        with self.assertRaises(ValueError):m.fixture(seed(),'unknown')
    def test_wrong_seed(self):
        with self.assertRaises(ValueError):m.fixture(seed(),m.CASES[0])
    def test_invalid_seed_checksum(self):
        raw=bytearray(seed());raw[m.OFFSET+8]^=1;raw=bytes(raw)
        with patch.object(m.old.old,'SEED',m.identity(raw)),self.assertRaises(ValueError):m.fixture(raw,m.CASES[1])
    def test_pending_mismatch(self):
        data,_,_=sample(m.CASES[1]);ledger=bytearray(data[m.OFFSET:m.OFFSET+2048]);ledger[m.OWNER+52]=6
        with self.assertRaises(ValueError):m.recovered(m.old.seal(ledger),m.CASES[1])
    def test_recovery_checksum(self):
        data,_,_=sample();ledger=bytearray(data[m.OFFSET:m.OFFSET+2048]);ledger[8]^=1
        with self.assertRaises(ValueError):m.recovered(ledger,m.CASES[0])
    def test_fixture_address(self):self.bad(lambda r:r[1].update(address=m.AVAILABLE+4))
    def test_fixture_phase(self):self.bad(lambda r:r[1].update(pc=m.PHASE0+2))
    def test_fixture_extra_write(self):self.bad(lambda r:r[1].update(byte_writes=5))
    def test_fixture_flash_write(self):self.bad(lambda r:r[1].update(flash_unchanged=False))
    def test_fixture_register_write(self):self.bad(lambda r:r[1].update(registers_unchanged=False))
    def test_fixture_ewram_write(self):self.bad(lambda r:r[1].update(ewram_unchanged=False))
    def test_guard_not_rearmed(self):self.bad(lambda r:r[1].update(guard_rearmed=False))
    def test_wrong_boot_caller(self):self.bad(lambda r:r[0].update(root_lr=0x080789FE))
    def test_failure_hidden(self):self.bad(lambda r:r[2].update(result=1))
    def test_error_lost(self):self.bad(lambda r:r[3].update(last_result=0))
    def test_rollback_not_whole(self):self.bad(lambda r:r[3].update(ledger_sha256='0'*64))
    def test_failed_native_result(self):self.bad(lambda r:r[4].update(native_result=1))
    def test_failed_counter_advanced(self):self.bad(lambda r:r[3].update(counter=3))
    def test_failed_flash_changed(self):self.bad(lambda r:r[5].update(full_flash_unchanged=False))
    def test_failure_owner_lost(self):self.bad(lambda r:r[6].update(owner='00'*64),m.CASES[1])
    def test_recovery_extra_save(self):self.bad(lambda r:r[10].update(save_calls=2))
    def test_recovery_missing_save(self):self.bad(lambda r:r[10].update(phase0=0))
    def test_recovery_flash_digest(self):self.bad(lambda r:r[11].update(flash_sha256='z'*64))
    def test_recovery_durable_mismatch(self):self.bad(lambda r:r[11].update(durable_matches_ram=False))
    def test_reward_duplicated(self):
        def mutate(rows):
            owner=bytearray.fromhex(rows[14]['owner']);owner[4]=10;rows[14]['owner']=owner.hex()
        self.bad(mutate,m.CASES[1])
    def test_unrelated_ledger_changed(self):self.bad(lambda r:r[13].update(unrelated_ledger_sha256='0'*64))
    def test_bag_changed(self):self.bad(lambda r:r[12].update(inventory_sha256='0'*64))
    def test_party_changed(self):self.bad(lambda r:r[16].update(party_sha256='0'*64))
    def test_counter_bool_rejected(self):self.bad(lambda r:r[4].update(counter_at_save=True))
    def test_steps_bool_rejected(self):self.bad(lambda r:r[4].update(steps=True))
    def test_truncated_output(self):self.bad(lambda r:r.pop(18))
    def test_extra_output(self):self.bad(lambda r:r.append(r[-1]))
    def test_injected_unknown_key(self):self.bad(lambda r:r[10].update(ignored=True))
    def test_ui_overclaim(self):self.bad(lambda r:r[-1].update(transaction_ui_accepted=True))
    def test_physical_fault_overclaim(self):self.bad(lambda r:r[-1].update(physical_flash_fault_accepted=True))
    def test_same_core_overclaim(self):self.bad(lambda r:r[-1].update(same_core_menu_retry_accepted=True))
    def test_wrong_candidate(self):self.bad(lambda r:r[-1].update(candidate_sha256='0'*64))
    def test_wrong_core_count(self):self.bad(lambda r:r[-1].update(fresh_cores=3))
    def test_guard_count(self):self.bad(lambda r:r[-1].update(host_write_barriers=6))
    def test_canonical_adapter_failure_contract(self):
        text=(ROOT/m.SOURCE).read_text();token='u8 ResearchEconomy_SaveLoadAdapter(u8 save_type)\n'
        self.assertEqual(text.count(token),1);a=text.index(token);b=text.index('\n}\n',a)+3;body=text[a:b]
        prefix=r'''
#include <assert.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;
static u8 ledger[2048],rollback[2048],input[2048];
static struct {u8 migration_dirty,recovery_blocked;} state;
static u16 special,last;static unsigned calls,saves,recoveries,resets,copies;
static u8 delegated,persist_ok,promoted;static u32 validation,migration;static u16 recovery;
#define G_LEDGER ledger
#define G_SAVE_ROLLBACK rollback
#define G_VOLATILE (&state)
#define G_SPECIAL_RESULT (&special)
#define RESEARCH_ECONOMY_LEDGER_SIZE 2048u
#define LEDGER_VERSION_OFFSET 4u
#define LEDGER_VERSION_V1 1u
#define SAVE_OK 0u
#define RESEARCH_RESULT_SUCCESS 0u
#define RESEARCH_RESULT_EFFECTLESS 1u
#define RESEARCH_RESULT_CORRUPT_SAVE 7u
#define RESEARCH_RESULT_PERSIST_FAILED 13u
static void reset_volatile_state(void){++resets;memset(&state,0,sizeof(state));}
static u8 load(u8 type){assert(type==0);++calls;memcpy(ledger,input,2048);memcpy(rollback,input,2048);if(promoted){ledger[4]=2;ledger[123]^=0xA5;state.migration_dirty=1;}return delegated;}
#define FN_MIRAGE_SAVE_LOAD load
static u32 ResearchEconomy_SaveValidate(const void*p,u32 n){assert(p==ledger&&n==2048);return validation;}
static u16 read_u16(const u8*p){return (u16)(p[0]|p[1]<<8);}
static u32 ResearchEconomy_MigrateV1(void*p,u32 n){assert(p==ledger&&n==2048);if(!migration){ledger[4]=2;ledger[123]^=0xA5;state.migration_dirty=1;}return migration;}
static u8 persist_phase(u8 phase){assert(phase==0);++saves;return persist_ok;}
static void copy_bytes(u8*dst,const u8*src,u32 n){assert(dst==ledger&&src==rollback&&n==2048);++copies;memcpy(dst,src,n);}
static u16 recover_internal(void){++recoveries;if(recovery==13)state.recovery_blocked=1;return recovery;}
static u16 set_result(u16 value){return special=last=value;}
'''
        suffix=r'''
int main(void){unsigned mode,k;for(mode=0;mode<2;++mode){
for(k=0;k<2048;++k)input[k]=(u8)(k*13+3);input[4]=1;input[5]=0;
delegated=1;validation=migration=0;promoted=mode;persist_ok=0;recovery=1;calls=saves=recoveries=resets=copies=0;
assert(ResearchEconomy_SaveLoadAdapter(0)==0);assert(calls==1&&saves==1&&recoveries==0&&resets==1&&copies==1);
assert(last==13&&special==13&&!state.migration_dirty&&state.recovery_blocked==1&&!memcmp(ledger,input,2048));
persist_ok=1;assert(ResearchEconomy_SaveLoadAdapter(0)==1);assert(calls==2&&saves==2&&recoveries==1&&resets==2&&copies==1);
assert(last==0&&special==0&&!state.migration_dirty&&!state.recovery_blocked&&ledger[4]==2);
}
promoted=0;input[4]=2;recovery=13;calls=saves=recoveries=resets=copies=0;
assert(ResearchEconomy_SaveLoadAdapter(0)==0);assert(calls==1&&saves==0&&recoveries==1&&last==13&&state.recovery_blocked);
recovery=0;assert(ResearchEconomy_SaveLoadAdapter(0)==1);assert(last==0&&!state.recovery_blocked);
delegated=2;assert(ResearchEconomy_SaveLoadAdapter(0)==2&&special==2);assert(recoveries==2);
puts("PASS canonical adapter: migration rollback paths 2, recovery propagation, subsequent load reset, delegate rejection");return 0;}
'''
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'adapter.c';exe=Path(tmp)/'adapter';source.write_text(prefix+body+suffix)
            build=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',str(source),'-o',str(exe)],capture_output=True,timeout=30)
            self.assertEqual((build.returncode,build.stderr),(0,b''),build.stderr.decode())
            run=subprocess.run([str(exe)],capture_output=True,timeout=10)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertTrue(run.stdout.startswith(b'PASS canonical adapter:'))


if __name__=='__main__':unittest.main()
