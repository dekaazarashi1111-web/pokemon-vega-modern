/* P03 Stage81 learning UI: four replacement slots, refuse, summary cancel,
 * empty-slot learn and below-level control; native Save and independent Continue.
 * Fixtures use native setters before observation. During the learning scene only
 * keys, frames, callbacks, task state and summary cursor are used (no ROM calls).
 * The representative fixture does not claim breeding or naturally obtained mons.
 */
#include "p03_learning_embedded.c"

enum {
    P03F_SUMMARY_CB = 0x0813868DU,
    P03F_SUMMARY_TASK = 0x08139BA9U,
    P03F_SUMMARY_CURSOR = 0x0203B0E1U,
    P03F_SUMMARY_STATE = 0x3234U,
    P03F_LEARN_ASK = 0x08126705U,
    P03F_STOP_ASK = 0x08126AB9U,
    P03F_PP_BONUSES = 21U,
    P03F_MOVE = 535U,
    P03F_MOVE_PP = 20U,
};

struct P03FTrace {
    unsigned dialog, summary, selection, stop, begin, update, field, down;
    int chosen;
    bool physical_b;
};

static void p03f_rtc_reserve(const char *path)
{
    /* Reserve mGBA 0.10.2's 16-byte RTC trailer BEFORE memory mapping, as in
     * the existing Floette runner. Extending a mapped flash during an RTC write
     * can invalidate currentBank. The original 128-KiB seed is checked first;
     * this modifies only its private copy. 2000-01-01 UTC matches fixed_unix_time.
     */
    const uint8_t rtc[16] = {0,1,1,6,0,0,0,0x40,0x80,0x43,0x6d,0x38,0,0,0,0};
    FILE *stream = fopen(path, "ab");
    p03_require(stream != NULL, "private RTC trailer open failed");
    size_t written = fwrite(rtc, 1U, sizeof(rtc), stream);
    int closed = fclose(stream);
    p03_require(written == sizeof(rtc) && closed == 0, "private RTC reserve failed");
}

static bool p03f_task(struct mCore *core, uint32_t function)
{
    for (unsigned i = 0U; i < 16U; ++i) {
        uint32_t task = QOL_TASKS + i * QOL_TASK_SIZE;
        if (read8(core, task + 4U) && read32(core, task) == function) return true;
    }
    return false;
}

static struct P03FTrace p03f_scene(struct mCore *core, int slot,
                                    bool reject, bool summary_cancel)
{
    struct P03FTrace trace = {.chosen = -1};
    p03_require(p02s_enter_item_party(core, P02S_ITEM_RARE_CANDY, "p03_fullslots"),
                "normal Start/Bag/party input did not reach party menu");
    uint32_t old_callback = 0U;
    unsigned field_stable = 0U;
    for (unsigned frame = 1U; frame <= P02S_MAX_SCENE_FRAMES; ++frame) {
        uint32_t callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
        if (old_callback != callback) {
            fprintf(stderr, "P03F frame=%u callback=%08x\n", frame, callback);
            old_callback = callback;
        }
        if (callback == P02S_CB2_EVOLUTION_BEGIN && !trace.begin) trace.begin = frame;
        if (callback == P02S_CB2_EVOLUTION_UPDATE && !trace.update) trace.update = frame;
        uint16_t key = 0U;
        bool pulse = frame % 30U == 0U;
        if (callback == P03F_SUMMARY_CB) {
            if (!trace.summary) trace.summary = frame;
            uint32_t summary = read32(core, QOL_SUMMARY_DATA_SLOT);
            p03_require(p02s_ewram_pointer(summary) && summary <= 0x0203CC00U,
                        "invalid summary pointer");
            if (p03f_task(core, P03F_SUMMARY_TASK)
                && read8(core, summary + P03F_SUMMARY_STATE) == 2U && pulse
                && !trace.selection) {
                uint8_t cursor = read8(core, P03F_SUMMARY_CURSOR);
                p03_require(cursor <= 4U, "invalid summary selection cursor");
                if (summary_cancel) {
                    key = QOL_KEY_B; trace.selection = frame; trace.chosen = -1;
                } else if ((int)cursor == slot) {
                    key = QOL_KEY_A; trace.selection = frame; trace.chosen = cursor;
                } else {
                    p03_require(slot >= 0 && slot < 4, "unexpected summary screen");
                    key = QOL_KEY_DOWN; ++trace.down;
                    p03_require(trace.down <= 4U, "summary cursor did not advance");
                }
            }
        } else if (callback == P02S_CB2_PARTY && p03f_task(core, P03F_LEARN_ASK)) {
            if (pulse && !trace.dialog) {
                trace.dialog = frame; key = reject ? QOL_KEY_B : QOL_KEY_A;
            }
        } else if (callback == P02S_CB2_PARTY && p03f_task(core, P03F_STOP_ASK)) {
            if (pulse && !trace.stop) {trace.stop = frame; key = QOL_KEY_A;}
        } else if (callback == P02S_CB2_EVOLUTION_UPDATE) {
            if (pulse) {key = QOL_KEY_B; trace.physical_b = true;}
        } else if (trace.begin || trace.update) {
            if (pulse && (callback == P02S_CB2_PARTY || callback == P02S_CB2_BAG
                          || callback == P02S_CB2_FIELD)) key = QOL_KEY_B;
        } else if (frame % 120U == 0U) key = QOL_KEY_A;
        core->setKeys(core, key);
        core->runFrame(core);
        if (callback == P02S_CB2_FIELD) ++field_stable; else field_stable = 0U;
        if (trace.begin && trace.update && field_stable >= 240U
            && read8(core, P02S_FIELD_LOCK) == 0U) {
            core->setKeys(core, 0U);
            trace.field = frame;
            return trace;
        }
    }
    core->setKeys(core, 0U);
    p02s_diagnostic(core, "p03_fullslots", "scene_timeout", P02S_MAX_SCENE_FRAMES,
                    P02S_ITEM_RARE_CANDY);
    p02s_die("full-slot learning/evolution scene timed out");
}

static void p03f_check_mon(struct mCore *core, unsigned level,
                            const unsigned moves[4], const unsigned pp[4])
{
    p03_require(p02s_data(core, P02S_MON_DATA_SPECIES2) == 649U, "species differs");
    p03_require(p02s_data(core, QOL_MON_DATA_LEVEL) == level, "level differs");
    p03_require(p02s_data(core, P03F_PP_BONUSES) == 0U, "PP bonuses differ");
    for (unsigned i = 0U; i < 4U; ++i) {
        unsigned actual_move = p02s_data(core, QOL_MON_DATA_MOVE1 + i);
        unsigned actual_pp = p02s_data(core, MON_DATA_PP1 + i);
        fprintf(stderr, "P03F slot=%u move=%u/%u pp=%u/%u\n", i,
                actual_move, moves[i], actual_pp, pp[i]);
        p03_require(actual_move == moves[i], "move slot differs");
        p03_require(actual_pp == pp[i], "move slot PP differs from canonical/retained PP");
    }
}

int main(int argc, char **argv)
{
    if (argc != 6) {
        fprintf(stderr, "usage: %s ROM PRIVATE_SAVE ROM_SHA SEED_SHA MODE\n", argv[0]);
        return 2;
    }
    const char *mode = argv[5];
    int slot = -1;
    bool reject = strcmp(mode, "reject") == 0;
    bool summary_cancel = strcmp(mode, "cancel-summary") == 0;
    bool empty = strcmp(mode, "empty") == 0;
    bool below = strcmp(mode, "below-level") == 0;
    for (unsigned i = 0U; i < 4U; ++i) {
        char name[16]; snprintf(name, sizeof(name), "replace-%u", i);
        if (strcmp(mode, name) == 0) slot = (int)i;
    }
    p03_require(slot >= 0 || reject || summary_cancel || empty || below, "unknown mode");
    unsigned before[4] = {33U,81U,45U,52U};
    unsigned before_pp[4] = {7U,8U,9U,10U};
    if (empty || below) {
        before[2] = before[3] = before_pp[2] = before_pp[3] = 0U;
    }
    unsigned after[4], after_pp[4];
    memcpy(after, before, sizeof(after)); memcpy(after_pp, before_pp, sizeof(after_pp));
    int learned_slot = empty ? 2 : slot;
    if (learned_slot >= 0) {
        after[learned_slot] = P03F_MOVE; after_pp[learned_slot] = P03F_MOVE_PP;
    }
    unsigned initial = below ? 7U : 8U;
    char rom_sha[65], seed_sha[65];
    sha256_file(argv[1], rom_sha); sha256_file(argv[2], seed_sha);
    p03_require(strcmp(rom_sha, argv[3]) == 0, "ROM SHA mismatch");
    p03_require(strcmp(seed_sha, argv[4]) == 0, "seed SHA mismatch");
    p03f_rtc_reserve(argv[2]);
    struct mLogger logger = {.log = qol_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    static color_t video[240U * 160U];
    struct mCore *core = qol_open(argv[1], argv[2]);
    qol_log_core = core; core->setVideoBuffer(core, video, 240U);
    p03_require(read32(core, 0x080001CCU) == 0x090421F4U
                && read8(core, 0x090421F8U + 12U * P03F_MOVE) == P03F_MOVE_PP,
                "canonical PP table mismatch");
    p03_require(p02s_continue_to_field(core, "p03f_initial"), "normal Continue failed");
    p03_require(p02s_install_field_fixture(core), "fixture field boundary failed");
    p02s_enable_national_dex(core);
    clear_parties(core); create_mon(core, QOL_PLAYER_PARTY, 649U, initial);
    write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
    p02s_set_data(core, P03F_PP_BONUSES, 0U);
    for (unsigned i = 0U; i < 4U; ++i) {
        p02s_set_data(core, QOL_MON_DATA_MOVE1 + i, before[i]);
        p02s_set_data(core, MON_DATA_PP1 + i, before_pp[i]);
    }
    p03f_check_mon(core, initial, before, before_pp);
    p02s_prepare_item(core, P02S_ITEM_RARE_CANDY);
    p03_require(p02s_bag_exact(core, P02S_ITEM_RARE_CANDY, 1U), "initial candy differs");
    fprintf(stderr, "P03F begin observed scene mode=%s\n", mode);
    struct P03FTrace trace = p03f_scene(core, slot, reject, summary_cancel);
    p03_require(trace.begin && trace.begin < trace.update && trace.update < trace.field
                && trace.physical_b, "evolution/cancellation/field ordering missing");
    if (slot >= 0 || summary_cancel) {
        p03_require(trace.dialog && trace.dialog < trace.summary
                    && trace.summary < trace.selection && trace.selection < trace.begin,
                    "replacement/summary-cancel input ordering missing");
        p03_require(trace.chosen == slot, "selected slot differs");
    } else if (reject) {
        p03_require(trace.dialog && !trace.summary && !trace.selection, "reject path differs");
    } else p03_require(!trace.dialog && !trace.summary && !trace.selection,
                       "empty/below-level unexpectedly entered replacement UI");
    if (reject || summary_cancel) {
        p03_require(trace.stop > (summary_cancel ? trace.selection : trace.dialog)
                    && trace.stop < trace.begin, "stop-learning confirmation missing");
    } else p03_require(!trace.stop, "unexpected stop-learning confirmation");
    p03_require(p02s_wait_input_ready_field(core), "field not ready after scene");
    p03f_check_mon(core, initial + 1U, after, after_pp);
    p03_require(p02s_bag_exact(core, P02S_ITEM_RARE_CANDY, 0U), "candy consumption differs");
    unsigned counter_before = read32(core, P03_SAVE_COUNTER);
    p03_require(p03_menu_save(core), "normal Start-menu Save failed");
    unsigned counter_after = read32(core, P03_SAVE_COUNTER);
    p03_require(counter_after == counter_before + 1U, "save counter increment differs");
    qol_close(core); core = NULL; qol_log_core = NULL;
    fprintf(stderr, "P03F original core destroyed; fresh core normal Continue\n");
    core = qol_open(argv[1], argv[2]);
    qol_log_core = core; core->setVideoBuffer(core, video, 240U);
    p03_require(p02s_continue_to_field(core, "p03f_fresh"), "fresh-core Continue failed");
    p03f_check_mon(core, initial + 1U, after, after_pp);
    p03_require(p02s_bag_exact(core, P02S_ITEM_RARE_CANDY, 0U)
                && read32(core, P03_SAVE_COUNTER) == counter_after,
                "fresh Continue item/save-counter mismatch");
    qol_close(core); core = NULL; qol_log_core = NULL;
    sha256_file(argv[1], seed_sha);
    p03_require(strcmp(rom_sha, seed_sha) == 0, "ROM changed");
    p03_require(log_problem_count == 0U, "mGBA warning/error observed");
    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"scope\":\"P03_NATIVE_PP_FULLSLOTS_SAVE_RELOAD_REPRESENTATIVE\","
           "\"mode\":\"%s\",\"rom_sha256\":\"%s\",\"species\":649,"
           "\"initial_level\":%u,\"final_level\":%u,\"learned_slot\":%d,"
           "\"canonical_bug_bite_pp\":20,"
           "\"moves_before\":[%u,%u,%u,%u],\"pp_before\":[%u,%u,%u,%u],"
           "\"moves_after\":[%u,%u,%u,%u],\"pp_after\":[%u,%u,%u,%u],"
           "\"witness\":{\"dialog\":%u,\"summary\":%u,\"selection\":%u,\"stop\":%u,"
           "\"evolution_begin\":%u,\"evolution_update\":%u,\"field\":%u,\"down_presses\":%u},"
           "\"normal_bag_party_input\":true,\"scene_keys_frames_only\":true,"
           "\"evolution_cancel_input\":true,\"normal_save_menu\":true,"
           "\"fresh_core_normal_continue\":true,\"all_slots_pp_persisted\":true,"
           "\"private_rtc_trailer_reserved\":true,\"save_counter_delta\":1,"
           "\"breeding_e2e\":false,\"full_p03_acceptance\":false,"
           "\"release_ready\":false,\"warnings_errors\":0}\n",
           mode, rom_sha, initial, initial + 1U, learned_slot,
           before[0],before[1],before[2],before[3],before_pp[0],before_pp[1],before_pp[2],before_pp[3],
           after[0],after[1],after[2],after[3],after_pp[0],after_pp[1],after_pp[2],after_pp[3],
           trace.dialog,trace.summary,trace.selection,trace.stop,trace.begin,trace.update,trace.field,trace.down);
    return 0;
}
