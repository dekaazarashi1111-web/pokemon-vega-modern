/* T17: preserve Vega encounter tables and add the authored Tohoku overlay. */

#include "wild_overlay.h"

#include <stdint.h>

enum {
    WILD_AREA_LAND = 0,
    WILD_AREA_WATER = 1,
    WILD_AREA_ROCKS = 2,
    WILD_CHECK_REPEL = 1,
    OVERLAY_ENTRY_SIZE = 32,
    OVERLAY_SPECIES_OFFSET = 6,
};

struct WildPokemon {
    uint8_t minimum_level;
    uint8_t maximum_level;
    uint16_t species;
};

struct WildPokemonInfo {
    uint8_t encounter_rate;
    uint8_t padding[3];
    const struct WildPokemon *wild_pokemon;
};

typedef uint8_t (*ChooseIndexFn)(void);
typedef uint8_t (*ChooseLevelFn)(const struct WildPokemon *wild_pokemon);
typedef uint8_t (*LevelAllowedFn)(uint8_t level);
typedef void (*GenerateWildMonFn)(uint16_t species, uint8_t level, uint8_t slot);
typedef uint16_t (*RandomFn)(void);

#ifndef VEGA_WILD_OVERLAY_TABLE_ADDRESS
#error "wild overlay table address is required"
#endif
#ifndef VEGA_WILD_OVERLAY_TABLE_COUNT
#error "wild overlay table count is required"
#endif

#define PTR(type, address) ((type)(uintptr_t)(address))
#define OVERLAY_TABLE PTR(const uint8_t *, VEGA_WILD_OVERLAY_TABLE_ADDRESS)
#define SAVE_BLOCK1_PTR PTR(uint8_t *volatile *, 0x03005048)
#define FN_CHOOSE_LAND PTR(ChooseIndexFn, 0x08082339)
#define FN_CHOOSE_WATER_ROCK PTR(ChooseIndexFn, 0x080823F5)
#define FN_CHOOSE_LEVEL PTR(ChooseLevelFn, 0x080824E5)
#define FN_LEVEL_ALLOWED PTR(LevelAllowedFn, 0x08082CF9)
#define FN_GENERATE_WILD PTR(GenerateWildMonFn, 0x080825E9)
#define FN_RANDOM PTR(RandomFn, 0x0804448D)

#define PUBLIC_TEXT(name) \
    __attribute__((section(".text." #name), used, noinline))

static uint16_t read_u16(const uint8_t *source)
{
    return (uint16_t)(source[0] | (uint16_t)source[1] << 8);
}

PUBLIC_TEXT(VegaWildOverlay_SelectSpecies)
uint16_t VegaWildOverlay_SelectSpecies(uint16_t original_species, uint8_t area)
{
    const uint8_t *save = *SAVE_BLOCK1_PTR;
    uint8_t map_group;
    uint8_t map_number;
    uint16_t entry_index;

    if (save == 0) {
        return original_species;
    }
    map_group = save[4];
    map_number = save[5];
    for (entry_index = 0; entry_index < VEGA_WILD_OVERLAY_TABLE_COUNT;
         ++entry_index) {
        const uint8_t *entry = OVERLAY_TABLE +
            (uint32_t)entry_index * OVERLAY_ENTRY_SIZE;
        uint8_t count;
        uint16_t random;
        uint8_t candidate;

        if (entry[0] != map_group || entry[1] != map_number || entry[2] != area) {
            continue;
        }
        count = entry[4];
        if (count == 0 || count > 12) {
            return original_species;
        }
        random = FN_RANDOM();
        if ((uint8_t)random >= entry[3]) {
            return original_species;
        }
        candidate = (uint8_t)(((uint32_t)(random >> 8) * count) >> 8);
        return read_u16(entry + OVERLAY_SPECIES_OFFSET + candidate * 2u);
    }
    return original_species;
}

PUBLIC_TEXT(VegaWildOverlay_TryGenerateWildMon)
uint8_t VegaWildOverlay_TryGenerateWildMon(const void *raw_info, uint8_t area,
                                           uint8_t flags)
{
    const struct WildPokemonInfo *info = raw_info;
    uint8_t slot;
    uint8_t level;
    uint16_t species;

    if (info == 0 || info->wild_pokemon == 0) {
        return 0;
    }
    if (area == WILD_AREA_LAND) {
        slot = FN_CHOOSE_LAND();
    } else if (area == WILD_AREA_WATER || area == WILD_AREA_ROCKS) {
        slot = FN_CHOOSE_WATER_ROCK();
    } else {
        return 0;
    }
    level = FN_CHOOSE_LEVEL(&info->wild_pokemon[slot]);
    if (flags == WILD_CHECK_REPEL && !FN_LEVEL_ALLOWED(level)) {
        return 0;
    }
    species = VegaWildOverlay_SelectSpecies(info->wild_pokemon[slot].species, area);
    FN_GENERATE_WILD(species, level, slot);
    return 1;
}
