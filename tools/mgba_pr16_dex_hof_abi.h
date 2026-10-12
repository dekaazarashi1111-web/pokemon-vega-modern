/* 固定ROMのHOF pack/appendだけを実ARMで観測する隔離試験。
 * 親schedulerのmainをrenameして末尾へ連結する。実save/通常画面は実行しない。
 * species上位bitの欠落は現ABIの観測であり、全種族対応の受入ではない。 */
#include <mgba/internal/gba/gba.h>
#define HA_PAYLOAD 0x0201C000u
#define HA_PAYLOAD_BYTES 7936u
#define HA_RAM_BYTES 8192u
#define HA_TEAM 0x02028000u
#define HA_TEAM_PTR 0x0203AAB0u
#define HA_PALETTE 0x0203AAACu
#define HA_HAS_RECORDS 0x0203AABCu
#define HA_TASKS 0x030050D0u
#define HA_PARTY 0x020241E4u
#define HA_INIT_MON 0x080F2ED4u
#define HA_INIT_TEAM 0x080F3074u
static uint8_t ha_seed_ram[262144],ha_seed_iwram[32768];
static uint8_t ha_before_ram[262144],ha_before_iwram[32768];
static uint8_t ha_disk[HA_PAYLOAD_BYTES],ha_expected[HA_RAM_BYTES],ha_team[120];
static uint8_t ha_expected_task[40],ha_expected_team[120];
static unsigned ha_task,ha_entry,ha_species,ha_load_result,ha_has_records;
static unsigned ha_gets,ha_quest,ha_loads,ha_sets,ha_copies,ha_draws,ha_prints,ha_windows;
static unsigned ha_pack_cases,ha_append_cases,ha_clear_cases;
static void ha_u16(uint8_t *p,unsigned v){p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8);}
static void ha_u32(uint8_t *p,uint32_t v){for(unsigned n=0;n<4;n++)p[n]=(uint8_t)(v>>(8*n));}
static unsigned ha_level(unsigned slot){return 1u+slot*19u;}
static uint32_t ha_tid(unsigned slot){return 0x11223344u+slot*0x01020304u;}
static uint32_t ha_personality(unsigned slot){return 0x89ABCDEFu^slot*0x1020304u;}
static uint8_t ha_nick(unsigned slot,unsigned n){return (uint8_t)(0x40u+slot*11u+n);}
static void ha_restore(void)
{
 struct GBA*g=c->board;memcpy(g->memory.wram,ha_seed_ram,sizeof(ha_seed_ram));memcpy(g->memory.iwram,ha_seed_iwram,sizeof(ha_seed_iwram));
 ha_gets=ha_quest=ha_loads=ha_sets=ha_copies=ha_draws=ha_prints=ha_windows=0;
 w32(HA_TEAM_PTR,HA_TEAM);w32(HA_PALETTE,0xA55A55AAu);
 for(unsigned n=0;n<40;n++)ha_expected_task[n]=(uint8_t)(0x41u+n*7u);
 ha_u16(ha_expected_task+8,0);put(HA_TASKS+40*ha_task,ha_expected_task,40);
}
static void ha_stub_getmon(unsigned mon,unsigned field,unsigned destination,unsigned sp)
{
 need(mon>=HA_PARTY&&mon<HA_PARTY+600&&(mon-HA_PARTY)%100==0,"HOF GetMonData party stride100");
 unsigned slot=(mon-HA_PARTY)/100;ha_gets++;
 switch(field){
 case 0xBu:case 0x41u:returned(ha_species);break;
 case 1u:returned(ha_tid(slot));break;
 case 0u:returned(ha_personality(slot));break;
 case 0x38u:returned(ha_level(slot));break;
 case 2u:
  need(destination>=sp-128&&destination+11<=sp,"nickname temporary is bounded stack owner");
  for(unsigned n=0;n<10;n++)c->busWrite8(c,destination+n,ha_nick(slot,n));
  c->busWrite8(c,destination+10,255);returned(10);break;
 default:need(0,"closed GetMonData field set");
 }
}
static void ha_call(unsigned sp)
{
 struct GBA*g=c->board;memcpy(ha_before_ram,g->memory.wram,sizeof(ha_before_ram));memcpy(ha_before_iwram,g->memory.iwram,sizeof(ha_before_iwram));
 calls++;set("cpsr",0xDF);set("sp",sp);set("lr",0x08000001u);
 for(unsigned i=0;i<12;i++){char name[8];snprintf(name,sizeof(name),"r%u",i);set(name,i?0x77000000u+i:ha_task);}
 set("cpsr",0xFF);set("pc",ha_entry|1u);
 for(unsigned n=0;;n++){
  need(n<30000,"bounded HOF ABI ARM call");unsigned pc=(reg("pc")&~1u)-2u,a=reg("r0"),b=reg("r1"),d=reg("r2");
  if(pc==0x08000000u)break;
  if(pc==0x0803F354u){need(ha_entry==HA_INIT_MON,"GetMonData only in pack primitive");ha_stub_getmon(a,b,d,sp);continue;}
  if(pc==0x08112F98u){need(ha_entry==HA_INIT_TEAM,"quest log only in append primitive");ha_quest++;returned(0);continue;}
  if(pc==0x080DB4E4u){need(ha_entry==HA_INIT_TEAM&&a==3&&ha_has_records,"one HOF-only load dependency");ha_loads++;if(ha_load_result==1)put(HA_PAYLOAD,ha_disk,HA_PAYLOAD_BYTES);returned(ha_load_result);continue;}
  if(pc==0x081C9DF8u){need(ha_entry==HA_INIT_TEAM&&a==HA_PAYLOAD&&b==0&&d==HA_RAM_BYTES,"only exact8192-byte initialization");ha_sets++;for(unsigned i=0;i<HA_RAM_BYTES;i++)c->busWrite8(c,a+i,0);returned(a);continue;}
  if(pc==0x081C9D98u){
   need(ha_entry==HA_INIT_TEAM&&d==120&&a>=HA_PAYLOAD&&a+120<=HA_PAYLOAD+6000,"exact120-byte team copy destination");
   need(b==HA_TEAM||(b==a+120&&b+120<=HA_PAYLOAD+6000),"append source or one-team left shift");
   uint8_t team[120];get(b,team,120);put(a,team,120);ha_copies++;returned(a);continue;
  }
  if(pc==0x080F7F44u){need(ha_entry==HA_INIT_TEAM&&a==0&&b==0,"original dialogue frame dependency");ha_draws++;returned(0);continue;}
  if(pc==0x080F7D28u){unsigned stack=reg("sp");need(ha_entry==HA_INIT_TEAM&&a==0&&b==2&&d==0x083E04B6u&&reg("r3")==0,"original saving text dependency");need(r32(stack)==0&&r32(stack+4)==2&&r32(stack+8)==1&&r32(stack+12)==3,"original printer stack arguments");ha_prints++;returned(0);continue;}
  if(pc==0x08003EECu){need(ha_entry==HA_INIT_TEAM&&a==0&&b==3,"original window-copy dependency");ha_windows++;returned(0);continue;}
  need((ha_entry==HA_INIT_MON&&pc>=HA_INIT_MON&&pc<HA_INIT_TEAM)||(ha_entry==HA_INIT_TEAM&&pc>=HA_INIT_TEAM&&pc<0x080F3180u),"no unstubbed dependency, save, UI, or other ROM path");
  c->step(c);steps++;
 }
 need(reg("sp")==sp,"HOF ABI exact SP return");
 for(unsigned i=4;i<12;i++){char name[8];snprintf(name,sizeof(name),"r%u",i);need(reg(name)==0x77000000u+i,"HOF ABI callee registers retained");}
 for(unsigned i=0;i<262144;i++){
  unsigned a=0x02000000u+i;
  if(ha_entry==HA_INIT_MON&&((a>=HA_TEAM&&a<HA_TEAM+120)||(a>=HA_PALETTE&&a<HA_PALETTE+4)))continue;
  if(ha_entry==HA_INIT_TEAM&&a>=HA_PAYLOAD&&a<HA_PAYLOAD+HA_RAM_BYTES)continue;
  need(((uint8_t*)g->memory.wram)[i]==ha_before_ram[i],"all non-owner EWRAM retained");
 }
 for(unsigned i=0;i<32768;i++){
  unsigned a=0x03000000u+i;
  if((a>=sp-256&&a<sp)||(a>=HA_TASKS+40*ha_task&&a<HA_TASKS+40*ha_task+40))continue;
  need(((uint8_t*)g->memory.iwram)[i]==ha_before_iwram[i],"all non-stack/non-task IWRAM retained");
 }
 uint8_t task[40];get(HA_TASKS+40*ha_task,task,40);need(!memcmp(task,ha_expected_task,40),"exact task callback/data writes");
 need(reads==0&&erases==0&&programs==0&&stock_calls==0,"no scheduler flash or save callback executed");
}
static void ha_pack(unsigned species,unsigned align)
{
 ha_task=align?15:0;ha_entry=HA_INIT_MON;ha_species=species;ha_restore();
 for(unsigned i=0;i<120;i++)ha_expected_team[i]=(uint8_t)(i*13u+71u);
 put(HA_TEAM,ha_expected_team,120);
 for(unsigned slot=0;slot<6;slot++){
  uint8_t*p=ha_expected_team+20*slot;
  ha_u32(p,species?ha_tid(slot):0);ha_u32(p+4,species?ha_personality(slot):0);
  ha_u16(p+8,species?((species&511u)|(ha_level(slot)<<9)):0);
  if(species)for(unsigned n=0;n<10;n++)p[10+n]=ha_nick(slot,n);else p[10]=255;
 }
 ha_u32(ha_expected_task,HA_INIT_TEAM|1u);ha_u16(ha_expected_task+10,0);ha_u16(ha_expected_task+12,species?6:0);
 for(unsigned i=4;i<=10;i++)ha_u16(ha_expected_task+8+2*i,255);
 ha_call(STACK+4*align);uint8_t team[120];get(HA_TEAM,team,120);
 need(!memcmp(team,ha_expected_team,120)&&r32(HA_PALETTE)==0,"observed20-byte mon and low9 species packing");
 need(ha_gets==(species?36u:6u)&&!ha_quest&&!ha_loads&&!ha_sets&&!ha_copies&&!ha_draws&&!ha_prints&&!ha_windows,"pack exact dependency counts");
 ha_pack_cases++;checks++;
}
static void ha_append(unsigned count,unsigned align,unsigned pattern,unsigned clear_kind)
{
 ha_task=align?15:0;ha_entry=HA_INIT_TEAM;ha_has_records=clear_kind!=1;ha_load_result=clear_kind>=2?(clear_kind==2?0:clear_kind==3?2:255):1;ha_restore();
 c->busWrite8(c,HA_HAS_RECORDS,(uint8_t)ha_has_records);
 for(unsigned i=0;i<HA_RAM_BYTES;i++)ha_expected[i]=(uint8_t)(i*37u+pattern*83u+19u);
 put(HA_PAYLOAD,ha_expected,HA_RAM_BYTES);
 for(unsigned i=0;i<HA_PAYLOAD_BYTES;i++)ha_disk[i]=(uint8_t)(i*29u+pattern*113u+7u);
 for(unsigned slot=0;slot<50;slot++)ha_u16(ha_disk+slot*120+8,slot==count?0xFE00u:((slot+1u)|0xB200u));
 for(unsigned i=0;i<120;i++)ha_team[i]=(uint8_t)(i*11u+pattern*31u+3u);
 ha_u16(ha_team+8,257u|(77u<<9));put(HA_TEAM,ha_team,120);
 if(clear_kind){memset(ha_expected,0,sizeof(ha_expected));memcpy(ha_expected,ha_team,120);}
 else{memcpy(ha_expected,ha_disk,HA_PAYLOAD_BYTES);if(count==50)memmove(ha_expected,ha_expected+120,49*120);memcpy(ha_expected+(count==50?49:count)*120,ha_team,120);}
 ha_u32(ha_expected_task,0x080F3181u);ha_call(STACK+4*align);
 uint8_t got[HA_RAM_BYTES];get(HA_PAYLOAD,got,sizeof(got));need(!memcmp(got,ha_expected,sizeof(got)),"all8192 HOF RAM bytes match independent append oracle");
 if(!clear_kind){need(!memcmp(got+6000,ha_disk+6000,1936),"opaque saved suffix1936 retained byte-exact");need(!memcmp(got+HA_PAYLOAD_BYTES,ha_before_ram+(HA_PAYLOAD-0x02000000u)+HA_PAYLOAD_BYTES,256),"unsaved liveRAM suffix256 retained");}
 need(ha_quest==1&&ha_loads==ha_has_records&&ha_sets==(clear_kind!=0)&&ha_copies==(!clear_kind&&count==50?50u:1u)&&ha_draws==1&&ha_prints==1&&ha_windows==1&&!ha_gets,"append/clear exact dependency counts");
 if(clear_kind)ha_clear_cases++;else ha_append_cases++;checks++;
}
int main(int argc,char**argv)
{
 need(argc==2,"one private hash-validated candidate");c=mCoreFind(argv[1]);need(c&&c->init(c),"HOF ABI core init");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");need(mCoreLoadFile(c,argv[1]),"HOF ABI candidate load");c->setVideoBuffer(c,video,240);c->reset(c);reset();
 struct GBA*g=c->board;memcpy(ha_seed_ram,g->memory.wram,sizeof(ha_seed_ram));memcpy(ha_seed_iwram,g->memory.iwram,sizeof(ha_seed_iwram));
 const unsigned species[]={0,1,511,512,513,1205,1520,65535};
 for(unsigned s=0;s<sizeof(species)/sizeof(species[0]);s++)for(unsigned align=0;align<2;align++)ha_pack(species[s],align);
 for(unsigned count=0;count<=50;count++)for(unsigned align=0;align<2;align++)for(unsigned pattern=0;pattern<2;pattern++)ha_append(count,align,pattern,0);
 for(unsigned kind=1;kind<=4;kind++)for(unsigned align=0;align<2;align++)ha_append(50,align,kind,kind);
 need(checks==228&&ha_pack_cases==16&&ha_append_cases==204&&ha_clear_cases==8&&calls==228,"closed228 new ABI cases");
 printf("{\"status\":\"PASS_ISOLATED_ARM_HOF_EXISTING_ABI\",\"cases\":%u,\"pack_cases\":%u,\"append_cases\":%u,\"clear_cases\":%u,\"calls\":%u,\"steps\":%llu,\"mon_bytes\":20,\"team_bytes\":120,\"max_teams\":50,\"species_bits\":9,\"opaque_suffix_bytes\":1936,\"native_processes\":1,\"game_boots\":0,\"real_saves\":0,\"native_gameplay_accepted\":false,\"all_species_accepted\":false,\"generation_binding_accepted\":false}\n",checks,ha_pack_cases,ha_append_cases,ha_clear_cases,calls,(unsigned long long)steps);fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
