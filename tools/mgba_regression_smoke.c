/* T17 exact-ROM smoke: boot stage17, validate repointed Kanto roots, and execute
 * the embedded QOL-B Thumb probe. No ROM/save/state/framebuffer artifact is written. */
#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include <mgba/core/config.h>
#include <mgba/core/core.h>
#include <mgba/core/log.h>

#define GBA_WIDTH 240U
#define GBA_HEIGHT 160U
#define MAX_CALL_STEPS UINT64_C(2000000)
#define ROM_BASE UINT32_C(0x08000000)
#define ROM_END UINT32_C(0x0A000000)
#define SPECIAL_VAR_RESULT UINT32_C(0x02037004)
#define QOL_MARKER UINT32_C(0x00000B17)
#define G_SAVE_BLOCK1 UINT32_C(0x03005048)
#define GLOBAL_RNG UINT32_C(0x03005040)
#define MAIN_CALLBACK2 UINT32_C(0x03003134)
#define SCRIPT_CONTEXT1_SETUP UINT32_C(0x080693A5)
#define GET_MON_DATA UINT32_C(0x0803F355)
#define GET_SPECIES_NAME UINT32_C(0x080406C5)
#define IDENTITY_NICKNAME_SCRATCH UINT32_C(0x0203E800)
#define IDENTITY_CANONICAL_SCRATCH UINT32_C(0x0203E820)
#define IDENTITY_MON_DATA_NICKNAME 2U
#define IDENTITY_NAME_SIZE 11U
#define ADD_BAG_ITEM UINT32_C(0x08099A8D)
#define FLAG_CLEAR UINT32_C(0x0806DE9D)
#define CREATE_TASK UINT32_C(0x08076BB5)
#define ITEM_USE_ON_FIELD_CALLBACK UINT32_C(0x02039910)
#define ENEMY_PARTY UINT32_C(0x02023F8C)
#define ENEMY_PARTY_COUNT UINT32_C(0x02023F8A)
#define PARTY_BYTES 600U
#define WILD_OVERLAY_CALLS 4096U
#define ECOLOGY_ENTRY_SIZE 104U
#define ECOLOGY_ITEM_ADDRESS UINT32_C(0x09050768)

static void die(const char *message)
{
    fprintf(stderr, "mgba-regression-smoke: %s\n", message);
    exit(1);
}

static void silent_log(struct mLogger *logger, int category, enum mLogLevel level,
                       const char *format, va_list args)
{
    (void)logger;
    (void)category;
    (void)level;
    (void)format;
    (void)args;
}

static uint32_t parse_u32(const char *text, const char *label)
{
    errno = 0;
    char *end = NULL;
    unsigned long value = strtoul(text, &end, 0);
    if (errno || end == NULL || *end != '\0' || value > UINT32_MAX) {
        fprintf(stderr, "mgba-regression-smoke: invalid %s\n", label);
        exit(2);
    }
    return (uint32_t)value;
}

static uint8_t read8(struct mCore *core, uint32_t address)
{
    return (uint8_t)core->rawRead8(core, address, -1);
}

static uint16_t read16(struct mCore *core, uint32_t address)
{
    return (uint16_t)core->rawRead16(core, address, -1);
}

static uint16_t read_le16_unaligned(struct mCore *core, uint32_t address)
{
    return (uint16_t)(read8(core, address)
        | ((uint16_t)read8(core, address + 1U) << 8U));
}

static uint32_t read32(struct mCore *core, uint32_t address)
{
    return core->rawRead32(core, address, -1);
}

static void write8(struct mCore *core, uint32_t address, uint8_t value)
{
    core->rawWrite8(core, address, -1, value);
}

static void write32(struct mCore *core, uint32_t address, uint32_t value)
{
    core->rawWrite32(core, address, -1, value);
}

static int32_t read_register(struct mCore *core, const char *name)
{
    int32_t value = 0;
    if (!core->readRegister(core, name, &value))
        die("register read failed");
    return value;
}

static void write_register(struct mCore *core, const char *name, int32_t value)
{
    if (!core->writeRegister(core, name, &value))
        die("register write failed");
}

static const char *const REGISTER_NAMES[] = {
    "r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7",
    "r8", "r9", "r10", "r11", "r12", "sp", "lr", "pc", "cpsr",
};

struct CpuContext {
    int32_t registers[17];
};

struct Segment {
    uint32_t frames;
    uint16_t keys;
};

#define A(wait_frames) {2, 1}, {(wait_frames), 0}

/* Fixed natural Vega new-game path shared with the T03 behavior fixture.
 * Key bits: A=1, B=2, START=8, RIGHT=16, LEFT=32, UP=64, DOWN=128. */
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

static struct CpuContext capture_cpu(struct mCore *core)
{
    struct CpuContext result;
    for (size_t index = 0; index < 17; ++index)
        result.registers[index] = read_register(core, REGISTER_NAMES[index]);
    return result;
}

static void restore_cpu(struct mCore *core, const struct CpuContext *context)
{
    write_register(core, "cpsr", context->registers[16]);
    for (size_t index = 0; index < 15; ++index)
        write_register(core, REGISTER_NAMES[index], context->registers[index]);
    write_register(core, "pc", context->registers[15]);
}

static uint32_t call_thumb(struct mCore *core, uint32_t function,
                           uint32_t r0, uint32_t r1, uint32_t r2, uint32_t r3)
{
    struct CpuContext original = capture_cpu(core);
    write_register(core, "cpsr", original.registers[16] | 0xA0);
    write_register(core, "lr", (int32_t)UINT32_C(0x08000001));
    write_register(core, "r0", (int32_t)r0);
    write_register(core, "r1", (int32_t)r1);
    write_register(core, "r2", (int32_t)r2);
    write_register(core, "r3", (int32_t)r3);
    write_register(core, "pc", (int32_t)function);
    uint64_t steps = 0;
    while ((((uint32_t)read_register(core, "pc")) & ~1U) != UINT32_C(0x08000002)) {
        if (++steps > MAX_CALL_STEPS) {
            fprintf(stderr,
                    "mgba-regression-smoke: direct call instruction limit "
                    "function=%08" PRIX32 " pc=%08" PRIX32 "\n",
                    function, (uint32_t)read_register(core, "pc"));
            exit(1);
        }
        core->step(core);
    }
    uint32_t result = (uint32_t)read_register(core, "r0");
    restore_cpu(core, &original);
    return result;
}

static void verify_canonical_nickname(struct mCore *core,
                                      uint32_t mon, uint16_t species)
{
    bool terminated = false;
    for (unsigned index = 0U; index < IDENTITY_NAME_SIZE; ++index) {
        write8(core, IDENTITY_NICKNAME_SCRATCH + index, 0U);
        write8(core, IDENTITY_CANONICAL_SCRATCH + index, 0U);
    }
    (void)call_thumb(core, GET_MON_DATA, mon, IDENTITY_MON_DATA_NICKNAME,
                     IDENTITY_NICKNAME_SCRATCH, 0U);
    (void)call_thumb(core, GET_SPECIES_NAME,
                     IDENTITY_CANONICAL_SCRATCH, species, 0U, 0U);
    for (unsigned index = 0U; index < IDENTITY_NAME_SIZE; ++index) {
        uint8_t nickname = read8(core, IDENTITY_NICKNAME_SCRATCH + index);
        uint8_t canonical = read8(core, IDENTITY_CANONICAL_SCRATCH + index);
        if (nickname != canonical) {
            fprintf(stderr,
                    "nickname mismatch species=%u index=%u actual=%02X expected=%02X\n",
                    species, index, nickname, canonical);
            die("generated wild nickname differs from canonical Species name");
        }
        if (canonical == 0xFFU) {
            terminated = true;
            break;
        }
    }
    if (!terminated)
        die("canonical Species name is unterminated");
}

static bool rom_pointer(uint32_t pointer)
{
    return pointer >= ROM_BASE && pointer < ROM_END && (pointer & 3U) == 0;
}

static bool rom_code_pointer(uint32_t pointer)
{
    pointer &= ~1U;
    return pointer >= ROM_BASE && pointer < ROM_END && (pointer & 1U) == 0;
}

static uint32_t find_ecology_entry(struct mCore *core, uint32_t table,
                                   uint32_t count, uint8_t group, uint8_t map,
                                   uint8_t area, uint8_t layer)
{
    for (uint32_t index = 0; index < count; ++index) {
        uint32_t entry = table + index * ECOLOGY_ENTRY_SIZE;
        if (read8(core, entry) == group && read8(core, entry + 1U) == map
            && read8(core, entry + 2U) == area
            && read8(core, entry + 3U) == layer)
            return entry;
    }
    return 0;
}

static bool ecology_entry_has_species(struct mCore *core, uint32_t entry,
                                       uint16_t species)
{
    uint8_t count = read8(core, entry + 5U);
    for (uint8_t index = 0; index < count; ++index) {
        if (species == read_le16_unaligned(core, entry + 8U + index * 2U))
            return true;
    }
    return false;
}

static void run_frames(struct mCore *core, unsigned count, uint16_t keys)
{
    core->setKeys(core, keys);
    for (unsigned frame = 0; frame < count; ++frame)
        core->runFrame(core);
    core->setKeys(core, 0);
}

static uint32_t run_natural_new_game(struct mCore *core, color_t *video)
{
    const uint32_t title_checkpoint = 1682U;
    uint32_t elapsed = 0;
    uint32_t transitions = 0;
    bool captured = false;
    for (size_t segment = 0; segment < sizeof(BOOT_TRACE) / sizeof(BOOT_TRACE[0]); ++segment) {
        uint32_t frames = BOOT_TRACE[segment].frames;
        if (!captured && elapsed < title_checkpoint
            && title_checkpoint < elapsed + frames) {
            run_frames(core, title_checkpoint - elapsed, BOOT_TRACE[segment].keys);
            frames -= title_checkpoint - elapsed;
            elapsed = title_checkpoint;
        }
        if (!captured && elapsed == title_checkpoint) {
            for (size_t index = 1; index < GBA_WIDTH * GBA_HEIGHT; ++index) {
                if (video[index] != video[index - 1])
                    ++transitions;
            }
            captured = true;
        }
        run_frames(core, frames, BOOT_TRACE[segment].keys);
        elapsed += frames;
    }
    run_frames(core, 120, 0);
    if (!captured || transitions < 100U)
        die("title checkpoint is blank or outside the natural trace");
    return transitions;
}

int main(int argc, char **argv)
{
    if (argc != 21 && argc != 22) {
        fprintf(stderr, "usage: %s ROM QOL_PROBE MAP_ROOT LAYOUT_ROOT WILD_ROOT PAYLOAD_SIZE PORTAL_TRAVEL RETURN_TRAVEL TRAINER_ROOT PEWTER_SCRIPT CHAMPION_SCRIPT WILD_SELECT WILD_TRY_GENERATE WILD_FISHING WILD_SET_MODE WILD_GET_MODE WILD_HIDDEN WILD_FIELD_USE WILD_OVERLAY_TABLE WILD_OVERLAY_COUNT [VERMILION_EVENT_OBJECTS]\n",
                argv[0]);
        return 2;
    }
    uint32_t probe = parse_u32(argv[2], "QOL probe");
    uint32_t expected_map_root = parse_u32(argv[3], "map root");
    uint32_t expected_layout_root = parse_u32(argv[4], "layout root");
    uint32_t expected_wild_root = parse_u32(argv[5], "wild root");
    uint32_t payload_size = parse_u32(argv[6], "payload size");
    uint32_t portal_travel = parse_u32(argv[7], "portal travel script");
    uint32_t return_travel = parse_u32(argv[8], "return travel script");
    uint32_t trainer_root = parse_u32(argv[9], "trainer root");
    uint32_t pewter_script = parse_u32(argv[10], "Pewter progression script");
    uint32_t champion_script = parse_u32(argv[11], "Champion progression script");
    uint32_t wild_select = parse_u32(argv[12], "wild overlay selector");
    uint32_t wild_try_generate = parse_u32(argv[13], "wild generation hook");
    uint32_t wild_fishing = parse_u32(argv[14], "wild fishing hook");
    uint32_t wild_set_mode = parse_u32(argv[15], "wild mode setter");
    uint32_t wild_get_mode = parse_u32(argv[16], "wild mode getter");
    uint32_t wild_hidden = parse_u32(argv[17], "hidden encounter scan");
    uint32_t wild_field_use = parse_u32(argv[18], "ecology radar callback");
    uint32_t wild_overlay_table = parse_u32(argv[19], "wild overlay table");
    uint32_t wild_overlay_count = parse_u32(argv[20], "wild overlay count");
    uint32_t vermilion_event_objects = argc == 22
        ? parse_u32(argv[21], "Vermilion event object count") : 1U;
    if ((probe & 1U) == 0 || payload_size == 0
        || !rom_pointer(portal_travel) || !rom_pointer(return_travel)
        || !rom_pointer(trainer_root) || !rom_pointer(pewter_script)
        || !rom_pointer(champion_script) || (wild_select & 1U) == 0
        || (wild_try_generate & 1U) == 0
        || (wild_fishing & 1U) == 0 || (wild_set_mode & 1U) == 0
        || (wild_get_mode & 1U) == 0 || (wild_hidden & 1U) == 0
        || (wild_field_use & 1U) == 0 || wild_overlay_count == 0
        || !rom_pointer(wild_overlay_table))
        die("runtime argument contract failed");

    struct mLogger logger = {.log = silent_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = mCoreFind(argv[1]);
    if (core == NULL || !core->init(core))
        die("core initialization failed");
    if (!mCoreLoadFile(core, argv[1]))
        die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    color_t *video = calloc(GBA_WIDTH * GBA_HEIGHT, sizeof(*video));
    if (video == NULL)
        die("video allocation failed");
    core->setVideoBuffer(core, video, GBA_WIDTH);
    core->reset(core);
    uint32_t transitions = run_natural_new_game(core, video);

    uint32_t map_root = read32(core, ROM_BASE + UINT32_C(0x54B0C));
    uint32_t layout_root = read32(core, ROM_BASE + UINT32_C(0x54A54));
    uint32_t wild_root = read32(core, ROM_BASE + UINT32_C(0x8257C));
    if (map_root != expected_map_root || layout_root != expected_layout_root
        || wild_root != expected_wild_root)
        die("repoint root differs from metadata");
    if (!rom_pointer(map_root) || !rom_pointer(layout_root) || !rom_pointer(wild_root))
        die("repoint root is not a ROM pointer");

    uint32_t group96 = read32(core, map_root + 96U * 4U);
    uint32_t vermilion_header = read32(core, group96 + 5U * 4U);
    uint32_t vermilion_layout = read32(core, vermilion_header);
    uint32_t vermilion_events = read32(core, vermilion_header + 4U);
    if (!rom_pointer(group96) || !rom_pointer(vermilion_header)
        || !rom_pointer(vermilion_layout) || !rom_pointer(vermilion_events))
        die("Kanto entry pointer graph is invalid");
    if (read32(core, vermilion_layout) != 48U
        || read32(core, vermilion_layout + 4U) != 40U
        || read16(core, vermilion_header + UINT32_C(0x12)) != 553U
        || read8(core, vermilion_events) != vermilion_event_objects
        || read8(core, vermilion_events + 1U) != 10U)
        die("Kanto entry ABI values differ from canonical map");

    unsigned kanto_wild_headers = 0;
    uint32_t first_route_land_info = 0;
    uint32_t t512_fishing_info = 0;
    for (unsigned index = 0; index < 1024; ++index) {
        uint32_t header = wild_root + index * 20U;
        uint8_t group = read8(core, header);
        uint8_t map = read8(core, header + 1U);
        if (group == 0xFFU && map == 0xFFU)
            break;
        if (group >= 96U && group <= 98U)
            ++kanto_wild_headers;
        if (group == 3U && map == 19U)
            first_route_land_info = read32(core, header + 4U);
        if (group == 11U && map == 3U)
            t512_fishing_info = read32(core, header + 16U);
    }
    if (kanto_wild_headers != 133U)
        die("Kanto wild header count differs from metadata");
    if (!rom_pointer(first_route_land_info))
        die("first-route native land encounter info is missing");
    if (!rom_pointer(t512_fishing_info))
        die("T512 native fishing encounter info is missing");

    /* The battle engine's literal pool must reference the expanded table, and
     * both ends of the Kanto progression must resolve to real six-mon parties. */
    if (read32(core, ROM_BASE + UINT32_C(0xF5C0)) != trainer_root)
        die("battle engine does not reference expanded trainer table");
    const unsigned trainer_ids[] = {751U, 763U};
    for (size_t index = 0; index < sizeof(trainer_ids) / sizeof(trainer_ids[0]); ++index) {
        uint32_t record = trainer_root + trainer_ids[index] * 32U;
        uint32_t party = read32(core, record + 0x1CU);
        if (read8(core, record) != 3U || read32(core, record + 0x14U) != 5U
            || read8(core, record + 0x18U) != 6U || !rom_pointer(party))
            die("generated trainer ABI record is invalid");
        uint16_t level = read16(core, party + 2U);
        /* The final ChangeKit legitimately uses a zero EV field.  Validate
         * the actual 16-byte party ABI instead of treating EV=0 as empty. */
        if (level == 0U || level > 100U
            || read16(core, party + 4U) == 0U || read16(core, party + 8U) == 0U
            || read16(core, party + 10U) == 0U || read16(core, party + 12U) == 0U
            || read16(core, party + 14U) == 0U)
            die("generated trainer party row is invalid");
    }

    uint32_t group98 = read32(core, map_root + 98U * 4U);
    uint32_t pewter_header = read32(core, group98 + 12U * 4U);
    uint32_t pewter_events = read32(core, pewter_header + 4U);
    uint32_t pewter_objects = read32(core, pewter_events + 4U);
    uint32_t group97 = read32(core, map_root + 97U * 4U);
    uint32_t champion_header = read32(core, group97 + 79U * 4U);
    uint32_t champion_events = read32(core, champion_header + 4U);
    uint32_t champion_objects = read32(core, champion_events + 4U);
    if (!rom_pointer(pewter_events) || !rom_pointer(pewter_objects)
        || !rom_pointer(champion_events) || !rom_pointer(champion_objects))
        die("Kanto progression object graph has an invalid pointer");
    bool pewter_found = false;
    bool champion_found = false;
    for (unsigned index = 0; index < read8(core, pewter_events); ++index) {
        if (read32(core, pewter_objects + index * 0x18U + 0x10U) == pewter_script)
            pewter_found = true;
    }
    for (unsigned index = 0; index < read8(core, champion_events); ++index) {
        if (read32(core, champion_objects + index * 0x18U + 0x10U) == champion_script)
            champion_found = true;
    }
    if (!pewter_found || !champion_found)
        die("Kanto progression object graph is invalid");
    if (read8(core, pewter_script) != 0x5AU)
        die("first Kanto gym proxy is invalid");
    if (read8(core, pewter_script + 1U) == 0x5CU
        && read_le16_unaligned(core, pewter_script + 3U) != 751U)
        die("first Kanto gym direct battle script is invalid");
    if (read8(core, champion_script) != 0x5AU)
        die("final Kanto League proxy is invalid");
    /* T35 replaces the original direct scripts with flag-aware proxies.  The
     * exact 1,302 command/party bindings are audited separately; this smoke
     * keeps verifying that each physical map resolves to its live proxy. */

    core->rawWrite16(core, SPECIAL_VAR_RESULT, -1, 0);
    uint32_t probe_result = call_thumb(core, probe, 0, 0, 0, 0);
    uint16_t marker = read16(core, SPECIAL_VAR_RESULT);
    if (probe_result != QOL_MARKER || marker != QOL_MARKER)
        die("embedded QOL-B probe did not execute");

    uint32_t saveblock1 = read32(core, G_SAVE_BLOCK1);
    if (saveblock1 < UINT32_C(0x02000000) || saveblock1 >= UINT32_C(0x02040000))
        die("natural new game did not retain a valid SaveBlock1");
    if (read8(core, saveblock1 + 4U) != 4U || read8(core, saveblock1 + 5U) != 0U)
        die("natural new game did not reach the Vega field checkpoint");

    /* Exercise the key item's real field callback and menu task from the
     * natural Vega field checkpoint.  First use a disposable task to obtain
     * the internal open-menu callback installed by VegaWildOverlay_FieldUse,
     * then restore the field and select night with DOWN/DOWN/A. */
    size_t ecology_menu_state_size = core->stateSize(core);
    void *ecology_menu_state = malloc(ecology_menu_state_size);
    if (ecology_menu_state == NULL
        || !core->saveState(core, ecology_menu_state))
        die("ecology radar menu state capture failed");
    uint32_t disposable_task = call_thumb(
        core, CREATE_TASK, wild_get_mode, 0x50U, 0U, 0U);
    if (disposable_task >= 16U)
        die("ecology radar disposable task could not be created");
    (void)call_thumb(core, wild_field_use, disposable_task, 0U, 0U, 0U);
    uint32_t ecology_open_menu = read32(core, ITEM_USE_ON_FIELD_CALLBACK);
    if (!rom_code_pointer(ecology_open_menu)
        || ecology_open_menu == wild_field_use)
        die("ecology radar did not install its field menu callback");
    if (!core->loadState(core, ecology_menu_state))
        die("ecology radar menu state restore failed");
    (void)call_thumb(core, wild_set_mode, 0U, 0U, 0U, 0U);
    uint32_t menu_task = call_thumb(
        core, CREATE_TASK, ecology_open_menu, 0x50U, 0U, 0U);
    if (menu_task >= 16U)
        die("ecology radar open-menu task could not be created");
    (void)call_thumb(core, ecology_open_menu, menu_task, 0U, 0U, 0U);
    run_frames(core, 30U, 0U);
    run_frames(core, 2U, 128U);
    run_frames(core, 10U, 0U);
    run_frames(core, 2U, 128U);
    run_frames(core, 10U, 0U);
    run_frames(core, 2U, 1U);
    run_frames(core, 30U, 0U);
    uint32_t ecology_selected_mode = call_thumb(
        core, wild_get_mode, 0U, 0U, 0U, 0U);
    if (ecology_selected_mode != 2U) {
        fprintf(stderr,
                "mgba-regression-smoke: ecology radar selected mode=%" PRIu32 "\n",
                ecology_selected_mode);
        die("ecology radar menu did not persist the selected night mode");
    }
    if (!core->loadState(core, ecology_menu_state))
        die("ecology radar post-menu state restore failed");
    free(ecology_menu_state);

    /* Run the exact portal travel bytecode from a natural Vega field state. */
    (void)call_thumb(core, SCRIPT_CONTEXT1_SETUP, portal_travel, 0, 0, 0);
    run_frames(core, 1200, 0);
    saveblock1 = read32(core, G_SAVE_BLOCK1);
    int16_t player_x = (int16_t)read16(core, saveblock1);
    int16_t player_y = (int16_t)read16(core, saveblock1 + 2U);
    uint8_t player_group = read8(core, saveblock1 + 4U);
    uint8_t player_map = read8(core, saveblock1 + 5U);
    if (player_group != 96U || player_map != 5U) {
        fprintf(stderr, "mgba-regression-smoke: Kanto load observed map=%u/%u pos=%d,%d\n",
                player_group, player_map, player_x, player_y);
        die("normal map loader did not enter Kanto Vermilion");
    }
    uint32_t kanto_transitions = 0;
    for (size_t index = 1; index < GBA_WIDTH * GBA_HEIGHT; ++index) {
        if (video[index] != video[index - 1])
            ++kanto_transitions;
    }
    if (kanto_transitions < 100U)
        die("Kanto framebuffer is blank or uniform");

    size_t field_state_size = core->stateSize(core);
    void *field_state = malloc(field_state_size);
    if (field_state == NULL || !core->saveState(core, field_state))
        die("Kanto field state capture failed");
    const uint16_t movement_keys[] = {16U, 32U, 64U, 128U};
    bool kanto_moved = false;
    int16_t moved_x = player_x;
    int16_t moved_y = player_y;
    uint16_t movement_key = 0;
    for (size_t index = 0; index < sizeof(movement_keys) / sizeof(movement_keys[0]); ++index) {
        if (!core->loadState(core, field_state))
            die("Kanto field state restore failed");
        run_frames(core, 60, movement_keys[index]);
        run_frames(core, 4, 0);
        int16_t observed_x = (int16_t)read16(core, saveblock1);
        int16_t observed_y = (int16_t)read16(core, saveblock1 + 2U);
        if (read8(core, saveblock1 + 4U) == 96U
            && read8(core, saveblock1 + 5U) == 5U
            && (observed_x != player_x || observed_y != player_y)) {
            kanto_moved = true;
            moved_x = observed_x;
            moved_y = observed_y;
            movement_key = movement_keys[index];
            break;
        }
    }
    free(field_state);
    if (!kanto_moved)
        die("player could not move on the rendered Kanto map");

    (void)call_thumb(core, SCRIPT_CONTEXT1_SETUP, return_travel, 0, 0, 0);
    run_frames(core, 900, 0);
    saveblock1 = read32(core, G_SAVE_BLOCK1);
    if (read8(core, saveblock1 + 4U) != 4U || read8(core, saveblock1 + 5U) != 0U)
        die("return event bytecode did not enter the Vega map");

    /* Exercise the exact in-ROM selector used by the first grass route after
     * the field/event checks, so the synthetic map coordinate cannot affect
     * those independent scenarios. T501 is the first overlay row (map 3/19). */
    if (read8(core, wild_overlay_table) != 3U
        || read8(core, wild_overlay_table + 1U) != 19U
        || read8(core, wild_overlay_table + 2U) != 0U
        || read8(core, wild_overlay_table + 3U) != 0U
        || read8(core, wild_overlay_table + 4U) != 13U
        || read8(core, wild_overlay_table + 5U) != 8U
        || read8(core, wild_overlay_table + 6U) != 5U)
        die("first-route wild overlay row differs from authored 5% contract");
    uint32_t ecology_candidates = 0;
    uint32_t ecology_layer_mask = 0;
    uint32_t ecology_radar_overrides = 0;
    for (uint32_t index = 0; index < wild_overlay_count; ++index) {
        uint32_t entry = wild_overlay_table + index * ECOLOGY_ENTRY_SIZE;
        uint8_t layer = read8(core, entry + 3U);
        uint8_t count = read8(core, entry + 5U);
        if (layer > 5U || count == 0U || count > 12U
            || read8(core, entry + 4U) == 0U
            || read8(core, entry + 6U) == 0U)
            die("ecology table entry ABI is invalid");
        ecology_layer_mask |= UINT32_C(1) << layer;
        ecology_candidates += count;
        for (uint8_t candidate = 0; candidate < count; ++candidate) {
            if (read_le16_unaligned(core, entry + 8U + candidate * 2U) == 0U
                || read8(core, entry + 32U + candidate) == 0U
                || read8(core, entry + 44U + candidate)
                    < read8(core, entry + 32U + candidate)
                || read8(core, entry + 68U + candidate)
                    < read8(core, entry + 56U + candidate)
                || (read8(core, entry + 80U + candidate) & 0x7FU) > 8U
                || read8(core, entry + 92U + candidate) > 2U)
                die("ecology candidate ABI is invalid");
            if (read8(core, entry + 80U + candidate) & 0x80U)
                ++ecology_radar_overrides;
        }
    }
    if (wild_overlay_count != 95U || ecology_candidates != 294U
        || ecology_layer_mask != UINT32_C(0x3F)
        || ecology_radar_overrides != 1U)
        die("ecology table does not cover all authored method layers");
    if (read16(core, ECOLOGY_ITEM_ADDRESS + 10U) != 348U
        || read32(core, ECOLOGY_ITEM_ADDRESS + 24U) != wild_field_use)
        die("ecology radar key-item row is not connected to its callback");
    if (read32(core, ROM_BASE + UINT32_C(0x826DC)) != wild_try_generate
        || read32(core, ROM_BASE + UINT32_C(0x82754)) != wild_fishing)
        die("ecology encounter hooks do not own the stock entrypoints");

    (void)call_thumb(core, wild_set_mode, 1U, 0U, 0U, 0U);
    if (call_thumb(core, wild_get_mode, 0U, 0U, 0U, 0U) != 1U)
        die("ecology mode did not persist through expanded Var storage");
    /* Auto mode must be able to refresh/read the RTC even on a map with no
     * ecology row.  This catches a bad DirectClockUpdate ABI before release;
     * manual modes remain the emulator-independent fallback. */
    (void)call_thumb(core, wild_set_mode, 0U, 0U, 0U, 0U);
    if (call_thumb(core, wild_select, 1U, 0U, 0U, 0U) != 1U
        || call_thumb(core, wild_get_mode, 0U, 0U, 0U, 0U) != 0U)
        die("RTC automatic ecology mode did not preserve an unmatched encounter");
    (void)call_thumb(core, wild_set_mode, 1U, 0U, 0U, 0U);
    uint32_t previous_rng = read32(core, GLOBAL_RNG);
    uint8_t previous_group = read8(core, saveblock1 + 4U);
    uint8_t previous_map = read8(core, saveblock1 + 5U);
    write8(core, saveblock1 + 4U, 3U);
    write8(core, saveblock1 + 5U, 19U);
    write32(core, GLOBAL_RNG, UINT32_C(0x12345678));
    unsigned wild_overlay_hits = 0;
    uint32_t wild_candidates_seen = 0;
    for (unsigned call = 0; call < WILD_OVERLAY_CALLS; ++call) {
        uint16_t species = (uint16_t)call_thumb(core, wild_select, 1U, 0U, 0U, 0U);
        if (species == 1U)
            continue;
        bool matched = false;
        for (unsigned candidate = 0; candidate < 8U; ++candidate) {
            if (species == read_le16_unaligned(
                    core, wild_overlay_table + 8U + candidate * 2U)) {
                wild_candidates_seen |= UINT32_C(1) << candidate;
                matched = true;
                break;
            }
        }
        if (!matched)
            die("first-route selector returned a species outside its ROM table");
        ++wild_overlay_hits;
    }
    if (wild_overlay_hits < 120U || wild_overlay_hits > 300U
        || wild_candidates_seen != UINT32_C(0xFF))
        die("first-route selector did not produce the complete authored 5% pool");

    /* Call the function installed at stock TryGenerateWildMon, not just its
     * selector helper. This proves native slot/level generation reaches the
     * overlay and creates a readable party Pokemon on the actual hook path. */
    uint32_t native_slots = read32(core, first_route_land_info + 4U);
    if (!rom_pointer(native_slots))
        die("first-route native land slots are invalid");
    write32(core, GLOBAL_RNG, UINT32_C(0x12345678));
    unsigned generation_calls = 0;
    uint16_t generated_overlay_species = 0;
    for (; generation_calls < 512U && generated_overlay_species == 0U;
         ++generation_calls) {
        for (unsigned byte = 0; byte < PARTY_BYTES; ++byte)
            write8(core, ENEMY_PARTY + byte, 0U);
        write8(core, ENEMY_PARTY_COUNT, 0U);
        if (call_thumb(core, wild_try_generate,
                       first_route_land_info, 0U, 0U, 0U) != 1U)
            die("first-route wild generation hook rejected valid land info");
        uint16_t species = (uint16_t)call_thumb(
            core, GET_MON_DATA, ENEMY_PARTY, 11U, 0U, 0U);
        bool valid = false;
        for (unsigned candidate = 0; candidate < 8U; ++candidate) {
            if (species == read_le16_unaligned(
                    core, wild_overlay_table + 8U + candidate * 2U)) {
                generated_overlay_species = species;
                valid = true;
                break;
            }
        }
        for (unsigned slot = 0; slot < 12U && !valid; ++slot) {
            if (species == read_le16_unaligned(core, native_slots + slot * 4U + 2U))
                valid = true;
        }
        if (!valid)
            die("wild generation hook created a species outside native/overlay tables");
        verify_canonical_nickname(core, ENEMY_PARTY, species);
    }
    if (generated_overlay_species == 0U)
        die("first-route generation hook never created an overlay species");

    write8(core, saveblock1 + 4U, 4U);
    write8(core, saveblock1 + 5U, 0U);
    for (unsigned call = 0; call < 256U; ++call) {
        if (call_thumb(core, wild_select, 1U, 0U, 0U, 0U) != 1U)
            die("wild overlay leaked into an unmatched Vega map");
    }
    write8(core, saveblock1 + 4U, previous_group);
    write8(core, saveblock1 + 5U, previous_map);
    write32(core, GLOBAL_RNG, previous_rng);

    /* Manual day/night/swarm modes must each expose the authored-only layer
     * without replacing the original species when their extra roll misses. */
    const struct {
        uint8_t mode;
        uint8_t group;
        uint8_t map;
        uint8_t layer;
    } mode_cases[] = {
        {1U, 3U, 48U, 1U},  /* T036 morning/day */
        {2U, 1U, 0U, 2U},   /* T516 night */
        {3U, 0U, 0U, 3U},   /* T520 swarm */
    };
    unsigned special_mode_hits = 0;
    for (size_t case_index = 0;
         case_index < sizeof(mode_cases) / sizeof(mode_cases[0]);
         ++case_index) {
        uint32_t entry = find_ecology_entry(
            core, wild_overlay_table, wild_overlay_count,
            mode_cases[case_index].group, mode_cases[case_index].map,
            0U, mode_cases[case_index].layer);
        if (!entry)
            die("authored special-mode entry is missing");
        write8(core, saveblock1 + 4U, mode_cases[case_index].group);
        write8(core, saveblock1 + 5U, mode_cases[case_index].map);
        write32(core, GLOBAL_RNG, UINT32_C(0x13572468) + (uint32_t)case_index);
        (void)call_thumb(core, wild_set_mode, mode_cases[case_index].mode, 0U, 0U, 0U);
        bool observed = false;
        for (unsigned call = 0; call < 2048U && !observed; ++call) {
            uint16_t species = (uint16_t)call_thumb(
                core, wild_select, 1U, 0U, 0U, 0U);
            if (species != 1U && !ecology_entry_has_species(core, entry, species))
                die("special mode returned a species outside its authored layer");
            if (species != 1U)
                observed = true;
        }
        if (!observed)
            die("special ecology mode never selected its authored layer");
        ++special_mode_hits;
    }

    /* T513's authored "badge 4 + night, or ecology ticket" alternative is
     * represented by owning the ecology radar and selecting manual night. */
    uint32_t radar_night_entry = find_ecology_entry(
        core, wild_overlay_table, wild_overlay_count, 3U, 9U, 1U, 2U);
    if (!radar_night_entry)
        die("T513 radar-night alternative entry is missing");
    for (uint16_t flag = 0x0820U; flag <= 0x0827U; ++flag)
        (void)call_thumb(core, FLAG_CLEAR, flag, 0U, 0U, 0U);
    write8(core, saveblock1 + 4U, 3U);
    write8(core, saveblock1 + 5U, 9U);
    (void)call_thumb(core, wild_set_mode, 2U, 0U, 0U, 0U);
    write32(core, GLOBAL_RNG, UINT32_C(0x31415926));
    for (unsigned call = 0; call < 512U; ++call) {
        uint16_t species = (uint16_t)call_thumb(
            core, wild_select, 1U, 1U, 0U, 0U);
        if (ecology_entry_has_species(core, radar_night_entry, species))
            die("T513 radar-night alternative ignored its badge/item gate");
    }
    if (call_thumb(core, ADD_BAG_ITEM, 348U, 1U, 0U, 0U) != 1U)
        die("ecology radar could not be inserted into the key-item pocket");
    bool radar_night_observed = false;
    for (unsigned call = 0; call < 2048U && !radar_night_observed; ++call) {
        uint16_t species = (uint16_t)call_thumb(
            core, wild_select, 1U, 1U, 0U, 0U);
        radar_night_observed = ecology_entry_has_species(
            core, radar_night_entry, species);
    }
    if (!radar_night_observed)
        die("ecology radar manual night did not satisfy the ticket alternative");

    /* The actual GenerateFishingEncounter replacement must build a Pokemon
     * from the T512 fishing layer while retaining native slots on misses. */
    uint32_t fishing_entry = find_ecology_entry(
        core, wild_overlay_table, wild_overlay_count, 11U, 3U, 3U, 4U);
    uint32_t fishing_slots = read32(core, t512_fishing_info + 4U);
    if (!fishing_entry || !rom_pointer(fishing_slots))
        die("T512 fishing ecology/native tables are invalid");
    write8(core, saveblock1 + 4U, 11U);
    write8(core, saveblock1 + 5U, 3U);
    write32(core, GLOBAL_RNG, UINT32_C(0x24681357));
    unsigned fishing_calls = 0;
    uint16_t fishing_species = 0;
    for (; fishing_calls < 1024U && fishing_species == 0U; ++fishing_calls) {
        for (unsigned byte = 0; byte < PARTY_BYTES; ++byte)
            write8(core, ENEMY_PARTY + byte, 0U);
        write8(core, ENEMY_PARTY_COUNT, 0U);
        uint16_t species = (uint16_t)call_thumb(
            core, wild_fishing, t512_fishing_info, 2U, 0U, 0U);
        uint16_t generated = (uint16_t)call_thumb(
            core, GET_MON_DATA, ENEMY_PARTY, 11U, 0U, 0U);
        if (species != generated)
            die("fishing dispatcher return/species differ");
        verify_canonical_nickname(core, ENEMY_PARTY, species);
        if (ecology_entry_has_species(core, fishing_entry, species)) {
            fishing_species = species;
            continue;
        }
        bool native = false;
        for (unsigned slot = 0; slot < 10U; ++slot) {
            if (species == read_le16_unaligned(core, fishing_slots + slot * 4U + 2U))
                native = true;
        }
        if (!native)
            die("fishing dispatcher generated outside native/ecology tables");
    }
    if (fishing_species == 0U)
        die("fishing dispatcher never generated an ecology species");

    /* Hidden/DexNav-only rows are reachable even on indoor maps without a
     * stock walking table by invoking the ecology radar scan. */
    uint32_t hidden_entry = find_ecology_entry(
        core, wild_overlay_table, wild_overlay_count, 3U, 63U, 4U, 5U);
    if (!hidden_entry)
        die("T034 hidden ecology entry is missing");
    write8(core, saveblock1 + 4U, 3U);
    write8(core, saveblock1 + 5U, 63U);
    write32(core, GLOBAL_RNG, UINT32_C(0x10293847));
    for (unsigned byte = 0; byte < PARTY_BYTES; ++byte)
        write8(core, ENEMY_PARTY + byte, 0U);
    write8(core, ENEMY_PARTY_COUNT, 0U);
    (void)call_thumb(core, wild_set_mode, 4U, 0U, 0U, 0U);
    uint32_t hidden_callback_before = read32(core, MAIN_CALLBACK2);
    if (call_thumb(core, wild_hidden, 0U, 0U, 0U, 0U) != 1U)
        die("ecology radar hidden scan rejected an authored indoor map");
    uint16_t hidden_species = (uint16_t)call_thumb(
        core, GET_MON_DATA, ENEMY_PARTY, 11U, 0U, 0U);
    if (!ecology_entry_has_species(core, hidden_entry, hidden_species))
        die("ecology radar generated outside the hidden authored pool");
    verify_canonical_nickname(core, ENEMY_PARTY, hidden_species);
    for (unsigned call = 0; call < 64U; ++call) {
        uint16_t species = (uint16_t)call_thumb(
            core, wild_select, 1U, 0U, 0U, 0U);
        if (species != 1U && ecology_entry_has_species(core, hidden_entry, species))
            die("hidden mode leaked into ordinary step encounters");
    }
    /* StartWildBattle creates a transition task; callback2 changes when that
     * task runs, not during the direct setup call itself. */
    run_frames(core, 360U, 0U);
    uint32_t hidden_callback_after = read32(core, MAIN_CALLBACK2);
    if (hidden_callback_after == hidden_callback_before
        || !rom_code_pointer(hidden_callback_after))
        die("ecology radar hidden scan did not enter a wild battle");

    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"checks\":{\"boot\":true,\"map_roots\":true,"
           "\"kanto_entry\":true,\"wild_headers\":true,"
           "\"trainer_table\":true,\"kanto_progression_objects\":true,"
           "\"first_route_wild_overlay\":true,\"first_route_wild_generation\":true,"
           "\"wild_overlay_isolated\":true,\"special_ecology_modes\":true,"
           "\"rtc_auto_ecology\":true,"
           "\"radar_ticket_alternative\":true,"
           "\"fishing_ecology\":true,\"hidden_ecology\":true,"
           "\"hidden_mode_isolated\":true,\"hidden_battle_scheduled\":true,"
           "\"ecology_radar_item\":true,\"ecology_radar_menu\":true,"
           "\"qol_b_thumb_execution\":true,\"kanto_map_load\":true,"
           "\"kanto_movement\":true,\"event_round_trip\":true},"
           "\"framebuffer_transitions\":%" PRIu32 ","
           "\"kanto_framebuffer_transitions\":%" PRIu32 ","
           "\"kanto_position\":{\"group\":%u,\"map\":%u,\"x\":%d,\"y\":%d},"
           "\"kanto_movement\":{\"key\":%u,\"x\":%d,\"y\":%d},"
           "\"first_route_wild_overlay\":{\"calls\":%u,\"hits\":%u,"
           "\"candidate_mask\":%" PRIu32 ",\"generation_calls\":%u,"
           "\"generated_species\":%u},"
           "\"ecology\":{\"entries\":%" PRIu32 ",\"candidate_bindings\":%" PRIu32 ","
           "\"layer_mask\":%" PRIu32 ",\"radar_overrides\":%" PRIu32 ","
           "\"special_mode_hits\":%u,"
           "\"fishing_calls\":%u,\"fishing_species\":%u,"
           "\"hidden_species\":%u},"
           "\"kanto_wild_headers\":%u,\"qol_marker\":%u,"
           "\"payload_size\":%" PRIu32 ",\"artifacts_written\":[]}\n",
           transitions, kanto_transitions, player_group, player_map,
           player_x, player_y, movement_key, moved_x, moved_y,
           WILD_OVERLAY_CALLS, wild_overlay_hits, wild_candidates_seen,
           generation_calls, generated_overlay_species,
           wild_overlay_count, ecology_candidates, ecology_layer_mask,
           ecology_radar_overrides,
           special_mode_hits, fishing_calls, fishing_species, hidden_species,
           kanto_wild_headers, marker, payload_size);

    free(video);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
