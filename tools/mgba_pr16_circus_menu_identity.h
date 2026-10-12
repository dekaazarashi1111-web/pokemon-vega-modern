#ifndef VEGA_CIRCUS_MENU_IDENTITY_H
#define VEGA_CIRCUS_MENU_IDENTITY_H
#include <stdint.h>
/* メニューを開く前のslotは保持しない。開いた後の実個体から一意に再解決。 */
static inline unsigned mi_find(unsigned count,const uint32_t *pid,const uint32_t *ot,
    const uint16_t *species,uint32_t wanted_pid,uint32_t wanted_ot,unsigned wanted_species)
{
    unsigned found=3U;
    if(count!=3U || !wanted_species || wanted_species>65535U)return 3U;
    for(unsigned i=0;i<count;++i)
        if(pid[i]==wanted_pid && ot[i]==wanted_ot && species[i]==wanted_species){
            if(found!=3U)return 3U;
            found=i;
        }
    return found;
}
#endif
