/* Issue19: fresh wild adapter only. Retire V4 fixed four-move grants.
 * Never call this on player/Box storage or preserve-only owners. */
#include "pr16_wild_bindings.h"
uint8_t Pr16_GameApplyWildInitialMoves(void *mon)
{
    struct Pr16RuntimeView view;
    uint32_t zero = 0;
    uint16_t species;
    uint8_t level, field;
    if (!mon || !PR16_WILD_SLOT(mon))
        return 0;
    if (PR16_GET_MON_DATA(mon, 45, (uint8_t *)0))
        return 0;
    species = (uint16_t)PR16_GET_MON_DATA(mon, 11, (uint8_t *)0);
    if (PR16_READ_VIEW(PR16_IMAGE, PR16_IMAGE_SIZE, species,
                      PR16_CONSUMER_LEVEL_UP, &view) != PR16_OWNER_PREPARED_LOOKUP)
        return 0;
    level = PR16_GET_BOX_LEVEL(mon);
    if (level < 1u || level > 100u)
        return 0;
    /* Species may already have been normalized by a wild-only adapter.
     * Clear the former species/V4 slots, PP and PP Ups only after the gate.
     * The accepted original initializer supplies raw-row-order moves + PP. */
    for (field = 13u; field <= 21u; ++field)
        PR16_SET_MON_DATA(mon, field, &zero);
    PR16_INITIAL(mon);
    return 1;
}
