/*
 * T04 Vega early-game move smoke.
 *
 * Reuse the exact, reviewed T01 natural-new-game input trace and its minimal
 * libmGBA plumbing.  Renaming the bundled entry point keeps this runner's
 * contract independent while preventing a second copy of the 233-segment
 * trace from drifting.
 *
 * The runner is read-only: it neither autoloads nor writes savedata.  From the
 * natural T03 field state it creates rooted early-game species through the ROM
 * CreateMon routine, starts a normal wild battle through the ROM setup routine,
 * and emits one JSON line after the battle remains alive for fixed frames.
 */
#define main t01_ai_fixture_bundled_entry_point
#include "mgba_ai_fixture_runner.c"
#undef main

enum {
    MOVE_SMOKE_MAX_VEGA_ID = 511,
    MOVE_SMOKE_MAX_BATTLERS = 4,
    MOVE_SMOKE_SLOTS = 4,
    MOVE_SMOKE_BOOT_SEGMENTS = 233,
    BATTLE_MON_HP_OFFSET = 0x28,
    ROM_CREATE_MON = 0x0803D1C1,
    ROM_START_WILD_BATTLE = 0x0807EE2D,
};

struct ActiveMoveSnapshot {
    uint16_t species;
    uint16_t hp;
    uint16_t moves[MOVE_SMOKE_SLOTS];
    uint8_t pp[MOVE_SMOKE_SLOTS];
};

struct BattleSnapshot {
    uint32_t type_flags;
    uint8_t battler_count;
    uint8_t absent_flags;
    struct ActiveMoveSnapshot battlers[MOVE_SMOKE_MAX_BATTLERS];
};

static const char *const MOVE_SMOKE_REGISTERS[] = {
    "r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7",
    "r8", "r9", "r10", "r11", "r12", "sp", "lr", "pc", "cpsr",
};

struct MoveSmokeCpuContext {
    int32_t values[ARRAY_LEN(MOVE_SMOKE_REGISTERS)];
};

static struct MoveSmokeCpuContext capture_move_smoke_cpu(struct mCore *core) {
    struct MoveSmokeCpuContext result;
    for (size_t i = 0; i < ARRAY_LEN(MOVE_SMOKE_REGISTERS); ++i) {
        result.values[i] = read_register(core, MOVE_SMOKE_REGISTERS[i]);
    }
    return result;
}

static void restore_move_smoke_cpu(struct mCore *core,
                                   const struct MoveSmokeCpuContext *context) {
    write_register(core, "cpsr", (uint32_t) context->values[16]);
    for (size_t i = 0; i < 15; ++i) {
        write_register(core, MOVE_SMOKE_REGISTERS[i], (uint32_t) context->values[i]);
    }
    write_register(core, "pc", (uint32_t) context->values[15]);
}

static uint32_t call_preserving_cpu(struct mCore *core, uint32_t function,
                                    uint32_t r0, uint32_t r1,
                                    uint32_t r2, uint32_t r3) {
    struct MoveSmokeCpuContext original = capture_move_smoke_cpu(core);
    uint32_t result = call_rom_args(core, function, r0, r1, r2, r3).return_value;
    restore_move_smoke_cpu(core, &original);
    return result;
}

static void run_segment_trace(struct mCore *core, const struct Segment *trace,
                              size_t count) {
    for (size_t segment = 0; segment < count; ++segment) {
        core->setKeys(core, trace[segment].keys);
        for (uint32_t frame = 0; frame < trace[segment].frames; ++frame) {
            core->runFrame(core);
        }
    }
    core->setKeys(core, 0);
}

static void create_mon(struct mCore *core, uint32_t destination,
                       uint16_t species, uint8_t level) {
    /* CreateMon has eight ARM ABI arguments.  r0-r3 are passed in registers;
     * fixedPersonality/personality/fixedOTID/otID are placed at caller SP. */
    struct MoveSmokeCpuContext original = capture_move_smoke_cpu(core);
    uint32_t original_sp = (uint32_t) original.values[13];
    uint32_t call_sp = (original_sp - 16U) & ~7U;
    for (unsigned offset = 0; offset < 16; ++offset) write8(core, call_sp + offset, 0);
    write_register(core, "sp", (int32_t) call_sp);
    (void) call_rom_args(core, ROM_CREATE_MON, destination, species, level, 0);
    restore_move_smoke_cpu(core, &original);
    if (call_preserving_cpu(core, ROM_GET_MON_DATA, destination, 11, 0, 0) != species) {
        die("CreateMon did not produce rooted early-game species");
    }
}

static void create_early_battle_parties(struct mCore *core) {
    create_mon(core, ADDR_PLAYER_PARTY, 4, 5);
    create_mon(core, ADDR_ENEMY_PARTY, 10, 5);
    write8(core, ADDR_PLAYER_PARTY_COUNT, 1);
}

static uint32_t parse_progress_frames(const char *text) {
    errno = 0;
    char *end = NULL;
    unsigned long value = strtoul(text, &end, 0);
    if (errno || !end || *end || value == 0 || value > 60000UL) {
        die("invalid progress frame count");
    }
    return (uint32_t) value;
}

static struct BattleSnapshot capture_move_snapshot(struct mCore *core) {
    struct BattleSnapshot result = {0};
    result.type_flags = read32(core, ADDR_BATTLE_TYPE_FLAGS);
    if (result.type_flags & BATTLE_TYPE_TRAINER) {
        die("synthetic smoke entered trainer battle");
    }
    result.battler_count = read8(core, ADDR_BATTLERS_COUNT);
    result.absent_flags = read8(core, ADDR_ABSENT_BATTLER_FLAGS);
    if (result.battler_count < 2 || result.battler_count > MOVE_SMOKE_MAX_BATTLERS) {
        die("active battler count is invalid");
    }
    if (result.absent_flags & ((1U << result.battler_count) - 1U)) {
        die("an active battler is marked absent");
    }
    for (unsigned battler = 0; battler < result.battler_count; ++battler) {
        uint32_t base = ADDR_BATTLE_MONS + battler * BATTLE_MON_SIZE;
        struct ActiveMoveSnapshot *active = &result.battlers[battler];
        active->species = read16(core, base);
        active->hp = read16(core, base + BATTLE_MON_HP_OFFSET);
        if (!active->species || !active->hp) die("active battler is invalid or fainted");
        unsigned populated = 0;
        for (unsigned slot = 0; slot < MOVE_SMOKE_SLOTS; ++slot) {
            active->moves[slot] = read16(core, base + BATTLE_MON_MOVES_OFFSET + slot * 2);
            active->pp[slot] = read8(core, base + BATTLE_MON_PP_OFFSET + slot);
            if (!active->moves[slot]) continue;
            ++populated;
            if (active->moves[slot] > MOVE_SMOKE_MAX_VEGA_ID) {
                die("active move ID is outside the frozen Vega range");
            }
            if (!active->pp[slot]) die("active move has zero PP");
        }
        if (!populated) die("active battler has no usable move");
    }
    return result;
}

static uint32_t settle_executable_pc(struct mCore *core) {
    for (unsigned step = 0; step < 100000U; ++step) {
        uint32_t pc = (uint32_t) read_register(core, "pc");
        if ((pc >= 0x02000000U && pc < 0x02040000U) ||
            (pc >= 0x03000000U && pc < 0x03008000U) ||
            (pc >= 0x08000000U && pc < 0x0A000000U)) {
            return pc;
        }
        core->step(core);
    }
    die("emulated core did not return to an executable address");
    return 0;
}

static bool same_active_moves(const struct BattleSnapshot *left,
                              const struct BattleSnapshot *right) {
    if (left->battler_count != right->battler_count) return false;
    for (unsigned battler = 0; battler < left->battler_count; ++battler) {
        if (left->battlers[battler].species != right->battlers[battler].species) return false;
        for (unsigned slot = 0; slot < MOVE_SMOKE_SLOTS; ++slot) {
            if (left->battlers[battler].moves[slot] != right->battlers[battler].moves[slot]) {
                return false;
            }
        }
    }
    return true;
}

static void print_battlers(const struct BattleSnapshot *value) {
    putchar('[');
    for (unsigned battler = 0; battler < value->battler_count; ++battler) {
        if (battler) putchar(',');
        const struct ActiveMoveSnapshot *active = &value->battlers[battler];
        printf("{\"index\":%u,\"species\":%u,\"hp\":%u,\"moves\":[",
               battler, active->species, active->hp);
        for (unsigned slot = 0; slot < MOVE_SMOKE_SLOTS; ++slot) {
            if (slot) putchar(',');
            printf("%u", active->moves[slot]);
        }
        printf("],\"pp\":[");
        for (unsigned slot = 0; slot < MOVE_SMOKE_SLOTS; ++slot) {
            if (slot) putchar(',');
            printf("%u", active->pp[slot]);
        }
        putchar(']');
        putchar('}');
    }
    putchar(']');
}

int main(int argc, char **argv) {
    if (argc < 3 || argc > 4) {
        fprintf(stderr, "usage: %s ROM EXPECTED_ROM_SHA256 [PROGRESS_FRAMES]\n", argv[0]);
        return 2;
    }
    uint32_t progress_frames = argc == 4 ? parse_progress_frames(argv[3]) : 300U;
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64 || strcmp(rom_sha256, argv[2]) != 0) {
        die("ROM SHA-256 mismatch");
    }

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {.sample = NULL, .unixTime = fixed_unix_time,
                             .serialize = NULL, .deserialize = NULL};
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1])) die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);

    run_segment_trace(core, BOOT_TRACE, MOVE_SMOKE_BOOT_SEGMENTS);
    if (log_problem_count) die("mGBA emitted warning/error diagnostics during boot");
    create_early_battle_parties(core);
    (void) call_preserving_cpu(core, ROM_START_WILD_BATTLE, 0, 0, 0, 0);
    run_segment_trace(core, (const struct Segment[]) {{300, 0}}, 1);
    uint32_t before_pc = settle_executable_pc(core);
    struct BattleSnapshot before = capture_move_snapshot(core);
    uint64_t before_digest = fnv1a64_ram(core);

    /* Dismiss the fixed opening messages, choose FIGHT, and select slot 0.
     * This is the same deterministic input on the reference and candidate,
     * and must result in a real PP spend rather than an idle battle screen. */
    run_segment_trace(core, (const struct Segment[]) {
        {2, 1}, {160, 0}, {2, 1}, {160, 0},
        {2, 1}, {160, 0}, {2, 1}, {160, 0},
        {2, 1}, {160, 0}, {2, 1}, {300, 0},
    }, 12);

    core->setKeys(core, 0);
    for (uint32_t frame = 0; frame < progress_frames; ++frame) core->runFrame(core);
    if (log_problem_count) die("mGBA emitted warning/error diagnostics during progression");
    uint32_t after_pc = settle_executable_pc(core);
    struct BattleSnapshot after = capture_move_snapshot(core);
    uint64_t after_digest = fnv1a64_ram(core);
    if (!same_active_moves(&before, &after)) die("active move identity changed unexpectedly");
    bool player_pp_spent = false;
    bool hp_changed = false;
    for (unsigned slot = 0; slot < MOVE_SMOKE_SLOTS; ++slot) {
        if (after.battlers[0].pp[slot] < before.battlers[0].pp[slot]) {
            player_pp_spent = true;
        }
    }
    for (unsigned battler = 0; battler < before.battler_count; ++battler) {
        if (after.battlers[battler].hp != before.battlers[battler].hp) hp_changed = true;
    }
    if (!player_pp_spent) die("fixed battle input did not execute a player move");
    if (!hp_changed) die("fixed battle turn produced no HP change");

    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    if (log_problem_count) die("mGBA emitted warning/error diagnostics during shutdown");

    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"fixture\":\"synthetic_rooted_early_wild_battle\",\"battle_kind\":\"WILD\","
           "\"rom_sha256\":\"%s\",\"fixed_rtc_unix\":946684800,"
           "\"provenance\":{\"field_base\":\"natural_T03_233_segment_trace\","
           "\"rooted_species\":{\"player\":4,\"enemy\":10,\"level\":5},"
           "\"direct_rom_calls\":{\"CreateMon\":\"0x%08X\","
           "\"BattleSetup_StartWildBattle\":\"0x%08X\"}},"
           "\"boot_trace_segments\":%zu,"
           "\"progress_frames\":%" PRIu32 ","
           "\"move_id_contract\":{\"zero_slot_allowed\":true,\"nonzero_min\":1,"
           "\"nonzero_max\":511},\"warnings_errors\":0,\"before\":{"
           "\"wild_battle_active\":true,\"battle_type_flags\":%" PRIu32 ","
           "\"active_battlers\":%u,\"absent_flags\":%u,\"ewram_iwram_fnv1a64\":\"%016" PRIx64
           "\",\"pc\":%" PRIu32 ",\"battlers\":",
           rom_sha256, ROM_CREATE_MON, ROM_START_WILD_BATTLE,
           (size_t) MOVE_SMOKE_BOOT_SEGMENTS, progress_frames,
           before.type_flags,
           before.battler_count, before.absent_flags, before_digest, before_pc);
    print_battlers(&before);
    printf("},\"after\":{\"wild_battle_active\":true,\"battle_type_flags\":%" PRIu32 ","
           "\"active_battlers\":%u,\"absent_flags\":%u,\"ewram_iwram_fnv1a64\":\"%016" PRIx64
           "\",\"pc\":%" PRIu32 ",\"battlers\":",
           after.type_flags, after.battler_count, after.absent_flags, after_digest,
           after_pc);
    print_battlers(&after);
    printf("},\"move_execution\":{\"input\":\"A_x6_slot0\","
           "\"player_pp_spent\":true,\"hp_changed\":true},"
           "\"core_alive_after_progression\":true,\"active_move_ids_stable\":true,"
           "\"artifacts_written\":[]}\n");
    return 0;
}
