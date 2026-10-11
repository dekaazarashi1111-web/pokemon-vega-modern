/* Native predicate ABI probes are synthetic stopped-memory fixtures.
 * The photo regression uses only physical keys after the existing stopped warp.
 * No new host write API is introduced; the seven-API guard is inherited. */
static void mv_visual(struct mCore*c,const char*stage){
 unsigned s=read32(c,QOL_SAVE_BLOCK1_SLOT),h=0x02036D30U,l=read32(c,h);
 si_need(l==0x092A4498U&&read32(c,h+4)==0x09413750U,"bound live header");
 unsigned s2=read32(c,QOL_SAVE_BLOCK2_SLOT);bool empty=true;
 for(unsigned i=0;i<512;++i)if(read8(c,s2+0x898U+i))empty=false;
 char hash[65],name[80];ct_screen(30,hash);snprintf(name,sizeof(name),"visual-%s.ppm",stage);si_need(rename("catalog-page-30.ppm",name)==0,"unique visual image");
 printf("{\"visual\":\"%s\",\"map\":[%u,%u],\"position\":[%u,%u],\"layout_id\":%u,\"layout\":%u,\"primary\":%u,\"secondary\":%u,\"view_empty\":%s,\"screen\":\"%s\"}\n",stage,read8(c,s+4),read8(c,s+5),read16(c,s),read16(c,s+2),read16(c,s+0x32),l,read32(c,l+16),read32(c,l+20),empty?"true":"false",hash);fflush(stdout);
}
static void mv_predicate(const char*rom,const char*save){
 struct mCore*c=ct_open(rom,save);uint8_t flash[131072],check[131072];uc_copy_flash(c,flash);
 /* Isolated synthetic SaveBlock2 owner; this core is discarded, never saved. */
 const unsigned base=0x02028000U,at=base+0x898U;write32_bytes(c,QOL_SAVE_BLOCK2_SLOT,base);
 for(unsigned i=0;i<1024;++i)write8(c,at+i,0);
 unsigned value=si_call(c,0x08058A15U,0,0,0,false);si_need(value==1,"zero view is empty");
 for(unsigned index=0;index<512;++index){
  si_write16(c,at+2*index,0x8001U);
  value=si_call(c,0x08058A15U,0,0,0,false);si_need(value==(unsigned)(index>=256),"inside detected; adjacent owner ignored");
  for(unsigned i=0;i<1024;++i){unsigned want=i==2*index?1:i==2*index+1?128:0;si_need(read8(c,at+i)==want,"predicate is readonly for all source/neighbor bytes");}
  si_write16(c,at+2*index,0);
 }
 for(unsigned i=0;i<1024;++i)write8(c,at+i,0xA5);
 (void)si_call(c,0x08058A55U,0,0,0,false);
 for(unsigned i=0;i<1024;++i)si_need(read8(c,at+i)==(i<512?0:0xA5),"stock CpuSet clears exactly 512 bytes, no adjacent owner");
 si_guard(c);uc_copy_flash(c,check);si_need(!memcmp(flash,check,131072)&&!si_saves,"pure ABI probes never save");qol_close(c);
 printf("{\"boundary\":\"saved-map-view\",\"view_bytes\":512,\"neighbor_bytes\":512,\"inside_one_hot_cases\":256,\"outside_one_hot_cases\":256,\"zero_case\":1,\"source_unchanged\":true,\"clear_bytes\":512,\"clear_neighbor_unchanged\":true,\"flash_unchanged\":true}\n");
}
static void mv_photo(const char*rom,const char*save){
 struct mCore*c=ph_setup(rom,save);uint8_t ledger[2048],party[600],flash[131072],check[131072];unsigned items[2048];
 lc_read(c,ledger);for(unsigned i=0;i<600;++i)party[i]=read8(c,QOL_PLAYER_PARTY+i);si_inventory(c,items);unsigned counter=read32(c,SI_COUNTER);
 si_need(counter==2&&si_read16(c,SI_OWNER+4)==0,"zero RP fixture");lc_event(c,"fixture");
 /* Earning is the sole impact regression prerequisite for the actual old fault.
  * Accepted decline and duplicate visits are deliberately not repeated. */
 ph_visit(c,"earn",true,0);ph_invariants(c,ledger,items,party,true,counter+2);lc_event(c,"earned");mv_visual(c,"earned");uc_copy_flash(c,flash);qol_close(c);
 c=ct_open(rom,save);si_guard(c);ph_stance(c);ph_invariants(c,ledger,items,party,true,counter+2);lc_event(c,"cold");mv_visual(c,"cold");
 uc_copy_flash(c,check);si_need(!memcmp(flash,check,131072),"cold Continue no extra Flash writes");
 /* Observe the normal dialogue over the restored terrain; do not confirm it. */
 uc_tap(c,QOL_KEY_A);for(unsigned i=0;i<90;++i)uc_frame(c,0);si_need(!si_field(c),"native cold prompt");mv_visual(c,"cold_prompt");
 ph_invariants(c,ledger,items,party,true,counter+2);uc_copy_flash(c,check);si_need(!memcmp(flash,check,131072),"cold prompt is readonly");qol_close(c);
 printf("{\"invariants\":\"after-cold-prompt\",\"full_flash_unchanged\":true,\"full_ledger_unchanged\":true,\"full_bag_party_unchanged\":true,\"counter\":4}\n");
}
int main(int argc,char**argv){
 si_need(argc==4,"map-view case");bool predicate=!strcmp(argv[3],"predicate-boundary");si_need(predicate||!strcmp(argv[3],"photo-cold-visual"),"closed map-view cases");
 char hash[65];sha256_file(argv[1],hash);si_need(!strcmp(hash,UC_ROM),"exact repaired candidate");sha256_file(argv[2],hash);si_need(!strcmp(hash,UC_FIXTURE),"unchanged private fixture");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);
 if(predicate)mv_predicate(argv[1],argv[2]);else mv_photo(argv[1],argv[2]);
 si_need(!log_problem_count,"map view warning/error free");
 printf("{\"status\":\"PASS\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",\"fresh_cores\":%u,\"predicate_calls\":%u,\"clear_calls\":%u,\"transaction_saves\":%u,\"manual_saves\":0,\"guarded_host_writes\":0,\"photo_earning_regressions\":%u,\"natural_arrival_accepted\":false,\"release_ready\":false,\"warnings_errors\":%u}\n",argv[3],UC_ROM,si_cores,predicate?513:0,predicate?1:0,predicate?0:2,predicate?0:1,log_problem_count);return 0;
}
