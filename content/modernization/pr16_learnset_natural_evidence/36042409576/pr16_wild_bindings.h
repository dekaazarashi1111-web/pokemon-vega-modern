#include "pr16_learnset_runtime.h"
#define PR16_IMAGE ((const uint8_t *)0x95dee7cu)
#define PR16_IMAGE_SIZE 108008u
#define PR16_READ_VIEW ((uint8_t (*)(const uint8_t *,uint32_t,uint16_t,uint8_t,struct Pr16RuntimeView *))0x95f94d3u)
#define PR16_GET_MON_DATA ((uint32_t (*)(const void *,int,uint8_t *))0x0803F355u)
#define PR16_GET_BOX_LEVEL ((uint8_t (*)(const void *))0x0803DF9Du)
#define PR16_SET_MON_DATA ((void (*)(void *,int,const void *))0x0803FA71u)
#define PR16_INITIAL ((void (*)(void *))0x95f9949u)
static inline uint8_t pr16_wild_slot(void *mon) {
    uintptr_t base=0x02023F8Cu;
    for(uint8_t i=0;i<6u;++i,base+=100u) if((uintptr_t)mon==base) return 1u;
    return 0u;
}
#define PR16_WILD_SLOT pr16_wild_slot
