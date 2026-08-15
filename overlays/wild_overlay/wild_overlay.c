/*
 * T17 Tohoku ecology runtime.
 *
 * Vega's native encounter slots remain authoritative.  This adapter performs
 * an authored, map-specific extra roll before the generated Pokemon is built.
 * Special layers are selected by RTC or by the persistent ecology-radar mode.
 */

#include "wild_overlay.h"

#include <stddef.h>
#include <stdint.h>

enum {
    WILD_AREA_LAND = 0,
    WILD_AREA_WATER = 1,
    WILD_AREA_ROCKS = 2,
    WILD_AREA_FISHING = 3,
    WILD_AREA_HIDDEN = 4,

    ECOLOGY_LAYER_NORMAL = 0,
    ECOLOGY_LAYER_DAY = 1,
    ECOLOGY_LAYER_NIGHT = 2,
    ECOLOGY_LAYER_SWARM = 3,
    ECOLOGY_LAYER_FISHING = 4,
    ECOLOGY_LAYER_HIDDEN = 5,

    WILD_CHECK_REPEL = 1,
    OVERLAY_ENTRY_SIZE = 104,
    OVERLAY_SPECIES_OFFSET = 8,
    OVERLAY_PRE_MIN_OFFSET = 32,
    OVERLAY_PRE_MAX_OFFSET = 44,
    OVERLAY_POST_MIN_OFFSET = 56,
    OVERLAY_POST_MAX_OFFSET = 68,
    OVERLAY_MIN_BADGES_OFFSET = 80,
    OVERLAY_MIN_ROD_OFFSET = 92,
    OVERLAY_MAX_CANDIDATES = 12,

    ECOLOGY_MODE_VAR = 0x51FF,
    ECOLOGY_RADAR_ITEM = 348,
    BADGE_RULE_RADAR_OVERRIDE = 0x80,
    FLAG_HALL_OF_FAME = 0x082C,
    FIRST_BADGE_FLAG = 0x0820,

    PARTY_TASK_COUNT = 16,
    MENU_COUNT = 6,
    MENU_CANCEL = 5,
    MENU_NOTHING_CHOSEN = -2,
    MENU_B_PRESSED = -1,
    MENU_WINDOW_INVALID = 0xFF,
    COPYWIN_BOTH = 3,
    SE_SELECT = 5,
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

struct Clock {
    uint16_t year;
    uint8_t unused;
    uint8_t month;
    uint8_t day;
    uint8_t day_of_week;
    uint8_t hour;
    uint8_t minute;
    uint8_t second;
};

struct Task {
    void (*func)(uint8_t task_id);
    uint8_t is_active;
    uint8_t prev;
    uint8_t next;
    uint8_t priority;
    int16_t data[16];
};

struct WindowTemplate {
    uint8_t bg;
    uint8_t tilemap_left;
    uint8_t tilemap_top;
    uint8_t width;
    uint8_t height;
    uint8_t palette_num;
    uint16_t base_block;
};

struct EcologySelection {
    uint16_t species;
    uint8_t level;
    uint8_t hit;
};

_Static_assert(sizeof(struct Task) == 40, "FireRed Task ABI changed");
_Static_assert(offsetof(struct Task, data) == 8, "FireRed Task data ABI changed");
_Static_assert(sizeof(struct WindowTemplate) == 8, "FireRed WindowTemplate ABI changed");

typedef uint8_t (*ChooseIndexFn)(void);
typedef uint8_t (*ChooseFishingIndexFn)(uint8_t rod);
typedef uint8_t (*ChooseLevelFn)(const struct WildPokemon *wild_pokemon);
typedef uint8_t (*LevelAllowedFn)(uint8_t level);
typedef void (*GenerateWildMonFn)(uint16_t species, uint8_t level, uint8_t slot);
typedef uint16_t (*RandomFn)(void);
typedef uint8_t (*FlagGetFn)(uint16_t flag);
typedef uint8_t (*CheckBagHasItemFn)(uint16_t item, uint16_t quantity);
typedef uint16_t (*VarGetFn)(uint16_t variable);
typedef uint8_t (*VarSetFn)(uint16_t variable, uint16_t value);
typedef void (*VoidFn)(void);
typedef void (*TaskIdFn)(uint8_t task_id);
typedef void (*TaskFunc)(uint8_t task_id);
typedef uint8_t (*CreateTaskFn)(TaskFunc func, uint8_t priority);
typedef uint16_t (*AddWindowFn)(const struct WindowTemplate *template);
typedef void (*WindowU8Fn)(uint8_t window_id);
typedef void (*WindowPairFn)(uint8_t window_id, uint8_t value);
typedef void (*TextPrinterFn)(uint8_t window_id, uint8_t font_id,
                              const uint8_t *text, uint8_t x, uint8_t y,
                              uint8_t speed, void *callback);
typedef uint8_t (*MenuInitCursorFn)(uint8_t window_id, uint8_t font_id,
                                    uint8_t left, uint8_t top,
                                    uint8_t cursor_height, uint8_t count,
                                    uint8_t cursor);
typedef int8_t (*MenuInputFn)(void);
typedef uint16_t (*GetBaseTileFn)(void);
typedef void (*PlaySeFn)(uint16_t song);

#ifndef VEGA_WILD_OVERLAY_TABLE_ADDRESS
#error "wild overlay table address is required"
#endif
#ifndef VEGA_WILD_OVERLAY_TABLE_COUNT
#error "wild overlay table count is required"
#endif
#ifndef VEGA_WILD_SWARM_ENTRY_COUNT
#error "wild overlay swarm entry count is required"
#endif
#ifndef VEGA_DIRECT_CLOCK_UPDATE_ADDRESS
#error "fixed CFRU DirectClockUpdate address is required"
#endif

#define PTR(type, address) ((type)(uintptr_t)(address))
#define OVERLAY_TABLE PTR(const uint8_t *, VEGA_WILD_OVERLAY_TABLE_ADDRESS)
#define SAVE_BLOCK1_PTR PTR(uint8_t *volatile *, 0x03005048)
#define G_CLOCK PTR(volatile struct Clock *, 0x03005EF0)
#define G_TASKS PTR(struct Task *, 0x030050D0)
#define S_ITEM_USE_ON_FIELD_CB PTR(volatile TaskFunc *, 0x02039910)

#define FN_CHOOSE_LAND PTR(ChooseIndexFn, 0x08082339)
#define FN_CHOOSE_WATER_ROCK PTR(ChooseIndexFn, 0x080823F5)
#define FN_CHOOSE_FISHING PTR(ChooseFishingIndexFn, 0x08082449)
#define FN_CHOOSE_LEVEL PTR(ChooseLevelFn, 0x080824E5)
#define FN_LEVEL_ALLOWED PTR(LevelAllowedFn, 0x08082CF9)
#define FN_GENERATE_WILD PTR(GenerateWildMonFn, 0x080825E9)
#define FN_RANDOM PTR(RandomFn, 0x0804448D)
#define FN_FLAG_GET PTR(FlagGetFn, 0x0806DEC5)
#define FN_CHECK_BAG_HAS_ITEM PTR(CheckBagHasItemFn, 0x08099949)
#define FN_VAR_GET PTR(VarGetFn, 0x0806DD5D)
#define FN_VAR_SET PTR(VarSetFn, 0x0806DD79)
#define FN_DIRECT_CLOCK_UPDATE PTR(VoidFn, VEGA_DIRECT_CLOCK_UPDATE_ADDRESS)
#define FN_START_WILD_BATTLE PTR(VoidFn, 0x0807EE2D)
#define FN_ENABLE_BOTH_SCRIPT_CONTEXTS PTR(VoidFn, 0x080693F5)
#define FN_SCRIPT_CONTEXT2_ENABLE PTR(VoidFn, 0x08069201)
#define FN_SETUP_ITEM_USE_ON_FIELD PTR(TaskIdFn, 0x080A2311)
#define FN_CREATE_TASK PTR(CreateTaskFn, 0x08076BB5)
#define FN_DESTROY_TASK PTR(TaskIdFn, 0x08076CA1)
#define FN_ADD_WINDOW PTR(AddWindowFn, 0x08003CB1)
#define FN_REMOVE_WINDOW PTR(WindowU8Fn, 0x08003E09)
#define FN_COPY_WINDOW_TO_VRAM PTR(WindowPairFn, 0x08003EED)
#define FN_PUT_WINDOW_TILEMAP PTR(WindowU8Fn, 0x08003F6D)
#define FN_FILL_WINDOW_PIXEL_BUFFER PTR(WindowPairFn, 0x08004429)
#define FN_ADD_TEXT_PRINTER PTR(TextPrinterFn, 0x08002C45)
#define FN_SCHEDULE_BG_COPY PTR(WindowU8Fn, 0x080F77FD)
#define FN_DRAW_STD_WINDOW_FRAME PTR(WindowPairFn, 0x080F7F7D)
#define FN_CLEAR_STD_WINDOW_FRAME PTR(WindowPairFn, 0x080F7FFD)
#define FN_GET_STD_WINDOW_BASE_TILE PTR(GetBaseTileFn, 0x080F89CD)
#define FN_MENU_INIT_CURSOR PTR(MenuInitCursorFn, 0x0811030D)
#define FN_MENU_PROCESS_INPUT PTR(MenuInputFn, 0x08110BF9)
#define FN_PLAY_SE PTR(PlaySeFn, 0x08071A71)

#define PUBLIC_TEXT(name) \
    __attribute__((section(".text." #name), used, noinline))

/* CFRU-JP Japanese game encoding. */
static const uint8_t sTextMode[] = {0x73, 0xAE, 0x95, 0xFF};
static const uint8_t sTextAuto[] = {0x3D, 0x45, 0x03, 0xFF};
static const uint8_t sTextAutoDay[] = {
    0x3D, 0x45, 0x03, 0x00, 0x01, 0x0B, 0xAF, 0x1B, 0x29, 0xFF,
};
static const uint8_t sTextAutoNight[] = {
    0x3D, 0x45, 0x03, 0x00, 0x26, 0x29, 0xFF,
};
static const uint8_t sTextDay[] = {0x01, 0x0B, 0xAF, 0x1B, 0x29, 0xFF};
static const uint8_t sTextNight[] = {0x26, 0x29, 0xFF};
static const uint8_t sTextSwarm[] = {
    0x10, 0x02, 0x28, 0x36, 0x03, 0x1A, 0x50, 0x0E, 0x02, 0xFF,
};
static const uint8_t sTextHidden[] = {
    0x06, 0x08, 0x0C, 0x5D, 0x57, 0x84, 0x7E, 0xFF,
};
static const uint8_t sTextCancel[] = {0x24, 0x22, 0x29, 0xFF};
static const uint8_t *const sModeTexts[MENU_COUNT] = {
    sTextAuto, sTextDay, sTextNight, sTextSwarm, sTextHidden, sTextCancel,
};

static uint16_t read_u16(const uint8_t *source)
{
    return (uint16_t)(source[0] | (uint16_t)source[1] << 8);
}

static uint16_t bounded_mod_u32(uint32_t value, uint16_t divisor)
{
    uint32_t remainder = 0;
    uint8_t bit;
    if (divisor == 0) {
        return 0;
    }
    for (bit = 0; bit < 32; ++bit) {
        remainder = (remainder << 1) | (value >> 31);
        value <<= 1;
        if (remainder >= divisor) {
            remainder -= divisor;
        }
    }
    return (uint16_t)remainder;
}

static uint8_t badge_count(void)
{
    uint8_t count = 0;
    uint16_t flag;
    for (flag = FIRST_BADGE_FLAG; flag < FIRST_BADGE_FLAG + 8; ++flag) {
        if (FN_FLAG_GET(flag)) {
            ++count;
        }
    }
    return count;
}

static uint8_t normalized_mode(void)
{
    uint16_t value = FN_VAR_GET(ECOLOGY_MODE_VAR);
    if (value > VEGA_ECOLOGY_MODE_HIDDEN) {
        return VEGA_ECOLOGY_MODE_AUTO;
    }
    return (uint8_t)value;
}

static void update_clock(void)
{
    FN_DIRECT_CLOCK_UPDATE();
}

static uint8_t is_night(void)
{
    uint8_t hour;
    update_clock();
    hour = G_CLOCK->hour;
    return hour >= 18 || hour < 6;
}

static uint16_t daily_swarm_index(void)
{
    uint32_t value;
    update_clock();
    value = (uint32_t)G_CLOCK->year * 372u
        + (uint32_t)G_CLOCK->month * 31u + G_CLOCK->day;
    return bounded_mod_u32(value, VEGA_WILD_SWARM_ENTRY_COUNT);
}

static const uint8_t *find_entry(uint8_t map_group, uint8_t map_number,
                                 uint8_t area, uint8_t layer,
                                 uint8_t daily_only)
{
    uint16_t entry_index;
    uint16_t swarm_index = 0;
    uint16_t active_swarm = daily_only ? daily_swarm_index() : 0;

    for (entry_index = 0; entry_index < VEGA_WILD_OVERLAY_TABLE_COUNT;
         ++entry_index) {
        const uint8_t *entry = OVERLAY_TABLE
            + (uint32_t)entry_index * OVERLAY_ENTRY_SIZE;
        uint8_t is_swarm = entry[3] == ECOLOGY_LAYER_SWARM;
        if (entry[0] == map_group && entry[1] == map_number
            && entry[2] == area && entry[3] == layer
            && (!daily_only || swarm_index == active_swarm)) {
            return entry;
        }
        if (is_swarm) {
            ++swarm_index;
        }
    }
    return NULL;
}

static struct EcologySelection select_from_entry(const uint8_t *entry,
                                                   uint16_t original_species,
                                                   uint8_t original_level,
                                                   uint8_t rod,
                                                   uint8_t force)
{
    struct EcologySelection result = {original_species, original_level, 0};
    uint8_t eligible[OVERLAY_MAX_CANDIDATES];
    uint8_t eligible_count = 0;
    uint8_t badges = badge_count();
    uint8_t count;
    uint8_t index;
    uint16_t random;
    uint8_t candidate;
    uint8_t badge_rule;
    uint8_t minimum;
    uint8_t maximum;

    if (entry == NULL) {
        return result;
    }
    count = entry[5];
    if (count == 0 || count > OVERLAY_MAX_CANDIDATES) {
        return result;
    }
    random = FN_RANDOM();
    if (!force && (uint8_t)random >= entry[4]) {
        return result;
    }
    for (index = 0; index < count; ++index) {
        badge_rule = entry[OVERLAY_MIN_BADGES_OFFSET + index];
        if ((badges >= (badge_rule & ~BADGE_RULE_RADAR_OVERRIDE)
             || ((badge_rule & BADGE_RULE_RADAR_OVERRIDE)
                 && normalized_mode() == VEGA_ECOLOGY_MODE_NIGHT
                 && FN_CHECK_BAG_HAS_ITEM(ECOLOGY_RADAR_ITEM, 1)))
            && rod >= entry[OVERLAY_MIN_ROD_OFFSET + index]) {
            eligible[eligible_count++] = index;
        }
    }
    if (eligible_count == 0) {
        return result;
    }
    candidate = eligible[(uint8_t)(((uint32_t)(random >> 8)
                                    * eligible_count) >> 8)];
    result.species = read_u16(entry + OVERLAY_SPECIES_OFFSET + candidate * 2u);
    if (FN_FLAG_GET(FLAG_HALL_OF_FAME)) {
        minimum = entry[OVERLAY_POST_MIN_OFFSET + candidate];
        maximum = entry[OVERLAY_POST_MAX_OFFSET + candidate];
    } else {
        minimum = entry[OVERLAY_PRE_MIN_OFFSET + candidate];
        maximum = entry[OVERLAY_PRE_MAX_OFFSET + candidate];
    }
    if (minimum == 0 || maximum < minimum) {
        result.species = original_species;
        return result;
    }
    random = FN_RANDOM();
    result.level = (uint8_t)(minimum + bounded_mod_u32(
        random, (uint16_t)(maximum - minimum + 1u)));
    result.hit = 1;
    return result;
}

static struct EcologySelection select_encounter(uint16_t original_species,
                                                 uint8_t original_level,
                                                 uint8_t area, uint8_t rod,
                                                 uint8_t force_hidden)
{
    struct EcologySelection result = {original_species, original_level, 0};
    const uint8_t *save = *SAVE_BLOCK1_PTR;
    const uint8_t *entry = NULL;
    uint8_t mode;
    uint8_t group;
    uint8_t map;

    if (save == NULL) {
        return result;
    }
    group = save[4];
    map = save[5];
    mode = normalized_mode();

    /* Hidden rows are an explicit radar scan, not a replacement for every
     * ordinary step encounter while the menu cursor remains on that mode. */
    if (force_hidden) {
        entry = find_entry(group, map, WILD_AREA_HIDDEN,
                           ECOLOGY_LAYER_HIDDEN, 0);
        result = select_from_entry(entry, original_species, original_level,
                                   rod, 1);
        return result;
    }

    if (area == WILD_AREA_FISHING) {
        entry = find_entry(group, map, WILD_AREA_FISHING,
                           ECOLOGY_LAYER_FISHING, 0);
        return select_from_entry(entry, original_species, original_level,
                                 rod, 0);
    }

    if (mode == VEGA_ECOLOGY_MODE_SWARM) {
        entry = find_entry(group, map, area, ECOLOGY_LAYER_SWARM, 0);
    } else if (mode == VEGA_ECOLOGY_MODE_DAY) {
        entry = find_entry(group, map, area, ECOLOGY_LAYER_DAY, 0);
    } else if (mode == VEGA_ECOLOGY_MODE_NIGHT) {
        entry = find_entry(group, map, area, ECOLOGY_LAYER_NIGHT, 0);
    } else if (mode == VEGA_ECOLOGY_MODE_AUTO) {
        entry = find_entry(group, map, area, ECOLOGY_LAYER_SWARM, 1);
        result = select_from_entry(entry, original_species, original_level,
                                   rod, 0);
        if (result.hit) {
            return result;
        }
        entry = find_entry(group, map, area,
                           is_night() ? ECOLOGY_LAYER_NIGHT
                                      : ECOLOGY_LAYER_DAY, 0);
    }

    result = select_from_entry(entry, original_species, original_level, rod, 0);
    if (result.hit) {
        return result;
    }
    entry = find_entry(group, map, area, ECOLOGY_LAYER_NORMAL, 0);
    return select_from_entry(entry, original_species, original_level, rod, 0);
}

PUBLIC_TEXT(VegaWildOverlay_SelectSpecies)
uint16_t VegaWildOverlay_SelectSpecies(uint16_t original_species, uint8_t area)
{
    return select_encounter(original_species, 1, area, 0, 0).species;
}

PUBLIC_TEXT(VegaWildOverlay_TryGenerateWildMon)
uint8_t VegaWildOverlay_TryGenerateWildMon(const void *raw_info, uint8_t area,
                                           uint8_t flags)
{
    const struct WildPokemonInfo *info = raw_info;
    struct EcologySelection selected;
    uint8_t slot;
    uint8_t level;

    if (info == NULL || info->wild_pokemon == NULL) {
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
    selected = select_encounter(info->wild_pokemon[slot].species, level,
                                area, 0, 0);
    if ((flags & WILD_CHECK_REPEL) && !FN_LEVEL_ALLOWED(selected.level)) {
        return 0;
    }
    FN_GENERATE_WILD(selected.species, selected.level, slot);
    return 1;
}

PUBLIC_TEXT(VegaWildOverlay_GenerateFishingEncounter)
uint16_t VegaWildOverlay_GenerateFishingEncounter(const void *raw_info,
                                                   uint8_t rod)
{
    const struct WildPokemonInfo *info = raw_info;
    struct EcologySelection selected;
    uint8_t slot;
    uint8_t level;

    if (info == NULL || info->wild_pokemon == NULL) {
        return 0;
    }
    slot = FN_CHOOSE_FISHING(rod);
    level = FN_CHOOSE_LEVEL(&info->wild_pokemon[slot]);
    selected = select_encounter(info->wild_pokemon[slot].species, level,
                                WILD_AREA_FISHING, rod, 0);
    FN_GENERATE_WILD(selected.species, selected.level, slot);
    return selected.species;
}

PUBLIC_TEXT(VegaWildOverlay_SetMode)
void VegaWildOverlay_SetMode(uint8_t mode)
{
    if (mode > VEGA_ECOLOGY_MODE_HIDDEN) {
        mode = VEGA_ECOLOGY_MODE_AUTO;
    }
    (void)FN_VAR_SET(ECOLOGY_MODE_VAR, mode);
}

PUBLIC_TEXT(VegaWildOverlay_GetMode)
uint8_t VegaWildOverlay_GetMode(void)
{
    return normalized_mode();
}

PUBLIC_TEXT(VegaWildOverlay_TryHiddenEncounter)
uint8_t VegaWildOverlay_TryHiddenEncounter(void)
{
    struct EcologySelection selected = select_encounter(0, 1,
        WILD_AREA_HIDDEN, 2, 1);
    if (!selected.hit || selected.species == 0) {
        return 0;
    }
    FN_GENERATE_WILD(selected.species, selected.level, 0);
    FN_START_WILD_BATTLE();
    return 1;
}

static void close_mode_menu(uint8_t task_id)
{
    uint8_t window_id = (uint8_t)G_TASKS[task_id].data[0];
    FN_PLAY_SE(SE_SELECT);
    FN_CLEAR_STD_WINDOW_FRAME(window_id, 1);
    FN_REMOVE_WINDOW(window_id);
    FN_SCHEDULE_BG_COPY(0);
    FN_DESTROY_TASK(task_id);
    FN_ENABLE_BOTH_SCRIPT_CONTEXTS();
}

static void Task_HandleEcologyMenu(uint8_t task_id)
{
    int8_t choice = FN_MENU_PROCESS_INPUT();
    if (choice == MENU_NOTHING_CHOSEN) {
        return;
    }
    if (choice == MENU_B_PRESSED || choice < 0 || choice >= MENU_COUNT) {
        close_mode_menu(task_id);
        return;
    }
    if (choice < MENU_CANCEL) {
        VegaWildOverlay_SetMode((uint8_t)choice);
    }
    close_mode_menu(task_id);
    if (choice == VEGA_ECOLOGY_MODE_HIDDEN) {
        (void)VegaWildOverlay_TryHiddenEncounter();
    }
}

static void Task_OpenEcologyMenu(uint8_t old_task_id)
{
    struct WindowTemplate template;
    uint8_t task_id;
    uint8_t window_id;
    uint8_t index;
    uint8_t mode = normalized_mode();
    const uint8_t *mode_text = sModeTexts[mode];

    if (mode == VEGA_ECOLOGY_MODE_AUTO) {
        mode_text = is_night() ? sTextAutoNight : sTextAutoDay;
    }

    FN_DESTROY_TASK(old_task_id);
    task_id = FN_CREATE_TASK(Task_HandleEcologyMenu, 0x50);
    if (task_id >= PARTY_TASK_COUNT) {
        FN_ENABLE_BOTH_SCRIPT_CONTEXTS();
        return;
    }
    template.bg = 0;
    template.tilemap_left = 9;
    template.tilemap_top = 0;
    template.width = 20;
    template.height = 19;
    template.palette_num = 15;
    template.base_block = FN_GET_STD_WINDOW_BASE_TILE();
    window_id = (uint8_t)FN_ADD_WINDOW(&template);
    if (window_id == MENU_WINDOW_INVALID) {
        FN_DESTROY_TASK(task_id);
        FN_ENABLE_BOTH_SCRIPT_CONTEXTS();
        return;
    }
    G_TASKS[task_id].data[0] = window_id;
    FN_FILL_WINDOW_PIXEL_BUFFER(window_id, 0x11);
    FN_DRAW_STD_WINDOW_FRAME(window_id, 0);
    FN_PUT_WINDOW_TILEMAP(window_id);
    FN_ADD_TEXT_PRINTER(window_id, 2, sTextMode, 8, 1, 0, NULL);
    FN_ADD_TEXT_PRINTER(window_id, 2, mode_text, 64, 1, 0, NULL);
    for (index = 0; index < MENU_COUNT; ++index) {
        FN_ADD_TEXT_PRINTER(window_id, 2, sModeTexts[index], 16,
                            (uint8_t)(17 + index * 16), 0, NULL);
    }
    FN_MENU_INIT_CURSOR(window_id, 2, 0, 17, 16, MENU_COUNT, mode);
    FN_COPY_WINDOW_TO_VRAM(window_id, COPYWIN_BOTH);
    FN_SCHEDULE_BG_COPY(0);
    FN_SCRIPT_CONTEXT2_ENABLE();
}

PUBLIC_TEXT(VegaWildOverlay_FieldUse)
void VegaWildOverlay_FieldUse(uint8_t task_id)
{
    *S_ITEM_USE_ON_FIELD_CB = Task_OpenEcologyMenu;
    FN_SETUP_ITEM_USE_ON_FIELD(task_id);
}
