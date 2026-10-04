/* 観測専用。MDXの新RAM ownerと保存bankの一致を読む。emulator書込は無い。 */
#include "overlays/dex_owner/dex_owner.h"
static void dx_observe(struct mCore*c,unsigned index,unsigned frame)
{
 uint8_t live[522],flash[131072],stock[0x1000],legacy[208];char sha[65],legacy_sha[65],stable_sha[65],bag_sha[65];uint16_t seen=0,caught=0;
 for(unsigned i=0;i<522;i++)live[i]=read8(c,VEGA_DEX_OWNER_RAM+i);
 ng_flash(c,flash);si_digest(live,522,sha);si_digest(live+314,208,legacy_sha);
 unsigned sb1=read32(c,QOL_SAVE_BLOCK1_SLOT),sb2=read32(c,QOL_SAVE_BLOCK2_SLOT);
 si_need(sb1>=0x02000000&&sb1+0x3D40<=0x02040000&&sb2>=0x02000000&&sb2+0xF24<=0x02040000,"dex read-only save pointers");
 unsigned pos=0;
 for(unsigned i=0xEE0;i<0x1200;i++)stock[pos++]=read8(c,sb1+i);
 for(unsigned i=0;i<0x600;i++)stock[pos++]=read8(c,0x0203B0E8+i);
 unsigned inventory[2048];si_inventory(c,inventory);si_inventory_digest(inventory,2048,bag_sha);
 for(unsigned i=0;i<52;i++){legacy[i]=read8(c,sb1+0x5F8+i);legacy[52+i]=read8(c,sb1+0x3A18+i);legacy[104+i]=read8(c,sb2+0x5C+i);legacy[156+i]=read8(c,sb2+0x28+i);}
 si_digest(stock,pos,stable_sha);
 unsigned valid=VegaDexValidate(live,522)==VEGA_DEX_OK,matching=0;
 if(valid){si_need(VegaDexCount(live,522,VEGA_DEX_GET_SEEN,&seen)==0&&VegaDexCount(live,522,VEGA_DEX_GET_CAUGHT,&caught)==0,"read-only counts");}
 for(unsigned i=0;i<28;i++){
  const uint8_t*s=flash+4096*i;unsigned id=s[0xFF4]|(s[0xFF5]<<8);uint32_t signature=s[0xFF8]|(s[0xFF9]<<8)|(s[0xFFA]<<16)|((uint32_t)s[0xFFB]<<24);
  uint32_t counter=s[0xFFC]|(s[0xFFD]<<8)|(s[0xFFE]<<16)|((uint32_t)s[0xFFF]<<24);
  if(id==13&&signature==0x08012025&&counter==read32(c,SI_COUNTER)&&!memcmp(s+0xDE6,live,522))matching++;
 }
 printf("{\"mdx\":%u,\"frame\":%u,\"valid\":%s,\"legacy_snapshot\":%u,\"seen_count\":%u,\"caught_count\":%u,\"live_sha256\":\"%s\",\"legacy_sha256\":\"%s\",\"stock_flags_vars_sha256\":\"%s\",\"bag_sha256\":\"%s\",\"legacy_snapshot_matches_current_stock\":%s,\"physical_matches_current_generation\":%u,\"save_file_status\":%u}\n",index,frame,valid?"true":"false",live[10]&1,seen,caught,sha,legacy_sha,stable_sha,bag_sha,!memcmp(live+314,legacy,208)?"true":"false",matching,read16(c,0x030053F0));
}
