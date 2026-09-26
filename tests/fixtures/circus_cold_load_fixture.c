#include "../../overlays/circus_streak/circus_streak.h"
#include "../../overlays/circus_streak/circus_streak_io.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
uint8_t CircusStreakColdLoad(uint8_t);
static struct {uint8_t before[16];CircusStreakOwner owner;uint8_t after[16];} ram;
static CircusStreakOwner disk;
static unsigned reads,calls,automatic_saves;
static uint8_t delegate_result,requested_type;
CircusStreakOwner *ColdLoadHostOwner(void){return &ram.owner;}
void ColdLoadHostRead(uint16_t sector,uint32_t offset,void *out,uint32_t size)
{
    assert(sector==31 && offset==CIRCUS_STREAK_SECTOR_OFFSET && size==64);
    assert(calls==0);++reads;memcpy(out,&disk,size);
}
uint8_t ColdLoadHostDelegate(uint8_t type)
{
    assert(type==requested_type);assert(reads<=1);assert(calls++==0);
    /* 実既存source restore_original()はsnapshot有時persist_currentを2回呼ぶ。
     * legacy loadがtailを戻さず各SaveがRAM imageを保存する最小の再現。 */
    for(unsigned i=0;i<automatic_saves;++i)memcpy(&disk,&ram.owner,64);
    /* 既存CircusStreakRuntimeSaveLoadの委譲後cache無効化も保持。 */
    memset(&ram.owner,0,64);return delegate_result;
}
static int persist(const CircusStreakOwner *p,void *unused)
{(void)unused;disk=*p;return 1;}
static void setup(CircusStreakOwner value,unsigned saves,uint8_t result)
{
    memset(&ram,0xA5,sizeof(ram));memset(&ram.owner,0,64);disk=value;
    reads=calls=0;automatic_saves=saves;delegate_result=result;requested_type=2;
}
static void boundary(void)
{
    for(unsigned i=0;i<16;++i)assert(ram.before[i]==0xA5 && ram.after[i]==0xA5);
    for(unsigned i=0;i<64;++i)assert(((uint8_t *)&ram.owner)[i]==0);
}
int main(void)
{
    CircusStreakOwner armed={0};
    assert(CircusStreakInitializeFor(&armed,0x40BE35D5,persist,NULL)==0);
    assert(CircusStreakBegin(&armed,persist,NULL)==0);
    assert(CircusStreakArm(&armed,persist,NULL)==0);
    assert(CircusStreakSettle(&armed,1,CIRCUS_WIN,persist,NULL)==0);
    assert(CircusStreakArm(&armed,persist,NULL)==0);
    assert(armed.current==1 && armed.best==1 && armed.prepared==2 && armed.settled==1);
    setup(armed,2,1);assert(ColdLoadHostDelegate(2)==1);
    assert(!CircusStreakValid(&disk)); /* 修復前は2回Saveで消失 */
    setup(armed,2,1);assert(CircusStreakColdLoad(2)==1);boundary();
    assert(reads==1 && calls==1 && !memcmp(&disk,&armed,64));
    assert(CircusStreakLoadBytes(&ram.owner,&disk,armed.save_identity)==0);
    assert(CircusStreakRecover(&ram.owner,persist,NULL)==0);
    assert(ram.owner.current==0 && ram.owner.best==1 && ram.owner.phase==CIRCUS_IDLE
        && ram.owner.last_outcome==CIRCUS_ABORT && ram.owner.prepared==2 && ram.owner.settled==2);
    CircusStreakOwner recovered=ram.owner;
    setup(recovered,0,1);assert(CircusStreakColdLoad(2)==1);boundary();
    assert(CircusStreakLoadBytes(&ram.owner,&disk,recovered.save_identity)==0);
    assert(CircusStreakRecover(&ram.owner,persist,NULL)==CIRCUS_DUPLICATE);
    assert(!memcmp(&ram.owner,&recovered,64)); /* 後続Continueは二重ABORTしない */
    setup(armed,2,1);assert(CircusStreakColdLoad(2)==1);
    assert(CircusStreakLoadBytes(&ram.owner,&disk,0x12345678)==0);
    assert(ram.owner.current==0 && ram.owner.best==0 && ram.owner.session==0
        && ram.owner.save_identity==0x12345678); /* IDは安定field側で拒否 */
    for(unsigned result=0;result<256;++result){
        setup(armed,0,(uint8_t)result);assert(CircusStreakColdLoad(2)==result);boundary();
        assert(reads==1 && calls==1 && !memcmp(&disk,&armed,64));
    }
    for(unsigned bit=0;bit<512;++bit){
        CircusStreakOwner bad=armed;((uint8_t *)&bad)[bit/8]^=(uint8_t)(1U<<(bit%8));
        assert(!CircusStreakValid(&bad));setup(bad,2,1);assert(CircusStreakColdLoad(2)==1);boundary();
        for(unsigned i=0;i<64;++i)assert(((uint8_t *)&disk)[i]==0);
    }
    puts("PASS_CIRCUS_COLD_LOAD preserved64=1 legacy_auto_saves=2 single_bit_corruptions=512 delegate_results=256");
    return 0;
}
