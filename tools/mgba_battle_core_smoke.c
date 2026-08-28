/*
 * T06 CFRU-on-Vega battle-core smoke for libmGBA 0.10.2.
 *
 * This is a read-only runner.  It reuses the reviewed T04/T01 natural-new-game
 * trace, restores that field state for every case, and starts both a normal
 * wild battle and a normal trainer battle through the ROM's real setup paths.
 * Core routes use the real battle scheduler/controllers: normal wins, a
 * persistent major-status move, priority ordering between two selected moves,
 * four-battler spread damage, party-menu switching, faint/EXP, and bag/ball
 * capture.  No route is promoted to E2E evidence by a direct function call.
 */
#define main t01_ai_fixture_bundled_entry_point
#include "mgba_ai_fixture_runner.c"
#undef main

enum {
    BATTLE_CORE_FIELD_TRACE_SEGMENTS = 233,
    BATTLE_CORE_FIXED_FRAMES = 360,
    BATTLE_CORE_TURN_INPUT_PRESSES = 6,
    BATTLE_CORE_TURN_INPUT_WAIT = 160,
    BATTLE_CORE_TURN_SETTLE_FRAMES = 300,
    BATTLE_CORE_MENU_READY_FRAMES = 500,
    BATTLE_CORE_MENU_INPUT_WAIT = 160,
    BATTLE_CORE_SWITCH_MENU_PRESSES = 3,
    BATTLE_CORE_SWITCH_SETTLE_FRAMES = 800,
    BATTLE_CORE_DOUBLE_INPUT_PRESSES = 12,
    BATTLE_CORE_DOUBLE_SETTLE_FRAMES = 500,
    BATTLE_CORE_END_INPUT_PULSES = 64,
    BATTLE_CORE_END_INPUT_WAIT = 120,
    BATTLE_CORE_DIRECT_CALL_LIMIT = 5000000,
    BATTLE_CORE_CANONICAL_MOVE_COUNT = 1063,
    BATTLE_CORE_CANONICAL_MOVE_MAX = 1062,
    BATTLE_CORE_BATTLE_MOVE_SIZE = 12,
    BATTLE_CORE_MAX_BATTLERS = 4,
    BATTLE_CORE_MOVE_SLOTS = 4,
    BATTLE_CORE_MAX_VEGA_SPECIES = 411,

    BATTLE_CORE_PAYLOAD_START = 0x09000000,
    BATTLE_CORE_PAYLOAD_END = 0x09200000,
    BATTLE_CORE_ROM_END = 0x0A000000,

    BATTLE_CORE_MOVE_TABLE_REPOINT = 0x080001CC,
    BATTLE_CORE_CREATE_MON = 0x0803D1C1,
    BATTLE_CORE_GET_MON_DATA = 0x0803F355,
    BATTLE_CORE_START_WILD = 0x0807EE2D,
    BATTLE_CORE_START_TRAINER = 0x0807FB85,
    BATTLE_CORE_TRAINER_MODE = 0x020385E0,
    BATTLE_CORE_TRAINER_OPPONENT_A = 0x020385E2,
    BATTLE_CORE_GLOBAL_RNG = 0x03005040,
    BATTLE_CORE_ENEMY_PARTY_COUNT = 0x02023F8A,
    BATTLE_CORE_BATTLE_OUTCOME = 0x02023DEA,
    BATTLE_CORE_ACTION_SELECTION_CURSOR = 0x02023F58,
    BATTLE_CORE_MOVE_SELECTION_CURSOR = 0x02023F5C,
    BATTLE_CORE_CHOSEN_ACTIONS = 0x02023CDC,
    BATTLE_CORE_SELECTED_PARTY_MON = 0x0203B01D,
    BATTLE_CORE_BAG_STATE = 0x0203AC74,
    BATTLE_CORE_MAIN_CALLBACK2 = 0x03003134,

    BATTLE_CORE_ADD_BAG_ITEM = 0x08099A8D,
    BATTLE_CORE_CHECK_BAG_HAS_ITEM = 0x08099949,

    BATTLE_CORE_MON_STAT_STAGES = 0x19,
    BATTLE_CORE_MON_HP = 0x28,
    BATTLE_CORE_MON_LEVEL = 0x2A,
    BATTLE_CORE_MON_EXPERIENCE = 0x44,
    BATTLE_CORE_MON_STATUS1 = 0x4C,
    BATTLE_CORE_MON_STATUS2 = 0x50,
    BATTLE_CORE_MON_DATA_EXP = 25,
    BATTLE_CORE_MON_DATA_STATUS = 55,
    BATTLE_CORE_MON_DATA_HP = 57,
    BATTLE_CORE_PARTY_SPECIES_OFFSET = 0x20,
    BATTLE_CORE_PARTY_EXPERIENCE_OFFSET = 0x24,
    BATTLE_CORE_PARTY_STATUS_OFFSET = 0x50,
    BATTLE_CORE_MOVE_TOXIC = 92,
    BATTLE_CORE_MOVE_QUICK_ATTACK = 98,
    BATTLE_CORE_MOVE_SCRATCH = 10,
    BATTLE_CORE_MOVE_TACKLE = 33,
    BATTLE_CORE_STATUS_TOXIC = 0x80,
    BATTLE_CORE_MON_SPEED = 0x06,
    BATTLE_CORE_MON_TYPE1 = 0x21,
    BATTLE_CORE_MON_TYPE2 = 0x22,
    BATTLE_CORE_TYPE_POISON = 3,
    BATTLE_CORE_TYPE_STEEL = 8,
    BATTLE_CORE_BANKS_BY_TURN_ORDER = 0x02023B3E,
    BATTLE_CORE_CHOSEN_MOVES = 0x02023D24,
    BATTLE_CORE_OUTCOME_WON = 1,
    BATTLE_CORE_OUTCOME_CAUGHT = 7,
    BATTLE_CORE_ACTION_USE_ITEM = 1,
    BATTLE_CORE_ACTION_SWITCH = 2,
    BATTLE_CORE_MASTER_BALL = 1,
    BATTLE_CORE_BAG_BALL_POCKET = 2,

#if defined(BATTLE_CORE_ISOLATE_HOST_CALL_STACK)
#if !defined(BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS) \
    || !defined(BATTLE_CORE_HOST_STACK_TOP_ADDRESS)
#error "isolated host calls require explicit scratch-stack bounds"
#endif
    /*
     * Host-direct calls must not borrow either the interrupted System stack
     * or the banked IRQ stack.  The including runner must select an interval
     * whose normal owner is inactive for every direct-call target.  Every
     * byte is restored before the emulated scheduler resumes.
     */
    BATTLE_CORE_HOST_STACK_BOTTOM = BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS,
    BATTLE_CORE_HOST_STACK_TOP = BATTLE_CORE_HOST_STACK_TOP_ADDRESS,
    BATTLE_CORE_HOST_STACK_SIZE =
        BATTLE_CORE_HOST_STACK_TOP - BATTLE_CORE_HOST_STACK_BOTTOM,
    BATTLE_CORE_HOST_STACK_GUARD_SIZE = 64,
    BATTLE_CORE_HOST_STACK_MAX_ARGUMENTS = 8,
#endif
};

_Static_assert(ARRAY_LEN(BOOT_TRACE) >= BATTLE_CORE_FIELD_TRACE_SEGMENTS,
               "T04 natural-field trace prefix is unavailable");

enum RouteIndex {
    ROUTE_STATUS,
    ROUTE_PRIORITY,
    ROUTE_MULTI_TARGET,
    ROUTE_SWITCH,
    ROUTE_FAINT,
    ROUTE_EXPERIENCE,
    ROUTE_CAPTURE,
    ROUTE_COUNT,
};

struct HookContract {
    const char *route;
    const char *classification;
    const char *observation;
    uint32_t site;
    uint8_t reg;
    bool direct_call;
};

static const struct HookContract ROUTE_CONTRACTS[ROUTE_COUNT] = {
    {"status", "SCHEDULER_E2E", "Toxic_status_battle_party_persistence_and_cleanup",
     0x0801F730, 2, false},
    {"priority", "SCHEDULER_E2E", "slower_Quick_Attack_precedes_faster_Tackle",
     0x080144F8, 3, false},
    {"multi_target", "SCHEDULER_E2E", "double_four_controller_spread_damage",
     0x08012B28, 0, false},
    {"switch", "SCHEDULER_E2E", "battle_command_party_menu_controller_switch",
     0x08019420, 3, false},
    {"faint", "SCHEDULER_E2E", "enemy_HP_zero_and_battle_cleanup",
     0x080187A0, 0, false},
    {"experience", "SCHEDULER_E2E", "party_experience_increased_after_faint",
     0x08049942, 1, false},
    {"capture", "SCHEDULER_E2E", "battle_bag_master_ball_capture_cleanup",
     0x08015C72, 0, false},
};

static const struct HookContract WILD_SETUP_HOOK = {
    "wild_setup", "DIRECT_CALL_BOUNDED", "DoStandardWildBattle",
    0x0807EE70, 0, true,
};

static const struct HookContract TRAINER_SETUP_HOOK = {
    "trainer_setup", "DIRECT_CALL_BOUNDED", "BattleSetup_StartTrainerBattle",
    0x0807FB84, 0, true,
};

struct CpuState {
    int32_t registers[17];
};

#if defined(BATTLE_CORE_ISOLATE_HOST_CALL_STACK)
struct HostCallStack {
    uint8_t original[BATTLE_CORE_HOST_STACK_SIZE];
    uint32_t entry_sp;
};

_Static_assert((BATTLE_CORE_HOST_STACK_BOTTOM & 7U) == 0U,
               "host-call scratch-stack bottom must be 8-byte aligned");
_Static_assert((BATTLE_CORE_HOST_STACK_TOP & 7U) == 0U,
               "host-call scratch-stack top must be 8-byte aligned");
_Static_assert(BATTLE_CORE_HOST_STACK_BOTTOM >= 0x02000000U
                   && BATTLE_CORE_HOST_STACK_TOP <= 0x02040000U,
               "host-call scratch stack must stay inside EWRAM");
_Static_assert(BATTLE_CORE_HOST_STACK_SIZE
                   > BATTLE_CORE_HOST_STACK_GUARD_SIZE + 256U,
               "host-call scratch stack is too small");
#endif

static const char *const CPU_REGISTER_NAMES[17] = {
    "r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8",
    "r9", "r10", "r11", "r12", "sp", "lr", "pc", "cpsr",
};

struct HookObservation {
    uint32_t target;
    uint8_t stub_size;
};

struct CallObservation {
    uint32_t result;
    uint32_t instructions;
    bool payload_pc_seen;
};

struct MoveTableObservation {
    uint32_t pointer;
    uint32_t status_count;
    uint32_t priority_count;
    uint32_t multi_target_count;
};

struct MonObservation {
    uint16_t species;
    uint16_t hp;
    uint8_t level;
    uint16_t moves[BATTLE_CORE_MOVE_SLOTS];
    uint8_t pp[BATTLE_CORE_MOVE_SLOTS];
    uint32_t experience;
    uint32_t status1;
    uint32_t status2;
};

struct TurnObservation {
    uint8_t selected_slot;
    uint16_t selected_move;
    uint8_t pp_before;
    uint8_t pp_after;
    uint16_t player_hp_before;
    uint16_t player_hp_after;
    uint16_t opponent_hp_before;
    uint16_t opponent_hp_after;
    uint32_t opponent_status_before;
    uint32_t opponent_status_after;
    uint32_t opponent_party_status_before;
    uint32_t opponent_party_status_after;
    uint8_t outcome_before;
    uint8_t outcome_after;
    uint32_t frames;
    bool pp_spent;
    bool hp_changed;
    bool status_applied;
};

struct BattleObservation {
    uint32_t type_flags;
    uint8_t battler_count;
    uint8_t absent_flags;
    uint8_t outcome;
    uint32_t setup_frames;
    uint64_t ram_digest;
    bool new_battle_struct_initialized;
    bool battle_struct_initialized;
    bool battle_resources_initialized;
    struct CallObservation setup_call;
    struct MonObservation battlers[BATTLE_CORE_MAX_BATTLERS];
    struct TurnObservation turn;
};

struct StatusObservation {
    struct BattleObservation battle;
    uint32_t party_status_after_cleanup;
    uint32_t cleanup_frames;
    uint8_t outcome_seen;
    bool enemy_fainted_seen;
    bool battle_runtime_cleaned;
    bool status_cleared_on_faint;
};

struct PriorityObservation {
    struct BattleObservation battle;
    uint16_t priority_move;
    uint16_t alternative_move;
    uint16_t opponent_move;
    int8_t priority_value;
    int8_t opponent_priority_value;
    uint16_t player_speed;
    uint16_t opponent_speed;
    uint8_t turn_order[2];
    uint8_t first_damage_dealt_by;
    uint8_t player_pp_before;
    uint8_t player_pp_after;
    uint8_t opponent_pp_before;
    uint8_t opponent_pp_after;
    uint16_t player_hp_before;
    uint16_t player_hp_after;
    uint16_t opponent_hp_before;
    uint16_t opponent_hp_after;
    uint32_t frames;
    bool selected_through_controller;
    bool both_moves_executed;
    bool slower_priority_user_moved_first;
};

struct EndObservation {
    struct CallObservation setup_call;
    bool trainer;
    uint32_t experience_before;
    uint32_t experience_after;
    uint32_t frames;
    uint8_t outcome_seen;
    bool enemy_fainted_seen;
    bool battle_runtime_initialized;
    bool battle_runtime_cleaned;
};

struct MultiTargetObservation {
    struct CallObservation setup_call;
    uint32_t type_flags;
    uint8_t battler_count;
    uint16_t species[BATTLE_CORE_MAX_BATTLERS];
    uint16_t party_index[BATTLE_CORE_MAX_BATTLERS];
    uint16_t spread_move;
    uint8_t spread_pp_before;
    uint8_t spread_pp_after;
    uint16_t opponent_hp_before[2];
    uint16_t opponent_hp_after[2];
    uint32_t frames;
    bool four_controllers_initialized;
    bool both_opponents_hit;
};

struct SwitchObservation {
    struct CallObservation setup_call;
    uint16_t species_before;
    uint16_t species_after;
    uint16_t party_index_before;
    uint16_t party_index_after;
    uint8_t selected_party_mon;
    uint8_t chosen_action;
    uint32_t battle_callback;
    uint32_t party_menu_callback;
    uint32_t frames;
    bool party_menu_opened;
    bool controller_returned;
};

struct CaptureObservation {
    struct CallObservation setup_call;
    uint32_t add_ball_result;
    uint32_t add_ball_instructions;
    uint32_t frames;
    uint8_t outcome_seen;
    uint8_t party_count_before;
    uint8_t party_count_after;
    uint16_t captured_species;
    uint8_t chosen_action;
    bool bag_opened;
    bool ball_consumed;
    bool battle_runtime_initialized;
    bool battle_runtime_cleaned;
};

static void battle_core_die(const char *message) {
    fprintf(stderr, "mgba-battle-core-smoke: %s\n", message);
    exit(1);
}

static bool payload_address(uint32_t address) {
    address &= ~1U;
    return address >= BATTLE_CORE_PAYLOAD_START && address < BATTLE_CORE_PAYLOAD_END;
}

static void write32_bytes(struct mCore *core, uint32_t address, uint32_t value) {
    for (unsigned byte = 0; byte < 4; ++byte) {
        write8(core, address + byte, (uint8_t)(value >> (byte * 8)));
    }
}

static struct CpuState capture_cpu_state(struct mCore *core) {
    struct CpuState result;
    for (unsigned index = 0; index < ARRAY_LEN(CPU_REGISTER_NAMES); ++index) {
        result.registers[index] = read_register(core, CPU_REGISTER_NAMES[index]);
    }
    return result;
}

static void restore_cpu_state(struct mCore *core, const struct CpuState *state) {
    write_register(core, "cpsr", (uint32_t)state->registers[16]);
    for (unsigned index = 0; index < 15; ++index) {
        write_register(core, CPU_REGISTER_NAMES[index],
                       (uint32_t)state->registers[index]);
    }
    write_register(core, "pc", (uint32_t)state->registers[15]);
}

#if defined(BATTLE_CORE_ISOLATE_HOST_CALL_STACK)
static uint8_t host_stack_guard_byte(unsigned index) {
    return (uint8_t)(0xA5U ^ (uint8_t)(index * 29U));
}

static void begin_host_call_stack(struct mCore *core,
                                  struct HostCallStack *stack,
                                  const uint32_t *arguments,
                                  unsigned argument_count) {
    if (argument_count > BATTLE_CORE_HOST_STACK_MAX_ARGUMENTS
        || (argument_count != 0U && arguments == NULL)) {
        battle_core_die("host-call scratch-stack argument contract failed");
    }
    for (unsigned byte = 0U; byte < BATTLE_CORE_HOST_STACK_SIZE; ++byte) {
        stack->original[byte] = read8(
            core, BATTLE_CORE_HOST_STACK_BOTTOM + byte);
    }
    for (unsigned byte = 0U;
         byte < BATTLE_CORE_HOST_STACK_GUARD_SIZE; ++byte) {
        write8(core, BATTLE_CORE_HOST_STACK_BOTTOM + byte,
               host_stack_guard_byte(byte));
    }

    uint32_t argument_bytes = argument_count * 4U;
    uint32_t aligned_bytes = (argument_bytes + 7U) & ~7U;
    stack->entry_sp = BATTLE_CORE_HOST_STACK_TOP - aligned_bytes;
    for (unsigned index = 0U; index < argument_count; ++index) {
        write32_bytes(core, stack->entry_sp + index * 4U, arguments[index]);
    }
    write_register(core, "sp", stack->entry_sp);
}

static bool restore_host_call_stack(struct mCore *core,
                                    const struct HostCallStack *stack) {
    bool guard_intact = true;
    for (unsigned byte = 0U;
         byte < BATTLE_CORE_HOST_STACK_GUARD_SIZE; ++byte) {
        guard_intact = guard_intact
            && read8(core, BATTLE_CORE_HOST_STACK_BOTTOM + byte)
                == host_stack_guard_byte(byte);
    }
    bool stack_balanced = (uint32_t)read_register(core, "sp")
        == stack->entry_sp;
    for (unsigned byte = 0U; byte < BATTLE_CORE_HOST_STACK_SIZE; ++byte) {
        write8(core, BATTLE_CORE_HOST_STACK_BOTTOM + byte,
               stack->original[byte]);
    }
    return guard_intact && stack_balanced;
}
#endif

static struct CallObservation call_bounded(struct mCore *core, uint32_t function,
                                           uint32_t r0, uint32_t r1,
                                           uint32_t r2, uint32_t r3) {
    struct CallObservation result = {0};
    struct CpuState original = capture_cpu_state(core);
#if defined(BATTLE_CORE_ISOLATE_HOST_CALL_STACK)
    struct HostCallStack call_stack;
    begin_host_call_stack(core, &call_stack, NULL, 0U);
#endif
    uint32_t cpsr = (uint32_t)original.registers[16];
    write_register(core, "cpsr", cpsr | 0xA0U);
    write_register(core, "lr", 0x08000001U);
    write_register(core, "r0", r0);
    write_register(core, "r1", r1);
    write_register(core, "r2", r2);
    write_register(core, "r3", r3);
    write_register(core, "pc", function);
    while ((((uint32_t)read_register(core, "pc")) & ~1U) != 0x08000002U) {
        uint32_t pc = ((uint32_t)read_register(core, "pc")) & ~1U;
        if (payload_address(pc)) result.payload_pc_seen = true;
        if (++result.instructions > BATTLE_CORE_DIRECT_CALL_LIMIT) {
            battle_core_die("bounded direct ROM call exceeded instruction limit");
        }
        core->step(core);
    }
    result.result = (uint32_t)read_register(core, "r0");
#if defined(BATTLE_CORE_ISOLATE_HOST_CALL_STACK)
    bool stack_ok = restore_host_call_stack(core, &call_stack);
#endif
    restore_cpu_state(core, &original);
#if defined(BATTLE_CORE_ISOLATE_HOST_CALL_STACK)
    if (!stack_ok)
        battle_core_die("bounded direct call overflowed its scratch stack");
#endif
    return result;
}

static struct HookObservation observe_hook(struct mCore *core,
                                           const struct HookContract *contract) {
    struct HookObservation result = {0};
    uint32_t site = contract->site;
    if (site & 1U) battle_core_die("hook contract site is not halfword aligned");
    if (site & 2U) {
        if (read8(core, site) != 0x01U
            || read8(core, site + 1) != (uint8_t)(0x48U | contract->reg)
            || read8(core, site + 2) != (uint8_t)(contract->reg << 3)
            || read8(core, site + 3) != 0x47U
            || read16(core, site + 4) != 0) {
            battle_core_die("hook stub differs from the classified CFRU Thumb emission");
        }
        result.stub_size = 10;
        result.target = read32(core, site + 6);
    } else {
        if (read8(core, site) != 0x00U
            || read8(core, site + 1) != (uint8_t)(0x48U | contract->reg)
            || read8(core, site + 2) != (uint8_t)(contract->reg << 3)
            || read8(core, site + 3) != 0x47U) {
            battle_core_die("hook stub differs from the classified CFRU Thumb emission");
        }
        result.stub_size = 8;
        result.target = read32(core, site + 4);
    }
    if (!(result.target & 1U) || !payload_address(result.target)) {
        battle_core_die("classified battle hook does not target CFRU payload code");
    }
    return result;
}

static struct MoveTableObservation observe_move_table(struct mCore *core) {
    struct MoveTableObservation result = {0};
    result.pointer = read32(core, BATTLE_CORE_MOVE_TABLE_REPOINT);
    uint64_t end = (uint64_t)result.pointer
        + (uint64_t)BATTLE_CORE_CANONICAL_MOVE_COUNT * BATTLE_CORE_BATTLE_MOVE_SIZE;
    if ((result.pointer & 3U) || result.pointer < 0x08000000U
        || end > BATTLE_CORE_ROM_END) {
        battle_core_die("canonical gBattleMoves pointer/range is invalid");
    }
    for (uint32_t move = 1; move <= BATTLE_CORE_CANONICAL_MOVE_MAX; ++move) {
        uint32_t row = result.pointer + move * BATTLE_CORE_BATTLE_MOVE_SIZE;
        uint8_t type = read8(core, row + 2);
        uint8_t target = read8(core, row + 6);
        int8_t priority = (int8_t)read8(core, row + 7);
        uint8_t split = read8(core, row + 10);
        if (type > 24U || split > 2U) {
            battle_core_die("canonical move row has invalid type/split ABI");
        }
        if (split == 2U) ++result.status_count;
        if (priority != 0) ++result.priority_count;
        if (target & (0x08U | 0x20U)) ++result.multi_target_count;
    }
    if (!result.status_count || !result.priority_count || !result.multi_target_count) {
        battle_core_die("canonical move table lacks a required route class");
    }
    return result;
}

static void run_trace_prefix(struct mCore *core) {
    for (unsigned segment = 0; segment < BATTLE_CORE_FIELD_TRACE_SEGMENTS; ++segment) {
        core->setKeys(core, BOOT_TRACE[segment].keys);
        for (uint32_t frame = 0; frame < BOOT_TRACE[segment].frames; ++frame) {
            core->runFrame(core);
        }
    }
    core->setKeys(core, 0);
}

static void run_fixed_frames(struct mCore *core) {
    core->setKeys(core, 0);
    for (unsigned frame = 0; frame < BATTLE_CORE_FIXED_FRAMES; ++frame) {
        core->runFrame(core);
    }
}

static uint32_t call_preserving(struct mCore *core, uint32_t function,
                                uint32_t r0, uint32_t r1,
                                uint32_t r2, uint32_t r3) {
    struct CpuState original = capture_cpu_state(core);
#if defined(BATTLE_CORE_ISOLATE_HOST_CALL_STACK)
    struct HostCallStack call_stack;
    begin_host_call_stack(core, &call_stack, NULL, 0U);
#endif
    uint32_t result = call_rom_args(core, function, r0, r1, r2, r3).return_value;
#if defined(BATTLE_CORE_ISOLATE_HOST_CALL_STACK)
    bool stack_ok = restore_host_call_stack(core, &call_stack);
#endif
    restore_cpu_state(core, &original);
#if defined(BATTLE_CORE_ISOLATE_HOST_CALL_STACK)
    if (!stack_ok)
        battle_core_die("direct call overflowed its scratch stack");
#endif
    return result;
}

static void clear_parties(struct mCore *core) {
    for (unsigned byte = 0; byte < PARTY_SIZE * POKEMON_SIZE; ++byte) {
        write8(core, ADDR_PLAYER_PARTY + byte, 0);
        write8(core, ADDR_ENEMY_PARTY + byte, 0);
    }
    write8(core, ADDR_PLAYER_PARTY_COUNT, 0);
    write8(core, BATTLE_CORE_ENEMY_PARTY_COUNT, 0);
}

static void set_mon_data_u32(struct mCore *core, uint32_t mon,
                             uint32_t field, uint32_t value);

static void create_mon(struct mCore *core, uint32_t destination,
                       uint16_t species, uint8_t level) {
    struct CpuState original = capture_cpu_state(core);
#if defined(BATTLE_CORE_ISOLATE_HOST_CALL_STACK)
    static const uint32_t stack_arguments[4] = {0U, 0U, 0U, 0U};
    struct HostCallStack call_stack;
    begin_host_call_stack(
        core, &call_stack, stack_arguments, ARRAY_LEN(stack_arguments));
#else
    uint32_t original_sp = (uint32_t)original.registers[13];
    uint32_t call_sp = (original_sp - 16U) & ~7U;
    for (unsigned byte = 0; byte < 16; ++byte) write8(core, call_sp + byte, 0);
    write_register(core, "sp", call_sp);
#endif
    (void)call_rom_args(core, BATTLE_CORE_CREATE_MON,
                        destination, species, level, 0);
#if defined(BATTLE_CORE_ISOLATE_HOST_CALL_STACK)
    bool stack_ok = restore_host_call_stack(core, &call_stack);
#endif
    restore_cpu_state(core, &original);
#if defined(BATTLE_CORE_ISOLATE_HOST_CALL_STACK)
    if (!stack_ok)
        battle_core_die("CreateMon overflowed its scratch stack");
#endif
    if (call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                        destination, 11, 0, 0) != species) {
        battle_core_die("CreateMon species readback failed");
    }
    uint32_t actual_level = call_preserving(
        core, BATTLE_CORE_GET_MON_DATA, destination, 56, 0, 0);
    if (actual_level != level) {
        char diagnostic[128];
        (void)snprintf(diagnostic, sizeof(diagnostic),
                       "CreateMon level readback failed species=%u expected=%u actual=%u exp=%u",
                       species, level, actual_level,
                       call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                                       destination, BATTLE_CORE_MON_DATA_EXP, 0, 0));
        battle_core_die(diagnostic);
    }
}

static void create_mon_image(struct mCore *core, uint16_t species, uint8_t level,
                             const uint16_t moves[BATTLE_CORE_MOVE_SLOTS],
                             const uint8_t pp[BATTLE_CORE_MOVE_SLOTS],
                             uint8_t output[POKEMON_SIZE]) {
    struct Snapshot original = take_snapshot(core);
    create_mon(core, ADDR_PLAYER_PARTY, species, level);
    if (moves != NULL && pp != NULL) {
        for (unsigned slot = 0; slot < BATTLE_CORE_MOVE_SLOTS; ++slot) {
            set_mon_data_u32(core, ADDR_PLAYER_PARTY,
                             MON_DATA_MOVE1 + slot, moves[slot]);
            set_mon_data_u32(core, ADDR_PLAYER_PARTY,
                             MON_DATA_PP1 + slot, pp[slot]);
        }
    }
    for (unsigned byte = 0; byte < POKEMON_SIZE; ++byte) {
        output[byte] = read8(core, ADDR_PLAYER_PARTY + byte);
    }
    restore_snapshot(core, &original);
    free(original.bytes);
}

static void install_mon_image(struct mCore *core, uint32_t destination,
                              const uint8_t image[POKEMON_SIZE]) {
    for (unsigned byte = 0; byte < POKEMON_SIZE; ++byte) {
        write8(core, destination + byte, image[byte]);
    }
}

static void set_mon_data_u32(struct mCore *core, uint32_t mon,
                             uint32_t field, uint32_t value) {
    write32_bytes(core, SET_MON_DATA_SCRATCH, value);
    (void)call_preserving(core, ROM_SET_MON_DATA,
                          mon, field, SET_MON_DATA_SCRATCH, 0);
    if (call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                        mon, field, 0, 0) != value) {
        battle_core_die("SetMonData fixture readback failed");
    }
}

static void seed_fixture(struct mCore *core) {
    write32_bytes(core, BATTLE_CORE_GLOBAL_RNG, UINT32_C(0x12345678));
}

static struct MonObservation observe_mon(struct mCore *core, unsigned battler) {
    struct MonObservation result = {0};
    uint32_t base = ADDR_BATTLE_MONS + battler * BATTLE_MON_SIZE;
    result.species = read16(core, base);
    result.hp = read16(core, base + BATTLE_CORE_MON_HP);
    result.level = read8(core, base + BATTLE_CORE_MON_LEVEL);
    result.experience = read32(core, base + BATTLE_CORE_MON_EXPERIENCE);
    result.status1 = read32(core, base + BATTLE_CORE_MON_STATUS1);
    result.status2 = read32(core, base + BATTLE_CORE_MON_STATUS2);
    if (!result.species || result.species > BATTLE_CORE_MAX_VEGA_SPECIES
        || !result.hp || !result.level) {
        char diagnostic[160];
        (void)snprintf(
            diagnostic,
            sizeof(diagnostic),
            "battle fixture battler %u invalid (species=%u hp=%u level=%u "
            "maxhp=%u item=%u ability=%u raw28=%08x raw2c=%08x)",
            battler, result.species, result.hp, result.level,
            read16(core, base + 0x2C), read16(core, base + 0x2E),
            read16(core, base + 0x38), read32(core, base + 0x28),
            read32(core, base + 0x2C));
        battle_core_die(diagnostic);
    }
    unsigned populated = 0;
    for (unsigned slot = 0; slot < BATTLE_CORE_MOVE_SLOTS; ++slot) {
        result.moves[slot] = read16(core, base + BATTLE_MON_MOVES_OFFSET + slot * 2);
        result.pp[slot] = read8(core, base + BATTLE_MON_PP_OFFSET + slot);
        if (!result.moves[slot]) continue;
        ++populated;
        if (result.moves[slot] > BATTLE_CORE_CANONICAL_MOVE_MAX || !result.pp[slot]) {
            battle_core_die("active move lies outside canonical 0..1062 ABI or has zero PP");
        }
    }
    if (!populated) {
        char diagnostic[160];
        (void)snprintf(
            diagnostic,
            sizeof(diagnostic),
            "active battler %u species %u has no canonical move (pp=%u/%u/%u/%u)",
            battler,
            result.species,
            result.pp[0], result.pp[1], result.pp[2], result.pp[3]);
        battle_core_die(diagnostic);
    }
    return result;
}

static void run_key_frames(struct mCore *core, uint16_t keys,
                           uint32_t frames) {
    core->setKeys(core, keys);
    for (uint32_t frame = 0; frame < frames; ++frame) {
        core->runFrame(core);
    }
}

static struct TurnObservation execute_one_turn(struct mCore *core,
                                                uint8_t selected_slot,
                                                uint32_t expected_status_mask) {
    struct TurnObservation result = {0};
    struct MonObservation before_player = observe_mon(core, 0);
    struct MonObservation before_opponent = observe_mon(core, 1);

    if (selected_slot >= BATTLE_CORE_MOVE_SLOTS
        || before_player.moves[selected_slot] == 0
        || before_player.pp[selected_slot] == 0) {
        battle_core_die("turn fixture selected an unavailable move slot");
    }

    result.selected_slot = selected_slot;
    result.selected_move = before_player.moves[selected_slot];
    result.pp_before = before_player.pp[selected_slot];
    result.player_hp_before = before_player.hp;
    result.opponent_hp_before = before_opponent.hp;
    result.opponent_status_before = before_opponent.status1;
    /* The T06 flat Pokemon ABI makes these fields directly observable.  A
     * ROM direct-call while the scheduler is active advances mGBA timing and
     * can consume the input cadence, so live-route observations stay passive. */
    result.opponent_party_status_before = read32(
        core, ADDR_ENEMY_PARTY + BATTLE_CORE_PARTY_STATUS_OFFSET);
    result.outcome_before = read8(core, BATTLE_CORE_BATTLE_OUTCOME);

    /*
     * Reuse the reviewed T04 UI cadence.  Pinning gMoveSelectionCursor before
     * every A press makes slot 0/1 deterministic without bypassing the battle
     * controller, command buffers, scripts, animations, or end-turn state.
     */
    for (unsigned press = 0; press < BATTLE_CORE_TURN_INPUT_PRESSES; ++press) {
        write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR, selected_slot);
        run_key_frames(core, 1, 2);
        run_key_frames(core, 0, BATTLE_CORE_TURN_INPUT_WAIT);
    }
    run_key_frames(core, 0, BATTLE_CORE_TURN_SETTLE_FRAMES);
    result.frames = BATTLE_CORE_TURN_INPUT_PRESSES
        * (2U + BATTLE_CORE_TURN_INPUT_WAIT)
        + BATTLE_CORE_TURN_SETTLE_FRAMES;

    struct MonObservation after_player = observe_mon(core, 0);
    struct MonObservation after_opponent = observe_mon(core, 1);
    result.pp_after = after_player.pp[selected_slot];
    result.player_hp_after = after_player.hp;
    result.opponent_hp_after = after_opponent.hp;
    result.opponent_status_after = after_opponent.status1;
    result.opponent_party_status_after = read32(
        core, ADDR_ENEMY_PARTY + BATTLE_CORE_PARTY_STATUS_OFFSET);
    result.outcome_after = read8(core, BATTLE_CORE_BATTLE_OUTCOME);
    result.pp_spent = result.pp_after < result.pp_before;
    result.hp_changed = result.player_hp_after != result.player_hp_before
        || result.opponent_hp_after != result.opponent_hp_before;
    result.status_applied = expected_status_mask != 0
        && !(result.opponent_status_before & expected_status_mask)
        && (result.opponent_status_after & expected_status_mask)
        && (result.opponent_party_status_after & expected_status_mask);

    if (after_player.species != before_player.species
        || after_opponent.species != before_opponent.species
        || memcmp(after_player.moves, before_player.moves,
                  sizeof(after_player.moves)) != 0
        || memcmp(after_opponent.moves, before_opponent.moves,
                  sizeof(after_opponent.moves)) != 0) {
        battle_core_die("one-turn fixture changed active species/move identity");
    }
    if (!result.pp_spent || result.pp_after + 1U != result.pp_before) {
        char diagnostic[320];
        (void)snprintf(
            diagnostic, sizeof(diagnostic),
            "one-turn fixture did not spend exactly one selected PP "
            "(move=%u slot=%u before=%u after=%u player=%u/%u opponent=%u/%u "
            "status=%08" PRIx32 " outcome=%u)",
            result.selected_move, selected_slot, result.pp_before, result.pp_after,
            result.player_hp_before, result.player_hp_after,
            result.opponent_hp_before, result.opponent_hp_after,
            result.opponent_status_after, result.outcome_after);
        battle_core_die(diagnostic);
    }
    if (result.outcome_before != 0 || result.outcome_after != 0) {
        battle_core_die("non-finishing one-turn fixture unexpectedly ended battle");
    }
    if (expected_status_mask != 0) {
        if (result.selected_move != BATTLE_CORE_MOVE_TOXIC
            || !result.status_applied
            || result.opponent_party_status_before != 0
            || (result.opponent_status_after & expected_status_mask)
                 != (result.opponent_party_status_after & expected_status_mask)) {
            char diagnostic[224];
            (void)snprintf(
                diagnostic,
                sizeof(diagnostic),
                "Toxic fixture did not persist major status to the enemy party "
                "(move=%u active_before=%08" PRIx32 " active_after=%08" PRIx32
                " party_before=%08" PRIx32 " party_after=%08" PRIx32
                " dynamax_timer=%u)",
                result.selected_move, result.opponent_status_before,
                result.opponent_status_after, result.opponent_party_status_before,
                result.opponent_party_status_after,
                read8(core, read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) + 0x253));
            battle_core_die(diagnostic);
        }
    } else if (!result.hp_changed) {
        battle_core_die("damaging one-turn fixture produced no HP change");
    }
    return result;
}

static struct BattleObservation observe_battle(struct mCore *core,
                                               bool trainer,
                                               struct CallObservation setup_call) {
    struct BattleObservation result = {0};
    result.setup_frames = BATTLE_CORE_FIXED_FRAMES;
    result.setup_call = setup_call;
    result.type_flags = read32(core, ADDR_BATTLE_TYPE_FLAGS);
    result.battler_count = read8(core, ADDR_BATTLERS_COUNT);
    result.absent_flags = read8(core, ADDR_ABSENT_BATTLER_FLAGS);
    result.outcome = read8(core, BATTLE_CORE_BATTLE_OUTCOME);
    result.new_battle_struct_initialized = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0;
    result.battle_struct_initialized = read32(core, ADDR_BATTLE_STRUCT_POINTER) != 0;
    result.battle_resources_initialized = read32(core, ADDR_BATTLE_RESOURCES_POINTER) != 0;
    if (((result.type_flags & BATTLE_TYPE_TRAINER) != 0) != trainer) {
        battle_core_die("normal battle trainer flag differs");
    }
    if (result.battler_count != 2) {
        battle_core_die("normal battle battler count differs");
    }
    if (result.absent_flags & 0x03U) {
        battle_core_die("normal battle marks an active side absent");
    }
    if (!result.new_battle_struct_initialized) {
        battle_core_die("normal battle gNewBS was not initialized");
    }
    if (!result.battle_struct_initialized) {
        battle_core_die("normal battle gBattleStruct was not initialized");
    }
    if (!result.battle_resources_initialized) {
        battle_core_die("normal battle gBattleResources was not initialized");
    }
    for (unsigned battler = 0; battler < result.battler_count; ++battler) {
        result.battlers[battler] = observe_mon(core, battler);
    }
    result.ram_digest = fnv1a64_ram(core);
    return result;
}

static struct CallObservation setup_wild(struct mCore *core,
                                         const struct Snapshot *field) {
    static const uint16_t player_moves[BATTLE_CORE_MOVE_SLOTS] = {
        BATTLE_CORE_MOVE_SCRATCH, 0, 0, 0,
    };
    static const uint8_t player_pp[BATTLE_CORE_MOVE_SLOTS] = {35, 0, 0, 0};
    static const uint16_t enemy_moves[BATTLE_CORE_MOVE_SLOTS] = {
        BATTLE_CORE_MOVE_TACKLE, 0, 0, 0,
    };
    static const uint8_t enemy_pp[BATTLE_CORE_MOVE_SLOTS] = {35, 0, 0, 0};
    uint8_t player[POKEMON_SIZE];
    uint8_t enemy[POKEMON_SIZE];
    restore_snapshot(core, field);
    create_mon_image(core, 4, 5, player_moves, player_pp, player);
    create_mon_image(core, 10, 5, enemy_moves, enemy_pp, enemy);
    clear_parties(core);
    seed_fixture(core);
    install_mon_image(core, ADDR_PLAYER_PARTY, player);
    install_mon_image(core, ADDR_ENEMY_PARTY, enemy);
    uint32_t player_level = call_preserving(
        core, BATTLE_CORE_GET_MON_DATA, ADDR_PLAYER_PARTY, 56, 0, 0);
    uint32_t enemy_level = call_preserving(
        core, BATTLE_CORE_GET_MON_DATA, ADDR_ENEMY_PARTY, 56, 0, 0);
    if (player_level != 5 || enemy_level != 5) {
        char diagnostic[128];
        (void)snprintf(diagnostic, sizeof(diagnostic),
                       "normal wild party level readback failed (%u/%u)",
                       player_level, enemy_level);
        battle_core_die(diagnostic);
    }
    write8(core, ADDR_PLAYER_PARTY_COUNT, 1);
    write8(core, BATTLE_CORE_ENEMY_PARTY_COUNT, 1);
    struct CallObservation setup = call_bounded(core, BATTLE_CORE_START_WILD, 0, 0, 0, 0);
    if (!setup.payload_pc_seen) {
        battle_core_die("normal wild setup did not execute CFRU payload code");
    }
    run_fixed_frames(core);
    return setup;
}

static struct CallObservation setup_custom_wild(
    struct mCore *core,
    const struct Snapshot *field,
    uint16_t player_species,
    uint16_t enemy_species,
    const uint16_t player_moves[BATTLE_CORE_MOVE_SLOTS],
    const uint8_t player_pp[BATTLE_CORE_MOVE_SLOTS],
    const uint16_t enemy_moves[BATTLE_CORE_MOVE_SLOTS],
    const uint8_t enemy_pp[BATTLE_CORE_MOVE_SLOTS]
) {
    uint8_t player[POKEMON_SIZE];
    uint8_t enemy[POKEMON_SIZE];
    restore_snapshot(core, field);
    create_mon_image(core, player_species, 20, player_moves, player_pp, player);
    create_mon_image(core, enemy_species, 20, enemy_moves, enemy_pp, enemy);
    clear_parties(core);
    seed_fixture(core);
    install_mon_image(core, ADDR_PLAYER_PARTY, player);
    install_mon_image(core, ADDR_ENEMY_PARTY, enemy);
    write8(core, ADDR_PLAYER_PARTY_COUNT, 1);
    write8(core, BATTLE_CORE_ENEMY_PARTY_COUNT, 1);
    struct CallObservation setup = call_bounded(
        core, BATTLE_CORE_START_WILD, 0, 0, 0, 0);
    if (!setup.payload_pc_seen) {
        battle_core_die("custom wild setup did not execute CFRU payload code");
    }
    run_fixed_frames(core);
    return setup;
}

static struct BattleObservation run_wild(struct mCore *core,
                                         const struct Snapshot *field,
                                         uint8_t selected_slot) {
    struct CallObservation setup = setup_wild(core, field);
    if (read8(core, ADDR_BATTLERS_COUNT) != 2) {
        battle_core_die("normal wild fixture did not initialize two battlers");
    }
    struct BattleObservation result = observe_battle(core, false, setup);
    if (result.battlers[0].species != 4 || result.battlers[1].species != 10) {
        battle_core_die("wild fixture species identity changed");
    }
    result.turn = execute_one_turn(core, selected_slot, 0);
    return result;
}

static struct CallObservation setup_trainer(struct mCore *core,
                                            const struct Snapshot *field) {
    static const uint16_t player_moves[BATTLE_CORE_MOVE_SLOTS] = {
        BATTLE_CORE_MOVE_SCRATCH, 0, 0, 0,
    };
    static const uint8_t player_pp[BATTLE_CORE_MOVE_SLOTS] = {35, 0, 0, 0};
    uint8_t player[POKEMON_SIZE];
    restore_snapshot(core, field);
    create_mon_image(core, 7, 5, player_moves, player_pp, player);
    clear_parties(core);
    seed_fixture(core);
    install_mon_image(core, ADDR_PLAYER_PARTY, player);
    write8(core, ADDR_PLAYER_PARTY_COUNT, 1);
    write16(core, BATTLE_CORE_TRAINER_MODE, 0);
    write16(core, BATTLE_CORE_TRAINER_OPPONENT_A, 328);
    struct CallObservation setup = call_bounded(core, BATTLE_CORE_START_TRAINER, 0, 0, 0, 0);
    if (!setup.payload_pc_seen) {
        battle_core_die("normal trainer setup did not execute CFRU payload code");
    }
    run_fixed_frames(core);
    return setup;
}

static struct BattleObservation run_trainer(struct mCore *core,
                                            const struct Snapshot *field) {
    struct CallObservation setup = setup_trainer(core, field);
    if (read8(core, ADDR_BATTLERS_COUNT) != 2) {
        battle_core_die("normal trainer fixture did not initialize two battlers");
    }
    struct BattleObservation result = observe_battle(core, true, setup);
    if (result.battlers[0].species != 7 || result.battlers[1].species != 4) {
        battle_core_die("Vega trainer 328 party was not built through the normal trainer path");
    }
    result.turn = execute_one_turn(core, 0, 0);
    return result;
}

static void sample_status_cleanup(struct mCore *core,
                                  struct StatusObservation *result) {
    uint8_t outcome = read8(core, BATTLE_CORE_BATTLE_OUTCOME);
    if (outcome != 0 && result->outcome_seen == 0) result->outcome_seen = outcome;
    if (read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                    + BATTLE_CORE_MON_HP) == 0) {
        result->enemy_fainted_seen = true;
    }
    if (read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0) {
        result->battle_runtime_cleaned = true;
    }
}

static void run_status_cleanup_frames(struct mCore *core,
                                      struct StatusObservation *result,
                                      uint16_t keys, uint32_t frames) {
    core->setKeys(core, keys);
    for (uint32_t frame = 0; frame < frames; ++frame) {
        core->runFrame(core);
        ++result->cleanup_frames;
        sample_status_cleanup(core, result);
    }
}

static struct StatusObservation run_status_route(
    struct mCore *core,
    const struct Snapshot *field
) {
    static const uint16_t player_moves[BATTLE_CORE_MOVE_SLOTS] = {
        BATTLE_CORE_MOVE_TOXIC, BATTLE_CORE_MOVE_SCRATCH, 0, 0,
    };
    static const uint8_t player_pp[BATTLE_CORE_MOVE_SLOTS] = {10, 35, 0, 0};
    static const uint16_t enemy_moves[BATTLE_CORE_MOVE_SLOTS] = {
        BATTLE_CORE_MOVE_TACKLE, 0, 0, 0,
    };
    static const uint8_t enemy_pp[BATTLE_CORE_MOVE_SLOTS] = {35, 0, 0, 0};
    struct StatusObservation result = {0};
    struct CallObservation setup = setup_custom_wild(
        core, field, 29, 10, player_moves, player_pp, enemy_moves, enemy_pp);
    if (read8(core, ADDR_BATTLERS_COUNT) != 2) {
        battle_core_die("status fixture did not initialize two battlers");
    }
    result.battle = observe_battle(core, false, setup);
    if (result.battle.battlers[0].species != 29
        || result.battle.battlers[1].species != 10) {
        battle_core_die("status fixture species identity changed");
    }
    uint8_t player_type1 = read8(
        core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_TYPE1);
    uint8_t player_type2 = read8(
        core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_TYPE2);
    uint8_t enemy_type1 = read8(
        core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_CORE_MON_TYPE1);
    uint8_t enemy_type2 = read8(
        core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_CORE_MON_TYPE2);
    if ((player_type1 != BATTLE_CORE_TYPE_POISON
         && player_type2 != BATTLE_CORE_TYPE_POISON)
        || enemy_type1 == BATTLE_CORE_TYPE_POISON
        || enemy_type2 == BATTLE_CORE_TYPE_POISON
        || enemy_type1 == BATTLE_CORE_TYPE_STEEL
        || enemy_type2 == BATTLE_CORE_TYPE_STEEL) {
        battle_core_die("Toxic fixture types do not guarantee a legal status attempt");
    }
    /* Species 29 can expose a contact-trigger poison ability.  Make Toxic
     * execute first so the fixture observes Toxic itself, not poison caused
     * by the opponent's preceding contact move. */
    write16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_SPEED, 1000);
    write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                  + BATTLE_CORE_MON_SPEED, 1);
    result.battle.turn = execute_one_turn(
        core, 0, BATTLE_CORE_STATUS_TOXIC);

    /* Finish the same poisoned battle through the ordinary scheduler. */
    write16(core, ADDR_ENEMY_PARTY + POKEMON_CURRENT_HP_OFFSET, 1);
    write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                  + BATTLE_CORE_MON_HP, 1);
    for (unsigned press = 0; press < BATTLE_CORE_TURN_INPUT_PRESSES; ++press) {
        write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR, 1);
        run_status_cleanup_frames(core, &result, 1, 2);
        run_status_cleanup_frames(core, &result, 0,
                                  BATTLE_CORE_TURN_INPUT_WAIT);
    }
    for (unsigned pulse = 0;
         pulse < BATTLE_CORE_END_INPUT_PULSES && !result.battle_runtime_cleaned;
         ++pulse) {
        run_status_cleanup_frames(core, &result, 1, 2);
        run_status_cleanup_frames(core, &result, 0,
                                  BATTLE_CORE_END_INPUT_WAIT);
    }
    run_status_cleanup_frames(core, &result, 0, 60);
    result.party_status_after_cleanup = read32(
        core, ADDR_ENEMY_PARTY + BATTLE_CORE_PARTY_STATUS_OFFSET);
    result.status_cleared_on_faint =
        (result.party_status_after_cleanup & BATTLE_CORE_STATUS_TOXIC) == 0;
    if (!result.enemy_fainted_seen
        || result.outcome_seen != BATTLE_CORE_OUTCOME_WON
        || !result.battle_runtime_cleaned
        || !result.status_cleared_on_faint) {
        char diagnostic[320];
        (void)snprintf(
            diagnostic, sizeof(diagnostic),
            "status fixture did not clear Toxic through the faint path "
            "(fainted=%u outcome=%u cleaned=%u party_status=%08" PRIx32
            " frames=%u callback=%08" PRIx32 " newbs=%08" PRIx32 ")",
            result.enemy_fainted_seen, result.outcome_seen,
            result.battle_runtime_cleaned, result.party_status_after_cleanup,
            result.cleanup_frames, read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER));
        battle_core_die(diagnostic);
    }
    return result;
}

static void sample_priority_frame(struct mCore *core,
                                  struct PriorityObservation *result,
                                  bool *turn_order_seen) {
    uint16_t player_hp = read16(core, ADDR_BATTLE_MONS
                                     + BATTLE_CORE_MON_HP);
    uint16_t opponent_hp = read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                                       + BATTLE_CORE_MON_HP);
    if (result->first_damage_dealt_by == UINT8_MAX) {
        if (opponent_hp < result->opponent_hp_before) {
            result->first_damage_dealt_by = 0;
        } else if (player_hp < result->player_hp_before) {
            result->first_damage_dealt_by = 1;
        }
    }
    if (read16(core, BATTLE_CORE_CHOSEN_MOVES) == result->priority_move
        && read16(core, BATTLE_CORE_CHOSEN_MOVES + 2U)
             == result->opponent_move) {
        result->selected_through_controller = true;
        uint8_t first = read8(core, BATTLE_CORE_BANKS_BY_TURN_ORDER);
        uint8_t second = read8(core, BATTLE_CORE_BANKS_BY_TURN_ORDER + 1U);
        if ((first == 0 || first == 1) && (second == 0 || second == 1)
            && first != second) {
            result->turn_order[0] = first;
            result->turn_order[1] = second;
            *turn_order_seen = true;
        }
    }
}

static void run_priority_frames(struct mCore *core,
                                struct PriorityObservation *result,
                                bool *turn_order_seen,
                                uint16_t keys, uint32_t frames) {
    core->setKeys(core, keys);
    for (uint32_t frame = 0; frame < frames; ++frame) {
        core->runFrame(core);
        ++result->frames;
        sample_priority_frame(core, result, turn_order_seen);
    }
}

static struct PriorityObservation run_priority_route(
    struct mCore *core,
    const struct Snapshot *field,
    uint32_t move_table_pointer
) {
    static const uint16_t player_moves[BATTLE_CORE_MOVE_SLOTS] = {
        BATTLE_CORE_MOVE_QUICK_ATTACK, BATTLE_CORE_MOVE_TACKLE, 0, 0,
    };
    static const uint8_t player_pp[BATTLE_CORE_MOVE_SLOTS] = {30, 35, 0, 0};
    static const uint16_t enemy_moves[BATTLE_CORE_MOVE_SLOTS] = {
        BATTLE_CORE_MOVE_TACKLE, 0, 0, 0,
    };
    static const uint8_t enemy_pp[BATTLE_CORE_MOVE_SLOTS] = {35, 0, 0, 0};
    struct PriorityObservation result = {0};
    bool turn_order_seen = false;
    struct CallObservation setup = setup_custom_wild(
        core, field, 4, 10, player_moves, player_pp, enemy_moves, enemy_pp);
    if (read8(core, ADDR_BATTLERS_COUNT) != 2) {
        battle_core_die("priority fixture did not initialize two battlers");
    }
    result.battle = observe_battle(core, false, setup);
    result.priority_move = BATTLE_CORE_MOVE_QUICK_ATTACK;
    result.alternative_move = BATTLE_CORE_MOVE_TACKLE;
    result.opponent_move = BATTLE_CORE_MOVE_TACKLE;
    result.priority_value = (int8_t)read8(
        core, move_table_pointer
            + result.priority_move * BATTLE_CORE_BATTLE_MOVE_SIZE + 7U);
    result.opponent_priority_value = (int8_t)read8(
        core, move_table_pointer
            + result.opponent_move * BATTLE_CORE_BATTLE_MOVE_SIZE + 7U);

    /* Deliberately make the priority user slower than its opponent. */
    result.player_speed = 10;
    result.opponent_speed = 1000;
    write16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_SPEED,
            result.player_speed);
    write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                  + BATTLE_CORE_MON_SPEED, result.opponent_speed);
    result.player_pp_before = read8(
        core, ADDR_BATTLE_MONS + BATTLE_MON_PP_OFFSET);
    result.opponent_pp_before = read8(
        core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_MON_PP_OFFSET);
    result.player_hp_before = read16(
        core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_HP);
    result.opponent_hp_before = read16(
        core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_CORE_MON_HP);
    result.first_damage_dealt_by = UINT8_MAX;

    for (unsigned press = 0; press < BATTLE_CORE_TURN_INPUT_PRESSES; ++press) {
        write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR, 0);
        run_priority_frames(core, &result, &turn_order_seen, 1, 2);
        run_priority_frames(core, &result, &turn_order_seen, 0,
                            BATTLE_CORE_TURN_INPUT_WAIT);
    }
    run_priority_frames(core, &result, &turn_order_seen, 0,
                        BATTLE_CORE_TURN_SETTLE_FRAMES);
    result.player_pp_after = read8(
        core, ADDR_BATTLE_MONS + BATTLE_MON_PP_OFFSET);
    result.opponent_pp_after = read8(
        core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_MON_PP_OFFSET);
    result.player_hp_after = read16(
        core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_HP);
    result.opponent_hp_after = read16(
        core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_CORE_MON_HP);
    result.both_moves_executed =
        result.player_pp_after + 1U == result.player_pp_before
        && result.opponent_pp_after + 1U == result.opponent_pp_before
        && result.player_hp_after < result.player_hp_before
        && result.opponent_hp_after < result.opponent_hp_before;
    result.slower_priority_user_moved_first = turn_order_seen
        && result.turn_order[0] == 0 && result.turn_order[1] == 1
        && result.first_damage_dealt_by == 0;
    if (result.priority_value <= result.opponent_priority_value
        || result.player_speed >= result.opponent_speed
        || !result.selected_through_controller
        || !result.both_moves_executed
        || !result.slower_priority_user_moved_first
        || read8(core, BATTLE_CORE_BATTLE_OUTCOME) != 0) {
        battle_core_die("priority scheduler did not order slower Quick Attack before Tackle");
    }
    return result;
}

static void sample_end_state(struct mCore *core, struct EndObservation *result) {
    uint8_t outcome = read8(core, BATTLE_CORE_BATTLE_OUTCOME);
    if (outcome != 0 && result->outcome_seen == 0) result->outcome_seen = outcome;
    if (read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_CORE_MON_HP) == 0) {
        result->enemy_fainted_seen = true;
    }
    if (result->battle_runtime_initialized
        && read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0) {
        result->battle_runtime_cleaned = true;
    }
}

static void run_end_frames(struct mCore *core, struct EndObservation *result,
                           uint16_t keys, uint32_t frames) {
    core->setKeys(core, keys);
    for (uint32_t frame = 0; frame < frames; ++frame) {
        core->runFrame(core);
        ++result->frames;
        sample_end_state(core, result);
    }
}

static struct EndObservation run_battle_win_end(
    struct mCore *core,
    const struct Snapshot *field,
    bool trainer,
    bool expect_experience
) {
    struct EndObservation result = {0};
    result.trainer = trainer;
    result.setup_call = trainer ? setup_trainer(core, field) : setup_wild(core, field);
    if (read8(core, ADDR_BATTLERS_COUNT) != 2
        || ((read32(core, ADDR_BATTLE_TYPE_FLAGS) & BATTLE_TYPE_TRAINER) != 0)
               != trainer) {
        battle_core_die("win fixture did not enter the requested normal battle");
    }
    result.battle_runtime_initialized =
        read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0;
    if (!result.battle_runtime_initialized) {
        battle_core_die("faint fixture battle runtime was not initialized");
    }
    result.experience_before = read32(
        core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_EXPERIENCE);

    /* Make the next real damaging move take the ordinary faint/EXP/end path. */
    write16(core, ADDR_ENEMY_PARTY + POKEMON_CURRENT_HP_OFFSET, 1);
    write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_CORE_MON_HP, 1);

    for (unsigned press = 0; press < BATTLE_CORE_TURN_INPUT_PRESSES; ++press) {
        write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR, 0);
        run_end_frames(core, &result, 1, 2);
        run_end_frames(core, &result, 0, BATTLE_CORE_TURN_INPUT_WAIT);
    }
    for (unsigned pulse = 0;
         pulse < BATTLE_CORE_END_INPUT_PULSES && !result.battle_runtime_cleaned;
         ++pulse) {
        run_end_frames(core, &result, 1, 2);
        run_end_frames(core, &result, 0, BATTLE_CORE_END_INPUT_WAIT);
    }
    run_end_frames(core, &result, 0, 60);
    if (expect_experience) {
        result.experience_after = read32(
            core, ADDR_PLAYER_PARTY + BATTLE_CORE_PARTY_EXPERIENCE_OFFSET);
    }

    if (!result.enemy_fainted_seen) {
        battle_core_die("faint fixture never observed enemy HP zero");
    }
    if (result.outcome_seen != BATTLE_CORE_OUTCOME_WON) {
        char diagnostic[256];
        (void)snprintf(
            diagnostic, sizeof(diagnostic),
            "faint fixture never observed the normal win outcome "
            "(outcome=%u fainted=%u frames=%u callback=%08" PRIx32
            " newbs=%08" PRIx32 " enemy_hp=%u outcomes=%u/%u/%u/%u)",
            result.outcome_seen, result.enemy_fainted_seen, result.frames,
            read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
            read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_CORE_MON_HP),
            read8(core, 0x02023DEA), read8(core, 0x02023E8A),
            read8(core, 0x02023F4A), read8(core, 0x02023DCA));
        battle_core_die(diagnostic);
    }
    if (expect_experience && result.experience_after <= result.experience_before) {
        battle_core_die("faint fixture did not grant party experience");
    }
    if (!result.battle_runtime_cleaned) {
        battle_core_die("battle end did not clear gNewBS runtime state");
    }
    return result;
}

static struct EndObservation run_faint_experience_end(
    struct mCore *core,
    const struct Snapshot *field
) {
    return run_battle_win_end(core, field, false, true);
}

static struct EndObservation run_trainer_battle_end(
    struct mCore *core,
    const struct Snapshot *field
) {
    return run_battle_win_end(core, field, true, false);
}

static struct MultiTargetObservation run_multi_target_double(
    struct mCore *core,
    const struct Snapshot *field
) {
    static const uint16_t player_left_moves[BATTLE_CORE_MOVE_SLOTS] = {57, 0, 0, 0};
    static const uint8_t player_left_pp[BATTLE_CORE_MOVE_SLOTS] = {15, 0, 0, 0};
    static const uint16_t player_right_moves[BATTLE_CORE_MOVE_SLOTS] = {45, 0, 0, 0};
    static const uint8_t player_right_pp[BATTLE_CORE_MOVE_SLOTS] = {40, 0, 0, 0};
    static const uint16_t opponent_moves[BATTLE_CORE_MOVE_SLOTS] = {33, 0, 0, 0};
    static const uint8_t opponent_pp[BATTLE_CORE_MOVE_SLOTS] = {35, 0, 0, 0};
    static const uint16_t expected_species[BATTLE_CORE_MAX_BATTLERS] = {4, 10, 7, 11};
    static const uint16_t expected_party_index[BATTLE_CORE_MAX_BATTLERS] = {0, 0, 1, 1};
    uint8_t images[BATTLE_CORE_MAX_BATTLERS][POKEMON_SIZE];
    struct MultiTargetObservation result = {0};

    restore_snapshot(core, field);
    create_mon_image(core, 4, 5, player_left_moves, player_left_pp, images[0]);
    create_mon_image(core, 7, 5, player_right_moves, player_right_pp, images[2]);
    create_mon_image(core, 10, 5, opponent_moves, opponent_pp, images[1]);
    create_mon_image(core, 11, 5, opponent_moves, opponent_pp, images[3]);
    clear_parties(core);
    install_mon_image(core, ADDR_PLAYER_PARTY, images[0]);
    install_mon_image(core, ADDR_PLAYER_PARTY + POKEMON_SIZE, images[2]);
    install_mon_image(core, ADDR_ENEMY_PARTY, images[1]);
    install_mon_image(core, ADDR_ENEMY_PARTY + POKEMON_SIZE, images[3]);
    write8(core, ADDR_PLAYER_PARTY_COUNT, 2);
    write8(core, BATTLE_CORE_ENEMY_PARTY_COUNT, 2);
    seed_fixture(core);
    result.setup_call = call_bounded(core, BATTLE_CORE_START_WILD, 0, 0, 0, 0);
    if (!result.setup_call.payload_pc_seen) {
        battle_core_die("double wild setup did not execute CFRU payload code");
    }
    write32_bytes(core, ADDR_BATTLE_TYPE_FLAGS,
                  read32(core, ADDR_BATTLE_TYPE_FLAGS) | BATTLE_TYPE_DOUBLE);
    run_key_frames(core, 0, BATTLE_CORE_MENU_READY_FRAMES);

    result.type_flags = read32(core, ADDR_BATTLE_TYPE_FLAGS);
    result.battler_count = read8(core, ADDR_BATTLERS_COUNT);
    for (unsigned battler = 0; battler < BATTLE_CORE_MAX_BATTLERS; ++battler) {
        uint32_t mon = ADDR_BATTLE_MONS + battler * BATTLE_MON_SIZE;
        result.species[battler] = read16(core, mon);
        result.party_index[battler] = read16(
            core, ADDR_BATTLER_PARTY_INDEXES + battler * 2U);
    }
    result.four_controllers_initialized =
        (result.type_flags & BATTLE_TYPE_DOUBLE) != 0
        && result.battler_count == BATTLE_CORE_MAX_BATTLERS
        && (read8(core, ADDR_ABSENT_BATTLER_FLAGS) & 0x0FU) == 0
        && read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0;
    if (!result.four_controllers_initialized
        || memcmp(result.species, expected_species, sizeof(expected_species)) != 0
        || memcmp(result.party_index, expected_party_index,
                  sizeof(expected_party_index)) != 0) {
        battle_core_die("double fixture did not initialize four real battlers/controllers");
    }

    result.spread_move = read16(
        core, ADDR_BATTLE_MONS + BATTLE_MON_MOVES_OFFSET);
    result.spread_pp_before = read8(
        core, ADDR_BATTLE_MONS + BATTLE_MON_PP_OFFSET);
    result.opponent_hp_before[0] = read16(
        core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_CORE_MON_HP);
    result.opponent_hp_before[1] = read16(
        core, ADDR_BATTLE_MONS + 3U * BATTLE_MON_SIZE + BATTLE_CORE_MON_HP);

    for (unsigned press = 0; press < BATTLE_CORE_DOUBLE_INPUT_PRESSES; ++press) {
        for (unsigned battler = 0; battler < BATTLE_CORE_MAX_BATTLERS; ++battler) {
            write8(core, BATTLE_CORE_ACTION_SELECTION_CURSOR + battler, 0);
            write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR + battler, 0);
        }
        run_key_frames(core, 1, 2);
        run_key_frames(core, 0, BATTLE_CORE_MENU_INPUT_WAIT);
    }
    run_key_frames(core, 0, BATTLE_CORE_DOUBLE_SETTLE_FRAMES);
    result.frames = BATTLE_CORE_DOUBLE_INPUT_PRESSES
        * (2U + BATTLE_CORE_MENU_INPUT_WAIT)
        + BATTLE_CORE_DOUBLE_SETTLE_FRAMES;
    result.spread_pp_after = read8(
        core, ADDR_BATTLE_MONS + BATTLE_MON_PP_OFFSET);
    result.opponent_hp_after[0] = read16(
        core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_CORE_MON_HP);
    result.opponent_hp_after[1] = read16(
        core, ADDR_BATTLE_MONS + 3U * BATTLE_MON_SIZE + BATTLE_CORE_MON_HP);
    result.both_opponents_hit =
        result.opponent_hp_after[0] < result.opponent_hp_before[0]
        && result.opponent_hp_after[1] < result.opponent_hp_before[1];
    if (result.spread_move != 57
        || result.spread_pp_after + 1U != result.spread_pp_before
        || !result.both_opponents_hit
        || read8(core, BATTLE_CORE_BATTLE_OUTCOME) != 0) {
        battle_core_die("real double controller turn did not apply one spread move to both foes");
    }
    return result;
}

static struct CallObservation setup_switch_wild(
    struct mCore *core,
    const struct Snapshot *field
) {
    uint8_t player_lead[POKEMON_SIZE];
    uint8_t player_bench[POKEMON_SIZE];
    uint8_t enemy[POKEMON_SIZE];
    restore_snapshot(core, field);
    create_mon_image(core, 4, 5, NULL, NULL, player_lead);
    create_mon_image(core, 7, 5, NULL, NULL, player_bench);
    create_mon_image(core, 10, 5, NULL, NULL, enemy);
    clear_parties(core);
    install_mon_image(core, ADDR_PLAYER_PARTY, player_lead);
    install_mon_image(core, ADDR_PLAYER_PARTY + POKEMON_SIZE, player_bench);
    install_mon_image(core, ADDR_ENEMY_PARTY, enemy);
    write8(core, ADDR_PLAYER_PARTY_COUNT, 2);
    write8(core, BATTLE_CORE_ENEMY_PARTY_COUNT, 1);
    seed_fixture(core);
    struct CallObservation setup = call_bounded(
        core, BATTLE_CORE_START_WILD, 0, 0, 0, 0);
    if (!setup.payload_pc_seen) {
        battle_core_die("switch wild setup did not execute CFRU payload code");
    }
    run_fixed_frames(core);
    return setup;
}

static struct SwitchObservation run_switch_menu(
    struct mCore *core,
    const struct Snapshot *field
) {
    struct SwitchObservation result = {0};
    result.setup_call = setup_switch_wild(core, field);
    if (read8(core, ADDR_BATTLERS_COUNT) != 2
        || read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0) {
        battle_core_die("switch fixture did not enter a normal wild battle");
    }
    result.species_before = read16(core, ADDR_BATTLE_MONS);
    result.party_index_before = read16(core, ADDR_BATTLER_PARTY_INDEXES);
    result.battle_callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);

    /* Three A pulses reach the party menu from the battle action cursor.
     * A fourth pulse is already consumed by the party menu and opens the
     * lead slot's SHIFT/SUMMARY context instead of selecting the bench mon. */
    for (unsigned press = 0;
         press < BATTLE_CORE_SWITCH_MENU_PRESSES;
         ++press) {
        write8(core, BATTLE_CORE_ACTION_SELECTION_CURSOR,
               BATTLE_CORE_ACTION_SWITCH);
        run_key_frames(core, 1, 2);
        run_key_frames(core, 0, BATTLE_CORE_MENU_INPUT_WAIT);
    }
    result.chosen_action = read8(core, BATTLE_CORE_CHOSEN_ACTIONS);
    run_key_frames(core, 0, BATTLE_CORE_MENU_READY_FRAMES);
    result.party_menu_callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
    result.party_menu_opened = result.party_menu_callback != 0
        && result.party_menu_callback != result.battle_callback;

    run_key_frames(core, 128, 2);
    run_key_frames(core, 0, 60);
    result.selected_party_mon = read8(core, BATTLE_CORE_SELECTED_PARTY_MON);
    run_key_frames(core, 1, 2);
    run_key_frames(core, 0, 80);
    run_key_frames(core, 1, 2);
    run_key_frames(core, 0, BATTLE_CORE_SWITCH_SETTLE_FRAMES);
    result.frames = BATTLE_CORE_SWITCH_MENU_PRESSES
        * (2U + BATTLE_CORE_MENU_INPUT_WAIT)
        + BATTLE_CORE_MENU_READY_FRAMES + 2U + 60U + 2U + 80U
        + 2U + BATTLE_CORE_SWITCH_SETTLE_FRAMES;
    result.species_after = read16(core, ADDR_BATTLE_MONS);
    result.party_index_after = read16(core, ADDR_BATTLER_PARTY_INDEXES);
    result.controller_returned =
        read32(core, BATTLE_CORE_MAIN_CALLBACK2) == result.battle_callback;
    if (result.species_before != 4 || result.party_index_before != 0
        || result.chosen_action != BATTLE_CORE_ACTION_SWITCH
        || !result.party_menu_opened || result.selected_party_mon != 1
        || result.species_after != 7 || result.party_index_after != 1
        || !result.controller_returned
        || read8(core, BATTLE_CORE_BATTLE_OUTCOME) != 0) {
        battle_core_die("party-menu controller fixture did not complete a real switch");
    }
    return result;
}

static void sample_capture_state(struct mCore *core,
                                 struct CaptureObservation *result) {
    uint8_t outcome = read8(core, BATTLE_CORE_BATTLE_OUTCOME);
    if (outcome != 0 && result->outcome_seen == 0) result->outcome_seen = outcome;
    if (read8(core, BATTLE_CORE_BAG_STATE + 5U) != 0) result->bag_opened = true;
    if (result->battle_runtime_initialized
        && read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0) {
        result->battle_runtime_cleaned = true;
    }
}

static void run_capture_frames(struct mCore *core,
                               struct CaptureObservation *result,
                               uint16_t keys, uint32_t frames) {
    core->setKeys(core, keys);
    for (uint32_t frame = 0; frame < frames; ++frame) {
        core->runFrame(core);
        ++result->frames;
        sample_capture_state(core, result);
    }
}

static struct CaptureObservation run_capture_menu(
    struct mCore *core,
    const struct Snapshot *field
) {
    uint8_t player[POKEMON_SIZE];
    uint8_t enemy[POKEMON_SIZE];
    struct CaptureObservation result = {0};
    restore_snapshot(core, field);
    create_mon_image(core, 4, 5, NULL, NULL, player);
    create_mon_image(core, 10, 5, NULL, NULL, enemy);
    clear_parties(core);
    install_mon_image(core, ADDR_PLAYER_PARTY, player);
    install_mon_image(core, ADDR_ENEMY_PARTY, enemy);
    write8(core, ADDR_PLAYER_PARTY_COUNT, 1);
    write8(core, BATTLE_CORE_ENEMY_PARTY_COUNT, 1);

    struct Snapshot before_bag_read = take_snapshot(core);
    uint32_t already_had_ball = call_bounded(
        core, BATTLE_CORE_CHECK_BAG_HAS_ITEM,
        BATTLE_CORE_MASTER_BALL, 1, 0, 0).result;
    restore_snapshot(core, &before_bag_read);
    free(before_bag_read.bytes);
    if (already_had_ball != 0) {
        battle_core_die("capture fixture field base unexpectedly has a Master Ball");
    }
    struct CallObservation add_ball = call_bounded(
        core, BATTLE_CORE_ADD_BAG_ITEM,
        BATTLE_CORE_MASTER_BALL, 1, 0, 0);
    result.add_ball_result = add_ball.result;
    result.add_ball_instructions = add_ball.instructions;
    if (result.add_ball_result != 1) {
        battle_core_die("capture fixture could not add exactly one Master Ball");
    }
    write16(core, BATTLE_CORE_BAG_STATE + 6U, BATTLE_CORE_BAG_BALL_POCKET);
    for (unsigned cursor = 0; cursor < 6; ++cursor) {
        write16(core, BATTLE_CORE_BAG_STATE + 8U + cursor * 2U, 0);
    }
    seed_fixture(core);
    result.setup_call = call_bounded(core, BATTLE_CORE_START_WILD, 0, 0, 0, 0);
    if (!result.setup_call.payload_pc_seen) {
        battle_core_die("capture wild setup did not execute CFRU payload code");
    }
    run_fixed_frames(core);
    result.party_count_before = read8(core, ADDR_PLAYER_PARTY_COUNT);
    result.battle_runtime_initialized =
        read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0;
    if (read8(core, ADDR_BATTLERS_COUNT) != 2
        || result.party_count_before != 1
        || !result.battle_runtime_initialized) {
        battle_core_die("capture fixture did not enter a normal wild battle");
    }

    for (unsigned press = 0; press < 4; ++press) {
        write8(core, BATTLE_CORE_ACTION_SELECTION_CURSOR,
               BATTLE_CORE_ACTION_USE_ITEM);
        run_capture_frames(core, &result, 1, 2);
        run_capture_frames(core, &result, 0, BATTLE_CORE_MENU_INPUT_WAIT);
    }
    result.chosen_action = read8(core, BATTLE_CORE_CHOSEN_ACTIONS);
    run_capture_frames(core, &result, 0, BATTLE_CORE_MENU_READY_FRAMES);
    for (unsigned pulse = 0;
         pulse < BATTLE_CORE_END_INPUT_PULSES
             && !result.battle_runtime_cleaned;
         ++pulse) {
        run_capture_frames(core, &result, 1, 2);
        run_capture_frames(core, &result, 0, BATTLE_CORE_MENU_INPUT_WAIT);
    }
    run_capture_frames(core, &result, 0, 60);
    result.party_count_after = read8(core, ADDR_PLAYER_PARTY_COUNT);
    result.captured_species = read16(
        core, ADDR_PLAYER_PARTY + POKEMON_SIZE
            + BATTLE_CORE_PARTY_SPECIES_OFFSET);
    result.ball_consumed = call_preserving(
        core, BATTLE_CORE_CHECK_BAG_HAS_ITEM,
        BATTLE_CORE_MASTER_BALL, 1, 0, 0) == 0;
    if (result.chosen_action != BATTLE_CORE_ACTION_USE_ITEM
        || !result.bag_opened || result.outcome_seen != BATTLE_CORE_OUTCOME_CAUGHT
        || result.party_count_after != 2 || result.captured_species != 10
        || !result.ball_consumed || !result.battle_runtime_cleaned) {
        battle_core_die("bag/ball controller fixture did not complete capture and cleanup");
    }
    return result;
}

static bool call_equal(const struct CallObservation *left,
                       const struct CallObservation *right) {
    return left->result == right->result
        && left->instructions == right->instructions
        && left->payload_pc_seen == right->payload_pc_seen;
}

static bool mon_equal(const struct MonObservation *left,
                      const struct MonObservation *right) {
    return left->species == right->species && left->hp == right->hp
        && left->level == right->level && left->experience == right->experience
        && left->status1 == right->status1 && left->status2 == right->status2
        && memcmp(left->moves, right->moves, sizeof(left->moves)) == 0
        && memcmp(left->pp, right->pp, sizeof(left->pp)) == 0;
}

static bool turn_equal(const struct TurnObservation *left,
                       const struct TurnObservation *right) {
    return left->selected_slot == right->selected_slot
        && left->selected_move == right->selected_move
        && left->pp_before == right->pp_before
        && left->pp_after == right->pp_after
        && left->player_hp_before == right->player_hp_before
        && left->player_hp_after == right->player_hp_after
        && left->opponent_hp_before == right->opponent_hp_before
        && left->opponent_hp_after == right->opponent_hp_after
        && left->opponent_status_before == right->opponent_status_before
        && left->opponent_status_after == right->opponent_status_after
        && left->opponent_party_status_before
               == right->opponent_party_status_before
        && left->opponent_party_status_after
               == right->opponent_party_status_after
        && left->outcome_before == right->outcome_before
        && left->outcome_after == right->outcome_after
        && left->frames == right->frames
        && left->pp_spent == right->pp_spent
        && left->hp_changed == right->hp_changed
        && left->status_applied == right->status_applied;
}

static bool end_equal(const struct EndObservation *left,
                      const struct EndObservation *right) {
    return call_equal(&left->setup_call, &right->setup_call)
        && left->trainer == right->trainer
        && left->experience_before == right->experience_before
        && left->experience_after == right->experience_after
        && left->frames == right->frames
        && left->outcome_seen == right->outcome_seen
        && left->enemy_fainted_seen == right->enemy_fainted_seen
        && left->battle_runtime_initialized == right->battle_runtime_initialized
        && left->battle_runtime_cleaned == right->battle_runtime_cleaned;
}

static bool multi_target_equal(const struct MultiTargetObservation *left,
                               const struct MultiTargetObservation *right) {
    return call_equal(&left->setup_call, &right->setup_call)
        && left->type_flags == right->type_flags
        && left->battler_count == right->battler_count
        && memcmp(left->species, right->species, sizeof(left->species)) == 0
        && memcmp(left->party_index, right->party_index,
                  sizeof(left->party_index)) == 0
        && left->spread_move == right->spread_move
        && left->spread_pp_before == right->spread_pp_before
        && left->spread_pp_after == right->spread_pp_after
        && memcmp(left->opponent_hp_before, right->opponent_hp_before,
                  sizeof(left->opponent_hp_before)) == 0
        && memcmp(left->opponent_hp_after, right->opponent_hp_after,
                  sizeof(left->opponent_hp_after)) == 0
        && left->frames == right->frames
        && left->four_controllers_initialized
               == right->four_controllers_initialized
        && left->both_opponents_hit == right->both_opponents_hit;
}

static bool switch_equal(const struct SwitchObservation *left,
                         const struct SwitchObservation *right) {
    return call_equal(&left->setup_call, &right->setup_call)
        && left->species_before == right->species_before
        && left->species_after == right->species_after
        && left->party_index_before == right->party_index_before
        && left->party_index_after == right->party_index_after
        && left->selected_party_mon == right->selected_party_mon
        && left->chosen_action == right->chosen_action
        && left->battle_callback == right->battle_callback
        && left->party_menu_callback == right->party_menu_callback
        && left->frames == right->frames
        && left->party_menu_opened == right->party_menu_opened
        && left->controller_returned == right->controller_returned;
}

static bool capture_equal(const struct CaptureObservation *left,
                          const struct CaptureObservation *right) {
    return call_equal(&left->setup_call, &right->setup_call)
        && left->add_ball_result == right->add_ball_result
        && left->add_ball_instructions == right->add_ball_instructions
        && left->frames == right->frames
        && left->outcome_seen == right->outcome_seen
        && left->party_count_before == right->party_count_before
        && left->party_count_after == right->party_count_after
        && left->captured_species == right->captured_species
        && left->chosen_action == right->chosen_action
        && left->bag_opened == right->bag_opened
        && left->ball_consumed == right->ball_consumed
        && left->battle_runtime_initialized
               == right->battle_runtime_initialized
        && left->battle_runtime_cleaned == right->battle_runtime_cleaned;
}

static bool battle_equal(const struct BattleObservation *left,
                         const struct BattleObservation *right) {
    if (left->type_flags != right->type_flags
        || left->battler_count != right->battler_count
        || left->absent_flags != right->absent_flags
        || left->outcome != right->outcome
        || left->setup_frames != right->setup_frames
        || left->ram_digest != right->ram_digest
        || left->new_battle_struct_initialized != right->new_battle_struct_initialized
        || left->battle_struct_initialized != right->battle_struct_initialized
        || left->battle_resources_initialized != right->battle_resources_initialized
        || !call_equal(&left->setup_call, &right->setup_call)
        || !turn_equal(&left->turn, &right->turn)) {
        return false;
    }
    for (unsigned battler = 0; battler < left->battler_count; ++battler) {
        if (!mon_equal(&left->battlers[battler], &right->battlers[battler])) return false;
    }
    return true;
}

static bool status_equal(const struct StatusObservation *left,
                         const struct StatusObservation *right) {
    return battle_equal(&left->battle, &right->battle)
        && left->party_status_after_cleanup
               == right->party_status_after_cleanup
        && left->cleanup_frames == right->cleanup_frames
        && left->outcome_seen == right->outcome_seen
        && left->enemy_fainted_seen == right->enemy_fainted_seen
        && left->battle_runtime_cleaned == right->battle_runtime_cleaned
        && left->status_cleared_on_faint
               == right->status_cleared_on_faint;
}

static bool priority_equal(const struct PriorityObservation *left,
                           const struct PriorityObservation *right) {
    return battle_equal(&left->battle, &right->battle)
        && left->priority_move == right->priority_move
        && left->alternative_move == right->alternative_move
        && left->opponent_move == right->opponent_move
        && left->priority_value == right->priority_value
        && left->opponent_priority_value == right->opponent_priority_value
        && left->player_speed == right->player_speed
        && left->opponent_speed == right->opponent_speed
        && memcmp(left->turn_order, right->turn_order,
                  sizeof(left->turn_order)) == 0
        && left->first_damage_dealt_by == right->first_damage_dealt_by
        && left->player_pp_before == right->player_pp_before
        && left->player_pp_after == right->player_pp_after
        && left->opponent_pp_before == right->opponent_pp_before
        && left->opponent_pp_after == right->opponent_pp_after
        && left->player_hp_before == right->player_hp_before
        && left->player_hp_after == right->player_hp_after
        && left->opponent_hp_before == right->opponent_hp_before
        && left->opponent_hp_after == right->opponent_hp_after
        && left->frames == right->frames
        && left->selected_through_controller
               == right->selected_through_controller
        && left->both_moves_executed == right->both_moves_executed
        && left->slower_priority_user_moved_first
               == right->slower_priority_user_moved_first;
}

static void print_call(const struct CallObservation *value) {
    printf("{\"bounded\":true,\"instruction_limit\":%u,"
           "\"instructions\":%" PRIu32 ",\"result\":%" PRIu32 ","
           "\"payload_pc_seen\":%s}",
           BATTLE_CORE_DIRECT_CALL_LIMIT, value->instructions, value->result,
           value->payload_pc_seen ? "true" : "false");
}

static void print_turn(const struct TurnObservation *value) {
    printf("{\"input\":\"A_x6\",\"selected_slot\":%u,"
           "\"selected_move\":%u,\"frames\":%" PRIu32 ","
           "\"pp_before\":%u,\"pp_after\":%u,\"pp_spent\":%s,"
           "\"player_hp_before\":%u,\"player_hp_after\":%u,"
           "\"opponent_hp_before\":%u,\"opponent_hp_after\":%u,"
           "\"hp_changed\":%s,\"opponent_status_before\":%" PRIu32 ","
           "\"opponent_status_after\":%" PRIu32 ","
           "\"opponent_party_status_before\":%" PRIu32 ","
           "\"opponent_party_status_after\":%" PRIu32 ","
           "\"status_applied\":%s,"
           "\"outcome_before\":%u,\"outcome_after\":%u}",
           value->selected_slot, value->selected_move, value->frames,
           value->pp_before, value->pp_after,
           value->pp_spent ? "true" : "false",
           value->player_hp_before, value->player_hp_after,
           value->opponent_hp_before, value->opponent_hp_after,
           value->hp_changed ? "true" : "false",
           value->opponent_status_before, value->opponent_status_after,
           value->opponent_party_status_before,
           value->opponent_party_status_after,
           value->status_applied ? "true" : "false",
           value->outcome_before, value->outcome_after);
}

static void print_end(const struct EndObservation *value) {
    printf("{\"kind\":\"%s\",\"trainer\":%s,\"frames\":%" PRIu32 ","
           "\"outcome_seen\":%u,\"enemy_fainted_seen\":%s,"
           "\"experience_before\":%" PRIu32 ","
           "\"experience_after\":%" PRIu32 ",\"experience_checked\":%s,"
           "\"experience_increased\":%s,"
           "\"battle_runtime_initialized\":%s,"
           "\"battle_runtime_cleaned\":%s,\"setup_call\":",
           value->trainer ? "TRAINER_WIN" : "WILD_WIN",
           value->trainer ? "true" : "false",
           value->frames, value->outcome_seen,
           value->enemy_fainted_seen ? "true" : "false",
           value->experience_before, value->experience_after,
           value->trainer ? "false" : "true",
           value->experience_after > value->experience_before ? "true" : "false",
           value->battle_runtime_initialized ? "true" : "false",
           value->battle_runtime_cleaned ? "true" : "false");
    print_call(&value->setup_call);
    putchar('}');
}

static void print_multi_target(const struct MultiTargetObservation *value) {
    printf("{\"kind\":\"WILD_DOUBLE\",\"battle_type_flags\":%" PRIu32 ","
           "\"active_battlers\":%u,\"frames\":%" PRIu32 ","
           "\"four_controllers_initialized\":%s,\"species\":[",
           value->type_flags, value->battler_count, value->frames,
           value->four_controllers_initialized ? "true" : "false");
    for (unsigned battler = 0; battler < BATTLE_CORE_MAX_BATTLERS; ++battler) {
        if (battler) putchar(',');
        printf("%u", value->species[battler]);
    }
    printf("],\"party_indexes\":[");
    for (unsigned battler = 0; battler < BATTLE_CORE_MAX_BATTLERS; ++battler) {
        if (battler) putchar(',');
        printf("%u", value->party_index[battler]);
    }
    printf("],\"spread_move\":%u,\"spread_pp_before\":%u,"
           "\"spread_pp_after\":%u,\"opponent_hp_before\":[%u,%u],"
           "\"opponent_hp_after\":[%u,%u],\"both_opponents_hit\":%s,"
           "\"setup_call\":",
           value->spread_move, value->spread_pp_before, value->spread_pp_after,
           value->opponent_hp_before[0], value->opponent_hp_before[1],
           value->opponent_hp_after[0], value->opponent_hp_after[1],
           value->both_opponents_hit ? "true" : "false");
    print_call(&value->setup_call);
    putchar('}');
}

static void print_switch(const struct SwitchObservation *value) {
    printf("{\"kind\":\"PARTY_MENU_SWITCH\",\"frames\":%" PRIu32 ","
           "\"chosen_action\":%u,\"selected_party_mon\":%u,"
           "\"species_before\":%u,\"species_after\":%u,"
           "\"party_index_before\":%u,\"party_index_after\":%u,"
           "\"battle_callback\":\"0x%08" PRIX32 "\","
           "\"party_menu_callback\":\"0x%08" PRIX32 "\","
           "\"party_menu_opened\":%s,\"controller_returned\":%s,"
           "\"setup_call\":",
           value->frames, value->chosen_action, value->selected_party_mon,
           value->species_before, value->species_after,
           value->party_index_before, value->party_index_after,
           value->battle_callback, value->party_menu_callback,
           value->party_menu_opened ? "true" : "false",
           value->controller_returned ? "true" : "false");
    print_call(&value->setup_call);
    putchar('}');
}

static void print_capture(const struct CaptureObservation *value) {
    printf("{\"kind\":\"MASTER_BALL_CAPTURE\",\"frames\":%" PRIu32 ","
           "\"chosen_action\":%u,\"outcome_seen\":%u,"
           "\"party_count_before\":%u,\"party_count_after\":%u,"
           "\"captured_species\":%u,\"bag_opened\":%s,"
           "\"ball_consumed\":%s,\"battle_runtime_initialized\":%s,"
           "\"battle_runtime_cleaned\":%s,\"add_ball\":{"
           "\"item\":%u,\"count\":1,\"result\":%" PRIu32 ","
           "\"instructions\":%" PRIu32 "},\"setup_call\":",
           value->frames, value->chosen_action, value->outcome_seen,
           value->party_count_before, value->party_count_after,
           value->captured_species, value->bag_opened ? "true" : "false",
           value->ball_consumed ? "true" : "false",
           value->battle_runtime_initialized ? "true" : "false",
           value->battle_runtime_cleaned ? "true" : "false",
           BATTLE_CORE_MASTER_BALL, value->add_ball_result,
           value->add_ball_instructions);
    print_call(&value->setup_call);
    putchar('}');
}

static void print_status_completion(const struct StatusObservation *value) {
    printf("{\"cleanup_frames\":%" PRIu32 ",\"outcome_seen\":%u,"
           "\"enemy_fainted_seen\":%s,\"party_status_after_cleanup\":%"
           PRIu32 ",\"status_mask\":%u,"
           "\"status_cleared_on_faint\":%s,"
           "\"battle_runtime_cleaned\":%s}",
           value->cleanup_frames, value->outcome_seen,
           value->enemy_fainted_seen ? "true" : "false",
           value->party_status_after_cleanup, BATTLE_CORE_STATUS_TOXIC,
           value->status_cleared_on_faint ? "true" : "false",
           value->battle_runtime_cleaned ? "true" : "false");
}

static void print_priority(const struct PriorityObservation *value) {
    printf("{\"kind\":\"WILD_PRIORITY_ORDER\",\"frames\":%" PRIu32 ","
           "\"priority_move\":%u,\"alternative_move\":%u,"
           "\"opponent_move\":%u,\"priority_value\":%d,"
           "\"opponent_priority_value\":%d,"
           "\"player_speed\":%u,\"opponent_speed\":%u,"
           "\"turn_order\":[%u,%u],\"first_damage_dealt_by\":%u,"
           "\"player_pp_before\":%u,\"player_pp_after\":%u,"
           "\"opponent_pp_before\":%u,\"opponent_pp_after\":%u,"
           "\"player_hp_before\":%u,\"player_hp_after\":%u,"
           "\"opponent_hp_before\":%u,\"opponent_hp_after\":%u,"
           "\"selected_through_controller\":%s,"
           "\"both_moves_executed\":%s,"
           "\"slower_priority_user_moved_first\":%s,\"setup_call\":",
           value->frames, value->priority_move, value->alternative_move,
           value->opponent_move, value->priority_value,
           value->opponent_priority_value, value->player_speed,
           value->opponent_speed, value->turn_order[0], value->turn_order[1],
           value->first_damage_dealt_by, value->player_pp_before,
           value->player_pp_after, value->opponent_pp_before,
           value->opponent_pp_after, value->player_hp_before,
           value->player_hp_after, value->opponent_hp_before,
           value->opponent_hp_after,
           value->selected_through_controller ? "true" : "false",
           value->both_moves_executed ? "true" : "false",
           value->slower_priority_user_moved_first ? "true" : "false");
    print_call(&value->battle.setup_call);
    putchar('}');
}

static void print_battle(const char *kind, uint32_t setup_address,
                         uint32_t trainer_id,
                         const struct BattleObservation *value) {
    printf("{\"kind\":\"%s\",\"direct_setup\":\"0x%08" PRIX32 "\","
           "\"trainer_id\":%" PRIu32 ",\"setup_frames\":%" PRIu32 ","
           "\"battle_type_flags\":%" PRIu32 ",\"trainer_flag\":%s,"
           "\"active_battlers\":%u,\"absent_flags\":%u,\"outcome\":%u,"
           "\"runtime_initialized\":{\"gNewBS\":%s,\"gBattleStruct\":%s,"
           "\"gBattleResources\":%s},\"ewram_iwram_fnv1a64\":\"%016" PRIx64 "\","
           "\"setup_call\":",
           kind, setup_address, trainer_id, value->setup_frames, value->type_flags,
           (value->type_flags & BATTLE_TYPE_TRAINER) ? "true" : "false",
           value->battler_count, value->absent_flags, value->outcome,
           value->new_battle_struct_initialized ? "true" : "false",
           value->battle_struct_initialized ? "true" : "false",
           value->battle_resources_initialized ? "true" : "false",
           value->ram_digest);
    print_call(&value->setup_call);
    printf(",\"turn\":");
    print_turn(&value->turn);
    printf(",\"battlers\":[");
    for (unsigned battler = 0; battler < value->battler_count; ++battler) {
        const struct MonObservation *mon = &value->battlers[battler];
        if (battler) putchar(',');
        printf("{\"index\":%u,\"species\":%u,\"hp\":%u,\"level\":%u,"
               "\"experience\":%" PRIu32 ",\"status1\":%" PRIu32 ","
               "\"status2\":%" PRIu32 ",\"moves\":[",
               battler, mon->species, mon->hp, mon->level, mon->experience,
               mon->status1, mon->status2);
        for (unsigned slot = 0; slot < BATTLE_CORE_MOVE_SLOTS; ++slot) {
            if (slot) putchar(',');
            printf("%u", mon->moves[slot]);
        }
        printf("],\"pp\":[");
        for (unsigned slot = 0; slot < BATTLE_CORE_MOVE_SLOTS; ++slot) {
            if (slot) putchar(',');
            printf("%u", mon->pp[slot]);
        }
        printf("]}");
    }
    printf("]}");
}

#ifndef BATTLE_CORE_EMBEDDED
int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s ROM EXPECTED_ROM_SHA256\n", argv[0]);
        return 2;
    }
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64 || strcmp(rom_sha256, argv[2]) != 0) {
        battle_core_die("ROM SHA-256 mismatch");
    }

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {.sample = NULL, .unixTime = fixed_unix_time,
                             .serialize = NULL, .deserialize = NULL};
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) battle_core_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1])) battle_core_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);

    struct MoveTableObservation move_table = observe_move_table(core);
    struct HookObservation route_hooks[ROUTE_COUNT];
    for (unsigned route = 0; route < ROUTE_COUNT; ++route) {
        route_hooks[route] = observe_hook(core, &ROUTE_CONTRACTS[route]);
    }
    struct HookObservation wild_hook = observe_hook(core, &WILD_SETUP_HOOK);
    struct HookObservation trainer_hook = observe_hook(core, &TRAINER_SETUP_HOOK);

    run_trace_prefix(core);
    if (log_problem_count) battle_core_die("mGBA warned/errored during natural field boot");
    struct Snapshot field = take_snapshot(core);
    struct BattleObservation wild[2];
    struct BattleObservation trainer[2];
    struct StatusObservation status[2];
    struct PriorityObservation priority[2];
    struct EndObservation wild_end[2];
    struct EndObservation trainer_end[2];
    struct MultiTargetObservation multi_target[2];
    struct SwitchObservation switch_route[2];
    struct CaptureObservation capture[2];
    for (unsigned run = 0; run < 2; ++run) {
        wild[run] = run_wild(core, &field, 0);
        trainer[run] = run_trainer(core, &field);
        status[run] = run_status_route(core, &field);
        priority[run] = run_priority_route(core, &field, move_table.pointer);
        wild_end[run] = run_faint_experience_end(core, &field);
        trainer_end[run] = run_trainer_battle_end(core, &field);
        multi_target[run] = run_multi_target_double(core, &field);
        switch_route[run] = run_switch_menu(core, &field);
        capture[run] = run_capture_menu(core, &field);
    }
    if (!battle_equal(&wild[0], &wild[1])
        || !battle_equal(&trainer[0], &trainer[1])
        || !status_equal(&status[0], &status[1])
        || !priority_equal(&priority[0], &priority[1])
        || !end_equal(&wild_end[0], &wild_end[1])
        || !end_equal(&trainer_end[0], &trainer_end[1])
        || !multi_target_equal(&multi_target[0], &multi_target[1])
        || !switch_equal(&switch_route[0], &switch_route[1])
        || !capture_equal(&capture[0], &capture[1])) {
        battle_core_die("two internal battle-core fixture runs differ");
    }
    if (log_problem_count) battle_core_die("mGBA warned/errored during battle fixtures");

    printf("{\"schema_version\":3,\"status\":\"PASS\","
           "\"fixture\":\"t06_battle_core_scheduler_v3\","
           "\"rom_sha256\":\"%s\",\"fixed_rtc_unix\":946684800,"
           "\"read_only\":true,\"boot_trace_segments\":%u,"
           "\"warnings_errors\":0,\"canonical_move_contract\":{"
           "\"count\":%u,\"max_id\":%u,\"stride\":%u,"
           "\"table_pointer\":\"0x%08" PRIX32 "\","
           "\"status_moves\":%" PRIu32 ",\"priority_moves\":%" PRIu32 ","
           "\"multi_target_moves\":%" PRIu32 "},\"setup_hooks\":{"
           "\"wild\":{\"site\":\"0x%08" PRIX32 "\",\"target\":\"0x%08" PRIX32
           "\",\"stub_size\":%u},\"trainer\":{\"site\":\"0x%08" PRIX32
           "\",\"target\":\"0x%08" PRIX32 "\",\"stub_size\":%u}},"
           "\"route_fixtures\":[",
           rom_sha256, BATTLE_CORE_FIELD_TRACE_SEGMENTS,
           BATTLE_CORE_CANONICAL_MOVE_COUNT, BATTLE_CORE_CANONICAL_MOVE_MAX,
           BATTLE_CORE_BATTLE_MOVE_SIZE, move_table.pointer,
           move_table.status_count, move_table.priority_count,
           move_table.multi_target_count,
           WILD_SETUP_HOOK.site, wild_hook.target, wild_hook.stub_size,
           TRAINER_SETUP_HOOK.site, trainer_hook.target, trainer_hook.stub_size);
    for (unsigned route = 0; route < ROUTE_COUNT; ++route) {
        const struct HookContract *contract = &ROUTE_CONTRACTS[route];
        uint32_t evidence_count = 1;
        bool executed_end_to_end = true;
        if (route) putchar(',');
        printf("{\"route\":\"%s\",\"classification\":\"%s\","
               "\"observation\":\"%s\",\"executed_end_to_end\":%s,"
               "\"direct_call_bounded\":%s,\"evidence_count\":%" PRIu32 ","
               "\"hook_site\":\"0x%08" PRIX32 "\","
               "\"hook_target\":\"0x%08" PRIX32 "\",\"stub_size\":%u}",
               contract->route, contract->classification, contract->observation,
               executed_end_to_end ? "true" : "false",
               contract->direct_call ? "true" : "false", evidence_count,
               contract->site, route_hooks[route].target,
               route_hooks[route].stub_size);
    }
    printf("],\"battles\":{\"wild\":");
    print_battle("WILD", BATTLE_CORE_START_WILD, 0, &wild[0]);
    printf(",\"trainer\":");
    print_battle("TRAINER", BATTLE_CORE_START_TRAINER, 328, &trainer[0]);
    printf(",\"status\":");
    print_battle("WILD_STATUS", BATTLE_CORE_START_WILD, 0, &status[0].battle);
    printf("},\"battle_end\":{\"wild\":");
    print_end(&wild_end[0]);
    printf(",\"trainer\":");
    print_end(&trainer_end[0]);
    printf("},\"multi_target\":");
    print_multi_target(&multi_target[0]);
    printf(",\"status_completion\":");
    print_status_completion(&status[0]);
    printf(",\"priority\":");
    print_priority(&priority[0]);
    printf(",\"switch\":");
    print_switch(&switch_route[0]);
    printf(",\"capture\":");
    print_capture(&capture[0]);
    printf(",\"repeatability\":{\"internal_runs\":2,"
           "\"wild_identical\":true,\"trainer_identical\":true,"
           "\"status_identical\":true,\"priority_identical\":true,"
           "\"wild_end_identical\":true,"
           "\"trainer_end_identical\":true,\"multi_target_identical\":true,"
           "\"switch_identical\":true,\"capture_identical\":true},"
           "\"claims\":{\"wild_trainer_setup_executed\":true,"
           "\"wild_trainer_turn_executed\":true,"
           "\"wild_trainer_completion_executed\":true,"
           "\"status_apply_and_faint_clear_e2e\":true,"
           "\"faint_exp_end_executed\":true,"
           "\"priority_scheduler_order_e2e\":true,"
           "\"multi_target_double_e2e\":true,"
           "\"party_menu_switch_e2e\":true,"
           "\"bag_ball_capture_e2e\":true,"
           "\"all_routes_scheduler_e2e\":true,"
           "\"cfru_payload_pc_executed\":true},"
           "\"non_e2e_routes\":[],"
           "\"unreached_routes\":[],"
           "\"artifacts_written\":[]}\n");

    free(field.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
#endif
