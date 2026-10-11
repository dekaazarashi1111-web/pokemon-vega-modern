/* 旧120byte undoと正確世代token。空き詰め/圧縮/履歴削減は行わない。 */
#include "hof_journal.h"
static uint32_t read32(const uint8_t *p)
{ return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24; }
static uint64_t read64(const uint8_t *p)
{ return (uint64_t)read32(p) | (uint64_t)read32(p+4)<<32; }
static void write32(uint8_t *p,uint32_t n)
{ unsigned i; for(i=0;i<4;i++)p[i]=(uint8_t)(n>>(8*i)); }
static void write64(uint8_t *p,uint64_t n)
{ write32(p,(uint32_t)n);write32(p+4,(uint32_t)(n>>32)); }
static uint32_t crc(const uint8_t *p,unsigned n)
{ uint32_t v=0xffffffffu;unsigned i,b;for(i=0;i<n;i++){v^=p[i];for(b=0;b<8;b++)v=(v>>1)^(0xedb88320u & (0u-(v&1u)));}return v^0xffffffffu; }
int HJ_Validate(const uint8_t j[HJ_SIZE])
{
 if(!j || j[0]!='H'||j[1]!='J'||j[2]!='3'||j[3]!='2'||j[4]!=1||j[5]||j[6]!=(HJ_SIZE&255u)||j[7]!=(HJ_SIZE>>8))return 0;
 if(read32(j+12)!=read32(j+8)+1u || read64(j+16)==UINT64_MAX || read64(j+24)!=read64(j+16)+1u)return 0;
 if(j[98]||j[99]||!((j[96]==HJ_APPEND&&j[97]<HJ_TEAMS)||((j[96]==HJ_SHIFT||j[96]==HJ_INITIAL)&&j[97]==0)))return 0;
 return read32(j+252)==crc(j,252);
}
int HJ_Build(uint8_t out[HJ_SIZE],const uint8_t old[HJ_PAYLOAD],const uint8_t next[HJ_PAYLOAD],uint32_t counter,uint64_t epoch,const uint8_t old_sha[32],const uint8_t new_sha[32],const uint8_t source_sha[32],unsigned kind,unsigned slot)
{
 uint8_t j[HJ_SIZE];unsigned i,at;
 if(!out||!old||!next||!old_sha||!new_sha||!source_sha||epoch==UINT64_MAX)return 0;
 if(!((kind==HJ_APPEND&&slot<HJ_TEAMS)||((kind==HJ_SHIFT||kind==HJ_INITIAL)&&slot==0)))return 0;
 at=slot*HJ_TEAM;
 for(i=0;i<HJ_PAYLOAD;i++){
  if(kind==HJ_INITIAL && old[i])return 0;
  if(kind==HJ_APPEND||kind==HJ_INITIAL){if((i<at||i>=at+HJ_TEAM)&&old[i]!=next[i])return 0;}
  else if(i<HJ_TAIL-HJ_TEAM){if(old[i+HJ_TEAM]!=next[i])return 0;}
  else if(i>=HJ_TAIL&&old[i]!=next[i])return 0;
 }
 for(i=0;i<HJ_SIZE;i++)j[i]=0;
 j[0]='H';j[1]='J';j[2]='3';j[3]='2';j[4]=1;j[6]=(HJ_SIZE&255u);j[7]=(HJ_SIZE>>8);
 write32(j+8,counter);write32(j+12,counter+1u);write64(j+16,epoch);write64(j+24,epoch+1u);
 for(i=0;i<32;i++){j[32+i]=old_sha[i];j[64+i]=new_sha[i];}
 j[96]=(uint8_t)kind;j[97]=(uint8_t)slot;
 for(i=0;i<HJ_TEAM;i++)j[100+i]=old[at+i];
 for(i=0;i<32;i++)j[220+i]=source_sha[i];
 write32(j+252,crc(j,252));for(i=0;i<HJ_SIZE;i++)out[i]=j[i];return 1;
}
int HJ_Rollback(uint8_t out[HJ_PAYLOAD],const uint8_t next[HJ_PAYLOAD],const uint8_t j[HJ_SIZE])
{
 unsigned i,at;
 if(!out||!next||!HJ_Validate(j))return 0;
 /* 同一bufferも許す。shift復元は末尾から行い未読sourceを保持する。 */
 if(j[96]==HJ_SHIFT){for(i=HJ_PAYLOAD;i>HJ_TAIL;i--)out[i-1]=next[i-1];for(i=HJ_TAIL;i>HJ_TEAM;i--)out[i-1]=next[i-1-HJ_TEAM];at=0;}
 else{for(i=0;i<HJ_PAYLOAD;i++)out[i]=next[i];at=j[97]*HJ_TEAM;}
 for(i=0;i<HJ_TEAM;i++)out[at+i]=j[100+i];
 return 1;
}
