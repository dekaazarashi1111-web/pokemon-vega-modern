/* Stage68 Mega Stone BP shop exact-ROM stateful smoke.
 *
 * The fixture uses only production ROM entrypoints to create gameplay state:
 * AddBagItem for the Mega Ring / bag fixtures, VegaFactoryAddBattlePoints for
 * BP, FlagGet through the public shop ABI for claims, and the standard save
 * loader for the fresh-core durability check.  No host-test overlay is linked.
 */
#define main mgba_regression_smoke_embedded_main
#include "mgba_regression_smoke.c"
#undef main

#include <string.h>
#include <time.h>

/* Stage68 keeps its exact 14-object graph. The cumulative caller
 * opts into the exact Stage69 15-object graph, never a range. */
#ifndef MEGA_EXPECTED_FACTORY_OBJECT_COUNT
#define MEGA_EXPECTED_FACTORY_OBJECT_COUNT 14U
#endif

#define MEGA_MAX_CALL_STEPS UINT64_C(30000000)
#define MEGA_SAVE_FILE_SIZE UINT32_C(0x20000)
#define MEGA_ABI_MARKER UINT32_C(0xA168)
#define MEGA_LEDGER UINT32_C(0x0203D000)
#define MEGA_LEDGER_SIZE UINT32_C(0x800)
#define MEGA_FACTORY_OFFSET UINT32_C(0x392)
#define MEGA_BALANCE_OFFSET UINT32_C(0)
#define MEGA_FLASH_LEDGER UINT32_C(0x0E01F064)
#define MEGA_FLAG_GET UINT32_C(0x0806DEC5)
#define MEGA_CHECK_BAG UINT32_C(0x08099949)
#define MEGA_ADD_BAG UINT32_C(0x08099A8D)
#define MEGA_REMOVE_BAG UINT32_C(0x08099BE1)
#define MEGA_SET_BAG_POCKETS UINT32_C(0x0809984D)
#define MEGA_SET_SAVE_BLOCK_POINTERS UINT32_C(0x0804B811)
#define MEGA_SAVE_BLOCK1_SLOT UINT32_C(0x03005048)
#define MEGA_SAVE_BLOCK2_SLOT UINT32_C(0x0300504C)
#define MEGA_STORAGE_SLOT UINT32_C(0x03005050)
#define MEGA_SAVE_LOAD UINT32_C(0x080DB4E5)
#define MEGA_FACTORY_ADD_BP UINT32_C(0x092DD9B1)
#define MEGA_BASE_SANITIZE_ITEM UINT32_C(0x0809A2AD)
#define MEGA_CFRU_SANITIZE_ITEM UINT32_C(0x0910FD9D)
#define MEGA_ITEM_GET_NAME UINT32_C(0x0910FDB1)
#define MEGA_ITEM_GET_HOLD_EFFECT UINT32_C(0x0910FDD1)
#define MEGA_ITEM_GET_HOLD_EFFECT_PARAM UINT32_C(0x0910FDF1)
#define MEGA_IS_MEGA_STONE UINT32_C(0x0910FE11)
#define MEGA_HOLD_EFFECT UINT32_C(0x49)
#define MEGA_RING_ITEM UINT16_C(580)
#define MEGA_ITEM_FIRST UINT16_C(999)
#define MEGA_ITEM_MIDDLE UINT16_C(1021)
#define MEGA_ITEM_LAST UINT16_C(1043)
#define MEGA_CLAIM_FIRST UINT16_C(0x14A0)
#define MEGA_CLAIM_MIDDLE UINT16_C(0x14B6)
#define MEGA_CLAIM_LAST UINT16_C(0x14CC)
#define MEGA_RESULT_SUCCESS UINT32_C(0)
#define MEGA_RESULT_LOCKED UINT32_C(3)
#define MEGA_RESULT_INSUFFICIENT UINT32_C(14)
#define MEGA_RESULT_BAG_FULL UINT32_C(15)
#define MEGA_RESULT_ALREADY_CLAIMED UINT32_C(17)

static unsigned mega_log_problem_count;
static struct mCore *mega_log_core;

static time_t mega_fixed_unix_time(struct mRTCSource *source)
{
    (void)source;
    return (time_t)946684800;
}

static void mega_die(const char *message)
{
    fprintf(stderr, "mgba-modernization-mega-shop: %s\n", message);
    exit(1);
}

static void mega_phase(const char *phase)
{
    fprintf(stderr, "mgba-modernization-mega-shop: phase=%s\n", phase);
    fflush(stderr);
}

static void mega_log(struct mLogger *logger, int category,
                     enum mLogLevel level, const char *format, va_list args)
{
    (void)logger;
    if (!(level & (mLOG_FATAL | mLOG_ERROR | mLOG_WARN)))
        return;
    /* mGBA emits this host timestamp diagnostic when the same deterministic
     * save is attached to the second core; it is not a ROM warning. */
    if (strstr(mLogCategoryName(category), "Savedata") != NULL
        && strstr(format, "Savegame time offset set") != NULL)
        return;
    ++mega_log_problem_count;
    fprintf(stderr, "mGBA[%s][0x%02x] pc=%08" PRIx32 ": ",
            mLogCategoryName(category), (unsigned)level,
            mega_log_core
                ? (uint32_t)read_register(mega_log_core, "pc") : 0U);
    vfprintf(stderr, format, args);
    fputc('\n', stderr);
}

static void mega_initialize_save(const char *path)
{
    FILE *stream = fopen(path, "wb");
    if (stream == NULL)
        mega_die("temporary save creation failed");
    uint8_t block[4096];
    memset(block, 0xFF, sizeof(block));
    uint32_t remaining = MEGA_SAVE_FILE_SIZE;
    while (remaining != 0U) {
        size_t amount = remaining < sizeof(block) ? remaining : sizeof(block);
        if (fwrite(block, 1U, amount, stream) != amount) {
            (void)fclose(stream);
            mega_die("temporary save initialization failed");
        }
        remaining -= (uint32_t)amount;
    }
    if (fclose(stream) != 0)
        mega_die("temporary save close failed");
}

static void mega_write16(struct mCore *core, uint32_t address, uint16_t value)
{
    core->rawWrite16(core, address, -1, value);
}

static uint32_t mega_read_u32_unaligned(struct mCore *core, uint32_t address)
{
    return (uint32_t)read8(core, address)
        | ((uint32_t)read8(core, address + 1U) << 8U)
        | ((uint32_t)read8(core, address + 2U) << 16U)
        | ((uint32_t)read8(core, address + 3U) << 24U);
}

static uint64_t mega_hash_region(struct mCore *core, uint32_t address,
                                 size_t size)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    for (size_t index = 0; index < size; ++index) {
        hash ^= read8(core, address + (uint32_t)index);
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

static uint32_t mega_call_thumb(struct mCore *core, uint32_t function,
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
    uint64_t steps = 0;
    while ((((uint32_t)read_register(core, "pc")) & ~1U)
           != UINT32_C(0x08000002)) {
        if (++steps > MEGA_MAX_CALL_STEPS) {
            fprintf(stderr,
                    "mgba-modernization-mega-shop: instruction limit "
                    "function=%#010" PRIx32 " pc=%#010" PRIx32 "\n",
                    function, (uint32_t)read_register(core, "pc"));
            mega_die("runtime instruction limit exceeded");
        }
        core->step(core);
    }
    uint32_t result = (uint32_t)read_register(core, "r0");
    restore_cpu(core, &original);
    return result;
}

static uint32_t mega_invoke_result(struct mCore *core, uint32_t entrypoint,
                                   uint32_t argument)
{
    mega_write16(core, SPECIAL_VAR_RESULT, UINT16_C(0xFFFF));
    uint32_t direct = mega_call_thumb(core, entrypoint, argument, 0, 0, 0);
    uint32_t script = read16(core, SPECIAL_VAR_RESULT);
    if ((direct & UINT32_C(0xFFFF)) != script) {
        fprintf(stderr,
                "mgba-modernization-mega-shop: direct/script result differs "
                "entry=%#010" PRIx32 " direct=%" PRIu32
                " script=%" PRIu32 "\n",
                entrypoint, direct, script);
        exit(1);
    }
    return script;
}

static bool mega_has_item(struct mCore *core, uint16_t item, uint16_t quantity)
{
    return mega_call_thumb(core, MEGA_CHECK_BAG, item, quantity, 0, 0) != 0U;
}

static void mega_empty_item(struct mCore *core, uint16_t item)
{
    uint32_t removed = 0U;
    while (mega_has_item(core, item, 1U)) {
        if (mega_call_thumb(core, MEGA_REMOVE_BAG, item, 1U, 0, 0) == 0U)
            mega_die("bag item could not be removed");
        if (++removed > 2000U)
            mega_die("bag cleanup exceeded item capacity");
    }
}

static uint32_t mega_fill_item(struct mCore *core, uint16_t item)
{
    uint32_t count = 0U;
    for (uint32_t chunk = 1024U; chunk != 0U; chunk >>= 1U) {
        while (mega_call_thumb(core, MEGA_ADD_BAG, item, chunk, 0, 0) != 0U) {
            count += chunk;
            if (count > 4096U)
                mega_die("bag fill exceeded item capacity");
        }
    }
    if (count == 0U || !mega_has_item(core, item, 1U)
        || mega_call_thumb(core, MEGA_ADD_BAG, item, 1U, 0, 0) != 0U)
        mega_die("bag fill did not create a full stack");
    return count;
}

static void mega_remove_count(struct mCore *core, uint16_t item,
                              uint32_t count)
{
    if (count == 0U || count > UINT16_MAX
        || mega_call_thumb(core, MEGA_REMOVE_BAG, item, count, 0, 0) == 0U
        || mega_has_item(core, item, 1U))
        mega_die("bag-full fixture cleanup failed");
}

static uint16_t mega_balance(struct mCore *core)
{
    return read16(core, MEGA_LEDGER + MEGA_FACTORY_OFFSET
                         + MEGA_BALANCE_OFFSET);
}

static void mega_add_bp(struct mCore *core, uint16_t amount)
{
    uint32_t status = mega_call_thumb(core, MEGA_FACTORY_ADD_BP,
                                      MEGA_LEDGER, amount, 0, 0);
    if (status != 0U)
        mega_die("VegaFactoryAddBattlePoints rejected fixture BP");
}

static bool mega_flag(struct mCore *core, uint16_t flag)
{
    return mega_call_thumb(core, MEGA_FLAG_GET, flag, 0, 0, 0) != 0U;
}

static void mega_verify_item_consumers(struct mCore *core,
                                       uint32_t item_data)
{
    const uint16_t accepted[] = {999U, 1023U, 1024U, 1043U};
    for (size_t index = 0U;
         index < sizeof(accepted) / sizeof(accepted[0]); ++index) {
        uint16_t item = accepted[index];
        if (mega_call_thumb(core, MEGA_BASE_SANITIZE_ITEM,
                            item, 0U, 0U, 0U) != item
            || mega_call_thumb(core, MEGA_CFRU_SANITIZE_ITEM,
                               item, 0U, 0U, 0U) != item
            || mega_call_thumb(core, MEGA_ITEM_GET_NAME,
                               item, 0U, 0U, 0U)
                != item_data + (uint32_t)item * 40U
            || read8(core, item_data + (uint32_t)item * 40U) == 0U
            || mega_call_thumb(core, MEGA_ITEM_GET_HOLD_EFFECT,
                               item, 0U, 0U, 0U) != MEGA_HOLD_EFFECT
            || mega_call_thumb(core, MEGA_ITEM_GET_HOLD_EFFECT_PARAM,
                               item, 0U, 0U, 0U) != 0U
            || mega_call_thumb(core, MEGA_IS_MEGA_STONE,
                               item, 0U, 0U, 0U) != 1U)
            mega_die("new Mega Stone item consumer acceptance failed");
    }
    if (mega_call_thumb(core, MEGA_BASE_SANITIZE_ITEM,
                        1044U, 0U, 0U, 0U) != 0U
        || mega_call_thumb(core, MEGA_CFRU_SANITIZE_ITEM,
                           1044U, 0U, 0U, 0U) != 0U
        || mega_call_thumb(core, MEGA_ITEM_GET_NAME,
                           1044U, 0U, 0U, 0U) != item_data
        || mega_call_thumb(core, MEGA_ITEM_GET_HOLD_EFFECT,
                           1044U, 0U, 0U, 0U) != 0U
        || mega_call_thumb(core, MEGA_ITEM_GET_HOLD_EFFECT_PARAM,
                           1044U, 0U, 0U, 0U) != 0U
        || mega_call_thumb(core, MEGA_IS_MEGA_STONE,
                           1044U, 0U, 0U, 0U) != 0U)
        mega_die("first rejected Mega Stone item boundary failed");
}

static bool mega_ewram_pointer(uint32_t value)
{
    return value >= UINT32_C(0x02000000)
        && value < UINT32_C(0x02040000);
}

static void mega_prepare_fresh_save_pointers(struct mCore *core)
{
    uint32_t save1 = read32(core, MEGA_SAVE_BLOCK1_SLOT);
    uint32_t save2 = read32(core, MEGA_SAVE_BLOCK2_SLOT);
    uint32_t storage = read32(core, MEGA_STORAGE_SLOT);
    if (!mega_ewram_pointer(save1) || !mega_ewram_pointer(save2)
        || !mega_ewram_pointer(storage)) {
        (void)mega_call_thumb(core, MEGA_SET_SAVE_BLOCK_POINTERS,
                              0U, 0U, 0U, 0U);
        save1 = read32(core, MEGA_SAVE_BLOCK1_SLOT);
        save2 = read32(core, MEGA_SAVE_BLOCK2_SLOT);
        storage = read32(core, MEGA_STORAGE_SLOT);
    }
    if (!mega_ewram_pointer(save1) || !mega_ewram_pointer(save2)
        || !mega_ewram_pointer(storage)) {
        fprintf(stderr,
                "mgba-modernization-mega-shop: fresh save pointers "
                "sb1=%08" PRIx32 " sb2=%08" PRIx32
                " storage=%08" PRIx32 "\n",
                save1, save2, storage);
        mega_die("fresh-core save pointers were not initialized");
    }
}

static void mega_verify_map(struct mCore *core, uint32_t npc_script,
                            uint32_t open_entry, uint32_t expected_events,
                            uint32_t expected_map_scripts)
{
    uint32_t map_root = read32(core, ROM_BASE + UINT32_C(0x54B0C));
    uint32_t group96 = read32(core, map_root + 96U * 4U);
    uint32_t header = read32(core, group96 + 5U * 4U);
    uint32_t events = read32(core, header + 4U);
    uint32_t scripts = read32(core, header + 8U);
    uint32_t objects = read32(core, events + 4U);
    uint32_t shop = 0U;
    bool clone_seen = false;
    if (!rom_pointer(map_root) || !rom_pointer(group96) || !rom_pointer(header)
        || events != expected_events || scripts != expected_map_scripts
        || !rom_pointer(objects) || read8(core, events) != MEGA_EXPECTED_FACTORY_OBJECT_COUNT
        || read8(core, events + 1U) != 10U
        || read8(core, events + 2U) != 0U
        || read8(core, events + 3U) != 7U)
        mega_die("Factory map root/events/scripts graph is invalid");
    for (uint32_t index = 0U; index < MEGA_EXPECTED_FACTORY_OBJECT_COUNT; ++index) {
        uint32_t object = objects + index * 0x18U;
        if (read8(core, object) == 3U)
            clone_seen = true;
        if (read8(core, object) == 14U)
            shop = object;
    }
    if (!clone_seen || shop == 0U
        || read8(core, shop + 1U) != 62U
        || read16(core, shop + 4U) != 24U
        || read16(core, shop + 6U) != 19U
        || read8(core, shop + 8U) != 3U
        || read32(core, shop + 0x10U) != npc_script
        || read8(core, npc_script) != 0x6AU
        || read8(core, npc_script + 1U) != 0x5AU
        || read8(core, npc_script + 2U) != 0x23U
        || mega_read_u32_unaligned(core, npc_script + 3U) != open_entry)
        mega_die("physical Mega Stone shop NPC script graph is invalid");
}

static struct mCore *mega_open_core(const char *rom_path,
                                    const char *save_path,
                                    color_t **video_out)
{
    static struct mRTCSource rtc = {
        .sample = NULL,
        .unixTime = mega_fixed_unix_time,
        .serialize = NULL,
        .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(rom_path);
    if (core == NULL || !core->init(core))
        mega_die("core initialization failed");
    if (!mCoreLoadFile(core, rom_path))
        mega_die("ROM load failed");
    if (!mCoreLoadSaveFile(core, save_path, false))
        mega_die("save attachment failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    color_t *video = NULL;
    if (video_out != NULL) {
        video = calloc(GBA_WIDTH * GBA_HEIGHT, sizeof(*video));
        if (video == NULL)
            mega_die("video allocation failed");
        core->setVideoBuffer(core, video, GBA_WIDTH);
        *video_out = video;
    }
    mega_log_core = core;
    core->reset(core);
    return core;
}

static void mega_close_core(struct mCore *core, color_t *video)
{
    free(video);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    mega_log_core = NULL;
}

int main(int argc, char **argv)
{
    if (argc != 14) {
        fprintf(stderr,
                "usage: %s ROM SAVE PROBE ENSURE BALANCE UNLOCK CLAIM "
                "PURCHASE OPEN NPC_SCRIPT EVENTS MAP_SCRIPTS ITEM_DATA\n",
                argv[0]);
        return 2;
    }
    uint32_t probe = parse_u32(argv[3], "probe");
    uint32_t ensure = parse_u32(argv[4], "ensure");
    uint32_t balance = parse_u32(argv[5], "balance");
    uint32_t unlock = parse_u32(argv[6], "unlock");
    uint32_t claim = parse_u32(argv[7], "claim");
    uint32_t purchase = parse_u32(argv[8], "purchase");
    uint32_t open_entry = parse_u32(argv[9], "open");
    uint32_t npc_script = parse_u32(argv[10], "NPC script");
    uint32_t events = parse_u32(argv[11], "events");
    uint32_t map_scripts = parse_u32(argv[12], "map scripts");
    uint32_t item_data = parse_u32(argv[13], "item data");
    const uint32_t entrypoints[] = {
        probe, ensure, balance, unlock, claim, purchase, open_entry,
    };
    for (size_t index = 0U;
         index < sizeof(entrypoints) / sizeof(entrypoints[0]); ++index) {
        if ((entrypoints[index] & 1U) == 0U
            || !rom_pointer(entrypoints[index] & ~1U))
            mega_die("runtime entrypoint contract failed");
    }
    if (!rom_pointer(npc_script) || !rom_pointer(events)
        || !rom_pointer(map_scripts) || !rom_pointer(item_data))
        mega_die("map/script address contract failed");

    struct mLogger logger = {.log = mega_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    mega_initialize_save(argv[2]);
    color_t *video = NULL;
    struct mCore *core = mega_open_core(argv[1], argv[2], &video);

    mega_phase("natural-new-game");
    uint32_t transitions = run_natural_new_game(core, video);
    mega_phase("physical-graph-and-probe");
    mega_verify_map(core, npc_script, open_entry, events, map_scripts);
    mega_verify_item_consumers(core, item_data);
    if (mega_invoke_result(core, probe, 0U) != MEGA_ABI_MARKER
        || mega_invoke_result(core, ensure, 0U) != 1U
        || mega_invoke_result(core, balance, 0U) != 0U)
        mega_die("Mega shop ABI/save initialization failed");

    mega_phase("mega-ring-gate");
    if (mega_invoke_result(core, unlock, 0U) != 0U)
        mega_die("index 0 unlocked without Mega Ring");
    uint64_t locked_ledger = mega_hash_region(core, MEGA_LEDGER,
                                               MEGA_LEDGER_SIZE);
    uint64_t locked_flash = mega_hash_region(core, MEGA_FLASH_LEDGER,
                                              MEGA_LEDGER_SIZE);
    if (mega_invoke_result(core, purchase, 0U) != MEGA_RESULT_LOCKED
        || mega_hash_region(core, MEGA_LEDGER, MEGA_LEDGER_SIZE)
               != locked_ledger
        || mega_hash_region(core, MEGA_FLASH_LEDGER, MEGA_LEDGER_SIZE)
               != locked_flash
        || mega_has_item(core, MEGA_ITEM_FIRST, 1U)
        || mega_flag(core, MEGA_CLAIM_FIRST))
        mega_die("Mega Ring gate rejection mutated state");
    if (mega_call_thumb(core, MEGA_ADD_BAG, MEGA_RING_ITEM, 1U, 0, 0) == 0U
        || !mega_has_item(core, MEGA_RING_ITEM, 1U)
        || mega_invoke_result(core, unlock, 0U) != 1U)
        mega_die("Mega Ring production bag gate did not unlock shop");

    mega_phase("insufficient-bp");
    mega_empty_item(core, MEGA_ITEM_MIDDLE);
    mega_add_bp(core, 15U);
    uint64_t insufficient_ledger = mega_hash_region(core, MEGA_LEDGER,
                                                     MEGA_LEDGER_SIZE);
    uint64_t insufficient_flash = mega_hash_region(core, MEGA_FLASH_LEDGER,
                                                    MEGA_LEDGER_SIZE);
    if (mega_invoke_result(core, purchase, 22U) != MEGA_RESULT_INSUFFICIENT
        || mega_balance(core) != 15U
        || mega_hash_region(core, MEGA_LEDGER, MEGA_LEDGER_SIZE)
               != insufficient_ledger
        || mega_hash_region(core, MEGA_FLASH_LEDGER, MEGA_LEDGER_SIZE)
               != insufficient_flash
        || mega_has_item(core, MEGA_ITEM_MIDDLE, 1U)
        || mega_flag(core, MEGA_CLAIM_MIDDLE))
        mega_die("insufficient-BP rejection mutated state");

    mega_phase("bag-full");
    mega_add_bp(core, 85U);
    uint32_t full_count = mega_fill_item(core, MEGA_ITEM_MIDDLE);
    uint64_t full_ledger = mega_hash_region(core, MEGA_LEDGER,
                                            MEGA_LEDGER_SIZE);
    uint64_t full_flash = mega_hash_region(core, MEGA_FLASH_LEDGER,
                                           MEGA_LEDGER_SIZE);
    if (mega_invoke_result(core, purchase, 22U) != MEGA_RESULT_BAG_FULL
        || mega_balance(core) != 100U
        || mega_hash_region(core, MEGA_LEDGER, MEGA_LEDGER_SIZE) != full_ledger
        || mega_hash_region(core, MEGA_FLASH_LEDGER, MEGA_LEDGER_SIZE)
               != full_flash
        || !mega_has_item(core, MEGA_ITEM_MIDDLE, 1U)
        || mega_call_thumb(core, MEGA_ADD_BAG,
                           MEGA_ITEM_MIDDLE, 1U, 0, 0) != 0U
        || mega_flag(core, MEGA_CLAIM_MIDDLE))
        mega_die("bag-full rejection mutated state");
    mega_remove_count(core, MEGA_ITEM_MIDDLE, full_count);

    mega_phase("representative-purchases");
    const uint16_t indices[] = {0U, 22U, 44U};
    const uint16_t items[] = {
        MEGA_ITEM_FIRST, MEGA_ITEM_MIDDLE, MEGA_ITEM_LAST,
    };
    const uint16_t flags[] = {
        MEGA_CLAIM_FIRST, MEGA_CLAIM_MIDDLE, MEGA_CLAIM_LAST,
    };
    const uint16_t expected_balance[] = {84U, 68U, 52U};
    for (size_t index = 0U; index < 3U; ++index) {
        mega_empty_item(core, items[index]);
        if (mega_invoke_result(core, purchase, indices[index])
                != MEGA_RESULT_SUCCESS
            || mega_invoke_result(core, balance, 0U)
                != expected_balance[index]
            || !mega_has_item(core, items[index], 1U)
            || !mega_flag(core, flags[index])
            || mega_invoke_result(core, claim, indices[index]) != 1U)
            mega_die("representative 16 BP purchase failed");
    }

    mega_phase("fresh-core-reload");
    mega_close_core(core, video);
    core = mega_open_core(argv[1], argv[2], NULL);
    run_frames(core, 180U, 0U);
    mega_prepare_fresh_save_pointers(core);
    uint32_t load_status = mega_call_thumb(
        core, MEGA_SAVE_LOAD, 0U, 0U, 0U, 0U);
    (void)mega_call_thumb(core, MEGA_SET_BAG_POCKETS, 0U, 0U, 0U, 0U);
    uint32_t ensure_status = mega_invoke_result(core, ensure, 0U);
    uint32_t loaded_balance = mega_invoke_result(core, balance, 0U);
    bool loaded_ring = mega_has_item(core, MEGA_RING_ITEM, 1U);
    if (load_status != 1U || ensure_status != 1U
        || loaded_balance != 52U || !loaded_ring) {
        fprintf(stderr,
                "mgba-modernization-mega-shop: fresh reload "
                "load=%" PRIu32 " ensure=%" PRIu32
                " balance=%" PRIu32 " ring=%u\n",
                load_status, ensure_status, loaded_balance,
                loaded_ring ? 1U : 0U);
        mega_die("fresh-core standard/sector31 reload failed");
    }
    uint64_t reload_ledger = mega_hash_region(core, MEGA_LEDGER,
                                               MEGA_LEDGER_SIZE);
    uint64_t reload_flash = mega_hash_region(core, MEGA_FLASH_LEDGER,
                                              MEGA_LEDGER_SIZE);
    for (size_t index = 0U; index < 3U; ++index) {
        if (!mega_has_item(core, items[index], 1U)
            || !mega_flag(core, flags[index])
            || mega_invoke_result(core, claim, indices[index]) != 1U
            || mega_invoke_result(core, purchase, indices[index])
                != MEGA_RESULT_ALREADY_CLAIMED
            || mega_balance(core) != 52U
            || mega_hash_region(core, MEGA_LEDGER, MEGA_LEDGER_SIZE)
                != reload_ledger
            || mega_hash_region(core, MEGA_FLASH_LEDGER, MEGA_LEDGER_SIZE)
                != reload_flash)
            mega_die("fresh-core once-per-save rejection failed");
    }
    mega_close_core(core, NULL);
    if (mega_log_problem_count != 0U)
        mega_die("mGBA warning/error was emitted");

    mega_phase("complete");
    printf("{\"schema_version\":1,\"stage\":68,\"status\":\"PASS\","
           "\"warnings_errors\":%u,\"checks\":{"
           "\"physical_npc_script_graph_to_entrypoint\":true,"
           "\"item_consumer_boundaries_999_1023_1024_1043_1044\":true,"
           "\"name_hold_effect_and_is_mega_stone_consumers\":true,"
           "\"probe_and_save_init\":true,\"mega_ring_580_gate\":true,"
           "\"insufficient_bp_no_mutation\":true,"
           "\"bag_full_no_mutation\":true,"
           "\"index_0_item_999_price_16\":true,"
           "\"index_22_item_1021_price_16\":true,"
           "\"index_44_item_1043_price_16\":true,"
           "\"claim_flags_14a0_14b6_14cc\":true,"
           "\"fresh_core_normal_save_reload\":true,"
           "\"fresh_core_once_rejected\":true},"
           "\"representative_indices\":[0,22,44],"
           "\"representative_item_ids\":[999,1021,1043],"
           "\"representative_claim_flags\":[5280,5302,5324],"
           "\"accepted_item_boundary_ids\":[999,1023,1024,1043],"
           "\"first_rejected_item_id\":1044,\"hold_effect\":73,"
           "\"price_bp\":16,\"initial_bp\":100,\"final_bp\":52,"
           "\"bag_full_capacity\":%" PRIu32 ","
           "\"core_instances\":2,\"process_runs\":1,"
           "\"framebuffer_transitions\":%" PRIu32 ","
           "\"state_fixture\":\"PRODUCTION_ROM_FUNCTIONS_ONLY\","
           "\"retained_artifacts\":[]}\n",
           mega_log_problem_count, full_count, transitions);
    fflush(stdout);
    fflush(stderr);
    _Exit(EXIT_SUCCESS);
}
