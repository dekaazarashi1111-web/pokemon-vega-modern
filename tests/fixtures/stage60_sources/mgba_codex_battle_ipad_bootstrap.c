/*
 * T27 Stage 44 iPad QA save bootstrap.
 *
 * The exact Stage 44 ROM boots a natural new game against a blank physical
 * flash save, enters the authored map through stock warp/load callbacks,
 * creates a six-member QA party, and invokes TrySavingData twice.  A fresh
 * libmGBA core then verifies the unmodified save and each alternating save
 * slot independently before the file is allowed onto the iPad.
 */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define BATTLE_CORE_EMBEDDED
#include "mgba_battle_core_smoke.c"

#include <unistd.h>

enum {
    BOOTSTRAP_SAVE_SIZE = 0x20000U,
    BOOTSTRAP_SLOT_SIZE = 0xE000U,
    BOOTSTRAP_SAVE_BLOCK1_PTR = 0x03005048U,
    BOOTSTRAP_SAVE_BLOCK2_PTR = 0x0300504CU,
    BOOTSTRAP_VMAP = 0x03005080U,
    BOOTSTRAP_PLAYER_PARTY = 0x020241E4U,
    BOOTSTRAP_PLAYER_COUNT = 0x02023F89U,
    BOOTSTRAP_TRY_SAVE = 0x080DB34DU,
    BOOTSTRAP_LOAD_SAVE = 0x080DB4E5U,
    BOOTSTRAP_KANTO_WARP = 0x09220861U,
    BOOTSTRAP_CB2_OVERWORLD = 0x08055E75U,
    BOOTSTRAP_FIELD_CALLBACK = 0x03005060U,
    BOOTSTRAP_DEFAULT_WARP_EXIT = 0x0807D695U,
    BOOTSTRAP_MAP_GROUP = 96U,
    BOOTSTRAP_MAP_NUMBER = 5U,
    BOOTSTRAP_X = 20U,
    BOOTSTRAP_Y = 20U,
    BOOTSTRAP_FIELD_FRAMES = 1800U,
    BOOTSTRAP_TITLE_FRAMES = 1200U,
    BOOTSTRAP_CONTINUE_WAIT_FRAMES = 180U,
    BOOTSTRAP_CONTINUE_PULSES = 24U,
    BOOTSTRAP_MON_SIZE = 100U,
    BOOTSTRAP_TEAM_SIZE = 6U,
    BOOTSTRAP_STATUS_OK = 1U,
    BOOTSTRAP_MAP_VIEW_OFFSET = 0x898U,
    BOOTSTRAP_MAP_VIEW_WIDTH = 15U,
    BOOTSTRAP_MAP_VIEW_HEIGHT = 14U,
    BOOTSTRAP_MAP_VIEW_COUNT = 210U,
};

static const uint16_t bootstrap_species[BOOTSTRAP_TEAM_SIZE] = {
    1U, 4U, 7U, 10U, 11U, 13U,
};

static char bootstrap_slot_paths[2][4096];
static uint16_t bootstrap_expected_map_view[BOOTSTRAP_MAP_VIEW_COUNT];
static const char *bootstrap_phase = "startup";

static void bootstrap_log(struct mLogger *logger, int category,
                          enum mLogLevel level, const char *format,
                          va_list args)
{
    (void)logger;
    if (!(level & (mLOG_FATAL | mLOG_ERROR | mLOG_WARN)))
        return;
    ++log_problem_count;
    if (log_problem_count <= 8U) {
        fprintf(stderr, "mGBA[%s][0x%02x][%s]: ",
                mLogCategoryName(category), (unsigned)level,
                bootstrap_phase);
        vfprintf(stderr, format, args);
        fputc('\n', stderr);
    }
}

static void bootstrap_die(const char *message)
{
    fprintf(stderr, "mgba-codex-battle-ipad-bootstrap: %s\n", message);
    exit(1);
}

static void bootstrap_cleanup(void)
{
    for (unsigned slot = 0U; slot < 2U; ++slot) {
        if (bootstrap_slot_paths[slot][0] != '\0') {
            (void)unlink(bootstrap_slot_paths[slot]);
            bootstrap_slot_paths[slot][0] = '\0';
        }
    }
}

static void bootstrap_write_blank_save(const char *path)
{
    FILE *stream = fopen(path, "wb");
    uint8_t block[4096];
    size_t remaining = BOOTSTRAP_SAVE_SIZE;
    if (!stream)
        bootstrap_die("output save could not be created");
    memset(block, 0xFF, sizeof(block));
    while (remaining != 0U) {
        size_t amount = remaining < sizeof(block) ? remaining : sizeof(block);
        if (fwrite(block, 1U, amount, stream) != amount) {
            (void)fclose(stream);
            bootstrap_die("blank save write failed");
        }
        remaining -= amount;
    }
    if (fclose(stream) != 0)
        bootstrap_die("blank save close failed");
}

static void bootstrap_copy_with_blank_slot(const char *source,
                                            const char *destination,
                                            unsigned blank_slot)
{
    uint8_t *bytes = malloc(BOOTSTRAP_SAVE_SIZE);
    FILE *input;
    FILE *output;
    if (!bytes)
        bootstrap_die("save copy allocation failed");
    input = fopen(source, "rb");
    if (!input || fread(bytes, 1U, BOOTSTRAP_SAVE_SIZE, input)
            != BOOTSTRAP_SAVE_SIZE || fgetc(input) != EOF) {
        if (input)
            (void)fclose(input);
        free(bytes);
        bootstrap_die("generated save size differs");
    }
    if (fclose(input) != 0) {
        free(bytes);
        bootstrap_die("generated save close failed");
    }
    memset(bytes + blank_slot * BOOTSTRAP_SLOT_SIZE, 0xFF,
           BOOTSTRAP_SLOT_SIZE);
    output = fopen(destination, "wb");
    if (!output || fwrite(bytes, 1U, BOOTSTRAP_SAVE_SIZE, output)
            != BOOTSTRAP_SAVE_SIZE) {
        if (output != NULL)
            (void)fclose(output);
        free(bytes);
        bootstrap_die("single-slot save write failed");
    }
    if (fclose(output) != 0) {
        free(bytes);
        bootstrap_die("single-slot save close failed");
    }
    free(bytes);
}

static struct mCore *bootstrap_open_core(const char *rom_path,
                                         const char *save_path,
                                         color_t *video)
{
    static struct mRTCSource rtc = {
        .sample = NULL, .unixTime = fixed_unix_time,
        .serialize = NULL, .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(rom_path);
    if (!core || !core->init(core))
        bootstrap_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, rom_path)
            || !mCoreLoadSaveFile(core, save_path, false))
        bootstrap_die("ROM/save attachment failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    if (video)
        core->setVideoBuffer(core, video, 240U);
    core->reset(core);
    return core;
}

static void bootstrap_close_core(struct mCore *core)
{
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
}

static uint64_t bootstrap_framebuffer_hash(const color_t *video)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    for (unsigned index = 0U; index < 240U * 160U; ++index) {
        uint32_t pixel = (uint32_t)video[index];
        for (unsigned byte = 0U; byte < sizeof(video[index]); ++byte) {
            hash ^= (uint8_t)(pixel >> (byte * 8U));
            hash *= UINT64_C(1099511628211);
        }
    }
    return hash;
}

static unsigned bootstrap_pixel_transitions(const color_t *video)
{
    unsigned transitions = 0U;
    for (unsigned index = 1U; index < 240U * 160U; ++index) {
        if (video[index] != video[index - 1U])
            ++transitions;
    }
    return transitions;
}

static void bootstrap_write_ppm(const char *save_path, const color_t *video)
{
    char path[4096];
    int length = snprintf(path, sizeof(path), "%s.ppm", save_path);
    if (length <= 0 || (size_t)length >= sizeof(path))
        bootstrap_die("framebuffer path formatting failed");
    FILE *stream = fopen(path, "wb");
    if (!stream || fprintf(stream, "P6\n240 160\n255\n") < 0)
        bootstrap_die("framebuffer output open failed");
    for (unsigned index = 0U; index < 240U * 160U; ++index) {
        uint32_t pixel = (uint32_t)video[index];
        uint8_t rgb[3] = {
            (uint8_t)pixel, (uint8_t)(pixel >> 8U),
            (uint8_t)(pixel >> 16U),
        };
        if (fwrite(rgb, 1U, sizeof(rgb), stream) != sizeof(rgb)) {
            (void)fclose(stream);
            bootstrap_die("framebuffer output write failed");
        }
    }
    if (fclose(stream) != 0)
        bootstrap_die("framebuffer output close failed");
}

static void bootstrap_verify_loaded(struct mCore *core, bool render)
{
    uint32_t save1;
    uint32_t save2;
    uint32_t status;
    run_fixed_frames(core);
    status = call_preserving(core, BOOTSTRAP_LOAD_SAVE, 0U, 0U, 0U, 0U);
    if (status != BOOTSTRAP_STATUS_OK)
        bootstrap_die("fresh-core Save_LoadGameData status differs");
    save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
    save2 = read32(core, BOOTSTRAP_SAVE_BLOCK2_PTR);
    if (save1 < 0x02000000U || save1 >= 0x02040000U || (save1 & 3U)
        || save2 < 0x02000000U || save2 >= 0x02040000U || (save2 & 3U)
        || read8(core, save1 + 4U) != BOOTSTRAP_MAP_GROUP
        || read8(core, save1 + 5U) != BOOTSTRAP_MAP_NUMBER
        || read16(core, save1) != BOOTSTRAP_X
        || read16(core, save1 + 2U) != BOOTSTRAP_Y
        || read8(core, BOOTSTRAP_PLAYER_COUNT) != BOOTSTRAP_TEAM_SIZE)
        bootstrap_die("fresh-core field or party state differs");
    for (unsigned index = 0U; index < BOOTSTRAP_MAP_VIEW_COUNT; ++index) {
        if (read16(core, save2 + BOOTSTRAP_MAP_VIEW_OFFSET + index * 2U)
                != bootstrap_expected_map_view[index])
            bootstrap_die("fresh-core saved map view differs");
    }
    for (unsigned slot = 0U; slot < BOOTSTRAP_TEAM_SIZE; ++slot) {
        uint32_t mon = BOOTSTRAP_PLAYER_PARTY + slot * BOOTSTRAP_MON_SIZE;
        if (call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                            mon, 11U, 0U, 0U) != bootstrap_species[slot])
            bootstrap_die("fresh-core party member differs");
    }
    if (render) {
        (void)call_preserving(core, BOOTSTRAP_KANTO_WARP,
                              BOOTSTRAP_MAP_GROUP, BOOTSTRAP_MAP_NUMBER,
                              BOOTSTRAP_X, BOOTSTRAP_Y);
        run_key_frames(core, 0U, BOOTSTRAP_FIELD_FRAMES);
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                != BOOTSTRAP_CB2_OVERWORLD)
            bootstrap_die("fresh-core map did not enter the overworld callback");
    }
}

static void bootstrap_prepare_save_map_view(struct mCore *core)
{
    uint32_t save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
    uint32_t save2 = read32(core, BOOTSTRAP_SAVE_BLOCK2_PTR);
    uint32_t width = read32(core, BOOTSTRAP_VMAP);
    uint32_t height = read32(core, BOOTSTRAP_VMAP + 4U);
    uint32_t map = read32(core, BOOTSTRAP_VMAP + 8U);
    int16_t x;
    int16_t y;
    unsigned index = 0U;
    unsigned distinct = 0U;

    if (save1 < 0x02000000U || save1 >= 0x02040000U || (save1 & 3U)
        || save2 < 0x02000000U || save2 >= 0x02040000U || (save2 & 3U)
        || map < 0x02000000U || map >= 0x02040000U || (map & 1U)
        || width < BOOTSTRAP_MAP_VIEW_WIDTH
        || height < BOOTSTRAP_MAP_VIEW_HEIGHT)
        bootstrap_die("stock SaveMapView ABI is unavailable");
    x = (int16_t)read16(core, save1);
    y = (int16_t)read16(core, save1 + 2U);
    if (x < 0 || y < 0
        || (uint32_t)x + BOOTSTRAP_MAP_VIEW_WIDTH > width
        || (uint32_t)y + BOOTSTRAP_MAP_VIEW_HEIGHT > height)
        bootstrap_die("stock SaveMapView window is outside VMap");

    /* StartMenu_PrepareForSave calls SaveMapView before TrySavingData.  The
     * bootstrap invokes TrySavingData directly, so reproduce that mandatory
     * stock preparation step exactly instead of serializing a blank mapView. */
    for (unsigned row = 0U; row < BOOTSTRAP_MAP_VIEW_HEIGHT; ++row) {
        for (unsigned column = 0U; column < BOOTSTRAP_MAP_VIEW_WIDTH;
             ++column) {
            uint32_t source = map + 2U * (width * ((uint32_t)y + row)
                                      + (uint32_t)x + column);
            uint16_t value = read16(core, source);
            bootstrap_expected_map_view[index] = value;
            write16(core, save2 + BOOTSTRAP_MAP_VIEW_OFFSET + index * 2U,
                    value);
            ++index;
        }
    }
    for (unsigned outer = 0U; outer < BOOTSTRAP_MAP_VIEW_COUNT; ++outer) {
        bool first = true;
        for (unsigned inner = 0U; inner < outer; ++inner) {
            if (bootstrap_expected_map_view[inner]
                    == bootstrap_expected_map_view[outer]) {
                first = false;
                break;
            }
        }
        if (first)
            ++distinct;
    }
    if (index != BOOTSTRAP_MAP_VIEW_COUNT || distinct < 8U)
        bootstrap_die("prepared saved map view is blank or uniform");
}

static void bootstrap_continue_to_field(struct mCore *core)
{
    uint32_t save1;
    uint32_t callback = 0U;

    run_key_frames(core, 0U, BOOTSTRAP_TITLE_FRAMES);
    for (unsigned pulse = 0U; pulse < BOOTSTRAP_CONTINUE_PULSES; ++pulse) {
        /* A advances the title and confirms the default Continue entry.  START
         * is also accepted by the title; use it only for the first pulse so
         * this follows the same user-visible route as the iPad proof. */
        run_key_frames(core, pulse == 0U ? 8U : 1U, 2U);
        run_key_frames(core, 0U, BOOTSTRAP_CONTINUE_WAIT_FRAMES);
        callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
        save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
        if (callback == BOOTSTRAP_CB2_OVERWORLD
            && save1 >= 0x02000000U && save1 < 0x02040000U
            && !(save1 & 3U)
            && read8(core, save1 + 4U) == BOOTSTRAP_MAP_GROUP
            && read8(core, save1 + 5U) == BOOTSTRAP_MAP_NUMBER) {
            run_key_frames(core, 0U, BOOTSTRAP_FIELD_FRAMES);
            return;
        }
    }
    fprintf(stderr,
            "mgba-codex-battle-ipad-bootstrap: natural Continue did not reach "
            "reception (callback=%08" PRIx32 ")\n",
            callback);
    exit(1);
}

static void bootstrap_generate(const char *rom_path, const char *save_path)
{
    struct mCore *core;
    uint32_t save1;
    bootstrap_phase = "generate-blank";
    bootstrap_write_blank_save(save_path);
    core = bootstrap_open_core(rom_path, save_path, NULL);
    bootstrap_phase = "generate-natural-new-game";
    run_trace_prefix(core);
    run_fixed_frames(core);
    save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
    if (save1 < 0x02000000U || save1 >= 0x02040000U || (save1 & 3U))
        bootstrap_die("natural new game did not initialize SaveBlock1");

    bootstrap_phase = "generate-field-warp";
    (void)call_preserving(core, BOOTSTRAP_KANTO_WARP,
                          BOOTSTRAP_MAP_GROUP, BOOTSTRAP_MAP_NUMBER,
                          BOOTSTRAP_X, BOOTSTRAP_Y);
    run_key_frames(core, 0U, BOOTSTRAP_FIELD_FRAMES);
    /* A stock map load may swap the alternating SaveBlock work buffers. */
    save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
    if (save1 < 0x02000000U || save1 >= 0x02040000U || (save1 & 3U))
        bootstrap_die("post-warp SaveBlock1 pointer differs");
    if (read8(core, save1 + 4U) != BOOTSTRAP_MAP_GROUP
        || read8(core, save1 + 5U) != BOOTSTRAP_MAP_NUMBER
        || read16(core, save1) != BOOTSTRAP_X
        || read16(core, save1 + 2U) != BOOTSTRAP_Y
        || read32(core, BATTLE_CORE_MAIN_CALLBACK2) != BOOTSTRAP_CB2_OVERWORLD) {
        fprintf(stderr,
                "bootstrap warp differs: map=%u/%u pos=%u/%u callback=%08" PRIx32
                " expected=%u/%u %u/%u %08x\n",
                read8(core, save1 + 4U), read8(core, save1 + 5U),
                read16(core, save1), read16(core, save1 + 2U),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                BOOTSTRAP_MAP_GROUP, BOOTSTRAP_MAP_NUMBER,
                BOOTSTRAP_X, BOOTSTRAP_Y, BOOTSTRAP_CB2_OVERWORLD);
        bootstrap_die("stock warp/load did not reach the reception map");
    }

    for (unsigned byte = 0U;
         byte < BOOTSTRAP_TEAM_SIZE * BOOTSTRAP_MON_SIZE; ++byte)
        write8(core, BOOTSTRAP_PLAYER_PARTY + byte, 0U);
    for (unsigned slot = 0U; slot < BOOTSTRAP_TEAM_SIZE; ++slot)
        create_mon(core, BOOTSTRAP_PLAYER_PARTY
                         + slot * BOOTSTRAP_MON_SIZE,
                   bootstrap_species[slot], 50U);
    write8(core, BOOTSTRAP_PLAYER_COUNT, BOOTSTRAP_TEAM_SIZE);

    bootstrap_prepare_save_map_view(core);

    bootstrap_phase = "generate-two-saves";
    if (call_preserving(core, BOOTSTRAP_TRY_SAVE, 0U, 0U, 0U, 0U)
            != BOOTSTRAP_STATUS_OK
        || call_preserving(core, BOOTSTRAP_TRY_SAVE, 0U, 0U, 0U, 0U)
            != BOOTSTRAP_STATUS_OK)
        bootstrap_die("two-generation TrySavingData failed");
    bootstrap_close_core(core);
}

#ifndef CODEX_IPAD_BOOTSTRAP_EMBEDDED
int main(int argc, char **argv)
{
    color_t *video;
    struct mCore *core;
    char rom_sha256[65];
    uint64_t framebuffer;
    unsigned transitions;
    if (argc != 3) {
        fprintf(stderr, "usage: %s STAGE44_ROM OUTPUT_SAVE\n", argv[0]);
        return 2;
    }
    if (snprintf(bootstrap_slot_paths[0], sizeof(bootstrap_slot_paths[0]),
                 "%s.slot0-only.tmp", argv[2]) <= 0
        || snprintf(bootstrap_slot_paths[1], sizeof(bootstrap_slot_paths[1]),
                    "%s.slot1-only.tmp", argv[2]) <= 0)
        bootstrap_die("temporary save path formatting failed");
    atexit(bootstrap_cleanup);
    struct mLogger logger = {.log = bootstrap_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);

    bootstrap_generate(argv[1], argv[2]);
    video = calloc(240U * 160U, sizeof(*video));
    if (!video)
        bootstrap_die("framebuffer allocation failed");
    bootstrap_phase = "verify-full-save";
    core = bootstrap_open_core(argv[1], argv[2], video);
    bootstrap_verify_loaded(core, false);
    bootstrap_close_core(core);

    memset(video, 0, 240U * 160U * sizeof(*video));
    bootstrap_phase = "verify-natural-continue";
    core = bootstrap_open_core(argv[1], argv[2], video);
    bootstrap_continue_to_field(core);
    framebuffer = bootstrap_framebuffer_hash(video);
    transitions = bootstrap_pixel_transitions(video);
    bootstrap_write_ppm(argv[2], video);
    bootstrap_close_core(core);
    free(video);
    if (transitions < 100U)
        bootstrap_die("loaded reception framebuffer is blank or uniform");

    /* slot0-only: blank slot 1; slot1-only: blank slot 0. */
    bootstrap_copy_with_blank_slot(argv[2], bootstrap_slot_paths[0], 1U);
    bootstrap_copy_with_blank_slot(argv[2], bootstrap_slot_paths[1], 0U);
    for (unsigned slot = 0U; slot < 2U; ++slot) {
        bootstrap_phase = slot == 0U ? "verify-slot0" : "verify-slot1";
        core = bootstrap_open_core(argv[1], bootstrap_slot_paths[slot], NULL);
        bootstrap_verify_loaded(core, false);
        bootstrap_close_core(core);
    }
    if (log_problem_count != 0U)
        bootstrap_die("mGBA emitted warning/error diagnostics");
    sha256_file(argv[1], rom_sha256);
    printf("{\"schema_version\":1,\"task\":\"T27\",\"status\":\"PASS\","
           "\"rom_sha256\":\"%s\",\"save_size\":%u,"
           "\"save_generations\":2,\"slot0_fresh_load\":true,"
           "\"slot1_fresh_load\":true,\"map\":{\"group\":%u,"
           "\"number\":%u,\"x\":%u,\"y\":%u},"
           "\"party_count\":%u,\"framebuffer_fnv1a64\":\"%016" PRIx64 "\","
           "\"pixel_transitions\":%u,\"warnings\":0}\n",
           rom_sha256, BOOTSTRAP_SAVE_SIZE, BOOTSTRAP_MAP_GROUP,
           BOOTSTRAP_MAP_NUMBER, BOOTSTRAP_X, BOOTSTRAP_Y,
           BOOTSTRAP_TEAM_SIZE, framebuffer, transitions);
    return 0;
}
#endif
