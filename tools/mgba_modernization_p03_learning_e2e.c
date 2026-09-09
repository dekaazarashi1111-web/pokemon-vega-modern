/* P03代表経路: 通常入力の技習得、進化取消、保存、新規core Continue。
 * fixtureだけをhostで作り、対象の習得/保存callbackは直接呼び出さない。
 * P03全経路・タマゴ生成・配布仕様の受入には拡大しない。 */
#define main p03_existing_p02_main
#include "mgba_modernization_p02_stage71_acceptance_smoke.c"
#undef main

enum {
    P03_SAVE_ACTION = 4U,
    P03_SAVE_CALLBACK = 0x0806EDB9U,
    P03_SAVE_COUNTER = 0x030053E0U,
};

static void p03_require(bool value, const char *message)
{
    if (!value) p02s_die(message);
}

static bool p03_moves(struct mCore *core, uint16_t learned)
{
    const uint16_t expected[] = {33U, 81U, learned, 0U};
    for (unsigned i = 0U; i < 4U; ++i)
        if (p02s_data(core, QOL_MON_DATA_MOVE1 + i) != expected[i])
            return false;
    return true;
}

static bool p03_menu_save(struct mCore *core)
{
    /* 保存メニューaction/callbackは既存Stage58/61 UI試験と同じnative owner。 */
    uint32_t counter = read32(core, P03_SAVE_COUNTER);
    qol_press(core, QOL_KEY_START, 120U);
    if (read32(core, QOL_START_MENU_CALLBACK) != QOL_START_MENU_INPUT)
        return false;
    uint8_t count = read8(core, QOL_START_MENU_COUNT);
    uint8_t cursor = read8(core, QOL_START_MENU_CURSOR);
    if (count == 0U || count > 9U || cursor >= count) return false;
    uint8_t target = count;
    for (uint8_t i = 0U; i < count; ++i)
        if (read8(core, QOL_START_MENU_ORDER + i) == P03_SAVE_ACTION)
            target = i;
    if (target == count) return false;
    unsigned steps = (unsigned)(target + count - cursor) % count;
    for (unsigned i = 0U; i < steps; ++i)
        qol_press(core, QOL_KEY_DOWN, 30U);
    if (read8(core, QOL_START_MENU_CURSOR) != target) return false;
    qol_press(core, QOL_KEY_A, 120U);
    bool callback_seen = false;
    for (unsigned prompt = 0U; prompt < 32U; ++prompt) {
        uint32_t cb = read32(core, QOL_START_MENU_CALLBACK);
        if (cb == P03_SAVE_CALLBACK) callback_seen = true;
        if (callback_seen && cb == P03_SAVE_CALLBACK
            && read32(core, P03_SAVE_COUNTER) == counter + 1U
            && p02s_input_ready_field(core)) {
            run_key_frames(core, 0U, 180U);
            return p02s_input_ready_field(core);
        }
        qol_press(core, QOL_KEY_A, 180U);
    }
    fprintf(stderr, "P03 save failed: seen=%u counter=%u/%u menu=%08x\n",
            callback_seen, read32(core, P03_SAVE_COUNTER), counter,
            read32(core, QOL_START_MENU_CALLBACK));
    return false;
}

int main(int argc, char **argv)
{
    if (argc != 9) {
        fprintf(stderr, "usage: %s ROM PRIVATE_SAVE ROM_SHA SEED_SHA SPECIES LEVEL MOVE MODE\n", argv[0]);
        return 2;
    }
    uint16_t species = (uint16_t)qol_number(argv[5], "species");
    uint8_t level = (uint8_t)qol_number(argv[6], "level");
    uint16_t move = (uint16_t)qol_number(argv[7], "move");
    bool negative = strcmp(argv[8], "below-level") == 0;
    if (!negative && strcmp(argv[8], "learn") != 0) return 2;
    p03_require(species == 649U && level == 9U && move == 535U,
                "P03固定採用経路とCLIが不一致");
    char rom_sha[65], seed_sha[65];
    sha256_file(argv[1], rom_sha); sha256_file(argv[2], seed_sha);
    p03_require(strcmp(rom_sha, argv[3]) == 0, "ROM SHA mismatch");
    p03_require(strcmp(seed_sha, argv[4]) == 0, "seed SHA mismatch");
    struct mLogger logger = {.log = qol_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    static color_t video[240U * 160U];
    struct mCore *core = qol_open(argv[1], argv[2]);
    qol_log_core = core;
    core->setVideoBuffer(core, video, 240U);
    p03_require(p02s_continue_to_field(core, "p03_initial_continue"), "normal Continue failed");
    p03_require(p02s_install_field_fixture(core), "fixture boundary failed");
    p02s_enable_national_dex(core);
    uint8_t initial_level = level - (negative ? 2U : 1U);
    clear_parties(core);
    create_mon(core, QOL_PLAYER_PARTY, species, initial_level);
    write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
    const uint16_t before[] = {33U, 81U, 0U, 0U};
    for (unsigned i = 0U; i < 4U; ++i) {
        p02s_set_data(core, QOL_MON_DATA_MOVE1 + i, before[i]);
        p02s_set_data(core, MON_DATA_PP1 + i, before[i] ? 10U : 0U);
    }
    p03_require(p03_moves(core, 0U), "target move already present before input");
    p03_require(p02s_data(core, QOL_MON_DATA_LEVEL) == initial_level, "fixture level mismatch");
    p02s_prepare_item(core, P02S_ITEM_RARE_CANDY);
    uint32_t evolution = call_preserving(core, P02S_GET_EVOLUTION_TARGET,
                                         QOL_PLAYER_PARTY, 0U, 0U, 0U);
    p03_require(evolution != 0U && evolution != species, "fixture evolution target unavailable");
    fprintf(stderr, "P03 before-input species=%u level=%u move=%u mode=%s\n",
            species, initial_level, move, argv[8]);
    struct P02SScene scene = p02s_run_item_scene(core, P02S_ITEM_RARE_CANDY,
                            species, (uint16_t)evolution, true, "p03_learning");
    uint16_t expected = negative ? 0U : move;
    p03_require(scene.normal_input && p02s_scene_seen(&scene) && scene.physical_b,
                "normal scheduler/evolution cancellation not observed");
    p03_require(p02s_data(core, QOL_MON_DATA_LEVEL) == initial_level + 1U,
                "normal input level increment differs");
    p03_require(p02s_data(core, P02S_MON_DATA_SPECIES2) == species,
                "cancelled species not retained");
    p03_require(p03_moves(core, expected), "learned move or retained slots differ");
    p03_require(p02s_bag_exact(core, P02S_ITEM_RARE_CANDY, 0U), "candy not consumed exactly once");
    uint32_t pp = p02s_data(core, MON_DATA_PP1 + 2U);
    p03_require(negative ? pp == 0U : pp > 0U, "learned slot PP invalid");
    fprintf(stderr, "P03 after-input level=%u learned=%u pp=%u frames=%u\n",
            initial_level + 1U, expected, pp, scene.frames);
    p03_require(p02s_wait_input_ready_field(core), "field not ready for save");
    p03_require(p03_menu_save(core), "normal Start-menu save failed");
    uint32_t saved_counter = read32(core, P03_SAVE_COUNTER);
    qol_close(core);
    core = NULL; qol_log_core = NULL;
    fprintf(stderr, "P03 original core destroyed; opening independent core\n");
    core = qol_open(argv[1], argv[2]);
    qol_log_core = core;
    core->setVideoBuffer(core, video, 240U);
    p03_require(p02s_continue_to_field(core, "p03_fresh_continue"), "fresh-core normal Continue failed");
    p03_require(p02s_data(core, P02S_MON_DATA_SPECIES2) == species
                && p02s_data(core, QOL_MON_DATA_LEVEL) == initial_level + 1U
                && p03_moves(core, expected)
                && p02s_data(core, MON_DATA_PP1 + 2U) == pp
                && p02s_bag_exact(core, P02S_ITEM_RARE_CANDY, 0U)
                && read32(core, P03_SAVE_COUNTER) == saved_counter,
                "fresh-core reload lost learned mon/item/counter");
    qol_close(core); core = NULL; qol_log_core = NULL;
    sha256_file(argv[1], seed_sha);
    p03_require(strcmp(rom_sha, seed_sha) == 0, "ROM changed during execution");
    p03_require(log_problem_count == 0U, "mGBA warning/error observed");
    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"scope\":\"P03_CATERPIE_LEVELUP_SAVE_RELOAD_REPRESENTATIVE\","
           "\"mode\":\"%s\",\"rom_sha256\":\"%s\","
           "\"species\":%u,\"initial_level\":%u,\"final_level\":%u,"
           "\"expected_move\":%u,\"learned_slot_pp\":%u,"
           "\"normal_bag_party_input\":true,\"evolution_cancel_input\":true,"
           "\"normal_save_menu\":true,\"fresh_core_normal_continue\":true,"
           "\"representative_scheduler_e2e\":true,"
           "\"representative_save_reload_e2e\":true,"
           "\"breeding_e2e\":false,\"full_p03_acceptance\":false,"
           "\"release_ready\":false,\"warnings_errors\":0}\n",
           argv[8], rom_sha, species, initial_level, initial_level + 1U,
           expected, pp);
    return 0;
}
