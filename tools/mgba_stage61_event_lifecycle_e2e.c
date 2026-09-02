/*
 * Stage61 event lifecycle E2E.
 *
 * The reviewed display/NPC/event harness is embedded so every producer is
 * reached with its ordinary field/UI inputs.  Host calls below are limited
 * to fixture preparation and read-only state inspection; no script owner,
 * ScriptContext setup, choice result, battle result, or transition callback
 * is invoked from the host.
 */
#ifndef S61_EVENT_LIFECYCLE_EMBEDDED_HARNESS
#error "compile through scripts/run_stage61_event_lifecycle_e2e.py"
#endif
#include S61_EVENT_LIFECYCLE_EMBEDDED_HARNESS

enum {
    EL_MAP_GRID_GET_METATILE_ID_AT = 0x08058705U,
    EL_FIELD_BORDER = 7U,
    EL_TEMP_FLAG_FIRST_SWITCH = 1U,
    EL_VAR_TEMP_0 = 0x4000U,
    EL_VAR_TEMP_1 = 0x4001U,
    EL_VAR_SCENE_CINNABAR = 0x4071U,
    EL_VAR_SCENE_ONE_ISLAND_CENTER = 0x4076U,
    EL_FERRY_SPECIAL = 0x08147468U,
    EL_FERRY_EXPECTED_GROUP = 3U,
    EL_FERRY_EXPECTED_MAP = 5U,
    EL_FERRY_EXPECTED_X = 23U,
    EL_FERRY_EXPECTED_Y = 32U,
    EL_TASK_COUNT = 16U,
    EL_TASK_ACTIVE_OFFSET = 4U,
    EL_GYM_GROUP = 98U,
    EL_GYM_MAP = 40U,
    EL_ROUTE16_GROUP = 96U,
    EL_ROUTE16_MAP = 27U,
};

struct ElFerryOwner {
    const char *id;
    const char *stem;
    uint8_t group;
    uint8_t map;
    uint32_t root;
};

static const struct ElFerryOwner el_ferry_owners[] = {
    {"OBJECT:031/006:001", "ferry-seven", 31U, 6U, 0x0818F658U},
    {"OBJECT:032/004:001", "ferry-one",   32U, 4U, 0x081909EBU},
    {"OBJECT:033/004:001", "ferry-two",   33U, 4U, 0x08191380U},
    {"OBJECT:035/005:001", "ferry-four",  35U, 5U, 0x08191DC0U},
    {"OBJECT:036/002:001", "ferry-five",  36U, 2U, 0x08191F62U},
    {"OBJECT:037/002:001", "ferry-six",   37U, 2U, 0x081922BDU},
    {"OBJECT:038/000:001", "ferry-three", 38U, 0U, 0x081923DBU},
};

struct ElFerryTrace {
    bool owner_seen;
    bool special_seen;
    bool callback_seen;
    bool task_seen;
    bool arrived;
    uint32_t first_nonfield_callback;
    uint32_t first_task_function;
    unsigned actual_walk_steps;
    unsigned input_pulses;
    unsigned owner_hits;
    unsigned special_hits;
    uint64_t ppm_rgb_fnv1a64;
};

struct ElCancelTrace {
    bool released;
    bool menu_cancel_seen;
    uint16_t post_cancel_result;
    unsigned input_pulses;
};

struct ElGymTrace {
    unsigned first_id_initial;
    unsigned second_id_initial;
    unsigned wrong_id;
    unsigned first_id_retry;
    unsigned second_id_retry;
    unsigned actual_walk_steps;
    unsigned owner_hits;
    uint64_t baseline_metatile_hash;
    uint64_t half_metatile_hash;
    uint64_t reset_metatile_hash;
    uint64_t open_metatile_hash;
    uint64_t reentry_metatile_hash;
};

struct ElSnorlaxTrace {
    const char *outcome_name;
    unsigned actual_walk_steps;
    unsigned owner_hits;
    unsigned producer_messages;
    unsigned choice_no_result;
    uint16_t species;
    uint8_t outcome;
    bool caught_with_real_bag_keys;
    bool actual_run_direction_a;
    unsigned battle_input_pulses;
    unsigned producer_owner_hits;
    uint32_t battle_callback;
    unsigned party_count_before;
    unsigned party_count_after;
    uint16_t captured_species;
    bool preparation_state_valid;
    bool battle_runtime_initialized;
    bool battle_runtime_cleaned;
    bool master_ball_consumed;
    bool field_returned;
    uint64_t ppm_rgb_fnv1a64;
};

struct ElRunTrace {
    bool runtime_seen;
    bool field_terminal;
    bool actual_direction_input;
    bool actual_a_input;
    uint8_t outcome;
    uint32_t first_battle_callback;
    unsigned input_pulses;
};

enum {
    EL_HEAP_TRANSITION_LIMIT = 128U,
    EL_HEAP_WATCH_ADDRESS_COUNT = 5U,
    EL_HEAP_HISTORY_COUNT = 64U,
    EL_INTR_TABLE_COUNT = 16U,
};

struct ElInstructionTrace {
    uint64_t ordinal;
    uint32_t raw_pc;
    uint32_t instruction_pc;
    uint32_t cpsr;
    uint32_t lr;
    uint32_t sp;
    uint32_t r0;
    uint32_t r1;
    uint32_t r2;
    uint32_t r3;
    uint32_t frame;
    uint32_t callback;
    uint32_t battle_pointer;
    uint8_t battle_outcome;
    uint8_t party_count;
};

struct ElHeapTransition {
    uint32_t address;
    uint32_t before;
    uint32_t after;
    uint32_t instruction_pc;
    uint32_t lr;
    uint32_t r0;
    uint32_t r1;
    uint32_t r2;
    uint32_t r3;
    uint32_t previous_instruction_pc;
    uint32_t previous_lr;
    uint32_t previous_r0;
    uint32_t previous_r1;
    uint64_t ordinal;
};

struct ElHeapWatch {
    uint32_t addresses[EL_HEAP_WATCH_ADDRESS_COUNT];
    uint32_t values[EL_HEAP_WATCH_ADDRESS_COUNT];
    struct ElHeapTransition transitions[EL_HEAP_TRANSITION_LIMIT];
    unsigned transition_count;
    bool overflow;
    bool first_corrupt_seen;
    struct ElHeapTransition first_corrupt;
    bool previous_valid;
    uint32_t previous_instruction_pc;
    uint32_t previous_lr;
    uint32_t previous_r0;
    uint32_t previous_r1;
    struct ElInstructionTrace history[EL_HEAP_HISTORY_COUNT];
    struct ElInstructionTrace first_corrupt_history[EL_HEAP_HISTORY_COUNT];
    uint64_t instruction_count;
    uint64_t first_corrupt_history_end;
    uint64_t first_bag_open_ordinal;
    uint64_t first_outcome_ordinal;
    uint64_t first_party_two_ordinal;
    uint64_t first_runtime_cleanup_ordinal;
    uint32_t initial_intr_table[EL_INTR_TABLE_COUNT];
    uint32_t first_corrupt_intr_table[EL_INTR_TABLE_COUNT];
};

static uint32_t el_u32_env(const char *name, uint32_t fallback)
{
    return (uint32_t)s61_uint_env(name, fallback, UINT32_MAX);
}

static struct mCore *el_open_fresh(const char *rom_path,
                                   const char *save_path,
                                   const struct Fixture *fixture)
{
    /* libmGBA 0.10.x classifies its deterministic writer/reader RTC delta as
     * an error.  Reuse the embedded harness's exact-format suppression only
     * while attaching a save; all other warning/error output remains fatal. */
    s61_allow_savedata_time_offset_notice = true;
    struct mCore *core = s61_open_fresh(rom_path, save_path, fixture);
    s61_allow_savedata_time_offset_notice = false;
    return core;
}

static void el_close_exact_srm(struct mCore *core, const char *save_path)
{
    uint8_t *savedata = s61_cow_clone_savedata(core);
    bootstrap_close_core(core);
    s61_write_exact_binary(save_path, savedata, BOOTSTRAP_SAVE_SIZE);
    free(savedata);
}

static uint64_t el_framebuffer_rgb_fnv1a64(const color_t *video)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    for (unsigned index = 0U; index < 240U * 160U; ++index) {
        uint32_t pixel = (uint32_t)video[index];
        for (unsigned byte = 0U; byte < 3U; ++byte) {
            hash ^= (uint8_t)(pixel >> (byte * 8U));
            hash *= UINT64_C(1099511628211);
        }
    }
    return hash;
}

static uint64_t el_ppm_rgb_fnv1a64(const char *path)
{
    static const uint8_t header[] = "P6\n240 160\n255\n";
    FILE *stream = fopen(path, "rb");
    if (stream == NULL)
        s61_die("event lifecycle PPM readback open failed");
    uint8_t actual_header[sizeof(header) - 1U];
    if (fread(actual_header, 1U, sizeof(actual_header), stream)
            != sizeof(actual_header)
        || memcmp(actual_header, header, sizeof(actual_header)) != 0) {
        (void)fclose(stream);
        s61_die("event lifecycle PPM readback header differs");
    }
    uint64_t hash = UINT64_C(14695981039346656037);
    for (unsigned index = 0U; index < 240U * 160U * 3U; ++index) {
        int byte = fgetc(stream);
        if (byte == EOF) {
            (void)fclose(stream);
            s61_die("event lifecycle PPM RGB readback is truncated");
        }
        hash ^= (uint8_t)byte;
        hash *= UINT64_C(1099511628211);
    }
    int extra = fgetc(stream);
    bool read_error = ferror(stream) != 0;
    int close_result = fclose(stream);
    if (extra != EOF || read_error || close_result != 0)
        s61_die("event lifecycle PPM RGB readback length differs");
    return hash;
}

static uint64_t el_write_ppm(const char *directory, const char *name)
{
    char path[4096];
    int length = snprintf(path, sizeof(path), "%s/%s", directory, name);
    if (length <= 0 || (size_t)length >= sizeof(path))
        s61_die("event lifecycle PPM path formatting failed");
    uint64_t hash = el_framebuffer_rgb_fnv1a64(s61_video);
    bootstrap_write_ppm(path, s61_video);
    int ppm_length = snprintf(path, sizeof(path), "%s/%s.ppm",
                              directory, name);
    if (ppm_length <= 0 || (size_t)ppm_length >= sizeof(path))
        s61_die("event lifecycle PPM readback path formatting failed");
    if (el_ppm_rgb_fnv1a64(path) != hash)
        s61_die("event lifecycle saved PPM RGB differs from framebuffer");
    return hash;
}

static void el_read_position(struct mCore *core, uint16_t *x, uint16_t *y)
{
    uint32_t save1 = world_save1(core, s61_case_name);
    *x = read16(core, save1);
    *y = read16(core, save1 + 2U);
}

static void el_walk_axis(struct mCore *core, uint16_t target,
                         bool horizontal, uint16_t *x, uint16_t *y,
                         struct FixtureResult *movement)
{
    while ((horizontal ? *x : *y) != target) {
        uint16_t key;
        if (horizontal)
            key = *x < target ? WORLD_KEY_RIGHT : WORLD_KEY_LEFT;
        else
            key = *y < target ? WORLD_KEY_DOWN : WORLD_KEY_UP;
        if (!world_walk_to_new_tile(core, key, x, y, movement))
            s61_die("event lifecycle authored physical path was blocked");
    }
}

static void el_trash_coordinate(unsigned id, uint16_t *x, uint16_t *y)
{
    if (id == 0U || id > 15U)
        s61_die("Vermilion switch ID is outside 1..15");
    unsigned index = id - 1U;
    *x = (uint16_t)(1U + (index % 5U) * 2U);
    *y = (uint16_t)(10U + (index / 5U) * 2U);
}

static unsigned el_walk_to_trash(struct mCore *core, unsigned id)
{
    uint16_t target_x;
    uint16_t target_y;
    uint16_t x;
    uint16_t y;
    struct FixtureResult movement = {0};
    el_trash_coordinate(id, &target_x, &target_y);
    el_read_position(core, &x, &y);

    /* Trash cans occupy odd x on even rows.  Cross each can row only on an
     * adjacent even-x aisle, then approach from the open row below it. */
    uint16_t aisle_x = target_x == 1U ? 0U : (uint16_t)(target_x - 1U);
    el_walk_axis(core, aisle_x, true, &x, &y, &movement);
    el_walk_axis(core, (uint16_t)(target_y + 1U), false,
                 &x, &y, &movement);
    el_walk_axis(core, target_x, true, &x, &y, &movement);
    if (x != target_x || y != target_y + 1U)
        s61_die("Vermilion physical path did not end below trash can");
    return movement.successful_steps;
}

static uint64_t el_gym_metatile_hash(struct mCore *core)
{
    uint64_t hash = UINT64_C(1469598103934665603);
    for (uint16_t y = 6U; y <= 7U; ++y) {
        for (uint16_t x = 3U; x <= 7U; ++x) {
            uint32_t id = s61_call_synced(
                core, EL_MAP_GRID_GET_METATILE_ID_AT,
                x + EL_FIELD_BORDER, y + EL_FIELD_BORDER, 0U, 0U);
            hash ^= (uint16_t)id;
            hash *= UINT64_C(1099511628211);
        }
    }
    return hash;
}

static unsigned el_read_var(struct mCore *core, uint16_t id)
{
    return s61_call_synced(core, WORLD_VAR_GET, id, 0U, 0U, 0U);
}

static unsigned el_interact_trash(struct mCore *core, unsigned id,
                                  uint32_t root_base, const char *directory,
                                  const char *label, unsigned *walked)
{
    *walked += el_walk_to_trash(core, id);
    char artifact[4096];
    struct S61Capture capture = s61_new_capture(
        directory, label, artifact, sizeof(artifact));
    uint32_t root = root_base + (id - 1U) * 11U;
    capture.watched_script_pointer_start = root;
    capture.watched_script_pointer_end = root + 10U;
    if (!s61_drive_interaction(core, WORLD_KEY_UP,
                               S61_CHOICE_ADVANCE, &capture, false)
        || !s61_field_terminal(core)
        || capture.watched_script_pointer_hits == 0U
        || capture.invalid_control_flow)
        s61_die("Vermilion trash direction+A owner did not release");
    s61_write_peak_frame(&capture, "peak.ppm");
    return capture.watched_script_pointer_hits;
}

static void el_case_vermilion(const char *rom_path, const char *directory)
{
    const uint16_t persistent_flag = (uint16_t)el_u32_env(
        "EL_GYM_PERSISTENT_FLAG", 0x1871U);
    const uint32_t root_base = el_u32_env(
        "EL_GYM_TRASH_ROOT_BASE", 0x094316D0U);
    struct S61Interaction interaction = {
        EL_GYM_GROUP, EL_GYM_MAP, 5U, 18U, WORLD_KEY_UP, 0U, 0U,
    };
    struct Fixture fixture = s61_world_fixture(
        "event-lifecycle-vermilion", &interaction);
    char save_path[4096];
    s61_save_path(save_path, sizeof(save_path), directory, fixture.name);
    s61_generate(rom_path, save_path, &fixture);
    struct mCore *core = el_open_fresh(rom_path, save_path, &fixture);
    struct ElGymTrace trace = {0};
    uint64_t baseline_ppm_hash;
    uint64_t open_ppm_hash;
    uint64_t reentry_ppm_hash;
    if (s61_flag(core, persistent_flag) != 0U
        || s61_flag(core, EL_TEMP_FLAG_FIRST_SWITCH) != 0U)
        s61_die("Vermilion initial switch flags are dirty");
    trace.first_id_initial = el_read_var(core, EL_VAR_TEMP_0);
    trace.second_id_initial = el_read_var(core, EL_VAR_TEMP_1);
    if (trace.first_id_initial == trace.second_id_initial) {
        fprintf(stderr, "Vermilion switch init debug temp0=%u temp1=%u "
                "persistent=%u temp_flag=%u map_script=%08" PRIX32 "\n",
                trace.first_id_initial, trace.second_id_initial,
                s61_flag(core, persistent_flag),
                s61_flag(core, EL_TEMP_FLAG_FIRST_SWITCH),
                read32(core, WORLD_MAP_HEADER + 8U));
        s61_die("Vermilion generated identical first/second switches");
    }
    trace.baseline_metatile_hash = el_gym_metatile_hash(core);
    baseline_ppm_hash = el_write_ppm(directory, "vermilion-baseline");

    trace.owner_hits += el_interact_trash(
        core, trace.first_id_initial, root_base, directory,
        "vermilion-first", &trace.actual_walk_steps);
    trace.half_metatile_hash = el_gym_metatile_hash(core);
    if (s61_flag(core, EL_TEMP_FLAG_FIRST_SWITCH) == 0U
        || s61_flag(core, persistent_flag) != 0U
        || trace.half_metatile_hash == trace.baseline_metatile_hash)
        s61_die("Vermilion first switch did not set TEMP_FLAG/half door");

    trace.wrong_id = 1U;
    while (trace.wrong_id == trace.first_id_initial
           || trace.wrong_id == trace.second_id_initial)
        ++trace.wrong_id;
    if (trace.wrong_id > 15U)
        s61_die("Vermilion could not choose a distinct wrong switch");
    trace.owner_hits += el_interact_trash(
        core, trace.wrong_id, root_base, directory,
        "vermilion-wrong", &trace.actual_walk_steps);
    trace.reset_metatile_hash = el_gym_metatile_hash(core);
    if (s61_flag(core, EL_TEMP_FLAG_FIRST_SWITCH) != 0U
        || s61_flag(core, persistent_flag) != 0U
        || trace.reset_metatile_hash != trace.baseline_metatile_hash)
        s61_die("Vermilion wrong second switch did not reset flag/door");

    trace.first_id_retry = el_read_var(core, EL_VAR_TEMP_0);
    trace.second_id_retry = el_read_var(core, EL_VAR_TEMP_1);
    if (trace.first_id_retry == trace.second_id_retry)
        s61_die("Vermilion retry generated identical switches");
    trace.owner_hits += el_interact_trash(
        core, trace.first_id_retry, root_base, directory,
        "vermilion-retry-first", &trace.actual_walk_steps);
    trace.owner_hits += el_interact_trash(
        core, trace.second_id_retry, root_base, directory,
        "vermilion-retry-second", &trace.actual_walk_steps);
    trace.open_metatile_hash = el_gym_metatile_hash(core);
    if (s61_flag(core, persistent_flag) == 0U
        || s61_flag(core, EL_TEMP_FLAG_FIRST_SWITCH) == 0U
        || trace.open_metatile_hash == trace.baseline_metatile_hash
        || trace.open_metatile_hash == trace.half_metatile_hash)
        s61_die("Vermilion correct pair did not persist/open door");
    open_ppm_hash = el_write_ppm(directory, "vermilion-open");
    if (!s61_normal_input_save(core))
        s61_die("Vermilion normal START/SAVE failed");
    el_close_exact_srm(core, save_path);

    core = el_open_fresh(rom_path, save_path, &fixture);
    trace.reentry_metatile_hash = el_gym_metatile_hash(core);
    if (s61_flag(core, persistent_flag) == 0U
        || s61_flag(core, EL_TEMP_FLAG_FIRST_SWITCH) != 0U
        || trace.reentry_metatile_hash != trace.open_metatile_hash
        || !s61_field_terminal(core))
        s61_die("Vermilion fresh Continue/reentry state differs");
    reentry_ppm_hash = el_write_ppm(directory, "vermilion-reentry");
    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"case\":\"vermilion_gym_lifecycle\","
           "\"preparation_teleport_only\":true,"
           "\"direct_owner_or_script_calls\":0,"
           "\"map\":\"98/40\",\"persistent_flag\":\"0x%04X\","
           "\"temp_flag\":\"0x0001\","
           "\"switches_initial\":[%u,%u],\"wrong_switch\":%u,"
           "\"switches_retry\":[%u,%u],"
           "\"actual_walk_steps\":%u,\"direction_plus_a\":true,"
           "\"owner_pc_hits\":%u,\"failure_reset\":true,"
           "\"success_persisted\":true,\"fresh_core_continue\":true,"
           "\"reentry_temp_reset\":true,\"field_input_recovered\":true,"
           "\"metatile_hashes\":{\"baseline\":\"%016" PRIX64
           "\",\"half\":\"%016" PRIX64 "\",\"reset\":\"%016" PRIX64
           "\",\"open\":\"%016" PRIX64 "\",\"reentry\":\"%016" PRIX64
           "\"},\"srm\":\"event-lifecycle-vermilion.srm\","
           "\"ppms\":[\"vermilion-baseline.ppm\","
           "\"vermilion-open.ppm\",\"vermilion-reentry.ppm\"],"
           "\"framebuffer_artifact_fnv1a64\":{"
           "\"vermilion-baseline.ppm\":\"%016" PRIX64 "\","
           "\"vermilion-open.ppm\":\"%016" PRIX64 "\","
           "\"vermilion-reentry.ppm\":\"%016" PRIX64 "\"},"
           "\"framebuffer_artifact_roles\":{"
           "\"vermilion-baseline.ppm\":\"pre_switch_baseline\","
           "\"vermilion-open.ppm\":\"success_open\","
           "\"vermilion-reentry.ppm\":\"fresh_continue_reentry\"},"
           "\"failed\":0,\"untested\":0,\"warnings\":0}\n",
           persistent_flag, trace.first_id_initial,
           trace.second_id_initial, trace.wrong_id,
           trace.first_id_retry, trace.second_id_retry,
           trace.actual_walk_steps, trace.owner_hits,
           trace.baseline_metatile_hash, trace.half_metatile_hash,
           trace.reset_metatile_hash, trace.open_metatile_hash,
           trace.reentry_metatile_hash, baseline_ppm_hash,
           open_ppm_hash, reentry_ppm_hash);
    el_close_exact_srm(core, save_path);
}

static unsigned el_active_task_count(struct mCore *core,
                                     uint32_t *first_function)
{
    unsigned count = 0U;
    for (unsigned index = 0U; index < EL_TASK_COUNT; ++index) {
        uint32_t task = WORLD_TASKS + index * WORLD_TASK_SIZE;
        if (read8(core, task + EL_TASK_ACTIVE_OFFSET) == 0U)
            continue;
        uint32_t function = read32(core, task);
        if (function >= 0x08000001U && function < 0x0A000000U) {
            if (*first_function == 0U)
                *first_function = function;
            ++count;
        }
    }
    return count;
}

/* The stock multichoice task writes 0x7f for B, but the ferry owner then
 * immediately calls IsPlayerLeftOfVermilionSailor, which legitimately
 * replaces VAR_RESULT before the field becomes terminal.  Observe the
 * transient value at CPU-instruction granularity while still driving only
 * ordinary keys; checking the terminal value would reject a real cancel. */
static void el_step_cancel_observer(struct mCore *core, uint16_t keys,
                                    unsigned frames,
                                    struct S61Capture *capture,
                                    struct ElCancelTrace *trace)
{
    core->setKeys(core, keys);
    uint32_t first_frame = core->frameCounter(core);
    while ((uint32_t)(core->frameCounter(core) - first_frame) < frames) {
        if (read16(core, WORLD_SPECIAL_RESULT) == 0x7FU)
            trace->menu_cancel_seen = true;
        if (s61_capture_invalid_control_flow(core, capture))
            return;
        uint32_t before = core->frameCounter(core);
        core->step(core);
        if (read16(core, WORLD_SPECIAL_RESULT) == 0x7FU)
            trace->menu_cancel_seen = true;
        if (s61_capture_invalid_control_flow(core, capture))
            return;
        if (core->frameCounter(core) != before)
            s61_capture_frame(core, capture);
    }
}

static struct ElCancelTrace el_cancel_ferry(
    struct mCore *core, const struct ElFerryOwner *owner,
    struct S61Capture *capture)
{
    struct ElCancelTrace trace = {0};
    s61_pulse(core, WORLD_KEY_RIGHT, 2U, 10U, capture);
    s61_pulse(core, WORLD_KEY_A, 2U, 20U, capture);
    ++trace.input_pulses;
    bool saw_owner = world_script_enabled(core)
        || capture->active_frames != 0U || capture->count != 0U
        || capture->printer_call_count != 0U;
    unsigned quiet = 0U;
    for (unsigned pulse = 0U; pulse < 160U; ++pulse) {
        if (world_script_enabled(core)
            || capture->active_frames != 0U || capture->count != 0U
            || capture->printer_call_count != 0U)
            saw_owner = true;
        bool terminal = world_overworld(core)
            && !world_script_enabled(core)
            && read8(core, S61_FIELD_MESSAGE_STATE) == 0U;
        if (terminal && saw_owner) {
            if (++quiet >= 6U) {
                trace.released = true;
                break;
            }
            el_step_cancel_observer(core, 0U, 15U, capture, &trace);
            continue;
        }
        quiet = 0U;
        uint16_t key = capture->count != 0U ? WORLD_KEY_B : WORLD_KEY_A;
        el_step_cancel_observer(core, key, 2U, capture, &trace);
        el_step_cancel_observer(core, 0U, 45U, capture, &trace);
        ++trace.input_pulses;
        if (capture->invalid_control_flow)
            break;
    }
    trace.post_cancel_result = read16(core, WORLD_SPECIAL_RESULT);
    (void)owner;
    return trace;
}

static struct ElHeapWatch el_heap_watch_begin(struct mCore *core)
{
    struct ElHeapWatch watch = {
        /* The observed 0x2000-byte allocation starts at 0x02015324.  Watch
         * its complete 16-byte allocator header plus the first word beyond
         * the allocation, so the first under/overflowing writer is not
         * inferred from a later Free assertion. */
        .addresses = {
            0x02015314U, 0x02015318U, 0x0201531CU,
            0x02015320U, 0x02017324U,
        },
    };
    for (unsigned index = 0U; index < EL_HEAP_WATCH_ADDRESS_COUNT; ++index)
        watch.values[index] = read32(core, watch.addresses[index]);
    for (unsigned index = 0U; index < EL_INTR_TABLE_COUNT; ++index)
        watch.initial_intr_table[index] = read32(
            core, 0x03003580U + index * 4U);
    return watch;
}

static void el_heap_watch_step(struct mCore *core,
                               struct ElHeapWatch *watch)
{
    uint32_t raw_pc = (uint32_t)read_register(core, "pc");
    uint32_t instruction_pc = (raw_pc - 4U) & ~1U;
    uint32_t lr = (uint32_t)read_register(core, "lr");
    uint32_t registers[4] = {
        (uint32_t)read_register(core, "r0"),
        (uint32_t)read_register(core, "r1"),
        (uint32_t)read_register(core, "r2"),
        (uint32_t)read_register(core, "r3"),
    };
    struct ElInstructionTrace *history = &watch->history[
        watch->instruction_count % EL_HEAP_HISTORY_COUNT];
    *history = (struct ElInstructionTrace){
        .ordinal = watch->instruction_count,
        .raw_pc = raw_pc,
        .instruction_pc = instruction_pc,
        .cpsr = (uint32_t)read_register(core, "cpsr"),
        .lr = lr,
        .sp = (uint32_t)read_register(core, "sp"),
        .r0 = registers[0],
        .r1 = registers[1],
        .r2 = registers[2],
        .r3 = registers[3],
        .frame = core->frameCounter(core),
        .callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2),
        .battle_pointer = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
        .battle_outcome = read8(core, BATTLE_CORE_BATTLE_OUTCOME),
        .party_count = read8(core, BOOTSTRAP_PLAYER_COUNT),
    };
    if (watch->first_bag_open_ordinal == 0U
        && read8(core, BATTLE_CORE_BAG_STATE + 5U) != 0U)
        watch->first_bag_open_ordinal = watch->instruction_count + 1U;
    if (watch->first_outcome_ordinal == 0U
        && history->battle_outcome != 0U)
        watch->first_outcome_ordinal = watch->instruction_count + 1U;
    if (watch->first_party_two_ordinal == 0U && history->party_count == 2U)
        watch->first_party_two_ordinal = watch->instruction_count + 1U;
    if (watch->first_runtime_cleanup_ordinal == 0U
        && history->battle_pointer == 0U)
        watch->first_runtime_cleanup_ordinal = watch->instruction_count + 1U;
    uint32_t before[EL_HEAP_WATCH_ADDRESS_COUNT];
    memcpy(before, watch->values, sizeof(before));
    core->step(core);
    for (unsigned index = 0U; index < EL_HEAP_WATCH_ADDRESS_COUNT; ++index) {
        uint32_t after = read32(core, watch->addresses[index]);
        if (after != before[index]) {
            struct ElHeapTransition transition = {
                watch->addresses[index], before[index], after,
                instruction_pc, lr, registers[0], registers[1],
                registers[2], registers[3],
                watch->previous_instruction_pc, watch->previous_lr,
                watch->previous_r0, watch->previous_r1,
                watch->instruction_count,
            };
            if (watch->transition_count < EL_HEAP_TRANSITION_LIMIT)
                watch->transitions[watch->transition_count++] = transition;
            else
                watch->overflow = true;
            if (index == 0U && after == 0x00000021U
                && !watch->first_corrupt_seen) {
                watch->first_corrupt_seen = true;
                watch->first_corrupt = transition;
                memcpy(watch->first_corrupt_history, watch->history,
                       sizeof(watch->history));
                watch->first_corrupt_history_end =
                    watch->instruction_count + 1U;
                for (unsigned intr = 0U;
                     intr < EL_INTR_TABLE_COUNT; ++intr)
                    watch->first_corrupt_intr_table[intr] = read32(
                        core, 0x03003580U + intr * 4U);
            }
        }
        watch->values[index] = after;
    }
    watch->previous_valid = true;
    watch->previous_instruction_pc = instruction_pc;
    watch->previous_lr = lr;
    watch->previous_r0 = registers[0];
    watch->previous_r1 = registers[1];
    ++watch->instruction_count;
}

static void el_heap_watch_print(struct mCore *core,
                                const struct ElHeapWatch *watch)
{
    fprintf(stderr, "Route16 heap watch transitions=%u overflow=%u",
            watch->transition_count, watch->overflow ? 1U : 0U);
    for (unsigned index = 0U; index < watch->transition_count; ++index) {
        const struct ElHeapTransition *row = &watch->transitions[index];
        fprintf(stderr,
                " [%u addr=%08" PRIX32 " old=%08" PRIX32
                " new=%08" PRIX32 " pc=%08" PRIX32
                " lr=%08" PRIX32 " r0=%08" PRIX32
                " r1=%08" PRIX32 " r2=%08" PRIX32
                " r3=%08" PRIX32 " previous_pc=%08" PRIX32
                " previous_lr=%08" PRIX32
                " previous_r0=%08" PRIX32
                " previous_r1=%08" PRIX32 "]",
                index, row->address, row->before, row->after,
                row->instruction_pc, row->lr, row->r0, row->r1,
                row->r2, row->r3, row->previous_instruction_pc,
                row->previous_lr, row->previous_r0, row->previous_r1);
    }
    fputc('\n', stderr);
    if (watch->first_corrupt_seen) {
        const struct ElHeapTransition *row = &watch->first_corrupt;
        fprintf(stderr,
                "Route16 first heap-header corruption addr=%08" PRIX32
                " old=%08" PRIX32 " new=%08" PRIX32
                " writer_pc=%08" PRIX32 " lr=%08" PRIX32
                " r0=%08" PRIX32 " r1=%08" PRIX32
                " r2=%08" PRIX32 " r3=%08" PRIX32
                " previous_pc=%08" PRIX32
                " previous_lr=%08" PRIX32
                " previous_r0=%08" PRIX32
                " previous_r1=%08" PRIX32 "\n",
                row->address, row->before, row->after,
                row->instruction_pc, row->lr, row->r0, row->r1,
                row->r2, row->r3, row->previous_instruction_pc,
                row->previous_lr, row->previous_r0, row->previous_r1);
    }
    fprintf(stderr,
            "Route16 capture lifecycle instructions=%" PRIu64
            " first_bag_open=%" PRIu64 " first_outcome=%" PRIu64
            " first_party_two=%" PRIu64 " first_runtime_cleanup=%" PRIu64
            " first_corrupt=%" PRIu64 "\n",
            watch->instruction_count, watch->first_bag_open_ordinal,
            watch->first_outcome_ordinal, watch->first_party_two_ordinal,
            watch->first_runtime_cleanup_ordinal,
            watch->first_corrupt_seen ? watch->first_corrupt.ordinal : 0U);
    uint64_t history_end = watch->first_corrupt_seen
        ? watch->first_corrupt_history_end : watch->instruction_count;
    uint64_t history_start = history_end > EL_HEAP_HISTORY_COUNT
        ? history_end - EL_HEAP_HISTORY_COUNT : 0U;
    for (uint64_t ordinal = history_start; ordinal < history_end; ++ordinal) {
        const struct ElInstructionTrace *rows = watch->first_corrupt_seen
            ? watch->first_corrupt_history : watch->history;
        const struct ElInstructionTrace *row = &rows[
            ordinal % EL_HEAP_HISTORY_COUNT];
        fprintf(stderr,
                "Route16 pc-history ord=%" PRIu64
                " raw=%08" PRIX32 " current=%08" PRIX32
                " cpsr=%08" PRIX32 " lr=%08" PRIX32
                " sp=%08" PRIX32 " r0=%08" PRIX32
                " r1=%08" PRIX32 " r2=%08" PRIX32
                " r3=%08" PRIX32 " frame=%" PRIu32
                " cb=%08" PRIX32 " battle=%08" PRIX32
                " outcome=%u party=%u\n",
                row->ordinal, row->raw_pc, row->instruction_pc,
                row->cpsr, row->lr, row->sp, row->r0, row->r1,
                row->r2, row->r3, row->frame, row->callback,
                row->battle_pointer, row->battle_outcome,
                row->party_count);
    }
    for (unsigned index = 0U; index < EL_INTR_TABLE_COUNT; ++index) {
        uint32_t address = 0x03003580U + index * 4U;
        fprintf(stderr,
                "Route16 intr-table index=%u address=%08" PRIX32
                " initial=%08" PRIX32 " at_corruption=%08" PRIX32
                " final=%08" PRIX32 "\n",
                index, address, watch->initial_intr_table[index],
                watch->first_corrupt_intr_table[index],
                read32(core, address));
    }
}

static void el_ball_frames(struct mCore *core,
                           struct S61BallThrowResult *result,
                           bool *battle_runtime_seen,
                           struct ElHeapWatch *watch,
                           uint16_t keys, unsigned frames)
{
    core->setKeys(core, keys);
    uint32_t first_frame = core->frameCounter(core);
    while ((uint32_t)(core->frameCounter(core) - first_frame) < frames) {
        s61_sample_ball_throw(core, result, battle_runtime_seen);
        if (watch->first_corrupt_seen)
            return;
        if (s61_illegal_opcode_dumped)
            return;
        uint32_t raw_pc = (uint32_t)read_register(core, "pc");
        if (!s61_cpu_pc_is_executable(raw_pc))
            return;
        el_heap_watch_step(core, watch);
        s61_sample_ball_throw(core, result, battle_runtime_seen);
    }
}

static void el_ball_pulse(struct mCore *core,
                          struct S61BallThrowResult *result,
                          bool *battle_runtime_seen,
                          struct ElHeapWatch *watch,
                          uint16_t key, unsigned released)
{
    el_ball_frames(core, result, battle_runtime_seen, watch, key, 2U);
    el_ball_frames(core, result, battle_runtime_seen, watch, 0U, released);
}

static struct S61BallThrowResult el_throw_master_ball_with_heap_watch(
    struct mCore *core, const struct Fixture *fixture,
    struct ElHeapWatch *watch)
{
    struct S61BallThrowResult result = {0};
    bool battle_runtime_seen = false;
    for (unsigned cycle = 0U; cycle < 480U; ++cycle) {
        s61_sample_ball_throw(core, &result, &battle_runtime_seen);
        if (result.runtime_cleaned)
            return result;
        if (watch->first_corrupt_seen)
            break;
        if (s61_illegal_opcode_dumped)
            break;
        if (!s61_cpu_pc_is_executable(
                (uint32_t)read_register(core, "pc")))
            break;
        if (read8(core, WORLD_BATTLE_BUFFER_A)
                == WORLD_BATTLE_COMMAND_CHOOSE_ACTION) {
            result.choose_action_seen = true;
            uint8_t cursor = read8(core, BATTLE_CORE_ACTION_SELECTION_CURSOR);
            if (cursor > 3U)
                s61_die("heap-watch battle action cursor invalid");
            if (cursor == WORLD_BATTLE_ACTION_USE_ITEM) {
                el_ball_pulse(core, &result, &battle_runtime_seen, watch,
                              WORLD_KEY_LEFT, 24U);
                result.actual_direction_input = true;
                ++result.input_pulses;
                cursor = read8(core, BATTLE_CORE_ACTION_SELECTION_CURSOR);
            }
            if ((cursor & 2U) != 0U) {
                el_ball_pulse(core, &result, &battle_runtime_seen, watch,
                              WORLD_KEY_UP, 24U);
                result.actual_direction_input = true;
                ++result.input_pulses;
            }
            cursor = read8(core, BATTLE_CORE_ACTION_SELECTION_CURSOR);
            if ((cursor & 1U) == 0U) {
                el_ball_pulse(core, &result, &battle_runtime_seen, watch,
                              WORLD_KEY_RIGHT, 24U);
                result.actual_direction_input = true;
                ++result.input_pulses;
            }
            result.action_cursor = read8(
                core, BATTLE_CORE_ACTION_SELECTION_CURSOR);
            if (result.action_cursor != WORLD_BATTLE_ACTION_USE_ITEM)
                s61_die("heap-watch keys did not select Bag");
            el_ball_pulse(core, &result, &battle_runtime_seen, watch,
                          WORLD_KEY_A, BATTLE_CORE_MENU_INPUT_WAIT);
            result.actual_a_input = true;
            ++result.input_pulses;
            result.chosen_action = read8(core, BATTLE_CORE_CHOSEN_ACTIONS);
            continue;
        }
        if (result.bag_opened || cycle % 5U == 4U) {
            el_ball_pulse(core, &result, &battle_runtime_seen, watch,
                          WORLD_KEY_A, BATTLE_CORE_MENU_INPUT_WAIT);
            result.actual_a_input = true;
            ++result.input_pulses;
        } else {
            el_ball_frames(core, &result, &battle_runtime_seen, watch,
                           0U, 30U);
        }
    }
    el_heap_watch_print(core, watch);
    (void)fixture;
    return result;
}

static void el_run_frames(struct mCore *core, uint16_t keys,
                          unsigned frames, struct ElRunTrace *trace)
{
    core->setKeys(core, keys);
    uint32_t first_frame = core->frameCounter(core);
    while ((uint32_t)(core->frameCounter(core) - first_frame) < frames) {
        uint8_t outcome = read8(core, BATTLE_CORE_BATTLE_OUTCOME);
        if (outcome != 0U)
            trace->outcome = outcome;
        if (read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U
            || read8(core, ADDR_BATTLERS_COUNT) != 0U)
            trace->runtime_seen = true;
        uint32_t callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
        if (callback != BOOTSTRAP_CB2_OVERWORLD
            && trace->first_battle_callback == 0U)
            trace->first_battle_callback = callback;
        core->step(core);
    }
}

static void el_run_pulse(struct mCore *core, uint16_t key,
                         unsigned released, struct ElRunTrace *trace)
{
    el_run_frames(core, key, 2U, trace);
    el_run_frames(core, 0U, released, trace);
    ++trace->input_pulses;
}

static struct ElRunTrace el_run_from_wild_with_keys(struct mCore *core)
{
    struct ElRunTrace trace = {0};
    bool run_selected = false;
    for (unsigned pulse = 0U; pulse < 1200U; ++pulse) {
        el_run_frames(core, 0U, 1U, &trace);
        if (trace.runtime_seen && world_overworld(core)) {
            el_run_frames(core, 0U, 180U, &trace);
            if (world_overworld(core) && !world_script_enabled(core)) {
                trace.field_terminal = true;
                return trace;
            }
        }
        if (!trace.runtime_seen) {
            el_run_frames(core, 0U, 30U, &trace);
            if (pulse % 6U == 5U) {
                el_run_pulse(core, WORLD_KEY_A, 30U, &trace);
                trace.actual_a_input = true;
            }
            continue;
        }
        if (read8(core, WORLD_BATTLE_BUFFER_A)
                == WORLD_BATTLE_COMMAND_CHOOSE_ACTION) {
            uint8_t cursor = read8(core, BATTLE_CORE_ACTION_SELECTION_CURSOR);
            if (cursor > 3U)
                s61_die("Route16 Run action cursor left the 2x2 menu");
            if (cursor == 3U) {
                el_run_pulse(core, WORLD_KEY_LEFT, 24U, &trace);
                cursor = read8(core, BATTLE_CORE_ACTION_SELECTION_CURSOR);
            }
            if ((cursor & 2U) == 0U) {
                el_run_pulse(core, WORLD_KEY_DOWN, 24U, &trace);
                cursor = read8(core, BATTLE_CORE_ACTION_SELECTION_CURSOR);
            }
            if ((cursor & 1U) == 0U) {
                el_run_pulse(core, WORLD_KEY_RIGHT, 24U, &trace);
                cursor = read8(core, BATTLE_CORE_ACTION_SELECTION_CURSOR);
            }
            trace.actual_direction_input = true;
            if (cursor != 3U)
                s61_die("Route16 direction keys did not select Run");
            el_run_pulse(core, WORLD_KEY_A,
                         BATTLE_CORE_MENU_INPUT_WAIT, &trace);
            trace.actual_a_input = true;
            run_selected = true;
            continue;
        }
        for (unsigned bank = 0U; bank < 4U; bank += 2U) {
            if (read8(core, 0x02022B24U + bank * 0x200U)
                    == WORLD_BATTLE_COMMAND_CHOOSE_POKEMON)
                s61_die("Route16 Run unexpectedly required party switch");
        }
        if (!run_selected || pulse % 5U == 4U) {
            el_run_pulse(core, WORLD_KEY_A,
                         BATTLE_CORE_MENU_INPUT_WAIT, &trace);
            trace.actual_a_input = true;
        } else {
            el_run_frames(core, 0U, 30U, &trace);
        }
        if (world_overworld(core) && !world_script_enabled(core)) {
            el_run_frames(core, 0U, 120U, &trace);
            trace.field_terminal = true;
            return trace;
        }
    }
    s61_die("Route16 Run did not return to field through keys");
    return trace;
}

static struct ElFerryTrace el_board_ferry(
    struct mCore *core, const struct ElFerryOwner *owner,
    const char *directory)
{
    char artifact[4096];
    struct S61Capture capture = s61_new_capture(
        directory, owner->stem, artifact, sizeof(artifact));
    capture.watched_script_pointer_start = owner->root;
    capture.watched_script_pointer_end = owner->root + 127U;
    capture.event_consumer_instruction_pc = EL_FERRY_SPECIAL;
    struct ElFerryTrace trace = {0};
    uint32_t baseline_task_function = 0U;
    unsigned baseline_tasks = el_active_task_count(
        core, &baseline_task_function);
    (void)baseline_task_function;
    s61_pulse(core, WORLD_KEY_RIGHT, 2U, 10U, &capture);
    s61_pulse(core, WORLD_KEY_A, 2U, 20U, &capture);
    ++trace.input_pulses;
    unsigned field_stable = 0U;
    for (unsigned cycle = 0U; cycle < 720U; ++cycle) {
        uint32_t callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
        if (callback != BOOTSTRAP_CB2_OVERWORLD) {
            trace.callback_seen = true;
            if (trace.first_nonfield_callback == 0U)
                trace.first_nonfield_callback = callback;
        }
        uint32_t task_function = 0U;
        unsigned tasks = el_active_task_count(core, &task_function);
        if (trace.callback_seen && tasks > baseline_tasks) {
            trace.task_seen = true;
            if (trace.first_task_function == 0U)
                trace.first_task_function = task_function;
        }
        uint32_t save1 = world_save1(core, owner->id);
        bool destination = read8(core, save1 + 4U)
                == EL_FERRY_EXPECTED_GROUP
            && read8(core, save1 + 5U) == EL_FERRY_EXPECTED_MAP
            && read16(core, save1) == EL_FERRY_EXPECTED_X
            && read16(core, save1 + 2U) == EL_FERRY_EXPECTED_Y;
        if (destination && s61_field_terminal(core)) {
            if (++field_stable >= 6U) {
                trace.arrived = true;
                break;
            }
        } else {
            field_stable = 0U;
        }
        uint16_t key = (!trace.callback_seen && cycle % 3U == 2U)
            ? WORLD_KEY_A : 0U;
        if (key != 0U)
            ++trace.input_pulses;
        s61_step_capture_frames(core, key, key != 0U ? 2U : 15U,
                                &capture);
        if (key != 0U)
            s61_step_capture_frames(core, 0U, 43U, &capture);
    }
    trace.owner_hits = capture.watched_script_pointer_hits;
    trace.special_hits = capture.event_consumer_instruction_hits;
    trace.owner_seen = trace.owner_hits != 0U;
    trace.special_seen = trace.special_hits != 0U;
    if (!trace.owner_seen || !trace.special_seen || !trace.callback_seen
        || !trace.task_seen || !trace.arrived || capture.invalid_control_flow) {
        uint32_t save1 = world_save1(core, owner->id);
        uint32_t final_task_function = 0U;
        unsigned final_tasks = el_active_task_count(
            core, &final_task_function);
        fprintf(stderr,
                "ferry board debug owner=%s owner_seen=%u owner_hits=%u "
                "special_seen=%u special_hits=%u callback_seen=%u "
                "first_callback=%08" PRIX32 " task_seen=%u "
                "first_task=%08" PRIX32 " baseline_tasks=%u "
                "final_tasks=%u final_task=%08" PRIX32 " arrived=%u "
                "map=%u/%u@%u,%u terminal=%u result=%u pulses=%u "
                "script=%08" PRIX32 " callback=%08" PRIX32 "\n",
                owner->id, trace.owner_seen ? 1U : 0U,
                trace.owner_hits, trace.special_seen ? 1U : 0U,
                trace.special_hits, trace.callback_seen ? 1U : 0U,
                trace.first_nonfield_callback, trace.task_seen ? 1U : 0U,
                trace.first_task_function, baseline_tasks, final_tasks,
                final_task_function, trace.arrived ? 1U : 0U,
                read8(core, save1 + 4U), read8(core, save1 + 5U),
                read16(core, save1), read16(core, save1 + 2U),
                s61_field_terminal(core) ? 1U : 0U,
                read16(core, WORLD_SPECIAL_RESULT), trace.input_pulses,
                read32(core, WORLD_SCRIPT_CONTEXT1_POINTER),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2));
        s61_die("ferry boarding owner/task/callback/arrival differs");
    }
    trace.ppm_rgb_fnv1a64 = el_write_ppm(directory, owner->stem);
    return trace;
}

static void el_case_ferry(const char *rom_path, const char *directory)
{
    uint64_t ppm_hashes[
        sizeof(el_ferry_owners) / sizeof(el_ferry_owners[0])] = {0};
    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"case\":\"ferry_all_owner_lifecycle\","
           "\"preparation_teleport_and_engine_var_fixture\":true,"
           "\"preparation_engine_var_writes\":["
           "{\"var\":\"0x4076\",\"value\":0},"
           "{\"var\":\"0x4071\",\"value\":4}],"
           "\"preparation_engine_api_calls_only\":true,"
           "\"host_direct_memory_writes\":0,"
           "\"direct_owner_or_script_calls\":0,"
           "\"direct_special_calls\":0,\"owners\":[");
    for (unsigned index = 0U;
         index < sizeof(el_ferry_owners) / sizeof(el_ferry_owners[0]);
         ++index) {
        const struct ElFerryOwner *owner = &el_ferry_owners[index];
        struct S61Interaction interaction = {
            owner->group, owner->map, 6U, 4U,
            WORLD_KEY_RIGHT, 1U, 2U,
        };
        struct Fixture fixture = s61_world_fixture(owner->stem, &interaction);
        char save_path[4096];
        s61_save_path(save_path, sizeof(save_path), directory, owner->stem);
        s61_generate(rom_path, save_path, &fixture);
        struct mCore *core = el_open_fresh(rom_path, save_path, &fixture);
        (void)s61_call_synced(core, WORLD_VAR_SET,
                             EL_VAR_SCENE_ONE_ISLAND_CENTER, 0U, 0U, 0U);
        (void)s61_call_synced(core, WORLD_VAR_SET,
                             EL_VAR_SCENE_CINNABAR, 4U, 0U, 0U);
        if (el_read_var(core, EL_VAR_SCENE_ONE_ISLAND_CENTER) != 0U
            || el_read_var(core, EL_VAR_SCENE_CINNABAR) != 4U)
            s61_die("ferry menu preparation vars differ");
        unsigned walked = s61_walk_approach(core, &interaction);
        char cancel_label[128];
        int cancel_size = snprintf(cancel_label, sizeof(cancel_label),
                                   "%s-cancel", owner->stem);
        if (cancel_size <= 0
            || (size_t)cancel_size >= sizeof(cancel_label))
            s61_die("ferry cancel label formatting failed");
        char cancel_artifact[4096];
        struct S61Capture cancel = s61_new_capture(
            directory, cancel_label, cancel_artifact,
            sizeof(cancel_artifact));
        cancel.watched_script_pointer_start = owner->root;
        cancel.watched_script_pointer_end = owner->root + 127U;
        struct ElCancelTrace cancel_trace = el_cancel_ferry(
            core, owner, &cancel);
        if (!cancel_trace.released || !cancel_trace.menu_cancel_seen
            || cancel.watched_script_pointer_hits == 0U
            || !s61_field_terminal(core) || cancel.invalid_control_flow) {
            fprintf(stderr,
                    "ferry cancel debug owner=%s released=%u result=%u "
                    "owner_hits=%u messages=%u printers=%u terminal=%u "
                    "lock=%u message=%u script=%08" PRIX32
                    " callback=%08" PRIX32 "\n",
                    owner->id, cancel_trace.released ? 1U : 0U,
                    cancel_trace.post_cancel_result,
                    cancel.watched_script_pointer_hits, cancel.count,
                    cancel.printer_call_count, s61_field_terminal(core),
                    world_script_enabled(core),
                    read8(core, S61_FIELD_MESSAGE_STATE),
                    read32(core, WORLD_SCRIPT_CONTEXT1_POINTER),
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2));
            s61_die("ferry real B cancel did not preserve field");
        }
        unsigned pre_board_one_island = el_read_var(
            core, EL_VAR_SCENE_ONE_ISLAND_CENTER);
        unsigned pre_board_cinnabar = el_read_var(
            core, EL_VAR_SCENE_CINNABAR);
        if (pre_board_one_island != 0U || pre_board_cinnabar != 4U)
            s61_die("ferry cancel changed engine-var fixture before boarding");

        struct ElFerryTrace board = el_board_ferry(
            core, owner, directory);
        ppm_hashes[index] = board.ppm_rgb_fnv1a64;
        board.actual_walk_steps = walked;
        if (!s61_normal_input_save(core))
            s61_die("ferry arrival normal START/SAVE failed");
        el_close_exact_srm(core, save_path);

        struct S61Interaction arrival_interaction = {
            EL_FERRY_EXPECTED_GROUP, EL_FERRY_EXPECTED_MAP,
            EL_FERRY_EXPECTED_X, EL_FERRY_EXPECTED_Y,
            WORLD_KEY_UP, 0U, 0U,
        };
        struct Fixture arrival = s61_world_fixture(
            owner->stem, &arrival_interaction);
        core = el_open_fresh(rom_path, save_path, &arrival);
        if (!s61_field_terminal(core))
            s61_die("ferry fresh Continue did not recover field");
        struct S61FieldRoundtripResult roundtrip = s61_field_roundtrip(
            core, owner->id, EL_FERRY_EXPECTED_GROUP,
            EL_FERRY_EXPECTED_MAP);
        if (!s61_field_roundtrip_exact(&roundtrip))
            s61_die("ferry fresh Continue START/B recovery differs");
        if (index != 0U)
            putchar(',');
        printf("{\"owner_id\":\"%s\",\"map\":\"%u/%u\","
               "\"owner_root\":\"0x%08" PRIX32 "\","
               "\"actual_walk_steps\":%u,\"direction_plus_a\":true,"
               "\"choice_cancel_via_b\":true,\"cancel_result\":127,"
               "\"post_cancel_result\":%u,"
               "\"cancel_owner_pc_hits\":%u,"
               "\"pre_board_engine_var_readback\":{"
               "\"0x4076\":%u,\"0x4071\":%u},"
               "\"choice_zero_via_a\":true,\"boarding\":true,"
               "\"owner_pc_hits\":%u,\"special_pc\":\"0x%08X\","
               "\"special_pc_hits\":%u,"
               "\"first_nonfield_callback\":\"0x%08" PRIX32 "\","
               "\"first_task_function\":\"0x%08" PRIX32 "\","
               "\"task_observed\":true,\"arrival\":\"3/5@23,32\","
               "\"save_via_start_menu\":true,"
               "\"fresh_core_continue\":true,"
               "\"field_input_recovered\":true,"
               "\"srm\":\"%s.srm\",\"ppm\":\"%s.ppm\"}",
               owner->id, owner->group, owner->map, owner->root,
               board.actual_walk_steps,
               cancel_trace.post_cancel_result,
               cancel.watched_script_pointer_hits,
               pre_board_one_island, pre_board_cinnabar,
               board.owner_hits, EL_FERRY_SPECIAL, board.special_hits,
               board.first_nonfield_callback, board.first_task_function,
               owner->stem, owner->stem);
        el_close_exact_srm(core, save_path);
    }
    printf("],\"owner_count\":7,\"cancel_count\":7,"
           "\"boarding_count\":7,\"arrival_count\":7,"
           "\"normal_save_count\":7,\"fresh_continue_count\":7,"
           "\"framebuffer_artifact_fnv1a64\":{");
    for (unsigned index = 0U;
         index < sizeof(el_ferry_owners) / sizeof(el_ferry_owners[0]);
         ++index) {
        printf("%s\"%s.ppm\":\"%016" PRIX64 "\"",
               index == 0U ? "" : ",", el_ferry_owners[index].stem,
               ppm_hashes[index]);
    }
    printf("},\"framebuffer_artifact_roles\":{");
    for (unsigned index = 0U;
         index < sizeof(el_ferry_owners) / sizeof(el_ferry_owners[0]);
         ++index) {
        printf("%s\"%s.ppm\":\"arrival_after_boarding\"",
               index == 0U ? "" : ",", el_ferry_owners[index].stem);
    }
    printf("},\"failed\":0,\"untested\":0,\"warnings\":0}\n");
}

static bool el_unused_party_slots_are_zero(struct mCore *core)
{
    for (unsigned slot = 1U; slot < BOOTSTRAP_TEAM_SIZE; ++slot) {
        uint32_t mon = BOOTSTRAP_PLAYER_PARTY
            + slot * BOOTSTRAP_MON_SIZE;
        for (unsigned byte = 0U; byte < BOOTSTRAP_MON_SIZE; ++byte)
            if (read8(core, mon + byte) != 0U)
                return false;
    }
    return true;
}

static bool el_capture_preparation_is_established_fixture(
    struct mCore *core)
{
    return read8(core, BOOTSTRAP_PLAYER_COUNT) == 1U
        && s61_call_synced(
            core, BATTLE_CORE_GET_MON_DATA,
            BOOTSTRAP_PLAYER_PARTY, 11U, 0U, 0U) == 150U
        && el_unused_party_slots_are_zero(core)
        && s61_item(core, WORLD_MASTER_BALL) == 1U
        && read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0U
        && read8(core, ADDR_BATTLERS_COUNT) == 0U
        && read8(core, BATTLE_CORE_BATTLE_OUTCOME) == 0U;
}

static struct ElSnorlaxTrace el_run_snorlax_outcome(
    const char *rom_path, const char *directory,
    const struct S61Config *config, bool caught, const char *stem,
    const char *root_environment, uint32_t root_fallback,
    bool exercise_no_choice)
{
    struct Fixture giver = s61_world_fixture(stem, &config->giver);
    struct Fixture snorlax = s61_world_fixture(stem, &config->snorlax);
    char save_path[4096];
    s61_save_path(save_path, sizeof(save_path), directory, stem);
    s61_generate(rom_path, save_path, &giver);
    struct mCore *core = el_open_fresh(rom_path, save_path, &giver);
    char producer_artifact[4096];
    char producer_name[256];
    int producer_name_size = snprintf(
        producer_name, sizeof(producer_name), "%s-producer", stem);
    if (producer_name_size <= 0
        || (size_t)producer_name_size >= sizeof(producer_name))
        s61_die("Snorlax producer artifact name formatting failed");
    struct S61Capture producer = s61_new_capture(
        directory, producer_name,
        producer_artifact, sizeof(producer_artifact));
    uint32_t producer_root = el_u32_env(
        "EL_FLUTE_GIVER_ROOT", 0x087700B1U);
    producer.watched_script_pointer_start = producer_root;
    producer.watched_script_pointer_end = producer_root + 511U;
    struct ElSnorlaxTrace trace = {
        .outcome_name = caught ? "CAUGHT" : "RAN",
    };
    s61_acquire_flute(core, config, &producer, &trace.actual_walk_steps);
    trace.producer_messages = producer.count;
    trace.producer_owner_hits = producer.watched_script_pointer_hits;
    if (trace.producer_owner_hits == 0U)
        s61_die("natural flute producer owner PC was not observed");
    if (caught) {
        s61_prepare_master_ball_fixture(core);
    }
    s61_stock_warp_save(core, &snorlax);
    el_close_exact_srm(core, save_path);
    core = el_open_fresh(rom_path, save_path, &snorlax);
    trace.party_count_before = read8(core, BOOTSTRAP_PLAYER_COUNT);
    if (caught) {
        trace.preparation_state_valid =
            el_capture_preparation_is_established_fixture(core);
        if (!trace.preparation_state_valid)
            s61_die("Snorlax capture preparation differs from established fixture");
        s61_prepare_ball_pocket_cursor(core);
    }
    if (!s61_object_visible(core, &config->snorlax))
        s61_die("Route16 Snorlax is hidden before natural consumer");
    trace.actual_walk_steps += s61_walk_approach(core, &config->snorlax);

    uint32_t root = el_u32_env(root_environment, root_fallback);
    if (exercise_no_choice) {
        char no_artifact[4096];
        char no_name[256];
        int no_name_size = snprintf(
            no_name, sizeof(no_name), "%s-choice-no", stem);
        if (no_name_size <= 0 || (size_t)no_name_size >= sizeof(no_name))
            s61_die("Snorlax No artifact name formatting failed");
        struct S61Capture no = s61_new_capture(
            directory, no_name, no_artifact,
            sizeof(no_artifact));
        no.watched_script_pointer_start = root;
        no.watched_script_pointer_end = root + 511U;
        if (!s61_drive_interaction(core, config->snorlax.action_key,
                                   S61_CHOICE_NO, &no, false)
            || !s61_object_visible(core, &config->snorlax)
            || s61_flag(core, config->snorlax_hidden_flag) != 0U
            || no.watched_script_pointer_hits == 0U)
            s61_die("Route16 Snorlax No branch did not preserve object");
        trace.choice_no_result = read16(core, WORLD_SPECIAL_RESULT);
        trace.owner_hits += no.watched_script_pointer_hits;
    }

    char battle_artifact[4096];
    struct S61Capture battle_capture = s61_new_capture(
        directory, stem, battle_artifact, sizeof(battle_artifact));
    battle_capture.watched_script_pointer_start = root;
    battle_capture.watched_script_pointer_end = root + 511U;
    if (!s61_drive_interaction(core, config->snorlax.action_key,
                               S61_CHOICE_YES, &battle_capture, true)
        || !s61_battle_active(core)
        || battle_capture.watched_script_pointer_hits == 0U)
        s61_die("Route16 Snorlax Yes branch did not start battle");
    trace.owner_hits += battle_capture.watched_script_pointer_hits;
    struct FixtureResult battle = {0};
    world_record_wild(core, &snorlax, &battle);
    trace.species = battle.first_wild_species;
    if (trace.species != config->snorlax_species)
        s61_die("Route16 Snorlax canonical species differs");
    trace.battle_runtime_initialized =
        read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U
        && read8(core, ADDR_BATTLERS_COUNT) == 2U;
    if (!trace.battle_runtime_initialized)
        s61_die("Snorlax natural battle runtime did not initialize");
    if (caught) {
        trace.battle_callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
        struct S61BallThrowResult throw_result;
        if (strcmp(s61_case_name, "snorlax-caught-diagnostic") == 0) {
            struct ElHeapWatch heap_watch = el_heap_watch_begin(core);
            throw_result = el_throw_master_ball_with_heap_watch(
                core, &snorlax, &heap_watch);
        } else {
            throw_result = s61_throw_master_ball_with_keys(core, &snorlax);
        }
        trace.outcome = throw_result.outcome;
        trace.caught_with_real_bag_keys = throw_result.choose_action_seen
            && throw_result.bag_opened
            && throw_result.actual_direction_input
            && throw_result.actual_a_input;
        trace.battle_input_pulses = throw_result.input_pulses;
    } else {
        struct ElRunTrace run = el_run_from_wild_with_keys(core);
        world_wait_player_ready(core, &snorlax);
        trace.outcome = run.outcome;
        trace.actual_run_direction_a = run.actual_direction_input
            && run.actual_a_input && run.field_terminal;
        trace.battle_input_pulses = run.input_pulses;
        trace.battle_callback = run.first_battle_callback;
    }
    trace.party_count_after = read8(core, BOOTSTRAP_PLAYER_COUNT);
    trace.battle_runtime_cleaned =
        read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0U;
    trace.field_returned = s61_field_terminal(core);
    if (caught) {
        trace.captured_species = (uint16_t)s61_call_synced(
            core, BATTLE_CORE_GET_MON_DATA,
            BOOTSTRAP_PLAYER_PARTY + BOOTSTRAP_MON_SIZE,
            11U, 0U, 0U);
        trace.master_ball_consumed =
            s61_item(core, WORLD_MASTER_BALL) == 0U;
    }
    if (trace.outcome != (caught ? WORLD_BATTLE_OUTCOME_CAUGHT
                                 : WORLD_BATTLE_OUTCOME_RAN)
        || (caught && !trace.caught_with_real_bag_keys)
        || (!caught && !trace.actual_run_direction_a)
        || trace.battle_callback == 0U
        || trace.battle_callback == BOOTSTRAP_CB2_OVERWORLD
        || !trace.battle_runtime_cleaned || !trace.field_returned
        || trace.party_count_after
            != (caught ? 2U : trace.party_count_before)
        || (caught && (trace.captured_species != config->snorlax_species
                       || !trace.master_ball_consumed))
        || s61_flag(core, config->snorlax_hidden_flag) == 0U
        || s61_object_visible(core, &config->snorlax)) {
        fprintf(stderr,
                "Route16 terminal debug branch=%s outcome=%u expected=%u "
                "bag_keys=%u hidden_flag=0x%04X hidden=%u visible=%u "
                "callback=%08" PRIX32 " lock=%u message=%u\n",
                caught ? "caught" : "ran", trace.outcome,
                caught ? WORLD_BATTLE_OUTCOME_CAUGHT
                       : WORLD_BATTLE_OUTCOME_RAN,
                trace.caught_with_real_bag_keys ? 1U : 0U,
                config->snorlax_hidden_flag,
                s61_flag(core, config->snorlax_hidden_flag),
                s61_object_visible(core, &config->snorlax) ? 1U : 0U,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                world_script_enabled(core),
                read8(core, S61_FIELD_MESSAGE_STATE));
        s61_die("Route16 Snorlax terminal/hidden state differs");
    }
    trace.ppm_rgb_fnv1a64 = el_write_ppm(directory, stem);
    if (!s61_normal_input_save(core))
        s61_die("Route16 Snorlax normal START/SAVE failed");
    el_close_exact_srm(core, save_path);

    core = el_open_fresh(rom_path, save_path, &snorlax);
    if (s61_flag(core, config->flute_flag) == 0U
        || s61_flag(core, config->snorlax_hidden_flag) == 0U
        || s61_object_visible(core, &config->snorlax)
        || !s61_field_terminal(core))
        s61_die("Route16 Snorlax fresh Continue/reentry differs");
    struct S61FieldRoundtripResult roundtrip = s61_field_roundtrip(
        core, stem, config->snorlax.group, config->snorlax.map);
    if (!s61_field_roundtrip_exact(&roundtrip))
        s61_die("Route16 Snorlax fresh field input differs");
    el_close_exact_srm(core, save_path);
    return trace;
}

static void el_case_snorlax(const char *rom_path, const char *directory,
                            const struct S61Config *config)
{
    struct ElSnorlaxTrace ran = el_run_snorlax_outcome(
        rom_path, directory, config, false, "route16-snorlax-ran",
        "EL_ROUTE16_SNORLAX_ROOT", 0x094283A0U, true);
    struct ElSnorlaxTrace caught = el_run_snorlax_outcome(
        rom_path, directory, config, true, "route16-snorlax-caught",
        "EL_ROUTE16_SNORLAX_ROOT", 0x094283A0U, false);
    struct S61Config route12 = *config;
    route12.snorlax = (struct S61Interaction){
        96U, 23U, 11U, 70U, WORLD_KEY_RIGHT, 1U, 15U,
    };
    route12.snorlax_hidden_flag = 0x149EU;
    struct ElSnorlaxTrace route12_caught = el_run_snorlax_outcome(
        rom_path, directory, &route12, true, "route12-snorlax-caught",
        "EL_ROUTE12_SNORLAX_ROOT", 0x09428344U, false);
    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"case\":\"route16_snorlax_lifecycle\","
           "\"owner_id\":\"OBJECT:096/027:005\","
           "\"owner_root\":\"0x%08" PRIX32 "\","
           "\"producer_owner_id\":\"OBJECT:001/045:008\","
           "\"producer_owner_root\":\"0x%08" PRIX32 "\","
           "\"producer_owner_pc_hits\":%u,"
           "\"producer_message_count\":%u,"
           "\"preparation_teleport_and_declared_capture_fixture\":true,"
           "\"direct_owner_or_script_calls\":0,"
           "\"natural_flute_producer\":true,"
           "\"actual_walk_steps\":%u,\"direction_plus_a\":true,"
           "\"choice_no_preserved\":true,\"choice_no_result\":%u,"
           "\"choice_yes_battle\":true,\"species\":%u,"
           "\"owner_pc_hits\":%u,"
           "\"capture_preparation\":{"
           "\"matches_established_last_ball_fixture\":true,"
           "\"master_ball_added_via_rom_call\":true,"
           "\"host_writes_limited_to_inventory_party_menu_preparation\":true,"
           "\"party_slots_1_through_5_zeroed_by_host\":true,"
           "\"party_count_set_to_one_by_host\":true,"
           "\"bag_ball_pocket_cursor_prepared_by_host\":true,"
           "\"direct_memory_writes_outside_declared_fixture\":0,"
           "\"battle_struct_host_writes\":0,"
           "\"battle_result_host_writes\":0,"
           "\"battle_action_cursor_host_writes\":0,"
           "\"fresh_continue_before_battle\":true,"
           "\"unused_party_slots_zero\":true},"
           "\"outcomes\":["
           "{\"name\":\"%s\",\"value\":%u,"
           "\"battle_result_via_keys\":true,"
           "\"species\":%u,\"party_count_before\":%u,"
           "\"party_count_after\":%u,"
           "\"battle_runtime_initialized\":true,"
           "\"battle_runtime_cleaned\":true,\"field_returned\":true,"
           "\"first_battle_callback\":\"0x%08" PRIX32 "\","
           "\"battle_input_pulses\":%u,\"owner_pc_hits\":%u,"
           "\"producer_owner_pc_hits\":%u},"
           "{\"name\":\"%s\",\"value\":%u,"
           "\"battle_result_via_keys\":true,"
           "\"bag_direction_a\":true,\"species\":%u,"
           "\"party_count_before\":%u,\"party_count_after\":%u,"
           "\"captured_species\":%u,"
           "\"capture_preparation_valid\":true,"
           "\"battle_runtime_initialized\":true,"
           "\"battle_runtime_cleaned\":true,\"field_returned\":true,"
           "\"master_ball_consumed\":true,"
           "\"first_battle_callback\":\"0x%08" PRIX32 "\","
           "\"battle_input_pulses\":%u,\"owner_pc_hits\":%u,"
           "\"producer_owner_pc_hits\":%u}],"
           "\"route12_capture_control\":{"
           "\"owner_id\":\"OBJECT:096/023:014\","
           "\"owner_root\":\"0x%08" PRIX32 "\","
           "\"map\":\"96/23\",\"physical_start\":[11,70],"
           "\"approach_key\":\"RIGHT\",\"approach_steps\":1,"
           "\"owner_position\":[13,70],\"species\":%u,"
           "\"outcome_name\":\"%s\",\"outcome_value\":%u,"
           "\"natural_flute_producer\":true,"
           "\"producer_owner_pc_hits\":%u,\"owner_pc_hits\":%u,"
           "\"actual_walk_steps\":%u,\"direction_plus_a\":true,"
           "\"choice_yes_battle\":true,\"bag_direction_a\":true,"
           "\"party_count_before\":%u,\"party_count_after\":%u,"
           "\"captured_species\":%u,"
           "\"capture_preparation_valid\":true,"
           "\"battle_runtime_initialized\":true,"
           "\"battle_runtime_cleaned\":true,\"field_returned\":true,"
           "\"master_ball_consumed\":true,"
           "\"first_battle_callback\":\"0x%08" PRIX32 "\","
           "\"battle_input_pulses\":%u,"
           "\"save_via_start_menu\":true,\"fresh_core_continue\":true,"
           "\"reentry_hidden\":true,\"field_input_recovered\":true,"
           "\"srm\":\"route12-snorlax-caught.srm\","
           "\"ppm\":\"route12-snorlax-caught.ppm\"},"
           "\"hidden_after_each_terminal\":true,"
           "\"normal_save_count\":3,\"fresh_continue_count\":3,"
           "\"reentry_hidden_count\":3,\"field_input_recovered\":true,"
           "\"srms\":[\"route16-snorlax-ran.srm\","
           "\"route16-snorlax-caught.srm\","
           "\"route12-snorlax-caught.srm\"],"
           "\"ppms\":[\"route16-snorlax-ran.ppm\","
           "\"route16-snorlax-caught.ppm\","
           "\"route12-snorlax-caught.ppm\"],"
           "\"framebuffer_artifact_fnv1a64\":{"
           "\"route16-snorlax-ran.ppm\":\"%016" PRIX64 "\","
           "\"route16-snorlax-caught.ppm\":\"%016" PRIX64 "\","
           "\"route12-snorlax-caught.ppm\":\"%016" PRIX64 "\"},"
           "\"framebuffer_artifact_roles\":{"
           "\"route16-snorlax-ran.ppm\":\"route16_ran_field\","
           "\"route16-snorlax-caught.ppm\":\"route16_caught_field\","
           "\"route12-snorlax-caught.ppm\":\"route12_caught_field\"},"
           "\"failed\":0,\"untested\":0,\"warnings\":0}\n",
           el_u32_env("EL_ROUTE16_SNORLAX_ROOT", 0x094283A0U),
           el_u32_env("EL_FLUTE_GIVER_ROOT", 0x087700B1U),
           ran.producer_owner_hits + caught.producer_owner_hits
               + route12_caught.producer_owner_hits,
           ran.producer_messages + caught.producer_messages
               + route12_caught.producer_messages,
           ran.actual_walk_steps + caught.actual_walk_steps
               + route12_caught.actual_walk_steps,
           ran.choice_no_result, ran.species,
           ran.owner_hits + caught.owner_hits,
           ran.outcome_name, ran.outcome, ran.species,
           ran.party_count_before, ran.party_count_after,
           ran.battle_callback, ran.battle_input_pulses,
           ran.owner_hits, ran.producer_owner_hits,
           caught.outcome_name, caught.outcome, caught.species,
           caught.party_count_before, caught.party_count_after,
           caught.captured_species, caught.battle_callback,
           caught.battle_input_pulses, caught.owner_hits,
           caught.producer_owner_hits,
           el_u32_env("EL_ROUTE12_SNORLAX_ROOT", 0x09428344U),
           route12_caught.species, route12_caught.outcome_name,
           route12_caught.outcome, route12_caught.producer_owner_hits,
           route12_caught.owner_hits, route12_caught.actual_walk_steps,
           route12_caught.party_count_before,
           route12_caught.party_count_after,
           route12_caught.captured_species,
           route12_caught.battle_callback,
           route12_caught.battle_input_pulses,
           ran.ppm_rgb_fnv1a64, caught.ppm_rgb_fnv1a64,
           route12_caught.ppm_rgb_fnv1a64);
}

static void el_case_fly(const char *rom_path, const char *directory,
                        const struct S61Config *config)
{
    /* Keep the embedded audited key sequence intact, while binding each
     * retained PPM to the exact RGB bytes present when it was written. */
    char save_path[4096];
    char artifact[4096];
    struct S61Interaction source = {
        config->fly_origin_group, config->fly_origin_map,
        config->fly_origin_x, config->fly_origin_y, WORLD_KEY_DOWN, 0U, 0U,
    };
    struct Fixture fixture = s61_world_fixture("fly_normal_menu", &source);
    s61_save_path(save_path, sizeof(save_path), directory, fixture.name);
    s61_generate(rom_path, save_path, &fixture);
    struct mCore *core = el_open_fresh(rom_path, save_path, &fixture);

    for (unsigned badge = 0U; badge < S61_FLAG_BADGE_COUNT; ++badge)
        (void)s61_call_synced(core, WORLD_FLAG_SET,
                             S61_FLAG_BADGE_1 + badge, 0U, 0U, 0U);
    if (!world_overworld(core))
        s61_die("Fly badge preparation left the input-ready field");
    (void)s61_call_synced(core, WORLD_FLAG_SET,
                         S61_FLAG_POKEMON_GET, 0U, 0U, 0U);
    if (!world_overworld(core))
        s61_die("Fly Pokemon-get preparation left the input-ready field");
    (void)s61_call_synced(core, WORLD_FLAG_SET,
                         config->fly_visited_flag, 0U, 0U, 0U);
    if (s61_flag(core, config->fly_visited_flag) != 1U)
        s61_die("Fly destination visited-flag preparation failed");
    if (s61_call_synced(core, BATTLE_CORE_ADD_BAG_ITEM,
                       S61_FLY_HM_ITEM, 1U, 0U, 0U) == 0U)
        s61_die("Fly HM ownership preparation failed");
    if (!world_overworld(core))
        s61_die("Fly HM preparation left the input-ready field");
    s61_set_mon_data_u32(core, BOOTSTRAP_PLAYER_PARTY,
                         MON_DATA_MOVE1, S61_FLY_MOVE);
    world_wait_player_ready(core, &fixture);
    if (!world_overworld(core)) {
        fprintf(stderr, "Fly preparation debug main=%08" PRIX32
                " pc=%08" PRIX32 " cpsr=%08" PRIX32 "\n",
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                (uint32_t)read_register(core, "pc"),
                (uint32_t)read_register(core, "cpsr"));
        s61_die("Fly host preparation left the input-ready field");
    }

    struct S61Capture capture = s61_new_capture(
        directory, fixture.name, artifact, sizeof(artifact));
    capture.suppress_semantic_content = true;
    uint64_t field_hash = bootstrap_framebuffer_hash(s61_video);
    uint64_t origin_rgb_hash = el_framebuffer_rgb_fnv1a64(s61_video);
    if (!s61_enter_party_menu(core, &capture)) {
        fprintf(stderr,
                "Fly party debug start_callback=%08" PRIX32
                " count=%u cursor=%u party_slot=%u overworld=%u "
                "main=%08" PRIX32 " lock=%u message=%u\n",
                read32(core, S61_START_MENU_CALLBACK),
                read8(core, S61_START_MENU_COUNT),
                read8(core, S61_START_MENU_CURSOR),
                read8(core, S61_PARTY_MENU + S61_PARTY_MENU_SLOT),
                world_overworld(core),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                world_script_enabled(core),
                read8(core, S61_FIELD_MESSAGE_STATE));
        s61_die("normal Start-menu path did not enter the party screen");
    }
    s61_pulse(core, WORLD_KEY_A, 2U, 120U, &capture);
    for (unsigned step = 0U; step < config->fly_context_down; ++step)
        s61_pulse(core, WORLD_KEY_DOWN, 2U, 45U, &capture);
    s61_pulse(core, WORLD_KEY_A, 2U, 900U, &capture);
    uint64_t town_map_hash = bootstrap_framebuffer_hash(s61_video);
    if (town_map_hash == field_hash || world_overworld(core))
        s61_die("normal party field-move path did not open a visible Fly map");
    uint64_t town_map_rgb_hash = el_write_ppm(
        directory, "fly_normal_menu-town-map");
    struct S61KeyStep steps[S61_MAX_SEQUENCE_STEPS];
    unsigned step_count = s61_parse_sequence(steps, S61_MAX_SEQUENCE_STEPS);
    for (unsigned index = 0U; index < step_count; ++index)
        s61_pulse(core, steps[index].key, steps[index].pressed,
                  steps[index].released, &capture);
    uint64_t landing_rgb_hash = el_write_ppm(
        directory, "fly_normal_menu-final");
    uint32_t save1 = world_save1(core, fixture.name);
    uint8_t final_group = read8(core, save1 + 4U);
    uint8_t final_map = read8(core, save1 + 5U);
    uint16_t final_x = read16(core, save1);
    uint16_t final_y = read16(core, save1 + 2U);
    bool expected_destination = config->fly_destination_group == 0xFFU
        || (final_group == config->fly_destination_group
            && final_map == config->fly_destination_map
            && final_x == config->fly_destination_x
            && final_y == config->fly_destination_y);
    bool warped = final_group != fixture.group || final_map != fixture.map;
    bool landing_overworld = world_overworld(core);
    bool landing_script_released = !world_script_enabled(core);
    bool landing_controls_unlocked =
        read8(core, WORLD_FIELD_CONTROLS_LOCKED) == 0U;
    bool landing_field_ready = s61_field_terminal(core)
        && landing_overworld && landing_script_released
        && landing_controls_unlocked;
    if (!expected_destination || !warped || !landing_field_ready) {
        fprintf(stderr,
                "Fly debug origin=%u/%u final=%u/%u@%u,%u "
                "expected=%u/%u@%u,%u "
                "overworld=%u callback=%08" PRIX32
                " lock=%u field_ready=%u steps=%u\n",
                fixture.group, fixture.map, final_group, final_map,
                final_x, final_y,
                config->fly_destination_group,
                config->fly_destination_map,
                config->fly_destination_x, config->fly_destination_y,
                world_overworld(core),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                world_script_enabled(core), landing_field_ready ? 1U : 0U,
                step_count);
        s61_die("normal Fly selection did not settle at the expected destination");
    }
    s61_step_capture_pulse(core, WORLD_KEY_START, 2U, 120U, &capture);
    bool start_menu_opened =
        read32(core, S61_START_MENU_CALLBACK) == S61_START_MENU_INPUT;
    bool back_pressed = start_menu_opened;
    if (back_pressed)
        s61_step_capture_pulse(core, WORLD_KEY_B, 2U, 180U, &capture);
    save1 = world_save1(core, fixture.name);
    bool field_input_recovered = back_pressed && s61_field_terminal(core)
        && read8(core, WORLD_FIELD_CONTROLS_LOCKED) == 0U
        && read8(core, save1 + 4U) == final_group
        && read8(core, save1 + 5U) == final_map
        && read16(core, save1) == final_x
        && read16(core, save1 + 2U) == final_y;
    if (!start_menu_opened || !field_input_recovered)
        s61_die("Fly landing START/B field-input recovery differs");
    printf("{\"schema_version\":3,\"status\":\"PASS\","
           "\"case\":\"fly_normal_menu\","
           "\"preparation_only_host_writes\":true,"
           "\"direct_owner_or_script_calls\":0,"
           "\"start_party_town_map_via_keys\":true,"
           "\"town_map_visible\":true,\"context_down_steps\":%u,"
           "\"sequence_steps\":%u,"
           "\"origin\":\"%u/%u\",\"destination\":\"%u/%u\","
           "\"landing\":[%u,%u],"
           "\"landing_overworld\":true,"
           "\"landing_script_released\":true,"
           "\"landing_controls_unlocked\":true,"
           "\"start_pressed\":true,\"start_menu_opened\":true,"
           "\"back_pressed\":true,\"field_input_recovered\":true,"
           "\"field_framebuffer_fnv1a64\":\"%016" PRIX64 "\","
           "\"town_map_framebuffer_fnv1a64\":\"%016" PRIX64 "\","
           "\"framebuffer_artifact_fnv1a64\":{"
           "\"fly_normal_menu-town-map.ppm\":\"%016" PRIX64 "\","
           "\"fly_normal_menu-final.ppm\":\"%016" PRIX64 "\"},"
           "\"framebuffer_artifact_roles\":{"
           "\"fly_normal_menu-town-map.ppm\":\"town_map\","
           "\"fly_normal_menu-final.ppm\":\"landing\"},"
           "\"framebuffer_stage_rgb_fnv1a64\":{"
           "\"origin\":\"%016" PRIX64 "\","
           "\"town_map\":\"%016" PRIX64 "\","
           "\"landing\":\"%016" PRIX64 "\"},"
           "\"capture\":", config->fly_context_down, step_count,
           fixture.group, fixture.map,
           final_group, final_map, final_x, final_y,
           field_hash, town_map_hash,
           town_map_rgb_hash, landing_rgb_hash,
           origin_rgb_hash, town_map_rgb_hash, landing_rgb_hash);
    s61_print_capture(&capture);
    printf(",\"failed\":0,\"untested\":0,\"warnings\":0}\n");
    bootstrap_close_core(core);
}

int main(int argc, char **argv)
{
    if (argc != 4) {
        fprintf(stderr, "usage: %s ROM WORK_DIRECTORY CASE\n", argv[0]);
        return 2;
    }
    if (mkdir(argv[2], 0700) != 0 && errno != EEXIST) {
        perror("mkdir");
        return 2;
    }
    s61_case_name = argv[3];
    bootstrap_phase = argv[3];
    s61_artifact_directory = argv[2];
    struct mLogger logger = {.log = s61_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct S61Config config = s61_load_config();
    if (strcmp(argv[3], "vermilion") == 0)
        el_case_vermilion(argv[1], argv[2]);
    else if (strcmp(argv[3], "ferry") == 0)
        el_case_ferry(argv[1], argv[2]);
    else if (strcmp(argv[3], "snorlax") == 0)
        el_case_snorlax(argv[1], argv[2], &config);
    else if (strcmp(argv[3], "snorlax-caught-diagnostic") == 0)
        (void)el_run_snorlax_outcome(
            argv[1], argv[2], &config, true,
            "route16-snorlax-caught-diagnostic",
            "EL_ROUTE16_SNORLAX_ROOT", 0x094283A0U, false);
    else if (strcmp(argv[3], "fly") == 0)
        el_case_fly(argv[1], argv[2], &config);
    else
        s61_die("unknown event lifecycle case");
    return 0;
}
