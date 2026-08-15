/*
 * USER-20260816-ACQUISITION-EVENTS
 *
 * v1.3.9 stage 25の固定FireRed/CFRU/DPE ABIを、取得パッケージの共通
 * transaction runtimeへ接続する。生ROMアドレスはbuild scriptが署名検証し、
 * CFRU linked symbolは固定fingerprintのlinked.oから注入する。
 */

#include "acquisition_engine_adapter_rom.h"

#include <stddef.h>
#include <stdint.h>

#include "../save_migration/save_migration.h"
#include "../../vendor/vega_acquisition/generated/acquisition_collection_defs.h"
#include "../../vendor/vega_acquisition/generated/acquisition_event_defs.h"
#include "../../vendor/vega_acquisition/generated/acquisition_host_defs.h"
#include "../../vendor/vega_acquisition/generated/acquisition_save_layout.h"
#include "../../vendor/vega_acquisition/overlays/acquisition_runtime/acquisition_engine_adapter.h"
#include "../../vendor/vega_acquisition/overlays/acquisition_runtime/acquisition_save_migration.h"

typedef uint8_t u8;
typedef int8_t s8;
typedef uint16_t u16;
typedef int16_t s16;
typedef uint32_t u32;
typedef int32_t s32;

enum {
    ACQ_SPECIES_COUNT = 1621,
    ACQ_NATIONAL_COUNT = 1025,
    ACQ_PARTY_SIZE = 6,
    ACQ_MON_SIZE = 100,
    ACQ_BOX_MON_SIZE = 80,
    ACQ_BOX_COUNT = 14,
    ACQ_BOX_CAPACITY = 30,
    ACQ_MON_DATA_SPECIES = 11,
    ACQ_SAVE_SECTOR = 31,
    ACQ_SAVE_SECTOR_DATA_SIZE = 0x0FF0,
    ACQ_SAVE_SECTOR_SIZE = 0x1000,
    ACQ_GET_CAUGHT = 1,
    ACQ_SET_SEEN = 2,
    ACQ_SET_CAUGHT = 3,

    ACQ_FLAG_BADGE_1 = 0x0820,
    ACQ_FLAG_HALL_OF_FAME = 0x082C,
    ACQ_FLAG_SHIOU_CLEAR = 0x0824,
    ACQ_FLAG_DH_CLEAR = 0x114B,
    ACQ_VAR_PC_BOX_TO_SEND_MON = 0x4037,

    ACQ_ITEM_LINK_CABLE = 395,
    ACQ_ITEM_ECOLOGY_RADAR = 348,

    ACQ_MENU_PAGE_SIZE = 5,
    ACQ_MENU_MAX_ROWS = 6,
    ACQ_MENU_NOTHING = -2,
    ACQ_MENU_B = -1,
    ACQ_WINDOW_INVALID = 0xFF,
    ACQ_NUM_TASKS = 16,
    ACQ_COPYWIN_BOTH = 3,
    ACQ_SE_SELECT = 5,

    ACQ_LOCAL_MINE = 0xFFFD,
    ACQ_TOKEN_PARTY = 0x10000000u,
    ACQ_TOKEN_BOX = 0x20000000u,
    ACQ_TOKEN_ITEM = 0x30000000u,
    ACQ_TOKEN_KIND_MASK = 0xF0000000u,

    ACQ_RESULT_NOT_SET = 0xFFFF,
    ACQ_BATTLE_WON = 1,
    ACQ_BATTLE_RAN = 4,
    ACQ_BATTLE_PLAYER_TELEPORTED = 5,
    ACQ_BATTLE_MON_FLED = 6,
    ACQ_BATTLE_CAUGHT = 7,
    ACQ_BATTLE_MON_TELEPORTED = 10,
};

struct Task {
    void (*func)(u8 task_id);
    u8 is_active;
    u8 prev;
    u8 next;
    u8 priority;
    s16 data[16];
};

struct WindowTemplate {
    u8 bg;
    u8 tilemap_left;
    u8 tilemap_top;
    u8 width;
    u8 height;
    u8 palette_num;
    u16 base_block;
};

typedef struct AcqFossilRecipe {
    u16 species;
    u16 item1;
    u16 item2;
} AcqFossilRecipe;

typedef struct AcqVolatileState {
    u16 eligible[26];
    u16 last_result;
    u16 last_event;
    u8 eligible_count;
    u8 page;
    u8 window_id;
    u8 empty_result;
    u8 rank_valid;
    u8 effective_rank;
    u8 consumed_mask;
    u8 reserved0;
    u8 names[ACQ_MENU_MAX_ROWS][11];
    u8 mon[ACQ_MON_SIZE];
    u8 reserved[58];
} AcqVolatileState;

_Static_assert(sizeof(struct Task) == 40, "FireRed Task ABI changed");
_Static_assert(sizeof(struct WindowTemplate) == 8,
               "FireRed WindowTemplate ABI changed");
_Static_assert(sizeof(AcqVolatileState) == VEGA_ACQ_VOLATILE_STATE_BYTES,
               "acquisition volatile reservation changed");
_Static_assert(sizeof(VegaAcqSaveBlock) == VEGA_ACQUISITION_SAVE_BYTES,
               "inner acquisition save does not fit outer reservation");

typedef void (*TaskFunc)(u8 task_id);
typedef u8 (*CreateTaskFn)(TaskFunc func, u8 priority);
typedef void (*TaskIdFn)(u8 task_id);
typedef void (*VoidFn)(void);
typedef u8 (*FlagGetFn)(u16 flag);
typedef u16 (*VarGetFn)(u16 variable);
typedef u8 (*VarSetFn)(u16 variable, u16 value);
typedef u8 (*BagFn)(u16 item, u16 quantity);
typedef u32 (*GetMonDataFn)(const void *mon, s32 field, u8 *destination);
typedef u32 (*GetBoxMonDataAtFn)(u8 box, u8 position, s32 field);
typedef void *(*GetBoxedMonPtrFn)(u8 box, u8 position);
typedef void (*ZeroBoxMonAtFn)(u8 box, u8 position);
typedef void (*CreateMonFn)(void *mon, u16 species, u8 level, u8 fixed_iv,
                            u8 nature, u8 unown_letter);
typedef void (*CreateEggFn)(void *mon, u16 species);
typedef u8 (*GiveMonFn)(void *mon);
typedef u8 (*TryWriteSectorFn)(u16 sector, const void *source);
typedef u8 (*TrySavingDataFn)(u8 save_type);
typedef void (*ReadFlashFn)(u16 sector, u32 offset, void *destination,
                            u32 size);
typedef u16 (*SpeciesToNationalFn)(u16 species);
typedef u8 (*GetSetPokedexFlagFn)(u16 national, u8 operation);
typedef u16 (*RandomFn)(void);
typedef u16 (*AddWindowFn)(const struct WindowTemplate *template);
typedef void (*WindowU8Fn)(u8 window_id);
typedef void (*WindowPairFn)(u8 window_id, u8 value);
typedef void (*TextPrinterFn)(u8 window_id, u8 font_id, const u8 *text,
                              u8 x, u8 y, u8 speed, void *callback);
typedef u8 (*MenuInitCursorFn)(u8 window_id, u8 font_id, u8 left, u8 top,
                               u8 cursor_height, u8 count, u8 cursor);
typedef s8 (*MenuInputFn)(void);
typedef u16 (*GetBaseTileFn)(void);
typedef void (*PlaySeFn)(u16 song);
typedef void (*GetSpeciesNameFn)(u8 *destination, u16 species);

#define PTR(type, address) ((type)(uintptr_t)(address))

#ifndef VEGA_ACQ_CREATE_MON_ADDRESS
#error "fixed CFRU CreateMonWithNatureLetter address is required"
#endif
#ifndef VEGA_ACQ_CREATE_EGG_ADDRESS
#error "fixed CFRU CreateEgg address is required"
#endif
#ifndef VEGA_ACQ_GIVE_MON_ADDRESS
#error "fixed CFRU GiveMonToPlayer address is required"
#endif
#ifndef VEGA_ACQ_GET_BOX_MON_DATA_ADDRESS
#error "fixed CFRU GetBoxMonDataAt address is required"
#endif
#ifndef VEGA_ACQ_GET_BOXED_MON_PTR_ADDRESS
#error "fixed CFRU GetBoxedMonPtr address is required"
#endif
#ifndef VEGA_ACQ_ZERO_BOX_MON_AT_ADDRESS
#error "fixed CFRU ZeroBoxMonAt address is required"
#endif
#ifndef VEGA_ACQ_SPECIES_NAME_ADDRESS
#error "fixed T09 species-name address is required"
#endif

#define G_ACQ_STATE PTR(AcqVolatileState *, VEGA_ACQ_VOLATILE_STATE_ADDRESS)
#define G_PLAYER_PARTY PTR(u8 *, 0x020241E4u)
#define G_PLAYER_PARTY_COUNT PTR(volatile u8 *, 0x02023F89u)
#define G_ENEMY_PARTY PTR(u8 *, 0x02023F8Cu)
#define G_BATTLE_OUTCOME PTR(volatile u8 *, 0x02023DEAu)
#define G_SPECIAL_RESULT PTR(volatile u16 *, 0x02037004u)
#define G_SPECIAL_VAR_8004 PTR(volatile u16 *, 0x02036FF4u)
#define G_SPECIAL_MON_BOX_ID PTR(volatile u16 *, 0x0203700Au)
#define G_SPECIAL_MON_BOX_POS PTR(volatile u16 *, 0x0203700Cu)
#define G_TASKS PTR(struct Task *, 0x030050D0u)

#define FN_FLAG_GET PTR(FlagGetFn, 0x0806DEC5u)
#define FN_VAR_GET PTR(VarGetFn, 0x0806DD5Du)
#define FN_VAR_SET PTR(VarSetFn, 0x0806DD79u)
#define FN_CHECK_BAG PTR(BagFn, 0x08099949u)
#define FN_ADD_BAG PTR(BagFn, 0x08099A8Du)
#define FN_REMOVE_BAG PTR(BagFn, 0x08099BE1u)
#define FN_GET_MON_DATA PTR(GetMonDataFn, 0x0803F355u)
#define FN_CALCULATE_PARTY_COUNT PTR(u8 (*)(void), 0x08040331u)
#define FN_CREATE_MON PTR(CreateMonFn, VEGA_ACQ_CREATE_MON_ADDRESS)
#define FN_CREATE_EGG PTR(CreateEggFn, VEGA_ACQ_CREATE_EGG_ADDRESS)
#define FN_GIVE_MON PTR(GiveMonFn, VEGA_ACQ_GIVE_MON_ADDRESS)
#define FN_GET_BOX_MON_DATA \
    PTR(GetBoxMonDataAtFn, VEGA_ACQ_GET_BOX_MON_DATA_ADDRESS)
#define FN_GET_BOXED_MON_PTR \
    PTR(GetBoxedMonPtrFn, VEGA_ACQ_GET_BOXED_MON_PTR_ADDRESS)
#define FN_ZERO_BOX_MON_AT \
    PTR(ZeroBoxMonAtFn, VEGA_ACQ_ZERO_BOX_MON_AT_ADDRESS)
#define FN_TRY_WRITE_SECTOR PTR(TryWriteSectorFn, 0x080DA9C1u)
#define FN_TRY_SAVING_DATA PTR(TrySavingDataFn, 0x080DB34Du)
#define FN_READ_FLASH PTR(ReadFlashFn, 0x081C2A55u)
#define FN_SPECIES_TO_NATIONAL PTR(SpeciesToNationalFn, 0x08042989u)
#define FN_GET_SET_DEX PTR(GetSetPokedexFlagFn, 0x08088A51u)
#define FN_RANDOM PTR(RandomFn, 0x0804448Du)
#define FN_START_SCRIPTED_WILD_BATTLE PTR(VoidFn, 0x0807EEB5u)
#define FN_SCRIPT_CONTEXT2_ENABLE PTR(VoidFn, 0x08069201u)
#define FN_ENABLE_BOTH_SCRIPT_CONTEXTS PTR(VoidFn, 0x080693F5u)
#define FN_CREATE_TASK PTR(CreateTaskFn, 0x08076BB5u)
#define FN_DESTROY_TASK PTR(TaskIdFn, 0x08076CA1u)
#define FN_ADD_WINDOW PTR(AddWindowFn, 0x08003CB1u)
#define FN_REMOVE_WINDOW PTR(WindowU8Fn, 0x08003E09u)
#define FN_COPY_WINDOW_TO_VRAM PTR(WindowPairFn, 0x08003EEDu)
#define FN_PUT_WINDOW_TILEMAP PTR(WindowU8Fn, 0x08003F6Du)
#define FN_FILL_WINDOW_PIXEL_BUFFER PTR(WindowPairFn, 0x08004429u)
#define FN_ADD_TEXT_PRINTER PTR(TextPrinterFn, 0x08002C45u)
#define FN_SCHEDULE_BG_COPY PTR(WindowU8Fn, 0x080F77FDu)
#define FN_DRAW_STD_WINDOW_FRAME PTR(WindowPairFn, 0x080F7F7Du)
#define FN_CLEAR_STD_WINDOW_FRAME PTR(WindowPairFn, 0x080F7FFDu)
#define FN_GET_STD_WINDOW_BASE_TILE PTR(GetBaseTileFn, 0x080F89CDu)
#define FN_MENU_INIT_CURSOR PTR(MenuInitCursorFn, 0x0811030Du)
#define FN_MENU_PROCESS_INPUT PTR(MenuInputFn, 0x08110BF9u)
#define FN_PLAY_SE PTR(PlaySeFn, 0x08071A71u)
#define FN_GET_SPECIES_NAME \
    PTR(GetSpeciesNameFn, VEGA_ACQ_SPECIES_NAME_ADDRESS)
#define ACQ_SAVE_BUFFER PTR(u8 *, 0x020399B0u)
#define ACQ_SECTOR31_IMAGE PTR(const u8 *, 0x0203CF9Cu)

#define ACQ_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

static const u8 sTextNext[] = {0x12, 0x38, 0xFF};
static const u8 sTextCancel[] = {0x24, 0x22, 0x29, 0xFF};
static const u8 sTextMine[] = {0x56, 0x5E, 0x57, 0x0B, 0x02, 0x08, 0x12, 0xFF};
static const u8 sTextLinkCable[] = {
    0x12, 0x03, 0x0C, 0x2E, 0x59, 0xAE, 0x98, 0x79, 0xFF
};
static const u8 sTextEcologyRadar[] = {
    0x0E, 0x02, 0x10, 0x02, 0x7A, 0xAE, 0x91, 0xAE, 0xFF
};

static const AcqFossilRecipe sFossilRecipes[] = {
    {487, 583, 0}, {489, 584, 0}, {635, 519, 0}, {698, 842, 0},
    {700, 843, 0}, {812, 844, 0}, {814, 845, 0}, {985, 846, 0},
    {987, 847, 0}, {1353, 848, 850}, {1354, 848, 851},
    {1355, 849, 850}, {1356, 849, 851}, {121, 287, 0},
    {388, 358, 0}, {390, 357, 0},
};

static const u16 sMineableFossils[] = {
    287, 357, 358, 519, 583, 584, 842, 843, 844,
    845, 846, 847, 848, 849, 850, 851,
};

static VegaAcqSaveBlock *save_block(void)
{
    return (VegaAcqSaveBlock *)(void *)gVegaModernSaveData->acquisition_save_block;
}

static u8 save_structurally_ready(void)
{
    VegaAcqSaveBlock *block = save_block();
    return (u8)(
        gVegaModernSaveData->magic == VEGA_SAVE_MAGIC
        && gVegaModernSaveData->version == VEGA_SAVE_VERSION
        && gVegaModernSaveData->struct_size == sizeof(*gVegaModernSaveData)
        && block->magic == VEGA_ACQ_SAVE_MAGIC
        && block->version == VEGA_ACQ_SAVE_VERSION
        && block->size == sizeof(*block));
}

static void clear_bytes(void *destination, u32 size)
{
    u8 *out = (u8 *)destination;
    u32 index;
    for (index = 0; index < size; ++index)
        out[index] = 0u;
}

static void copy_bytes(void *destination, const void *source, u32 size)
{
    u8 *out = (u8 *)destination;
    const u8 *in = (const u8 *)source;
    u32 index;
    for (index = 0u; index < size; ++index)
        out[index] = in[index];
}

static u8 persist_save_sector(void)
{
    clear_bytes(ACQ_SAVE_BUFFER, ACQ_SAVE_SECTOR_SIZE);
    copy_bytes(ACQ_SAVE_BUFFER, ACQ_SECTOR31_IMAGE,
               ACQ_SAVE_SECTOR_DATA_SIZE);
    return (u8)(FN_TRY_WRITE_SECTOR(ACQ_SAVE_SECTOR, ACQ_SAVE_BUFFER) == 1u);
}

static u8 persist_standard_save(void)
{
    return (u8)(FN_TRY_SAVING_DATA(0u) == 1u);
}

static u8 restore_durable_ledger(void)
{
    VegaModernSaveData *candidate;
    FN_READ_FLASH(ACQ_SAVE_SECTOR, 0u, ACQ_SAVE_BUFFER,
                  ACQ_SAVE_SECTOR_SIZE);
    candidate = (VegaModernSaveData *)(void *)(
        ACQ_SAVE_BUFFER + (VEGA_SAVE_EWRAM_ADDRESS
                           - (u32)(uintptr_t)ACQ_SECTOR31_IMAGE));
    if (VegaSaveValidate(candidate, VEGA_SAVE_LEDGER_SIZE) != VEGA_SAVE_OK)
        return 0u;
    copy_bytes(gVegaModernSaveData, candidate, VEGA_SAVE_LEDGER_SIZE);
    return 1u;
}

static void copy_text(u8 *destination, const u8 *source)
{
    u8 index;
    for (index = 0u; index < 10u; ++index) {
        destination[index] = source[index];
        if (source[index] == 0xFFu)
            return;
    }
    destination[10] = 0xFFu;
}

static u8 strings_equal(const char *left, const char *right)
{
    if (left == NULL || right == NULL)
        return 0u;
    while (*left != '\0' && *left == *right) {
        ++left;
        ++right;
    }
    return (u8)(*left == *right);
}

static void set_bit(u8 *bits, u16 bit, u8 value)
{
    u8 mask = (u8)(1u << (bit & 7u));
    if (value)
        bits[bit >> 3] |= mask;
    else
        bits[bit >> 3] &= (u8)~mask;
}

static u8 get_bit(const u8 *bits, u16 bit)
{
    return (u8)((bits[bit >> 3] >> (bit & 7u)) & 1u);
}

static u16 national_for_species(u16 species)
{
    u16 national;
    if (species == 0u || species >= ACQ_SPECIES_COUNT)
        return 0u;
    national = FN_SPECIES_TO_NATIONAL(species);
    return national <= ACQ_NATIONAL_COUNT ? national : 0u;
}

static u8 direct_registered(u16 species)
{
    const VegaAcqCollectionDef *def;
    u16 national;
    if (species >= ACQ_SPECIES_COUNT)
        return 0u;
    def = &gVegaAcqCollectionDefs[species];
    if (def->target_class == 3u && def->ledger_bit_index != 0xFFFFu
        && save_structurally_ready())
        return get_bit(save_block()->collection_bits, def->ledger_bit_index);
    national = national_for_species(species);
    if (national != 0u && FN_GET_SET_DEX(national, ACQ_GET_CAUGHT))
        return 1u;
    return (u8)(def->ledger_bit_index != 0xFFFFu
                && save_structurally_ready()
                && get_bit(save_block()->collection_bits,
                           def->ledger_bit_index));
}

static u8 migration_registered(u16 species, void *context)
{
    (void)context;
    return direct_registered(species);
}

static u8 ensure_save(void)
{
    VegaSaveStatus outer = VegaSaveValidate(gVegaModernSaveData,
                                             VEGA_SAVE_LEDGER_SIZE);
    if (outer == VEGA_SAVE_EMPTY_OR_LEGACY && restore_durable_ledger())
        outer = VEGA_SAVE_OK;
    if (outer == VEGA_SAVE_EMPTY_OR_LEGACY) {
        VegaSaveInitNew(gVegaModernSaveData,
                        FN_FLAG_GET(ACQ_FLAG_BADGE_1));
    } else if (outer != VEGA_SAVE_OK) {
        return 0u;
    }
    if (!VegaAcqSaveValidate(save_block())) {
        if (!VegaAcqSaveMigrate(save_block(), migration_registered, NULL))
            return 0u;
        VegaSaveFinalize(gVegaModernSaveData);
        /* Establish the normal two-slot save before sector 31.  A first-ever
         * normal save clears expansion sectors 28..31 in the base engine. */
        if (!persist_standard_save() || !persist_save_sector())
            return 0u;
    }
    return 1u;
}

static const AcqFossilRecipe *fossil_recipe(const VegaAcqEventDef *event_def)
{
    u8 index;
    for (index = 0u;
         index < (u8)(sizeof(sFossilRecipes) / sizeof(sFossilRecipes[0]));
         ++index) {
        if (sFossilRecipes[index].species == event_def->species_id)
            return &sFossilRecipes[index];
    }
    return NULL;
}

static u8 storage_available(void)
{
    u8 box;
    u8 position;
    if (*G_PLAYER_PARTY_COUNT < ACQ_PARTY_SIZE)
        return 1u;
    for (box = 0u; box < ACQ_BOX_COUNT; ++box) {
        for (position = 0u; position < ACQ_BOX_CAPACITY; ++position) {
            if (FN_GET_BOX_MON_DATA(box, position, ACQ_MON_DATA_SPECIES) == 0u)
                return 1u;
        }
    }
    return 0u;
}

static u8 caught_count_rank(void)
{
    u16 national;
    u16 caught = 0u;
    u8 rank;
    if (!FN_FLAG_GET(ACQ_FLAG_HALL_OF_FAME)
        && !gVegaModernSaveData->vega_hall_of_fame)
        return 0u;
    for (national = 1u; national <= ACQ_NATIONAL_COUNT; ++national) {
        if (FN_GET_SET_DEX(national, ACQ_GET_CAUGHT))
            ++caught;
    }
    rank = 1u;
    if (caught >= 150u)
        rank = 2u;
    if (caught >= 350u)
        rank = 3u;
    if (caught >= 600u)
        rank = 4u;
    if (caught >= 850u)
        rank = 5u;
    if (gVegaModernSaveData->research_rank > rank)
        rank = gVegaModernSaveData->research_rank;
    if (rank > 5u)
        rank = 5u;
    if (rank > gVegaModernSaveData->research_rank)
        gVegaModernSaveData->research_rank = rank;
    return rank;
}

static u8 effective_rank(void)
{
    if (!G_ACQ_STATE->rank_valid) {
        G_ACQ_STATE->effective_rank = caught_count_rank();
        G_ACQ_STATE->rank_valid = 1u;
    }
    return G_ACQ_STATE->effective_rank;
}

static u8 hall_of_fame(void)
{
    return (u8)(gVegaModernSaveData->vega_hall_of_fame
                || FN_FLAG_GET(ACQ_FLAG_HALL_OF_FAME));
}

static u8 kanto_access(void)
{
    return (u8)(gVegaModernSaveData->kanto_travel_unlocked
                || hall_of_fame()
                || (FN_FLAG_GET(ACQ_FLAG_SHIOU_CLEAR)
                    && FN_FLAG_GET(ACQ_FLAG_DH_CLEAR)));
}

static void clear_destination(u32 token)
{
    u32 kind = token & ACQ_TOKEN_KIND_MASK;
    if (kind == ACQ_TOKEN_PARTY) {
        u8 slot = (u8)(token & 0xFFu);
        if (slot < ACQ_PARTY_SIZE) {
            clear_bytes(G_PLAYER_PARTY + (u32)slot * ACQ_MON_SIZE,
                        ACQ_MON_SIZE);
            *G_PLAYER_PARTY_COUNT = FN_CALCULATE_PARTY_COUNT();
        }
    } else if (kind == ACQ_TOKEN_BOX) {
        u8 box = (u8)((token >> 8) & 0xFFu);
        u8 position = (u8)(token & 0xFFu);
        if (box < ACQ_BOX_COUNT && position < ACQ_BOX_CAPACITY)
            FN_ZERO_BOX_MON_AT(box, position);
    }
}

static u16 destination_species(u32 token)
{
    u32 kind = token & ACQ_TOKEN_KIND_MASK;
    if (kind == ACQ_TOKEN_PARTY) {
        u8 slot = (u8)(token & 0xFFu);
        if (slot < ACQ_PARTY_SIZE)
            return (u16)FN_GET_MON_DATA(
                G_PLAYER_PARTY + (u32)slot * ACQ_MON_SIZE,
                ACQ_MON_DATA_SPECIES, NULL);
    } else if (kind == ACQ_TOKEN_BOX) {
        u8 box = (u8)((token >> 8) & 0xFFu);
        u8 position = (u8)(token & 0xFFu);
        if (box < ACQ_BOX_COUNT && position < ACQ_BOX_CAPACITY)
            return (u16)FN_GET_BOX_MON_DATA(
                box, position, ACQ_MON_DATA_SPECIES);
    }
    return 0u;
}

static u16 deliver_mon(const VegaAcqEventDef *event_def, u32 *token)
{
    u8 outcome;
    u8 level = event_def->level == 0u ? 5u : event_def->level;
    u8 party_before = *G_PLAYER_PARTY_COUNT;
    u16 previous_pc_box = 0u;
    clear_bytes(G_ACQ_STATE->mon, ACQ_MON_SIZE);
    if (event_def->mode == VEGA_ACQ_MODE_EGG)
        FN_CREATE_EGG(G_ACQ_STATE->mon, event_def->species_id);
    else
        FN_CREATE_MON(G_ACQ_STATE->mon, event_def->species_id, level,
                      32u, (u8)(((u32)FN_RANDOM() * 25u) >> 16), 1u);
    if (party_before >= ACQ_PARTY_SIZE) {
        previous_pc_box = FN_VAR_GET(ACQ_VAR_PC_BOX_TO_SEND_MON);
        (void)FN_VAR_SET(ACQ_VAR_PC_BOX_TO_SEND_MON, 0u);
    }
    outcome = FN_GIVE_MON(G_ACQ_STATE->mon);
    if (outcome == 0u) {
        u8 slot = *G_PLAYER_PARTY_COUNT == 0u
            ? party_before : (u8)(*G_PLAYER_PARTY_COUNT - 1u);
        *token = ACQ_TOKEN_PARTY | slot;
        return VEGA_ACQ_RESULT_SUCCESS;
    }
    if (outcome == 1u) {
        if (*G_SPECIAL_MON_BOX_ID >= ACQ_BOX_COUNT) {
            FN_ZERO_BOX_MON_AT((u8)*G_SPECIAL_MON_BOX_ID,
                              (u8)*G_SPECIAL_MON_BOX_POS);
            (void)FN_VAR_SET(ACQ_VAR_PC_BOX_TO_SEND_MON, previous_pc_box);
            *token = 0u;
            return VEGA_ACQ_RESULT_BOX_FULL;
        }
        *token = ACQ_TOKEN_BOX
            | ((u32)(*G_SPECIAL_MON_BOX_ID & 0xFFu) << 8)
            | (u32)(*G_SPECIAL_MON_BOX_POS & 0xFFu);
        return VEGA_ACQ_RESULT_SUCCESS;
    }
    if (party_before >= ACQ_PARTY_SIZE)
        (void)FN_VAR_SET(ACQ_VAR_PC_BOX_TO_SEND_MON, previous_pc_box);
    *token = 0u;
    return VEGA_ACQ_RESULT_BOX_FULL;
}

ACQ_EXPORT(VegaAcqEngine_AdapterProbe)
u16 VegaAcqEngine_AdapterProbe(void)
{
    return VEGA_ACQ_ENGINE_ADAPTER_ABI_VERSION;
}

ACQ_EXPORT(VegaAcqAdapter_Probe)
u16 VegaAcqAdapter_Probe(void)
{
    return 0xA926u;
}

VegaAcqPendingTransaction *VegaAcqEngine_GetPending(void)
{
    if (!ensure_save())
        return NULL;
    return &save_block()->pending;
}

u8 VegaAcqEngine_IsUnlockSatisfied(const char *key)
{
    u8 rank;
    if (!save_structurally_ready())
        return 0u;
    if (strings_equal(key, "UNLOCK_NEW_GAME")
        || strings_equal(key, "UNLOCK_EXISTING_MAP_PROGRESSION")
        || strings_equal(key, "UNLOCK_EVOLUTION_GLOBAL"))
        return 1u;
    if (strings_equal(key, "UNLOCK_BADGE_1")
        || strings_equal(key, "UNLOCK_DAYCARE"))
        return FN_FLAG_GET(ACQ_FLAG_BADGE_1);
    if (strings_equal(key, "UNLOCK_HALL_OF_FAME"))
        return hall_of_fame();
    if (strings_equal(key, "UNLOCK_KANTO_EARLY_ACCESS")
        || strings_equal(key, "UNLOCK_LINK_CORD_SERVICE")
        || strings_equal(key, "UNLOCK_FOSSIL_SERVICE")
        || strings_equal(key, "UNLOCK_REGIONAL_NURSERY")
        || strings_equal(key, "UNLOCK_MOVE_CONDITION_TUTOR"))
        return kanto_access();
    rank = effective_rank();
    if (strings_equal(key, "UNLOCK_RESEARCH_RANK_1"))
        return rank >= 1u;
    if (strings_equal(key, "UNLOCK_RESEARCH_RANK_2"))
        return rank >= 2u;
    if (strings_equal(key, "UNLOCK_RESEARCH_RANK_3"))
        return rank >= 3u;
    if (strings_equal(key, "UNLOCK_RESEARCH_RANK_4"))
        return rank >= 4u;
    if (strings_equal(key, "UNLOCK_RESEARCH_RANK_5"))
        return rank >= 5u;
    if (strings_equal(key, "UNLOCK_SPHERE_RUINS_CLEAR"))
        return (u8)(gVegaModernSaveData->league_ii_cleared
                    || (hall_of_fame() && rank >= 4u));
    if (strings_equal(key, "UNLOCK_SPECIAL_ARCHIVE"))
        return (u8)(hall_of_fame() && kanto_access());
    if (strings_equal(key, "UNLOCK_BEAST_BALL"))
        return rank >= 3u;
    if (strings_equal(key, "UNLOCK_PARADOX_RESEARCH"))
        return (u8)(rank >= 4u
                    && (gVegaModernSaveData->league_ii_cleared
                        || hall_of_fame()));
    if (strings_equal(key, "UNLOCK_TERA_ORB"))
        return rank >= 5u;
    return 0u;
}

u8 VegaAcqEngine_IsEventConditionSatisfied(const VegaAcqEventDef *event_def)
{
    const AcqFossilRecipe *recipe;
    if (event_def == NULL)
        return 0u;
    if (event_def->mode != VEGA_ACQ_MODE_FOSSIL)
        return 1u;
    recipe = fossil_recipe(event_def);
    return (u8)(recipe != NULL
                && FN_CHECK_BAG(recipe->item1, 1u)
                && (recipe->item2 == 0u
                    || FN_CHECK_BAG(recipe->item2, 1u)));
}

u8 VegaAcqEngine_IsSpeciesRegistered(u16 species)
{
    if (!save_structurally_ready())
        return 0u;
    return direct_registered(species);
}

u8 VegaAcqEngine_SetSpeciesRegistered(u16 species, u8 registered)
{
    const VegaAcqCollectionDef *def;
    u16 national;
    if (!save_structurally_ready() || species >= ACQ_SPECIES_COUNT)
        return 0u;
    def = &gVegaAcqCollectionDefs[species];
    if (def->ledger_bit_index != 0xFFFFu)
        set_bit(save_block()->collection_bits, def->ledger_bit_index,
                registered);
    national = national_for_species(species);
    if (registered && national != 0u) {
        (void)FN_GET_SET_DEX(national, ACQ_SET_SEEN);
        (void)FN_GET_SET_DEX(national, ACQ_SET_CAUGHT);
    }
    return 1u;
}

u8 VegaAcqEngine_GetClaimCount(const VegaAcqEventDef *event_def)
{
    if (!save_structurally_ready() || event_def == NULL)
        return 0u;
    if (event_def->bounded_counter_index != 0xFFFFu)
        return save_block()->bounded_claim_counters[
            event_def->bounded_counter_index];
    if (event_def->claim_bit_index != 0xFFFFu)
        return get_bit(save_block()->event_claim_bits,
                       event_def->claim_bit_index);
    return 0u;
}

u8 VegaAcqEngine_SetClaimCount(const VegaAcqEventDef *event_def, u8 count)
{
    if (!save_structurally_ready() || event_def == NULL)
        return 0u;
    if (event_def->bounded_counter_index != 0xFFFFu) {
        save_block()->bounded_claim_counters[
            event_def->bounded_counter_index] = count;
        return 1u;
    }
    if (event_def->claim_bit_index != 0xFFFFu) {
        set_bit(save_block()->event_claim_bits, event_def->claim_bit_index,
                count != 0u);
        return 1u;
    }
    return (u8)(count == 0u);
}

u16 VegaAcqEngine_Preflight(const VegaAcqEventDef *event_def)
{
    if (!save_structurally_ready() || event_def == NULL)
        return VEGA_ACQ_RESULT_ENGINE_REJECTED;
    if (event_def->mode == VEGA_ACQ_MODE_CAPTURE
        || event_def->mode == VEGA_ACQ_MODE_GIFT
        || event_def->mode == VEGA_ACQ_MODE_EGG
        || event_def->mode == VEGA_ACQ_MODE_FOSSIL) {
        if (!storage_available())
            return VEGA_ACQ_RESULT_BOX_FULL;
    }
    if (event_def->mode == VEGA_ACQ_MODE_FOSSIL
        && !VegaAcqEngine_IsEventConditionSatisfied(event_def))
        return VEGA_ACQ_RESULT_MISSING_INPUT;
    return VEGA_ACQ_RESULT_SUCCESS;
}

u16 VegaAcqEngine_StartCaptureBattle(const VegaAcqEventDef *event_def)
{
    u8 level;
    if (event_def == NULL || event_def->species_id == 0u)
        return VEGA_ACQ_RESULT_ENGINE_REJECTED;
    level = event_def->level == 0u ? 50u : event_def->level;
    clear_bytes(G_ENEMY_PARTY, ACQ_PARTY_SIZE * ACQ_MON_SIZE);
    FN_CREATE_MON(G_ENEMY_PARTY, event_def->species_id, level, 32u,
                  (u8)(((u32)FN_RANDOM() * 25u) >> 16), 1u);
    FN_START_SCRIPTED_WILD_BATTLE();
    return VEGA_ACQ_RESULT_BATTLE_STARTED;
}

u16 VegaAcqEngine_StageOperation(const VegaAcqEventDef *event_def,
                                 u32 *transaction_token)
{
    const AcqFossilRecipe *recipe;
    u16 result;
    if (event_def == NULL || transaction_token == NULL)
        return VEGA_ACQ_RESULT_ENGINE_REJECTED;
    *transaction_token = 0u;
    G_ACQ_STATE->consumed_mask = 0u;
    if (event_def->mode == VEGA_ACQ_MODE_EVOLUTION_SUPPORT
        || event_def->mode == VEGA_ACQ_MODE_SERVICE)
        return VEGA_ACQ_RESULT_SUCCESS;
    if (event_def->mode == VEGA_ACQ_MODE_TRADE_EMULATOR) {
        if (FN_CHECK_BAG(ACQ_ITEM_LINK_CABLE, 1u))
            return VEGA_ACQ_RESULT_SUCCESS;
        if (!FN_ADD_BAG(ACQ_ITEM_LINK_CABLE, 1u))
            return VEGA_ACQ_RESULT_ENGINE_REJECTED;
        *transaction_token = ACQ_TOKEN_ITEM | ACQ_ITEM_LINK_CABLE;
        return VEGA_ACQ_RESULT_SUCCESS;
    }
    if (event_def->mode != VEGA_ACQ_MODE_GIFT
        && event_def->mode != VEGA_ACQ_MODE_EGG
        && event_def->mode != VEGA_ACQ_MODE_FOSSIL)
        return VEGA_ACQ_RESULT_ENGINE_REJECTED;
    result = deliver_mon(event_def, transaction_token);
    if (result != VEGA_ACQ_RESULT_SUCCESS)
        return result;
    if (event_def->mode != VEGA_ACQ_MODE_FOSSIL)
        return VEGA_ACQ_RESULT_SUCCESS;
    recipe = fossil_recipe(event_def);
    if (recipe == NULL || !FN_REMOVE_BAG(recipe->item1, 1u)) {
        clear_destination(*transaction_token);
        *transaction_token = 0u;
        return VEGA_ACQ_RESULT_MISSING_INPUT;
    }
    G_ACQ_STATE->consumed_mask = 1u;
    if (recipe->item2 != 0u && !FN_REMOVE_BAG(recipe->item2, 1u)) {
        (void)FN_ADD_BAG(recipe->item1, 1u);
        G_ACQ_STATE->consumed_mask = 0u;
        clear_destination(*transaction_token);
        *transaction_token = 0u;
        return VEGA_ACQ_RESULT_MISSING_INPUT;
    }
    if (recipe->item2 != 0u)
        G_ACQ_STATE->consumed_mask = 3u;
    return VEGA_ACQ_RESULT_SUCCESS;
}

void VegaAcqEngine_RollbackOperation(const VegaAcqEventDef *event_def,
                                     u32 transaction_token)
{
    const AcqFossilRecipe *recipe;
    u32 kind = transaction_token & ACQ_TOKEN_KIND_MASK;
    if (kind == ACQ_TOKEN_PARTY || kind == ACQ_TOKEN_BOX)
        clear_destination(transaction_token);
    else if (kind == ACQ_TOKEN_ITEM)
        (void)FN_REMOVE_BAG((u16)(transaction_token & 0xFFFFu), 1u);
    if (event_def != NULL && event_def->mode == VEGA_ACQ_MODE_FOSSIL
        && transaction_token != 0u) {
        recipe = fossil_recipe(event_def);
        if (recipe != NULL) {
            (void)FN_ADD_BAG(recipe->item1, 1u);
            if (recipe->item2 != 0u)
                (void)FN_ADD_BAG(recipe->item2, 1u);
        }
    }
    G_ACQ_STATE->consumed_mask = 0u;
}

void VegaAcqEngine_FinalizeOperation(const VegaAcqEventDef *event_def,
                                     u32 transaction_token)
{
    (void)event_def;
    (void)transaction_token;
    G_ACQ_STATE->consumed_mask = 0u;
}

u8 VegaAcqEngine_IsOperationDurable(const VegaAcqEventDef *event_def,
                                    u32 transaction_token)
{
    u32 kind;
    if (event_def == NULL)
        return 0u;
    if (event_def->mode == VEGA_ACQ_MODE_CAPTURE)
        return VegaAcqEngine_IsSpeciesRegistered(event_def->species_id);
    kind = transaction_token & ACQ_TOKEN_KIND_MASK;
    if (kind == ACQ_TOKEN_PARTY || kind == ACQ_TOKEN_BOX)
        return (u8)(destination_species(transaction_token)
                    == event_def->species_id);
    if (kind == ACQ_TOKEN_ITEM)
        return FN_CHECK_BAG((u16)(transaction_token & 0xFFFFu), 1u);
    return (u8)(event_def->mode == VEGA_ACQ_MODE_EVOLUTION_SUPPORT
                || event_def->mode == VEGA_ACQ_MODE_SERVICE
                || event_def->mode == VEGA_ACQ_MODE_TRADE_EMULATOR);
}

void VegaAcqEngine_FinalizeInMemory(void)
{
    if (!save_structurally_ready())
        return;
    VegaAcqSaveFinalize(save_block());
    VegaSaveFinalize(gVegaModernSaveData);
}

u8 VegaAcqEngine_PersistAll(void)
{
    VegaAcqPendingTransaction *pending;
    if (!save_structurally_ready())
        return 0u;
    VegaAcqEngine_FinalizeInMemory();
    pending = &save_block()->pending;
    if (pending->magic == VEGA_ACQ_PENDING_MAGIC) {
        if (pending->phase == VEGA_ACQ_PHASE_PREPARED
            || pending->phase == VEGA_ACQ_PHASE_CAPTURE_ACTIVE)
            return persist_save_sector();
        /* Write-ahead journal: a reset can only observe an operation after its
         * pending record is durable.  The recovery path then verifies party/PC. */
        if (!persist_save_sector())
            return 0u;
        if (!persist_standard_save())
            return 0u;
        /* The base normal-save path does not retain the dedicated expansion
         * sector on every save mode, so restore the same journal image. */
        VegaAcqEngine_FinalizeInMemory();
        return persist_save_sector();
    }
    /* Commit/rollback: make party, PC, bag and Pokedex durable before clearing
     * the journal or publishing claim/collection bits in sector 31. */
    if (!persist_standard_save())
        return 0u;
    return persist_save_sector();
}

ACQ_EXPORT(VegaAcq_RegisterHatchedPartyMon)
u16 VegaAcq_RegisterHatchedPartyMon(void)
{
    u16 slot = *G_SPECIAL_VAR_8004;
    u16 species;
    u8 old_registered;
    if (slot >= ACQ_PARTY_SIZE || slot >= *G_PLAYER_PARTY_COUNT)
        return VEGA_ACQ_RESULT_INVALID_SELECTION;
    species = (u16)FN_GET_MON_DATA(
        G_PLAYER_PARTY + (u32)slot * ACQ_MON_SIZE,
        ACQ_MON_DATA_SPECIES, NULL);
    if (species == 0u || species >= ACQ_SPECIES_COUNT || !ensure_save())
        return VEGA_ACQ_RESULT_ENGINE_REJECTED;
    old_registered = VegaAcqEngine_IsSpeciesRegistered(species);
    if (old_registered)
        return VEGA_ACQ_RESULT_SUCCESS;
    if (!VegaAcqEngine_SetSpeciesRegistered(species, 1u))
        return VEGA_ACQ_RESULT_ENGINE_REJECTED;
    VegaAcqEngine_FinalizeInMemory();
    /* The collection ledger is the form-aware source of truth.  Persist it
     * first, then persist the standard Pokedex state.  A later normal save can
     * repeat the latter without risking loss of the collection registration. */
    if (!persist_save_sector()) {
        (void)VegaAcqEngine_SetSpeciesRegistered(species, old_registered);
        VegaAcqEngine_FinalizeInMemory();
        return VEGA_ACQ_RESULT_PERSIST_FAILED;
    }
    if (!persist_standard_save())
        return VEGA_ACQ_RESULT_PERSIST_FAILED;
    VegaAcqEngine_FinalizeInMemory();
    return persist_save_sector()
        ? VEGA_ACQ_RESULT_SUCCESS : VEGA_ACQ_RESULT_PERSIST_FAILED;
}

static u8 event_available(u16 event_index, u8 *saw_unlocked)
{
    const VegaAcqEventDef *event_def;
    if (event_index >= VEGA_ACQ_EVENT_COUNT)
        return 0u;
    event_def = &gVegaAcqEventDefs[event_index];
    if (!VegaAcqEngine_IsUnlockSatisfied(event_def->unlock_key)
        || !VegaAcqEngine_IsEventConditionSatisfied(event_def))
        return 0u;
    *saw_unlocked = 1u;
    if ((event_def->policy_flags & VEGA_ACQ_POLICY_REQUIRE_REGISTERED) != 0u
        && !VegaAcqEngine_IsSpeciesRegistered(event_def->species_id))
        return 0u;
    if (event_def->max_claims != 0u
        && VegaAcqEngine_GetClaimCount(event_def) >= event_def->max_claims)
        return 0u;
    return 1u;
}

static void close_window(u8 task_id)
{
    u8 window_id = (u8)G_TASKS[task_id].data[0];
    if (window_id != ACQ_WINDOW_INVALID) {
        FN_CLEAR_STD_WINDOW_FRAME(window_id, 1u);
        FN_REMOVE_WINDOW(window_id);
        FN_SCHEDULE_BG_COPY(0u);
        G_TASKS[task_id].data[0] = ACQ_WINDOW_INVALID;
    }
}

static u8 page_row_count(void)
{
    u8 first = (u8)(G_ACQ_STATE->page * ACQ_MENU_PAGE_SIZE);
    u8 remaining = first < G_ACQ_STATE->eligible_count
        ? (u8)(G_ACQ_STATE->eligible_count - first) : 0u;
    return remaining > ACQ_MENU_PAGE_SIZE ? ACQ_MENU_PAGE_SIZE : remaining;
}

static void name_for_event(u8 *destination, u16 event_index)
{
    const VegaAcqEventDef *event_def = &gVegaAcqEventDefs[event_index];
    if (event_def->species_id != 0u) {
        FN_GET_SPECIES_NAME(destination, event_def->species_id);
    } else if (event_def->mode == VEGA_ACQ_MODE_TRADE_EMULATOR) {
        copy_text(destination, sTextLinkCable);
    } else {
        copy_text(destination, sTextEcologyRadar);
    }
}

static u8 render_menu(u8 task_id)
{
    struct WindowTemplate template;
    u8 first = (u8)(G_ACQ_STATE->page * ACQ_MENU_PAGE_SIZE);
    u8 rows = page_row_count();
    u8 has_next = (u8)(first + rows < G_ACQ_STATE->eligible_count);
    u8 menu_count = (u8)(rows + 1u);
    u8 index;
    u8 window_id;

    template.bg = 0u;
    template.tilemap_left = 11u;
    template.tilemap_top = 1u;
    template.width = 18u;
    template.height = (u8)(menu_count * 2u + 2u);
    template.palette_num = 15u;
    template.base_block = FN_GET_STD_WINDOW_BASE_TILE();
    window_id = (u8)FN_ADD_WINDOW(&template);
    if (window_id == ACQ_WINDOW_INVALID)
        return 0u;
    G_TASKS[task_id].data[0] = window_id;
    G_ACQ_STATE->window_id = window_id;
    FN_FILL_WINDOW_PIXEL_BUFFER(window_id, 0x11u);
    FN_DRAW_STD_WINDOW_FRAME(window_id, 0u);
    FN_PUT_WINDOW_TILEMAP(window_id);
    for (index = 0u; index < rows; ++index) {
        u16 event_index = G_ACQ_STATE->eligible[first + index];
        if (event_index == ACQ_LOCAL_MINE)
            copy_text(G_ACQ_STATE->names[index], sTextMine);
        else
            name_for_event(G_ACQ_STATE->names[index], event_index);
        FN_ADD_TEXT_PRINTER(window_id, 2u, G_ACQ_STATE->names[index],
                            8u, (u8)(1u + index * 16u), 0u, NULL);
    }
    copy_text(G_ACQ_STATE->names[rows], has_next ? sTextNext : sTextCancel);
    FN_ADD_TEXT_PRINTER(window_id, 2u, G_ACQ_STATE->names[rows],
                        8u, (u8)(1u + rows * 16u), 0u, NULL);
    FN_MENU_INIT_CURSOR(window_id, 2u, 0u, 1u, 16u, menu_count, 0u);
    FN_COPY_WINDOW_TO_VRAM(window_id, ACQ_COPYWIN_BOTH);
    FN_SCHEDULE_BG_COPY(0u);
    return 1u;
}

ACQ_EXPORT(VegaAcq_MineFossil)
u16 VegaAcq_MineFossil(void)
{
    u8 index;
    u16 item = 0u;
    for (index = 0u;
         index < (u8)(sizeof(sMineableFossils) / sizeof(sMineableFossils[0]));
         ++index) {
        if (!FN_CHECK_BAG(sMineableFossils[index], 1u)) {
            item = sMineableFossils[index];
            break;
        }
    }
    if (item == 0u) {
        index = (u8)(((u32)FN_RANDOM()
            * (sizeof(sMineableFossils) / sizeof(sMineableFossils[0]))) >> 16);
        item = sMineableFossils[index];
    }
    if (!FN_ADD_BAG(item, 1u))
        return VEGA_ACQ_RESULT_ENGINE_REJECTED;
    if (!VegaAcqEngine_PersistAll()) {
        (void)FN_REMOVE_BAG(item, 1u);
        return VEGA_ACQ_RESULT_PERSIST_FAILED;
    }
    return VEGA_ACQ_RESULT_SUCCESS;
}

static void finish_menu(u8 task_id, u16 event_index, u16 result,
                        u8 resume_script)
{
    close_window(task_id);
    FN_DESTROY_TASK(task_id);
    FN_PLAY_SE(ACQ_SE_SELECT);
    VegaAcqEngine_ShowResult(event_index, result);
    if (resume_script)
        FN_ENABLE_BOTH_SCRIPT_CONTEXTS();
}

static void Task_HandleAcquisitionMenu(u8 task_id)
{
    s8 choice = FN_MENU_PROCESS_INPUT();
    u8 first;
    u8 rows;
    u8 has_next;
    u16 selected;
    u16 result;
    if (choice == ACQ_MENU_NOTHING)
        return;
    first = (u8)(G_ACQ_STATE->page * ACQ_MENU_PAGE_SIZE);
    rows = page_row_count();
    has_next = (u8)(first + rows < G_ACQ_STATE->eligible_count);
    if (choice == ACQ_MENU_B || choice < 0) {
        finish_menu(task_id, VEGA_ACQ_NO_INDEX,
                    G_ACQ_STATE->eligible_count == 0u
                        ? G_ACQ_STATE->empty_result
                        : VEGA_ACQ_RESULT_CANCELLED, 1u);
        return;
    }
    if ((u8)choice == rows) {
        if (has_next) {
            close_window(task_id);
            ++G_ACQ_STATE->page;
            if (!render_menu(task_id))
                finish_menu(task_id, VEGA_ACQ_NO_INDEX,
                            VEGA_ACQ_RESULT_ENGINE_REJECTED, 1u);
        } else {
            finish_menu(task_id, VEGA_ACQ_NO_INDEX,
                        G_ACQ_STATE->eligible_count == 0u
                            ? G_ACQ_STATE->empty_result
                            : VEGA_ACQ_RESULT_CANCELLED, 1u);
        }
        return;
    }
    if (choice < 0 || (u8)choice >= rows) {
        finish_menu(task_id, VEGA_ACQ_NO_INDEX,
                    VEGA_ACQ_RESULT_INVALID_SELECTION, 1u);
        return;
    }
    selected = G_ACQ_STATE->eligible[first + (u8)choice];
    close_window(task_id);
    FN_DESTROY_TASK(task_id);
    FN_PLAY_SE(ACQ_SE_SELECT);
    result = selected == ACQ_LOCAL_MINE
        ? VegaAcq_MineFossil() : VegaAcq_Begin(selected);
    VegaAcqEngine_ShowResult(selected, result);
    if (result != VEGA_ACQ_RESULT_BATTLE_STARTED)
        FN_ENABLE_BOTH_SCRIPT_CONTEXTS();
}

u16 VegaAcqEngine_SelectHostEvent(const u16 *event_indices, u16 event_count)
{
    u16 offset;
    u8 task_id;
    u8 saw_unlocked = 0u;
    u8 is_mining_host;
    if (!ensure_save() || event_indices == NULL || event_count == 0u)
        return VEGA_ACQ_NO_INDEX;
    if (save_block()->pending.magic != 0u)
        (void)VegaAcq_RecoverPending();
    clear_bytes(G_ACQ_STATE, sizeof(*G_ACQ_STATE));
    G_ACQ_STATE->window_id = ACQ_WINDOW_INVALID;
    G_ACQ_STATE->last_result = ACQ_RESULT_NOT_SET;
    G_ACQ_STATE->last_event = VEGA_ACQ_NO_INDEX;
    is_mining_host = (u8)(
        event_indices == &gVegaAcqHostEventIndices[
            gVegaAcqHostDefs[5].first_event_index]);
    if (is_mining_host)
        G_ACQ_STATE->eligible[G_ACQ_STATE->eligible_count++] = ACQ_LOCAL_MINE;
    for (offset = 0u; offset < event_count; ++offset) {
        u16 event_index = event_indices[offset];
        if (event_available(event_index, &saw_unlocked)
            && G_ACQ_STATE->eligible_count
                < (u8)(sizeof(G_ACQ_STATE->eligible)
                       / sizeof(G_ACQ_STATE->eligible[0])))
            G_ACQ_STATE->eligible[G_ACQ_STATE->eligible_count++] = event_index;
    }
    G_ACQ_STATE->empty_result = saw_unlocked
        ? VEGA_ACQ_RESULT_ALREADY_CLAIMED : VEGA_ACQ_RESULT_LOCKED;
    task_id = FN_CREATE_TASK(Task_HandleAcquisitionMenu, 0x50u);
    if (task_id >= ACQ_NUM_TASKS)
        return VEGA_ACQ_NO_INDEX;
    G_TASKS[task_id].data[0] = ACQ_WINDOW_INVALID;
    if (!render_menu(task_id)) {
        FN_DESTROY_TASK(task_id);
        return VEGA_ACQ_NO_INDEX;
    }
    *G_SPECIAL_RESULT = VEGA_ACQ_RESULT_BUSY;
    FN_SCRIPT_CONTEXT2_ENABLE();
    return VEGA_ACQ_ASYNC_SELECTION;
}

void VegaAcqEngine_ShowResult(u16 event_index, u16 result)
{
    G_ACQ_STATE->last_event = event_index;
    G_ACQ_STATE->last_result = result;
    *G_SPECIAL_RESULT = result;
}

ACQ_EXPORT(VegaAcq_PostHost)
void VegaAcq_PostHost(void)
{
    VegaAcqPendingTransaction *pending = VegaAcqEngine_GetPending();
    u16 result = G_ACQ_STATE->last_result;
    if (pending != NULL && pending->magic == VEGA_ACQ_PENDING_MAGIC
        && pending->phase == VEGA_ACQ_PHASE_CAPTURE_ACTIVE) {
        u8 outcome = *G_BATTLE_OUTCOME;
        u16 mapped;
        if (outcome == ACQ_BATTLE_CAUGHT)
            mapped = VEGA_ACQ_BATTLE_CAUGHT;
        else if (outcome == ACQ_BATTLE_WON)
            mapped = VEGA_ACQ_BATTLE_DEFEATED;
        else if (outcome == ACQ_BATTLE_RAN
                 || outcome == ACQ_BATTLE_PLAYER_TELEPORTED
                 || outcome == ACQ_BATTLE_MON_FLED
                 || outcome == ACQ_BATTLE_MON_TELEPORTED)
            mapped = VEGA_ACQ_BATTLE_ESCAPED;
        else
            mapped = VEGA_ACQ_BATTLE_ABORTED;
        result = VegaAcq_ResolveBattle(mapped);
        G_ACQ_STATE->last_result = result;
    }
    if (result == ACQ_RESULT_NOT_SET)
        result = VEGA_ACQ_RESULT_CANCELLED;
    *G_SPECIAL_RESULT = result;
}
