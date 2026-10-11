"""再試行oracleとcanonical関数の分岐だけ。旧native/unitを呼ばない。"""
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_research_retry as p
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE={'size':33554432,'sha256':'a'*64}
AFTER={'size':63636,'sha256':'08375e4c9c65f698358b92c4eb1c8439fe5e70e7d7ddd9d17854edce4b58abda'}


def corrected():
    raw=(ROOT/p.SOURCE).read_bytes()
    if p.identity(raw)==p.BEFORE_SOURCE:return p.correct_source(raw)
    assert p.identity(raw)==AFTER
    return raw


def sample(case):
    owner=bytearray(64);owner[0]=1;owner[1]=64;owner[6]=1;owner[36]=1
    digest=hashlib.sha256(b'only synthetic oracle input').hexdigest();rows=[]
    retry=case.startswith('retry-');reject=case.startswith('reject-')
    for i,stage in enumerate(p.STAGES):
        fixture=(retry and i in (1,2,3)) or (reject and i in (1,2,3,4,5))
        ev={'event':stage,'counter':2+int(retry and i>=4),'item_quantity':0,'party_count':6,
            'owner':('00'*64 if fixture else owner.hex()),'inventory_sha256':digest,
            'other_inventory_sha256':digest,'party_sha256':digest}
        ledger={'ledger_event':stage,'version':1 if fixture else 2,'size':2048,'checksum_valid':True,
                'ledger_sha256':('0'*64 if fixture else digest),'unrelated_ledger_sha256':digest,
                'migration_dirty':0,'recovery_blocked':int((retry and i in (2,3)) or (case=='valid-v2-blocked' and i==1))}
        rows.extend((ev,ledger))
        if 2<=i<=5:
            want=p.expected_calls(case)[i-2]
            rows.append(dict(call=i-1,loads=0,phase1=0,phase2=0,native_returns=want['saves'],
                             destroy_calls=1,host_task_writes_during_observation=0,**want))
    rows.append({'status':'PASS','scope':p.SCOPE,'case':case,'candidate_sha256':CANDIDATE['sha256'],
                 'same_core_calls':4,'fresh_cores':3,'host_write_barriers':7,'normal_ui_accepted':False,
                 'physical_flash_fault_accepted':False,'v1_load_adapter_accepted':False,'warnings_errors':0})
    return rows


def raw(rows):return ('\n'.join(json.dumps(x) for x in rows)+'\n').encode()


class RetryTests(unittest.TestCase):
    def bad(self,fn,case='retry-zero'):
        rows=sample(case);fn(rows)
        with self.assertRaises((ValueError,KeyError,TypeError)):p.validate(raw(rows),case,CANDIDATE)
    def test_seven_synthetic_cases(self):
        for case in p.CASES:self.assertEqual(p.validate(raw(sample(case)),case,CANDIDATE)['same_core_calls'],4)
    def test_second_failure_skips_save(self):self.bad(lambda r:r[9].update(saves=0))
    def test_second_failure_clears_block(self):self.bad(lambda r:r[8].update(recovery_blocked=0))
    def test_first_failure_loses_preimage(self):self.bad(lambda r:r[5].update(ledger_sha256='2'*64))
    def test_second_failure_loses_preimage(self):self.bad(lambda r:r[8].update(ledger_sha256='2'*64))
    def test_success_did_not_persist(self):self.bad(lambda r:r[12].update(saves=0))
    def test_success_counter_unchanged(self):self.bad(lambda r:r[10].update(counter=2))
    def test_duplicate_commit(self):self.bad(lambda r:r[15].update(saves=1))
    def test_native_failure_hidden(self):self.bad(lambda r:r[12].update(native_result=255))
    def test_destroy_task_missing(self):self.bad(lambda r:r[9].update(destroy_calls=0))
    def test_host_task_write(self):self.bad(lambda r:r[9].update(host_task_writes_during_observation=1))
    def test_bag_change(self):self.bad(lambda r:r[7].update(inventory_sha256='3'*64))
    def test_party_change(self):self.bad(lambda r:r[7].update(party_sha256='3'*64))
    def test_continue_loses_data(self):self.bad(lambda r:r[17].update(ledger_sha256='4'*64))
    def test_second_continue_change(self):self.bad(lambda r:r[19].update(ledger_sha256='4'*64))
    def test_owner_change(self):self.bad(lambda r:r[7].update(owner='12'*64))
    def test_dirty_flag(self):self.bad(lambda r:r[8].update(migration_dirty=1))
    def test_counter_bool(self):self.bad(lambda r:r[7].update(counter=True))
    def test_case_order(self):self.bad(lambda r:r[7].update(event='failed_first'))
    def test_missing_row(self):
        with self.assertRaises(ValueError):p.validate(raw(sample('retry-zero')[:-2]),'retry-zero',CANDIDATE)
    def test_duplicate_json_key(self):
        value=raw(sample('retry-zero')).replace(b'"destroy_calls": 1',b'"destroy_calls": 1, "destroy_calls": 1',1)
        with self.assertRaises(ValueError):p.validate(value,'retry-zero',CANDIDATE)
    def test_ui_overclaim(self):self.bad(lambda r:r[-1].update(normal_ui_accepted=True))
    def test_load_overclaim(self):self.bad(lambda r:r[-1].update(v1_load_adapter_accepted=True))
    def test_physical_overclaim(self):self.bad(lambda r:r[-1].update(physical_flash_fault_accepted=True))
    def test_canonical_source(self):
        value=corrected();self.assertEqual(p.identity(value),AFTER)
        self.assertIn(p.FUNCTION.encode().replace(b'static u8 ensure_save_idle',b'__attribute__((section(".text.ensure_save_idle"),used)) u8 ensure_save_idle'),p.translation_unit(value))
    def test_wrong_source(self):
        with self.assertRaises(ValueError):p.correct_source(b'not the canonical source')
    def test_translation_drift(self):
        with self.assertRaises(ValueError):p.translation_unit(corrected().replace(b'goto failed;',b'return 1u;',1))
    def test_linker_window_and_roots(self):
        value=p.linker_script();self.assertIn('SIZEOF(.text) <= 188',value)
        for name,address in p.ROOTS.items():self.assertIn(f'{name} = {address:#010x};',value)
    def test_host_canonical_control_flow(self):
        """nativeとは別の明記済みstubで、移行失敗/既存pending分岐も網羅する。"""
        tu=p.translation_unit(corrected()).decode();at=tu.index('__attribute__')
        shim='''
#include <assert.h>
#include <string.h>
static u8 ledger[2048],backup[2048];
static ResearchEconomyVolatileState state;
static unsigned available,saves,commits,recovery_calls,migrate_error,recovery_result,bad;
#undef G_LEDGER
#undef G_OWNER
#undef G_SAVE_ROLLBACK
#undef G_VOLATILE
#define G_LEDGER ledger
#define G_OWNER (ledger+0x73f)
#define G_SAVE_ROLLBACK backup
#define G_VOLATILE (&state)
'''
        mocks='''
void ensure_volatile_state(void){}
void copy_bytes(volatile void*d,const volatile void*s,u32 n){memcpy((void*)d,(const void*)s,n);}
u32 ResearchEconomy_SaveValidate(const void*x,u32 n){
 assert(x==ledger&&n==2048);if(bad)return bad;
 unsigned z=0,f=0;for(unsigned i=0;i<n;++i){z+=ledger[i]==0;f+=ledger[i]==255;}
 return z==n||f==n?1:0;
}
void ResearchEconomy_SaveInitNew(void*x,u8 flag){assert(x==ledger&&flag==1);memset(ledger,0,2048);ledger[4]=2;}
u8 flag_get(u16 f){assert(f==0x0820);return 1;}
u8 persist_phase(u8 phase){assert(phase==0);++saves;if(available)++commits;return available;}
u32 ResearchEconomy_MigrateV1(void*x,u32 n){assert(x==ledger&&n==2048);if(migrate_error==1)return 5;memcpy(backup,ledger,n);ledger[4]=2;state.migration_dirty=1;return migrate_error==2?5:0;}
u16 recover_internal(void){++recovery_calls;if(recovery_result<=1)state.recovery_blocked=0;return recovery_result;}
static void reset(unsigned version,unsigned fill){memset(ledger,fill,2048);memset(backup,0,2048);memset(&state,0,sizeof(state));available=saves=commits=recovery_calls=migrate_error=bad=0;recovery_result=1;if(version){ledger[0]=0x56;ledger[4]=version;ledger[5]=0;}}
int main(void){
 for(unsigned fill=0;fill<2;++fill){u8 pre[2048];reset(0,fill?255:0);memcpy(pre,ledger,2048);
  assert(ensure_save_idle()==0&&saves==1&&state.recovery_blocked==1&&!memcmp(pre,ledger,2048));
  assert(ensure_save_idle()==0&&saves==2&&!memcmp(pre,ledger,2048));
  available=1;assert(ensure_save_idle()==1&&saves==3&&commits==1&&ledger[4]==2);
  assert(ensure_save_idle()==1&&saves==3&&state.recovery_blocked==0);
 }
 for(unsigned fail=0;fail<3;++fail){u8 pre[2048];reset(1,0);memcpy(pre,ledger,2048);migrate_error=fail;
  assert(ensure_save_idle()==0&&state.recovery_blocked==1&&state.migration_dirty==0&&!memcmp(pre,ledger,2048));
  assert(saves==(fail?0:1));
 }
 reset(1,0);available=1;assert(ensure_save_idle()==1&&saves==1&&state.migration_dirty==0);
 for(unsigned status=2;status<=8;++status){reset(2,0);bad=status;assert(ensure_save_idle()==0&&saves==0&&recovery_calls==0);}
 reset(2,0);assert(ensure_save_idle()==1&&saves==0&&recovery_calls==0);
 for(unsigned result=0;result<4;++result){reset(2,0);state.recovery_blocked=1;recovery_result=result;
  assert(ensure_save_idle()==(result<=1)&&recovery_calls==1&&saves==0);
  reset(2,0);G_OWNER[48]=1;recovery_result=result;
  assert(ensure_save_idle()==(result<=1)&&recovery_calls==1&&saves==0);
 }
 return 0;
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/'retry.c';exe=Path(tmp)/'retry'
            src.write_text(tu[:at]+shim+tu[at:]+mocks)
            compile_result=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(src),'-o',str(exe)],capture_output=True,timeout=30)
            self.assertEqual(compile_result.returncode,0,compile_result.stderr.decode())
            self.assertEqual(compile_result.stderr,b'')
            subprocess.run([str(exe)],check=True,timeout=10)

if __name__=='__main__':unittest.main()
