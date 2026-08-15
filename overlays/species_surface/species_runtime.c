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
    VEGA_SPECIES_NONE = 0,
    VEGA_SPECIES_EGG = 412,
    VEGA_SPECIES_UNOWN = 201,
    VEGA_SPECIES_UNOWN_B = 650,
    VEGA_SPECIES_HIPPOPOTAS = 728,
    VEGA_SPECIES_HIPPOWDON = 729,
    VEGA_SPECIES_UNFEZANT = 778,
    VEGA_SPECIES_FRILLISH = 840,
    VEGA_SPECIES_JELLICENT = 841,
    VEGA_SPECIES_UNFEZANT_FEMALE = 884,
    VEGA_SPECIES_FRILLISH_FEMALE = 885,
    VEGA_SPECIES_JELLICENT_FEMALE = 886,
    VEGA_SPECIES_HIPPOPOTAS_FEMALE = 925,
    VEGA_SPECIES_HIPPOWDON_FEMALE = 926,
    VEGA_SPECIES_PYROAR = 957,
    VEGA_SPECIES_XERNEAS = 1005,
    VEGA_SPECIES_PYROAR_FEMALE = 1012,
    VEGA_SPECIES_XERNEAS_NATURAL = 1282,
    VEGA_MON_FEMALE = 0xFE,
    VEGA_ICON_PALETTE_COUNT = 6,
    VEGA_MAIN_IN_BATTLE_OFFSET = 0x439,
    VEGA_MAIN_IN_BATTLE_MASK = 2,
};

#ifndef VEGA_SPECIES_NAMES_ADDRESS
#error "canonical Species name address must be supplied by the T09 linker"
#endif

#ifndef VEGA_LEVEL_UP_LEARNSETS_ADDRESS
#error "canonical level-up learnset address must be supplied by the T09 linker"
#endif

#ifndef VEGA_FRONT_SPRITES_ADDRESS
#error "canonical front-sprite table address must be supplied by the T09 linker"
#endif

#ifndef VEGA_BACK_SPRITES_ADDRESS
#error "canonical back-sprite table address must be supplied by the T09 linker"
#endif

#ifndef VEGA_NORMAL_PALETTES_ADDRESS
#error "canonical normal-palette table address must be supplied by the T09 linker"
#endif

#ifndef VEGA_SHINY_PALETTES_ADDRESS
#error "canonical shiny-palette table address must be supplied by the T09 linker"
#endif

#ifndef VEGA_ICON_PALETTE_INDICES_ADDRESS
#error "canonical icon-palette index table address must be supplied by the T09 linker"
#endif

#ifndef VEGA_NATIONAL_DEX_ADDRESS
#error "canonical National Dex table address must be supplied by the T09 linker"
#endif

#define VEGA_SPECIES_NAMES \
    ((const uint8_t *)(uintptr_t)(VEGA_SPECIES_NAMES_ADDRESS))
#define VEGA_LEVEL_UP_LEARNSETS \
    ((const uint8_t *const *)(uintptr_t)(VEGA_LEVEL_UP_LEARNSETS_ADDRESS))

struct VegaSpritePalette {
    const uint16_t *data;
    uint16_t tag;
    uint16_t padding;
};

#define VEGA_ICON_PALETTE_INDICES \
    ((const uint8_t *)(uintptr_t)(VEGA_ICON_PALETTE_INDICES_ADDRESS))
#define VEGA_NATIONAL_DEX \
    ((const uint16_t *)(uintptr_t)(VEGA_NATIONAL_DEX_ADDRESS))
#define VEGA_ICON_PALETTES \
    ((const struct VegaSpritePalette *)(uintptr_t)0x0839C540u)
#define VEGA_MAIN \
    ((const volatile uint8_t *)(uintptr_t)0x03003130u)

typedef uint16_t (*GiveMoveToBoxMonFn)(void *, uint16_t);
typedef void (*DeleteFirstMoveAndGiveMoveToBoxMonFn)(void *, uint16_t);
typedef uint8_t (*GetGenderFromSpeciesAndPersonalityFn)(uint16_t, uint32_t);
typedef uint8_t (*IndexOfSpritePaletteTagFn)(uint16_t);
typedef void (*LoadSpritePaletteFn)(const struct VegaSpritePalette *);
typedef void (*FreeSpritePaletteByTagFn)(uint16_t);

#define FN_GIVE_MOVE_TO_BOX_MON \
    ((GiveMoveToBoxMonFn)(uintptr_t)0x0803E01Du)
#define FN_DELETE_FIRST_MOVE_AND_GIVE_MOVE_TO_BOX_MON \
    ((DeleteFirstMoveAndGiveMoveToBoxMonFn)(uintptr_t)0x0803E3ADu)
#define FN_GET_GENDER_FROM_SPECIES_AND_PERSONALITY \
    ((GetGenderFromSpeciesAndPersonalityFn)(uintptr_t)0x0803EEF9u)
#define FN_INDEX_OF_SPRITE_PALETTE_TAG \
    ((IndexOfSpritePaletteTagFn)(uintptr_t)0x08008565u)
#define FN_LOAD_SPRITE_PALETTE \
    ((LoadSpritePaletteFn)(uintptr_t)0x080084A5u)
#define FN_FREE_SPRITE_PALETTE_BY_TAG \
    ((FreeSpritePaletteByTagFn)(uintptr_t)0x080085ADu)

enum {
    VEGA_LEVEL_UP_ROW_SIZE = 3,
    VEGA_LEVEL_UP_SCAN_LIMIT = 256,
};

static uint16_t VegaSpeciesSurface_GetUnownLetter(uint32_t personality)
{
    uint16_t letter = (uint16_t)(((personality & 0x03000000u) >> 18)
                               | ((personality & 0x00030000u) >> 12)
                               | ((personality & 0x00000300u) >> 6)
                               | (personality & 3u));

    /* Avoid a libgcc division helper in the freestanding ROM overlay. */
    while (letter >= 28u) {
        letter -= 28u;
    }
    return letter;
}

static uint16_t VegaSpeciesSurface_ResolveDisplaySpecies(
    uint16_t species, uint32_t personality)
{
    uint16_t letter;

    if (species >= VEGA_SPECIES_COUNT) {
        return VEGA_SPECIES_NONE;
    }
    if (species == VEGA_SPECIES_EGG) {
        return VEGA_SPECIES_EGG;
    }
    if (species == VEGA_SPECIES_UNOWN) {
        letter = VegaSpeciesSurface_GetUnownLetter(personality);
        return letter == 0
            ? VEGA_SPECIES_UNOWN
            : (uint16_t)(VEGA_SPECIES_UNOWN_B + letter - 1u);
    }
    if (FN_GET_GENDER_FROM_SPECIES_AND_PERSONALITY(species, personality)
            == VEGA_MON_FEMALE) {
        switch (species) {
        case VEGA_SPECIES_HIPPOPOTAS:
            return VEGA_SPECIES_HIPPOPOTAS_FEMALE;
        case VEGA_SPECIES_HIPPOWDON:
            return VEGA_SPECIES_HIPPOWDON_FEMALE;
        case VEGA_SPECIES_UNFEZANT:
            return VEGA_SPECIES_UNFEZANT_FEMALE;
        case VEGA_SPECIES_FRILLISH:
            return VEGA_SPECIES_FRILLISH_FEMALE;
        case VEGA_SPECIES_JELLICENT:
            return VEGA_SPECIES_JELLICENT_FEMALE;
        case VEGA_SPECIES_PYROAR:
            return VEGA_SPECIES_PYROAR_FEMALE;
        default:
            break;
        }
    }
    if (species == VEGA_SPECIES_XERNEAS
            && (VEGA_MAIN[VEGA_MAIN_IN_BATTLE_OFFSET]
                & VEGA_MAIN_IN_BATTLE_MASK) == 0) {
        return VEGA_SPECIES_XERNEAS_NATURAL;
    }
    return species;
}

__attribute__((section(".text.VegaSpeciesSurface_GetIconSpecies"), used, noinline))
uint16_t VegaSpeciesSurface_GetIconSpecies(
    uint16_t species, uint32_t personality)
{
    return VegaSpeciesSurface_ResolveDisplaySpecies(species, personality);
}

static uint8_t VegaSpeciesSurface_BoundedIconPaletteIndex(uint16_t species)
{
    uint8_t index;

    if (species >= VEGA_SPECIES_COUNT) {
        species = VEGA_SPECIES_NONE;
    }
    index = VEGA_ICON_PALETTE_INDICES[species];
    return index < VEGA_ICON_PALETTE_COUNT ? index : 0;
}

__attribute__((section(".text.VegaSpeciesSurface_SafeLoadMonIconPalette"),
               used, noinline))
void VegaSpeciesSurface_SafeLoadMonIconPalette(uint16_t species)
{
    const struct VegaSpritePalette *palette =
        &VEGA_ICON_PALETTES[VegaSpeciesSurface_BoundedIconPaletteIndex(species)];

    if (FN_INDEX_OF_SPRITE_PALETTE_TAG(palette->tag) == 0xFFu) {
        FN_LOAD_SPRITE_PALETTE(palette);
    }
}

__attribute__((section(".text.VegaSpeciesSurface_SafeFreeMonIconPalette"),
               used, noinline))
void VegaSpeciesSurface_SafeFreeMonIconPalette(uint16_t species)
{
    const struct VegaSpritePalette *palette =
        &VEGA_ICON_PALETTES[VegaSpeciesSurface_BoundedIconPaletteIndex(species)];
    FN_FREE_SPRITE_PALETTE_BY_TAG(palette->tag);
}

__attribute__((section(".text.VegaSpeciesSurface_GetValidMonIconPalettePtr"),
               used, noinline))
const uint16_t *VegaSpeciesSurface_GetValidMonIconPalettePtr(uint16_t species)
{
    return VEGA_ICON_PALETTES[
        VegaSpeciesSurface_BoundedIconPaletteIndex(species)].data;
}

__attribute__((section(".text.VegaSpeciesSurface_GetValidMonIconPalIndex"),
               used, noinline))
uint8_t VegaSpeciesSurface_GetValidMonIconPalIndex(uint16_t species)
{
    return VegaSpeciesSurface_BoundedIconPaletteIndex(species);
}

__attribute__((section(".text.VegaSpeciesSurface_NationalPokedexNumToSpecies"),
               used, noinline))
uint16_t VegaSpeciesSurface_NationalPokedexNumToSpecies(uint16_t national_dex)
{
    uint16_t species;

    if (national_dex == 0u) {
        return VEGA_SPECIES_NONE;
    }
    for (species = VEGA_SPECIES_EGG + 1u;
         species < VEGA_SPECIES_COUNT; ++species) {
        if (VEGA_NATIONAL_DEX[species] == national_dex) {
            return species;
        }
    }
    return VEGA_SPECIES_NONE;
}

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
