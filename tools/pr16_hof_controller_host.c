/* controller専用host callback。ゲーム/S61E/MDXの受入を代替しない。 */
#include <stdint.h>
#include <string.h>
#include "overlays/hof_journal/hof_transaction.h"
static uint8_t flash[32][4096],sector[4096],hof[7936];
static HT_Workspace work;
static const uint16_t sizes[14]={0xF24,0xF80,0xF80,0xF80,0xEC0,0xF80,0xF80,0xF80,0xF80,0xF80,0xF80,0xF80,0xF80,0x7D0};
static unsigned reads,erases,programs,prepares,validations,selects,write_ops,blocked;
static unsigned cut_at,fault_type,fault_at,fault_mode,fault_prefix,prepare_change;
static unsigned erase_trace[128],erase_ops[128],prepare_during_pending;
static uint32_t rd32(const uint8_t *p){return(uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static unsigned rd16(const uint8_t *p){return p[0]|(unsigned)p[1]<<8;}
static void wr32(uint8_t *p,uint32_t v){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(v>>(8*i));}
static uint16_t checksum(const uint8_t *b,unsigned n){uint32_t v=0;for(unsigned i=0;i<n;i+=4)v+=rd32(b+i);return(uint16_t)(v+(v>>16));}
static int read_cb(void *user,unsigned p,uint8_t *out){(void)user;if(blocked||p>=32)return 0;reads++;memcpy(out,flash[p],4096);return 1;}
static int erase_cb(void *user,unsigned p){(void)user;if(blocked||p>=30)return 0;erases++;write_ops++;if(erases<=128){erase_trace[erases-1]=p;erase_ops[erases-1]=write_ops;}
 if(fault_type==1&&erases==fault_at){if(fault_mode==1)return 1;if(fault_mode==2){memset(flash[p],255,fault_prefix);blocked=1;return 0;}if(fault_mode==3)return 0;}
 memset(flash[p],255,4096);if(cut_at&&write_ops==cut_at){blocked=1;return 0;}return 1;}
static int program_cb(void *user,unsigned p,unsigned off,uint8_t v){(void)user;if(blocked||p>=30||off>=4096)return 0;programs++;write_ops++;
 if(fault_type==2&&programs==fault_at){if(fault_mode==1)return 1;if(fault_mode==3)return 0;}
 flash[p][off]&=v;if(cut_at&&write_ops==cut_at){blocked=1;return 0;}return 1;}
static int valid_sector(const HT_Main *m,unsigned id,const uint8_t *b){return id<14&&rd16(b+0xFF4)==id&&rd16(b+0xFF6)==checksum(b,sizes[id])&&rd32(b+0xFF8)==0x08012025u&&rd32(b+0xFFC)==m->counter&&m->base==14*(m->counter&1);}
static int bank(unsigned base,HT_Main *m){unsigned seen=0;uint32_t counter=0;unsigned first=0;for(unsigned p=0;p<14;p++){const uint8_t *b=flash[base+p];unsigned id=rd16(b+0xFF4);if(id>=14||(seen&(1u<<id)))return 0;if(!p)counter=rd32(b+0xFFC);m->base=(uint8_t)base;m->counter=counter;if(!valid_sector(m,id,b))return 0;seen|=1u<<id;if(id==0)first=p;}for(unsigned p=0;p<14;p++)if(rd16(flash[base+p]+0xFF4)!=(p+14-first)%14)return 0;m->first=(uint8_t)first;return seen==0x3FFF;}
static int select_cb(void *user,HT_Main *out,uint8_t *buffer){HT_Main a,b;int x,y;(void)user;(void)buffer;selects++;if(blocked)return 0;x=bank(0,&a);y=bank(14,&b);if(!x&&!y)return 0;if(x&&y){uint32_t delta=b.counter-a.counter;if(delta==0x80000000u)return 0;*out=(delta&&delta<0x80000000u)?b:a;}else *out=x?a:b;return 1;}
static int validate_cb(void *user,const HT_Main *m,unsigned id,const uint8_t *b){(void)user;validations++;return valid_sector(m,id,b);}
static int prepare_cb(void *user,const HT_Main *source,const HT_Main *target,unsigned id,const uint8_t *j,uint8_t *b){(void)user;prepares++;if(id>=14||blocked)return 0;memcpy(b,flash[source->base+(source->first+id)%14],4096);wr32(b+0xFFC,target->counter);if(id==4){memset(b+0xEC0,0,304);if(j)memcpy(b+0xEC0,j,256);}if(prepare_change&&id==1)b[0]^=0x51;unsigned check=checksum(b,sizes[id]);b[0xFF6]=(uint8_t)check;b[0xFF7]=(uint8_t)(check>>8);if(prepare_change==2&&prepares>14)b[10]^=1;return 1;}
static const HT_Ops ops={0,read_cb,erase_cb,program_cb,select_cb,validate_cb,prepare_cb};
void HC_Reset(const uint8_t *input){memcpy(flash,input,sizeof flash);memset(&work,0,sizeof work);memset(sector,0,sizeof sector);memset(hof,0,sizeof hof);work.sector=sector;work.hof=hof;reads=erases=programs=prepares=validations=selects=write_ops=blocked=0;cut_at=fault_type=fault_at=fault_mode=fault_prefix=prepare_change=prepare_during_pending=0;memset(erase_trace,0,sizeof erase_trace);memset(erase_ops,0,sizeof erase_ops);}
void HC_Fault(unsigned type,unsigned at,unsigned mode,unsigned prefix){fault_type=type;fault_at=at;fault_mode=mode;fault_prefix=prefix;}
void HC_Cut(unsigned at){cut_at=at;}
void HC_Change(unsigned value){prepare_change=value;}
int HC_Run(unsigned method,const uint8_t *next,unsigned kind,unsigned slot,unsigned absence){if(method==0)return HT_Resolve(&ops,&work);if(method==1)return HT_Recover(&ops,&work);if(method==2)return HT_Commit(&ops,&work,next,kind,slot,(int)absence);if(method==3)return HT_Normal(&ops,&work);return -99;}
void HC_Copy(uint8_t *out){memcpy(out,flash,sizeof flash);}
void HC_Payload(uint8_t *out){memcpy(out,hof,sizeof hof);}
void HC_Result(uint32_t *out){out[0]=work.result.main.counter;out[1]=work.result.main.base;out[2]=work.result.main.first;out[3]=work.result.has_hof;out[4]=work.result.has_journal;out[5]=work.result.pending;out[6]=work.result.route;out[7]=(uint32_t)work.result.epoch;out[8]=(uint32_t)(work.result.epoch>>32);out[9]=reads;out[10]=erases;out[11]=programs;out[12]=prepares;out[13]=write_ops;out[14]=blocked;out[15]=validations;}
void HC_Erases(uint32_t *sectors,uint32_t *ops_out){for(unsigned i=0;i<erases&&i<128;i++){sectors[i]=erase_trace[i];ops_out[i]=erase_ops[i];}}
