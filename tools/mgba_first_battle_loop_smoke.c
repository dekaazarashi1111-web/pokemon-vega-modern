/*
 * USER-20260814-FIRST-BATTLE-LOOP regression runner for libmGBA 0.10.2.
 *
 * The fixture restores the reviewed natural-new-game field snapshot, enters
 * each of Vega's three first-rival trainer records through the real trainer
 * setup path, and selects a move through the battle controller.  It rejects
 * repeated Quick Claw/Custap scripts, placeholder item activation for an
 * itemless battler, and turns which fail to spend one PP or change HP.
 */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define BATTLE_CORE_EMBEDDED
#include "mgba_battle_core_smoke.c"

enum {
    FIRST_BATTLE_TRAINER_FAMER = 326,
    FIRST_BATTLE_TRAINER_ACTASHI = 327,
    FIRST_BATTLE_TRAINER_LEEPUN = 328,
    FIRST_BATTLE_SPECIES_LEEPUN = 1,
    FIRST_BATTLE_SPECIES_FAMER = 4,
    FIRST_BATTLE_SPECIES_ACTASHI = 7,
    FIRST_BATTLE_ITEM_NONE = 0,
    FIRST_BATTLE_ITEM_QUICK_CLAW = 183,
    FIRST_BATTLE_ITEM_CUSTAP_BERRY = 678,
    FIRST_BATTLE_ABILITY_QUICK_DRAW = 260,
    FIRST_BATTLE_ITEM_EFFECT_QUICK_CLAW = 26,
    FIRST_BATTLE_ITEM_EFFECT_CUSTAP_BERRY = 96,
    FIRST_BATTLE_QUICK_CLAW_SCRIPT = 0x09001AC2,
    FIRST_BATTLE_QUICK_DRAW_SCRIPT = 0x09001B00,
    FIRST_BATTLE_QUICK_DRAW_SCRIPT_END = 0x09001B28,
    FIRST_BATTLE_SCRIPT_POINTER = 0x02023CD4,
    FIRST_BATTLE_LAST_USED_ITEM = 0x02023CC8,
    FIRST_BATTLE_CURRENT_ACTION = 0x02023B43,
    FIRST_BATTLE_MAIN_FUNC = 0x03004FC4,
    FIRST_BATTLE_NEWBS_QUICK_CLAW_CUSTAP = 0x122,
    FIRST_BATTLE_NEWBS_QUICK_DRAW = 0x123,
    FIRST_BATTLE_NEWBS_QUICK_CLAW_RANDOM = 0xB4,
    FIRST_BATTLE_NEWBS_QUICK_DRAW_RANDOM = 0xB8,
    FIRST_BATTLE_NEWBS_ACTIVATED_BYTE = 0x164,
    FIRST_BATTLE_NEWBS_ACTIVATED_MASK = 0x04,
    FIRST_BATTLE_TURN_FRAME_LIMIT = 2400,
    FIRST_BATTLE_SCHEDULER_STEP_LIMIT = 1000000,
};

static uint32_t first_battle_get_bank_item_effect;
static uint32_t first_battle_run_turn_entry_pc;
static uint32_t first_battle_invalid_item_skip_pc;

struct FirstBattleCase {
    const char *name;
    uint16_t trainer_id;
    uint16_t player_species;
    uint16_t opponent_species;
    uint16_t player_move;
};

enum FirstBattlePriorityKind {
    FIRST_BATTLE_PRIORITY_QUICK_CLAW,
    FIRST_BATTLE_PRIORITY_CUSTAP,
    FIRST_BATTLE_PRIORITY_QUICK_DRAW,
};

struct FirstBattlePriorityCase {
    const char *name;
    enum FirstBattlePriorityKind kind;
    uint16_t item;
    uint16_t ability;
    uint8_t item_effect;
};

struct FirstBattleObservation {
    uint16_t trainer_id;
    uint16_t player_species;
    uint16_t opponent_species;
    uint16_t player_item;
    uint16_t opponent_item;
    uint16_t player_ability;
    uint16_t opponent_ability;
    uint8_t player_item_effect;
    uint8_t opponent_item_effect;
    uint8_t player_pp_before;
    uint8_t player_pp_after;
    uint16_t player_hp_before;
    uint16_t player_hp_after;
    uint16_t opponent_hp_before;
    uint16_t opponent_hp_after;
    uint32_t frames;
    uint32_t quick_claw_script_entries;
    uint32_t quick_draw_script_entries;
    uint32_t placeholder_item_entries;
    uint32_t max_consecutive_quick_claw_frames;
    uint32_t invalid_indicator_injection_writes;
    uint32_t scheduler_steps;
    uint32_t injection_first_main_func;
    uint32_t final_main_func;
    uint8_t final_action;
    uint8_t final_quick_draw_indicator;
    uint8_t final_quick_claw_indicator;
    bool final_activation_latched;
    bool invalid_indicator_injected;
    bool invalid_indicator_rejected;
    bool pp_spent_once;
    bool hp_changed;
};

struct FirstBattlePriorityObservation {
    struct FirstBattleObservation battle;
    uint8_t first_bank;
    bool scheduler_seen;
    bool indicator_seen;
    bool notification_seen;
};

static const struct FirstBattleCase FIRST_BATTLE_CASES[] = {
    {"PLAYER_ACTASHI", FIRST_BATTLE_TRAINER_ACTASHI,
     FIRST_BATTLE_SPECIES_ACTASHI, FIRST_BATTLE_SPECIES_LEEPUN, 1},
    {"PLAYER_FAMER", FIRST_BATTLE_TRAINER_FAMER,
     FIRST_BATTLE_SPECIES_FAMER, FIRST_BATTLE_SPECIES_ACTASHI,
     BATTLE_CORE_MOVE_TACKLE},
    {"PLAYER_LEEPUN", FIRST_BATTLE_TRAINER_LEEPUN,
     FIRST_BATTLE_SPECIES_LEEPUN, FIRST_BATTLE_SPECIES_FAMER,
     BATTLE_CORE_MOVE_SCRATCH},
};

static const struct FirstBattlePriorityCase FIRST_BATTLE_PRIORITY_CASES[] = {
    {"QUICK_CLAW", FIRST_BATTLE_PRIORITY_QUICK_CLAW,
     FIRST_BATTLE_ITEM_QUICK_CLAW, 65,
     FIRST_BATTLE_ITEM_EFFECT_QUICK_CLAW},
    {"CUSTAP_BERRY", FIRST_BATTLE_PRIORITY_CUSTAP,
     FIRST_BATTLE_ITEM_CUSTAP_BERRY, 65,
     FIRST_BATTLE_ITEM_EFFECT_CUSTAP_BERRY},
    {"QUICK_DRAW", FIRST_BATTLE_PRIORITY_QUICK_DRAW,
     FIRST_BATTLE_ITEM_NONE, FIRST_BATTLE_ABILITY_QUICK_DRAW, 0},
};

static struct CallObservation setup_first_battle(
    struct mCore *core,
    const struct Snapshot *field,
    const struct FirstBattleCase *fixture
) {
    uint16_t moves[BATTLE_CORE_MOVE_SLOTS] = {
        fixture->player_move, 0, 0, 0,
    };
    static const uint8_t pp[BATTLE_CORE_MOVE_SLOTS] = {35, 0, 0, 0};
    uint8_t player[POKEMON_SIZE];

    restore_snapshot(core, field);
    create_mon_image(core, fixture->player_species, 5, moves, pp, player);
    clear_parties(core);
    seed_fixture(core);
    install_mon_image(core, ADDR_PLAYER_PARTY, player);
    write8(core, ADDR_PLAYER_PARTY_COUNT, 1);
    write16(core, BATTLE_CORE_TRAINER_MODE, 0);
    write16(core, BATTLE_CORE_TRAINER_OPPONENT_A, fixture->trainer_id);

    struct CallObservation setup = call_bounded(
        core, BATTLE_CORE_START_TRAINER, 0, 0, 0, 0);
    if (!setup.payload_pc_seen) {
        battle_core_die("first-battle setup did not execute CFRU payload code");
    }
    run_key_frames(core, 0, BATTLE_CORE_MENU_READY_FRAMES + 700U);
    return setup;
}

static void sample_first_battle_frame(
    struct mCore *core,
    struct FirstBattleObservation *result,
    bool *quick_claw_active,
    bool *quick_draw_active,
    uint32_t *consecutive_quick_claw_frames
) {
    uint32_t script = read32(core, FIRST_BATTLE_SCRIPT_POINTER);
    bool quick_claw = script >= FIRST_BATTLE_QUICK_CLAW_SCRIPT
        && script < FIRST_BATTLE_QUICK_DRAW_SCRIPT;
    bool quick_draw = script >= FIRST_BATTLE_QUICK_DRAW_SCRIPT
        && script < FIRST_BATTLE_QUICK_DRAW_SCRIPT_END;

    if (quick_claw && !*quick_claw_active) {
        ++result->quick_claw_script_entries;
        if (read16(core, FIRST_BATTLE_LAST_USED_ITEM) == FIRST_BATTLE_ITEM_NONE) {
            ++result->placeholder_item_entries;
        }
    }
    if (quick_draw && !*quick_draw_active) {
        ++result->quick_draw_script_entries;
    }
    if (quick_claw) {
        ++*consecutive_quick_claw_frames;
        if (*consecutive_quick_claw_frames
            > result->max_consecutive_quick_claw_frames) {
            result->max_consecutive_quick_claw_frames =
                *consecutive_quick_claw_frames;
        }
    } else {
        *consecutive_quick_claw_frames = 0;
    }
    *quick_claw_active = quick_claw;
    *quick_draw_active = quick_draw;
}

static void run_sampled_frames(
    struct mCore *core,
    struct FirstBattleObservation *result,
    bool *quick_claw_active,
    bool *quick_draw_active,
    uint32_t *consecutive_quick_claw_frames,
    uint16_t keys,
    uint32_t frames
) {
    core->setKeys(core, keys);
    for (uint32_t frame = 0; frame < frames; ++frame) {
        core->runFrame(core);
        ++result->frames;
        sample_first_battle_frame(
            core, result, quick_claw_active, quick_draw_active,
            consecutive_quick_claw_frames);
    }
}

static struct FirstBattleObservation run_first_battle_case(
    struct mCore *core,
    const struct Snapshot *field,
    const struct FirstBattleCase *fixture
) {
    struct FirstBattleObservation result = {0};
    bool quick_claw_active = false;
    bool quick_draw_active = false;
    uint32_t consecutive_quick_claw_frames = 0;
    (void)setup_first_battle(core, field, fixture);

    if (read8(core, ADDR_BATTLERS_COUNT) != 2
        || !(read32(core, ADDR_BATTLE_TYPE_FLAGS) & BATTLE_TYPE_TRAINER)) {
        battle_core_die("first-battle fixture did not enter a 1v1 trainer battle");
    }

    struct MonObservation player = observe_mon(core, 0);
    struct MonObservation opponent = observe_mon(core, 1);
    if (player.species != fixture->player_species
        || opponent.species != fixture->opponent_species) {
        battle_core_die("first-battle starter branch resolved unexpected species");
    }

    result.trainer_id = fixture->trainer_id;
    result.player_species = player.species;
    result.opponent_species = opponent.species;
    result.player_item = read16(core, ADDR_BATTLE_MONS + 0x2E);
    result.opponent_item = read16(
        core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + 0x2E);
    result.player_ability = read16(core, ADDR_BATTLE_MONS + 0x38);
    result.opponent_ability = read16(
        core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + 0x38);
    result.player_item_effect = (uint8_t)call_preserving(
        core, first_battle_get_bank_item_effect, 0, 0, 0, 0);
    result.opponent_item_effect = (uint8_t)call_preserving(
        core, first_battle_get_bank_item_effect, 1, 0, 0, 0);
    result.player_pp_before = player.pp[0];
    result.player_hp_before = player.hp;
    result.opponent_hp_before = opponent.hp;

    for (unsigned press = 0;
         press < BATTLE_CORE_TURN_INPUT_PRESSES
             && result.frames < FIRST_BATTLE_TURN_FRAME_LIMIT;
         ++press) {
        write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR, 0);
        run_sampled_frames(core, &result, &quick_claw_active,
                           &quick_draw_active,
                           &consecutive_quick_claw_frames,
                           1, 2);
        run_sampled_frames(core, &result, &quick_claw_active,
                           &quick_draw_active,
                           &consecutive_quick_claw_frames, 0,
                           BATTLE_CORE_TURN_INPUT_WAIT);
    }
    run_sampled_frames(core, &result, &quick_claw_active,
                       &quick_draw_active,
                       &consecutive_quick_claw_frames, 0,
                       BATTLE_CORE_TURN_SETTLE_FRAMES);

    player = observe_mon(core, 0);
    opponent = observe_mon(core, 1);
    result.player_pp_after = player.pp[0];
    result.player_hp_after = player.hp;
    result.opponent_hp_after = opponent.hp;
    result.pp_spent_once = result.player_pp_after + 1U
        == result.player_pp_before;
    result.hp_changed = result.player_hp_after != result.player_hp_before
        || result.opponent_hp_after != result.opponent_hp_before;
    result.final_action = read8(core, FIRST_BATTLE_CURRENT_ACTION);
    result.final_main_func = read32(core, FIRST_BATTLE_MAIN_FUNC);

    uint32_t newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
    if (newbs != 0) {
        result.final_quick_draw_indicator = read8(
            core, newbs + FIRST_BATTLE_NEWBS_QUICK_DRAW);
        result.final_quick_claw_indicator = read8(
            core, newbs + FIRST_BATTLE_NEWBS_QUICK_CLAW_CUSTAP);
        result.final_activation_latched =
            (read8(core, newbs + FIRST_BATTLE_NEWBS_ACTIVATED_BYTE)
             & FIRST_BATTLE_NEWBS_ACTIVATED_MASK) != 0;
    }
    return result;
}

static bool first_battle_choices_ready(struct mCore *core) {
    return read8(core, BATTLE_CORE_CHOSEN_ACTIONS) == 0
        && read8(core, BATTLE_CORE_CHOSEN_ACTIONS + 1U) == 0
        && read16(core, BATTLE_CORE_CHOSEN_MOVES) != 0
        && read16(core, BATTLE_CORE_CHOSEN_MOVES + 2U) != 0;
}

static struct FirstBattleObservation run_invalid_indicator_fault_case(
    struct mCore *core,
    const struct Snapshot *field,
    const struct FirstBattleCase *fixture
) {
    struct FirstBattleObservation result = {0};
    (void)setup_first_battle(core, field, fixture);

    if (read8(core, ADDR_BATTLERS_COUNT) != 2
        || !(read32(core, ADDR_BATTLE_TYPE_FLAGS) & BATTLE_TYPE_TRAINER)) {
        battle_core_die("fault fixture did not enter a 1v1 trainer battle");
    }

    struct MonObservation player = observe_mon(core, 0);
    struct MonObservation opponent = observe_mon(core, 1);
    if (player.species != fixture->player_species
        || opponent.species != fixture->opponent_species) {
        battle_core_die("fault fixture resolved unexpected starter species");
    }

    result.trainer_id = fixture->trainer_id;
    result.player_species = player.species;
    result.opponent_species = opponent.species;
    result.player_item = read16(core, ADDR_BATTLE_MONS + 0x2E);
    result.opponent_item = read16(
        core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + 0x2E);
    result.player_ability = read16(core, ADDR_BATTLE_MONS + 0x38);
    result.opponent_ability = read16(
        core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + 0x38);
    result.player_item_effect = (uint8_t)call_preserving(
        core, first_battle_get_bank_item_effect, 0, 0, 0, 0);
    result.opponent_item_effect = (uint8_t)call_preserving(
        core, first_battle_get_bank_item_effect, 1, 0, 0, 0);
    result.player_pp_before = player.pp[0];
    result.player_hp_before = player.hp;
    result.opponent_hp_before = opponent.hp;

    bool choices_ready = false;
    for (unsigned press = 0;
         press < BATTLE_CORE_TURN_INPUT_PRESSES && !choices_ready;
         ++press) {
        write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR, 0);
        for (unsigned phase = 0; phase < 2 && !choices_ready; ++phase) {
            uint16_t keys = phase == 0 ? 1 : 0;
            uint32_t frames = phase == 0 ? 2U : BATTLE_CORE_TURN_INPUT_WAIT;
            core->setKeys(core, keys);
            for (uint32_t frame = 0; frame < frames; ++frame) {
                core->runFrame(core);
                ++result.frames;
                if (first_battle_choices_ready(core)) {
                    choices_ready = true;
                    break;
                }
            }
        }
    }
    if (!choices_ready) {
        battle_core_die("fault fixture did not complete controller move selection");
    }

    core->setKeys(core, 0);
    for (uint32_t step = 0;
         step < FIRST_BATTLE_SCHEDULER_STEP_LIMIT;
         ++step) {
        uint32_t pc = ((uint32_t)read_register(core, "pc")) & ~1U;
        if (pc == first_battle_run_turn_entry_pc
            && !result.invalid_indicator_injected) {
            uint32_t newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
            if (newbs == 0) {
                battle_core_die("fault fixture lost gNewBS before scheduler entry");
            }
            write8(core,
                   newbs + FIRST_BATTLE_NEWBS_QUICK_CLAW_CUSTAP,
                   read8(core,
                         newbs + FIRST_BATTLE_NEWBS_QUICK_CLAW_CUSTAP)
                       | 2U);
            result.invalid_indicator_injected = true;
            result.invalid_indicator_injection_writes = 1;
            result.injection_first_main_func = read32(
                core, FIRST_BATTLE_MAIN_FUNC);
        }
        uint32_t script = read32(core, FIRST_BATTLE_SCRIPT_POINTER);
        if (result.invalid_indicator_injected
            && script >= FIRST_BATTLE_QUICK_CLAW_SCRIPT
            && script < FIRST_BATTLE_QUICK_DRAW_SCRIPT) {
            ++result.quick_claw_script_entries;
            if (read16(core, FIRST_BATTLE_LAST_USED_ITEM)
                == FIRST_BATTLE_ITEM_NONE) {
                ++result.placeholder_item_entries;
            }
            break;
        }
        if (result.invalid_indicator_injected
            && pc >= first_battle_invalid_item_skip_pc
            && pc <= first_battle_invalid_item_skip_pc + 8U) {
            result.invalid_indicator_rejected = true;
            break;
        }

        core->setKeys(core, 0);
        core->step(core);
        ++result.scheduler_steps;
    }

    if (result.invalid_indicator_rejected) {
        bool quick_claw_active = false;
        bool quick_draw_active = false;
        uint32_t consecutive_quick_claw_frames = 0;
        bool pp_spent = false;
        uint32_t input_cycle = 2U + BATTLE_CORE_TURN_INPUT_WAIT;
        for (uint32_t frame = 0;
             frame < FIRST_BATTLE_TURN_FRAME_LIMIT && !pp_spent;
             ++frame) {
            core->setKeys(core, frame % input_cycle < 2U ? 1 : 0);
            core->runFrame(core);
            ++result.frames;
            sample_first_battle_frame(
                core, &result, &quick_claw_active, &quick_draw_active,
                &consecutive_quick_claw_frames);
            pp_spent = read8(
                core, ADDR_BATTLE_MONS + BATTLE_MON_PP_OFFSET)
                + 1U == result.player_pp_before;
        }
        core->setKeys(core, 0);
    }

    player = observe_mon(core, 0);
    opponent = observe_mon(core, 1);
    result.player_pp_after = player.pp[0];
    result.player_hp_after = player.hp;
    result.opponent_hp_after = opponent.hp;
    result.pp_spent_once = result.player_pp_after + 1U
        == result.player_pp_before;
    result.hp_changed = result.player_hp_after != result.player_hp_before
        || result.opponent_hp_after != result.opponent_hp_before;
    result.final_action = read8(core, FIRST_BATTLE_CURRENT_ACTION);
    result.final_main_func = read32(core, FIRST_BATTLE_MAIN_FUNC);

    uint32_t newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
    if (newbs != 0) {
        result.final_quick_draw_indicator = read8(
            core, newbs + FIRST_BATTLE_NEWBS_QUICK_DRAW);
        result.final_quick_claw_indicator = read8(
            core, newbs + FIRST_BATTLE_NEWBS_QUICK_CLAW_CUSTAP);
        result.final_activation_latched =
            (read8(core, newbs + FIRST_BATTLE_NEWBS_ACTIVATED_BYTE)
             & FIRST_BATTLE_NEWBS_ACTIVATED_MASK) != 0;
    }
    return result;
}

static struct FirstBattlePriorityObservation run_legitimate_priority_case(
    struct mCore *core,
    const struct Snapshot *field,
    const struct FirstBattleCase *fixture,
    const struct FirstBattlePriorityCase *priority
) {
    struct FirstBattlePriorityObservation result = {
        .first_bank = UINT8_MAX,
    };
    struct FirstBattleObservation *battle = &result.battle;
    (void)setup_first_battle(core, field, fixture);

    uint32_t opponent_base = ADDR_BATTLE_MONS + BATTLE_MON_SIZE;
    write16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_SPEED, 100);
    write16(core, opponent_base + BATTLE_CORE_MON_SPEED, 1);
    write16(core, opponent_base + 0x2E, priority->item);
    write16(core, opponent_base + 0x38, priority->ability);
    if (priority->kind == FIRST_BATTLE_PRIORITY_CUSTAP) {
        write16(core, opponent_base + BATTLE_CORE_MON_HP, 1);
    }

    uint32_t newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
    if (newbs == 0) {
        battle_core_die("priority fixture lost gNewBS");
    }
    write8(core, newbs + FIRST_BATTLE_NEWBS_QUICK_CLAW_RANDOM + 1U, 0);
    write8(core, newbs + FIRST_BATTLE_NEWBS_QUICK_DRAW_RANDOM + 1U, 0);

    struct MonObservation player = observe_mon(core, 0);
    struct MonObservation opponent = observe_mon(core, 1);
    battle->trainer_id = fixture->trainer_id;
    battle->player_species = player.species;
    battle->opponent_species = opponent.species;
    battle->player_item = read16(core, ADDR_BATTLE_MONS + 0x2E);
    battle->opponent_item = read16(core, opponent_base + 0x2E);
    battle->player_ability = read16(core, ADDR_BATTLE_MONS + 0x38);
    battle->opponent_ability = read16(core, opponent_base + 0x38);
    battle->player_item_effect = (uint8_t)call_preserving(
        core, first_battle_get_bank_item_effect, 0, 0, 0, 0);
    battle->opponent_item_effect = (uint8_t)call_preserving(
        core, first_battle_get_bank_item_effect, 1, 0, 0, 0);
    battle->player_pp_before = player.pp[0];
    battle->player_hp_before = player.hp;
    battle->opponent_hp_before = opponent.hp;

    bool choices_ready = false;
    for (unsigned press = 0;
         press < BATTLE_CORE_TURN_INPUT_PRESSES && !choices_ready;
         ++press) {
        write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR, 0);
        for (unsigned phase = 0; phase < 2 && !choices_ready; ++phase) {
            uint16_t keys = phase == 0 ? 1 : 0;
            uint32_t frames = phase == 0 ? 2U : BATTLE_CORE_TURN_INPUT_WAIT;
            core->setKeys(core, keys);
            for (uint32_t frame = 0; frame < frames; ++frame) {
                core->runFrame(core);
                ++battle->frames;
                if (first_battle_choices_ready(core)) {
                    choices_ready = true;
                    break;
                }
            }
        }
    }
    if (!choices_ready) {
        battle_core_die("priority fixture did not complete move selection");
    }
    write8(core, newbs + FIRST_BATTLE_NEWBS_QUICK_CLAW_RANDOM + 1U, 0);
    write8(core, newbs + FIRST_BATTLE_NEWBS_QUICK_DRAW_RANDOM + 1U, 0);

    core->setKeys(core, 0);
    for (uint32_t step = 0;
         step < FIRST_BATTLE_SCHEDULER_STEP_LIMIT;
         ++step) {
        uint32_t pc = ((uint32_t)read_register(core, "pc")) & ~1U;
        if (pc == first_battle_run_turn_entry_pc && !result.scheduler_seen) {
            result.scheduler_seen = true;
            result.first_bank = read8(core, BATTLE_CORE_BANKS_BY_TURN_ORDER);
            uint8_t indicator = priority->kind
                    == FIRST_BATTLE_PRIORITY_QUICK_DRAW
                ? read8(core, newbs + FIRST_BATTLE_NEWBS_QUICK_DRAW)
                : read8(core, newbs + FIRST_BATTLE_NEWBS_QUICK_CLAW_CUSTAP);
            result.indicator_seen = (indicator & 2U) != 0;
        }

        uint32_t script = read32(core, FIRST_BATTLE_SCRIPT_POINTER);
        bool quick_claw_script = script >= FIRST_BATTLE_QUICK_CLAW_SCRIPT
            && script < FIRST_BATTLE_QUICK_DRAW_SCRIPT;
        bool quick_draw_script = script >= FIRST_BATTLE_QUICK_DRAW_SCRIPT
            && script < FIRST_BATTLE_QUICK_DRAW_SCRIPT_END;
        bool notification_seen = priority->kind == FIRST_BATTLE_PRIORITY_QUICK_DRAW
            ? quick_draw_script : quick_claw_script;
        if (result.scheduler_seen && notification_seen) {
            result.notification_seen = true;
            if (priority->kind != FIRST_BATTLE_PRIORITY_QUICK_DRAW) {
                battle->quick_claw_script_entries = 1;
                if (read16(core, FIRST_BATTLE_LAST_USED_ITEM)
                    == FIRST_BATTLE_ITEM_NONE) {
                    battle->placeholder_item_entries = 1;
                }
            } else {
                battle->quick_draw_script_entries = 1;
            }
            break;
        }

        core->step(core);
        ++battle->scheduler_steps;
    }

    if (result.notification_seen) {
        uint32_t input_cycle = 2U + BATTLE_CORE_TURN_INPUT_WAIT;
        bool pp_spent = false;
        for (uint32_t frame = 0;
             frame < FIRST_BATTLE_TURN_FRAME_LIMIT && !pp_spent;
             ++frame) {
            core->setKeys(core, frame % input_cycle < 2U ? 1 : 0);
            core->runFrame(core);
            ++battle->frames;
            pp_spent = read8(
                core, ADDR_BATTLE_MONS + BATTLE_MON_PP_OFFSET)
                + 1U == battle->player_pp_before;
        }
        core->setKeys(core, 0);
    }

    player = observe_mon(core, 0);
    opponent = observe_mon(core, 1);
    battle->player_pp_after = player.pp[0];
    battle->player_hp_after = player.hp;
    battle->opponent_hp_after = opponent.hp;
    battle->pp_spent_once = battle->player_pp_after + 1U
        == battle->player_pp_before;
    battle->hp_changed = battle->player_hp_after != battle->player_hp_before
        || battle->opponent_hp_after != battle->opponent_hp_before;
    battle->final_action = read8(core, FIRST_BATTLE_CURRENT_ACTION);
    battle->final_main_func = read32(core, FIRST_BATTLE_MAIN_FUNC);
    battle->final_quick_draw_indicator = read8(
        core, newbs + FIRST_BATTLE_NEWBS_QUICK_DRAW);
    battle->final_quick_claw_indicator = read8(
        core, newbs + FIRST_BATTLE_NEWBS_QUICK_CLAW_CUSTAP);
    battle->final_activation_latched =
        (read8(core, newbs + FIRST_BATTLE_NEWBS_ACTIVATED_BYTE)
         & FIRST_BATTLE_NEWBS_ACTIVATED_MASK) != 0;
    return result;
}

static void print_first_battle_observation(
    const struct FirstBattleCase *fixture,
    const struct FirstBattleObservation *value
) {
    printf("{\"branch\":\"%s\",\"trainer_id\":%u,"
           "\"player_species\":%u,\"opponent_species\":%u,"
           "\"player_item\":%u,\"opponent_item\":%u,"
           "\"player_ability\":%u,\"opponent_ability\":%u,"
           "\"player_item_effect\":%u,\"opponent_item_effect\":%u,"
           "\"frames\":%" PRIu32 ",\"quick_claw_script_entries\":%"
           PRIu32 ",\"quick_draw_script_entries\":%" PRIu32 ","
           "\"placeholder_item_entries\":%" PRIu32 ","
           "\"max_consecutive_quick_claw_frames\":%" PRIu32 ","
           "\"invalid_indicator_injection_writes\":%" PRIu32 ","
           "\"invalid_indicator_injected\":%s,"
           "\"invalid_indicator_rejected\":%s,"
           "\"scheduler_steps\":%" PRIu32 ","
           "\"injection_first_main_func\":\"0x%08" PRIx32 "\","
           "\"final_main_func\":\"0x%08" PRIx32 "\","
           "\"pp_before\":%u,\"pp_after\":%u,"
           "\"player_hp_before\":%u,\"player_hp_after\":%u,"
           "\"opponent_hp_before\":%u,\"opponent_hp_after\":%u,"
           "\"pp_spent_once\":%s,\"hp_changed\":%s,"
           "\"final_action\":%u,\"final_quick_draw_indicator\":%u,"
           "\"final_quick_claw_indicator\":%u,"
           "\"final_activation_latched\":%s}",
           fixture->name, value->trainer_id, value->player_species,
           value->opponent_species, value->player_item,
           value->opponent_item, value->player_ability,
           value->opponent_ability, value->player_item_effect,
           value->opponent_item_effect, value->frames,
           value->quick_claw_script_entries,
           value->quick_draw_script_entries,
           value->placeholder_item_entries,
           value->max_consecutive_quick_claw_frames,
           value->invalid_indicator_injection_writes,
           value->invalid_indicator_injected ? "true" : "false",
           value->invalid_indicator_rejected ? "true" : "false",
           value->scheduler_steps,
           value->injection_first_main_func, value->final_main_func,
           value->player_pp_before, value->player_pp_after,
           value->player_hp_before, value->player_hp_after,
           value->opponent_hp_before, value->opponent_hp_after,
           value->pp_spent_once ? "true" : "false",
           value->hp_changed ? "true" : "false", value->final_action,
           value->final_quick_draw_indicator,
           value->final_quick_claw_indicator,
           value->final_activation_latched ? "true" : "false");
}

static void print_first_battle_priority_observation(
    const struct FirstBattlePriorityCase *fixture,
    const struct FirstBattlePriorityObservation *value
) {
    printf("{\"effect\":\"%s\",\"scheduler_seen\":%s,"
           "\"indicator_seen\":%s,\"notification_seen\":%s,"
           "\"first_bank\":%u,\"observation\":",
           fixture->name,
           value->scheduler_seen ? "true" : "false",
           value->indicator_seen ? "true" : "false",
           value->notification_seen ? "true" : "false",
           value->first_bank);
    print_first_battle_observation(&FIRST_BATTLE_CASES[0], &value->battle);
    putchar('}');
}

#ifndef FIRST_BATTLE_EMBEDDED
int main(int argc, char **argv) {
    if (argc != 5) {
        fprintf(stderr,
                "usage: %s ROM EXPECTED_ROM_SHA256 "
                "RunTurnActionsFunctions GetBankItemEffect\n",
                argv[0]);
        return 2;
    }
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64 || strcmp(rom_sha256, argv[2]) != 0) {
        battle_core_die("ROM SHA-256 mismatch");
    }
    uint32_t run_turn_actions = parse_address(argv[3]);
    first_battle_get_bank_item_effect = parse_address(argv[4]);
    first_battle_run_turn_entry_pc = run_turn_actions + 0x002U;
    first_battle_invalid_item_skip_pc = run_turn_actions + 0x08CU;

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {.sample = NULL, .unixTime = fixed_unix_time,
                             .serialize = NULL, .deserialize = NULL};
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) {
        battle_core_die("mGBA core initialization failed");
    }
    if (!mCoreLoadFile(core, argv[1])) battle_core_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);

    run_trace_prefix(core);
    if (log_problem_count) {
        battle_core_die("mGBA warned/errored during natural field boot");
    }
    struct Snapshot field = take_snapshot(core);
    struct FirstBattleObservation observations[ARRAY_LEN(FIRST_BATTLE_CASES)];
    bool pass = true;

    printf("{\"schema_version\":1,\"fixture\":"
           "\"first_rival_action_order_scheduler\","
           "\"rom_sha256\":\"%s\",\"branches\":[", rom_sha256);
    for (unsigned index = 0; index < ARRAY_LEN(FIRST_BATTLE_CASES); ++index) {
        observations[index] = run_first_battle_case(
            core, &field, &FIRST_BATTLE_CASES[index]);
        const struct FirstBattleObservation *value = &observations[index];
        if (index) putchar(',');
        print_first_battle_observation(&FIRST_BATTLE_CASES[index], value);
        if (value->player_item != FIRST_BATTLE_ITEM_NONE
            || value->opponent_item != FIRST_BATTLE_ITEM_NONE
            || value->player_item_effect != 0
            || value->opponent_item_effect != 0
            || value->quick_claw_script_entries != 0
            || value->quick_draw_script_entries != 0
            || value->placeholder_item_entries != 0
            || !value->pp_spent_once
            || !value->hp_changed) {
            pass = false;
        }
    }
    struct FirstBattleObservation fault_injection =
        run_invalid_indicator_fault_case(
            core, &field, &FIRST_BATTLE_CASES[0]);
    printf("],\"invalid_indicator_fault_injection\":");
    print_first_battle_observation(&FIRST_BATTLE_CASES[0], &fault_injection);
    if (!fault_injection.invalid_indicator_injected
        || !fault_injection.invalid_indicator_rejected
        || fault_injection.quick_claw_script_entries != 0
        || fault_injection.placeholder_item_entries != 0
        || !fault_injection.pp_spent_once
        || !fault_injection.hp_changed) {
        pass = false;
    }

    struct FirstBattlePriorityObservation priority_observations[
        ARRAY_LEN(FIRST_BATTLE_PRIORITY_CASES)];
    printf(",\"legitimate_priority_effects\":[");
    for (unsigned index = 0;
         index < ARRAY_LEN(FIRST_BATTLE_PRIORITY_CASES);
         ++index) {
        const struct FirstBattlePriorityCase *fixture =
            &FIRST_BATTLE_PRIORITY_CASES[index];
        priority_observations[index] = run_legitimate_priority_case(
            core, &field, &FIRST_BATTLE_CASES[0], fixture);
        const struct FirstBattlePriorityObservation *value =
            &priority_observations[index];
        const struct FirstBattleObservation *battle = &value->battle;
        if (index) putchar(',');
        print_first_battle_priority_observation(fixture, value);
        bool quick_claw_expected = fixture->kind
            != FIRST_BATTLE_PRIORITY_QUICK_DRAW;
        if (!value->scheduler_seen
            || !value->indicator_seen
            || !value->notification_seen
            || value->first_bank != 1
            || battle->opponent_item != fixture->item
            || battle->opponent_ability != fixture->ability
            || battle->opponent_item_effect != fixture->item_effect
            || battle->quick_claw_script_entries
                != (quick_claw_expected ? 1U : 0U)
            || battle->quick_draw_script_entries
                != (quick_claw_expected ? 0U : 1U)
            || battle->placeholder_item_entries != 0
            || !battle->pp_spent_once
            || !battle->hp_changed) {
            pass = false;
        }
    }
    printf("],\"warnings_errors\":%u,\"status\":\"%s\"}\n",
           log_problem_count, pass && !log_problem_count ? "PASS" : "FAIL");

    free(field.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return pass && !log_problem_count ? 0 : 1;
}
#endif
