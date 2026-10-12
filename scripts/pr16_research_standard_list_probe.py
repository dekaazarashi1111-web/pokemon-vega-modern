#!/usr/bin/env python3
"""標準リストの変更影響だけを物理入力で観測。RP注入/旧matrix反復なし。"""
from pathlib import Path
import pr16_research_connection as connection
import pr16_research_counter_probe as fixture_source
import pr16_research_standard_list as s
ROOT=Path(__file__).resolve().parents[1]
PROGRAM=(
    (64,40,'step'),(0,200,'door_entered'),(64,128,'step'),(0,60,'counter_approach'),
    (1,2,'step'),(0,120,'counter_intro'),(1,2,'step'),(0,90,'menu_first'),
    (1,2,'step'),(0,120,'balance_selected'),(1,2,'step'),(0,90,'menu_after_balance'),
    (128,2,'step'),(0,30,'guide_cursor'),(1,2,'step'),(0,120,'guide_one'),
    (1,2,'step'),(0,120,'guide_two'),(1,2,'step'),(0,90,'menu_after_guide'),
    (2,2,'step'),(0,120,'b_cancel_message'),(1,2,'step'),(0,90,'b_cancel_closed'),
    (1,2,'step'),(0,120,'revisit_intro'),(1,2,'step'),(0,90,'menu_revisit'),
    (128,2,'step'),(0,30,'step'),(128,2,'step'),(0,30,'exit_cursor'),
    (1,2,'step'),(0,120,'exit_message'),(1,2,'step'),(0,90,'exit_closed'),
    (1,2,'step'),(0,120,'third_intro'),(1,2,'step'),(0,90,'menu_third'),
    (2,2,'step'),(0,120,'third_cancel_message'),(1,2,'step'),(0,90,'third_closed'),
    (0,0,'end'))

def commands():return ''.join(f'{k} {n} {label}\n' for k,n,label in PROGRAM).encode('ascii')
def fixture(seed):return fixture_source.fixture(seed,0)

def generate(seed,recipe):
    source=connection.generate(seed).decode('utf-8')
    def replace(old,new):
        nonlocal source
        s.need(source.count(old)==1,'unique inherited generation boundary '+old[:50])
        source=source.replace(old,new)
    replace('#define UC_ROM "'+connection.CANDIDATE['sha256']+'"','#define UC_ROM "'+recipe['candidate']['sha256']+'"')
    helper=r'''
static unsigned sl_last_window=255;
static void sl_observe(struct mCore*c,const char*label){
 unsigned count=0;
 for(unsigned i=0;i<16;++i){unsigned a=0x030050D0U+40*i;if(read8(c,a+4)&&read32(c,a)==SL_TASK_ENTRY)++count;}
 printf("{\"menu\":\"%s\",\"result\":%u,\"task_count\":%u,\"tasks\":[",label,read16(c,0x02037004U),count);
 unsigned found=0;
 for(unsigned i=0;i<16;++i){unsigned a=0x030050D0U+40*i;if(!read8(c,a+4)||read32(c,a)!=SL_TASK_ENTRY)continue;
  sl_last_window=read16(c,a+8);
  printf("%s{\"id\":%u,\"window\":%u,\"debounce\":%u}",found++?",":"",i,sl_last_window,read16(c,a+10));}
 printf("],\"last_window\":%u,\"window_descriptor\":\"",sl_last_window);
 if(sl_last_window<32)for(unsigned i=0;i<12;++i)printf("%02x",read8(c,0x02020430U+sl_last_window*12+i));
 printf("\",\"stock_menu\":\"");for(unsigned i=0;i<16;++i)printf("%02x",read8(c,0x0203AD5CU+i));
 printf("\",\"rp\":%u,\"rank\":%u,\"buffers\":[",read16(c,SI_OWNER+4),read8(c,SI_OWNER+6));
 for(unsigned slot=0;slot<2;++slot){printf("%s\"",slot?",":"");for(unsigned i=0;i<20;++i){unsigned v=read8(c,0x02021C4CU+slot*20+i);printf("%02x",v);if(v==255)break;}printf("\"");}
 printf("]}\n");fflush(stdout);
}
'''.replace('SL_TASK_ENTRY',str(recipe['build']['task'])+'U')
    replace('static unsigned cn_commands,cn_screens;',helper+'\nstatic unsigned cn_commands,cn_screens;')
    replace('fflush(stdout);cn_objects(c);','fflush(stdout);cn_objects(c);sl_observe(c,label);')
    replace('PHYSICAL_DOOR_AND_NATIVE_WORDING','COUNTER_STANDARD_LIST_ONLY')
    return source.encode('utf-8')
