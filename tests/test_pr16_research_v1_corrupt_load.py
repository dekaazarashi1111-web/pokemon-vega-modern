"""新しい空/破損分岐と候補bindingだけを検証する。旧unit/nativeなし。"""
import json
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts'),str(Path(__file__).parent)]
import pr16_research_v1_corrupt_load as m
from test_pr16_research_v1_load import sample,encoded,BASE

class CorruptLoadTests(unittest.TestCase):
    def test_host_status_matrix(self):
        prefix=r'''
#include <assert.h>
#include <string.h>
#include <stdio.h>
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned u32;
typedef unsigned VegaSaveStatus; typedef struct {u8 bytes[2048];} VegaModernSaveData;
static VegaModernSaveData ram; static u8 buffer[4096],flash[4096];
static unsigned ram_status,flash_status,reads,copies,inits,flags;
#define PTR(type, address) ((type)(address))
#define SAVE_BUFFER buffer
#define SAVE_SECTOR_SIZE 4096u
#define SECTOR31_IMAGE 0u
#define VEGA_SAVE_EWRAM_ADDRESS 100u
#define VEGA_SAVE_LEDGER_SIZE 2048u
#define VEGA_SAVE_OK 0u
#define VEGA_SAVE_EMPTY_OR_LEGACY 1u
#define FLAG_BADGE_1 0x0820u
#define gVegaModernSaveData (&ram)
static unsigned validate(const VegaModernSaveData*p,unsigned n){assert(n==2048);assert(p==&ram||(const void*)p==buffer+100);return p==&ram?ram_status:flash_status;}
static void read_flash(u16 s,u32 o,void*p,u32 n){assert(s==31&&o==0&&p==buffer&&n==4096);++reads;memcpy(buffer,flash,n);}
static u8 flag_get(u16 flag){assert(flag==0x0820);++flags;return 1;}
static void initialize(VegaModernSaveData*p,u8 flag){assert(p==&ram&&flag==1);++inits;memset(p,0xCC,2048);}
static void copy_bytes(void*dst,const void*src,u32 n){assert(dst==&ram&&src==buffer+100&&n==2048);++copies;memcpy(dst,src,n);}
#define FN_SAVE_VALIDATE validate
#define FN_READ_FLASH read_flash
#define FN_FLAG_GET flag_get
#define FN_SAVE_INIT initialize
'''
        suffix=r'''
int main(void){unsigned a,b,k;u8 original[2048],flash_before[4096];
for(a=0;a<10;++a)for(b=0;b<10;++b){
for(k=0;k<2048;++k)ram.bytes[k]=(u8)(k*13+7);
for(k=0;k<4096;++k)flash[k]=(u8)(k*17+3);
memcpy(original,&ram,2048);memcpy(flash_before,flash,4096);
ram_status=a;flash_status=b;reads=copies=inits=flags=0;
unsigned result=ensure_save();
assert(result==(a==0||(a==1&&(b==0||b==1))));
assert(reads==(a==1));assert(copies==(a==1&&b!=1));assert(inits==(a==1&&b==1));assert(flags==inits);
if(a==1&&b!=1)assert(!memcmp(&ram,flash+100,2048));
else if(inits){for(k=0;k<2048;++k)assert(ram.bytes[k]==0xCC);}
else assert(!memcmp(&ram,original,2048));
assert(!memcmp(flash,flash_before,4096));
}
puts("PASS 100 canonical status pairs; corrupt preimage retained; Flash unchanged");return 0;}
'''
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'contract.c';exe=Path(tmp)/'contract';source.write_text(prefix+m.FUNCTION+suffix)
            build=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(source),'-o',str(exe)],capture_output=True,timeout=30)
            self.assertEqual((build.returncode,build.stderr),(0,b''))
            run=subprocess.run([str(exe)],capture_output=True,timeout=10)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(run.stdout,b'PASS 100 canonical status pairs; corrupt preimage retained; Flash unchanged\n')
    def test_source_preimage(self):
        with self.assertRaises(ValueError):m.correct_source(b'wrong')
    def test_parent_preimage(self):
        with self.assertRaises(ValueError):m.apply(b'wrong',b'aa')
    def test_exact_canonical_body(self):
        body=m.translation_unit().decode();self.assertIn(m.FUNCTION.split('static u8 ensure_save')[0],body)
        self.assertIn(m.FUNCTION.split('static u8 ensure_save')[1],body)
    def test_compiled_code_binding(self):
        self.assertEqual(m.CODE['size'],132);self.assertIn('136',m.linker_script())
    def test_bad_recipe_code(self):
        with self.assertRaises(ValueError):m.require_code(b'wrong')
    def test_three_bound_outputs(self):
        for case in m.root.prior.CASES:
            save,_,rows=sample(case);rows=m.root.root_expectations(case)+rows
            rows[-1]['candidate_sha256']=m.CANDIDATE['sha256']
            self.assertEqual(m.validate(encoded(rows),case,save,BASE)['candidate_sha256'],m.CANDIDATE['sha256'])
    def bad(self,change,case='v1-load-checksum'):
        save,_,rows=sample(case);rows=m.root.root_expectations(case)+rows;rows[-1]['candidate_sha256']=m.CANDIDATE['sha256'];change(rows)
        with self.assertRaises((ValueError,TypeError,KeyError)):m.validate(encoded(rows),case,save,BASE)
    def test_wrong_candidate(self):self.bad(lambda r:r[-1].update(candidate_sha256=m.PARENT['sha256']))
    def test_corrupt_normalized(self):self.bad(lambda r:r[2].update(version=2))
    def test_corrupt_ledger_lost(self):self.bad(lambda r:r[2].update(ledger_sha256='0'*64))
    def test_hidden_result(self):self.bad(lambda r:r[1].update(result=1))
    def test_corrupt_flash_write(self):self.bad(lambda r:r[3].update(save_calls=1))
    def test_corrupt_counter_changed(self):self.bad(lambda r:r[2].update(counter=3))
    def test_tail_hidden(self):self.bad(lambda r:r[2].update(last_result=0),'v1-load-tail')
    def test_phase0_duplication(self):self.bad(lambda r:r[3].update(phase0=2),'v1-load-valid')
    def test_no_whole_ledger(self):self.bad(lambda r:r[2].pop('ledger_sha256'))
    def test_wrong_root_order(self):self.bad(lambda r:r.reverse())
    def test_extra_row(self):self.bad(lambda r:r.append(r[-1]))
    def test_ui_overclaim(self):self.bad(lambda r:r[-1].update(transaction_ui_accepted=True))
    def test_flash_fault_overclaim(self):self.bad(lambda r:r[-1].update(physical_flash_fault_accepted=True))

if __name__=='__main__':unittest.main()
