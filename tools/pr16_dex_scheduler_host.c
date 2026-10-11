/* Synthetic host execution of the generated scheduler, not a game save. */
#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <stdint.h>
#include <stdlib.h>
static uint8_t flash_bytes[32][4096];
static unsigned reads,erases,programs,stock_calls,updates,serializes,checks;
static int fail_after=-1,lie_after=-1;
static uint8_t host_read(uint8_t sector,void *out)
{assert(sector<32);reads++;memcpy(out,flash_bytes[sector],4096);return 0;}
static uint16_t host_checksum(const void *v,uint16_t size)
{const uint8_t *p=v;uint32_t sum=0;for(unsigned i=0;i<size;i+=4){uint32_t w=0;memcpy(&w,p+i,4);sum+=w;}return (uint16_t)(sum+(sum>>16));}
static uint16_t host_erase(uint16_t sector)
{assert(sector<32);erases++;memset(flash_bytes[sector],255,4096);return 0;}
static uint16_t host_program(uint16_t sector,uint32_t index,uint8_t value)
{assert(sector<32&&index<4096);programs++;if(fail_after>=0&&(int)programs>=fail_after)return 1;if(lie_after<0||(int)programs!=lie_after)flash_bytes[sector][index]&=value;return 0;}
static uint8_t host_try(uint8_t sector,uint8_t *data)
{assert(sector<32);erases++;programs+=4096;memcpy(flash_bytes[sector],data,4096);return 1;}
static void host_update(void){updates++;}
static void host_serialize(void){serializes++;}
static uint8_t host_stock(uint8_t mode);
#include SCHEDULER_SOURCE
static uint8_t host_stock(uint8_t mode)
{stock_calls++;if(mode==1){for(unsigned i=0;i<5;++i)(void)DexImpl_Stage61State_HandleWriteSector(i,G_RAM_SAVE_SECTOR_LOCATIONS);}else if(mode==2){(void)DexImpl_Stage61State_HandleWriteSector(0,G_RAM_SAVE_SECTOR_LOCATIONS);}return 0;}
static void count(void){checks++;}
static void descriptors(void)
{
 struct Stage61SaveBlockChunk *c=(void*)G_RAM_SAVE_SECTOR_LOCATIONS;
 assert(stage61_save_build_live_descriptors(c));
}
static void reset(void)
{
 memset((void*)0x02000000,0,0x40000);memset((void*)0x03000000,0,0x8000);memset(flash_bytes,255,sizeof(flash_bytes));
 G_SAVE_BLOCK1_PTR=(void*)0x02004000;G_SAVE_BLOCK2_PTR=(void*)0x02008000;G_POKEMON_STORAGE_PTR=(void*)0x02010000;G_FAST_SAVE_SECTION=(void*)0x02020000;
 G_ERASE_FLASH_SECTOR=host_erase;G_PROGRAM_FLASH_BYTE=host_program;
 for(unsigned i=0;i<STAGE61_SAVE_BLOCK1_SIZE;i++)G_SAVE_BLOCK1_PTR[i]=(uint8_t)i;
 for(unsigned i=0;i<STAGE61_SAVE_BLOCK2_SIZE;i++)G_SAVE_BLOCK2_PTR[i]=(uint8_t)(i+31);
 for(unsigned i=0;i<STAGE61_POKEMON_STORAGE_SIZE;i++)G_POKEMON_STORAGE_PTR[i]=(uint8_t)(i+67);
 assert(VegaDexInitNew((uint8_t*)DEX_LIVE,522)==0);descriptors();reads=erases=programs=stock_calls=updates=serializes=0;fail_after=lie_after=-1;
}
static void saved(void){assert(DexImpl_Stage61State_HandleSavingData(0)==0);assert(G_DAMAGED_SAVE_SECTORS==0);}
static unsigned record_sector(void){return stage61_save_physical_sector_for_id(13);}
static void access(unsigned owner,unsigned mode){uint8_t out;assert(VegaDexAccess((uint8_t*)DEX_LIVE,522,owner,mode,&out)==0);}
static void all_banks(void)
{
 reset();access(1205,VEGA_DEX_SET_CAUGHT);saved();assert(G_SAVE_COUNTER==1&&G_FIRST_SAVE_SECTOR==1);assert(!memcmp(flash_bytes[record_sector()]+0xDE6,(void*)DEX_LIVE,522));count();
 uint8_t old[522];memcpy(old,(void*)DEX_LIVE,522);access(128,VEGA_DEX_SET_SEEN);saved();assert(G_SAVE_COUNTER==2);unsigned newer=record_sector();flash_bytes[newer][0xDF2]^=1;
 assert(DexImpl_Stage61State_GetSaveValidStatus(G_RAM_SAVE_SECTOR_LOCATIONS)==255);assert(G_SAVE_COUNTER==1);count();
 memset((void*)DEX_LIVE,0x77,522);assert(DexImpl_Stage61State_HandleLoadSector(0,G_RAM_SAVE_SECTOR_LOCATIONS)==1);assert(!memcmp(old,(void*)DEX_LIVE,522));count();
 flash_bytes[record_sector()][0xDF2]^=1;assert(DexImpl_Stage61State_GetSaveValidStatus(G_RAM_SAVE_SECTOR_LOCATIONS)==2);memset((void*)DEX_LIVE,0x88,522);(void)DexImpl_Stage61State_HandleLoadSector(0,G_RAM_SAVE_SECTOR_LOCATIONS);for(unsigned i=0;i<522;i++)assert(DEX_LIVE[i]==0);count();
 for(unsigned blank=0;blank<2;blank++){
  reset();saved();memset(flash_bytes[record_sector()]+0xDE6,blank?255:0,522);assert(DexImpl_Stage61State_GetSaveValidStatus(G_RAM_SAVE_SECTOR_LOCATIONS)==1);(void)DexImpl_Stage61State_HandleLoadSector(0,G_RAM_SAVE_SECTOR_LOCATIONS);assert(VegaDexValidate((void*)DEX_LIVE,522)==0);assert(DEX_LIVE[10]==1);count();
 }
}
static void invalid_live(void)
{
 for(unsigned mode=0;mode<6;mode++){
  reset();saved();uint8_t before[sizeof(flash_bytes)];memcpy(before,flash_bytes,sizeof(before));DEX_LIVE[0]^=1;unsigned e=erases,p=programs,s=stock_calls;
  assert(DexImpl_Stage61State_HandleSavingData(mode)==255);assert(e==erases&&p==programs&&s==stock_calls&&!memcmp(before,flash_bytes,sizeof(before)));count();
 }
}
static void linkfull(void)
{
 reset();saved();access(1205,VEGA_DEX_SET_SEEN);assert(DexImpl_Stage61State_HandleReplaceSector(13,G_RAM_SAVE_SECTOR_LOCATIONS)==1);unsigned at=record_sector();assert(flash_bytes[at][0xFF8]==255);count();
 unsigned p=programs;flash_bytes[at][0xDE6]^=1;assert(DexImpl_Stage61State_CommitSignatureByte(14,G_RAM_SAVE_SECTOR_LOCATIONS)==255);assert(programs==p&&flash_bytes[at][0xFF8]==255);count();
 G_DAMAGED_SAVE_SECTORS=0;assert(DexImpl_Stage61State_HandleReplaceSector(13,G_RAM_SAVE_SECTOR_LOCATIONS)==1);assert(DexImpl_Stage61State_CommitSignatureByte(14,G_RAM_SAVE_SECTOR_LOCATIONS)==1);assert(flash_bytes[at][0xFF8]==0x25);assert(!memcmp(flash_bytes[at]+0xDE6,(void*)DEX_LIVE,522));count();
}
static void partial_link(void)
{
 reset();saved();uint8_t old_pc[0x7D0],old_mdx[522];unsigned src=record_sector();memcpy(old_pc,flash_bytes[src],sizeof(old_pc));memcpy(old_mdx,flash_bytes[src]+0xDE6,522);
 access(1205,VEGA_DEX_SET_CAUGHT);memset((void*)(G_POKEMON_STORAGE_PTR+0x7C00),0xE5,0x7D0);
 assert(DexImpl_Stage61State_EnsureBackupGeneration(G_RAM_SAVE_SECTOR_LOCATIONS)==1);assert(G_SAVE_COUNTER==1);unsigned backup=src-14;assert(!memcmp(flash_bytes[backup]+0xDE6,old_mdx,522));count();
 assert(DexImpl_Stage61State_UpdateRecordOnly(G_RAM_SAVE_SECTOR_LOCATIONS)==1);assert(G_SAVE_COUNTER==2);assert(!memcmp(flash_bytes[backup],old_pc,sizeof(old_pc)));assert(!memcmp(flash_bytes[backup]+0xDE6,(void*)DEX_LIVE,522));count();
 reset();saved();uint8_t before[522];memcpy(before,flash_bytes[record_sector()]+0xDE6,522);access(5,VEGA_DEX_SET_SEEN);assert(DexImpl_Stage61State_HandleSavingData(2)==0);assert(!memcmp(before,flash_bytes[record_sector()]+0xDE6,522));count();
}
static void torn(void)
{
 for(unsigned f=1;f<=2;f++){
  reset();saved();uint8_t old[14*4096];memcpy(old,flash_bytes+14,sizeof(old));access(1000,VEGA_DEX_SET_SEEN);
  if(f==1)fail_after=programs+522;else lie_after=programs+0xDE7;
  assert(DexImpl_Stage61State_HandleSavingData(0)==255);assert(G_SAVE_COUNTER==1&&!memcmp(old,flash_bytes+14,sizeof(old)));count();
 }
}
int main(void)
{
 assert(mmap((void*)0x02000000,0x40000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)0x02000000);
 assert(mmap((void*)0x03000000,0x8000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)0x03000000);
 all_banks();invalid_live();linkfull();partial_link();torn();printf("{\"status\":\"PASS_SYNTHETIC_HOST_SAVE_SCHEDULER\",\"cases\":%u,\"native_game_runs\":0}\n",checks);return 0;
}
