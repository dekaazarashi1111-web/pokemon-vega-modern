/* START callback限定。全mode sweepはdispatch oracleでありmode副作用受入ではない。 */
static unsigned sf_mode;
static uint32_t start_gate(unsigned input,unsigned sp)
{
 get(0x02000000,ram_before,262144);get(0x03000000,all_iwram_before,32768);calls++;
 set("cpsr",0xDF);set("sp",sp);set("lr",0x08000001);
 for(unsigned i=0;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);set(n,i==0?input:i==5?sf_mode:0x77000000+i);}
 set("cpsr",0xFF);set("pc",0x080DB361);unsigned target;
 for(unsigned i=0;;i++){
  need(i<2000000,"bounded START gate");unsigned pc=(reg("pc")&~1u)-2;
  if(pc==0x080DB368||pc==0x080DB384||pc==0x080DB36E){target=pc;break;}
  need(pc!=0x080F6150&&pc!=0x080F64A8&&pc!=0x080DB178&&pc!=0x080DA9C0,"no UI/Flash/wipe executed in gate");c->step(c);steps++;
 }
 need(reg("sp")==sp,"exact SP");for(unsigned i=4;i<12;i++){char n[8];snprintf(n,sizeof(n),"r%u",i);need(reg(n)==(i==5?sf_mode:0x77000000+i),"all callee registers retained");}
 for(unsigned i=0;i<262144;i++)need(c->busRead8(c,0x02000000+i)==ram_before[i],"all EWRAM unchanged");ram_check(sp);return target;
}
int main(int argc,char**argv)
{
 need(argc==2,"one candidate");c=mCoreFind(argv[1]);need(c&&c->init(c),"core init");mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");need(mCoreLoadFile(c,argv[1]),"candidate load");c->setVideoBuffer(c,video,240);c->reset(c);reset();
 w32(0x03000FA4,0x0806F131);
 for(sf_mode=0;sf_mode<256;sf_mode++){w32(DAMAGED,0);need(start_gate(255,STACK)==(sf_mode==0||sf_mode==4?0x080DB36E:0x080DB368),"all256 mode dispatch");count();}
 const unsigned modes[]={0,4,1,3,5,255},callbacks[]={0x0806F131,0,0x0806F16D},status[]={0,1,255},masks[]={0,4,1u<<13,1u<<31};
 for(unsigned valid=0;valid<2;valid++)for(unsigned cb=0;cb<3;cb++)for(unsigned m=0;m<6;m++)for(unsigned s=0;s<3;s++)for(unsigned mask=0;mask<4;mask++)for(unsigned sp=0;sp<2;sp++){
  put(LIVE,live,522);if(!valid)c->busWrite8(c,LIVE+4,(uint8_t)(live[4]^1));sf_mode=modes[m];w32(0x03000FA4,callbacks[cb]);w32(DAMAGED,masks[mask]);
  unsigned want=status[s]==255&&!valid?0x080DB36E:status[s]!=255&&!masks[mask]?0x080DB384:cb==0&&(m==0||m==1)?0x080DB36E:0x080DB368;
  need(start_gate(status[s],STACK+sp*4)==want,"exact valid/invalid callback mode status mask alignment matrix");count();
 }
 need(checks==1120,"256 dispatch plus864 boundary cases");
 printf("{\"status\":\"PASS_START_ONLY_VALID_FAILURE_GATE\",\"cases\":%u,\"calls\":%u,\"steps\":%llu,\"all_byte_modes_dispatched\":256,\"boundary_cases\":864,\"native_processes\":1,\"real_flash_failures\":0,\"real_ui\":0,\"all_save_modes_accepted\":false,\"formal_save_changed\":false}\n",checks,calls,(unsigned long long)steps);fflush(stdout);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
