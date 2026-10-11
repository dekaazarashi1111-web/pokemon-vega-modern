/* 旧loadはlegacy2048byteだけを戻してFactoryの2段階復旧Saveを行う。
 * その前にCRC-validなCircus tail64だけをRAM imageへ戻し、消失を防ぐ。
 * 旧loadへ一度だけ委譲し、既存Circus adapterの後段cache無効化を保持する。
 * 主人公IDの受入/ABORT確定は既存の安定field復旧が所有する。 */
#include "circus_streak.h"
#ifdef CIRCUS_COLD_LOAD_HOST_TEST
extern CircusStreakOwner *ColdLoadHostOwner(void);
extern void ColdLoadHostRead(uint16_t, uint32_t, void *, uint32_t);
extern uint8_t ColdLoadHostDelegate(uint8_t);
#define COLD_OWNER ColdLoadHostOwner()
#define COLD_READ ColdLoadHostRead
#define COLD_DELEGATE ColdLoadHostDelegate
#else
#include "circus_cold_load_addresses.h"
#define COLD_OWNER ((CircusStreakOwner *)(uintptr_t)CIRCUS_STREAK_ADDRESS)
#define COLD_READ ((void (*)(uint16_t,uint32_t,void *,uint32_t))(uintptr_t)0x081C2A55u)
#define COLD_DELEGATE ((uint8_t (*)(uint8_t))(uintptr_t)CIRCUS_COLD_PREVIOUS_LOAD)
#endif

__attribute__((used,noinline,externally_visible))
uint8_t CircusStreakColdLoad(uint8_t save_type)
{
    CircusStreakOwner saved;
    uint8_t *target=(uint8_t *)COLD_OWNER;
    size_t i;
    COLD_READ(31u,CIRCUS_STREAK_SECTOR_OFFSET,&saved,CIRCUS_STREAK_SIZE);
    if (CircusStreakValid(&saved)) {
        const uint8_t *source=(const uint8_t *)&saved;
        for (i=0u;i<CIRCUS_STREAK_SIZE;++i) target[i]=source[i];
    } else {
        for (i=0u;i<CIRCUS_STREAK_SIZE;++i) target[i]=0u;
    }
    return COLD_DELEGATE(save_type);
}
