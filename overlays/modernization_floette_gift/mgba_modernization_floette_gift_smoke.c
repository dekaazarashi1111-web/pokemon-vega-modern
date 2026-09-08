/* Stage69 Floette Eternal one-time gift exact-ROM stateful smoke.
 *
 * Fixture setup uses production ROM APIs (CreateMon, SetBoxMonAt,
 * ZeroBoxMonAt, AddBagItem).  The gift itself is invoked only through the
 * linked Stage69 entrypoint and persists through the normal save path.
 */
#define main mgba_regression_smoke_embedded_main
#include "mgba_regression_smoke.c"
#undef main

#include <string.h>

#define FG_MAX_CALL_STEPS UINT64_C(60000000)
#define FG_SAVE_FILE_SIZE UINT32_C(0x20000)
#define FG_ABI_MARKER UINT32_C(0xA169)
#define FG_LEDGER UINT32_C(0x0203D000)
#define FG_LEDGER_SIZE UINT32_C(0x800)
#define FG_ACQ_INNER_OFFSET UINT32_C(68)
#define FG_COLLECTION_OFFSET UINT32_C(12)
#define FG_COLLECTION_BIT UINT32_C(850)
#define FG_FLASH_LEDGER UINT32_C(0x0E01F064)
#define FG_PLAYER_PARTY UINT32_C(0x020241E4)
#define FG_PLAYER_COUNT UINT32_C(0x02023F89)
#define FG_SPECIAL_BOX UINT32_C(0x0203700A)
#define FG_SPECIAL_POS UINT32_C(0x0203700C)
#define FG_SCRATCH UINT32_C(0x0203E300)
#define FG_MON_SIZE UINT32_C(100)
#define FG_BOX_MON_SIZE UINT32_C(80)
#define FG_PARTY_CAPACITY UINT32_C(6)
#define FG_BOX_COUNT UINT32_C(14)
#define FG_BOX_CAPACITY UINT32_C(30)
#define FG_SPECIES UINT16_C(1029)
#define FG_LEVEL UINT16_C(50)
#define FG_MEGA_RING UINT16_C(580)
#define FG_CLAIM_FLAG UINT16_C(0x14CD)
#define FG_FLAG_GET UINT32_C(0x0806DEC5)
#define FG_CHECK_BAG UINT32_C(0x08099949)
#define FG_ADD_BAG UINT32_C(0x08099A8D)
#define FG_CREATE_MON UINT32_C(0x0803D1C1)
#define FG_GET_MON_DATA UINT32_C(0x0803F355)
#define FG_SAVE_LOAD UINT32_C(0x080DB4E5)
#define FG_GET_PENDING UINT32_C(0x092D1CE1)
#define FG_RESULT_SUCCESS UINT32_C(0)
#define FG_RESULT_ALREADY UINT32_C(1)
#define FG_RESULT_LOCKED UINT32_C(3)
#define FG_RESULT_FULL UINT32_C(4)

static unsigned fg_log_problem_count;
static struct mCore *fg_log_core;
static uint32_t fg_get_box_mon_data;
static uint32_t fg_get_boxed_mon_ptr;
static uint32_t fg_zero_box_mon;

struct FgSnapshot {
    size_t size;
    void *bytes;
};

static void fg_die(const char *message)
{
    fprintf(stderr, "mgba-modernization-floette-gift: %s\n", message);
    exit(1);
}

static void fg_phase(const char *phase)
{
    fprintf(stderr, "mgba-modernization-floette-gift: phase=%s\n", phase);
    fflush(stderr);
}

static void fg_log(struct mLogger *logger, int category,
                   enum mLogLevel level, const char *format, va_list args)
{
    (void)logger;
    if (!(level & (mLOG_FATAL | mLOG_ERROR | mLOG_WARN)))
        return;
    if (strstr(mLogCategoryName(category), "Savedata") != NULL
        && strstr(format, "Savegame time offset set") != NULL)
        return;
    ++fg_log_problem_count;
    fprintf(stderr, "mGBA[%s][0x%02x] pc=%08" PRIx32 ": ",
            mLogCategoryName(category), (unsigned)level,
            fg_log_core ? (uint32_t)read_register(fg_log_core, "pc") : 0U);
    vfprintf(stderr, format, args);
    fputc('\n', stderr);
}

static void fg_initialize_save(const char *path)
{
    FILE *stream = fopen(path, "wb");
    if (stream == NULL)
        fg_die("temporary save creation failed");
    uint8_t block[4096];
    memset(block, 0xFF, sizeof(block));
    uint32_t remaining = FG_SAVE_FILE_SIZE;
    while (remaining != 0U) {
        size_t amount = remaining < sizeof(block) ? remaining : sizeof(block);
        if (fwrite(block, 1U, amount, stream) != amount) {
            (void)fclose(stream);
            fg_die("temporary save initialization failed");
        }
        remaining -= (uint32_t)amount;
    }
    if (fclose(stream) != 0)
        fg_die("temporary save close failed");
}

static void fg_write8(struct mCore *core, uint32_t address, uint8_t value)
{
    core->rawWrite8(core, address, -1, value);
}

static void fg_write16(struct mCore *core, uint32_t address, uint16_t value)
{
    core->rawWrite16(core, address, -1, value);
}

static uint32_t fg_read_u32_unaligned(struct mCore *core, uint32_t address)
{
    return (uint32_t)read8(core, address)
        | ((uint32_t)read8(core, address + 1U) << 8U)
        | ((uint32_t)read8(core, address + 2U) << 16U)
        | ((uint32_t)read8(core, address + 3U) << 24U);
}

static void fg_write32_unaligned(struct mCore *core, uint32_t address,
                                 uint32_t value)
{
    fg_write8(core, address, (uint8_t)value);
    fg_write8(core, address + 1U, (uint8_t)(value >> 8U));
    fg_write8(core, address + 2U, (uint8_t)(value >> 16U));
    fg_write8(core, address + 3U, (uint8_t)(value >> 24U));
}

static void fg_clear(struct mCore *core, uint32_t address, size_t size)
{
    for (size_t index = 0U; index < size; ++index)
        fg_write8(core, address + (uint32_t)index, 0U);
}

static struct FgSnapshot fg_take_snapshot(struct mCore *core)
{
    struct FgSnapshot result = {.size = core->stateSize(core), .bytes = NULL};
    result.bytes = malloc(result.size);
    if (result.bytes == NULL || !core->saveState(core, result.bytes))
        fg_die("state capture failed");
    return result;
}

static void fg_restore_snapshot(struct mCore *core,
                                const struct FgSnapshot *snapshot)
{
    if (core->stateSize(core) != snapshot->size
        || !core->loadState(core, snapshot->bytes))
        fg_die("state restore failed");
}

static uint64_t fg_hash_region(struct mCore *core, uint32_t address,
                               size_t size)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    for (size_t index = 0U; index < size; ++index) {
        hash ^= read8(core, address + (uint32_t)index);
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

static uint32_t fg_call_thumb(struct mCore *core, uint32_t function,
                              uint32_t r0, uint32_t r1,
                              uint32_t r2, uint32_t r3)
{
    struct CpuContext original = capture_cpu(core);
    write_register(core, "cpsr", original.registers[16] | 0xA0);
    write_register(core, "lr", (int32_t)UINT32_C(0x08000001));
    write_register(core, "r0", (int32_t)r0);
    write_register(core, "r1", (int32_t)r1);
    write_register(core, "r2", (int32_t)r2);
    write_register(core, "r3", (int32_t)r3);
    write_register(core, "pc", (int32_t)function);
    uint64_t steps = 0U;
    while ((((uint32_t)read_register(core, "pc")) & ~1U)
           != UINT32_C(0x08000002)) {
        if (++steps > FG_MAX_CALL_STEPS) {
            fprintf(stderr,
                    "mgba-modernization-floette-gift: instruction limit "
                    "function=%#010" PRIx32 " pc=%#010" PRIx32 "\n",
                    function, (uint32_t)read_register(core, "pc"));
            fg_die("runtime instruction limit exceeded");
        }
        core->step(core);
    }
    uint32_t result = (uint32_t)read_register(core, "r0");
    restore_cpu(core, &original);
    return result;
}

static uint32_t fg_call8(struct mCore *core, uint32_t function,
                         uint32_t r0, uint32_t r1,
                         uint32_t r2, uint32_t r3,
                         uint32_t a4, uint32_t a5,
                         uint32_t a6, uint32_t a7)
{
    struct CpuContext original = capture_cpu(core);
    uint32_t original_sp = (uint32_t)original.registers[13];
    uint32_t call_sp = (original_sp - 16U) & ~7U;
    uint8_t saved[16];
    for (unsigned index = 0U; index < sizeof(saved); ++index)
        saved[index] = read8(core, call_sp + index);
    fg_write32_unaligned(core, call_sp, a4);
    fg_write32_unaligned(core, call_sp + 4U, a5);
    fg_write32_unaligned(core, call_sp + 8U, a6);
    fg_write32_unaligned(core, call_sp + 12U, a7);
    write_register(core, "sp", (int32_t)call_sp);
    write_register(core, "cpsr", original.registers[16] | 0xA0);
    write_register(core, "lr", (int32_t)UINT32_C(0x08000001));
    write_register(core, "r0", (int32_t)r0);
    write_register(core, "r1", (int32_t)r1);
    write_register(core, "r2", (int32_t)r2);
    write_register(core, "r3", (int32_t)r3);
    write_register(core, "pc", (int32_t)function);
    uint64_t steps = 0U;
    while ((((uint32_t)read_register(core, "pc")) & ~1U)
           != UINT32_C(0x08000002)) {
        if (++steps > FG_MAX_CALL_STEPS)
            fg_die("eight-argument call exceeded instruction limit");
        core->step(core);
    }
    uint32_t result = (uint32_t)read_register(core, "r0");
    for (unsigned index = 0U; index < sizeof(saved); ++index)
        fg_write8(core, call_sp + index, saved[index]);
    restore_cpu(core, &original);
    return result;
}

static uint32_t fg_invoke(struct mCore *core, uint32_t entrypoint)
{
    fg_write16(core, SPECIAL_VAR_RESULT, UINT16_C(0xFFFF));
    uint32_t direct = fg_call_thumb(core, entrypoint, 0U, 0U, 0U, 0U);
    uint32_t script = read16(core, SPECIAL_VAR_RESULT);
    if ((direct & UINT32_C(0xFFFF)) != script)
        fg_die("direct/script result differs");
    return script;
}

static bool fg_flag(struct mCore *core)
{
    return fg_call_thumb(core, FG_FLAG_GET, FG_CLAIM_FLAG, 0U, 0U, 0U) != 0U;
}

static bool fg_collection_bit(struct mCore *core, uint32_t base)
{
    uint32_t byte = FG_ACQ_INNER_OFFSET + FG_COLLECTION_OFFSET
        + FG_COLLECTION_BIT / 8U;
    return (read8(core, base + byte) & (1U << (FG_COLLECTION_BIT & 7U))) != 0U;
}

static bool fg_has_ring(struct mCore *core)
{
    return fg_call_thumb(core, FG_CHECK_BAG, FG_MEGA_RING, 1U, 0U, 0U) != 0U;
}

static void fg_clear_boxes(struct mCore *core)
{
    for (uint32_t box = 0U; box < FG_BOX_COUNT; ++box)
        for (uint32_t slot = 0U; slot < FG_BOX_CAPACITY; ++slot)
            (void)fg_call_thumb(core, fg_zero_box_mon, box, slot, 0U, 0U);
}

static void fg_create_mon(struct mCore *core, uint16_t species,
                          uint8_t level, uint32_t personality)
{
    fg_clear(core, FG_SCRATCH, FG_MON_SIZE);
    (void)fg_call8(core, FG_CREATE_MON, FG_SCRATCH, species, level, 31U,
                   1U, personality, 0U, 0U);
    if (fg_call_thumb(core, FG_GET_MON_DATA,
                      FG_SCRATCH, 11U, 0U, 0U) != species
        || fg_call_thumb(core, FG_GET_MON_DATA,
                         FG_SCRATCH, 56U, 0U, 0U) != level)
        fg_die("CreateMon fixture failed");
}

static void fg_create_fixture_mon(struct mCore *core)
{
    fg_create_mon(core, 25U, 5U, UINT32_C(0x12345678));
}

static void fg_install_party(struct mCore *core, uint32_t count)
{
    if (count > FG_PARTY_CAPACITY)
        fg_die("invalid party fixture count");
    fg_create_fixture_mon(core);
    uint8_t mon[FG_MON_SIZE];
    for (uint32_t index = 0U; index < FG_MON_SIZE; ++index)
        mon[index] = read8(core, FG_SCRATCH + index);
    fg_clear(core, FG_PLAYER_PARTY, FG_PARTY_CAPACITY * FG_MON_SIZE);
    for (uint32_t slot = 0U; slot < count; ++slot)
        for (uint32_t index = 0U; index < FG_MON_SIZE; ++index)
            fg_write8(core, FG_PLAYER_PARTY + slot * FG_MON_SIZE + index,
                      mon[index]);
    fg_write8(core, FG_PLAYER_COUNT, (uint8_t)count);
}

static void fg_fill_boxes(struct mCore *core)
{
    fg_create_fixture_mon(core);
    for (uint32_t box = 0U; box < FG_BOX_COUNT; ++box) {
        for (uint32_t slot = 0U; slot < FG_BOX_CAPACITY; ++slot) {
            uint32_t destination = fg_call_thumb(
                core, fg_get_boxed_mon_ptr, box, slot, 0U, 0U);
            if (destination < UINT32_C(0x02000000)
                || destination + FG_BOX_MON_SIZE > UINT32_C(0x02040000))
                fg_die("DPE GetBoxedMonPtr fixture pointer is invalid");
            for (uint32_t byte = 0U; byte < FG_BOX_MON_SIZE; ++byte)
                fg_write8(core, destination + byte,
                          read8(core, FG_SCRATCH + byte));
            if (fg_call_thumb(core, fg_get_box_mon_data,
                              box, slot, 11U, 0U) != 25U)
                fg_die("DPE GetBoxedMonPtr fixture write failed");
        }
    }
}

static void fg_verify_map(struct mCore *core, uint32_t npc_script,
                          uint32_t claim, uint32_t expected_events,
                          uint32_t expected_map_scripts)
{
    uint32_t map_root = read32(core, ROM_BASE + UINT32_C(0x54B0C));
    uint32_t group96 = read32(core, map_root + 96U * 4U);
    uint32_t header = read32(core, group96 + 5U * 4U);
    uint32_t events = read32(core, header + 4U);
    uint32_t scripts = read32(core, header + 8U);
    uint32_t objects = read32(core, events + 4U);
    uint32_t shop = 0U;
    uint32_t gift = 0U;
    if (!rom_pointer(map_root) || !rom_pointer(group96) || !rom_pointer(header)
        || events != expected_events || scripts != expected_map_scripts
        || !rom_pointer(objects) || read8(core, events) != 15U
        || read8(core, events + 1U) != 10U
        || read8(core, events + 2U) != 0U
        || read8(core, events + 3U) != 7U)
        fg_die("Factory map root/events/scripts graph is invalid");
    for (uint32_t index = 0U; index < 15U; ++index) {
        uint32_t object = objects + index * 0x18U;
        if (read8(core, object) == 14U)
            shop = object;
        if (read8(core, object) == 15U)
            gift = object;
    }
    if (shop == 0U || gift == 0U
        || read16(core, shop + 4U) != 24U
        || read16(core, shop + 6U) != 19U
        || read8(core, gift + 1U) != 62U
        || read16(core, gift + 4U) != 25U
        || read16(core, gift + 6U) != 19U
        || read32(core, gift + 0x10U) != npc_script
        || read8(core, npc_script) != 0x6AU
        || read8(core, npc_script + 1U) != 0x5AU
        || read8(core, npc_script + 2U) != 0x23U
        || fg_read_u32_unaligned(core, npc_script + 3U) != claim)
        fg_die("physical Floette gift NPC script graph is invalid");
}

static struct mCore *fg_open_core(const char *rom_path,
                                  const char *save_path,
                                  color_t **video_out)
{
    struct mCore *core = mCoreFind(rom_path);
    if (core == NULL || !core->init(core))
        fg_die("core initialization failed");
    if (!mCoreLoadFile(core, rom_path))
        fg_die("ROM load failed");
    if (!mCoreLoadSaveFile(core, save_path, false))
        fg_die("save attachment failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    color_t *video = NULL;
    if (video_out != NULL) {
        video = calloc(GBA_WIDTH * GBA_HEIGHT, sizeof(*video));
        if (video == NULL)
            fg_die("video allocation failed");
        core->setVideoBuffer(core, video, GBA_WIDTH);
        *video_out = video;
    }
    fg_log_core = core;
    core->reset(core);
    return core;
}

static void fg_close_core(struct mCore *core, color_t *video)
{
    free(video);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    fg_log_core = NULL;
}

int main(int argc, char **argv)
{
    if (argc != 15) {
        fprintf(stderr,
                "usage: %s ROM SAVE PROBE CLAIM FORM SEEN CAUGHT "
                "NPC_SCRIPT EVENTS MAP_SCRIPTS GET_PENDING GET_BOX_MON_DATA "
                "GET_BOXED_MON_PTR ZERO_BOX_MON\n",
                argv[0]);
        return 2;
    }
    uint32_t probe = parse_u32(argv[3], "probe");
    uint32_t claim = parse_u32(argv[4], "claim");
    uint32_t form = parse_u32(argv[5], "form");
    uint32_t seen = parse_u32(argv[6], "seen");
    uint32_t caught = parse_u32(argv[7], "caught");
    uint32_t npc_script = parse_u32(argv[8], "NPC script");
    uint32_t events = parse_u32(argv[9], "events");
    uint32_t map_scripts = parse_u32(argv[10], "map scripts");
    uint32_t get_pending = parse_u32(argv[11], "get pending");
    fg_get_box_mon_data = parse_u32(argv[12], "GetBoxMonDataAt");
    fg_get_boxed_mon_ptr = parse_u32(argv[13], "GetBoxedMonPtr");
    fg_zero_box_mon = parse_u32(argv[14], "ZeroBoxMonAt");
    const uint32_t entrypoints[] = {
        probe, claim, form, seen, caught, get_pending, fg_get_box_mon_data,
        fg_get_boxed_mon_ptr, fg_zero_box_mon,
    };
    for (size_t index = 0U;
         index < sizeof(entrypoints) / sizeof(entrypoints[0]); ++index)
        if ((entrypoints[index] & 1U) == 0U
            || !rom_pointer(entrypoints[index] & ~1U))
            fg_die("runtime entrypoint contract failed");
    if (!rom_pointer(npc_script) || !rom_pointer(events)
        || !rom_pointer(map_scripts))
        fg_die("map/script address contract failed");

    struct mLogger logger = {.log = fg_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    fg_initialize_save(argv[2]);
    color_t *video = NULL;
    struct mCore *core = fg_open_core(argv[1], argv[2], &video);

    fg_phase("natural-new-game");
    uint32_t transitions = run_natural_new_game(core, video);
    fg_phase("physical-graph-and-save-init");
    fg_verify_map(core, npc_script, claim, events, map_scripts);
    if (fg_invoke(core, probe) != FG_ABI_MARKER
        || fg_call_thumb(core, get_pending, 0U, 0U, 0U, 0U) == 0U)
        fg_die("Floette gift ABI/acquisition save initialization failed");

    fg_phase("clean-production-fixture");
    fg_install_party(core, 0U);
    fg_clear_boxes(core);
    if (fg_has_ring(core))
        fg_die("new-game fixture already has Mega Ring");
    uint64_t locked_ledger = fg_hash_region(core, FG_LEDGER, FG_LEDGER_SIZE);
    uint64_t locked_flash = fg_hash_region(core, FG_FLASH_LEDGER, FG_LEDGER_SIZE);
    if (fg_invoke(core, claim) != FG_RESULT_LOCKED
        || fg_flag(core) || fg_collection_bit(core, FG_LEDGER)
        || fg_hash_region(core, FG_LEDGER, FG_LEDGER_SIZE) != locked_ledger
        || fg_hash_region(core, FG_FLASH_LEDGER, FG_LEDGER_SIZE) != locked_flash)
        fg_die("Mega Ring gate rejection mutated state");
    if (fg_call_thumb(core, FG_ADD_BAG, FG_MEGA_RING, 1U, 0U, 0U) == 0U
        || !fg_has_ring(core))
        fg_die("production AddBagItem did not install Mega Ring");
    struct FgSnapshot base = fg_take_snapshot(core);

    fg_phase("party-delivery");
    if (fg_invoke(core, claim) != FG_RESULT_SUCCESS
        || read8(core, FG_PLAYER_COUNT) != 1U
        || fg_call_thumb(core, FG_GET_MON_DATA,
                         FG_PLAYER_PARTY, 11U, 0U, 0U) != FG_SPECIES
        || fg_call_thumb(core, FG_GET_MON_DATA,
                         FG_PLAYER_PARTY, 56U, 0U, 0U) != FG_LEVEL
        || !fg_flag(core) || !fg_collection_bit(core, FG_LEDGER)
        || fg_invoke(core, form) != 1U
        || fg_invoke(core, seen) != 1U
        || fg_invoke(core, caught) != 1U)
        fg_die("party delivery/identity/registration failed");

    fg_phase("pc-delivery");
    fg_restore_snapshot(core, &base);
    fg_install_party(core, FG_PARTY_CAPACITY);
    if (fg_invoke(core, claim) != FG_RESULT_SUCCESS
        || read8(core, FG_PLAYER_COUNT) != FG_PARTY_CAPACITY)
        fg_die("full-party PC delivery rejected");
    uint32_t destination_box = read16(core, FG_SPECIAL_BOX);
    uint32_t destination_pos = read16(core, FG_SPECIAL_POS);
    fg_create_mon(core, FG_SPECIES, FG_LEVEL, UINT32_C(0x76543210));
    uint32_t level50_experience = fg_call_thumb(
        core, FG_GET_MON_DATA, FG_SCRATCH, 25U, 0U, 0U);
    if (destination_box >= FG_BOX_COUNT || destination_pos >= FG_BOX_CAPACITY
        || fg_call_thumb(core, fg_get_box_mon_data,
                         destination_box, destination_pos, 11U, 0U) != FG_SPECIES
        || level50_experience == 0U
        || fg_call_thumb(core, fg_get_box_mon_data,
                         destination_box, destination_pos, 25U, 0U)
               != level50_experience
        || !fg_flag(core) || !fg_collection_bit(core, FG_LEDGER))
        fg_die("PC gift Species1029/Lv50/registration failed");

    fg_phase("party-and-pc-full");
    fg_restore_snapshot(core, &base);
    fg_install_party(core, FG_PARTY_CAPACITY);
    fg_fill_boxes(core);
    uint64_t full_ledger = fg_hash_region(core, FG_LEDGER, FG_LEDGER_SIZE);
    uint64_t full_flash = fg_hash_region(core, FG_FLASH_LEDGER, FG_LEDGER_SIZE);
    if (fg_invoke(core, claim) != FG_RESULT_FULL
        || fg_flag(core) || fg_collection_bit(core, FG_LEDGER)
        || read8(core, FG_PLAYER_COUNT) != FG_PARTY_CAPACITY
        || fg_hash_region(core, FG_LEDGER, FG_LEDGER_SIZE) != full_ledger
        || fg_hash_region(core, FG_FLASH_LEDGER, FG_LEDGER_SIZE) != full_flash)
        fg_die("party+PC full rejection mutated claim state");

    fg_phase("durable-party-delivery");
    fg_restore_snapshot(core, &base);
    if (fg_invoke(core, claim) != FG_RESULT_SUCCESS
        || read8(core, FG_PLAYER_COUNT) != 1U
        || !fg_flag(core) || !fg_collection_bit(core, FG_LEDGER)
        || !fg_collection_bit(core, FG_FLASH_LEDGER))
        fg_die("final durable delivery failed");
    free(base.bytes);

    fg_phase("fresh-core-reload");
    fg_close_core(core, video);
    core = fg_open_core(argv[1], argv[2], NULL);
    run_frames(core, 120U, 0U);
    if (fg_call_thumb(core, FG_SAVE_LOAD, 0U, 0U, 0U, 0U) != 1U
        || fg_call_thumb(core, get_pending, 0U, 0U, 0U, 0U) == 0U
        || !fg_has_ring(core) || !fg_flag(core)
        || !fg_collection_bit(core, FG_LEDGER)
        || !fg_collection_bit(core, FG_FLASH_LEDGER)
        || read8(core, FG_PLAYER_COUNT) != 1U
        || fg_call_thumb(core, FG_GET_MON_DATA,
                         FG_PLAYER_PARTY, 11U, 0U, 0U) != FG_SPECIES
        || fg_call_thumb(core, FG_GET_MON_DATA,
                         FG_PLAYER_PARTY, 56U, 0U, 0U) != FG_LEVEL)
        fg_die("fresh-core standard/sector31 reload failed");
    uint64_t once_ledger = fg_hash_region(core, FG_LEDGER, FG_LEDGER_SIZE);
    uint64_t once_flash = fg_hash_region(core, FG_FLASH_LEDGER, FG_LEDGER_SIZE);
    if (fg_invoke(core, claim) != FG_RESULT_ALREADY
        || read8(core, FG_PLAYER_COUNT) != 1U
        || fg_hash_region(core, FG_LEDGER, FG_LEDGER_SIZE) != once_ledger
        || fg_hash_region(core, FG_FLASH_LEDGER, FG_LEDGER_SIZE) != once_flash)
        fg_die("fresh-core once-per-save rejection failed");
    if (fg_log_problem_count != 0U)
        fg_die("mGBA warning/error was emitted");

    fg_phase("complete");
    printf("{\"schema_version\":1,\"task\":\"%s\",\"stage\":69,"
           "\"status\":\"PASS\",\"warnings_errors\":%u,"
           "\"checks\":{"
           "\"physical_npc_script_graph_to_entrypoint\":true,"
           "\"mega_ring_580_gate\":true,"
           "\"party_delivery_species1029_level50\":true,"
           "\"full_party_pc_delivery_species1029_level50\":true,"
           "\"pc_level50_create_mon_experience_identity\":true,"
           "\"party_and_pc_full_unclaimed\":true,"
           "\"claim_flag_14cd\":true,"
           "\"national670_collection_bit850\":true,"
           "\"standard_save_fresh_core_reload\":true,"
           "\"fresh_core_once_rejected\":true},"
           "\"pc_destination\":{\"box\":%" PRIu32 ",\"position\":%" PRIu32 "},"
           "\"core_instances\":2,\"process_runs\":1,"
           "\"framebuffer_transitions\":%" PRIu32 ","
           "\"state_fixture\":\"PRODUCTION_ROM_FUNCTIONS_ONLY\","
           "\"retained_artifacts\":[]}\n",
           "USER-MODERNIZATION-FLOETTE-ETERNAL-GIFT",
           fg_log_problem_count,
           destination_box, destination_pos, transitions);
    fflush(stdout);
    fg_close_core(core, NULL);
    fflush(stderr);
    _Exit(EXIT_SUCCESS);
}
