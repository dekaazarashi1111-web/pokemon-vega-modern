#include <string.h>
#include "pr16_learnset_supply_bindings.h"
const uint8_t *SupplyFixtureImage;
uint32_t SupplyFixtureSize;
uint8_t SupplyFixtureMode;
static uint8_t flag, policy, tutor[16];
static uint32_t parent_calls;
void SupplyFixtureSetup(const uint8_t *image,uint32_t size,uint8_t mode,
    uint8_t unlocked,uint8_t owner_policy,const uint8_t *bits)
{
    SupplyFixtureImage=image; SupplyFixtureSize=size; SupplyFixtureMode=mode;
    flag=unlocked;policy=owner_policy;parent_calls=0;memcpy(tutor,bits,16);
}
uint32_t SupplyFixtureData(const void *mon,int field,uint8_t *unused)
{
    const uint8_t *p=mon;(void)unused;
    if (field==11) return p[0]|(uint32_t)p[1]<<8;
    if (field==45) return p[2];
    if (field>=13 && field<=16) return p[4+(field-13)*2]|(uint32_t)p[5+(field-13)*2]<<8;
    return 0;
}
uint8_t SupplyFixtureConditional(uint16_t owner,uint8_t consumer,struct Pr16RuntimeView *view)
{
    if (policy!=1 || owner>=1671u) return PR16_OWNER_PRESERVE_IDENTITY;
    view->owner=owner;view->bytes=tutor;view->count=consumer==PR16_CONSUMER_TUTOR ? 64u : 0u;
    return PR16_OWNER_PREPARED_LOOKUP;
}
uint8_t SupplyFixtureFlag(uint16_t id) { return id==0x082cu ? flag : 0u; }
uint8_t SupplyFixtureParent(void *mon,uint16_t *out)
{
    (void)mon;++parent_calls;out[0]=777u;return 1;
}
uint32_t SupplyFixtureParentCalls(void) { return parent_calls; }
