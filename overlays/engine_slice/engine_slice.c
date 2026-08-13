#include "engine_slice.h"

#include <string.h>

#ifndef VEGA_ENGINE_SLICE_DEBUG
#define VEGA_ENGINE_SLICE_DEBUG 0
#endif

bool VegaSliceDebugGift(struct VegaSliceGift *gift)
{
#if VEGA_ENGINE_SLICE_DEBUG
    if (gift == NULL)
        return false;
    gift->species = 445;   /* Primeape, appended canonical Species */
    gift->move = 1027;     /* Rage Fist */
    gift->ability = 129;   /* Defiant */
    gift->held_item = 669; /* DPE-appended held item */
    gift->level = 35;
    return true;
#else
    (void)gift;
    return false;
#endif
}

bool VegaSliceMoveCourse(uint16_t tiles, uint16_t frames_per_tile,
                         const uint8_t *events, size_t event_count,
                         struct VegaSliceMovementResult *out)
{
    size_t i;
    if (tiles == 0 || frames_per_tile == 0 || out == NULL ||
        (event_count != 0 && events == NULL))
        return false;
    memset(out, 0, sizeof(*out));
    out->tiles = tiles;
    out->frames = (uint32_t)tiles * frames_per_tile;
    out->event_count[VEGA_SLICE_STEP] = tiles;
    for (i = 0; i < event_count; ++i) {
        if (events[i] >= VEGA_SLICE_EVENT_KINDS)
            return false;
        ++out->event_count[events[i]];
    }
    return true;
}

bool VegaSliceRenderText(const uint8_t *tokens, size_t count, bool instant,
                         struct VegaSliceTextResult *out)
{
    size_t i;
    if (tokens == NULL || out == NULL)
        return false;
    memset(out, 0, sizeof(*out));
    for (i = 0; i < count; ++i) {
        if (tokens[i] > VEGA_TEXT_SOUND)
            return false;
        ++out->token_count[tokens[i]];
        if (tokens[i] == VEGA_TEXT_GLYPH) {
            ++out->glyph_count;
            out->delayed_glyph_count += (uint16_t)!instant;
        }
    }
    return true;
}

uint16_t VegaSliceResolveQuantity(uint16_t available, uint8_t choice)
{
    static const uint16_t amounts[] = {1, 5, 10};
    uint16_t requested;
    if (available == 0 || choice > 3)
        return 0;
    requested = choice == 3 ? available : amounts[choice];
    return requested < available ? requested : available;
}

bool VegaSliceUseTm(uint16_t *quantity, bool reuse_license)
{
    if (quantity == NULL || *quantity == 0)
        return false;
    if (!reuse_license)
        --*quantity;
    return true;
}

struct VegaSliceEncounter VegaSliceSelectOverlay(struct VegaSliceEncounter original,
                                                  struct VegaSliceEncounter overlay,
                                                  bool enabled, bool resolved,
                                                  bool original_is_rare_one_percent)
{
    if (!enabled || !resolved || original_is_rare_one_percent)
        return original;
    return overlay;
}

struct VegaSliceEncounter VegaSliceApplyResearch(struct VegaSliceEncounter base,
                                                 enum VegaSliceEncounterProfile profile,
                                                 uint8_t level_delta, uint8_t iv_floor,
                                                 uint8_t ability_slot, uint16_t egg_move,
                                                 uint16_t held_item, uint8_t shiny_policy)
{
    uint16_t level;
    if (profile != VEGA_SLICE_RESEARCH)
        return base;
    level = (uint16_t)base.level + level_delta;
    base.level = (uint8_t)(level > 100 ? 100 : level);
    base.iv_floor = iv_floor > 31 ? 31 : iv_floor;
    base.ability_slot = ability_slot > 2 ? 2 : ability_slot;
    base.egg_move = egg_move;
    base.held_item = held_item;
    base.shiny_policy = shiny_policy;
    return base;
}

bool VegaSliceSelectRentals(const uint16_t candidates[VEGA_SLICE_RENTAL_CANDIDATES],
                            const uint8_t selections[VEGA_SLICE_RENTAL_PARTY],
                            uint16_t party[VEGA_SLICE_RENTAL_PARTY])
{
    uint8_t i, j;
    if (candidates == NULL || selections == NULL || party == NULL)
        return false;
    for (i = 0; i < VEGA_SLICE_RENTAL_PARTY; ++i) {
        if (selections[i] >= VEGA_SLICE_RENTAL_CANDIDATES)
            return false;
        for (j = 0; j < i; ++j)
            if (selections[i] == selections[j])
                return false;
        party[i] = candidates[selections[i]];
    }
    return true;
}

bool VegaSliceExchangeRental(uint16_t party[VEGA_SLICE_RENTAL_PARTY], uint8_t party_slot,
                             uint16_t defeated_species)
{
    if (party == NULL || party_slot >= VEGA_SLICE_RENTAL_PARTY || defeated_species == 0)
        return false;
    party[party_slot] = defeated_species;
    return true;
}
