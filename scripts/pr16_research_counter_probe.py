#!/usr/bin/env python3
"""受付数値表示だけのfixture/観測器。旧native mainは呼ばず、入力は物理keyのみ。"""
from pathlib import Path
import struct
import pr16_research_counter_numeric as patch
import pr16_research_connection as connection
import pr16_research_photo as photo

ROOT = Path(__file__).resolve().parents[1]
C = 'tools/mgba_pr16_research_counter_numeric.c'
FIXTURES = (
    {'size': 131072, 'sha256': '434076d0db74c4c5bf1b63e3aa4cc336d17e1f2dbb894160e840c721aa337a38'},
    {'size': 131072, 'sha256': '95646d927206354df5f2ad4b0bfca85bc26bd3d1a90811df9988e3ccb0357046'},
)
VALUES = ((0, 0, 1), (9999, 2200, 7))
PROGRAM = ((64,40,'step'),(0,200,'door_entered'),(64,128,'step'),
    (0,60,'counter_approach'),(1,2,'step'),(0,120,'counter_intro'),
    (1,2,'step'),(0,120,'counter_balance'),(1,2,'step'),
    (0,120,'counter_activity_one'),(1,2,'step'),(0,120,'counter_activity_two'),
    (1,2,'step'),(0,120,'counter_revisit'),(1,2,'step'),
    (0,120,'counter_closed'),(0,0,'end'))


def fixture(seed, index):
    patch.need(type(index) is int and index in (0, 1), 'closed fixture index')
    save, receipt = photo.fixture(seed)
    patch.need(patch.identity(save) == FIXTURES[0], 'accepted original-derived zero fixture')
    offset = photo.purchase.prior.prior.OFFSET
    if index:
        ledger = bytearray(save[offset:offset+2048])
        struct.pack_into('<H', ledger, 0x73f+4, VALUES[index][0])
        ledger[0x73f+6] = VALUES[index][2]
        struct.pack_into('<I', ledger, 0x73f+10, VALUES[index][1])
        ledger = photo.purchase.prior.prior.old.seal(ledger)
        save = save[:offset] + ledger + save[offset+2048:]
    patch.need(patch.identity(save) == FIXTURES[index], 'exact preboot fixture')
    patch.need(save[:offset] == seed[:offset] and save[offset+2048:] == seed[offset+2048:],
               'outside ledger immutable')
    return save, dict(receipt, fixture=patch.identity(save),
        ledger=patch.identity(save[offset:offset+2048]), initial_rp=VALUES[index][0],
        initial_lifetime=VALUES[index][1], initial_rank=VALUES[index][2],
        balance_credit_injected=bool(index), natural_earning_claimed=False,
        purpose='PREBOOT_DISPLAY_BOUNDARY_NOT_NATURALLY_EARNED_CREDIT')


def commands():
    return ''.join(f'{k} {n} {label}\n' for k,n,label in PROGRAM).encode('ascii')


def generate(seed):
    source = connection.generate(seed).decode('utf-8')
    def replace(old, new):
        nonlocal source
        patch.need(source.count(old) == 1, 'unique generation boundary: '+old[:60])
        source = source.replace(old, new)
    replace('int main(int argc,char**argv){', 'int accepted_connection_main(int argc,char**argv){')
    replace('#define UC_ROM "'+patch.PARENT['sha256']+'"',
            '#define UC_ROM "'+patch.CANDIDATE['sha256']+'"')
    replace('#define UC_FIXTURE "'+FIXTURES[0]['sha256']+'"',
            'static const char*nb_fixture;\nstatic unsigned nb_balance,nb_lifetime,nb_rank;\n#define UC_FIXTURE nb_fixture')
    replace('si_need(si_read16(c,SI_OWNER+4)==0&&si_read32(c,SI_OWNER+10)==0,"no initial earned/spendable RP");',
            'si_need(si_read16(c,SI_OWNER+4)==nb_balance&&si_read32(c,SI_OWNER+10)==nb_lifetime&&read8(c,SI_OWNER+6)==nb_rank,"declared preboot numeric fixture, not natural credit");')
    helper = r'''
static void nb_observe(struct mCore*c,const char*label){
 printf("{\"numeric\":\"%s\",\"rp\":%u,\"lifetime\":%u,\"rank\":%u,\"buffers\":[",label,si_read16(c,SI_OWNER+4),si_read32(c,SI_OWNER+10),read8(c,SI_OWNER+6));
 for(unsigned slot=0;slot<2;++slot){printf("%s\"",slot?",":"");
  for(unsigned i=0;i<20;++i){unsigned v=read8(c,0x02021C4CU+slot*20+i);printf("%02x",v);if(v==255)break;}printf("\"");}
 printf("]}\n");fflush(stdout);
}
'''
    replace('static unsigned cn_commands,cn_screens;', helper+'\nstatic unsigned cn_commands,cn_screens;')
    replace('fflush(stdout);cn_objects(c);', 'fflush(stdout);cn_objects(c);nb_observe(c,label);')
    replace('PHYSICAL_DOOR_AND_NATIVE_WORDING', 'COUNTER_NUMERIC_TEXT_NOT_STANDARD_LIST')
    return (source+'\n'+(ROOT/C).read_text(encoding='utf-8')).encode('utf-8')
