#ifndef VEGA_ENGINE_SLICE_H
#define VEGA_ENGINE_SLICE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define VEGA_SLICE_RENTAL_CANDIDATES 6u
#define VEGA_SLICE_RENTAL_PARTY 3u
#define VEGA_SLICE_EVENT_KINDS 8u

enum VegaSliceEventKind {
    VEGA_SLICE_STEP,
    VEGA_SLICE_ENCOUNTER,
    VEGA_SLICE_HATCH,
    VEGA_SLICE_POISON,
    VEGA_SLICE_CONTACT,
    VEGA_SLICE_COORD,
    VEGA_SLICE_WARP,
    VEGA_SLICE_LEDGE
};

enum VegaSliceTextTokenKind {
    VEGA_TEXT_GLYPH,
    VEGA_TEXT_VARIABLE,
    VEGA_TEXT_COLOR,
    VEGA_TEXT_NEWLINE,
    VEGA_TEXT_PAGE,
    VEGA_TEXT_CHOICE,
    VEGA_TEXT_WAIT,
    VEGA_TEXT_SOUND
};

enum VegaSliceEncounterProfile { VEGA_SLICE_NORMAL, VEGA_SLICE_RESEARCH };

struct VegaSliceEncounter {
    uint16_t species;
    uint16_t held_item;
    uint16_t egg_move;
    uint8_t level;
    uint8_t iv_floor;
    uint8_t ability_slot;
    uint8_t shiny_policy;
    uint8_t rate_percent;
};

struct VegaSliceMovementResult {
    uint32_t frames;
    uint16_t tiles;
    uint16_t event_count[VEGA_SLICE_EVENT_KINDS];
};

struct VegaSliceTextResult {
    uint16_t glyph_count;
    uint16_t delayed_glyph_count;
    uint16_t token_count[8];
};

struct VegaSliceGift {
    uint16_t species;
    uint16_t move;
    uint16_t ability;
    uint16_t held_item;
    uint8_t level;
};

bool VegaSliceDebugGift(struct VegaSliceGift *gift);
bool VegaSliceMoveCourse(uint16_t tiles, uint16_t frames_per_tile,
                         const uint8_t *events, size_t event_count,
                         struct VegaSliceMovementResult *out);
bool VegaSliceRenderText(const uint8_t *tokens, size_t count, bool instant,
                         struct VegaSliceTextResult *out);
uint16_t VegaSliceResolveQuantity(uint16_t available, uint8_t choice);
bool VegaSliceUseTm(uint16_t *quantity, bool reuse_license);
struct VegaSliceEncounter VegaSliceSelectOverlay(struct VegaSliceEncounter original,
                                                  struct VegaSliceEncounter overlay,
                                                  bool enabled, bool resolved,
                                                  bool original_is_rare_one_percent);
struct VegaSliceEncounter VegaSliceApplyResearch(struct VegaSliceEncounter base,
                                                 enum VegaSliceEncounterProfile profile,
                                                 uint8_t level_delta, uint8_t iv_floor,
                                                 uint8_t ability_slot, uint16_t egg_move,
                                                 uint16_t held_item, uint8_t shiny_policy);
bool VegaSliceSelectRentals(const uint16_t candidates[VEGA_SLICE_RENTAL_CANDIDATES],
                            const uint8_t selections[VEGA_SLICE_RENTAL_PARTY],
                            uint16_t party[VEGA_SLICE_RENTAL_PARTY]);
bool VegaSliceExchangeRental(uint16_t party[VEGA_SLICE_RENTAL_PARTY], uint8_t party_slot,
                             uint16_t defeated_species);

#endif
