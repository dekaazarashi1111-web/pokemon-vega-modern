/* Native N-Solarizer/N-Lunarizer owner, not a species-only FORM service.
 * The pinned party_menu.c owner asks which occupied slot to forget; defusion
 * removes/compacts its signature. It NEVER automatically restores Photon Geyser.
 * The fixture's item/partner/progress are explicit. After the seven-write guard
 * only buttons, frames and reads drive fusion, full-slot choice, defusion,
 * ordinary Save and genuinely new-core Continue. Other cases delegate unchanged.
 */
#include "pr16_fixed_form_lifecycle_helpers.c"

struct UTrace {
    unsigned item_entry, bag, party, primary_selection, partner_selection;
    unsigned replace_prompt, summary, replacement_selection, transformed;
    unsigned defuse_entry;
};
static struct UTrace ut;

static unsigned u_item(const struct FCase *selected)
{
    return selected->target_species == 1260U ? 697U : 698U;
}

static unsigned u_partner(const struct FCase *selected)
{
    return selected->target_species == 1260U ? 1189U : 1190U;
}

static void u_state(struct mCore *core, const char *label)
{
    f_state(core, label);
    fprintf(stderr, "FUSION item=%u species=%u count=%u moves=%u,%u,%u,%u "
            "pp=%u,%u,%u,%u bonus=%u quest=%u playback=%u\n",
            read16(core, QOL_SPECIAL_VAR_ITEM), f_species(core),
            read8(core, QOL_PLAYER_PARTY_COUNT), f_move(core, 0U),
            f_move(core, 1U), f_move(core, 2U), f_move(core, 3U),
            f_pp(core, 0U), f_pp(core, 1U), f_pp(core, 2U), f_pp(core, 3U),
            f_pp_bonuses(core), read8(core, P02S_QUEST_LOG_STATE),
            read8(core, P02S_QUEST_LOG_PLAYBACK_STATE));
    for (unsigned index = 0U; index < 16U; ++index) {
        unsigned task = QOL_TASKS + index * QOL_TASK_SIZE;
        if (read8(core, task + 4U))
            fprintf(stderr, "FUSION_TASK id=%u fn=%08x data=%u,%u,%u\n",
                    index, read32(core, task), read16(core, task + 8U),
                    read16(core, task + 10U), read16(core, task + 12U));
    }
}

static void u_choose_slot(struct mCore *core, unsigned slot)
{
    a_require(read32(core, BATTLE_CORE_MAIN_CALLBACK2) == P02S_CB2_PARTY,
              "fusion selection outside native party menu");
    for (unsigned attempt = 0U;
         attempt < 8U && read8(core, F_PARTY_SLOT) != slot; ++attempt)
        b_press(core, QOL_KEY_DOWN, 30U);
    a_require(read8(core, F_PARTY_SLOT) == slot,
              "fusion native party cursor differs");
}

static void u_item_party(struct mCore *core, const struct FCase *selected,
                          bool defuse)
{
    if (defuse)
        ut.defuse_entry = b_frames + 1U;
    else
        f_trace.interaction = ut.item_entry = b_frames + 1U;
    f_open_live_bag(core);
    a_require(read32(core, BATTLE_CORE_MAIN_CALLBACK2) == P02S_CB2_BAG,
              "fusion native Bag absent");
    /* Key Items is pocket index 1. This is a real L/R pocket change after
     * Continue too, never a volatile pocket write after the barrier. */
    for (unsigned attempt = 0U;
         attempt < 5U && read16(core, BATTLE_CORE_BAG_STATE + 6U) != 1U;
         ++attempt)
        b_press(core, QOL_KEY_RIGHT, 90U);
    a_require(read16(core, BATTLE_CORE_BAG_STATE + 6U) == 1U,
              "fusion native Key Items pocket absent");
    if (defuse)
        f_trace.menu = b_frames;
    else
        ut.bag = b_frames;
    f_shot(core, defuse ? "defuse-item" : "fusion-item");
    b_press(core, QOL_KEY_A, 120U);
    a_require(read16(core, QOL_SPECIAL_VAR_ITEM) == u_item(selected),
              "fusion selected another native item");
    b_press(core, QOL_KEY_A, 180U); /* Use, not Give or an injected call. */
    a_require(read32(core, BATTLE_CORE_MAIN_CALLBACK2) == P02S_CB2_PARTY,
              "fusion item Use did not open native party menu");
    if (defuse)
        f_trace.party = b_frames;
    else
        ut.party = b_frames;
    u_state(core, defuse ? "defuse-party" : "fusion-party");
    f_shot(core, defuse ? "defuse-party" : "fusion-party");
    u_choose_slot(core, 1U);
    if (defuse)
        f_trace.selection = b_frames + 1U;
    else
        ut.primary_selection = b_frames + 1U;
    b_press(core, QOL_KEY_A, 180U);
    if (!defuse) {
        a_require(read8(core, QOL_PLAYER_PARTY_COUNT) == 3U
                  && f_species(core) == selected->base_species,
                  "fusion primary selection changed party before partner");
        u_state(core, "fusion-partner-menu");
        f_shot(core, "fusion-partner-menu");
        u_choose_slot(core, 2U);
        ut.partner_selection = b_frames + 1U;
        b_press(core, QOL_KEY_A, 180U);
    }
}

static bool u_complete(struct mCore *core, const struct FCase *selected,
                        bool defuse)
{
    return f_species(core) == (defuse ? selected->base_species
                                    : selected->target_species)
        && read8(core, QOL_PLAYER_PARTY_COUNT) == (defuse ? 3U : 2U)
        && (defuse ? !f_has_move(core, selected->project_move)
                   : (f_move(core, 1U) == selected->project_move
                      && ut.replacement_selection));
}

static void u_wait_scene(struct mCore *core, const struct FCase *selected,
                          bool defuse)
{
    unsigned stable = 0U, downs = 0U;
    uint32_t previous = 0U;
    for (unsigned frame = 1U; frame <= 24000U; ++frame) {
        uint32_t callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
        if (callback != previous) {
            u_state(core, defuse ? "defuse-scene" : "fusion-scene");
            previous = callback;
        }
        unsigned key = 0U;
        bool pulse = frame % 30U == 0U;
        if (callback == P03F_SUMMARY_CB) {
            a_require(!defuse && ut.replace_prompt,
                      "fusion unexpected replacement summary");
            if (!ut.summary) {
                ut.summary = b_frames;
                f_shot(core, "fusion-four-slot-summary");
            }
            uint32_t summary = read32(core, QOL_SUMMARY_DATA_SLOT);
            a_require(p02s_ewram_pointer(summary) && summary <= 0x0203CC00U,
                      "fusion summary pointer outside bound");
            if (!ut.replacement_selection && pulse
                && p03f_task(core, P03F_SUMMARY_TASK)
                && read8(core, summary + P03F_SUMMARY_STATE) == 2U) {
                unsigned cursor = read8(core, P03F_SUMMARY_CURSOR);
                a_require(cursor <= 4U, "fusion invalid summary cursor");
                if (cursor == 1U) {
                    key = QOL_KEY_A;
                    ut.replacement_selection = b_frames + 1U;
                } else {
                    key = QOL_KEY_DOWN;
                    a_require(++downs <= 5U,
                              "fusion replacement cursor did not advance");
                }
            }
        } else if (callback == P02S_CB2_PARTY
                   && p03f_task(core, P03F_LEARN_ASK)) {
            a_require(!defuse, "defusion must not invent a learned move");
            if (!ut.replace_prompt) {
                ut.replace_prompt = b_frames;
                f_shot(core, "fusion-replace-prompt");
            }
            if (pulse)
                key = QOL_KEY_A;
        } else if (callback == P02S_CB2_PARTY
                   && p03f_task(core, P03F_STOP_ASK)) {
            a_die("fusion replacement was cancelled unexpectedly");
        } else if (u_complete(core, selected, defuse)) {
            if (!f_live_field(core) && frame % 120U == 0U)
                key = QOL_KEY_B;
        } else if (callback == P02S_CB2_PARTY && frame % 120U == 0U) {
            key = QOL_KEY_A;
        }
        b_frame(core, key);
        if (u_complete(core, selected, defuse) && f_live_field(core)) {
            if (++stable == 60U) {
                core->setKeys(core, 0U);
                if (defuse)
                    f_trace.transition = f_trace.reversion = b_frames;
                else
                    ut.transformed = b_frames;
                u_state(core, defuse ? "defused-native" : "fused-native");
                f_shot(core, defuse ? "defused-native" : "fused-native");
                return;
            }
        } else {
            stable = 0U;
        }
    }
    u_state(core, "fusion-scene-timeout");
    f_shot(core, "fusion-scene-timeout");
    a_die("fusion owner did not finish its native lifecycle");
}

static void u_check_moves(struct mCore *core, const struct FCase *selected,
                           bool defuse)
{
    const unsigned moves[2][4] = {
        {98U, selected->project_move, 235U, 33U},
        {98U, 235U, 33U, 0U}
    };
    const unsigned pp[2][4] = {
        {11U, f_canonical_pp(core, selected->project_move), 3U, 7U},
        {11U, 3U, 7U, 0U}
    };
    a_require(u_complete(core, selected, defuse),
              "fusion native species/party/owned move boundary differs");
    for (unsigned slot = 0U; slot < 4U; ++slot) {
        a_require(f_move(core, slot) == moves[defuse][slot],
                  "fusion choice/removal/compaction move differs");
        a_require(f_pp(core, slot) == pp[defuse][slot],
                  "fusion choice/removal/compaction PP differs");
    }
    a_require(f_pp_bonuses(core) == (defuse ? 57U : 225U),
              "fusion PP Bonus reset/compaction differs");
    a_require(!f_has_move(core, F_PHOTON_GEYSER_MOVE),
              "fusion owner restored the player-forgotten move");
}

static void u_emit(const struct FCase *selected, const char *hash,
                    unsigned before, unsigned after)
{
    /* Extend, do not reinterpret, the previous fixed-form result schema. */
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"%s\",", F_SCOPE);
    printf("\"case\":\"%s\",\"kind\":\"necrozma-roundtrip\",\"family\":\"%s\",",
           selected->name, selected->family);
    printf("\"route_id\":\"%s\",\"rom_sha256\":\"%s\",", selected->route_id, hash);
    printf("\"form_index\":%u,\"canonical_ordinal\":%u,", selected->form_index, selected->ordinal);
    printf("\"base_species\":%u,\"target_species\":%u,", selected->base_species, selected->target_species);
    printf("\"project_move\":%u,\"auxiliary_move\":%u,", selected->project_move, F_PHOTON_GEYSER_MOVE);
    printf("\"held_item\":0,\"replacement_item\":0,\"automatic_saves\":0,\"manual_saves\":2,\"fresh_cores\":3,");
    printf("\"save_counter_before\":%u,\"save_counter_after\":%u,\"total_frames\":%u,", before, after, b_frames);
    printf("\"native_transition_entry\":true,\"transition_owned_move_resolution\":true,\"four_slot_boundary\":true,");
    printf("\"identity_preserved\":true,\"native_reversion\":true,\"normal_save\":true,\"fresh_continue\":true,");
    printf("\"native_decline_or_ineligible_control\":false,\"party_bytes_unchanged\":false,\"save_counter_unchanged\":false,");
    printf("\"native_held_item_or_battle_entry\":false,\"battle_form_and_move\":false,\"battle_exit_restoration\":false,");
    printf("\"held_item_removal_boundary\":false,\"no_invalid_saved_form_move_pair\":false,");
    printf("\"starting_progress_map_party_are_fixtures\":true,\"held_items_and_bag_are_fixtures\":true,");
    printf("\"input_only_after_guard\":true,\"warnings_errors\":0,\"case_accepted\":true,\"aggregate_gap_closed\":false,");
    printf("\"full_p03_acceptance\":false,\"release_ready\":false,");
    printf("\"entry_kind\":\"NATIVE_FUSION_ITEM\",\"form_service_selection_claimed\":false,");
    printf("\"fusion_item_id\":%u,\"fusion_partner_species\":%u,\"chosen_replacement_slot\":1,", u_item(selected), u_partner(selected));
    printf("\"fusion_partner_restored_exact\":true,\"forgotten_move_not_restored\":true,\"defusion_signature_removed_and_compacted\":true,");
    printf("\"fusion_witness\":{\"item_entry\":%u,\"bag\":%u,\"party\":%u,\"primary_selection\":%u,",
           ut.item_entry, ut.bag, ut.party, ut.primary_selection);
    printf("\"partner_selection\":%u,\"replace_prompt\":%u,\"summary\":%u,\"replacement_selection\":%u,\"transformed\":%u,\"defuse_entry\":%u},",
           ut.partner_selection, ut.replace_prompt, ut.summary, ut.replacement_selection, ut.transformed, ut.defuse_entry);
    printf("\"witness\":{\"interaction\":%u,\"menu\":%u,\"party\":%u,\"selection\":%u,\"transition\":%u,",
           f_trace.interaction, f_trace.menu, f_trace.party, f_trace.selection, f_trace.transition);
    printf("\"first_save\":%u,\"first_continue\":%u,\"reversion\":%u,\"second_save\":%u,\"second_continue\":%u,",
           f_trace.first_save, f_trace.first_continue, f_trace.reversion, f_trace.second_save, f_trace.second_continue);
    printf("\"decline_dusk\":0,\"decline_dawn\":0,\"first_battle\":0,\"project_move_seen\":0,\"project_move_spent\":0,");
    printf("\"first_battle_exit\":0,\"item_replaced\":0,\"second_battle\":0,\"second_battle_exit\":0}}\n");
}

static void u_run(struct mCore *core, struct mCore *original,
                   const struct FCase *selected, const char *rom,
                   const char *save, const char *hash)
{
    f_prepare_progress_and_map(core, 1U, 36U, 6U, 4U);
    f_prepare_two_mon_party(core, selected->base_species, F_PHOTON_GEYSER_MOVE);
    create_mon(core, QOL_PLAYER_PARTY + 200U, u_partner(selected), 50U);
    write8(core, QOL_PLAYER_PARTY_COUNT, 3U);
    (void)call_preserving(core, 0x0809984DU, 0U, 0U, 0U, 0U);
    uint32_t inventory[G_ITEMS];
    g_inventory(core, inventory);
    for (unsigned item = 1U; item < G_ITEMS; ++item) {
        if (inventory[item])
            g_remove_fixture(core, item);
    }
    a_require(call_preserving(core, QOL_ADD_BAG_ITEM, u_item(selected), 1U, 0U, 0U) == 1U,
              "fusion item fixture rejected");
    write16(core, BATTLE_CORE_BAG_STATE + 6U, 1U);
    for (unsigned index = 0U; index < 6U; ++index)
        write16(core, BATTLE_CORE_BAG_STATE + 8U + 2U * index, 0U);
    uint8_t decoy[100], partner[100];
    b_copy(core, QOL_PLAYER_PARTY, decoy, sizeof(decoy));
    b_copy(core, QOL_PLAYER_PARTY + 200U, partner, sizeof(partner));
    unsigned pid = read32(core, F_TARGET_MON), ot = read32(core, F_TARGET_MON + 4U);
    unsigned before = read32(core, P03_SAVE_COUNTER);
    *original = *core;
    a_guard(core);

    u_item_party(core, selected, false);
    u_wait_scene(core, selected, false);
    f_check_identity(core, decoy, pid, ot);
    u_check_moves(core, selected, false);
    a_require(read32(core, P03_SAVE_COUNTER) == before,
              "fusion item unexpectedly changed save counter");
    a_require(b_save(core), "fusion first native Save failed");
    f_trace.first_save = b_frames;
    uint8_t snapshot[300], loaded[300];
    b_copy(core, QOL_PLAYER_PARTY, snapshot, 200U);
    core = f_restart_continue(core, original, rom, save, "fusion first fresh Continue failed");
    f_trace.first_continue = b_frames;
    b_copy(core, QOL_PLAYER_PARTY, loaded, 200U);
    a_require(!memcmp(snapshot, loaded, 200U), "fusion saved party differs after fresh Continue");
    f_check_identity(core, decoy, pid, ot);
    u_check_moves(core, selected, false);
    f_shot(core, "fusion-continued");

    u_item_party(core, selected, true);
    u_wait_scene(core, selected, true);
    f_check_identity(core, decoy, pid, ot);
    u_check_moves(core, selected, true);
    b_copy(core, QOL_PLAYER_PARTY + 200U, loaded, 100U);
    a_require(!memcmp(partner, loaded, 100U), "defusion did not restore exact fused partner");
    g_inventory(core, inventory);
    a_require(inventory[u_item(selected)] == 1U, "fusion consumed its reusable item");
    a_require(read32(core, P03_SAVE_COUNTER) == before + 1U,
              "defusion unexpectedly changed save counter");
    a_require(b_save(core), "defusion second native Save failed");
    f_trace.second_save = b_frames;
    b_copy(core, QOL_PLAYER_PARTY, snapshot, sizeof(snapshot));
    core = f_restart_continue(core, original, rom, save, "defusion second fresh Continue failed");
    f_trace.second_continue = b_frames;
    b_copy(core, QOL_PLAYER_PARTY, loaded, sizeof(loaded));
    a_require(!memcmp(snapshot, loaded, sizeof(loaded)), "defusion saved party differs after fresh Continue");
    f_check_identity(core, decoy, pid, ot);
    u_check_moves(core, selected, true);
    g_inventory(core, inventory);
    a_require(inventory[u_item(selected)] == 1U, "fusion item changed after fresh Continue");
    f_shot(core, "defusion-continued");
    unsigned after = read32(core, P03_SAVE_COUNTER);
    a_require(after == before + 2U, "fusion two-save accounting differs");
    u_emit(selected, hash, before, after);
    a_restore(core, original);
    qol_close(core);
}

int main(int argc, char **argv)
{
    if (argc != 7 || (strcmp(argv[5], f_cases[0].name) && strcmp(argv[5], f_cases[1].name)))
        return fixed_form_parent_main(argc, argv);
    const struct FCase *selected = !strcmp(argv[5], f_cases[0].name) ? &f_cases[0] : &f_cases[1];
    f_prefix = g_prefix = argv[6];
    char hash[65], seed[65], after[65];
    sha256_file(argv[1], hash);sha256_file(argv[2], seed);
    a_require(!strcmp(hash, F_CANDIDATE_SHA256) && !strcmp(hash, argv[3])
              && !strcmp(seed, B_SEED_SHA) && !strcmp(seed, argv[4]),
              "fusion inputs differ from pinned candidate/seed");
    struct mLogger logger = {.log = qol_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    p03f_rtc_reserve(argv[2]);
    struct mCore *core = qol_open(argv[1], argv[2]);
    qol_log_core = core;core->setVideoBuffer(core, b_video, 240U);core->reset(core);
    a_require(a_continue(core), "fusion initial Continue failed");
    a_flash_prepare(core);
    struct mCore original = *core;
    u_run(core, &original, selected, argv[1], argv[2], hash);
    qol_log_core = NULL;sha256_file(argv[1], after);
    a_require(!strcmp(hash, after), "fusion modified immutable candidate ROM");
    a_require(!log_problem_count, "fusion emulator warnings/errors");
    return 0;
}
