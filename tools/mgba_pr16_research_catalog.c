/* 5ページの日本語表示を新規採取。購入/取消/Save受入は再実行しない。
 * 進行と残高は明示fixture、stock warp後は7 API barrier下のキー入力だけ。
 * 全pageを見た時点でmenuのまま終了し、取消caseへの読み替えを防ぐ。 */
static void ct_screen(unsigned page,char hash[65]){
 char name[48];snprintf(name,sizeof(name),"catalog-page-%u.ppm",page);
 bool varied=false;for(unsigned i=1;i<240*160;++i)if(si_video[i]!=si_video[0])varied=true;si_need(varied,"nonblank rendered screen");
 FILE*f=fopen(name,"wb");si_need(f!=NULL,"screen file");
 si_need(fprintf(f,"P6\n240 160\n255\n")>0,"screen header");
 for(unsigned i=0;i<240*160;++i){uint32_t pixel=si_video[i];unsigned char rgb[3]={(unsigned char)pixel,(unsigned char)(pixel>>8),(unsigned char)(pixel>>16)};si_need(fwrite(rgb,1,3,f)==3,"screen pixels");}
 si_need(fclose(f)==0,"screen close");sha256_file(name,hash);
}
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 si_need(argc==4&&!strcmp(argv[3],"catalog-all-pages-readonly"),"catalog case");char sha[65];
 sha256_file(argv[1],sha);si_need(!strcmp(sha,UC_ROM),"current candidate");
 sha256_file(argv[2],sha);si_need(!strcmp(sha,UC_FIXTURE),"declared progress fixture");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=ct_setup(argv[1],argv[2]);
 uint8_t before[2048],party[600],flash[131072],check[131072];unsigned items[2048];
 lc_read(c,before);for(unsigned i=0;i<600;++i)party[i]=read8(c,QOL_PLAYER_PARTY+i);si_inventory(c,items);uc_copy_flash(c,flash);unsigned counter=read32(c,SI_COUNTER);
 up_open_shop(c,"catalog");si_need(read8(c,SI_VOL+30)==23,"all23 actual eligible rows");
 for(unsigned page=0;page<5;++page){
  si_need(uc_active(c)&&read8(c,SI_VOL+31)==page,"real page index");
  si_need(si_read16(c,SI_VOL+18)==65535&&si_read16(c,SI_VOL+16)==9,"unselected busy");
  ct_screen(page,sha);printf("{\"page\":%u,\"catalog_indices\":[",page);
  unsigned count=page==4?3:5;
  for(unsigned i=0;i<count;++i){unsigned index=page*5+i;si_need(si_read16(c,SI_VOL+36+2*index)==index,"actual menu-to-catalog mapping");printf("%s%u",i?",":"",index);}
  printf("],\"frame\":%u,\"screen_sha256\":\"%s\"}\n",uc_frames,sha);fflush(stdout);
  uc_same_ledger(c,before);uc_same_inventory(c,items,party);uc_copy_flash(c,check);
  si_need(!memcmp(flash,check,131072)&&read32(c,SI_COUNTER)==counter,"no Flash/save transaction");
  if(page<4){for(unsigned i=0;i<5;++i)uc_tap(c,QOL_KEY_DOWN);uc_tap(c,QOL_KEY_A);}
 }
 si_need(!log_problem_count,"mGBA warnings/errors");qol_close(c);
 printf("{\"status\":\"PASS\",\"case\":\"catalog-all-pages-readonly\",\"candidate_sha256\":\"%s\",\"catalog_count\":23,\"pages\":5,\"fresh_cores\":%u,\"guarded_host_writes\":0,\"manual_saves\":0,\"transaction_saves\":0,\"natural_progress_accepted\":false,\"purchase_reruns\":0,\"cancel_reruns\":0,\"warnings_errors\":%u}\n",UC_ROM,si_cores,log_problem_count);return 0;
}
