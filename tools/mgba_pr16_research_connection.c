/* New physical-door/message probes. Setup fixtures stop before the write barrier.
 * After it, the command language permits only bounded physical keys/read/screens.
 * Prior accepted native mains are never called. No RP/PC/RNG/result injection. */
static unsigned cn_commands,cn_screens;
static uint8_t cn_ledger[2048],cn_party[600],cn_flash[131072];
static unsigned cn_items[2048],cn_counter;
static void cn_state(struct mCore*c,const char*label){
 unsigned s=read32(c,QOL_SAVE_BLOCK1_SLOT),id=read8(c,0x02036FB1U);char flash[65];uint8_t b[131072];uc_copy_flash(c,b);si_digest(b,sizeof(b),flash);
 printf("{\"state\":\"%s\",\"command\":%u,\"frame\":%u,\"map\":[%u,%u,%u,%u],\"facing\":%u,\"field\":%s,\"callback\":%u,\"result\":%u,\"shop_active\":%s,\"eligible\":%u,\"window\":%u,\"flash_sha256\":\"%s\",\"text\":\"",label,cn_commands,uc_frames,read8(c,s+4),read8(c,s+5),read16(c,s),read16(c,s+2),read8(c,0x02036D6CU+36*id+0x18)&15,si_field(c)?"true":"false",read32(c,BATTLE_CORE_MAIN_CALLBACK2),si_read16(c,SI_VOL+16),uc_active(c)?"true":"false",read8(c,SI_VOL+30),read8(c,SI_VOL+32),flash);
 for(unsigned i=0;i<128;++i){unsigned x=read8(c,0x02021C88U+i);printf("%02x",x);if(x==255)break;}printf("\"}\n");lc_event(c,label);fflush(stdout);
}
static void cn_screen(const char*label){
 char hash[65],name[80];si_need(cn_screens<40,"bounded screenshots");ct_screen(40,hash);snprintf(name,sizeof(name),"%s.ppm",label);si_need(rename("catalog-page-40.ppm",name)==0,"screen rename");++cn_screens;
 printf("{\"screen\":\"%s\",\"command\":%u,\"frame\":%u,\"sha256\":\"%s\"}\n",label,cn_commands,uc_frames,hash);fflush(stdout);
}
static struct mCore*cn_setup(const char*rom,const char*save,unsigned which){
 static const unsigned entry[4][4]={{96,0,16,14},{96,23,12,87},{96,6,34,22},{97,63,29,26}};
 const unsigned*v=entry[which];struct mCore*c=ct_open(rom,save);run_key_frames(c,0,2);
 (void)qol_call5_preserving(c,QOL_SET_WARP_DESTINATION,v[0],v[1],255,v[2],v[3]);
 (void)call_preserving(c,QOL_RESET_INITIAL_AVATAR,0,0,0,0);
 (void)call_preserving(c,QOL_WARP_INTO_MAP,0,0,0,0);
 qol_write32(c,QOL_FIELD_CALLBACK_SLOT,QOL_DEFAULT_WARP_EXIT);
 (void)call_preserving(c,QOL_SET_MAIN_CALLBACK2,QOL_CB2_LOAD_MAP,0,0,0);
 si_guard(c);for(unsigned i=0;i<900;++i)uc_frame(c,0);
 unsigned s=read32(c,QOL_SAVE_BLOCK1_SLOT);si_need(si_field(c)&&read8(c,s+4)==v[0]&&read8(c,s+5)==v[1]&&read16(c,s)==v[2]&&read16(c,s+2)==v[3],"declared outdoor fixture");
 si_need(si_read16(c,SI_OWNER+4)==0&&si_read32(c,SI_OWNER+10)==0,"no initial earned/spendable RP");
 si_need(read8(c,SI_VOL+28)==0&&read8(c,SI_VOL+34)==0&&si_read16(c,SI_VOL+20)==65535,"production services only");
 lc_read(c,cn_ledger);for(unsigned i=0;i<600;++i)cn_party[i]=read8(c,QOL_PLAYER_PARTY+i);si_inventory(c,cn_items);uc_copy_flash(c,cn_flash);cn_counter=read32(c,SI_COUNTER);
 cn_state(c,"fixture");return c;
}
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 si_need(argc==4,"connection args");unsigned which=qol_number(argv[3],"case");si_need(which<4,"closed case");char sha[65];sha256_file(argv[1],sha);si_need(!strcmp(sha,UC_ROM),"exact candidate");sha256_file(argv[2],sha);si_need(!strcmp(sha,UC_FIXTURE),"exact zero RP fixture");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=cn_setup(argv[1],argv[2],which);
 unsigned key,frames;char label[48],extra;
 while(scanf("%u %u %47s",&key,&frames,label)==3){
  si_need(++cn_commands<=400&&key<=255&&frames<=1200&&uc_frames+frames<=50000,"bounded key command");
  for(unsigned i=0;label[i];++i)si_need((label[i]>='a'&&label[i]<='z')||(label[i]>='0'&&label[i]<='9')||label[i]=='_',"safe label");
  printf("{\"input\":%u,\"keys\":%u,\"frames\":%u,\"label\":\"%s\"}\n",cn_commands,key,frames,label);fflush(stdout);
  for(unsigned i=0;i<frames;++i)uc_frame(c,key);
  if(strcmp(label,"step")){cn_state(c,label);cn_screen(label);}
  if(!strcmp(label,"end"))break;
 }
 (void)extra;
 uc_same_inventory(c,cn_items,cn_party);uc_same_ledger(c,cn_ledger);
 uint8_t check[131072];uc_copy_flash(c,check);si_need(!memcmp(check,cn_flash,sizeof(check))&&read32(c,SI_COUNTER)==cn_counter,"no guide/menu save or flash change");
 si_need(!log_problem_count,"no mGBA errors");cn_state(c,"final");qol_close(c);
 printf("{\"status\":\"MEASURED\",\"scope\":\"PHYSICAL_DOOR_AND_NATIVE_WORDING\",\"case\":%u,\"fresh_cores\":%u,\"commands\":%u,\"screens\":%u,\"guarded_host_writes\":0,\"manual_saves\":0,\"transaction_saves\":0,\"accepted_case_reruns\":0,\"natural_story_progress_accepted\":false,\"naturally_earned_spending_accepted\":false,\"warnings_errors\":%u}\n",which,si_cores,cn_commands,cn_screens,log_problem_count);return 0;
}
