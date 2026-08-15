/*
 * T09 canonical Species name adapter.
 *
 * FireRed/Vega's stock table has a six-byte row and rejects IDs above 412.
 * The canonical project table has 1,621 eleven-byte rows.  Keep the public
 * GetSpeciesName ABI while reading the canonical table with a strict bound.
 */

#include "species_runtime.h"

#include <stdint.h>

enum {
    VEGA_SPECIES_COUNT = 1621,
    VEGA_SPECIES_NAME_LENGTH = 11,
    VEGA_TEXT_TERMINATOR = 0xFF,
};

#ifndef VEGA_SPECIES_NAMES_ADDRESS
#error "canonical Species name address must be supplied by the T09 linker"
#endif

#ifndef VEGA_LEVEL_UP_LEARNSETS_ADDRESS
#error "canonical level-up learnset address must be supplied by the T09 linker"
#endif

#define VEGA_SPECIES_NAMES \
    ((const uint8_t *)(uintptr_t)(VEGA_SPECIES_NAMES_ADDRESS))
#define VEGA_LEVEL_UP_LEARNSETS \
    ((const uint8_t *const *)(uintptr_t)(VEGA_LEVEL_UP_LEARNSETS_ADDRESS))

typedef uint16_t (*GiveMoveToBoxMonFn)(void *, uint16_t);
typedef void (*DeleteFirstMoveAndGiveMoveToBoxMonFn)(void *, uint16_t);

#define FN_GIVE_MOVE_TO_BOX_MON \
    ((GiveMoveToBoxMonFn)(uintptr_t)0x0803E01Du)
#define FN_DELETE_FIRST_MOVE_AND_GIVE_MOVE_TO_BOX_MON \
    ((DeleteFirstMoveAndGiveMoveToBoxMonFn)(uintptr_t)0x0803E3ADu)

enum {
    VEGA_LEVEL_UP_ROW_SIZE = 3,
    VEGA_LEVEL_UP_SCAN_LIMIT = 256,
};

__attribute__((section(".text.VegaSpeciesSurface_GetSpeciesName"), used, noinline))
void VegaSpeciesSurface_GetSpeciesName(uint8_t *destination, uint16_t species)
{
    const uint8_t *source;
    uint8_t index;

    if (species >= VEGA_SPECIES_COUNT) {
        species = 0;
    }
    source = VEGA_SPECIES_NAMES + (uint32_t)species * VEGA_SPECIES_NAME_LENGTH;
    for (index = 0; index < VEGA_SPECIES_NAME_LENGTH; ++index) {
        uint8_t value = source[index];
        destination[index] = value;
        if (value == VEGA_TEXT_TERMINATOR) {
            return;
        }
    }
    destination[VEGA_SPECIES_NAME_LENGTH - 1] = VEGA_TEXT_TERMINATOR;
}

/*
 * Keep Vega's native GiveMoveToBoxMon semantics while adapting only the
 * level-up row decoder.  Redirecting the whole CFRU helper changed unrelated
 * stock battle setup state (notably Raid controller timing), even though the
 * resulting four move IDs happened to match.  Calling the native add/rotate
 * helpers for every eligible row preserves Vega's exact side effects and
 * "last four moves available at this level" behavior.
 */
__attribute__((section(".text.VegaSpeciesSurface_GiveBoxMonInitialMovesetAppended"),
               used, noinline))
void VegaSpeciesSurface_GiveBoxMonInitialMovesetAppended(
    void *box_mon, uint16_t species, uint8_t level)
{
    uint16_t row;
    const uint8_t *learnset;

    if (species >= VEGA_SPECIES_COUNT) {
        return;
    }
    learnset = VEGA_LEVEL_UP_LEARNSETS[species];

    for (row = 0; row < VEGA_LEVEL_UP_SCAN_LIMIT; ++row) {
        const uint8_t *entry = learnset + (uint32_t)row * VEGA_LEVEL_UP_ROW_SIZE;
        uint16_t move = (uint16_t)(entry[0] | ((uint16_t)entry[1] << 8));
        uint8_t learned_at = entry[2];

        if (move == 0 && learned_at == 0xFF) {
            break;
        }
        if (learned_at > level) {
            break;
        }
        if (FN_GIVE_MOVE_TO_BOX_MON(box_mon, move) == 0xFFFF) {
            FN_DELETE_FIRST_MOVE_AND_GIVE_MOVE_TO_BOX_MON(box_mon, move);
        }
    }
}
