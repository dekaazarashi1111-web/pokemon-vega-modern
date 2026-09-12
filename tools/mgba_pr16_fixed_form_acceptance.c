/* Formal P03 fixed-form acceptance for the exact five-case contract.
 *
 * The initial map, progress, party, held item and replacement bag item are
 * fixtures.  Once a_guard() is installed, every transition, decline, battle,
 * item replacement, Save and Continue is driven by ordinary GBA input while
 * the controller performs read-only observations.  This runner is deliberately
 * scoped to P03 fixed forms; it does not claim full P03 or release readiness.
 */
#include "pr16_fixed_form_acceptance_helpers.c"
#include "pr16_fixed_form_acceptance_contract.h"

#define F_SCOPE "PR16_P03_FIXED_FORM_TRANSITION_PHYSICAL"
#define F_STATE 0x0203F720U
#define F_CURSOR 0x0203AD5EU
#define F_PARTY_SLOT 0x0203B01DU
#define F_TARGET_MON (QOL_PLAYER_PARTY + 100U)
#define F_ROWS_PER_PAGE 5U
#define F_MAX_PAGES 80U
#define F_REPLACEMENT_ITEM 1012U
#define F_BATTLE_MOVE_TABLE_POINTER 0x080001CCU
#define F_BATTLE_MOVE_STRIDE 12U
#define F_BATTLE_MOVE_PP_OFFSET 4U

enum FKind {
    F_KIND_NECROZMA = 1,
    F_KIND_DECLINE = 2,
    F_KIND_CROWNED = 3,
};

struct FCase {
    const char *name;
    const char *family;
    const char *route_id;
    enum FKind kind;
    unsigned form_index;
    unsigned ordinal;
    unsigned base_species;
    unsigned target_species;
    unsigned project_move;
    unsigned held_item;
};

static const struct FCase f_cases[] = {
    {
        "necrozma-dusk-mane-four-slot-roundtrip",
        "necrozma_fixed_transition",
        "667255b406678096a7fa9344",
        F_KIND_NECROZMA,
        245U,
        70U,
        1198U,
        1260U,
        690U,
        0U,
    },
    {
        "necrozma-dawn-wings-four-slot-roundtrip",
        "necrozma_fixed_transition",
        "a79bbbec71c9a6be03a7d1e4",
        F_KIND_NECROZMA,
        246U,
        71U,
        1198U,
        1261U,
        669U,
        0U,
    },
    {
        "necrozma-decline-unchanged",
        "necrozma_fixed_transition",
        "667255b406678096a7fa9344+a79bbbec71c9a6be03a7d1e4",
        F_KIND_DECLINE,
        245U,
        70U,
        1198U,
        0U,
        0U,
        0U,
    },
    {
        "zacian-crowned-battle-roundtrip",
        "crowned_battle_transition",
        "371ffcca84ed4eb8fbb6d56b",
        F_KIND_CROWNED,
        280U,
        87U,
        1361U,
        1386U,
        768U,
        699U,
    },
    {
        "zamazenta-crowned-battle-roundtrip",
        "crowned_battle_transition",
        "2a8a2a856af40ec96087c9a7",
        F_KIND_CROWNED,
        281U,
        88U,
        1362U,
        1387U,
        769U,
        700U,
    },
};

static const unsigned f_other_moves[3] = {98U, 235U, 33U};
static const unsigned f_other_pp[3] = {11U, 3U, 7U};
static const char *f_prefix;
static unsigned f_growth_offset;
static unsigned f_attack_offset;
static unsigned f_bound_mon;

struct FTrace {
    unsigned interaction;
    unsigned menu;
    unsigned party;
    unsigned selection;
    unsigned transition;
    unsigned first_save;
    unsigned first_continue;
    unsigned reversion;
    unsigned second_save;
    unsigned second_continue;
    unsigned decline_dusk;
    unsigned decline_dawn;
    unsigned first_battle;
    unsigned project_move_seen;
    unsigned project_move_spent;
    unsigned first_battle_exit;
    unsigned item_replaced;
    unsigned second_battle;
    unsigned second_battle_exit;
};

static struct FTrace f_trace;

static void f_shot(struct mCore *core, const char *suffix)
{
    char path[4096];
    int length = snprintf(path, sizeof(path), "%s-%s.ppm", f_prefix, suffix);
    (void)core;
    a_require(length > 0 && length < (int)sizeof(path),
              "fixed acceptance screenshot path too long");
    FILE *stream = fopen(path, "wb");
    a_require(stream != NULL, "fixed acceptance screenshot open failed");
    a_require(fprintf(stream, "P6\n240 160\n255\n") > 0,
              "fixed acceptance screenshot header failed");
    for (unsigned index = 0U; index < 240U * 160U; ++index) {
        uint32_t pixel = (uint32_t)b_video[index];
        uint8_t rgb[3] = {
            (uint8_t)pixel,
            (uint8_t)(pixel >> 8),
            (uint8_t)(pixel >> 16),
        };
        a_require(fwrite(rgb, 1U, sizeof(rgb), stream) == sizeof(rgb),
                  "fixed acceptance screenshot write failed");
    }
    a_require(fclose(stream) == 0, "fixed acceptance screenshot close failed");
}

static void f_state(struct mCore *core, const char *label)
{
    b_state(core, label);
    fprintf(stderr,
            "FIXED_ACCEPT state=%08x result=%u host=%u service=%u mode=%u "
            "page=%u window=%u cursor=%u pending=%u slot=%u test=%u "
            "save=%u cb2=%08x newbs=%08x\n",
            read32(core, F_STATE), read16(core, F_STATE + 8U),
            read8(core, F_STATE + 18U), read8(core, F_STATE + 20U),
            read8(core, F_STATE + 19U), read8(core, F_STATE + 21U),
            read8(core, F_STATE + 22U), read8(core, F_CURSOR),
            read16(core, F_STATE + 10U), read8(core, F_PARTY_SLOT),
            read8(core, F_STATE + 27U), read32(core, P03_SAVE_COUNTER),
            read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER));
}

static bool f_live_field(struct mCore *core)
{
    return b_field(core) || k_equipment_field(core);
}

static bool f_menu(struct mCore *core, unsigned mode, unsigned page)
{
    return read16(core, F_STATE + 8U) == 9U
        && read8(core, F_STATE + 18U) == 3U
        && read8(core, F_STATE + 20U) == 3U
        && read8(core, F_STATE + 19U) == mode
        && read8(core, F_STATE + 21U) == page
        && read8(core, F_STATE + 22U) < 32U
        && read8(core, P02S_FIELD_LOCK)
        && !read8(core, F_STATE + 27U);
}

static void f_wait_menu(struct mCore *core, unsigned mode, unsigned page,
                        const char *label)
{
    for (unsigned frame = 0U; frame < 1800U; ++frame) {
        if (f_menu(core, mode, page)) {
            b_frames_run(core, 0U, 30U);
            return;
        }
        b_frame(core, 0U);
    }
    f_state(core, label);
    f_shot(core, label);
    a_die("fixed acceptance FORM menu timeout");
}

static void f_open_row(struct mCore *core, unsigned ordinal)
{
    unsigned page = ordinal / F_ROWS_PER_PAGE;
    unsigned cursor = ordinal % F_ROWS_PER_PAGE;
    a_require(page < F_MAX_PAGES && cursor < F_ROWS_PER_PAGE,
              "fixed acceptance row outside bounded menu");
    b_position(core, 1U, 36U, 6U, 4U);
    unsigned object = read8(core, P02S_PLAYER_AVATAR + 5U);
    a_require(object < 16U, "fixed acceptance FORM avatar unavailable");
    if ((read8(core, P02S_OBJECT_EVENTS + object * 0x24U + 0x18U) & 15U)
            != 2U)
        b_frame(core, QOL_KEY_UP);
    b_frames_run(core, 0U, 30U);
    b_position(core, 1U, 36U, 6U, 4U);
    f_trace.interaction = f_trace.interaction ? f_trace.interaction : b_frames + 1U;
    b_press(core, QOL_KEY_A, 90U);
    f_wait_menu(core, 0U, 0U, "root-timeout");
    a_require(read8(core, F_CURSOR) == 0U,
              "fixed acceptance root cursor differs");
    b_press(core, QOL_KEY_DOWN, 30U);
    a_require(read8(core, F_CURSOR) == 1U,
              "fixed acceptance FORM service cursor differs");
    b_press(core, QOL_KEY_A, 60U);
    f_wait_menu(core, 2U, 0U, "forms-timeout");
    for (unsigned current = 0U; current < page; ++current) {
        a_require(f_menu(core, 2U, current) && read8(core, F_CURSOR) == 0U,
                  "fixed acceptance page precondition differs");
        for (unsigned row = 0U; row < F_ROWS_PER_PAGE; ++row)
            b_press(core, QOL_KEY_DOWN, 30U);
        a_require(read8(core, F_CURSOR) == F_ROWS_PER_PAGE,
                  "fixed acceptance next-page cursor differs");
        b_press(core, QOL_KEY_A, 60U);
        f_wait_menu(core, 2U, current + 1U, "page-timeout");
    }
    a_require(f_menu(core, 2U, page) && read8(core, F_CURSOR) == 0U,
              "fixed acceptance target page differs");
    for (unsigned row = 0U; row < cursor; ++row)
        b_press(core, QOL_KEY_DOWN, 30U);
    a_require(read8(core, F_CURSOR) == cursor,
              "fixed acceptance target cursor differs");
    f_trace.menu = b_frames;
}

static void f_wait_party(struct mCore *core, unsigned expected_index)
{
    for (unsigned frame = 0U; frame < 1800U; ++frame) {
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) == P02S_CB2_PARTY) {
            b_frames_run(core, 0U, 120U);
            a_require(read16(core, F_STATE + 10U) == expected_index,
                      "fixed acceptance pending FORM index differs");
            a_require(read16(core, F_STATE + 8U) == 20U,
                      "fixed acceptance party state differs");
            f_trace.party = b_frames;
            return;
        }
        b_frame(core, 0U);
    }
    f_state(core, "party-timeout");
    f_shot(core, "party-timeout");
    a_die("fixed acceptance native party picker timeout");
}

static void f_wait_transition_field(struct mCore *core, int replacement_slot)
{
    unsigned stable = 0U;
    unsigned summary_down = 0U;
    for (unsigned frame = 1U; frame <= 24000U; ++frame) {
        uint32_t callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
        uint16_t key = 0U;
        bool pulse = frame % 30U == 0U;
        if (callback == P03F_SUMMARY_CB) {
            uint32_t summary = read32(core, QOL_SUMMARY_DATA_SLOT);
            a_require(p02s_ewram_pointer(summary) && summary <= 0x0203CC00U,
                      "fixed acceptance invalid summary pointer");
            if (p03f_task(core, P03F_SUMMARY_TASK)
                && read8(core, summary + P03F_SUMMARY_STATE) == 2U && pulse) {
                uint8_t cursor = read8(core, P03F_SUMMARY_CURSOR);
                a_require(cursor <= 4U,
                          "fixed acceptance invalid summary cursor");
                if ((int)cursor == replacement_slot) {
                    key = QOL_KEY_A;
                } else {
                    key = QOL_KEY_DOWN;
                    ++summary_down;
                    a_require(summary_down <= 5U,
                              "fixed acceptance summary cursor did not advance");
                }
            }
        } else if (callback == P02S_CB2_PARTY
                   && p03f_task(core, P03F_LEARN_ASK)) {
            if (pulse)
                key = QOL_KEY_A;
        } else if (callback == P02S_CB2_PARTY
                   && p03f_task(core, P03F_STOP_ASK)) {
            if (pulse)
                key = QOL_KEY_A;
        } else if (callback == P02S_CB2_PARTY && frame % 120U == 0U) {
            key = QOL_KEY_A;
        } else if (!f_live_field(core) && frame % 180U == 0U) {
            key = QOL_KEY_B;
        }
        core->setKeys(core, key);
        core->runFrame(core);
        ++b_frames;
        if (f_live_field(core) && !read8(core, P02S_FIELD_LOCK)) {
            if (++stable >= 60U) {
                core->setKeys(core, 0U);
                return;
            }
        } else {
            stable = 0U;
        }
    }
    core->setKeys(core, 0U);
    f_state(core, "transition-timeout");
    f_shot(core, "transition-timeout");
    a_die("fixed acceptance transition did not return to field");
}

static void f_select_target(struct mCore *core, const struct FCase *selected,
                            int replacement_slot)
{
    f_open_row(core, selected->ordinal);
    f_shot(core, "selected-row");
    b_press(core, QOL_KEY_A, 30U);
    f_wait_party(core, selected->form_index);
    for (unsigned attempt = 0U;
         attempt < 8U && read8(core, F_PARTY_SLOT) != 1U;
         ++attempt)
        b_press(core, QOL_KEY_DOWN, 30U);
    a_require(read8(core, F_PARTY_SLOT) == 1U,
              "fixed acceptance party picker did not select target");
    f_trace.selection = b_frames + 1U;
    b_press(core, QOL_KEY_A, 180U);
    f_wait_transition_field(core, replacement_slot);
    f_trace.transition = b_frames;
    f_state(core, "transition-observed");
    fprintf(stderr, "FIXED_MOVE species=%u item=%u moves=%u,%u,%u,%u "
            "pp=%u,%u,%u,%u bonuses=%u\n",
            read16(core, f_bound_mon + f_growth_offset),
            read16(core, f_bound_mon + f_growth_offset + 2U),
            read16(core, f_bound_mon + f_attack_offset),
            read16(core, f_bound_mon + f_attack_offset + 2U),
            read16(core, f_bound_mon + f_attack_offset + 4U),
            read16(core, f_bound_mon + f_attack_offset + 6U),
            read8(core, f_bound_mon + f_attack_offset + 8U),
            read8(core, f_bound_mon + f_attack_offset + 9U),
            read8(core, f_bound_mon + f_attack_offset + 10U),
            read8(core, f_bound_mon + f_attack_offset + 11U),
            read8(core, f_bound_mon + f_growth_offset + 8U));
    f_shot(core, "transition-observed");
}

static unsigned f_canonical_pp(struct mCore *core, unsigned move)
{
    uint32_t table = read32(core, F_BATTLE_MOVE_TABLE_POINTER);
    a_require(table >= 0x08000000U && table < 0x0A000000U,
              "fixed acceptance battle move table pointer differs");
    unsigned pp = read8(core, table + F_BATTLE_MOVE_PP_OFFSET
                              + F_BATTLE_MOVE_STRIDE * move);
    a_require(pp > 0U && pp <= 64U,
              "fixed acceptance canonical PP differs");
    return pp;
}

static unsigned f_species(struct mCore *core)
{
    return read16(core, f_bound_mon + f_growth_offset);
}

static unsigned f_held_item(struct mCore *core)
{
    return read16(core, f_bound_mon + f_growth_offset + 2U);
}

static unsigned f_pp_bonuses(struct mCore *core)
{
    return read8(core, f_bound_mon + f_growth_offset + 8U);
}

static unsigned f_move(struct mCore *core, unsigned slot)
{
    a_require(slot < 4U, "fixed acceptance move slot outside bound");
    return read16(core, f_bound_mon + f_attack_offset + 2U * slot);
}

static unsigned f_pp(struct mCore *core, unsigned slot)
{
    a_require(slot < 4U, "fixed acceptance PP slot outside bound");
    return read8(core, f_bound_mon + f_attack_offset + 8U + slot);
}

static bool f_has_move(struct mCore *core, unsigned move)
{
    for (unsigned slot = 0U; slot < 4U; ++slot) {
        if (f_move(core, slot) == move)
            return true;
    }
    return false;
}

static void f_bind_mon_layout(struct mCore *core, unsigned mon,
                              unsigned species, unsigned item,
                              const unsigned moves[4],
                              const unsigned pp[4])
{
    unsigned growth_count = 0U;
    unsigned attack_count = 0U;
    f_bound_mon = mon;
    for (unsigned index = 0U; index < 4U; ++index) {
        unsigned offset = 32U + 12U * index;
        if (read16(core, mon + offset) == species
            && read16(core, mon + offset + 2U) == item) {
            f_growth_offset = offset;
            ++growth_count;
        }
        bool match = true;
        for (unsigned slot = 0U; slot < 4U; ++slot) {
            if (read16(core, mon + offset + 2U * slot) != moves[slot]
                || read8(core, mon + offset + 8U + slot) != pp[slot])
                match = false;
        }
        if (match) {
            f_attack_offset = offset;
            ++attack_count;
        }
    }
    a_require(growth_count == 1U && attack_count == 1U
              && f_growth_offset != f_attack_offset,
              "fixed acceptance mon substructure layout is ambiguous");
}

static void f_check_identity(struct mCore *core, const uint8_t decoy[100],
                             unsigned pid, unsigned ot)
{
    uint8_t current[100];
    b_copy(core, QOL_PLAYER_PARTY, current, sizeof(current));
    a_require(!memcmp(current, decoy, sizeof(current)),
              "fixed acceptance changed nonselected individual");
    a_require(read32(core, f_bound_mon) == pid
              && read32(core, f_bound_mon + 4U) == ot,
              "fixed acceptance changed target identity");
}

static void f_check_necrozma_moves(struct mCore *core, unsigned species,
                                   unsigned transition_move,
                                   unsigned original_bonus)
{
    const unsigned slot = 1U;
    unsigned expected_bonus = original_bonus & ~(3U << (slot * 2U));
    a_require(f_species(core) == species,
              "fixed acceptance Necrozma species differs");
    a_require(f_move(core, slot)
                  == transition_move,
              "fixed acceptance transition-owned move differs");
    a_require(f_pp(core, slot)
                  == f_canonical_pp(core, transition_move),
              "fixed acceptance transition move PP differs");
    a_require(f_pp_bonuses(core) == expected_bonus,
              "fixed acceptance transition move PP Bonus boundary differs");
    unsigned other = 0U;
    for (unsigned index = 0U; index < 4U; ++index) {
        if (index == slot)
            continue;
        a_require(f_move(core, index)
                      == f_other_moves[other],
                  "fixed acceptance unrelated move changed");
        a_require(f_pp(core, index)
                      == f_other_pp[other],
                  "fixed acceptance unrelated PP changed");
        ++other;
    }
}

static void f_prepare_progress_and_map(struct mCore *core, unsigned group,
                                       unsigned map, unsigned x, unsigned y)
{
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_HALL_OF_FAME,
                          0U, 0U, 0U);
    write8(core, QOL_LEDGER + QOL_LEDGER_HALL_OF_FAME, 1U);
    write8(core, QOL_LEDGER + QOL_LEDGER_LEAGUE_II, 1U);
    write8(core, QOL_LEDGER + 0x73FU, 1U);
    write8(core, QOL_LEDGER + 0x745U, 1U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0U, 0U, 0U);
    (void)call_preserving(core, 0x09220861U, group, map, x, y);
    run_key_frames(core, 0U, 1800U);
    for (unsigned attempt = 0U; attempt < 12U && !b_field(core); ++attempt)
        b_press(core, QOL_KEY_B, 180U);
    a_require(b_field(core), "fixed acceptance fixture map did not settle");
    b_position(core, group, map, x, y);
}

static void f_prepare_two_mon_party(struct mCore *core, unsigned species,
                                    unsigned owned_move)
{
    clear_parties(core);
    b_create(core, QOL_PLAYER_PARTY, 0x123456F0U, 0x11223344U);
    create_mon(core, F_TARGET_MON, species, 50U);
    write8(core, QOL_PLAYER_PARTY_COUNT, 2U);
    set_mon_data_u32(core, F_TARGET_MON, QOL_MON_DATA_MOVE1 + 0U,
                     f_other_moves[0]);
    set_mon_data_u32(core, F_TARGET_MON, QOL_MON_DATA_MOVE1 + 1U,
                     owned_move);
    set_mon_data_u32(core, F_TARGET_MON, QOL_MON_DATA_MOVE1 + 2U,
                     f_other_moves[1]);
    set_mon_data_u32(core, F_TARGET_MON, QOL_MON_DATA_MOVE1 + 3U,
                     f_other_moves[2]);
    set_mon_data_u32(core, F_TARGET_MON, MON_DATA_PP1 + 0U, f_other_pp[0]);
    set_mon_data_u32(core, F_TARGET_MON, MON_DATA_PP1 + 1U, 5U);
    set_mon_data_u32(core, F_TARGET_MON, MON_DATA_PP1 + 2U, f_other_pp[1]);
    set_mon_data_u32(core, F_TARGET_MON, MON_DATA_PP1 + 3U, f_other_pp[2]);
    set_mon_data_u32(core, F_TARGET_MON, 21U, 229U);
    const unsigned moves[4] = {
        f_other_moves[0], owned_move, f_other_moves[1], f_other_moves[2]
    };
    const unsigned pp[4] = {f_other_pp[0], 5U, f_other_pp[1], f_other_pp[2]};
    f_bind_mon_layout(core, F_TARGET_MON, species, 0U, moves, pp);
}

static struct mCore *f_restart_continue(struct mCore *core,
                                        struct mCore *original,
                                        const char *rom,
                                        const char *save,
                                        const char *failure)
{
    a_restore(core, original);
    core = b_restart(core, rom, save);
    core->reset(core);
    *original = *core;
    a_guard(core);
    a_require(b_continue(core), failure);
    return core;
}

static void f_emit_common(const struct FCase *selected, const char *hash,
                          const char *kind, unsigned auxiliary_move,
                          unsigned automatic_saves, unsigned manual_saves,
                          unsigned fresh_cores, unsigned save_before,
                          unsigned save_after,
                          bool native_transition_entry,
                          bool transition_owned_move_resolution,
                          bool four_slot_boundary,
                          bool identity_preserved,
                          bool native_reversion,
                          bool normal_save,
                          bool fresh_continue,
                          bool native_decline_or_ineligible_control,
                          bool party_bytes_unchanged,
                          bool save_counter_unchanged,
                          bool native_held_item_or_battle_entry,
                          bool battle_form_and_move,
                          bool battle_exit_restoration,
                          bool held_item_removal_boundary,
                          bool no_invalid_saved_form_move_pair)
{
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"%s\",",
           F_SCOPE);
    printf("\"case\":\"%s\",\"kind\":\"%s\",\"family\":\"%s\",",
           selected->name, kind, selected->family);
    printf("\"route_id\":\"%s\",\"rom_sha256\":\"%s\",",
           selected->route_id, hash);
    printf("\"form_index\":%u,\"canonical_ordinal\":%u,",
           selected->form_index, selected->ordinal);
    printf("\"base_species\":%u,\"target_species\":%u,",
           selected->base_species, selected->target_species);
    printf("\"project_move\":%u,\"auxiliary_move\":%u,",
           selected->project_move, auxiliary_move);
    printf("\"held_item\":%u,\"replacement_item\":%u,",
           selected->held_item,
           selected->kind == F_KIND_CROWNED ? F_REPLACEMENT_ITEM : 0U);
    printf("\"automatic_saves\":%u,\"manual_saves\":%u,",
           automatic_saves, manual_saves);
    printf("\"fresh_cores\":%u,\"save_counter_before\":%u,",
           fresh_cores, save_before);
    printf("\"save_counter_after\":%u,\"total_frames\":%u,",
           save_after, b_frames);
#define F_BOOL(name, value) printf("\"" #name "\":%s,", (value) ? "true" : "false")
    F_BOOL(native_transition_entry, native_transition_entry);
    F_BOOL(transition_owned_move_resolution, transition_owned_move_resolution);
    F_BOOL(four_slot_boundary, four_slot_boundary);
    F_BOOL(identity_preserved, identity_preserved);
    F_BOOL(native_reversion, native_reversion);
    F_BOOL(normal_save, normal_save);
    F_BOOL(fresh_continue, fresh_continue);
    F_BOOL(native_decline_or_ineligible_control,
           native_decline_or_ineligible_control);
    F_BOOL(party_bytes_unchanged, party_bytes_unchanged);
    F_BOOL(save_counter_unchanged, save_counter_unchanged);
    F_BOOL(native_held_item_or_battle_entry,
           native_held_item_or_battle_entry);
    F_BOOL(battle_form_and_move, battle_form_and_move);
    F_BOOL(battle_exit_restoration, battle_exit_restoration);
    F_BOOL(held_item_removal_boundary, held_item_removal_boundary);
    F_BOOL(no_invalid_saved_form_move_pair,
           no_invalid_saved_form_move_pair);
#undef F_BOOL
    printf("\"starting_progress_map_party_are_fixtures\":true,");
    printf("\"held_items_and_bag_are_fixtures\":%s,",
           selected->kind == F_KIND_CROWNED ? "true" : "false");
    printf("\"input_only_after_guard\":true,\"warnings_errors\":0,");
    printf("\"case_accepted\":true,\"aggregate_gap_closed\":false,");
    printf("\"full_p03_acceptance\":false,\"release_ready\":false,");
    printf("\"witness\":{");
    printf("\"interaction\":%u,\"menu\":%u,\"party\":%u,",
           f_trace.interaction, f_trace.menu, f_trace.party);
    printf("\"selection\":%u,\"transition\":%u,",
           f_trace.selection, f_trace.transition);
    printf("\"first_save\":%u,\"first_continue\":%u,",
           f_trace.first_save, f_trace.first_continue);
    printf("\"reversion\":%u,\"second_save\":%u,",
           f_trace.reversion, f_trace.second_save);
    printf("\"second_continue\":%u,\"decline_dusk\":%u,",
           f_trace.second_continue, f_trace.decline_dusk);
    printf("\"decline_dawn\":%u,\"first_battle\":%u,",
           f_trace.decline_dawn, f_trace.first_battle);
    printf("\"project_move_seen\":%u,\"project_move_spent\":%u,",
           f_trace.project_move_seen, f_trace.project_move_spent);
    printf("\"first_battle_exit\":%u,\"item_replaced\":%u,",
           f_trace.first_battle_exit, f_trace.item_replaced);
    printf("\"second_battle\":%u,\"second_battle_exit\":%u}}\n",
           f_trace.second_battle, f_trace.second_battle_exit);
}

static void f_necrozma_case(struct mCore *core, struct mCore *original,
                            const struct FCase *selected,
                            const char *rom, const char *save,
                            const char *hash)
{
    uint8_t decoy[100];
    f_prepare_progress_and_map(core, 1U, 36U, 6U, 4U);
    f_prepare_two_mon_party(core, selected->base_species, F_PHOTON_GEYSER_MOVE);
    unsigned pid = read32(core, F_TARGET_MON);
    unsigned ot = read32(core, F_TARGET_MON + 4U);
    unsigned original_bonus = f_pp_bonuses(core);
    b_copy(core, QOL_PLAYER_PARTY, decoy, sizeof(decoy));
    unsigned save_before = read32(core, P03_SAVE_COUNTER);
    *original = *core;
    a_guard(core);

    f_select_target(core, selected, 1);
    f_check_identity(core, decoy, pid, ot);
    f_check_necrozma_moves(core, selected->target_species,
                           selected->project_move, original_bonus);
    a_require(!f_has_move(core, F_PHOTON_GEYSER_MOVE),
              "fixed acceptance retained both transition-owned moves");
    f_shot(core, "transformed");
    unsigned after_first_transition = read32(core, P03_SAVE_COUNTER);
    a_require(b_save(core), "fixed acceptance first normal Save failed");
    f_trace.first_save = b_frames;
    uint8_t target_snapshot[200];
    b_copy(core, QOL_PLAYER_PARTY, target_snapshot, sizeof(target_snapshot));
    core = f_restart_continue(core, original, rom, save,
                              "fixed acceptance first fresh Continue failed");
    f_trace.first_continue = b_frames;
    uint8_t target_loaded[200];
    b_copy(core, QOL_PLAYER_PARTY, target_loaded, sizeof(target_loaded));
    a_require(!memcmp(target_snapshot, target_loaded, sizeof(target_loaded)),
              "fixed acceptance first Continue changed transformed party");
    f_check_identity(core, decoy, pid, ot);
    f_check_necrozma_moves(core, selected->target_species,
                           selected->project_move, original_bonus);

    f_select_target(core, selected, 1);
    f_trace.reversion = b_frames;
    f_check_identity(core, decoy, pid, ot);
    f_check_necrozma_moves(core, selected->base_species,
                           F_PHOTON_GEYSER_MOVE, original_bonus);
    a_require(!f_has_move(core, selected->project_move),
              "fixed acceptance retained target move after reversion");
    f_shot(core, "reverted");
    unsigned after_reversion = read32(core, P03_SAVE_COUNTER);
    a_require(b_save(core), "fixed acceptance second normal Save failed");
    f_trace.second_save = b_frames;
    uint8_t base_snapshot[200];
    b_copy(core, QOL_PLAYER_PARTY, base_snapshot, sizeof(base_snapshot));
    core = f_restart_continue(core, original, rom, save,
                              "fixed acceptance second fresh Continue failed");
    f_trace.second_continue = b_frames;
    uint8_t base_loaded[200];
    b_copy(core, QOL_PLAYER_PARTY, base_loaded, sizeof(base_loaded));
    a_require(!memcmp(base_snapshot, base_loaded, sizeof(base_loaded)),
              "fixed acceptance second Continue changed reverted party");
    f_check_identity(core, decoy, pid, ot);
    f_check_necrozma_moves(core, selected->base_species,
                           F_PHOTON_GEYSER_MOVE, original_bonus);
    f_shot(core, "continued-reverted");

    unsigned save_after = read32(core, P03_SAVE_COUNTER);
    unsigned automatic_saves = (after_first_transition - save_before)
        + (after_reversion - (after_first_transition + 1U));
    a_require(save_after == save_before + automatic_saves + 2U,
              "fixed acceptance Necrozma save counter differs");
    f_emit_common(selected, hash, "necrozma-roundtrip",
                  F_PHOTON_GEYSER_MOVE, automatic_saves, 2U, 3U,
                  save_before, save_after,
                  true, true, true, true, true, true, true,
                  false, false, false, false, false, false, false, false);
    a_restore(core, original);
    qol_close(core);
}

static void f_decline_one(struct mCore *core, unsigned ordinal,
                          unsigned form_index, unsigned *witness)
{
    f_open_row(core, ordinal);
    b_press(core, QOL_KEY_A, 30U);
    f_wait_party(core, form_index);
    b_press(core, QOL_KEY_B, 180U);
    b_wait(core);
    a_require(b_field(core),
              "fixed acceptance native decline did not return to field");
    *witness = b_frames;
}

static void f_decline_case(struct mCore *core, struct mCore *original,
                           const struct FCase *selected, const char *hash)
{
    f_prepare_progress_and_map(core, 1U, 36U, 6U, 4U);
    f_prepare_two_mon_party(core, selected->base_species, F_PHOTON_GEYSER_MOVE);
    uint8_t before[200], after[200];
    b_copy(core, QOL_PLAYER_PARTY, before, sizeof(before));
    unsigned save_before = read32(core, P03_SAVE_COUNTER);
    *original = *core;
    a_guard(core);
    f_decline_one(core, 70U, 245U, &f_trace.decline_dusk);
    b_copy(core, QOL_PLAYER_PARTY, after, sizeof(after));
    a_require(!memcmp(before, after, sizeof(after)),
              "fixed acceptance Dusk decline changed party bytes");
    a_require(read32(core, P03_SAVE_COUNTER) == save_before,
              "fixed acceptance Dusk decline changed save counter");
    f_decline_one(core, 71U, 246U, &f_trace.decline_dawn);
    b_copy(core, QOL_PLAYER_PARTY, after, sizeof(after));
    a_require(!memcmp(before, after, sizeof(after)),
              "fixed acceptance Dawn decline changed party bytes");
    unsigned save_after = read32(core, P03_SAVE_COUNTER);
    a_require(save_after == save_before,
              "fixed acceptance Dawn decline changed save counter");
    f_shot(core, "declined-unchanged");
    f_emit_common(selected, hash, "necrozma-decline",
                  F_PHOTON_GEYSER_MOVE, 0U, 0U, 1U,
                  save_before, save_after,
                  true, false, false, true, false, false, false,
                  true, true, true, false, false, false, false, false);
    a_restore(core, original);
    qol_close(core);
}

static void f_prepare_crowned_party(struct mCore *core,
                                    const struct FCase *selected)
{
    clear_parties(core);
    create_mon(core, QOL_PLAYER_PARTY, selected->base_species, 100U);
    write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
    set_mon_data_u32(core, QOL_PLAYER_PARTY, QOL_MON_DATA_HELD_ITEM,
                     selected->held_item);
    set_mon_data_u32(core, QOL_PLAYER_PARTY, QOL_MON_DATA_MOVE1,
                     F_IRON_HEAD_MOVE);
    set_mon_data_u32(core, QOL_PLAYER_PARTY, QOL_MON_DATA_MOVE1 + 1U,
                     f_other_moves[0]);
    set_mon_data_u32(core, QOL_PLAYER_PARTY, QOL_MON_DATA_MOVE1 + 2U,
                     f_other_moves[1]);
    set_mon_data_u32(core, QOL_PLAYER_PARTY, QOL_MON_DATA_MOVE1 + 3U,
                     f_other_moves[2]);
    set_mon_data_u32(core, QOL_PLAYER_PARTY, MON_DATA_PP1, 12U);
    set_mon_data_u32(core, QOL_PLAYER_PARTY, MON_DATA_PP1 + 1U,
                     f_other_pp[0]);
    set_mon_data_u32(core, QOL_PLAYER_PARTY, MON_DATA_PP1 + 2U,
                     f_other_pp[1]);
    set_mon_data_u32(core, QOL_PLAYER_PARTY, MON_DATA_PP1 + 3U,
                     f_other_pp[2]);
    set_mon_data_u32(core, QOL_PLAYER_PARTY, 21U, 0U);
    const unsigned moves[4] = {
        F_IRON_HEAD_MOVE, f_other_moves[0], f_other_moves[1], f_other_moves[2]
    };
    const unsigned pp[4] = {12U, f_other_pp[0], f_other_pp[1], f_other_pp[2]};
    f_bind_mon_layout(core, QOL_PLAYER_PARTY, selected->base_species,
                      selected->held_item, moves, pp);
}

static void f_enter_first_grass_battle(struct mCore *core)
{
    k_path(core, 96U, 5U, k_town_path,
           sizeof(k_town_path) / sizeof(k_town_path[0]), false);
    n_step(core, QOL_KEY_UP);
    b_position(core, 96U, 17U, 11U, 39U);
    k_path(core, 96U, 17U, k_grass_path,
           sizeof(k_grass_path) / sizeof(k_grass_path[0]), true);
    for (unsigned attempt = 0U;
         attempt < 1024U && !read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
         ++attempt) {
        unsigned save1 = b_save1(core);
        unsigned x = read16(core, save1);
        unsigned y = read16(core, save1 + 2U);
        a_require(y == 30U && (x == 14U || x == 15U),
                  "fixed acceptance grass pair differs");
        n_step(core, x == 14U ? QOL_KEY_RIGHT : QOL_KEY_LEFT);
    }
    a_require(n_action(core),
              "fixed acceptance walk did not reach native battle action");
}

static void f_enter_next_grass_battle(struct mCore *core)
{
    for (unsigned attempt = 0U;
         attempt < 1024U && !read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
         ++attempt) {
        unsigned save1 = b_save1(core);
        unsigned x = read16(core, save1);
        unsigned y = read16(core, save1 + 2U);
        a_require(read8(core, save1 + 4U) == 96U
                  && read8(core, save1 + 5U) == 17U
                  && y == 30U && (x == 14U || x == 15U),
                  "fixed acceptance second grass pair differs");
        n_step(core, x == 14U ? QOL_KEY_RIGHT : QOL_KEY_LEFT);
    }
    a_require(n_action(core),
              "fixed acceptance second battle did not reach native action");
}

static void f_normalize_move_cursor(struct mCore *core)
{
    for (unsigned attempt = 0U;
         attempt < 6U && read8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR);
         ++attempt) {
        unsigned cursor = read8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR);
        b_press(core, cursor & 1U ? QOL_KEY_LEFT : QOL_KEY_UP, 12U);
    }
    a_require(!read8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR),
              "fixed acceptance battle move cursor differs");
}

static void f_use_project_move(struct mCore *core,
                               const struct FCase *selected,
                               unsigned *party_pp_after)
{
    a_require(read16(core, ADDR_BATTLE_MONS) == selected->target_species,
              "fixed acceptance crowned battle species differs");
    a_require(read16(core, ADDR_BATTLE_MONS + 0x2EU) == selected->held_item,
              "fixed acceptance crowned battle held item differs");
    a_require(read16(core, ADDR_BATTLE_MONS + BATTLE_MON_MOVES_OFFSET)
                  == selected->project_move,
              "fixed acceptance crowned battle move differs");
    f_trace.project_move_seen = b_frames;
    unsigned pp_before = read8(core,
        ADDR_BATTLE_MONS + BATTLE_MON_PP_OFFSET);
    n_cursor(core, 0U);
    b_press(core, QOL_KEY_A, 60U);
    a_require(read8(core, 0x02022B24U) == 0x14U
              && (read32(core, 0x02023B28U) & 1U),
              "fixed acceptance real move menu absent");
    f_normalize_move_cursor(core);
    b_press(core, QOL_KEY_A, 2U);
    unsigned pp_after = pp_before;
    f_shot(core, "project-move-menu");
    for (unsigned frame = 0U; frame < 18000U; ++frame) {
        /* Only sample the battle struct while the native battle owns it.
         * A winning attack can return directly to the field; demanding another
         * action menu after a KO rejects a valid battle, not a form transition. */
        if (read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER)) {
            unsigned observed = read8(core,
                ADDR_BATTLE_MONS + BATTLE_MON_PP_OFFSET);
            if (observed < pp_after)
                pp_after = observed;
            if (pp_after < pp_before && !f_trace.project_move_spent)
                f_trace.project_move_spent = b_frames;
        }
        if (f_trace.project_move_spent && (n_action(core)
            || (!read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER)
                && b_field(core))))
            break;
        b_frame(core, frame % 60U == 0U ? QOL_KEY_B : 0U);
    }
    a_require(f_trace.project_move_spent && pp_after < pp_before
              && pp_before - pp_after <= 2U,
              "fixed acceptance project move did not spend native PP");
    *party_pp_after = pp_after;
    n_state(core, "project-move-resolved");
    fprintf(stderr, "FIXED_BATTLE base=%u target=%u move=%u pp=%u->%u\n",
            selected->base_species, selected->target_species,
            selected->project_move, pp_before, pp_after);
    f_shot(core, "project-move-resolved");
}

static void f_exit_battle(struct mCore *core)
{
    if (!read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) && b_field(core)) {
        a_require(read8(core, BATTLE_CORE_BATTLE_OUTCOME)
                      == BATTLE_CORE_OUTCOME_WON,
                  "fixed acceptance unexpected automatic battle exit");
    } else {
        if (!n_action(core)) {
            n_state(core, "battle-exit-unresolved");
            f_shot(core, "battle-exit-unresolved");
        }
        a_require(n_action(core),
                  "fixed acceptance battle neither won nor reached action");
        n_cursor(core, 3U);
        b_press(core, QOL_KEY_A, 60U);
        n_return(core, false);
    }
    a_require(b_field(core) && !read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
              "fixed acceptance battle did not return to field");
}

static void f_give_replacement_item(struct mCore *core,
                                    const struct FCase *selected)
{
    k_start(core, 2U);
    a_require(read32(core, BATTLE_CORE_MAIN_CALLBACK2) == P02S_CB2_BAG,
              "fixed acceptance real Bag absent");
    b_press(core, QOL_KEY_A, 120U);
    a_require(read16(core, QOL_SPECIAL_VAR_ITEM) == F_REPLACEMENT_ITEM,
              "fixed acceptance Bag selected another item");
    b_press(core, QOL_KEY_DOWN, 30U);
    b_press(core, QOL_KEY_A, 180U);
    a_require(read32(core, BATTLE_CORE_MAIN_CALLBACK2) == P02S_CB2_PARTY,
              "fixed acceptance Give did not enter real party menu");
    a_require(!read8(core, BATTLE_CORE_SELECTED_PARTY_MON),
              "fixed acceptance Give did not select first party slot");
    b_press(core, QOL_KEY_A, 180U);
    for (unsigned attempt = 0U; attempt < 40U; ++attempt) {
        if (f_held_item(core)
                == F_REPLACEMENT_ITEM)
            break;
        b_press(core, QOL_KEY_A, 120U);
    }
    a_require(f_held_item(core)
                  == F_REPLACEMENT_ITEM,
              "fixed acceptance native held-item replacement failed");
    b_press(core, QOL_KEY_A, 180U);
    for (unsigned attempt = 0U; attempt < 32U && !b_field(core);
         ++attempt)
        b_press(core, QOL_KEY_B, 120U);
    if (!b_field(core)) {
        f_state(core, "item-menu-exit-unresolved");
        f_shot(core, "item-menu-exit-unresolved");
    }
    a_require(b_field(core),
              "fixed acceptance item menus did not return to idle field");
    uint32_t inventory[G_ITEMS];
    g_inventory(core, inventory);
    a_require(inventory[selected->held_item] == 1U
              && inventory[F_REPLACEMENT_ITEM] == 0U,
              "fixed acceptance native held-item inventory boundary differs");
    f_trace.item_replaced = b_frames;
}

static void f_crowned_case(struct mCore *core, struct mCore *original,
                           const struct FCase *selected,
                           const char *rom, const char *save,
                           const char *hash)
{
    f_prepare_progress_and_map(core, 96U, 5U, 24U, 20U);
    f_prepare_crowned_party(core, selected);
    (void)call_preserving(core, 0x0809984DU, 0U, 0U, 0U, 0U);
    uint32_t item_slots = read32(core, 0x020397D8U);
    unsigned fixture_ids[42];
    a_require(p02s_ewram_pointer(item_slots),
              "fixed acceptance item-pocket pointer differs");
    for (unsigned index = 0U; index < 42U; ++index)
        fixture_ids[index] = read16(core, item_slots + 4U * index);
    for (unsigned index = 0U; index < 42U; ++index) {
        if (fixture_ids[index])
            g_remove_fixture(core, fixture_ids[index]);
    }
    a_require(call_preserving(core, QOL_ADD_BAG_ITEM,
                              F_REPLACEMENT_ITEM, 1U, 0U, 0U) == 1U,
              "fixed acceptance replacement item fixture rejected");
    write16(core, BATTLE_CORE_BAG_STATE + 6U, 0U);
    for (unsigned index = 0U; index < 6U; ++index)
        write16(core, BATTLE_CORE_BAG_STATE + 8U + 2U * index, 0U);
    unsigned pid = read32(core, QOL_PLAYER_PARTY);
    unsigned ot = read32(core, QOL_PLAYER_PARTY + 4U);
    unsigned save_before = read32(core, P03_SAVE_COUNTER);
    *original = *core;
    a_guard(core);

    b_frames_run(core, 0U, 60U);
    b_press(core, QOL_KEY_UP, 60U);
    b_position(core, 96U, 5U, 24U, 20U);
    f_enter_first_grass_battle(core);
    f_trace.first_battle = b_frames;
    unsigned pp_after = 0U;
    f_use_project_move(core, selected, &pp_after);
    f_exit_battle(core);
    f_trace.first_battle_exit = b_frames;
    a_require(f_species(core) == selected->base_species
              && f_held_item(core)
                     == selected->held_item
              && f_move(core, 0U)
                     == F_IRON_HEAD_MOVE
              && f_pp(core, 0U) == pp_after
              && read32(core, QOL_PLAYER_PARTY) == pid
              && read32(core, QOL_PLAYER_PARTY + 4U) == ot,
              "fixed acceptance crowned battle exit restoration differs");
    a_require(!f_has_move(core, selected->project_move),
              "fixed acceptance battle-only move persisted after battle");
    f_shot(core, "crowned-restored");

    f_give_replacement_item(core, selected);
    f_shot(core, "rusted-item-removed");
    f_enter_next_grass_battle(core);
    f_trace.second_battle = b_frames;
    a_require(read16(core, ADDR_BATTLE_MONS) == selected->base_species
              && read16(core, ADDR_BATTLE_MONS + 0x2EU)
                     == F_REPLACEMENT_ITEM
              && read16(core, ADDR_BATTLE_MONS + BATTLE_MON_MOVES_OFFSET)
                     == F_IRON_HEAD_MOVE,
              "fixed acceptance held-item removal did not disable crown form");
    for (unsigned slot = 0U; slot < 4U; ++slot)
        a_require(read16(core, ADDR_BATTLE_MONS + BATTLE_MON_MOVES_OFFSET
                                  + 2U * slot) != selected->project_move,
                  "fixed acceptance project move leaked without Rusted item");
    n_cursor(core, 3U);
    b_press(core, QOL_KEY_A, 60U);
    n_return(core, false);
    f_trace.second_battle_exit = b_frames;
    a_require(b_field(core),
              "fixed acceptance second battle did not return to field");
    a_require(f_species(core) == selected->base_species
              && f_held_item(core)
                     == F_REPLACEMENT_ITEM
              && f_move(core, 0U)
                     == F_IRON_HEAD_MOVE
              && !f_has_move(core, selected->project_move),
              "fixed acceptance invalid form/move pair before Save");

    a_require(b_save(core), "fixed acceptance crowned normal Save failed");
    f_trace.first_save = b_frames;
    uint8_t snapshot[100];
    b_copy(core, QOL_PLAYER_PARTY, snapshot, sizeof(snapshot));
    core = f_restart_continue(core, original, rom, save,
                              "fixed acceptance crowned fresh Continue failed");
    f_trace.first_continue = b_frames;
    uint8_t loaded[100];
    b_copy(core, QOL_PLAYER_PARTY, loaded, sizeof(loaded));
    a_require(!memcmp(snapshot, loaded, sizeof(loaded))
              && f_species(core) == selected->base_species
              && f_held_item(core)
                     == F_REPLACEMENT_ITEM
              && f_move(core, 0U)
                     == F_IRON_HEAD_MOVE
              && !f_has_move(core, selected->project_move),
              "fixed acceptance crowned fresh Continue persisted invalid pair");
    f_shot(core, "crowned-continued");
    unsigned save_after = read32(core, P03_SAVE_COUNTER);
    a_require(save_after == save_before + 1U,
              "fixed acceptance crowned save counter differs");
    f_emit_common(selected, hash, "crowned-battle-roundtrip",
                  F_IRON_HEAD_MOVE, 0U, 1U, 2U,
                  save_before, save_after,
                  false, false, false, true, false, true, true,
                  false, false, false, true, true, true, true, true);
    a_restore(core, original);
    qol_close(core);
}

int main(int argc, char **argv)
{
    if (argc == 3 && !strcmp(argv[1], "--guard-check"))
        a_guard_check(argv[2]);
    if (argc != 7)
        return 2;
    const struct FCase *selected = NULL;
    for (unsigned index = 0U; index < sizeof(f_cases) / sizeof(f_cases[0]);
         ++index) {
        if (!strcmp(argv[5], f_cases[index].name))
            selected = &f_cases[index];
    }
    if (selected == NULL)
        return 2;
    f_prefix = argv[6];
    g_prefix = argv[6];
    memset(&f_trace, 0, sizeof(f_trace));
    n_steps = 0U;
    n_outcome = 0U;

    char hash[65], seed[65], after[65];
    sha256_file(argv[1], hash);
    sha256_file(argv[2], seed);
    a_require(!strcmp(hash, F_CANDIDATE_SHA256)
              && !strcmp(hash, argv[3])
              && !strcmp(seed, B_SEED_SHA)
              && !strcmp(seed, argv[4]),
              "fixed acceptance input identity differs");

    struct mLogger logger = {.log = qol_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    p03f_rtc_reserve(argv[2]);
    struct mCore *core = qol_open(argv[1], argv[2]);
    qol_log_core = core;
    core->setVideoBuffer(core, b_video, 240U);
    core->reset(core);
    a_require(a_continue(core),
              "fixed acceptance initial Continue failed");
    a_flash_prepare(core);
    struct mCore original = *core;

    if (selected->kind == F_KIND_NECROZMA) {
        f_necrozma_case(core, &original, selected, argv[1], argv[2], hash);
    } else if (selected->kind == F_KIND_DECLINE) {
        f_decline_case(core, &original, selected, hash);
    } else {
        f_crowned_case(core, &original, selected, argv[1], argv[2], hash);
    }
    qol_log_core = NULL;
    sha256_file(argv[1], after);
    a_require(!strcmp(hash, after) && !log_problem_count,
              "fixed acceptance changed ROM or emulator warned");
    return 0;
}
