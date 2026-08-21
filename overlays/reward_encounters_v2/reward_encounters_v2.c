/*
 * T24 Reward Encounters V2 production runtime.
 *
 * Durable state is deliberately limited to the T08 encounter credits,
 * Factory BP/claim ledger and the single VegaPendingEncounter.  The T24 RAM
 * block contains only menu state, a battle-local before image descriptor and
 * callback de-duplication.  The complete 0x800-byte ledger before image uses
 * the already reserved T08 rollback buffer.
 */

#include "reward_encounters_v2.h"

#include <stddef.h>
#include <stdint.h>

#include "../save_migration/save_migration.h"

typedef uint8_t u8;
typedef int8_t s8;
typedef uint16_t u16;
typedef int16_t s16;
typedef uint32_t u32;

typedef struct RewardEncounterServiceConfig {
    u8 tier;
    u8 credit_kind;
    u8 unlock_kind;
    u8 pool;
    u16 credit_cost;
    u16 bp_price;
} RewardEncounterServiceConfig;

typedef struct RewardEncounterPoolEntry {
    u16 species;
    u8 level_min;
    u8 level_max;
    u8 iv_floor;
    u8 hidden_ability_rate;
    u8 type1;
    u8 type2;
    u16 ability1;
    u16 ability2;
    u16 hidden_ability;
    u8 fingerprint[16];
} RewardEncounterPoolEntry;

#include "reward_encounters_v2_generated.h"

#define PTR(type, address) ((type)(uintptr_t)(address))
#define REWARD_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

_Static_assert(REWARD_ENCOUNTERS_GENERATED_SCHEMA_VERSION == 2u,
               "Reward Encounters generated schema differs");
_Static_assert(REWARD_ENCOUNTERS_SERVICE_COUNT == 4u,
               "Reward Encounter service count differs");
_Static_assert(REWARD_ENCOUNTERS_ENTRY_COUNT == 24u,
               "Reward Encounter pool count differs");
_Static_assert(REWARD_ENCOUNTERS_DIALOGUE_COUNT == 56u,
               "Reward Encounter dialogue count differs");
_Static_assert(REWARD_ENCOUNTERS_SOURCE_COUNT == 10u,
               "Reward Encounter source count differs");

enum {
    REWARD_STATE_MAGIC = 0x32564552u, /* "REV2" */
    REWARD_ENCOUNTER_KIND = 0x52u,
    REWARD_BATTLE_NO_EXP_EV = 0x08000000u,
    REWARD_BATTLE_OUTCOME_CAUGHT = 7u,
    REWARD_PARTY_CAPACITY = 6u,
    REWARD_PARTY_MON_SIZE = 100u,
    REWARD_BOX_COUNT = 14u,
    REWARD_BOX_CAPACITY = 30u,
    REWARD_MON_DATA_PERSONALITY = 0u,
    REWARD_MON_DATA_SPECIES = 11u,
    REWARD_MON_DATA_HELD_ITEM = 12u,
    REWARD_MON_DATA_HP_IV = 39u,
    REWARD_MON_DATA_ALT_ABILITY = 46u,
    REWARD_MON_DATA_SPECIES2 = 65u,
    REWARD_POKEDEX_GET_CAUGHT = 1u,
    REWARD_SAVE_BLOCK1_MONEY_OFFSET = 0x290u,
    REWARD_SAVE_BLOCK2_OWNED_OFFSET = 0x28u,
    REWARD_FLAG_BADGE_1 = 0x0820u,
    REWARD_MENU_TIER = 0u,
    REWARD_MENU_PAYMENT = 1u,
    REWARD_MENU_CONFIRM = 2u,
    REWARD_MENU_RESUME = 3u,
    REWARD_MENU_CODE_VOUCHER = 3u,
    REWARD_MENU_CODE_YES = 4u,
    REWARD_MENU_CODE_CANCEL = 0xFFu,
    REWARD_MENU_NOTHING = -2,
    REWARD_MENU_B = -1,
    REWARD_WINDOW_INVALID = 0xFFu,
    REWARD_NUM_TASKS = 16u,
    REWARD_COPYWIN_BOTH = 3u,
    REWARD_SE_SELECT = 5u,
    REWARD_SOURCE_FISHING = 0u,
    REWARD_SOURCE_ECOLOGY = 1u,
    REWARD_RESEARCH_ACTIVITY_FISHING = 0u,
    REWARD_RESEARCH_ACTIVITY_ECOLOGY = 1u,
    REWARD_RESEARCH_MAGIC = 0x31564552u,
    REWARD_TERA_FIELD_OFFSET = 0x11u,
    REWARD_HIDDEN_ABILITY_FIELD_OFFSET = 0x47u,
    REWARD_HIDDEN_ABILITY_MASK = 0x10u
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

typedef struct __attribute__((packed)) RewardEncountersV2State {
    u32 magic;
    u32 magic_inverse;
    u32 test_rng;
    u32 test_caught_mask;
    u32 last_source_token;
    u32 battle_type_before;
    u32 side_effect_hash_before;
    u8 money_before[4];
    u16 held_before[REWARD_PARTY_CAPACITY];
    u16 battle_species;
    u16 last_result;
    u8 test_mode;
    u8 persistence_fault;
    u8 capacity_override;
    u8 unlock_all;
    u8 battle_active;
    u8 party_count_before;
    u8 caught_before;
    u8 dexnav_before;
    u8 window_id;
    u8 menu_active;
    u8 menu_stage;
    u8 selected_tier;
    u8 selected_payment;
    u8 menu_count;
    u8 launch_count;
    u8 test_newly_caught;
    u8 menu_codes[5];
    u8 alignment_pad[3];
    u8 balance_text[40];
    u8 row_text[5][24];
    u8 reserved[24];
} RewardEncountersV2State;

typedef struct __attribute__((packed)) ResearchEconomyPrefix {
    u32 magic;
    u32 wild_pid;
    u16 wild_species;
    u16 game_initial_payout;
    u16 game_pre_coins;
    u16 game_last_remaining;
    u16 last_result;
    u16 selected_catalog;
    u16 test_bag_capacity;
    u8 wild_activity;
    u8 wild_pre_caught;
    u8 wild_armed;
} ResearchEconomyPrefix;

_Static_assert(sizeof(struct Task) == 40u, "FireRed Task ABI differs");
_Static_assert(sizeof(struct WindowTemplate) == 8u,
               "FireRed Window ABI differs");
_Static_assert(sizeof(RewardEncountersV2State)
                   == VEGA_REWARD_ENCOUNTER_VOLATILE_SIZE,
               "Reward Encounter volatile reservation differs");
_Static_assert(sizeof(VegaPendingEncounter) == 46u,
               "Reward Encounter pending ABI differs");
_Static_assert(offsetof(VegaModernSaveData, encounter_credits) == 0x684u,
               "typed credit offset differs");
_Static_assert(offsetof(VegaModernSaveData, pending_encounter) == 0x694u,
               "pending encounter offset differs");

typedef void (*VoidFn)(void);
typedef u8 (*U8ArgU8Fn)(u8);
typedef u16 (*RandomFn)(void);
typedef u8 (*FlagGetFn)(u16);
typedef u32 (*GetMonDataFn)(const void *, int, u8 *);
typedef void (*SetMonDataFn)(void *, int, const void *);
typedef void (*CreateMonFn)(void *, u16, u8, u8, u8, u32, u8, u32);
typedef void (*CalculateMonStatsFn)(void *);
typedef u16 (*SpeciesToNationalFn)(u16);
typedef u8 (*GetSetPokedexFn)(u16, u8);
typedef u32 (*GetBoxMonDataAtFn)(u8, u8, u32);
typedef void (*ZeroBoxMonAtFn)(u8, u8);
typedef void (*TaskFunc)(u8);
typedef u8 (*CreateTaskFn)(TaskFunc, u8);
typedef void (*TaskIdFn)(u8);
typedef u16 (*AddWindowFn)(const struct WindowTemplate *);
typedef void (*WindowU8Fn)(u8);
typedef void (*WindowPairFn)(u8, u8);
typedef void (*TextPrinterFn)(u8, u8, const u8 *, u8, u8, u8, void *);
typedef u8 (*MenuInitCursorFn)(u8, u8, u8, u8, u8, u8, u8);
typedef s8 (*MenuInputFn)(void);
typedef u16 (*GetBaseTileFn)(void);
typedef void (*PlaySeFn)(u16);

#define G_STATE PTR(volatile RewardEncountersV2State *, \
                    VEGA_REWARD_ENCOUNTER_VOLATILE_ADDRESS)
#define G_RESEARCH PTR(volatile ResearchEconomyPrefix *, \
                       REWARD_ENCOUNTERS_RESEARCH_VOLATILE_ADDRESS)
#define G_LEDGER PTR(VegaModernSaveData *, VEGA_SAVE_EWRAM_ADDRESS)
#define G_ROLLBACK PTR(VegaModernSaveData *, VEGA_SAVE_ROLLBACK_ADDRESS)
#define G_PLAYER_PARTY PTR(u8 *, 0x020241E4u)
#define G_ENEMY_PARTY PTR(u8 *, 0x02023F8Cu)
#define G_PARTY_COUNT PTR(volatile u8 *, 0x02023F89u)
#define G_BATTLE_OUTCOME PTR(volatile u8 *, 0x02023DEAu)
#define G_BATTLE_TYPE_FLAGS PTR(volatile u32 *, 0x02022AACu)
#define G_DEXNAV_CHAIN PTR(volatile u8 *, 0x0203DFC9u)
#define G_SPECIAL_RESULT PTR(volatile u16 *, 0x02037004u)
#define G_SPECIAL_MON_BOX_ID PTR(volatile u16 *, 0x0203700Au)
#define G_SPECIAL_MON_BOX_POS PTR(volatile u16 *, 0x0203700Cu)
#define G_TASKS PTR(struct Task *, 0x030050D0u)
#define G_SAVE_BLOCK1_PTR PTR(u8 * volatile *, 0x03005048u)
#define G_SAVE_BLOCK2_PTR PTR(u8 * volatile *, 0x0300504Cu)
#define FN_TRY_SAVING_DATA PTR(U8ArgU8Fn, REWARD_ENGINE_TRY_SAVING_DATA)
#define FN_RANDOM PTR(RandomFn, REWARD_ENGINE_RANDOM)
#define FN_FLAG_GET PTR(FlagGetFn, 0x0806DEC5u)
#define FN_GET_MON_DATA PTR(GetMonDataFn, REWARD_ENGINE_GET_MON_DATA)
#define FN_SET_MON_DATA PTR(SetMonDataFn, REWARD_ENGINE_SET_MON_DATA)
#define FN_CREATE_MON PTR(CreateMonFn, REWARD_ENGINE_CREATE_MON)
#define FN_CALCULATE_MON_STATS \
    PTR(CalculateMonStatsFn, REWARD_ENGINE_CALCULATE_MON_STATS)
#define FN_SPECIES_TO_NATIONAL \
    PTR(SpeciesToNationalFn, REWARD_ENGINE_SPECIES_TO_NATIONAL)
#define FN_GET_SET_POKEDEX PTR(GetSetPokedexFn, REWARD_ENGINE_GET_SET_POKEDEX)
#define FN_GET_BOX_MON_DATA_AT \
    PTR(GetBoxMonDataAtFn, REWARD_ENGINE_GET_BOX_MON_DATA_AT)
#define FN_ZERO_BOX_MON_AT PTR(ZeroBoxMonAtFn, REWARD_ENGINE_ZERO_BOX_MON_AT)
#define FN_START_SCRIPTED_WILD_BATTLE \
    PTR(VoidFn, REWARD_ENGINE_START_SCRIPTED_WILD_BATTLE)
#define FN_RESEARCH_WILD_END \
    PTR(VoidFn, REWARD_DELEGATE_RESEARCH_WILD_END)
#define FN_CREATE_TASK PTR(CreateTaskFn, 0x08076BB5u)
#define FN_DESTROY_TASK PTR(TaskIdFn, 0x08076CA1u)
#define FN_SCRIPT_CONTEXT2_ENABLE PTR(VoidFn, 0x08069201u)
#define FN_ENABLE_BOTH_SCRIPT_CONTEXTS PTR(VoidFn, 0x080693F5u)
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

static void clear_bytes(volatile void *destination, u32 size)
{
    volatile u8 *out = (volatile u8 *)destination;
    u32 index;
    for (index = 0u; index < size; ++index)
        out[index] = 0u;
}

static void copy_bytes(volatile void *destination,
                       const volatile void *source, u32 size)
{
    volatile u8 *out = (volatile u8 *)destination;
    const volatile u8 *in = (const volatile u8 *)source;
    u32 index;
    for (index = 0u; index < size; ++index)
        out[index] = in[index];
}

static u16 set_result(u16 result)
{
    G_STATE->last_result = result;
    *G_SPECIAL_RESULT = result;
    return result;
}

static void ensure_state(void)
{
    if (G_STATE->magic == REWARD_STATE_MAGIC
        && G_STATE->magic_inverse == (u32)~(u32)REWARD_STATE_MAGIC)
        return;
    clear_bytes(G_STATE, sizeof(*G_STATE));
    G_STATE->magic = REWARD_STATE_MAGIC;
    G_STATE->magic_inverse = ~REWARD_STATE_MAGIC;
    G_STATE->test_rng = 0x6D2B79F5u;
    G_STATE->capacity_override = 0xFFu;
    G_STATE->window_id = REWARD_WINDOW_INVALID;
    G_STATE->selected_tier = 0xFFu;
    G_STATE->selected_payment = 0xFFu;
    G_STATE->last_result = VEGA_REWARD_EFFECTLESS;
}

static u8 ledger_valid(void)
{
    return (u8)(VegaSaveValidate(G_LEDGER, VEGA_SAVE_LEDGER_SIZE)
                == VEGA_SAVE_OK);
}

static u32 random32(void)
{
    u32 value;
    ensure_state();
    if (!G_STATE->test_mode)
        return (u32)FN_RANDOM() | ((u32)FN_RANDOM() << 16);
    value = G_STATE->test_rng;
    value ^= value << 13;
    value ^= value >> 17;
    value ^= value << 5;
    if (value == 0u)
        value = 0xA341316Cu;
    G_STATE->test_rng = value;
    return value;
}

static u8 persist_current(void)
{
    ensure_state();
    VegaSaveFinalize(G_LEDGER);
    if (G_STATE->persistence_fault) {
        G_STATE->persistence_fault = 0u;
        return 0u;
    }
    if (G_STATE->test_mode)
        return 1u;
    /* Stage40のTrySavingData入口はQoL save adapterであり、標準save成功後に
     * modern ledger sector 31も一度だけ書く。ここでsectorを重ねて書かない。 */
    return (u8)(FN_TRY_SAVING_DATA(0u) == 1u);
}

static int persist_callback(const VegaModernSaveData *data, size_t size,
                            void *context)
{
    (void)data;
    (void)context;
    if (size != VEGA_SAVE_LEDGER_SIZE)
        return 0;
    return persist_current() != 0u;
}

static void compensate_after_failed_persist(void)
{
    if (!G_STATE->test_mode)
        (void)persist_current();
}

static const RewardEncounterServiceConfig *service_for(u16 tier)
{
    if (tier >= REWARD_ENCOUNTERS_SERVICE_COUNT)
        return (const RewardEncounterServiceConfig *)0;
    return &gRewardEncounterServices[tier];
}

static u8 service_unlocked(const RewardEncounterServiceConfig *service)
{
    if (G_STATE->unlock_all)
        return 1u;
    if (service->unlock_kind == REWARD_UNLOCK_KANTO_EARLY)
        return G_LEDGER->kanto_travel_unlocked != 0u;
    if (service->unlock_kind == REWARD_UNLOCK_RAID_HIGH)
        return (u8)(G_LEDGER->vega_hall_of_fame
                    && (G_LEDGER->kanto_certifications & 0x08u));
    return 0u;
}

static u8 source_unlocked(u8 activity)
{
    if (G_STATE->unlock_all)
        return 1u;
    if (activity == REWARD_SOURCE_FISHING)
        return FN_FLAG_GET(REWARD_FLAG_BADGE_1) != 0u;
    if (activity == REWARD_SOURCE_ECOLOGY)
        return G_LEDGER->vega_hall_of_fame != 0u;
    return 0u;
}

static u8 has_capacity(void)
{
    u8 box;
    u8 position;
    if (G_STATE->test_mode && G_STATE->capacity_override != 0xFFu)
        return G_STATE->capacity_override != 0u;
    if (*G_PARTY_COUNT < REWARD_PARTY_CAPACITY)
        return 1u;
    for (box = 0u; box < REWARD_BOX_COUNT; ++box) {
        for (position = 0u; position < REWARD_BOX_CAPACITY; ++position) {
            if (FN_GET_BOX_MON_DATA_AT(box, position,
                                       REWARD_MON_DATA_SPECIES) == 0u)
                return 1u;
        }
    }
    return 0u;
}

static u8 entry_index_for_species(u16 species)
{
    u8 index;
    for (index = 0u; index < REWARD_ENCOUNTERS_ENTRY_COUNT; ++index) {
        if (gRewardEncounterPool[index].species == species)
            return index;
    }
    return 0xFFu;
}

static u8 dex_caught_entry(u8 index)
{
    u16 national;
    if (index >= REWARD_ENCOUNTERS_ENTRY_COUNT)
        return 0u;
    if (G_STATE->test_mode)
        return (u8)((G_STATE->test_caught_mask >> index) & 1u);
    national = FN_SPECIES_TO_NATIONAL(gRewardEncounterPool[index].species);
    return national != 0u
        && FN_GET_SET_POKEDEX(national, REWARD_POKEDEX_GET_CAUGHT) != 0u;
}

static u8 dex_caught_species(u16 species)
{
    u8 index = entry_index_for_species(species);
    u16 national;
    if (G_STATE->test_mode && index != 0xFFu)
        return dex_caught_entry(index);
    national = FN_SPECIES_TO_NATIONAL(species);
    return national != 0u
        && FN_GET_SET_POKEDEX(national, REWARD_POKEDEX_GET_CAUGHT) != 0u;
}

static u8 choose_entry(u8 tier)
{
    u8 base = (u8)(tier * REWARD_ENCOUNTERS_POOL_SIZE);
    u8 uncaught[REWARD_ENCOUNTERS_POOL_SIZE];
    u8 uncaught_count = 0u;
    u8 index;
    u8 attempt;
    for (index = 0u; index < REWARD_ENCOUNTERS_POOL_SIZE; ++index) {
        if (!dex_caught_entry((u8)(base + index)))
            uncaught[uncaught_count++] = (u8)(base + index);
    }
    if (uncaught_count == 0u)
        return (u8)(base + random32() % REWARD_ENCOUNTERS_POOL_SIZE);
    for (attempt = 0u; attempt < 10u; ++attempt) {
        index = (u8)(base + random32() % REWARD_ENCOUNTERS_POOL_SIZE);
        if (!dex_caught_entry(index))
            return index;
    }
    return uncaught[random32() % uncaught_count];
}

static u32 player_trainer_id(void)
{
    const volatile u8 *save;
    if (G_STATE->test_mode)
        return 0x12345678u;
    save = *G_SAVE_BLOCK2_PTR;
    if (save == (const volatile u8 *)0)
        return 0u;
    return (u32)save[0x0Au] | ((u32)save[0x0Bu] << 8)
        | ((u32)save[0x0Cu] << 16) | ((u32)save[0x0Du] << 24);
}

static void generate_request(u8 tier, VegaEncounterRequest *request)
{
    const RewardEncounterServiceConfig *service = &gRewardEncounterServices[tier];
    u8 entry_index = choose_entry(tier);
    const RewardEncounterPoolEntry *entry = &gRewardEncounterPool[entry_index];
    u8 order[6] = {0u, 1u, 2u, 3u, 4u, 5u};
    u8 index;
    u8 swap;
    u32 pid;
    u32 trainer;
    clear_bytes(request, sizeof(*request));
    request->encounter_kind = REWARD_ENCOUNTER_KIND;
    request->credit_kind = service->credit_kind;
    request->cost = 1u;
    request->pool = tier;
    request->species = entry->species;
    request->form = 0u;
    request->level = (u8)(entry->level_min
        + random32() % (u32)(entry->level_max - entry->level_min + 1u));
    pid = random32();
    request->personality = pid;
    request->nature = (u8)(pid % 25u);
    for (index = 0u; index < 6u; ++index) {
        request->ivs[index] = (u8)(random32() & 31u);
        swap = (u8)(index + random32() % (u32)(6u - index));
        {
            u8 temporary = order[index];
            order[index] = order[swap];
            order[swap] = temporary;
        }
    }
    for (index = 0u; index < entry->iv_floor; ++index)
        request->ivs[order[index]] = 31u;
    request->ability = (u8)(entry->hidden_ability != 0u
        && random32() % 100u < entry->hidden_ability_rate ? 2u
        : (entry->ability2 != 0u && entry->ability2 != entry->ability1
           ? random32() & 1u : 0u));
    request->tera_type = (random32() & 1u) ? entry->type2 : entry->type1;
    trainer = player_trainer_id();
    request->shiny = (u8)((((pid >> 16) ^ (pid & 0xFFFFu)
                             ^ (trainer >> 16) ^ (trainer & 0xFFFFu))
                            & 0xFFFFu) < 8u);
    request->generator_version = VEGA_REWARD_ENCOUNTER_GENERATOR_VERSION;
    copy_bytes(request->generator_fingerprint, entry->fingerprint,
               sizeof(request->generator_fingerprint));
}

static void fill_pending(const VegaEncounterRequest *request)
{
    VegaPendingEncounter *pending = &G_LEDGER->pending_encounter;
    clear_bytes(pending, sizeof(*pending));
    pending->valid = 1u;
    pending->encounter_kind = request->encounter_kind;
    pending->pool = request->pool;
    pending->species = request->species;
    pending->form = request->form;
    pending->level = request->level;
    pending->nature = request->nature;
    pending->ability = request->ability;
    pending->shiny = request->shiny;
    pending->tera_type = request->tera_type;
    pending->credit_kind = request->credit_kind;
    copy_bytes(pending->ivs, request->ivs, sizeof(pending->ivs));
    pending->personality = request->personality;
    pending->generator_version = request->generator_version;
    copy_bytes(pending->generator_fingerprint,
               request->generator_fingerprint,
               sizeof(pending->generator_fingerprint));
    pending->transaction_id = G_LEDGER->generation + 1u;
}

static u8 pending_structurally_valid(const VegaPendingEncounter *pending)
{
    const RewardEncounterPoolEntry *entry;
    const RewardEncounterServiceConfig *service;
    u8 entry_index;
    u8 index;
    if (!pending->valid || pending->encounter_kind != REWARD_ENCOUNTER_KIND
        || pending->pool >= REWARD_ENCOUNTERS_SERVICE_COUNT
        || pending->species == 0u || pending->level == 0u
        || pending->level > 100u || pending->nature >= 25u
        || pending->ability > 2u || pending->form != 0u
        || pending->transaction_id == 0u
        || pending->generator_version != VEGA_REWARD_ENCOUNTER_GENERATOR_VERSION)
        return 0u;
    entry_index = entry_index_for_species(pending->species);
    if (entry_index == 0xFFu || entry_index / 6u != pending->pool)
        return 0u;
    entry = &gRewardEncounterPool[entry_index];
    service = &gRewardEncounterServices[pending->pool];
    if (pending->credit_kind != service->credit_kind
        || (pending->tera_type != entry->type1
            && pending->tera_type != entry->type2))
        return 0u;
    for (index = 0u; index < 6u; ++index) {
        if (pending->ivs[index] > 31u)
            return 0u;
    }
    return 1u;
}

static u16 purchase_precheck(u16 tier)
{
    const RewardEncounterServiceConfig *service;
    ensure_state();
    if (!ledger_valid())
        return VEGA_REWARD_INVALID;
    service = service_for(tier);
    if (service == (const RewardEncounterServiceConfig *)0)
        return VEGA_REWARD_INVALID;
    if (!service_unlocked(service))
        return VEGA_REWARD_LOCKED;
    if (G_LEDGER->factory.marker != VEGA_FACTORY_OUTSIDE)
        return VEGA_REWARD_FACTORY_ACTIVE;
    if (G_LEDGER->pending_encounter.valid)
        return VEGA_REWARD_PENDING_EXISTS;
    if (!has_capacity())
        return VEGA_REWARD_CAPACITY_FULL;
    return VEGA_REWARD_OK;
}

static u16 purchase_bp_request(u16 tier,
                               const VegaEncounterRequest *request)
{
    const RewardEncounterServiceConfig *service = service_for(tier);
    if (service == (const RewardEncounterServiceConfig *)0)
        return VEGA_REWARD_INVALID;
    if (G_LEDGER->factory.battle_points < service->bp_price)
        return VEGA_REWARD_INSUFFICIENT;
    copy_bytes(G_ROLLBACK, G_LEDGER, VEGA_SAVE_LEDGER_SIZE);
    G_LEDGER->factory.battle_points = (u16)(G_LEDGER->factory.battle_points
                                            - service->bp_price);
    ++G_LEDGER->factory.transaction_id;
    fill_pending(request);
    ++G_LEDGER->generation;
    VegaSaveFinalize(G_LEDGER);
    if (!persist_current()) {
        copy_bytes(G_LEDGER, G_ROLLBACK, VEGA_SAVE_LEDGER_SIZE);
        compensate_after_failed_persist();
        return VEGA_REWARD_PERSIST_FAILED;
    }
    return VEGA_REWARD_OK;
}

REWARD_EXPORT(RewardEncounterPurchaseWithBp)
u16 RewardEncounterPurchaseWithBp(u16 tier)
{
    VegaEncounterRequest request;
    u16 result = purchase_precheck(tier);
    if (result != VEGA_REWARD_OK)
        return set_result(result);
    generate_request((u8)tier, &request);
    return set_result(purchase_bp_request(tier, &request));
}

REWARD_EXPORT(RewardEncountersV2_Purchase)
u16 RewardEncountersV2_Purchase(u16 tier, u16 payment)
{
    VegaEncounterRequest request;
    VegaSaveStatus status;
    u16 result;
    if (payment == VEGA_REWARD_PAYMENT_CANCEL)
        return set_result(VEGA_REWARD_CANCELLED);
    result = purchase_precheck(tier);
    if (result != VEGA_REWARD_OK)
        return set_result(result);
    generate_request((u8)tier, &request);
    if (payment == VEGA_REWARD_PAYMENT_BP_DIRECT)
        return set_result(purchase_bp_request(tier, &request));
    if (payment != VEGA_REWARD_PAYMENT_TYPED_CREDIT)
        return set_result(VEGA_REWARD_INVALID);
    status = VegaSavePurchaseEncounter(G_LEDGER, &request,
                                       persist_callback, (void *)0);
    if (status == VEGA_SAVE_INSUFFICIENT_CREDIT)
        return set_result(VEGA_REWARD_INSUFFICIENT);
    if (status == VEGA_SAVE_PERSIST_FAILED) {
        compensate_after_failed_persist();
        return set_result(VEGA_REWARD_PERSIST_FAILED);
    }
    if (status != VEGA_SAVE_OK)
        return set_result(VEGA_REWARD_INVALID);
    return set_result(VEGA_REWARD_OK);
}

REWARD_EXPORT(RewardEncountersV2_PurchaseVoucher)
u16 RewardEncountersV2_PurchaseVoucher(u16 tier)
{
    const RewardEncounterServiceConfig *service;
    u16 *credit;
    ensure_state();
    if (!ledger_valid())
        return set_result(VEGA_REWARD_INVALID);
    service = service_for(tier);
    if (service == (const RewardEncounterServiceConfig *)0)
        return set_result(VEGA_REWARD_INVALID);
    if (!service_unlocked(service))
        return set_result(VEGA_REWARD_LOCKED);
    if (G_LEDGER->factory.marker != VEGA_FACTORY_OUTSIDE)
        return set_result(VEGA_REWARD_FACTORY_ACTIVE);
    credit = &G_LEDGER->encounter_credits[service->credit_kind];
    if (*credit == UINT16_MAX)
        return set_result(VEGA_REWARD_CREDIT_FULL);
    if (G_LEDGER->factory.battle_points < service->bp_price)
        return set_result(VEGA_REWARD_INSUFFICIENT);
    copy_bytes(G_ROLLBACK, G_LEDGER, VEGA_SAVE_LEDGER_SIZE);
    G_LEDGER->factory.battle_points = (u16)(G_LEDGER->factory.battle_points
                                            - service->bp_price);
    ++*credit;
    ++G_LEDGER->factory.transaction_id;
    ++G_LEDGER->generation;
    VegaSaveFinalize(G_LEDGER);
    if (!persist_current()) {
        copy_bytes(G_LEDGER, G_ROLLBACK, VEGA_SAVE_LEDGER_SIZE);
        compensate_after_failed_persist();
        return set_result(VEGA_REWARD_PERSIST_FAILED);
    }
    return set_result(VEGA_REWARD_OK);
}

static u32 side_effect_hash(void)
{
    const volatile u8 *bytes = (const volatile u8 *)G_LEDGER;
    u32 hash = 2166136261u;
    u32 index;
    const u32 pending_start = offsetof(VegaModernSaveData, pending_encounter);
    const u32 pending_end = pending_start + sizeof(VegaPendingEncounter);
    for (index = offsetof(VegaModernSaveData, shared_special_capture);
         index < offsetof(VegaModernSaveData, reserved); ++index) {
        if (index >= pending_start && index < pending_end)
            continue;
        hash ^= bytes[index];
        hash *= 16777619u;
    }
    return hash;
}

static void snapshot_external_side_effects(void)
{
    u8 index;
    u8 *save1;
    copy_bytes(G_ROLLBACK, G_LEDGER, VEGA_SAVE_LEDGER_SIZE);
    G_STATE->side_effect_hash_before = side_effect_hash();
    G_STATE->party_count_before = *G_PARTY_COUNT;
    G_STATE->dexnav_before = *G_DEXNAV_CHAIN;
    G_STATE->battle_type_before = *G_BATTLE_TYPE_FLAGS;
    save1 = *G_SAVE_BLOCK1_PTR;
    if (save1 != (u8 *)0)
        copy_bytes(G_STATE->money_before,
                   save1 + REWARD_SAVE_BLOCK1_MONEY_OFFSET, 4u);
    for (index = 0u; index < REWARD_PARTY_CAPACITY; ++index) {
        G_STATE->held_before[index] = (u16)FN_GET_MON_DATA(
            G_PLAYER_PARTY + (u32)index * REWARD_PARTY_MON_SIZE,
            REWARD_MON_DATA_HELD_ITEM, (u8 *)0);
    }
}

static void restore_external_side_effects(void)
{
    u8 index;
    u8 *save1 = *G_SAVE_BLOCK1_PTR;
    *G_DEXNAV_CHAIN = G_STATE->dexnav_before;
    *G_BATTLE_TYPE_FLAGS = G_STATE->battle_type_before;
    if (save1 != (u8 *)0)
        copy_bytes(save1 + REWARD_SAVE_BLOCK1_MONEY_OFFSET,
                   G_STATE->money_before, 4u);
    for (index = 0u; index < REWARD_PARTY_CAPACITY; ++index) {
        u16 item = G_STATE->held_before[index];
        FN_SET_MON_DATA(G_PLAYER_PARTY + (u32)index * REWARD_PARTY_MON_SIZE,
                        REWARD_MON_DATA_HELD_ITEM, &item);
    }
}

static void clear_research_provenance(void)
{
    if (G_RESEARCH->magic != REWARD_RESEARCH_MAGIC)
        return;
    G_RESEARCH->wild_pid = 0u;
    G_RESEARCH->wild_species = 0u;
    G_RESEARCH->wild_activity = 0xFFu;
    G_RESEARCH->wild_pre_caught = 0u;
    G_RESEARCH->wild_armed = 0u;
}

static void create_pending_enemy(void)
{
    const VegaPendingEncounter *pending = &G_LEDGER->pending_encounter;
    u16 value;
    u8 index;
    clear_bytes(G_ENEMY_PARTY, REWARD_PARTY_MON_SIZE * REWARD_PARTY_CAPACITY);
    FN_CREATE_MON(G_ENEMY_PARTY, pending->species, pending->level, 32u, 1u,
                  pending->personality, 0u, 0u);
    value = 0u;
    FN_SET_MON_DATA(G_ENEMY_PARTY, REWARD_MON_DATA_HELD_ITEM, &value);
    for (index = 0u; index < 6u; ++index) {
        value = pending->ivs[index];
        FN_SET_MON_DATA(G_ENEMY_PARTY, REWARD_MON_DATA_HP_IV + index, &value);
    }
    value = (u16)(pending->ability == 1u);
    FN_SET_MON_DATA(G_ENEMY_PARTY, REWARD_MON_DATA_ALT_ABILITY, &value);
    G_ENEMY_PARTY[REWARD_TERA_FIELD_OFFSET] = pending->tera_type;
    if (pending->ability == 2u)
        G_ENEMY_PARTY[REWARD_HIDDEN_ABILITY_FIELD_OFFSET]
            |= REWARD_HIDDEN_ABILITY_MASK;
    else
        G_ENEMY_PARTY[REWARD_HIDDEN_ABILITY_FIELD_OFFSET]
            &= (u8)~REWARD_HIDDEN_ABILITY_MASK;
    FN_CALCULATE_MON_STATS(G_ENEMY_PARTY);
}

REWARD_EXPORT(RewardEncountersV2_StartPendingBattle)
u16 RewardEncountersV2_StartPendingBattle(void)
{
    VegaPendingEncounter *pending;
    ensure_state();
    if (!ledger_valid())
        return set_result(VEGA_REWARD_INVALID);
    pending = &G_LEDGER->pending_encounter;
    if (!pending_structurally_valid(pending))
        return set_result(VEGA_REWARD_NO_PENDING);
    if (!has_capacity())
        return set_result(VEGA_REWARD_CAPACITY_FULL);
    snapshot_external_side_effects();
    G_STATE->battle_species = pending->species;
    G_STATE->caught_before = dex_caught_species(pending->species);
    G_STATE->battle_active = 1u;
    ++G_STATE->launch_count;
    clear_research_provenance();
    if (G_STATE->test_mode)
        return set_result(VEGA_REWARD_OK);
    create_pending_enemy();
    *G_BATTLE_TYPE_FLAGS |= REWARD_BATTLE_NO_EXP_EV;
    FN_START_SCRIPTED_WILD_BATTLE();
    return set_result(VEGA_REWARD_OK);
}

static void clear_standard_caught(u16 species)
{
    u16 national;
    u32 byte_index;
    u8 bit;
    u8 *save2;
    u8 entry = entry_index_for_species(species);
    if (G_STATE->test_mode) {
        if (entry != 0xFFu)
            G_STATE->test_caught_mask &= ~(1u << entry);
        return;
    }
    national = FN_SPECIES_TO_NATIONAL(species);
    save2 = *G_SAVE_BLOCK2_PTR;
    if (national == 0u || save2 == (u8 *)0)
        return;
    --national;
    byte_index = national >> 3;
    bit = (u8)(1u << (national & 7u));
    save2[REWARD_SAVE_BLOCK2_OWNED_OFFSET + byte_index] &= (u8)~bit;
}

static void rollback_captured_storage(void)
{
    if (G_STATE->test_mode) {
        if (!G_STATE->caught_before)
            clear_standard_caught(G_STATE->battle_species);
        return;
    }
    if (G_STATE->party_count_before < REWARD_PARTY_CAPACITY) {
        clear_bytes(G_PLAYER_PARTY
                        + (u32)G_STATE->party_count_before
                            * REWARD_PARTY_MON_SIZE,
                    REWARD_PARTY_MON_SIZE);
        *G_PARTY_COUNT = G_STATE->party_count_before;
    } else if (*G_SPECIAL_MON_BOX_ID < REWARD_BOX_COUNT
               && *G_SPECIAL_MON_BOX_POS < REWARD_BOX_CAPACITY) {
        FN_ZERO_BOX_MON_AT((u8)*G_SPECIAL_MON_BOX_ID,
                           (u8)*G_SPECIAL_MON_BOX_POS);
    }
    if (!G_STATE->caught_before)
        clear_standard_caught(G_STATE->battle_species);
}

REWARD_EXPORT(RewardEncounterCompleteNormalCapture)
u16 RewardEncounterCompleteNormalCapture(void)
{
    VegaPendingEncounter pending;
    ensure_state();
    if (!G_STATE->battle_active
        || !pending_structurally_valid(&G_LEDGER->pending_encounter))
        return set_result(VEGA_REWARD_NO_PENDING);
    copy_bytes(&pending, &G_LEDGER->pending_encounter, sizeof(pending));
    copy_bytes(G_LEDGER, G_ROLLBACK, VEGA_SAVE_LEDGER_SIZE);
    clear_bytes(&G_LEDGER->pending_encounter,
                sizeof(G_LEDGER->pending_encounter));
    ++G_LEDGER->generation;
    VegaSaveFinalize(G_LEDGER);
    if (!persist_current()) {
        copy_bytes(G_LEDGER, G_ROLLBACK, VEGA_SAVE_LEDGER_SIZE);
        rollback_captured_storage();
        compensate_after_failed_persist();
        G_STATE->battle_active = 0u;
        return set_result(VEGA_REWARD_PERSIST_FAILED);
    }
    (void)pending;
    G_STATE->battle_active = 0u;
    return set_result(VEGA_REWARD_OK);
}

static u16 credit_activity(u8 activity, u8 newly_caught, u32 source_token)
{
    u8 tier;
    const RewardEncounterServiceConfig *service;
    u16 *credit;
    if (activity > REWARD_SOURCE_ECOLOGY || source_token == 0u)
        return VEGA_REWARD_INVALID;
    if (!source_unlocked(activity))
        return VEGA_REWARD_LOCKED;
    if (activity == REWARD_SOURCE_ECOLOGY && !newly_caught)
        return VEGA_REWARD_EFFECTLESS;
    if (G_STATE->last_source_token == source_token)
        return VEGA_REWARD_EFFECTLESS;
    tier = activity == REWARD_SOURCE_FISHING
        ? VEGA_REWARD_TIER_HABITAT : VEGA_REWARD_TIER_RANDOM;
    service = &gRewardEncounterServices[tier];
    credit = &G_LEDGER->encounter_credits[service->credit_kind];
    if (*credit == UINT16_MAX) {
        G_STATE->last_source_token = source_token;
        return VEGA_REWARD_EFFECTLESS;
    }
    copy_bytes(G_ROLLBACK, G_LEDGER, VEGA_SAVE_LEDGER_SIZE);
    ++*credit;
    ++G_LEDGER->factory.transaction_id;
    ++G_LEDGER->generation;
    VegaSaveFinalize(G_LEDGER);
    if (!persist_current()) {
        copy_bytes(G_LEDGER, G_ROLLBACK, VEGA_SAVE_LEDGER_SIZE);
        compensate_after_failed_persist();
        return VEGA_REWARD_PERSIST_FAILED;
    }
    G_STATE->last_source_token = source_token;
    return VEGA_REWARD_OK;
}

static void handle_activity_source(void)
{
    u16 species;
    u32 pid;
    u32 token;
    u8 eligible;
    if (G_RESEARCH->magic != REWARD_RESEARCH_MAGIC
        || !G_RESEARCH->wild_armed
        || G_RESEARCH->wild_activity > REWARD_RESEARCH_ACTIVITY_ECOLOGY
        || *G_BATTLE_OUTCOME != REWARD_BATTLE_OUTCOME_CAUGHT)
        return;
    species = (u16)FN_GET_MON_DATA(G_ENEMY_PARTY,
                                    REWARD_MON_DATA_SPECIES2, (u8 *)0);
    pid = FN_GET_MON_DATA(G_ENEMY_PARTY,
                          REWARD_MON_DATA_PERSONALITY, (u8 *)0);
    if (species != G_RESEARCH->wild_species || pid != G_RESEARCH->wild_pid)
        return;
    eligible = (u8)(G_RESEARCH->wild_activity
                        == REWARD_RESEARCH_ACTIVITY_FISHING
                    || (!G_RESEARCH->wild_pre_caught
                        && dex_caught_species(species)));
    if (!eligible)
        return;
    token = pid ^ ((u32)species << 16)
        ^ ((u32)G_RESEARCH->wild_activity << 30);
    if (token == 0u)
        token = 1u;
    (void)credit_activity(G_RESEARCH->wild_activity,
                          (u8)!G_RESEARCH->wild_pre_caught, token);
}

REWARD_EXPORT(RewardEncountersV2_EndWildBattleCommitInternal)
void RewardEncountersV2_EndWildBattleCommitInternal(void)
{
    VegaPendingEncounter pending;
    ensure_state();
    if (!G_STATE->battle_active) {
        handle_activity_source();
        return;
    }
    copy_bytes(&pending, &G_LEDGER->pending_encounter, sizeof(pending));
    restore_external_side_effects();
    copy_bytes(G_LEDGER, G_ROLLBACK, VEGA_SAVE_LEDGER_SIZE);
    if (*G_BATTLE_OUTCOME == REWARD_BATTLE_OUTCOME_CAUGHT)
        (void)RewardEncounterCompleteNormalCapture();
    else {
        VegaSaveFinalize(G_LEDGER);
        G_STATE->battle_active = 0u;
        set_result(VEGA_REWARD_EFFECTLESS);
    }
    (void)pending;
}

REWARD_EXPORT(RewardEncountersV2_EndWildBattleAdapter)
__attribute__((naked))
void RewardEncountersV2_EndWildBattleAdapter(void)
{
    __asm__ volatile(
        "push {r4, lr}\n"
        "bl RewardEncountersV2_EndWildBattleCommitInternal\n"
        "pop {r4}\n"
        "pop {r3}\n"
        "mov lr, r3\n"
        "ldr r3, =%c0\n"
        "bx r3\n"
        :
        : "i" (REWARD_DELEGATE_RESEARCH_WILD_END)
        : "r3", "memory");
}

static void text_copy(u8 *destination, u32 capacity, const u8 *source)
{
    u32 index = 0u;
    if (capacity == 0u)
        return;
    while (index + 1u < capacity && source[index] != 0xFFu) {
        destination[index] = source[index];
        ++index;
    }
    destination[index] = 0xFFu;
}

static u32 text_append(u8 *destination, u32 capacity, u32 index,
                       const u8 *source)
{
    u32 cursor = 0u;
    while (index + 1u < capacity && source[cursor] != 0xFFu)
        destination[index++] = source[cursor++];
    destination[index] = 0xFFu;
    return index;
}

static u32 text_number(u8 *destination, u32 capacity, u32 index, u16 value)
{
    u16 divisor = 10000u;
    u8 started = 0u;
    while (divisor != 0u && index + 1u < capacity) {
        u8 digit = (u8)(value / divisor);
        if (digit != 0u || started || divisor == 1u) {
            destination[index++] = gRewardEncounterDigitGlyphs[digit];
            started = 1u;
        }
        value = (u16)(value % divisor);
        divisor = (u16)(divisor / 10u);
    }
    destination[index] = 0xFFu;
    return index;
}

static void build_balance_text(void)
{
    const RewardEncounterServiceConfig *service;
    u32 index = 0u;
    u16 credit = 0u;
    u16 bp = G_LEDGER->factory.battle_points;
    if (G_STATE->selected_tier < REWARD_ENCOUNTERS_SERVICE_COUNT) {
        service = &gRewardEncounterServices[G_STATE->selected_tier];
        credit = G_LEDGER->encounter_credits[service->credit_kind];
    }
    index = text_append((u8 *)G_STATE->balance_text,
                        sizeof(G_STATE->balance_text), index,
                        gRewardEncounterTextCreditPrefix);
    index = text_number((u8 *)G_STATE->balance_text,
                        sizeof(G_STATE->balance_text), index, credit);
    index = text_append((u8 *)G_STATE->balance_text,
                        sizeof(G_STATE->balance_text), index,
                        gRewardEncounterTextBpPrefix);
    (void)text_number((u8 *)G_STATE->balance_text,
                      sizeof(G_STATE->balance_text), index, bp);
}

static void add_menu_row(u8 code, const u8 *text)
{
    u8 index = G_STATE->menu_count;
    if (index >= 5u)
        return;
    G_STATE->menu_codes[index] = code;
    text_copy((u8 *)G_STATE->row_text[index],
              sizeof(G_STATE->row_text[index]), text);
    ++G_STATE->menu_count;
}

static void build_tier_menu(void)
{
    u8 tier;
    G_STATE->menu_stage = REWARD_MENU_TIER;
    G_STATE->menu_count = 0u;
    for (tier = 0u; tier < REWARD_ENCOUNTERS_SERVICE_COUNT; ++tier) {
        if (service_unlocked(&gRewardEncounterServices[tier]))
            add_menu_row(tier, gRewardEncounterTierLabels[tier]);
    }
    add_menu_row(REWARD_MENU_CODE_CANCEL, gRewardEncounterTextCancel);
}

static void build_payment_menu(void)
{
    const RewardEncounterServiceConfig *service =
        &gRewardEncounterServices[G_STATE->selected_tier];
    u16 credit = G_LEDGER->encounter_credits[service->credit_kind];
    u16 bp = G_LEDGER->factory.battle_points;
    G_STATE->menu_stage = REWARD_MENU_PAYMENT;
    G_STATE->menu_count = 0u;
    if (credit != 0u)
        add_menu_row(VEGA_REWARD_PAYMENT_TYPED_CREDIT,
                     gRewardEncounterTextPayCredit);
    if (bp >= service->bp_price)
        add_menu_row(VEGA_REWARD_PAYMENT_BP_DIRECT,
                     gRewardEncounterTextPayBp);
    if (bp >= service->bp_price && credit != UINT16_MAX)
        add_menu_row(REWARD_MENU_CODE_VOUCHER,
                     gRewardEncounterTextVoucher);
    add_menu_row(REWARD_MENU_CODE_CANCEL, gRewardEncounterTextCancel);
}

static void build_yes_no(u8 resume)
{
    G_STATE->menu_stage = resume ? REWARD_MENU_RESUME : REWARD_MENU_CONFIRM;
    G_STATE->menu_count = 0u;
    add_menu_row(REWARD_MENU_CODE_YES, gRewardEncounterTextYes);
    add_menu_row(REWARD_MENU_CODE_CANCEL, gRewardEncounterTextNo);
}

static const u8 *menu_header(void)
{
    u8 tier = G_STATE->selected_tier;
    if (tier >= REWARD_ENCOUNTERS_SERVICE_COUNT)
        tier = VEGA_REWARD_TIER_RANDOM;
    if (G_STATE->menu_stage == REWARD_MENU_TIER)
        return gRewardEncounterDialogues[tier][REWARD_DIALOGUE_INTRO];
    if (G_STATE->menu_stage == REWARD_MENU_RESUME)
        return gRewardEncounterDialogues[tier][REWARD_DIALOGUE_PENDING_RESUME];
    if (G_STATE->menu_stage == REWARD_MENU_CONFIRM) {
        return gRewardEncounterDialogues[tier][
            G_STATE->selected_payment == VEGA_REWARD_PAYMENT_TYPED_CREDIT
                ? REWARD_DIALOGUE_CONFIRM_CREDIT
                : REWARD_DIALOGUE_CONFIRM_BP];
    }
    if (G_STATE->menu_count <= 1u)
        return gRewardEncounterDialogues[tier][REWARD_DIALOGUE_INSUFFICIENT];
    return gRewardEncounterDialogues[tier][REWARD_DIALOGUE_MENU];
}

static void close_window(u8 task_id)
{
    u8 window = (u8)G_TASKS[task_id].data[0];
    if (window == REWARD_WINDOW_INVALID)
        return;
    FN_CLEAR_STD_WINDOW_FRAME(window, 0u);
    FN_REMOVE_WINDOW(window);
    FN_SCHEDULE_BG_COPY(0u);
    G_TASKS[task_id].data[0] = REWARD_WINDOW_INVALID;
    G_STATE->window_id = REWARD_WINDOW_INVALID;
}

static u8 render_menu(u8 task_id)
{
    struct WindowTemplate window;
    u8 id;
    u8 index;
    build_balance_text();
    window.bg = 0u;
    window.tilemap_left = 7u;
    window.tilemap_top = 0u;
    window.width = 22u;
    window.height = (u8)(G_STATE->menu_count * 2u + 5u);
    window.palette_num = 15u;
    window.base_block = FN_GET_STD_WINDOW_BASE_TILE();
    id = (u8)FN_ADD_WINDOW(&window);
    if (id == REWARD_WINDOW_INVALID)
        return 0u;
    G_TASKS[task_id].data[0] = id;
    G_STATE->window_id = id;
    FN_FILL_WINDOW_PIXEL_BUFFER(id, 0x11u);
    FN_DRAW_STD_WINDOW_FRAME(id, 0u);
    FN_PUT_WINDOW_TILEMAP(id);
    FN_ADD_TEXT_PRINTER(id, 2u, menu_header(), 8u, 1u, 0u, (void *)0);
    FN_ADD_TEXT_PRINTER(id, 2u, (const u8 *)G_STATE->balance_text,
                        8u, 17u, 0u, (void *)0);
    for (index = 0u; index < G_STATE->menu_count; ++index) {
        FN_ADD_TEXT_PRINTER(id, 2u, (const u8 *)G_STATE->row_text[index],
                            8u, (u8)(33u + index * 16u), 0u, (void *)0);
    }
    FN_MENU_INIT_CURSOR(id, 2u, 0u, 33u, 16u,
                        G_STATE->menu_count, 0u);
    FN_COPY_WINDOW_TO_VRAM(id, REWARD_COPYWIN_BOTH);
    FN_SCHEDULE_BG_COPY(0u);
    return 1u;
}

static void finish_field_menu(u8 task_id, u16 result)
{
    close_window(task_id);
    FN_DESTROY_TASK(task_id);
    FN_PLAY_SE(REWARD_SE_SELECT);
    G_STATE->menu_active = 0u;
    set_result(result);
    FN_ENABLE_BOTH_SCRIPT_CONTEXTS();
}

static void rerender(u8 task_id)
{
    close_window(task_id);
    if (!render_menu(task_id))
        finish_field_menu(task_id, VEGA_REWARD_ENGINE_REJECTED);
}

static void Task_RewardEncounterMenu(u8 task_id)
{
    s8 choice = FN_MENU_PROCESS_INPUT();
    u8 code;
    u16 result;
    if (choice == REWARD_MENU_NOTHING)
        return;
    if (choice == REWARD_MENU_B || choice < 0
        || (u8)choice >= G_STATE->menu_count) {
        finish_field_menu(task_id, VEGA_REWARD_CANCELLED);
        return;
    }
    code = G_STATE->menu_codes[(u8)choice];
    if (code == REWARD_MENU_CODE_CANCEL) {
        finish_field_menu(task_id, VEGA_REWARD_CANCELLED);
        return;
    }
    if (G_STATE->menu_stage == REWARD_MENU_TIER) {
        G_STATE->selected_tier = code;
        build_payment_menu();
        rerender(task_id);
        return;
    }
    if (G_STATE->menu_stage == REWARD_MENU_PAYMENT) {
        G_STATE->selected_payment = code;
        build_yes_no(0u);
        rerender(task_id);
        return;
    }
    if (G_STATE->menu_stage == REWARD_MENU_RESUME) {
        finish_field_menu(task_id, VEGA_REWARD_OK);
        (void)RewardEncountersV2_StartPendingBattle();
        return;
    }
    if (G_STATE->menu_stage != REWARD_MENU_CONFIRM) {
        finish_field_menu(task_id, VEGA_REWARD_INVALID);
        return;
    }
    if (G_STATE->selected_payment == REWARD_MENU_CODE_VOUCHER)
        result = RewardEncountersV2_PurchaseVoucher(G_STATE->selected_tier);
    else
        result = RewardEncountersV2_Purchase(G_STATE->selected_tier,
                                              G_STATE->selected_payment);
    finish_field_menu(task_id, result);
    if (result == VEGA_REWARD_OK
        && G_STATE->selected_payment != REWARD_MENU_CODE_VOUCHER)
        (void)RewardEncountersV2_StartPendingBattle();
}

REWARD_EXPORT(RewardEncountersV2_FieldScientist)
u16 RewardEncountersV2_FieldScientist(void)
{
    u8 task_id;
    ensure_state();
    if (!ledger_valid())
        return set_result(VEGA_REWARD_INVALID);
    if (G_LEDGER->factory.marker != VEGA_FACTORY_OUTSIDE)
        return set_result(VEGA_REWARD_FACTORY_ACTIVE);
    G_STATE->selected_tier = G_LEDGER->pending_encounter.valid
        ? (u8)G_LEDGER->pending_encounter.pool : 0xFFu;
    G_STATE->selected_payment = 0xFFu;
    G_STATE->window_id = REWARD_WINDOW_INVALID;
    G_STATE->menu_active = 0u;
    if (G_LEDGER->pending_encounter.valid) {
        if (!pending_structurally_valid(&G_LEDGER->pending_encounter))
            return set_result(VEGA_REWARD_INVALID);
        if (!has_capacity())
            return set_result(VEGA_REWARD_CAPACITY_FULL);
        build_yes_no(1u);
    } else {
        build_tier_menu();
        if (G_STATE->menu_count <= 1u)
            return set_result(VEGA_REWARD_LOCKED);
    }
    task_id = FN_CREATE_TASK(Task_RewardEncounterMenu, 0x50u);
    if (task_id >= REWARD_NUM_TASKS)
        return set_result(VEGA_REWARD_ENGINE_REJECTED);
    G_TASKS[task_id].data[0] = REWARD_WINDOW_INVALID;
    if (!render_menu(task_id)) {
        FN_DESTROY_TASK(task_id);
        return set_result(VEGA_REWARD_ENGINE_REJECTED);
    }
    G_STATE->menu_active = 1u;
    set_result(VEGA_REWARD_BUSY);
    FN_SCRIPT_CONTEXT2_ENABLE();
    return VEGA_REWARD_BUSY;
}

REWARD_EXPORT(RewardEncountersV2_Probe)
u32 RewardEncountersV2_Probe(u32 query)
{
    if (query == 0u)
        return VEGA_REWARD_ENCOUNTERS_V2_ABI_VERSION;
    if (query == 1u)
        return VEGA_REWARD_ENCOUNTER_VOLATILE_ADDRESS;
    if (query == 2u)
        return VEGA_SAVE_EWRAM_ADDRESS;
    if (query >= 0x100u
        && query < 0x100u + REWARD_ENCOUNTERS_SERVICE_COUNT)
        return (u32)(uintptr_t)&gRewardEncounterServices[query - 0x100u];
    if (query >= 0x200u
        && query < 0x200u + REWARD_ENCOUNTERS_ENTRY_COUNT)
        return (u32)(uintptr_t)&gRewardEncounterPool[query - 0x200u];
    if (query >= 0x300u
        && query < 0x300u + REWARD_ENCOUNTERS_DIALOGUE_COUNT) {
        u32 index = query - 0x300u;
        return (u32)(uintptr_t)gRewardEncounterDialogues[index / 14u]
                                                     [index % 14u];
    }
    return 0u;
}

REWARD_EXPORT(RewardEncountersV2_TestInitialize)
u16 RewardEncountersV2_TestInitialize(void)
{
    clear_bytes(G_STATE, sizeof(*G_STATE));
    G_STATE->magic = REWARD_STATE_MAGIC;
    G_STATE->magic_inverse = ~REWARD_STATE_MAGIC;
    G_STATE->test_mode = 1u;
    G_STATE->capacity_override = 1u;
    G_STATE->unlock_all = 1u;
    G_STATE->window_id = REWARD_WINDOW_INVALID;
    G_STATE->selected_tier = 0xFFu;
    G_STATE->selected_payment = 0xFFu;
    G_STATE->test_rng = 0x13579BDFu;
    VegaSaveInitNew(G_LEDGER, 1u);
    G_LEDGER->kanto_travel_unlocked = 1u;
    G_LEDGER->vega_hall_of_fame = 1u;
    G_LEDGER->kanto_certifications = 0xFFu;
    VegaSaveFinalize(G_LEDGER);
    return set_result(VEGA_REWARD_OK);
}

REWARD_EXPORT(RewardEncountersV2_TestResetVolatile)
u16 RewardEncountersV2_TestResetVolatile(void)
{
    clear_bytes(G_STATE, sizeof(*G_STATE));
    G_STATE->magic = REWARD_STATE_MAGIC;
    G_STATE->magic_inverse = (u32)~(u32)REWARD_STATE_MAGIC;
    G_STATE->test_mode = 1u;
    G_STATE->capacity_override = 1u;
    G_STATE->unlock_all = 1u;
    G_STATE->window_id = REWARD_WINDOW_INVALID;
    G_STATE->selected_tier = 0xFFu;
    G_STATE->selected_payment = 0xFFu;
    G_STATE->test_rng = 0x13579BDFu;
    if (!ledger_valid())
        return set_result(VEGA_REWARD_INVALID);
    return set_result(VEGA_REWARD_OK);
}

REWARD_EXPORT(RewardEncountersV2_TestSetBalances)
u16 RewardEncountersV2_TestSetBalances(u16 tier, u16 credit,
                                       u16 battle_points)
{
    const RewardEncounterServiceConfig *service = service_for(tier);
    if (service == (const RewardEncounterServiceConfig *)0)
        return set_result(VEGA_REWARD_INVALID);
    G_LEDGER->encounter_credits[service->credit_kind] = credit;
    G_LEDGER->factory.battle_points = battle_points;
    VegaSaveFinalize(G_LEDGER);
    return set_result(VEGA_REWARD_OK);
}

REWARD_EXPORT(RewardEncountersV2_TestSetCapacity)
u16 RewardEncountersV2_TestSetCapacity(u16 mode)
{
    if (mode > 2u)
        return set_result(VEGA_REWARD_INVALID);
    G_STATE->capacity_override = (u8)mode;
    return set_result(VEGA_REWARD_OK);
}

REWARD_EXPORT(RewardEncountersV2_TestSetPersistenceFault)
u16 RewardEncountersV2_TestSetPersistenceFault(u16 enabled)
{
    G_STATE->persistence_fault = (u8)(enabled != 0u);
    return set_result(VEGA_REWARD_OK);
}

REWARD_EXPORT(RewardEncountersV2_TestSetCaughtMask)
u16 RewardEncountersV2_TestSetCaughtMask(u32 mask)
{
    G_STATE->test_caught_mask = mask & 0x00FFFFFFu;
    return set_result(VEGA_REWARD_OK);
}

REWARD_EXPORT(RewardEncountersV2_TestGetCredit)
u16 RewardEncountersV2_TestGetCredit(u16 tier)
{
    const RewardEncounterServiceConfig *service = service_for(tier);
    if (service == (const RewardEncounterServiceConfig *)0)
        return 0u;
    return G_LEDGER->encounter_credits[service->credit_kind];
}

REWARD_EXPORT(RewardEncountersV2_TestGetBattlePoints)
u16 RewardEncountersV2_TestGetBattlePoints(void)
{
    return G_LEDGER->factory.battle_points;
}

REWARD_EXPORT(RewardEncountersV2_TestGetPendingHash)
u32 RewardEncountersV2_TestGetPendingHash(void)
{
    const volatile u8 *bytes =
        (const volatile u8 *)&G_LEDGER->pending_encounter;
    u32 hash = 2166136261u;
    u32 index;
    for (index = 0u; index < sizeof(G_LEDGER->pending_encounter); ++index) {
        hash ^= bytes[index];
        hash *= 16777619u;
    }
    return hash;
}

REWARD_EXPORT(RewardEncountersV2_TestGetGeneration)
u32 RewardEncountersV2_TestGetGeneration(void)
{
    return G_LEDGER->generation;
}

REWARD_EXPORT(RewardEncountersV2_TestGetPendingField)
u16 RewardEncountersV2_TestGetPendingField(u16 field)
{
    const VegaPendingEncounter *pending = &G_LEDGER->pending_encounter;
    switch (field) {
    case 0u: return pending->valid;
    case 1u: return pending->pool;
    case 2u: return pending->species;
    case 3u: return pending->level;
    case 4u: return pending->ability;
    case 5u: return pending->nature;
    case 6u: return pending->generator_version;
    case 7u: return pending->credit_kind;
    default: return 0xFFFFu;
    }
}

REWARD_EXPORT(RewardEncountersV2_TestSimulateOutcome)
u16 RewardEncountersV2_TestSimulateOutcome(u16 outcome,
                                           u16 mutate_side_effects)
{
    if (!G_STATE->battle_active)
        return set_result(VEGA_REWARD_NO_PENDING);
    if (mutate_side_effects) {
        G_LEDGER->shared_special_capture[0] ^= 0xFFu;
        G_LEDGER->raid_reward_claimed[0] ^= 0xFFu;
        G_LEDGER->factory.reward_claim_bits ^= 0x00FF0000u;
        G_LEDGER->encounter_credits[7] ^= 0x55AAu;
        ((volatile u8 *)&G_LEDGER->research_economy)[0] ^= 0x7Fu;
    }
    if (outcome == REWARD_BATTLE_OUTCOME_CAUGHT) {
        u8 entry = entry_index_for_species(G_STATE->battle_species);
        if (entry != 0xFFu)
            G_STATE->test_caught_mask |= 1u << entry;
    }
    *G_BATTLE_OUTCOME = (u8)outcome;
    RewardEncountersV2_EndWildBattleCommitInternal();
    return G_STATE->last_result;
}

REWARD_EXPORT(RewardEncountersV2_TestCreditActivity)
u16 RewardEncountersV2_TestCreditActivity(u16 activity,
                                          u16 newly_caught,
                                          u32 source_token)
{
    return set_result(credit_activity((u8)activity,
                                      (u8)(newly_caught != 0u),
                                      source_token));
}

REWARD_EXPORT(RewardEncountersV2_TestGetSideEffectHash)
u32 RewardEncountersV2_TestGetSideEffectHash(void)
{
    return side_effect_hash();
}

REWARD_EXPORT(RewardEncountersV2_TestGetCaughtMask)
u32 RewardEncountersV2_TestGetCaughtMask(void)
{
    return G_STATE->test_caught_mask;
}
