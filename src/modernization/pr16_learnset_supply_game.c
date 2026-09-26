#include "pr16_learnset_supply_game.h"
#include "pr16_learnset_supply_bindings.h"
static uint8_t owned(void *mon, uint8_t consumer, struct Pr16RuntimeView *view)
{
    uint16_t species;
    if (!mon || PR16_SUPPLY_GET_MON_DATA(mon,45,(uint8_t *)0)) return 0;
    species=(uint16_t)PR16_SUPPLY_GET_MON_DATA(mon,11,(uint8_t *)0);
    return PR16_SUPPLY_READ_CONDITIONAL(species,consumer,view)==PR16_OWNER_PREPARED_LOOKUP &&
        view->owner==species;
}
uint8_t Pr16_GameSupplyTutorSlot(void *mon, uint8_t slot)
{
    struct Pr16RuntimeView view;
    if (slot>=64u || !owned(mon,PR16_CONSUMER_TUTOR,&view)) return 0;
    return Pr16SupplyTutorBit(&view,view.owner,slot);
}
uint16_t Pr16_GameSupplyArchiveRowCount(void *mon, uint8_t family)
{
    struct Pr16RuntimeView view;
    uint16_t scratch[160], count=0;
    if (family>1u || !PR16_SUPPLY_FLAG_GET(0x082cu) ||
        !owned(mon,PR16_CONSUMER_EVOLUTION,&view)) return 0;
    if (!Pr16SupplyDecode(PR16_SUPPLY_IMAGE,PR16_SUPPLY_IMAGE_SIZE,view.owner,
        family,scratch,160u,&count)) return 0;
    return count;
}
uint8_t Pr16_GameSupplyRelearner(void *mon, uint16_t *moves)
{
    struct Pr16RuntimeView view;
    uint16_t archive[160], known[4], count=0;
    uint8_t mode, i;
    if (!mon || !moves) return 0;
    mode=*PR16_SUPPLY_MEMORY_MODE;
    /* Existing normal/egg consumers remain byte-for-byte separate. */
    if (mode<2u) return PR16_SUPPLY_PARENT_RELEARNER(mon,moves);
    if (mode>7u || !PR16_SUPPLY_FLAG_GET(0x082cu) ||
        !owned(mon,PR16_CONSUMER_EVOLUTION,&view)) return 0;
    if (!Pr16SupplyDecode(PR16_SUPPLY_IMAGE,PR16_SUPPLY_IMAGE_SIZE,view.owner,
        mode==7u ? PR16_SUPPLY_TUTOR : PR16_SUPPLY_MACHINE,archive,160u,&count)) return 0;
    for (i=0;i<4u;++i) known[i]=(uint16_t)PR16_SUPPLY_GET_MON_DATA(mon,13+i,(uint8_t *)0);
    return Pr16SupplyPage(archive,count,known,mode,1u,moves,40u);
}
