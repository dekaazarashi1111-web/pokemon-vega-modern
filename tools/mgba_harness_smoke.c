/*
 * T03 Vega harness smoke fixture.
 *
 * The same deterministic libmGBA observation is performed against the pinned
 * 16 MiB Vega reference and the generated 32 MiB harness ROM.  The fixture
 * boots the title, enters new game through the normal UI input path, moves the
 * field avatar, saves through TrySavingData, and reloads the physical save in
 * a fresh core through Save_LoadGameData. It emits numeric observations only
 * and never writes a ROM, savestate, framebuffer, RAM dump, or retained save.
 */
#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include <mgba/core/config.h>
#include <mgba/core/core.h>
#include <mgba/core/log.h>

#define ARRAY_LEN(value) (sizeof(value) / sizeof((value)[0]))
#define MAX_CALL_STEPS UINT64_C(50000000)
#define GBA_WIDTH 240U
#define GBA_HEIGHT 160U
#define SAVE_FILE_SIZE 0x20000U

struct CpuContext {
    int32_t registers[17];
};

struct Observation {
    uint64_t title_framebuffer_fnv1a64;
    uint32_t title_pixel_transitions;
    uint32_t saveblock1;
    int16_t initial_x;
    int16_t initial_y;
    int16_t moved_x;
    int16_t moved_y;
    int8_t map_group;
    int8_t map_number;
    uint16_t movement_key;
    uint32_t save_status;
    uint32_t load_status;
    bool fresh_core_load;
    size_t savedata_size;
    uint64_t savedata_fnv1a64;
};

struct LoadedState {
    uint32_t status;
    uint32_t saveblock1;
    int16_t x;
    int16_t y;
    int8_t map_group;
    int8_t map_number;
};

struct Segment {
    uint32_t frames;
    uint16_t keys;
};

#define A(wait_frames) {2, 1}, {(wait_frames), 0}

/* Vega-compatible natural new-game trace, inherited from the fixed T01
 * emulator fixture. Key bits: A=1, B=2, START=8, RIGHT=16, LEFT=32,
 * UP=64, DOWN=128. */
static const struct Segment BOOT_TRACE[] = {
    {600, 0}, {600, 0}, {1, 8}, {1, 0}, {180, 0}, {300, 0},
    {2, 8}, {2, 0}, {120, 0}, {120, 0}, {2, 1}, {2, 0}, {180, 0},
    A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20),
    A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(120),
    A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20),
    A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(120),
    A(60), A(60), A(60), A(60), A(60), A(60), A(60), A(60), A(60), A(180),
    A(100), A(100), A(100), A(100), A(100), A(100), A(100), A(100), A(100), A(200),
    A(120), A(120), A(120), A(180),
    A(120), A(120), A(120), A(120), A(120), A(200),
    A(120), A(120), A(120), A(120), A(120), A(120), A(120), A(120), A(120), A(300),
    {80, 16}, {10, 0}, {140, 64}, {180, 0}, {2, 2}, {30, 0}, {80, 32}, {120, 0},
    {60, 32}, {10, 0}, {180, 128}, {180, 0},
    {100, 16}, {10, 0}, {220, 128}, {180, 0}, {100, 32}, {10, 0}, {150, 128}, {180, 0},
    {50, 32}, {10, 0}, {80, 128}, {200, 0}, {40, 16}, {10, 0}, {60, 128}, {200, 0},
    {20, 32}, {10, 0}, {40, 64}, {10, 0}, {60, 128}, {200, 0},
    {120, 128}, {60, 32}, {300, 64}, {300, 0}, {180, 16}, {10, 0}, {300, 64}, {300, 0},
    {2, 1}, {120, 0}, {2, 1}, {120, 0}, {2, 1}, {120, 0}, {2, 1}, {120, 0},
    {2, 1}, {120, 0}, {2, 1}, {120, 0}, {2, 1}, {120, 0}, {2, 1}, {120, 0},
    {2, 1}, {120, 0}, {2, 1}, {500, 0},
    {2, 1}, {150, 0}, {2, 1}, {150, 0}, {2, 1}, {200, 0},
    {2, 1}, {150, 0}, {2, 1}, {150, 0}, {2, 1}, {200, 0},
    {2, 1}, {150, 0}, {2, 1}, {200, 0},
    {2, 1}, {150, 0}, {2, 1}, {150, 0}, {2, 1}, {200, 0},
    {2, 1}, {200, 0}, {2, 1}, {200, 0}, {2, 1}, {200, 0}, {2, 1}, {200, 0},
    {2, 1}, {300, 0},
    {60, 128}, {10, 0}, {80, 16}, {10, 0}, {40, 64}, {100, 0},
    {2, 1}, {100, 0}, {60, 16}, {10, 0}, {100, 64}, {100, 0},
    {2, 1}, {180, 0}, {2, 1}, {180, 0}, {2, 1}, {180, 0}, {2, 1}, {200, 0},
    {2, 1}, {180, 0}, {2, 128}, {10, 0}, {2, 1}, {400, 0},
    {2, 1}, {180, 0}, {2, 1}, {180, 0}, {2, 1}, {180, 0}, {2, 1}, {180, 0},
    {2, 1}, {300, 0}, {80, 32}, {10, 0}, {220, 128}, {400, 0},
    {90, 32}, {10, 0}, {220, 128}, {400, 0},
    {2, 1}, {180, 0}, {2, 1}, {180, 0}, {2, 1}, {180, 0}, {2, 1}, {180, 0},
    {2, 1}, {180, 0}, {2, 1}, {400, 0},
    {2, 1}, {160, 0}, {2, 1}, {160, 0}, {2, 1}, {160, 0}, {2, 1}, {160, 0},
    {2, 1}, {160, 0}, {2, 1}, {160, 0}, {2, 1}, {160, 0}, {2, 1}, {160, 0},
    {2, 1}, {160, 0}, {2, 1}, {160, 0}, {2, 1}, {160, 0}, {2, 1}, {160, 0},
    {2, 1}, {160, 0}, {2, 1}, {160, 0}, {2, 1}, {400, 0},
};

static char temporary_save_path[64];
static unsigned log_problem_count;

static void cleanup_save(void) {
    if (temporary_save_path[0] != '\0') {
        unlink(temporary_save_path);
        temporary_save_path[0] = '\0';
    }
}

static void die(const char *message) {
    fprintf(stderr, "mgba-harness-smoke: %s\n", message);
    cleanup_save();
    exit(1);
}

static void strict_log(struct mLogger *logger, int category, enum mLogLevel level,
                       const char *format, va_list args) {
    (void) logger;
    if (!(level & (mLOG_FATAL | mLOG_ERROR | mLOG_WARN))) return;
    ++log_problem_count;
    fprintf(stderr, "mGBA[%s][0x%02x]: ", mLogCategoryName(category), (unsigned) level);
    vfprintf(stderr, format, args);
    fputc('\n', stderr);
}

static time_t fixed_unix_time(struct mRTCSource *source) {
    (void) source;
    return (time_t) 946684800;
}

static uint8_t read8(struct mCore *core, uint32_t address) {
    return (uint8_t) core->rawRead8(core, address, -1);
}

static uint16_t read16(struct mCore *core, uint32_t address) {
    return (uint16_t) core->rawRead16(core, address, -1);
}

static uint32_t read32(struct mCore *core, uint32_t address) {
    return core->rawRead32(core, address, -1);
}

static int32_t read_register(struct mCore *core, const char *name) {
    int32_t value = 0;
    if (!core->readRegister(core, name, &value)) die("register read failed");
    return value;
}

static void write_register(struct mCore *core, const char *name, int32_t value) {
    if (!core->writeRegister(core, name, &value)) die("register write failed");
}

static const char *const REGISTER_NAMES[] = {
    "r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7",
    "r8", "r9", "r10", "r11", "r12", "sp", "lr", "pc", "cpsr",
};

static struct CpuContext capture_cpu(struct mCore *core) {
    struct CpuContext result;
    for (size_t i = 0; i < ARRAY_LEN(REGISTER_NAMES); ++i) {
        result.registers[i] = read_register(core, REGISTER_NAMES[i]);
    }
    return result;
}

static void restore_cpu(struct mCore *core, const struct CpuContext *context) {
    /* CPSR first selects the original register bank; PC is restored last. */
    write_register(core, "cpsr", context->registers[16]);
    for (size_t i = 0; i < 15; ++i) {
        write_register(core, REGISTER_NAMES[i], context->registers[i]);
    }
    write_register(core, "pc", context->registers[15]);
}

static uint32_t call_thumb(struct mCore *core, uint32_t function, uint32_t r0,
                           uint32_t r1, uint32_t r2, uint32_t r3) {
    struct CpuContext original = capture_cpu(core);
    write_register(core, "cpsr", original.registers[16] | 0xA0);
    write_register(core, "lr", (int32_t) 0x08000001U);
    write_register(core, "r0", (int32_t) r0);
    write_register(core, "r1", (int32_t) r1);
    write_register(core, "r2", (int32_t) r2);
    write_register(core, "r3", (int32_t) r3);
    write_register(core, "pc", (int32_t) function);
    uint64_t steps = 0;
    while ((((uint32_t) read_register(core, "pc")) & ~1U) != 0x08000002U) {
        if (++steps > MAX_CALL_STEPS) die("ROM call instruction limit exceeded");
        core->step(core);
    }
    uint32_t result = (uint32_t) read_register(core, "r0");
    restore_cpu(core, &original);
    return result;
}

struct Snapshot {
    size_t size;
    void *bytes;
};

static struct Snapshot take_snapshot(struct mCore *core) {
    struct Snapshot result = {.size = core->stateSize(core), .bytes = NULL};
    result.bytes = malloc(result.size);
    if (!result.bytes || !core->saveState(core, result.bytes)) die("state capture failed");
    return result;
}

static void restore_snapshot(struct mCore *core, const struct Snapshot *snapshot) {
    if (core->stateSize(core) != snapshot->size || !core->loadState(core, snapshot->bytes)) {
        die("state restore failed");
    }
}

static uint64_t fnv1a64(const void *data, size_t size) {
    const uint8_t *bytes = data;
    uint64_t hash = UINT64_C(14695981039346656037);
    for (size_t i = 0; i < size; ++i) {
        hash ^= bytes[i];
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

static uint64_t savedata_file_fingerprint(size_t *size_out, bool *all_ff_out) {
    FILE *file = fopen(temporary_save_path, "rb");
    if (!file) die("temporary save read failed");
    uint8_t buffer[4096];
    uint64_t hash = UINT64_C(14695981039346656037);
    size_t total = 0;
    bool all_ff = true;
    size_t count;
    while ((count = fread(buffer, 1, sizeof(buffer), file)) != 0) {
        for (size_t i = 0; i < count; ++i) {
            if (buffer[i] != 0xFF) all_ff = false;
            hash ^= buffer[i];
            hash *= UINT64_C(1099511628211);
        }
        total += count;
    }
    if (ferror(file) || fclose(file) != 0) die("temporary save read failed");
    *size_out = total;
    *all_ff_out = all_ff;
    return hash;
}

static void run_frames(struct mCore *core, uint32_t count, uint16_t keys) {
    core->setKeys(core, keys);
    for (uint32_t frame = 0; frame < count; ++frame) core->runFrame(core);
    core->setKeys(core, 0);
}

static void run_boot_trace(struct mCore *core, color_t *video, uint32_t title_checkpoint,
                           uint32_t trace_segments, struct Observation *result) {
    if (!trace_segments || trace_segments > ARRAY_LEN(BOOT_TRACE)) {
        die("trace segment count is outside the fixed natural trace");
    }
    uint32_t elapsed = 0;
    bool captured = false;
    for (size_t segment = 0; segment < trace_segments; ++segment) {
        uint32_t frames = BOOT_TRACE[segment].frames;
        if (!captured && elapsed < title_checkpoint && title_checkpoint < elapsed + frames) {
            run_frames(core, title_checkpoint - elapsed, BOOT_TRACE[segment].keys);
            frames -= title_checkpoint - elapsed;
            elapsed = title_checkpoint;
        }
        if (!captured && elapsed == title_checkpoint) {
            result->title_framebuffer_fnv1a64 = fnv1a64(
                video, GBA_WIDTH * GBA_HEIGHT * sizeof(*video));
            for (size_t i = 1; i < GBA_WIDTH * GBA_HEIGHT; ++i) {
                if (video[i] != video[i - 1]) ++result->title_pixel_transitions;
            }
            captured = true;
        }
        run_frames(core, frames, BOOT_TRACE[segment].keys);
        elapsed += frames;
    }
    if (!captured || result->title_pixel_transitions < 100) {
        die("title checkpoint is blank, uniform, or outside the trace");
    }
}

static void initialize_temporary_save(void) {
    strcpy(temporary_save_path, "/tmp/t03-harness-save-XXXXXX");
    int descriptor = mkstemp(temporary_save_path);
    if (descriptor < 0) die("temporary save creation failed");
    uint8_t block[4096];
    memset(block, 0xFF, sizeof(block));
    size_t remaining = SAVE_FILE_SIZE;
    while (remaining) {
        size_t amount = remaining < sizeof(block) ? remaining : sizeof(block);
        ssize_t written = write(descriptor, block, amount);
        if (written != (ssize_t) amount) {
            close(descriptor);
            die("temporary save initialization failed");
        }
        remaining -= amount;
    }
    if (close(descriptor) != 0) die("temporary save close failed");
}

static uint32_t parse_u32(const char *text, const char *label) {
    errno = 0;
    char *end = NULL;
    unsigned long value = strtoul(text, &end, 0);
    if (errno || !end || *end || value > UINT32_MAX) {
        fprintf(stderr, "mgba-harness-smoke: invalid %s\n", label);
        exit(2);
    }
    return (uint32_t) value;
}

static struct LoadedState load_from_fresh_core(
    const char *rom_path, uint32_t save_load_game_data, uint32_t g_saveblock1,
    uint32_t settle_frames
) {
    struct LoadedState result = {0};
    struct mRTCSource rtc = {
        .sample = NULL,
        .unixTime = fixed_unix_time,
        .serialize = NULL,
        .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(rom_path);
    if (!core || !core->init(core)) die("fresh load core initialization failed");
    if (!mCoreLoadFile(core, rom_path)) die("fresh load ROM failed");
    if (!mCoreLoadSaveFile(core, temporary_save_path, false)) {
        die("fresh load save attachment failed");
    }
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    run_frames(core, settle_frames, 0);
    result.status = call_thumb(core, save_load_game_data, 0, 0, 0, 0);
    result.saveblock1 = read32(core, g_saveblock1);
    if (result.saveblock1 < 0x02000000U || result.saveblock1 >= 0x02040000U
        || (result.saveblock1 & 3U)) {
        die("fresh load did not initialize SaveBlock1");
    }
    result.x = (int16_t) read16(core, result.saveblock1);
    result.y = (int16_t) read16(core, result.saveblock1 + 2U);
    result.map_group = (int8_t) read8(core, result.saveblock1 + 4U);
    result.map_number = (int8_t) read8(core, result.saveblock1 + 5U);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return result;
}

static struct Observation observe(
    const char *rom_path, uint32_t try_saving_data,
    uint32_t save_load_game_data, uint32_t g_saveblock1,
    uint32_t title_frames, uint32_t trace_segments, uint32_t settle_frames,
    uint32_t movement_frames,
    const uint16_t *movement_keys, size_t movement_key_count, uint32_t save_status_ok
) {
    struct Observation result = {0};
    struct mRTCSource rtc = {
        .sample = NULL,
        .unixTime = fixed_unix_time,
        .serialize = NULL,
        .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(rom_path);
    if (!core || !core->init(core)) die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, rom_path)) die("ROM load failed");
    initialize_temporary_save();
    if (!mCoreLoadSaveFile(core, temporary_save_path, false)) die("temporary save load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    color_t *video = calloc(GBA_WIDTH * GBA_HEIGHT, sizeof(*video));
    if (!video) die("video buffer allocation failed");
    core->setVideoBuffer(core, video, GBA_WIDTH);
    core->reset(core);

    run_boot_trace(core, video, title_frames, trace_segments, &result);
    run_frames(core, settle_frames, 0);
    result.saveblock1 = read32(core, g_saveblock1);
    if (result.saveblock1 < 0x02000000U || result.saveblock1 >= 0x02040000U
        || (result.saveblock1 & 3U)) {
        die("new game did not initialize SaveBlock1");
    }
    result.initial_x = (int16_t) read16(core, result.saveblock1);
    result.initial_y = (int16_t) read16(core, result.saveblock1 + 2U);
    result.map_group = (int8_t) read8(core, result.saveblock1 + 4U);
    result.map_number = (int8_t) read8(core, result.saveblock1 + 5U);
    if (result.map_group < 0 || result.map_number < 0) die("new game map is invalid");

    struct Snapshot field = take_snapshot(core);
    bool moved = false;
    for (size_t i = 0; i < movement_key_count; ++i) {
        restore_snapshot(core, &field);
        run_frames(core, movement_frames, movement_keys[i]);
        run_frames(core, 4, 0);
        int16_t x = (int16_t) read16(core, result.saveblock1);
        int16_t y = (int16_t) read16(core, result.saveblock1 + 2U);
        int8_t group = (int8_t) read8(core, result.saveblock1 + 4U);
        int8_t number = (int8_t) read8(core, result.saveblock1 + 5U);
        if ((x != result.initial_x || y != result.initial_y)
            && group == result.map_group && number == result.map_number) {
            result.moved_x = x;
            result.moved_y = y;
            result.movement_key = movement_keys[i];
            moved = true;
            break;
        }
    }
    free(field.bytes);
    if (!moved) {
        fprintf(stderr, "fixture field state: map=%d/%d pos=%d,%d\n",
                result.map_group, result.map_number, result.initial_x, result.initial_y);
        die("field avatar did not move through any tested direction");
    }

    result.save_status = call_thumb(core, try_saving_data, 0, 0, 0, 0);
    if (result.save_status != save_status_ok) die("TrySavingData failed");
    bool all_ff = true;
    result.savedata_fnv1a64 = savedata_file_fingerprint(
        &result.savedata_size, &all_ff);
    if (all_ff) die("save operation left flash blank");

    free(video);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    struct LoadedState loaded = load_from_fresh_core(
        rom_path, save_load_game_data, g_saveblock1, settle_frames);
    result.load_status = loaded.status;
    result.fresh_core_load = true;
    if (loaded.status != save_status_ok
        || loaded.x != result.moved_x || loaded.y != result.moved_y
        || loaded.map_group != result.map_group
        || loaded.map_number != result.map_number) {
        die("fresh-core Save_LoadGameData did not restore field state");
    }
    cleanup_save();
    return result;
}

static bool observations_equal(const struct Observation *left,
                               const struct Observation *right) {
    return left->title_framebuffer_fnv1a64 == right->title_framebuffer_fnv1a64
        && left->title_pixel_transitions == right->title_pixel_transitions
        && left->initial_x == right->initial_x
        && left->initial_y == right->initial_y
        && left->moved_x == right->moved_x
        && left->moved_y == right->moved_y
        && left->map_group == right->map_group
        && left->map_number == right->map_number
        && left->movement_key == right->movement_key
        && left->save_status == right->save_status
        && left->load_status == right->load_status
        && left->fresh_core_load == right->fresh_core_load
        && left->savedata_size == right->savedata_size
        && left->savedata_fnv1a64 == right->savedata_fnv1a64;
}

static void print_observation(const struct Observation *value) {
    printf("{\"title_framebuffer_fnv1a64\":\"%016" PRIx64
           "\",\"title_pixel_transitions\":%" PRIu32
           ",\"new_game\":{\"map_group\":%d,\"map_number\":%d,"
           "\"x\":%d,\"y\":%d},\"movement\":{\"key\":%u,"
           "\"x\":%d,\"y\":%d},\"save\":{\"status\":%" PRIu32
           ",\"size\":%zu,\"fnv1a64\":\"%016" PRIx64
           "\"},\"load\":{\"status\":%" PRIu32
           ",\"restored\":true,\"fresh_core\":true}}",
           value->title_framebuffer_fnv1a64, value->title_pixel_transitions,
           value->map_group, value->map_number, value->initial_x, value->initial_y,
           value->movement_key, value->moved_x, value->moved_y, value->save_status,
           value->savedata_size, value->savedata_fnv1a64, value->load_status);
}

int main(int argc, char **argv) {
    if (argc != 13) {
        fprintf(stderr,
                "usage: %s REFERENCE_ROM CANDIDATE_ROM TRY_SAVE LOAD_SAVE "
                "G_SAVEBLOCK1 TITLE_FRAMES TRACE_SEGMENTS SETTLE_FRAMES MOVEMENT_FRAMES "
                "SAVE_STATUS_OK MOVEMENT_KEYS_CSV EXPECTED_TITLE_FNV1A64\n",
                argv[0]);
        return 2;
    }
    uint32_t try_save = parse_u32(argv[3], "TrySavingData");
    uint32_t load_save = parse_u32(argv[4], "Save_LoadGameData");
    uint32_t g_saveblock1 = parse_u32(argv[5], "gSaveBlock1");
    uint32_t title_frames = parse_u32(argv[6], "title_frames");
    uint32_t trace_segments = parse_u32(argv[7], "trace_segments");
    uint32_t settle_frames = parse_u32(argv[8], "settle_frames");
    uint32_t movement_frames = parse_u32(argv[9], "movement_frames");
    uint32_t save_status_ok = parse_u32(argv[10], "save_status_ok");
    uint16_t movement_keys[8];
    size_t movement_key_count = 0;
    char keys_text[128];
    if (strlen(argv[11]) >= sizeof(keys_text)) die("movement key list is too long");
    strcpy(keys_text, argv[11]);
    for (char *token = strtok(keys_text, ","); token; token = strtok(NULL, ",")) {
        if (movement_key_count >= ARRAY_LEN(movement_keys)) die("too many movement keys");
        uint32_t key = parse_u32(token, "movement key");
        if (!key || key > UINT16_MAX) die("movement key is invalid");
        movement_keys[movement_key_count++] = (uint16_t) key;
    }
    if (!movement_key_count) die("movement key list is empty");
    if (strlen(argv[12]) != 16 || strspn(argv[12], "0123456789abcdef") != 16) {
        die("expected title FNV-1a64 must be 16 lowercase hex digits");
    }

    struct mLogger logger = {.log = strict_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    atexit(cleanup_save);
    struct Observation reference = observe(
        argv[1], try_save, load_save, g_saveblock1,
        title_frames, trace_segments, settle_frames, movement_frames, movement_keys,
        movement_key_count, save_status_ok);
    struct Observation candidate = observe(
        argv[2], try_save, load_save, g_saveblock1,
        title_frames, trace_segments, settle_frames, movement_frames, movement_keys,
        movement_key_count, save_status_ok);
    if (log_problem_count != 0) die("mGBA emitted warning/error diagnostics");
    char observed_title[17];
    snprintf(observed_title, sizeof(observed_title), "%016" PRIx64,
             reference.title_framebuffer_fnv1a64);
    if (strcmp(observed_title, argv[12]) != 0) die("title checkpoint fingerprint mismatch");
    if (!observations_equal(&reference, &candidate)) {
        die("reference and candidate observations differ");
    }
    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"measurement\":\"libmGBA_reference_candidate_behavior\","
           "\"checks\":{\"title\":true,\"new_game\":true,"
           "\"basic_map_movement\":true,\"save\":true,\"load\":true,"
           "\"observable_equivalence\":true},\"reference\":");
    print_observation(&reference);
    printf(",\"candidate\":");
    print_observation(&candidate);
    printf(",\"artifacts_written\":[]}\n");
    return 0;
}
