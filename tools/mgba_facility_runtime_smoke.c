/* Focused stage20 exact-ROM smoke.  Reuse the established natural boot trace
 * and libmGBA call bridge, then exercise the physically bound Factory Trial
 * runtime without writing ROM, state, screenshot, or save artifacts. */
#define main mgba_regression_smoke_embedded_main
#include "mgba_regression_smoke.c"
#undef main

#include <string.h>

#define FACILITY_MAX_CALL_STEPS UINT64_C(20000000)
#define FACILITY_PROBE_MARKER UINT32_C(0xFA20)
#define FACILITY_GET_MON_DATA UINT32_C(0x0803F355)
#define FACILITY_SPECIES_TO_NATIONAL UINT32_C(0x08042989)
#define FACILITY_GET_SET_POKEDEX UINT32_C(0x08088A51)
#define FACILITY_PLAYER_PARTY UINT32_C(0x020241E4)
#define FACILITY_ENEMY_PARTY UINT32_C(0x02023F8C)
#define FACILITY_PARTY_COUNT UINT32_C(0x02023F89)
#define FACILITY_BATTLE_OUTCOME UINT32_C(0x02023DEA)
#define FACILITY_SELECTED_ORDER UINT32_C(0x0203C6C8)
#define FACILITY_RNG UINT32_C(0x03005040)
#define FACILITY_LEDGER UINT32_C(0x0203D000)
#define FACILITY_LEDGER_SIZE UINT32_C(0x800)
#define FACILITY_FACTORY_OFFSET UINT32_C(0x392)
#define FACILITY_BP_OFFSET UINT32_C(0)
#define FACILITY_CURRENT_STREAK_OFFSET UINT32_C(2)
#define FACILITY_BEST_STREAK_OFFSET UINT32_C(50)
#define FACILITY_REWARD_BITS_OFFSET UINT32_C(98)
#define FACILITY_MARKER_OFFSET UINT32_C(110)
#define FACILITY_SNAPSHOT_VALID_OFFSET UINT32_C(111)
#define FACILITY_SNAPSHOT_COUNT_OFFSET UINT32_C(112)
#define FACILITY_REWARD_PENDING_OFFSET UINT32_C(113)
#define FACILITY_SNAPSHOT_OFFSET UINT32_C(114)
#define FACILITY_EXCHANGE_SCRATCH UINT32_C(0x0203E300)
#define FACILITY_FLASH_LEDGER UINT32_C(0x0E01F064)
#define FACILITY_G_SAVE_BLOCK2 UINT32_C(0x0300504C)
#define FACILITY_SAVE_BLOCK1_SEEN_OFFSET UINT32_C(0x5F8)
#define FACILITY_SAVE_BLOCK2_CAUGHT_OFFSET UINT32_C(0x28)
#define FACILITY_SEEN_BYTES UINT32_C(129)
#define FACILITY_CAUGHT_BYTES UINT32_C(52)
#define FACILITY_MON_SIZE UINT32_C(100)
#define FACILITY_PARTY_SIZE UINT32_C(6)
#define FACILITY_SELECTED_SIZE UINT32_C(3)
#define FACILITY_SNAPSHOT_COMMITTED UINT32_C(1)
#define FACILITY_BATTLE_ACTIVE UINT32_C(2)
#define FACILITY_EXCHANGE_MAGIC UINT32_C(0x58434846)

static void facility_die(const char *message)
{
    fprintf(stderr, "mgba-facility-runtime-smoke: %s\n", message);
    exit(1);
}

static void facility_write8(struct mCore *core, uint32_t address, uint8_t value)
{
    core->rawWrite8(core, address, -1, value);
}

static void facility_write16(struct mCore *core, uint32_t address, uint16_t value)
{
    core->rawWrite16(core, address, -1, value);
}

static void facility_write32(struct mCore *core, uint32_t address, uint32_t value)
{
    facility_write8(core, address, (uint8_t)value);
    facility_write8(core, address + 1U, (uint8_t)(value >> 8U));
    facility_write8(core, address + 2U, (uint8_t)(value >> 16U));
    facility_write8(core, address + 3U, (uint8_t)(value >> 24U));
}

static uint32_t facility_read_le32_unaligned(struct mCore *core, uint32_t address)
{
    return (uint32_t)read8(core, address)
        | ((uint32_t)read8(core, address + 1U) << 8U)
        | ((uint32_t)read8(core, address + 2U) << 16U)
        | ((uint32_t)read8(core, address + 3U) << 24U);
}

static void facility_read_bytes(struct mCore *core, uint32_t address,
                                uint8_t *destination, size_t size)
{
    for (size_t index = 0; index < size; ++index)
        destination[index] = read8(core, address + (uint32_t)index);
}

static void facility_write_bytes(struct mCore *core, uint32_t address,
                                 const uint8_t *source, size_t size)
{
    for (size_t index = 0; index < size; ++index)
        facility_write8(core, address + (uint32_t)index, source[index]);
}

static bool facility_memory_equals(struct mCore *core, uint32_t address,
                                   const uint8_t *expected, size_t size)
{
    for (size_t index = 0; index < size; ++index) {
        if (read8(core, address + (uint32_t)index) != expected[index])
            return false;
    }
    return true;
}

static bool facility_memory_regions_equal(struct mCore *core, uint32_t left,
                                           uint32_t right, size_t size)
{
    for (size_t index = 0; index < size; ++index) {
        if (read8(core, left + (uint32_t)index)
            != read8(core, right + (uint32_t)index))
            return false;
    }
    return true;
}

static uint32_t facility_call_thumb(struct mCore *core, uint32_t function,
                                    uint32_t r0, uint32_t r1,
                                    uint32_t r2, uint32_t r3)
{
    struct CpuContext original = capture_cpu(core);
    write_register(core, "cpsr", original.registers[16] | 0xA0);
    write_register(core, "lr", (int32_t)UINT32_C(0x08000001));
    write_register(core, "r0", (int32_t)r0);
    write_register(core, "r1", (int32_t)r1);
    write_register(core, "r2", (int32_t)r2);
    write_register(core, "r3", (int32_t)r3);
    write_register(core, "pc", (int32_t)function);
    uint64_t steps = 0;
    while ((((uint32_t)read_register(core, "pc")) & ~1U)
           != UINT32_C(0x08000002)) {
        if (++steps > FACILITY_MAX_CALL_STEPS) {
            fprintf(stderr,
                    "mgba-facility-runtime-smoke: instruction limit "
                    "function=%#010" PRIx32 " pc=%#010" PRIx32 "\n",
                    function, (uint32_t)read_register(core, "pc"));
            facility_die("runtime instruction limit exceeded");
        }
        core->step(core);
    }
    uint32_t result = (uint32_t)read_register(core, "r0");
    restore_cpu(core, &original);
    return result;
}

static uint16_t facility_invoke(struct mCore *core, uint32_t entrypoint)
{
    facility_write16(core, SPECIAL_VAR_RESULT, 0);
    (void)facility_call_thumb(core, entrypoint, 0, 0, 0, 0);
    return read16(core, SPECIAL_VAR_RESULT);
}

static uint16_t facility_species(struct mCore *core, uint32_t mon)
{
    return (uint16_t)facility_call_thumb(
        core, FACILITY_GET_MON_DATA, mon, 11U, 0, 0);
}

static void require_exact_party(struct mCore *core,
                                const uint8_t original[FACILITY_PARTY_SIZE
                                                       * FACILITY_MON_SIZE],
                                uint8_t original_count,
                                const char *exit_name)
{
    if (!facility_memory_equals(
            core, FACILITY_PLAYER_PARTY, original,
            FACILITY_PARTY_SIZE * FACILITY_MON_SIZE)
        || read8(core, FACILITY_PARTY_COUNT) != original_count
        || read8(core, FACILITY_LEDGER + FACILITY_FACTORY_OFFSET
                       + FACILITY_MARKER_OFFSET) != 0U
        || read8(core, FACILITY_LEDGER + FACILITY_FACTORY_OFFSET
                       + FACILITY_SNAPSHOT_VALID_OFFSET) != 0U) {
        fprintf(stderr, "mgba-facility-runtime-smoke: restore failed at %s\n",
                exit_name);
        exit(1);
    }
}

static void set_selected(struct mCore *core, uint8_t first,
                         uint8_t second, uint8_t third)
{
    const uint8_t order[6] = {first, second, third, 0, 0, 0};
    facility_write_bytes(core, FACILITY_SELECTED_ORDER, order, sizeof(order));
}

static void copy_mon(struct mCore *core, uint32_t destination, uint32_t source)
{
    uint8_t mon[FACILITY_MON_SIZE];
    facility_read_bytes(core, source, mon, sizeof(mon));
    facility_write_bytes(core, destination, mon, sizeof(mon));
}

static void verify_map_binding(struct mCore *core, uint32_t npc_script,
                               uint32_t map_scripts, uint32_t recover)
{
    uint32_t map_root = read32(core, ROM_BASE + UINT32_C(0x54B0C));
    uint32_t group96 = read32(core, map_root + 96U * 4U);
    uint32_t header = read32(core, group96 + 5U * 4U);
    uint32_t events = read32(core, header + 4U);
    uint32_t scripts = read32(core, header + 8U);
    uint32_t objects = read32(core, events + 4U);
    uint32_t facility_object = objects + 0x18U;
    if (!rom_pointer(map_root) || !rom_pointer(group96) || !rom_pointer(header)
        || !rom_pointer(events) || !rom_pointer(objects)
        || scripts != map_scripts || read8(core, events) != 2U
        || read8(core, objects) != 1U || read8(core, facility_object) != 2U
        || read16(core, facility_object + 4U) != 20U
        || read16(core, facility_object + 6U) != 19U
        || read32(core, facility_object + 0x10U) != npc_script
        || read8(core, npc_script) != 0x6AU
        || read8(core, npc_script + 1U) != 0x5AU)
        facility_die("physical Vermilion NPC graph is invalid");
    if (read8(core, scripts) != 3U
        || facility_read_le32_unaligned(core, scripts + 1U) == 0U
        || read8(core, scripts + 5U) != 0U) {
        facility_die("Vermilion recovery map-script table is invalid");
    }
    uint32_t recovery_script = facility_read_le32_unaligned(core, scripts + 1U);
    if ((recovery_script & 3U) != 0U || read8(core, recovery_script) != 0x23U
        || facility_read_le32_unaligned(core, recovery_script + 1U) != recover
        || read8(core, recovery_script + 5U) != 0x02U)
        facility_die("recovery callnative bytecode is invalid");
}

static void require_six_unique(struct mCore *core, uint16_t output[6])
{
    if (read8(core, FACILITY_PARTY_COUNT) != 6U)
        facility_die("rental generator did not produce six candidates");
    for (uint32_t left = 0; left < 6U; ++left) {
        output[left] = facility_species(
            core, FACILITY_PLAYER_PARTY + left * FACILITY_MON_SIZE);
        if (output[left] == 0U)
            facility_die("rental generator emitted an empty candidate");
        for (uint32_t right = 0; right < left; ++right) {
            if (output[left] == output[right])
                facility_die("rental generator emitted duplicate species");
        }
    }
}

static void require_enter(struct mCore *core, uint32_t enter,
                          uint16_t species[6])
{
    facility_write32(core, FACILITY_RNG, UINT32_C(0x12345678));
    if (facility_invoke(core, enter) != 1U)
        facility_die("FacilityRuntime_Enter failed");
    require_six_unique(core, species);
}

static void require_flash_ledger(struct mCore *core)
{
    if (!facility_memory_regions_equal(
            core, FACILITY_LEDGER, FACILITY_FLASH_LEDGER,
            FACILITY_LEDGER_SIZE))
        facility_die("save-backed ledger differs from sector 31 payload");
}

int main(int argc, char **argv)
{
    if (argc != 16) {
        fprintf(stderr,
                "usage: %s ROM PROBE ENTER COMMIT_SELECT PREPARE AFTER "
                "BEGIN_EXCHANGE COMMIT_EXCHANGE SKIP COMPLETE ABORT RECOVER "
                "NPC_SCRIPT MAP_SCRIPTS FACILITY_STATE_IS_ACTIVE\n",
                argv[0]);
        return 2;
    }
    uint32_t probe = parse_u32(argv[2], "probe");
    uint32_t enter = parse_u32(argv[3], "enter");
    uint32_t commit_selection = parse_u32(argv[4], "commit selection");
    uint32_t prepare = parse_u32(argv[5], "prepare battle");
    uint32_t after = parse_u32(argv[6], "after battle");
    uint32_t begin_exchange = parse_u32(argv[7], "begin exchange");
    uint32_t commit_exchange = parse_u32(argv[8], "commit exchange");
    uint32_t skip_exchange = parse_u32(argv[9], "skip exchange");
    uint32_t complete = parse_u32(argv[10], "complete");
    uint32_t abort_entry = parse_u32(argv[11], "abort");
    uint32_t recover = parse_u32(argv[12], "recover");
    uint32_t npc_script = parse_u32(argv[13], "NPC script");
    uint32_t map_scripts = parse_u32(argv[14], "map scripts");
    uint32_t facility_state_is_active = parse_u32(
        argv[15], "facility state is active");
    const uint32_t entrypoints[] = {
        probe, enter, commit_selection, prepare, after, begin_exchange,
        commit_exchange, skip_exchange, complete, abort_entry, recover,
    };
    for (size_t index = 0;
         index < sizeof(entrypoints) / sizeof(entrypoints[0]); ++index) {
        if ((entrypoints[index] & 1U) == 0U
            || (entrypoints[index] & ~1U) < ROM_BASE
            || (entrypoints[index] & ~1U) >= ROM_END)
            facility_die("runtime entrypoint contract failed");
    }
    if (!rom_pointer(npc_script) || !rom_pointer(map_scripts)
        || (facility_state_is_active & 1U) == 0U
        || !rom_pointer(facility_state_is_active & ~1U))
        facility_die("script address contract failed");

    struct mLogger logger = {.log = silent_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = mCoreFind(argv[1]);
    if (core == NULL || !core->init(core))
        facility_die("core initialization failed");
    if (!mCoreLoadFile(core, argv[1]))
        facility_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    color_t *video = calloc(GBA_WIDTH * GBA_HEIGHT, sizeof(*video));
    if (video == NULL)
        facility_die("video allocation failed");
    core->setVideoBuffer(core, video, GBA_WIDTH);
    core->reset(core);
    uint32_t transitions = run_natural_new_game(core, video);

    verify_map_binding(core, npc_script, map_scripts, recover);
    facility_write16(core, SPECIAL_VAR_RESULT, 0);
    if (facility_call_thumb(core, probe, 0, 0, 0, 0)
            != FACILITY_PROBE_MARKER
        || read16(core, SPECIAL_VAR_RESULT) != FACILITY_PROBE_MARKER)
        facility_die("embedded facility probe did not execute");

    uint32_t saveblock1 = read32(core, G_SAVE_BLOCK1);
    uint32_t saveblock2 = read32(core, FACILITY_G_SAVE_BLOCK2);
    if (saveblock1 < UINT32_C(0x02000000)
        || saveblock1 >= UINT32_C(0x02040000)
        || saveblock2 < UINT32_C(0x02000000)
        || saveblock2 >= UINT32_C(0x02040000))
        facility_die("natural new game lacks save blocks");
    uint8_t original[FACILITY_PARTY_SIZE * FACILITY_MON_SIZE];
    uint8_t rentals[FACILITY_PARTY_SIZE * FACILITY_MON_SIZE];
    uint8_t caught_before[FACILITY_CAUGHT_BYTES];
    uint8_t seen_before[FACILITY_SEEN_BYTES];
    facility_read_bytes(core, FACILITY_PLAYER_PARTY, original, sizeof(original));
    facility_read_bytes(core, saveblock1 + FACILITY_SAVE_BLOCK1_SEEN_OFFSET,
                        seen_before, sizeof(seen_before));
    facility_read_bytes(core, saveblock2 + FACILITY_SAVE_BLOCK2_CAUGHT_OFFSET,
                        caught_before, sizeof(caught_before));
    uint8_t original_count = read8(core, FACILITY_PARTY_COUNT);
    if (original_count > FACILITY_PARTY_SIZE)
        facility_die("natural party count is invalid");

    uint16_t rental_species[6];
    require_enter(core, enter, rental_species);
    facility_read_bytes(core, FACILITY_PLAYER_PARTY, rentals, sizeof(rentals));
    uint32_t factory = FACILITY_LEDGER + FACILITY_FACTORY_OFFSET;
    if (read8(core, factory + FACILITY_MARKER_OFFSET)
            != FACILITY_SNAPSHOT_COMMITTED
        || read8(core, factory + FACILITY_SNAPSHOT_VALID_OFFSET) != 1U
        || read8(core, factory + FACILITY_SNAPSHOT_COUNT_OFFSET)
               != original_count
        || !facility_memory_equals(core, factory + FACILITY_SNAPSHOT_OFFSET,
                                   original, sizeof(original)))
        facility_die("entry snapshot is not exact");
    require_flash_ledger(core);
    bool seen_changed = !facility_memory_equals(
        core, saveblock1 + FACILITY_SAVE_BLOCK1_SEEN_OFFSET,
        seen_before, sizeof(seen_before));
    bool caught_unchanged = facility_memory_equals(
        core, saveblock2 + FACILITY_SAVE_BLOCK2_CAUGHT_OFFSET,
        caught_before, sizeof(caught_before));
    bool rental_seen_only = true;
    for (size_t index = 0; index < 6; ++index) {
        uint32_t national = facility_call_thumb(
            core, FACILITY_SPECIES_TO_NATIONAL,
            rental_species[index], 0, 0, 0);
        if (national == 0U
            || facility_call_thumb(core, FACILITY_GET_SET_POKEDEX,
                                   national, 0U, 0, 0) != 1U
            || facility_call_thumb(core, FACILITY_GET_SET_POKEDEX,
                                   national, 1U, 0, 0) != 0U)
            rental_seen_only = false;
    }
    if (!seen_changed || !caught_unchanged || !rental_seen_only) {
        fprintf(stderr,
                "mgba-facility-runtime-smoke: dex diagnostic seen_changed=%u "
                "caught_unchanged=%u rental_seen_only=%u saveblock=%#010" PRIx32
                " species=[%u,%u,%u,%u,%u,%u]"
                " national=[%" PRIu32 ",%" PRIu32 ",%" PRIu32
                ",%" PRIu32 ",%" PRIu32 ",%" PRIu32 "]\n",
                seen_changed, caught_unchanged, rental_seen_only, saveblock1,
                rental_species[0], rental_species[1], rental_species[2],
                rental_species[3], rental_species[4], rental_species[5],
                facility_call_thumb(core, FACILITY_SPECIES_TO_NATIONAL,
                                    rental_species[0], 0, 0, 0),
                facility_call_thumb(core, FACILITY_SPECIES_TO_NATIONAL,
                                    rental_species[1], 0, 0, 0),
                facility_call_thumb(core, FACILITY_SPECIES_TO_NATIONAL,
                                    rental_species[2], 0, 0, 0),
                facility_call_thumb(core, FACILITY_SPECIES_TO_NATIONAL,
                                    rental_species[3], 0, 0, 0),
                facility_call_thumb(core, FACILITY_SPECIES_TO_NATIONAL,
                                    rental_species[4], 0, 0, 0),
                facility_call_thumb(core, FACILITY_SPECIES_TO_NATIONAL,
                                    rental_species[5], 0, 0, 0));
        facility_die("rental Pokédex update is not seen-only");
    }

    set_selected(core, 1, 2, 3);
    if (facility_invoke(core, commit_selection) != 1U
        || read8(core, FACILITY_PARTY_COUNT) != FACILITY_SELECTED_SIZE
        || read8(core, factory + FACILITY_MARKER_OFFSET)
               != FACILITY_BATTLE_ACTIVE
        || !facility_memory_equals(core, FACILITY_PLAYER_PARTY,
                                   rentals, 3U * FACILITY_MON_SIZE))
        facility_die("manual three-candidate selection failed");

    if (facility_invoke(core, prepare) != 1U
        || facility_call_thumb(core, facility_state_is_active, 0, 0, 0, 0)
               != 1U)
        facility_die("fixed CFRU facility policy is not active");

    /* Battle construction is already scheduler-tested by T06.  Install one
     * valid generated rental as the observed opponent result and validate the
     * stage20 post-battle ownership/exchange path on its exact 100-byte ABI. */
    copy_mon(core, FACILITY_ENEMY_PARTY,
             FACILITY_PLAYER_PARTY + 2U * FACILITY_MON_SIZE);
    for (uint32_t slot = 1; slot < FACILITY_PARTY_SIZE; ++slot) {
        uint8_t zero[FACILITY_MON_SIZE] = {0};
        facility_write_bytes(core,
            FACILITY_ENEMY_PARTY + slot * FACILITY_MON_SIZE,
            zero, sizeof(zero));
    }
    facility_write8(core, FACILITY_BATTLE_OUTCOME, 1U);
    if (facility_invoke(core, after) != 1U
        || read32(core, FACILITY_EXCHANGE_SCRATCH)
               != FACILITY_EXCHANGE_MAGIC)
        facility_die("first victory did not stage an exchange");
    uint8_t exchange_mon[FACILITY_MON_SIZE];
    facility_read_bytes(core, FACILITY_EXCHANGE_SCRATCH + 4U,
                        exchange_mon, sizeof(exchange_mon));
    if (facility_invoke(core, begin_exchange) != 1U)
        facility_die("exchange selection did not begin");
    set_selected(core, 2, 0, 0);
    if (facility_invoke(core, commit_exchange) != 1U
        || !facility_memory_equals(
            core, FACILITY_PLAYER_PARTY + FACILITY_MON_SIZE,
            exchange_mon, sizeof(exchange_mon)))
        facility_die("selected party slot was not exchanged");

    facility_write8(core, FACILITY_BATTLE_OUTCOME, 1U);
    if (facility_invoke(core, after) != 1U
        || facility_invoke(core, skip_exchange) != 1U)
        facility_die("second victory or exchange skip failed");
    facility_write8(core, FACILITY_BATTLE_OUTCOME, 1U);
    if (facility_invoke(core, after) != 2U
        || read8(core, factory + FACILITY_REWARD_PENDING_OFFSET) != 3U)
        facility_die("third victory did not complete the streak");
    if (facility_invoke(core, complete) != 9U)
        facility_die("completion reward failed");
    require_exact_party(core, original, original_count, "complete");
    if (read16(core, factory + FACILITY_BP_OFFSET) != 9U
        || read16(core, factory + FACILITY_CURRENT_STREAK_OFFSET) != 3U
        || read16(core, factory + FACILITY_BEST_STREAK_OFFSET) != 3U
        || (read32(core, factory + FACILITY_REWARD_BITS_OFFSET) & 1U) == 0U)
        facility_die("BP, streak, or first-clear record is invalid");
    require_flash_ledger(core);

    /* Loss, explicit abort, and serialized reset recovery all restore the
     * original six-slot image and count exactly once. */
    uint16_t ignored_species[6];
    require_enter(core, enter, ignored_species);
    set_selected(core, 1, 2, 3);
    if (facility_invoke(core, commit_selection) != 1U)
        facility_die("loss fixture selection failed");
    facility_write8(core, FACILITY_BATTLE_OUTCOME, 2U);
    if (facility_invoke(core, after) != 0U)
        facility_die("loss fixture returned a winning result");
    require_exact_party(core, original, original_count, "loss");

    require_enter(core, enter, ignored_species);
    if (facility_invoke(core, abort_entry) != 1U)
        facility_die("abort entrypoint failed");
    require_exact_party(core, original, original_count, "abort");

    require_enter(core, enter, ignored_species);
    uint8_t serialized[FACILITY_LEDGER_SIZE];
    facility_read_bytes(core, FACILITY_FLASH_LEDGER,
                        serialized, sizeof(serialized));
    uint8_t zero_ledger[FACILITY_LEDGER_SIZE] = {0};
    facility_write_bytes(core, FACILITY_LEDGER,
                         zero_ledger, sizeof(zero_ledger));
    facility_write_bytes(core, FACILITY_LEDGER,
                         serialized, sizeof(serialized));
    if (facility_invoke(core, recover) != 1U)
        facility_die("serialized reset recovery entrypoint failed");
    require_exact_party(core, original, original_count, "save/reset");
    require_flash_ledger(core);
    if (!facility_memory_equals(
            core, saveblock2 + FACILITY_SAVE_BLOCK2_CAUGHT_OFFSET,
            caught_before, sizeof(caught_before)))
        facility_die("caught Pokédex flags changed during facility sessions");

    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"checks\":{\"random_six_unique\":true,"
           "\"manual_select_three\":true,"
           "\"cfru_policy_pending\":true,\"win_exchange\":true,"
           "\"exact_restore_all_exits\":true,\"seen_only\":true,"
           "\"reward_and_streak\":true,"
           "\"physical_npc_and_recovery_script\":true,"
           "\"save_sector_round_trip\":true},"
           "\"rental_species\":[%u,%u,%u,%u,%u,%u],"
           "\"original_party_count\":%u,\"bp\":%u,"
           "\"streak\":%u,\"framebuffer_transitions\":%" PRIu32 ","
           "\"artifacts_written\":[]}\n",
           rental_species[0], rental_species[1], rental_species[2],
           rental_species[3], rental_species[4], rental_species[5],
           original_count, read16(core, factory + FACILITY_BP_OFFSET),
           read16(core, factory + FACILITY_CURRENT_STREAK_OFFSET), transitions);

    free(video);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
