#ifndef VEGA_CIRCUS_FAIRY_LOCK_HOST_H
#define VEGA_CIRCUS_FAIRY_LOCK_HOST_H
#include <stdint.h>
/* 固定CFRU e24a16fe: IsFairyLockActive / switching.c。
 * 新しいSave30以降の操作方針だけ。ROMの交代可否や強制交代は変更しない。
 * Ghost等の例外を推測せず、このfield中は任意交代を控えて通常技選択を続ける。 */
static unsigned fl_defer(unsigned streak,uint32_t flags,uint32_t types)
{
    return streak>=30U && (types&0x04000000U) && (flags&0x00004000U);
}
#ifndef CIRCUS_FAIRY_LOCK_HOST_TEST
static unsigned fl_seen,fl_streak;
static uint32_t fl_flags;
static unsigned fl_observe(struct mCore *c,unsigned streak)
{
    uint32_t flags=read32(c,CF_FLAGS),types=read32(c,CF_TYPES);
    if(!fl_defer(streak,flags,types))return 0U;
    if(!fl_seen || fl_streak!=streak || fl_flags!=flags){
        fprintf(stderr,"CIRCUS_FAIRY_LOCK_SKIP {\"frame\":%u,\"streak\":%u,\"flags\":%u,\"types\":%u,\"hp\":%u,\"pid\":%u,\"ot\":%u,\"host_writes\":0,\"forced_switch_untouched\":true}\n",
            b_frames,streak,flags,types,read16(c,ADDR_BATTLE_MONS+BATTLE_CORE_MON_HP),
            read32(c,ADDR_BATTLE_MONS+0x48U),read32(c,ADDR_BATTLE_MONS+0x54U));
        fl_seen=1U;fl_streak=streak;fl_flags=flags;
    }
    return 1U;
}
#endif
#endif
