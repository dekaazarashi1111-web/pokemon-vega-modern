#include "hm_field_access.h"

#include <stddef.h>
#include <stdint.h>

typedef uint8_t (*VegaHMFieldMoveCallback)(void);

enum {
    VEGA_HM_PARTY_SIZE = 6u,
    VEGA_HM_PLAYER_AVATAR_FLAG_SURFING = 8u,
    VEGA_HM_SHOULD_NOT_BE_SURFING = 1u,
    VEGA_HM_SHOULD_BE_SURFING = 2u,

    VEGA_MOVE_CUT = 15u,
    VEGA_MOVE_FLY = 19u,
    VEGA_MOVE_SURF = 57u,
    VEGA_MOVE_STRENGTH = 70u,
    VEGA_MOVE_WATERFALL = 127u,
    VEGA_MOVE_FLASH = 148u,
    VEGA_MOVE_ROCK_SMASH = 249u,
    VEGA_MOVE_DIVE = 291u,

    /* Vega IPSが既に使っているHM01..08。追加canonical IDは使用しない。 */
    VEGA_ITEM_HM01_CUT = 339u,
    VEGA_ITEM_HM02_FLY = 340u,
    VEGA_ITEM_HM03_SURF = 341u,
    VEGA_ITEM_HM04_STRENGTH = 342u,
    VEGA_ITEM_HM05_FLASH = 343u,
    VEGA_ITEM_HM06_ROCK_SMASH = 344u,
    VEGA_ITEM_HM07_WATERFALL = 345u,
    VEGA_ITEM_HM08_DIVE = 346u,
};

#define VEGA_HM_CHECK_BAG_HAS_ITEM \
    ((uint8_t (*)(uint16_t, uint16_t))(uintptr_t)0x08099949u)
#define VEGA_HM_TEST_PLAYER_AVATAR_FLAGS \
    ((uint8_t (*)(uint8_t))(uintptr_t)0x0805C009u)

#define VEGA_HM_SETUP_FLASH ((VegaHMFieldMoveCallback)(uintptr_t)0x080CACF9u)
#define VEGA_HM_SETUP_CUT ((VegaHMFieldMoveCallback)(uintptr_t)0x080972C5u)
#ifndef VEGA_HM_SETUP_FLY_ADDRESS
#error "VEGA_HM_SETUP_FLY_ADDRESS must come from the linked T06 contract"
#endif
#define VEGA_HM_SETUP_FLY \
    ((VegaHMFieldMoveCallback)(uintptr_t)VEGA_HM_SETUP_FLY_ADDRESS)
#define VEGA_HM_SETUP_STRENGTH ((VegaHMFieldMoveCallback)(uintptr_t)0x080D18ADu)
#ifndef VEGA_HM_SETUP_SURF_ADDRESS
#error "VEGA_HM_SETUP_SURF_ADDRESS must come from the linked T06 contract"
#endif
#define VEGA_HM_SETUP_SURF \
    ((VegaHMFieldMoveCallback)(uintptr_t)VEGA_HM_SETUP_SURF_ADDRESS)
#define VEGA_HM_SETUP_ROCK_SMASH ((VegaHMFieldMoveCallback)(uintptr_t)0x080CABA5u)
#ifndef VEGA_HM_SETUP_WATERFALL_ADDRESS
#error "VEGA_HM_SETUP_WATERFALL_ADDRESS must come from the linked T06 contract"
#endif
#define VEGA_HM_SETUP_WATERFALL \
    ((VegaHMFieldMoveCallback)(uintptr_t)VEGA_HM_SETUP_WATERFALL_ADDRESS)
#ifndef VEGA_HM_SETUP_DIVE_ADDRESS
#error "VEGA_HM_SETUP_DIVE_ADDRESS must come from the linked T06 contract"
#endif
#define VEGA_HM_SETUP_DIVE \
    ((VegaHMFieldMoveCallback)(uintptr_t)VEGA_HM_SETUP_DIVE_ADDRESS)

static uint16_t item_for_move(uint16_t move)
{
    switch (move) {
    case VEGA_MOVE_CUT:
        return VEGA_ITEM_HM01_CUT;
    case VEGA_MOVE_FLY:
        return VEGA_ITEM_HM02_FLY;
    case VEGA_MOVE_SURF:
        return VEGA_ITEM_HM03_SURF;
    case VEGA_MOVE_STRENGTH:
        return VEGA_ITEM_HM04_STRENGTH;
    case VEGA_MOVE_FLASH:
        return VEGA_ITEM_HM05_FLASH;
    case VEGA_MOVE_ROCK_SMASH:
        return VEGA_ITEM_HM06_ROCK_SMASH;
    case VEGA_MOVE_WATERFALL:
        return VEGA_ITEM_HM07_WATERFALL;
    case VEGA_MOVE_DIVE:
        return VEGA_ITEM_HM08_DIVE;
    default:
        return 0u;
    }
}

static uint8_t terrain_state_allows(uint8_t surfing_type)
{
    uint8_t is_surfing;

    if (surfing_type == 0u)
        return 1u;
    if (surfing_type != VEGA_HM_SHOULD_NOT_BE_SURFING
        && surfing_type != VEGA_HM_SHOULD_BE_SURFING)
        return 0u;

    is_surfing = VEGA_HM_TEST_PLAYER_AVATAR_FLAGS(
        VEGA_HM_PLAYER_AVATAR_FLAG_SURFING);
    if (surfing_type == VEGA_HM_SHOULD_NOT_BE_SURFING)
        return (uint8_t)(is_surfing == 0u);
    return (uint8_t)(is_surfing != 0u);
}

static uint8_t has_item(uint16_t item)
{
    return (uint8_t)(item != 0u && VEGA_HM_CHECK_BAG_HAS_ITEM(item, 1u) != 0u);
}

static uint8_t set_up_if_owned(
    uint16_t item,
    VegaHMFieldMoveCallback callback
)
{
    if (!has_item(item))
        return 0u;
    return callback();
}

uint8_t VegaHM_FieldCapability(
    uint16_t move,
    uint16_t ignored_item,
    uint8_t surfing_type
)
{
    uint16_t item;
    (void)ignored_item;

    if (!terrain_state_allows(surfing_type))
        return VEGA_HM_PARTY_SIZE;
    item = item_for_move(move);
    if (!has_item(item))
        return VEGA_HM_PARTY_SIZE;

    /*
     * 0は既存field-effect ABIで安全な既定actor。手持ちの存在・習得・適性を
     * 判定に使わず、ポケモン構造体へ技を書き込まない。
     */
    return 0u;
}

uint8_t VegaHM_SetUpFlash(void)
{
    return set_up_if_owned(VEGA_ITEM_HM05_FLASH, VEGA_HM_SETUP_FLASH);
}

uint8_t VegaHM_SetUpCut(void)
{
    return set_up_if_owned(VEGA_ITEM_HM01_CUT, VEGA_HM_SETUP_CUT);
}

uint8_t VegaHM_SetUpFly(void)
{
    return set_up_if_owned(VEGA_ITEM_HM02_FLY, VEGA_HM_SETUP_FLY);
}

uint8_t VegaHM_SetUpStrength(void)
{
    return set_up_if_owned(VEGA_ITEM_HM04_STRENGTH, VEGA_HM_SETUP_STRENGTH);
}

uint8_t VegaHM_SetUpSurf(void)
{
    return set_up_if_owned(VEGA_ITEM_HM03_SURF, VEGA_HM_SETUP_SURF);
}

uint8_t VegaHM_SetUpRockSmash(void)
{
    return set_up_if_owned(VEGA_ITEM_HM06_ROCK_SMASH, VEGA_HM_SETUP_ROCK_SMASH);
}

uint8_t VegaHM_SetUpWaterfall(void)
{
    return set_up_if_owned(VEGA_ITEM_HM07_WATERFALL, VEGA_HM_SETUP_WATERFALL);
}

uint8_t VegaHM_SetUpDive(void)
{
    return set_up_if_owned(VEGA_ITEM_HM08_DIVE, VEGA_HM_SETUP_DIVE);
}
