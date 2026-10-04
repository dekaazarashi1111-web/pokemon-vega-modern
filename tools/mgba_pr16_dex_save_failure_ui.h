/* 明示CRC1byteのnegative fixture専用。通常受入runnerから到達させない。 */
static void (*sf_fixture_write8)(struct mCore*,uint32_t,uint8_t);
static uint8_t sf_ram[262144],sf_iwram[32768],sf_mdx[522],sf_flash_before[131072],sf_party[600];
static unsigned sf_inventory[2048],sf_injected,sf_seen5,sf_seen6,sf_screens;
static void sf_read_mdx(struct mCore*c,uint8_t*out){for(unsigned i=0;i<522;i++)out[i]=read8(c,VEGA_DEX_OWNER_RAM+i);}
static void sf_invariants(struct mCore*c,bool flash)
{
 uint8_t mdx[522];sf_read_mdx(c,mdx);si_need(!memcmp(mdx,sf_mdx,522),"negative MDX stays exactly corrupted; no guessed repair");
 si_need(read32(c,SI_COUNTER)==101,"failed Save counter retained");
 si_need(read32(c,0x03000FA4)!=0x0806F1A9,"never ordinary save-success callback");
 if(flash){uint8_t raw[131072];ng_flash(c,raw);si_need(!memcmp(raw,sf_flash_before,sizeof(raw)),"whole Flash remains exact at failure checkpoints");}
}
static void sf_tick(struct mCore*c,unsigned key)
{
 st_keys(c,key,1);sf_invariants(c,false);unsigned state=read8(c,0x0203AAC8),active=read32(c,0x03005480);
 if(active&&state==5&&!sf_seen5){sf_seen5=1;printf("{\"save_failed_state\":5,\"frame\":%u,\"attempt\":%u}\n",st_frames,read16(c,0x03005470));fflush(stdout);}
 if(active&&state==6&&!sf_seen6){sf_seen6=1;printf("{\"save_failed_state\":6,\"frame\":%u,\"attempt\":%u}\n",st_frames,read16(c,0x03005470));fflush(stdout);}
}
static void sf_press(struct mCore*c,unsigned key,unsigned wait){sf_tick(c,key);sf_tick(c,key);for(unsigned i=0;i<wait;i++)sf_tick(c,0);}
static void sf_view(struct mCore*c,const char*stage)
{
 sf_invariants(c,true);printf("{\"failure_ui_stage\":\"%s\",\"frame\":%u,\"active\":%u,\"state\":%u,\"attempt\":%u,\"callback\":%u,\"delay\":%u,\"counter\":%u,\"damaged_mask\":%u}\n",stage,st_frames,read32(c,0x03005480),read8(c,0x0203AAC8),read16(c,0x03005470),read32(c,0x03000FA4),read8(c,0x03000FA8),read32(c,SI_COUNTER),read32(c,0x030053DC));st_screen(sf_screens++);fflush(stdout);
}
int main(int argc,char**argv)
{
 si_need(argc==3,"closed negative UI invocation");char sha[65];sha256_file(argv[1],sha);si_need(!strcmp(sha,NG_ROM),"fixed failure candidate");sha256_file(argv[2],sha);si_need(!strcmp(sha,"814a8e31ce20d720a1f1bddc08caa9cdd3d86b5bbb874738b9cb859653552149"),"exact private Save101 copy");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=st_open(argv[1],argv[2]);qol_log_core=c;sf_fixture_write8=c->busWrite8;si_flash(c);si_guard(c);
 printf("{\"begin\":\"EXPLICIT_CRC_NEGATIVE_SAVE_FAILURE_UI\",\"candidate_sha256\":\"%s\",\"host_write_barriers\":7,\"formal_save_changed\":false}\n",NG_ROM);fflush(stdout);
 st_keys(c,0,600);bool ready=false;
 for(unsigned i=0;i<100;i++){st_press(c,i==0?8:(i>12?2:1),120);if(si_field(c)){st_keys(c,0,180);if(si_field(c)){ready=true;break;}}}
 si_need(ready&&read32(c,SI_COUNTER)==101&&read8(c,QOL_PLAYER_PARTY_COUNT)==4,"stable original Continue counter/party");
 unsigned sb1=read32(c,QOL_SAVE_BLOCK1_SLOT);si_need(read8(c,sb1+4)==3&&read8(c,sb1+5)==24&&read16(c,sb1)==53&&read16(c,sb1+2)==13,"exact Route506 location");
 si_need(read8(c,0x02031CE4)==0,"same-save normal type0 path");sf_read_mdx(c,sf_mdx);si_need(VegaDexValidate(sf_mdx,522)==0,"valid migrated MDX before fixture");
 ng_flash(c,sf_flash_before);for(unsigned i=0;i<600;i++)sf_party[i]=read8(c,QOL_PLAYER_PARTY+i);si_inventory(c,sf_inventory);
 for(unsigned i=0;i<262144;i++)sf_ram[i]=read8(c,0x02000000+i);for(unsigned i=0;i<32768;i++)sf_iwram[i]=read8(c,0x03000000+i);
 si_need(!sf_injected&&sf_fixture_write8!=c->busWrite8&&si_field(c),"one explicit exception with barriers still active");unsigned old=sf_mdx[4];sf_fixture_write8(c,VEGA_DEX_OWNER_RAM+4,(uint8_t)(old^1));sf_injected=1;
 for(unsigned i=0;i<262144;i++)si_need(read8(c,0x02000000+i)==(i==VEGA_DEX_OWNER_RAM+4-0x02000000?(sf_ram[i]^1):sf_ram[i]),"only declared CRC byte changes without a frame");
 for(unsigned i=0;i<32768;i++)si_need(read8(c,0x03000000+i)==sf_iwram[i],"all IWRAM remains exact at injection");
 sf_read_mdx(c,sf_mdx);si_need(VegaDexValidate(sf_mdx,522)!=0,"fixture actually invalidates CRC");printf("{\"fixture_calls\":1,\"fixture_bytes\":1,\"address\":%u,\"old\":%u,\"new\":%u,\"register_writes\":0,\"other_host_writes\":0}\n",VEGA_DEX_OWNER_RAM+4,old,old^1);fflush(stdout);sf_view(c,"injected_at_field");
 sf_press(c,8,120);si_need(read32(c,QOL_START_MENU_CALLBACK)==QOL_START_MENU_INPUT,"ordinary START menu");unsigned count=read8(c,QOL_START_MENU_COUNT),cur=read8(c,QOL_START_MENU_CURSOR),target=99;
 si_need(count>0&&count<=10&&cur<count,"bounded menu");for(unsigned i=0;i<count;i++)if(read8(c,QOL_START_MENU_ORDER+i)==4)target=i;si_need(target<count,"SAVE action present");
 while(cur!=target){sf_press(c,128,30);cur=(cur+1)%count;}sf_press(c,1,120);
 bool failed=false;
 for(unsigned i=0;i<6000;i++){
  unsigned active=read32(c,0x03005480),state=read8(c,0x0203AAC8);
  if(active&&state==6){failed=true;break;}
  sf_tick(c,!active&&(i%120)<2?1:0);
 }
 si_need(failed&&sf_seen5&&sf_seen6&&read16(c,0x03005470)==255,"real SaveFailed reaches failed state6");for(unsigned i=0;i<2;i++)sf_tick(c,0);sf_view(c,"save_failed_state6");
 sf_press(c,1,2);bool error=false;
 for(unsigned i=0;i<1200;i++){if(!read32(c,0x03005480)&&read8(c,0x0203AAC8)==0&&read32(c,0x03000FA4)==0x0806F21D&&read8(c,0x03000FA8)==0){error=true;break;}sf_tick(c,0);}
 si_need(error&&read16(c,0x03005470)==255,"ordinary error message after first A");sf_view(c,"ordinary_save_error");sf_press(c,1,2);
 bool field=false;for(unsigned i=0;i<1200;i++){if(si_field(c)){field=true;break;}sf_tick(c,0);}si_need(field,"second ordinary A returns field");for(unsigned i=0;i<180;i++)sf_tick(c,0);
 si_need(si_field(c)&&!read32(c,0x03005480)&&read8(c,0x0203AAC8)==0,"stable field after failure");sf_view(c,"field_after_failure");
 si_need(read8(c,sb1+4)==3&&read8(c,sb1+5)==24&&read16(c,sb1)==53&&read16(c,sb1+2)==13,"location retained");for(unsigned i=0;i<600;i++)si_need(sf_party[i]==read8(c,QOL_PLAYER_PARTY+i),"entire party retained");unsigned inventory[2048];si_inventory(c,inventory);si_need(!memcmp(inventory,sf_inventory,sizeof(inventory)),"normalized Bag retained");
 si_need(!log_problem_count&&sf_injected==1,"clean negative process");printf("{\"end\":\"PASS_EXPLICIT_CRC_FIXTURE_SAVE_FAILURE_UI\",\"frames\":%u,\"inputs\":%u,\"screens\":%u,\"fixture_calls\":1,\"fixture_bytes\":1,\"host_write_barriers\":7,\"other_host_writes\":0,\"register_writes\":0,\"save_attempts\":1,\"save_commits\":0,\"counter\":101,\"all_flash_unchanged\":true,\"authority_present\":true,\"story_progress_accepted\":false}\n",st_frames,st_inputs,sf_screens);fflush(stdout);qol_close(c);return 0;
}
