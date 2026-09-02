/*
 * Stage61 normal Save UI -> real flash fault -> SaveFailed retry -> hard
 * Continue E2E.  The large Stage61 harness is embedded deliberately: this
 * keeps the exact title/field/menu/save helpers and the already-audited mGBA
 * flash-return fault model in one translation unit without widening its API.
 */
#ifndef S61_SAVE_UI_EMBEDDED_HARNESS
#error "compile through scripts/run_stage61_save_ui_cow_e2e.py"
#endif
#include S61_SAVE_UI_EMBEDDED_HARNESS

enum {
    SUI_SAVE_FAILED_STATE = 0x0203AAC8U,
    SUI_SAVE_FAILED_ACTIVE = 0x03005480U,
    SUI_SAVE_ATTEMPT_STATUS = 0x03005470U,
    SUI_SAVE_ATTEMPT_OK = 1U,
    SUI_SAVE_FAILED_WIPE_STATE = 5U,
    SUI_SAVE_FAILED_RESULT_STATE = 6U,
    SUI_STOCK_ERASE_FLASH_SECTOR = 0x081C2E90U,
    SUI_STOCK_PROGRAM_FAILURE_CONSUMER = 0x081C2C72U,
    SUI_STOCK_TRY_WRITE_SECTOR = 0x080DA9C0U,
    SUI_STOCK_PROGRAM_FLASH_SECTOR = 0x081C302CU,
    SUI_SAVE_SERIALIZED_GAME = 0x0804BAB8U,
    SUI_UPDATE_SAVE_ADDRESSES = 0x080DB1BCU,
    SUI_SAVE_DATA_BUFFER_PTR = 0x030053E4U,
    SUI_SAVE_BYTES = 131072U,
    SUI_SAVE_FAILED_OWNER_START = 0x080F6160U,
    SUI_SAVE_FAILED_OWNER_END = 0x080F6500U,
    SUI_EXPANDED_FLAG_CANARY_ID = 0x18B4U,
    SUI_EXPANDED_FLAG_CANARY_ADDRESS = 0x0203B2DEU,
    SUI_EXPANDED_VAR_CANARY_ID = 0x5170U,
    SUI_EXPANDED_VAR_CANARY_ADDRESS = 0x0203B5C8U,
};

struct SuiPostFaultTrace {
    uint8_t try_write_sectors[64];
    uint8_t erase_sectors[64];
    unsigned try_write_count;
    unsigned erase_count;
    unsigned program_sector_hits;
};

struct SuiInputTrace {
    bool start_menu_opened;
    bool save_action_selected;
    unsigned confirmation_pulses;
    unsigned wrapper_entry_hits;
    uint8_t save_type;
    uint16_t fault_physical_sector;
    uint32_t callback_pc;
    uint32_t callback_return;
    unsigned save_serialized_game_hits;
    unsigned update_save_addresses_hits;
    uint32_t buffer_before_input;
    uint32_t buffer_at_serialize;
    uint32_t buffer_at_update_addresses;
    uint32_t buffer_at_wrapper;
};

struct SuiOwnerStateObservation {
    uint32_t pc;
    uint32_t active;
    uint8_t state;
};

struct SuiLocation {
    uint8_t group;
    uint8_t map;
    uint8_t warp;
    uint16_t x;
    uint16_t y;
};

struct SuiFreshInputLiveness {
    struct S61FieldRoundtripResult roundtrip;
    struct SuiLocation before;
    struct SuiLocation after;
    bool map_preserved;
    bool position_preserved;
    bool field_terminal;
};

static uint64_t sui_hash_bytes(const uint8_t *bytes, size_t size)
{
    uint64_t hash = UINT64_C(1469598103934665603);
    for (size_t index = 0U; index < size; ++index) {
        hash ^= bytes[index];
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

static uint64_t sui_hash_ppm_pixels(const color_t *video)
{
    uint64_t hash = UINT64_C(1469598103934665603);
    for (unsigned index = 0U; index < 240U * 160U; ++index) {
        uint32_t pixel = (uint32_t)video[index];
        for (unsigned byte = 0U; byte < 3U; ++byte) {
            hash ^= (uint8_t)(pixel >> (byte * 8U));
            hash *= UINT64_C(1099511628211);
        }
    }
    return hash;
}

static unsigned sui_count_differences(const uint8_t *left,
                                      const uint8_t *right, size_t size)
{
    unsigned differences = 0U;
    for (size_t index = 0U; index < size; ++index)
        if (left[index] != right[index])
            ++differences;
    return differences;
}

static void sui_assert_pinned_save_failed_contract(
    struct mCore *core, uint32_t handle_saving_data)
{
    /* FireRed-JP/Vega does not use the English decomp's SaveFailed globals.
     * Pin the current Stage61 literals and state-5 TryWipe call before using
     * the addresses as observations. */
    if (read16(core, 0x080F6180U) != 0xAAC8U
        || read16(core, 0x080F6182U) != 0x0203U
        || read16(core, 0x080F6164U) != 0x5480U
        || read16(core, 0x080F6166U) != 0x0300U
        || read16(core, 0x080F62A8U) != 0x5470U
        || read16(core, 0x080F62AAU) != 0x0300U
        || read16(core, 0x080F64E0U) != 0x53DCU
        || read16(core, 0x080F64E2U) != 0x0300U
        || read16(core, 0x080F6290U) != 0xF000U
        || read16(core, 0x080F6292U) != 0xF90AU
        || handle_saving_data < 0x09000000U
        || handle_saving_data >= 0x0A000000U
        || read16(core, handle_saving_data & ~1U) == 0x0000U
        || read16(core, handle_saving_data & ~1U) == 0xFFFFU
        || (read32(core, WORLD_ERASE_FLASH_SECTOR_PTR) & ~1U)
            != SUI_STOCK_ERASE_FLASH_SECTOR)
        s61_die("save UI COW SaveFailed owner preimage differs");
    if (read32(core, SUI_SAVE_FAILED_ACTIVE) != 0U
        || read8(core, SUI_SAVE_FAILED_STATE) != 0U)
        s61_die("save UI COW SaveFailed state dirty before input");
}

static bool sui_step_frames_to_fault_callback(
    struct mCore *core, uint16_t keys, unsigned frames,
    uint32_t handle_saving_data, struct SuiInputTrace *trace)
{
    uint32_t first_frame = core->frameCounter(core);
    bool stepped = false;
    core->setKeys(core, keys);
    while ((uint32_t)(core->frameCounter(core) - first_frame) < frames) {
        uint32_t raw_pc = (uint32_t)read_register(core, "pc");
        uint32_t current_pc = stepped
            ? s61_running_thumb_current_pc(raw_pc) : UINT32_MAX;
        if (current_pc == (handle_saving_data & ~1U)) {
            ++trace->wrapper_entry_hits;
            trace->save_type = (uint8_t)read_register(core, "r0");
            trace->buffer_at_wrapper = read32(
                core, SUI_SAVE_DATA_BUFFER_PTR);
        }
        if (current_pc == SUI_SAVE_SERIALIZED_GAME) {
            ++trace->save_serialized_game_hits;
            trace->buffer_at_serialize = read32(
                core, SUI_SAVE_DATA_BUFFER_PTR);
        }
        if (current_pc == SUI_UPDATE_SAVE_ADDRESSES) {
            ++trace->update_save_addresses_hits;
            trace->buffer_at_update_addresses = read32(
                core, SUI_SAVE_DATA_BUFFER_PTR);
        }
        if (current_pc == SUI_STOCK_ERASE_FLASH_SECTOR) {
            trace->fault_physical_sector =
                (uint16_t)read_register(core, "r0");
            trace->callback_pc = SUI_STOCK_ERASE_FLASH_SECTOR;
            trace->callback_return =
                (uint32_t)read_register(core, "lr") & ~1U;
            core->setKeys(core, 0U);
            return true;
        }
        if (!s61_cpu_pc_is_executable(raw_pc))
            s61_die("save UI COW input entered non-executable memory");
        core->step(core);
        stepped = true;
    }
    return false;
}

static bool sui_pulse_to_fault_callback(
    struct mCore *core, uint16_t key, unsigned released,
    uint32_t handle_saving_data, struct SuiInputTrace *trace)
{
    if (sui_step_frames_to_fault_callback(
            core, key, 2U, handle_saving_data, trace))
        return true;
    return sui_step_frames_to_fault_callback(
        core, 0U, released, handle_saving_data, trace);
}

static struct SuiInputTrace sui_enter_save_with_keys_until_flash_fault(
    struct mCore *core, uint32_t handle_saving_data)
{
    struct SuiInputTrace trace = {0};
    if (!world_overworld(core) || world_script_enabled(core))
        s61_die("save UI COW did not begin in field input");
    trace.buffer_before_input = read32(core, SUI_SAVE_DATA_BUFFER_PTR);
    s61_pulse(core, WORLD_KEY_START, 2U, 120U, NULL);
    if (read32(core, WORLD_START_MENU_CALLBACK) != WORLD_START_MENU_INPUT)
        s61_die("save UI COW START did not open the real menu");
    trace.start_menu_opened = true;

    uint8_t count = read8(core, WORLD_START_MENU_COUNT);
    uint8_t cursor = read8(core, WORLD_START_MENU_CURSOR);
    if (count == 0U || count > 9U || cursor >= count)
        s61_die("save UI COW start-menu shape differs");
    uint8_t target = count;
    for (uint8_t index = 0U; index < count; ++index) {
        if (read8(core, WORLD_START_MENU_ORDER + index)
                == WORLD_START_MENU_SAVE_ACTION) {
            target = index;
            break;
        }
    }
    if (target >= count)
        s61_die("save UI COW SAVE action is absent");
    unsigned down = (unsigned)(target + count - cursor) % count;
    unsigned up = (unsigned)(cursor + count - target) % count;
    uint16_t direction = down <= up ? WORLD_KEY_DOWN : WORLD_KEY_UP;
    unsigned steps = down <= up ? down : up;
    for (unsigned step = 0U; step < steps; ++step)
        s61_pulse(core, direction, 2U, 30U, NULL);
    if (read8(core, WORLD_START_MENU_CURSOR) != target)
        s61_die("save UI COW SAVE cursor did not settle");

    /* The first A selects SAVE.  Subsequent A pulses answer the stock JP
     * same-file prompts.  Every instruction is stepped while the key state is
     * live, so the first real flash erase callback cannot pass
     * unnoticed inside runFrame(). */
    for (unsigned pulse = 0U; pulse < 32U; ++pulse) {
        if (sui_pulse_to_fault_callback(
                core, WORLD_KEY_A, 180U, handle_saving_data, &trace)) {
            trace.save_action_selected = true;
            trace.confirmation_pulses = pulse + 1U;
            if (trace.wrapper_entry_hits != 1U || trace.save_type != 0U)
                s61_die("save UI COW fault did not originate in normal SAVE");
            return trace;
        }
        if (pulse == 0U
            && read32(core, WORLD_START_MENU_CALLBACK)
                != WORLD_START_MENU_SAVE_CALLBACK)
            s61_die("save UI COW SAVE selection did not enter callback");
    }
    s61_die("save UI COW real flash erase callback was not reached");
    return trace;
}

static void sui_propagate_flash_failure(struct mCore *core,
                                        uint32_t callback_pc,
                                        uint32_t callback_return)
{
    s61_inject_status_at_callback_return(
        core, callback_pc, callback_return, 1U,
        UINT64_C(50000000),
        "save UI COW erase callback return exceeded bound");

    /* A repaired SAVE_NORMAL wrapper may deliberately establish its backup
     * before entering stock.  In that phase the callback returns directly to
     * Stage61 payload code, which consumes the injected status itself. */
    if (callback_return >= 0x09000000U
        && callback_return < 0x0A000000U)
        return;

    if (read16(core, SUI_STOCK_PROGRAM_FAILURE_CONSUMER) != 0x0400U
        || read16(core, SUI_STOCK_PROGRAM_FAILURE_CONSUMER + 2U) != 0x0C02U
        || read16(core, SUI_STOCK_PROGRAM_FAILURE_CONSUMER + 4U) != 0x2A00U
        || read16(core, SUI_STOCK_PROGRAM_FAILURE_CONSUMER + 6U) != 0xD1F0U)
        s61_die("save UI COW stock program failure consumer differs");
    for (uint64_t instructions = 0U;; ++instructions) {
        if (((uint32_t)read_register(core, "pc") & ~1U)
                == SUI_STOCK_PROGRAM_FAILURE_CONSUMER)
            break;
        if (instructions >= UINT64_C(2000000))
            s61_die("save UI COW aggregate failure return exceeded bound");
        core->step(core);
    }
    /* This is the existing Stage61 fault model: the real erase callback has
     * already performed its flash side effect.  Force its aggregate to return
     * that failure on the third/final stock verify attempt. */
    write_register(core, "r0", 1U);
    write_register(core, "r6", 2U);
}

static void sui_wait_for_real_save_failed_entry(
    struct mCore *core, struct SuiPostFaultTrace *trace)
{
    for (uint64_t instructions = 0U;; ++instructions) {
        if (read32(core, SUI_SAVE_FAILED_ACTIVE) != 0U
            && read32(core, WORLD_DAMAGED_SAVE_SECTORS) != 0U)
            return;
        uint32_t raw_pc = (uint32_t)read_register(core, "pc");
        uint32_t current_pc = instructions == 0U
            ? UINT32_MAX : s61_running_thumb_current_pc(raw_pc);
        if (current_pc == SUI_STOCK_TRY_WRITE_SECTOR
            && trace->try_write_count
                < sizeof(trace->try_write_sectors))
            trace->try_write_sectors[trace->try_write_count++] =
                (uint8_t)read_register(core, "r0");
        if (current_pc == SUI_STOCK_ERASE_FLASH_SECTOR
            && trace->erase_count < sizeof(trace->erase_sectors))
            trace->erase_sectors[trace->erase_count++] =
                (uint8_t)read_register(core, "r0");
        if (current_pc == SUI_STOCK_PROGRAM_FLASH_SECTOR)
            ++trace->program_sector_hits;
        if (!s61_cpu_pc_is_executable(raw_pc))
            s61_die("save UI COW failure path entered non-executable memory");
        if (instructions >= UINT64_C(100000000))
            s61_die("save UI COW did not enter the real SaveFailed owner");
        core->step(core);
    }
}

static void sui_print_failure_trace(
    const struct SuiInputTrace *input,
    const struct SuiPostFaultTrace *post_fault)
{
    fprintf(stderr,
            "SAVE_UI_COW_ENTRY_DIAGNOSTIC wrapper_hits=%u"
            " save_type=%u buffer_before=%08" PRIX32
            " serialized_hits=%u buffer_at_serialize=%08" PRIX32
            " update_addresses_hits=%u buffer_at_update=%08" PRIX32
            " buffer_at_wrapper=%08" PRIX32 "\n",
            input->wrapper_entry_hits, input->save_type,
            input->buffer_before_input,
            input->save_serialized_game_hits,
            input->buffer_at_serialize,
            input->update_save_addresses_hits,
            input->buffer_at_update_addresses,
            input->buffer_at_wrapper);
    fprintf(stderr,
            "SAVE_UI_COW_POST_FAULT_CALLBACKS"
            " try_write_count=%u try_write=[",
            post_fault->try_write_count);
    for (unsigned index = 0U;
         index < post_fault->try_write_count; ++index)
        fprintf(stderr, "%s%u", index == 0U ? "" : ",",
                post_fault->try_write_sectors[index]);
    fprintf(stderr, "] erase_count=%u erase=[",
            post_fault->erase_count);
    for (unsigned index = 0U; index < post_fault->erase_count; ++index)
        fprintf(stderr, "%s%u", index == 0U ? "" : ",",
                post_fault->erase_sectors[index]);
    fprintf(stderr, "] program_sector_hits=%u\n",
            post_fault->program_sector_hits);
}

static void sui_capture_save_failed_owner(
    struct mCore *core, uint8_t state,
    struct SuiOwnerStateObservation *observation)
{
    for (uint64_t instructions = 0U; instructions < UINT64_C(10000000);
         ++instructions) {
        uint8_t observed = read8(core, SUI_SAVE_FAILED_STATE);
        uint32_t active = read32(core, SUI_SAVE_FAILED_ACTIVE);
        uint32_t raw_pc = (uint32_t)read_register(core, "pc");
        uint32_t current_pc = instructions == 0U
            ? raw_pc & ~1U : s61_running_thumb_current_pc(raw_pc);
        if (observed != state || active == 0U)
            s61_die("save UI COW owner state changed before PC capture");
        if (current_pc >= SUI_SAVE_FAILED_OWNER_START
            && current_pc < SUI_SAVE_FAILED_OWNER_END) {
            observation->pc = current_pc;
            observation->active = active;
            observation->state = observed;
            return;
        }
        if (!s61_cpu_pc_is_executable(raw_pc))
            s61_die("save UI COW owner PC capture entered non-executable memory");
        core->step(core);
    }
    s61_die("save UI COW owner PC capture exceeded bound");
}

static void sui_wait_save_failed_state(
    struct mCore *core, uint8_t state, unsigned frame_limit,
    struct SuiOwnerStateObservation *observation)
{
    for (unsigned frame = 0U; frame <= frame_limit; ++frame) {
        uint8_t observed = read8(core, SUI_SAVE_FAILED_STATE);
        if (observed == state) {
            sui_capture_save_failed_owner(core, state, observation);
            return;
        }
        if (observed > state)
            s61_die("save UI COW skipped an observed SaveFailed state");
        if (read32(core, SUI_SAVE_FAILED_ACTIVE) == 0U)
            s61_die("save UI COW SaveFailed owner ended early");
        run_key_frames(core, 0U, 1U);
    }
    s61_die("save UI COW SaveFailed state wait exceeded bound");
}

static void sui_wait_for_field_after_ack(struct mCore *core)
{
    for (unsigned frame = 0U; frame < 1200U; ++frame) {
        if (read32(core, SUI_SAVE_FAILED_ACTIVE) == 0U
            && read8(core, SUI_SAVE_FAILED_STATE) == 0U
            && world_overworld(core) && !world_script_enabled(core))
            return;
        run_key_frames(core, 0U, 1U);
    }
    s61_die("save UI COW did not recover field input after A");
}

static void sui_format_path(char *destination, size_t size,
                            const char *directory, const char *name)
{
    int length = snprintf(destination, size, "%s/%s", directory, name);
    if (length <= 0 || (size_t)length >= size)
        s61_die("save UI COW artifact path is too long");
}

static struct SuiLocation sui_read_location(struct mCore *core,
                                            const char *case_id)
{
    uint32_t save1 = world_save1(core, case_id);
    return (struct SuiLocation){
        .group = read8(core, save1 + 4U),
        .map = read8(core, save1 + 5U),
        .warp = read8(core, save1 + 6U),
        .x = read16(core, save1),
        .y = read16(core, save1 + 2U),
    };
}

static struct SuiFreshInputLiveness sui_prove_fresh_input_liveness(
    struct mCore *core, const struct Fixture *fixture)
{
    struct SuiFreshInputLiveness result = {0};
    result.before = sui_read_location(core, fixture->name);
    result.roundtrip = s61_field_roundtrip(
        core, fixture->name, fixture->group, fixture->map);
    result.after = sui_read_location(core, fixture->name);
    result.map_preserved = result.before.group == result.after.group
        && result.before.map == result.after.map
        && result.before.warp == result.after.warp;
    result.position_preserved = result.before.x == result.after.x
        && result.before.y == result.after.y;
    result.field_terminal = s61_field_terminal(core);
    if (!s61_field_roundtrip_exact(&result.roundtrip)
        || !result.map_preserved || !result.position_preserved
        || !result.field_terminal
        || result.before.group != fixture->group
        || result.before.map != fixture->map
        || result.before.x != fixture->x || result.before.y != fixture->y)
        s61_die("save UI COW hard fresh Continue input liveness differs");
    return result;
}

static void sui_run(const char *rom_path, const char *directory)
{
    static const struct S61Interaction interaction = {
        96U, 5U, 20U, 20U, WORLD_KEY_DOWN, 1U, 0U,
    };
    struct Fixture fixture = s61_world_fixture(
        "save_ui_cow_fault_retry_continue", &interaction);
    char retained_path[4096];
    char before_path[4096];
    char after_path[4096];
    char fault_path[4096];
    char screenshot_path[4096];
    char framebuffer_raw_path[4096];
    sui_format_path(retained_path, sizeof(retained_path), directory,
                    "save-ui-cow-retained.srm");
    sui_format_path(before_path, sizeof(before_path), directory,
                    "save-ui-cow-before.srm");
    sui_format_path(after_path, sizeof(after_path), directory,
                    "save-ui-cow-after.srm");
    sui_format_path(fault_path, sizeof(fault_path), directory,
                    "save-ui-cow-fault.srm");
    sui_format_path(screenshot_path, sizeof(screenshot_path), directory,
                    "save-ui-cow-save-failed");
    sui_format_path(framebuffer_raw_path, sizeof(framebuffer_raw_path),
                    directory, "save-ui-cow-save-failed.rgba");

    s61_generate(rom_path, retained_path, &fixture);
    s61_allow_savedata_time_offset_notice = true;
    struct mCore *core = s61_open_fresh(rom_path, retained_path, &fixture);
    s61_allow_savedata_time_offset_notice = false;
    uint32_t handle_saving_data = s61_runtime_symbol_env(
        "S61_HANDLE_SAVING_DATA_SYMBOL");
    sui_assert_pinned_save_failed_contract(core, handle_saving_data);
    s61_apply_link_save_canaries(core);

    uint8_t *before = s61_cow_clone_savedata(core);
    s61_write_exact_binary(before_path, before, SUI_SAVE_BYTES);
    uint32_t initial_counter = read32(core, WORLD_SAVE_COUNTER);
    unsigned protected_slot = (unsigned)(initial_counter & 1U);
    unsigned target_slot = 1U - protected_slot;
    uint32_t selected_counter = 0U;
    if (!s61_cow_raw_complete_counter(
            before, protected_slot, &selected_counter)
        || selected_counter != initial_counter)
        s61_die("save UI COW initial selected generation is incomplete");
    uint32_t backup_counter = 0U;
    if (!s61_cow_raw_complete_counter(
            before, target_slot, &backup_counter)
        || backup_counter != initial_counter - 1U)
        s61_die("save UI COW initial backup generation is incomplete");

    struct SuiInputTrace input =
        sui_enter_save_with_keys_until_flash_fault(
            core, handle_saving_data);
    if (!input.start_menu_opened || !input.save_action_selected
        || input.callback_return == 0U)
        s61_die("save UI COW natural input trace is incomplete");
    if (input.save_serialized_game_hits != 1U
        || input.update_save_addresses_hits != 1U
        || input.buffer_before_input < 0x02000000U
        || input.buffer_before_input >= 0x02040000U
        || input.buffer_at_serialize != input.buffer_before_input
        || input.buffer_at_update_addresses != input.buffer_before_input
        || input.buffer_at_wrapper != input.buffer_before_input)
        s61_die("save UI COW serialization/buffer owner trace differs");
    sui_propagate_flash_failure(
        core, input.callback_pc, input.callback_return);
    struct SuiPostFaultTrace post_fault = {0};
    sui_wait_for_real_save_failed_entry(core, &post_fault);

    uint32_t damaged_before_wipe = read32(
        core, WORLD_DAMAGED_SAVE_SECTORS);
    uint8_t *fault_flash = s61_cow_clone_savedata(core);
    s61_write_exact_binary(fault_path, fault_flash, SUI_SAVE_BYTES);
    size_t protected_offset = protected_slot
        * WORLD_SAVE_SLOT_SECTORS * WORLD_SECTOR_SIZE;
    size_t protected_size = WORLD_SAVE_SLOT_SECTORS * WORLD_SECTOR_SIZE;
    bool protected_exact = memcmp(
        before + protected_offset, fault_flash + protected_offset,
        protected_size) == 0;
    unsigned fault_changed_bytes = sui_count_differences(
        before, fault_flash, SUI_SAVE_BYTES);
    uint64_t fault_hash = sui_hash_bytes(fault_flash, SUI_SAVE_BYTES);
    uint32_t ignored_counter = 0U;
    bool target_incomplete = !s61_cow_raw_complete_counter(
        fault_flash, target_slot, &ignored_counter);
    if (damaged_before_wipe == 0U || fault_changed_bytes == 0U
        || !protected_exact || !target_incomplete) {
        sui_print_failure_trace(&input, &post_fault);
        uint32_t slot_counters[2] = {0U, 0U};
        bool slot_complete[2] = {
            s61_cow_raw_complete_counter(
                fault_flash, 0U, &slot_counters[0]),
            s61_cow_raw_complete_counter(
                fault_flash, 1U, &slot_counters[1]),
        };
        fprintf(stderr,
                "SAVE_UI_COW_FAULT_DIAGNOSTIC damaged=%08" PRIX32
                " changed=%u protected_slot=%u target_slot=%u"
                " protected_exact=%u target_incomplete=%u"
                " target_counter=%" PRIu32 " live_counter=%" PRIu32
                " first_sector=%u slot0=%u/%" PRIu32
                " slot1=%u/%" PRIu32 " sectors=[",
                damaged_before_wipe, fault_changed_bytes,
                protected_slot, target_slot, protected_exact,
                target_incomplete, ignored_counter,
                read32(core, WORLD_SAVE_COUNTER),
                read16(core, WORLD_FIRST_SAVE_SECTOR),
                slot_complete[0], slot_counters[0],
                slot_complete[1], slot_counters[1]);
        for (unsigned physical = 0U; physical < 32U; ++physical) {
            unsigned changed = sui_count_differences(
                before + physical * WORLD_SECTOR_SIZE,
                fault_flash + physical * WORLD_SECTOR_SIZE,
                WORLD_SECTOR_SIZE);
            if (changed != 0U)
                fprintf(stderr, "%s%u:%u",
                        physical == 0U ? "" : ",", physical, changed);
        }
        fprintf(stderr, "]\n");
        s61_die("save UI COW fault did not preserve one complete generation");
    }

    struct SuiOwnerStateObservation state5 = {0};
    struct SuiOwnerStateObservation state6 = {0};
    sui_wait_save_failed_state(
        core, SUI_SAVE_FAILED_WIPE_STATE, 1200U, &state5);
    uint64_t failed_framebuffer_hash = bootstrap_framebuffer_hash(s61_video);
    uint64_t failed_ppm_hash = sui_hash_ppm_pixels(s61_video);
    s61_write_exact_binary(
        framebuffer_raw_path, (const uint8_t *)s61_video,
        sizeof(s61_video));
    bootstrap_write_ppm(screenshot_path, s61_video);
    if (read32(core, WORLD_DAMAGED_SAVE_SECTORS)
            != damaged_before_wipe)
        s61_die("save UI COW damaged mask changed before real wipe state");

    sui_wait_save_failed_state(
        core, SUI_SAVE_FAILED_RESULT_STATE, 1200U, &state6);
    uint32_t damaged_after_retry = read32(
        core, WORLD_DAMAGED_SAVE_SECTORS);
    uint16_t attempt_status = read16(core, SUI_SAVE_ATTEMPT_STATUS);
    uint32_t retry_counter = read32(core, WORLD_SAVE_COUNTER);
    uint8_t *retry_flash = s61_cow_clone_savedata(core);
    uint32_t retry_raw_counter = 0U;
    bool retry_generation_complete = s61_cow_raw_complete_counter(
        retry_flash, (unsigned)(retry_counter & 1U), &retry_raw_counter)
        && retry_raw_counter == retry_counter;
    bool protected_after_retry = memcmp(
        before + protected_offset, retry_flash + protected_offset,
        protected_size) == 0;
    if (damaged_after_retry != 0U
        || attempt_status != SUI_SAVE_ATTEMPT_OK
        || retry_counter != initial_counter + 1U
        || !retry_generation_complete || !protected_after_retry)
        s61_die("save UI COW real SaveFailed wipe/retry did not succeed");

    /* State 6 accepts the user's real A press.  Once field input is back, a
     * second complete START->SAVE interaction is the explicit user retry;
     * this prevents a host-direct HandleSavingData call from satisfying the
     * case even if the automatic damaged-sector recovery succeeded. */
    s61_pulse(core, WORLD_KEY_A, 2U, 60U, NULL);
    sui_wait_for_field_after_ack(core);
    if (!s61_normal_input_save(core))
        s61_die("save UI COW explicit START-menu retry failed");
    uint32_t final_counter = read32(core, WORLD_SAVE_COUNTER);
    if (final_counter != retry_counter + 1U)
        s61_die("save UI COW explicit retry counter did not advance once");
    s61_assert_link_save_canaries(core);

    uint8_t *after = s61_cow_clone_savedata(core);
    uint32_t final_raw_counter = 0U;
    if (!s61_cow_raw_complete_counter(
            after, (unsigned)(final_counter & 1U), &final_raw_counter)
        || final_raw_counter != final_counter)
        s61_die("save UI COW final generation is incomplete");
    s61_write_exact_binary(after_path, after, SUI_SAVE_BYTES);
    uint64_t before_hash = sui_hash_bytes(before, SUI_SAVE_BYTES);
    uint64_t after_hash = sui_hash_bytes(after, SUI_SAVE_BYTES);
    if (before_hash == after_hash)
        s61_die("save UI COW before/after save images are identical");

    free(retry_flash);
    free(fault_flash);
    bootstrap_close_core(core);
    s61_diagnostic_core = NULL;
    /* Materialize the exact post-retry bytes only after the old core is
     * closed; the next open therefore cannot inherit RAM or emulator state. */
    s61_write_exact_binary(retained_path, after, SUI_SAVE_BYTES);

    s61_allow_savedata_time_offset_notice = true;
    struct mCore *fresh = s61_open_fresh(
        rom_path, retained_path, &fixture);
    s61_allow_savedata_time_offset_notice = false;
    s61_assert_link_save_canaries(fresh);
    uint32_t fresh_flag = s61_flag(fresh, SUI_EXPANDED_FLAG_CANARY_ID);
    uint32_t fresh_var = s61_call_synced(
        fresh, WORLD_VAR_GET, SUI_EXPANDED_VAR_CANARY_ID, 0U, 0U, 0U);
    uint32_t fresh_last_ball = read16(fresh, WORLD_LAST_USED_BALL);
    uint32_t fresh_coins = read32(fresh, WORLD_PLAYER_COINS);
    if (fresh_flag != 1U || fresh_var != 0x61A5U
        || fresh_last_ball != 3U || fresh_coins != 0x00054321U)
        s61_die("save UI COW enumerated fresh canary readback differs");
    uint32_t fresh_counter = read32(fresh, WORLD_SAVE_COUNTER);
    bool fresh_field = world_overworld(fresh)
        && !world_script_enabled(fresh);
    uint32_t fresh_save1 = read32(fresh, BOOTSTRAP_SAVE_BLOCK1_PTR);
    if (fresh_save1 < 0x02000000U || fresh_save1 + 8U > 0x02040000U)
        s61_die("save UI COW fresh SaveBlock1 pointer differs");
    uint8_t fresh_group = read8(fresh, fresh_save1 + 4U);
    uint8_t fresh_map = read8(fresh, fresh_save1 + 5U);
    uint8_t fresh_warp = read8(fresh, fresh_save1 + 6U);
    uint16_t fresh_x = read16(fresh, fresh_save1);
    uint16_t fresh_y = read16(fresh, fresh_save1 + 2U);
    if (fresh_counter != final_counter || !fresh_field
        || fresh_group != fixture.group || fresh_map != fixture.map
        || fresh_x != fixture.x || fresh_y != fixture.y)
        s61_die("save UI COW hard fresh Continue differs");
    char continue_path[4096];
    char continue_framebuffer_raw_path[4096];
    sui_format_path(continue_path, sizeof(continue_path), directory,
                    "save-ui-cow-hard-continue");
    sui_format_path(
        continue_framebuffer_raw_path,
        sizeof(continue_framebuffer_raw_path), directory,
        "save-ui-cow-hard-continue.rgba");
    uint64_t continue_framebuffer_hash =
        bootstrap_framebuffer_hash(s61_video);
    uint64_t continue_ppm_hash = sui_hash_ppm_pixels(s61_video);
    s61_write_exact_binary(
        continue_framebuffer_raw_path, (const uint8_t *)s61_video,
        sizeof(s61_video));
    bootstrap_write_ppm(continue_path, s61_video);
    /* A passive field-memory readback cannot prove that the hard-fresh core
     * actually accepts player input.  Exercise the ordinary field callbacks
     * with real keys and require the exact map/position to survive the
     * START-menu roundtrip before the fresh core is closed. */
    struct SuiFreshInputLiveness input_liveness =
        sui_prove_fresh_input_liveness(fresh, &fixture);
    s61_assert_link_save_canaries(fresh);
    bootstrap_close_core(fresh);
    s61_diagnostic_core = NULL;
    const char *fault_phase = input.callback_return >= 0x09000000U
        && input.callback_return < 0x0A000000U
        ? "NORMAL_COW" : "STOCK";

    printf("{\"schema_version\":3,\"status\":\"PASS\","
           "\"case\":\"save_ui_cow_fault_retry_continue\","
           "\"preparation_only_host_writes\":true,"
           "\"direct_owner_or_script_calls\":0,"
           "\"natural_input\":{\"start_pressed\":true,"
           "\"save_action_selected\":true,"
           "\"confirmation_pulses\":%u,"
           "\"host_direct_save_callback\":false},"
           "\"engine_trace\":{"
           "\"save_serialized_game\":\"0x0804BAB8\","
           "\"save_serialized_game_hits_before_fault\":%u,"
           "\"update_save_addresses\":\"0x080DB1BC\","
           "\"update_save_addresses_hits_before_fault\":%u,"
           "\"handle_saving_data_hits_before_fault\":%u,"
           "\"save_data_buffer\":\"0x%08" PRIX32 "\","
           "\"save_data_buffer_stable\":true},"
           "\"fault\":{\"callback\":\"0x081C2E90\","
           "\"real_flash_callback_executed\":true,"
           "\"status_injected_at_real_return\":true,"
           "\"fault_callback_hits\":1,"
           "\"phase\":\"%s\","
           "\"normal_save_type\":%u,"
           "\"physical_sector\":%u,"
           "\"partial_flash_side_effect\":true,"
           "\"changed_bytes\":%u,\"damaged_mask_before_wipe\":%" PRIu32
           ",\"protected_slot\":%u,\"protected_counter\":%" PRIu32
           ",\"protected_generation_exact\":true,"
           "\"damaged_generation_incomplete\":true},"
           "\"save_failed_screen\":{"
           "\"real_owner_observed\":true,\"state5_observed\":true,"
           "\"framebuffer_hash\":\"%016" PRIx64 "\","
           "\"framebuffer_raw_path\":\"save-ui-cow-save-failed.rgba\","
           "\"artifact_path\":\"save-ui-cow-save-failed.ppm\","
           "\"artifact_pixel_fnv64\":\"%016" PRIx64 "\","
           "\"owner_state_trace\":["
           "{\"sequence\":0,\"pc\":\"0x%08" PRIX32 "\","
           "\"state_address\":\"0x0203AAC8\",\"state\":%u,"
           "\"active_address\":\"0x03005480\","
           "\"active\":%" PRIu32 "},"
           "{\"sequence\":1,\"pc\":\"0x%08" PRIX32 "\","
           "\"state_address\":\"0x0203AAC8\",\"state\":%u,"
           "\"active_address\":\"0x03005480\","
           "\"active\":%" PRIu32 "}],"
           "\"damaged_generation_wiped\":true,"
           "\"retry_completed\":true,\"attempt_status\":%u,"
           "\"state6_success_observed\":true,"
           "\"retry_acknowledged_with_a\":true,"
           "\"field_input_recovered\":true},"
           "\"explicit_retry\":{"
           "\"start_menu_save_with_keys\":true,"
           "\"counter_before\":%" PRIu32 ","
           "\"counter_after\":%" PRIu32 ","
           "\"full_generation_complete\":true},"
           "\"hard_restart\":{\"old_core_closed\":true,"
           "\"fresh_core_opened\":true,\"title_continue\":true,"
           "\"counter\":%" PRIu32 ",\"field_input_recovered\":true,"
           "\"location\":{\"map_group\":%u,\"map_number\":%u,"
           "\"x\":%u,\"y\":%u,\"warp_id\":%u},"
           "\"input_liveness\":{"
           "\"start_pressed\":%s,\"start_menu_opened\":%s,"
           "\"menu_callback_observed\":\"0x%08" PRIX32 "\","
           "\"back_pressed\":%s,\"callback_ordered\":%s,"
           "\"map_preserved\":%s,\"position_preserved\":%s,"
           "\"field_terminal\":%s,\"field_input_recovered\":%s,"
           "\"location_before\":{\"map_group\":%u,"
           "\"map_number\":%u,\"x\":%u,\"y\":%u,"
           "\"warp_id\":%u},"
           "\"location_after\":{\"map_group\":%u,"
           "\"map_number\":%u,\"x\":%u,\"y\":%u,"
           "\"warp_id\":%u}},"
           "\"framebuffer_hash\":\"%016" PRIx64 "\","
           "\"framebuffer_raw_path\":"
           "\"save-ui-cow-hard-continue.rgba\","
           "\"artifact_path\":\"save-ui-cow-hard-continue.ppm\","
           "\"artifact_pixel_fnv64\":"
           "\"%016" PRIx64 "\","
           "\"canaries_restored\":true,\"canary_count\":4,"
           "\"canaries\":["
           "{\"canary_id\":\"expanded_flag_18B4\","
           "\"region\":\"expanded_flags\",\"identifier\":6324,"
           "\"address\":\"0x%08X\",\"expected_value\":1,"
           "\"observed_value\":%" PRIu32 "},"
           "{\"canary_id\":\"expanded_var_5170\","
           "\"region\":\"expanded_vars\",\"identifier\":20848,"
           "\"address\":\"0x%08X\",\"expected_value\":24997,"
           "\"observed_value\":%" PRIu32 "},"
           "{\"canary_id\":\"last_used_ball\","
           "\"region\":\"last_used_ball\",\"identifier\":null,"
           "\"address\":\"0x%08X\",\"expected_value\":3,"
           "\"observed_value\":%" PRIu32 "},"
           "{\"canary_id\":\"player_coins\","
           "\"region\":\"player_coins\",\"identifier\":null,"
           "\"address\":\"0x%08X\",\"expected_value\":344865,"
           "\"observed_value\":%" PRIu32 "}]},"
           "\"srm\":{\"size\":%u,"
           "\"before_path\":\"save-ui-cow-before.srm\","
           "\"fault_path\":\"save-ui-cow-fault.srm\","
           "\"after_path\":\"save-ui-cow-after.srm\","
           "\"retained_path\":\"save-ui-cow-retained.srm\","
           "\"before_fnv64\":\"%016" PRIx64 "\","
           "\"fault_fnv64\":\"%016" PRIx64 "\","
           "\"after_fnv64\":\"%016" PRIx64 "\"},"
           "\"failed\":0,\"untested\":0,\"warnings\":0}\n",
           input.confirmation_pulses,
           input.save_serialized_game_hits,
           input.update_save_addresses_hits,
           input.wrapper_entry_hits, input.buffer_at_wrapper,
           fault_phase, input.save_type,
           input.fault_physical_sector, fault_changed_bytes,
           damaged_before_wipe, protected_slot, initial_counter,
           failed_framebuffer_hash, failed_ppm_hash,
           state5.pc, state5.state, state5.active,
           state6.pc, state6.state, state6.active,
           attempt_status, retry_counter, final_counter, fresh_counter,
           fresh_group, fresh_map, fresh_x, fresh_y, fresh_warp,
           input_liveness.roundtrip.start_pressed ? "true" : "false",
           input_liveness.roundtrip.start_menu_opened ? "true" : "false",
           input_liveness.roundtrip.menu_callback_observed,
           input_liveness.roundtrip.back_pressed ? "true" : "false",
           input_liveness.roundtrip.callback_ordered ? "true" : "false",
           input_liveness.map_preserved ? "true" : "false",
           input_liveness.position_preserved ? "true" : "false",
           input_liveness.field_terminal ? "true" : "false",
           input_liveness.roundtrip.field_input_recovered
               ? "true" : "false",
           input_liveness.before.group, input_liveness.before.map,
           input_liveness.before.x, input_liveness.before.y,
           input_liveness.before.warp,
           input_liveness.after.group, input_liveness.after.map,
           input_liveness.after.x, input_liveness.after.y,
           input_liveness.after.warp,
           continue_framebuffer_hash, continue_ppm_hash,
           SUI_EXPANDED_FLAG_CANARY_ADDRESS, fresh_flag,
           SUI_EXPANDED_VAR_CANARY_ADDRESS, fresh_var,
           WORLD_LAST_USED_BALL, fresh_last_ball,
           WORLD_PLAYER_COINS, fresh_coins,
           SUI_SAVE_BYTES, before_hash, fault_hash, after_hash);
    free(after);
    free(before);
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s ROM WORK_DIRECTORY\n", argv[0]);
        return 2;
    }
    if (mkdir(argv[2], 0700) != 0 && errno != EEXIST) {
        perror("mkdir");
        return 2;
    }
    s61_case_name = "save_ui_cow_fault_retry_continue";
    bootstrap_phase = s61_case_name;
    struct mLogger logger = {.log = s61_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    sui_run(argv[1], argv[2]);
    if (log_problem_count != 0U)
        s61_die("mGBA emitted warning/error diagnostics");
    return 0;
}
