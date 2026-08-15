/* USER-20260816-ACQUISITION-EVENTS exact-ROM fixture for libmGBA 0.10.2. */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define BATTLE_CORE_EMBEDDED
#include "mgba_battle_core_smoke.c"

enum {
    ACQ_SAVE = 0x0203D000,
    ACQ_SAVE_SIZE = 0x800,
    ACQ_FLASH_SAVE = 0x0E01F064,
    ACQ_INNER_OFFSET = 68,
    ACQ_SCRATCH = 0x0203E400,
    ACQ_HOF_OFFSET = 18,
    ACQ_PLAYER_PARTY = 0x020241E4,
    ACQ_PLAYER_PARTY_COUNT = 0x02023F89,
    ACQ_VAR_8004 = 0x02036FF4,
    ACQ_MON_SIZE = 100,
    ACQ_BOX_MON_SIZE = 80,
    ACQ_COMPRESSED_MON_SIZE = 58,
    ACQ_PARTY_SIZE = 6,
    ACQ_BOX_COUNT = 14,
    ACQ_BOX_CAPACITY = 30,
    ACQ_MON_DATA_SPECIES = 11,
    ACQ_TEST_SPECIES = 25,
    ACQ_ADD_BAG_ITEM = 0x08099A8D,
    ACQ_GET_MON_DATA = 0x0803F355,
    ACQ_EVENT_CAPTURE = 0,
    ACQ_EVENT_EGG = 30,
    ACQ_EVENT_GIFT = 54,
    ACQ_EVENT_FOSSIL = 159,
    ACQ_EVENT_EVOLUTION = 175,
    ACQ_EVENT_TRADE = 199,
    ACQ_EVENT_SERVICE = 200,
    ACQ_FOSSIL_ITEM = 583,
};

struct AcqSymbols {
    uint32_t probe;
    uint32_t adapter_probe;
    uint32_t begin;
    uint32_t resolve;
    uint32_t recover;
    uint32_t hatch_register;
    uint32_t is_registered;
    uint32_t save_init;
    uint32_t save_finalize;
    uint32_t save_validate;
    uint32_t inner_init;
    uint32_t inner_finalize;
    uint32_t inner_validate;
    uint32_t save_load;
    uint32_t get_boxed_mon_ptr;
    uint32_t get_box_mon_data;
    uint32_t get_compressed_mon_ptr;
    uint32_t create_compressed_mon;
    uint32_t validator_site;
    uint32_t map_header;
    uint32_t event_header;
    uint32_t object_record;
    uint32_t host_script;
    uint32_t host_wrapper;
    uint32_t egg_script_site;
    uint32_t egg_script_runtime;
    uint32_t egg_species;
    uint32_t evo_pure;
    uint32_t evo_pure_target;
    uint32_t evo_held;
    uint32_t evo_held_target;
    uint32_t evo_held_item;
    uint32_t wild_a;
    uint32_t wild_b;
};

static void acq_die(const char *message)
{
    fprintf(stderr, "mgba-acquisition-smoke: %s\n", message);
    exit(1);
}

static uint32_t acq_number(const char *raw)
{
    char *end = NULL;
    unsigned long value = strtoul(raw, &end, 0);
    if (!raw[0] || !end || *end || value > UINT32_MAX)
        acq_die("invalid numeric argument");
    return (uint32_t)value;
}

static void acq_set(struct AcqSymbols *symbols, const char *key, const char *value)
{
    uint32_t number = acq_number(value);
#define ACQ_FIELD(label, member) \
    if (!strcmp(key, label)) { symbols->member = number; return; }
    ACQ_FIELD("probe", probe)
    ACQ_FIELD("adapter_probe", adapter_probe)
    ACQ_FIELD("begin", begin)
    ACQ_FIELD("resolve", resolve)
    ACQ_FIELD("recover", recover)
    ACQ_FIELD("hatch_register", hatch_register)
    ACQ_FIELD("is_registered", is_registered)
    ACQ_FIELD("save_init", save_init)
    ACQ_FIELD("save_finalize", save_finalize)
    ACQ_FIELD("save_validate", save_validate)
    ACQ_FIELD("inner_init", inner_init)
    ACQ_FIELD("inner_finalize", inner_finalize)
    ACQ_FIELD("inner_validate", inner_validate)
    ACQ_FIELD("save_load", save_load)
    ACQ_FIELD("get_boxed_mon_ptr", get_boxed_mon_ptr)
    ACQ_FIELD("get_box_mon_data", get_box_mon_data)
    ACQ_FIELD("get_compressed_mon_ptr", get_compressed_mon_ptr)
    ACQ_FIELD("create_compressed_mon", create_compressed_mon)
    ACQ_FIELD("validator_site", validator_site)
    ACQ_FIELD("map_header", map_header)
    ACQ_FIELD("event_header", event_header)
    ACQ_FIELD("object_record", object_record)
    ACQ_FIELD("host_script", host_script)
    ACQ_FIELD("host_wrapper", host_wrapper)
    ACQ_FIELD("egg_script_site", egg_script_site)
    ACQ_FIELD("egg_script_runtime", egg_script_runtime)
    ACQ_FIELD("egg_species", egg_species)
    ACQ_FIELD("evo_pure", evo_pure)
    ACQ_FIELD("evo_pure_target", evo_pure_target)
    ACQ_FIELD("evo_held", evo_held)
    ACQ_FIELD("evo_held_target", evo_held_target)
    ACQ_FIELD("evo_held_item", evo_held_item)
    ACQ_FIELD("wild_a", wild_a)
    ACQ_FIELD("wild_b", wild_b)
#undef ACQ_FIELD
    acq_die("unknown argument key");
}

static bool acq_complete(const struct AcqSymbols *symbols)
{
    const uint32_t *values = (const uint32_t *)symbols;
    for (size_t index = 0; index < sizeof(*symbols) / sizeof(*values); ++index)
        if (!values[index]) return false;
    return true;
}

static uint32_t acq_call(struct mCore *core, uint32_t function,
                         uint32_t r0, uint32_t r1, uint32_t r2, uint32_t r3);
static void acq_expect(uint32_t observed, uint32_t expected,
                       const char *label);

static void acq_clear(struct mCore *core, uint32_t address, unsigned size)
{
    for (unsigned index = 0; index < size; ++index)
        write8(core, address + index, 0);
}

static void acq_read_bytes(struct mCore *core, uint32_t address,
                           uint8_t *destination, size_t size)
{
    for (size_t index = 0; index < size; ++index)
        destination[index] = read8(core, address + (uint32_t)index);
}

static void acq_write_bytes(struct mCore *core, uint32_t address,
                            const uint8_t *source, size_t size)
{
    for (size_t index = 0; index < size; ++index)
        write8(core, address + (uint32_t)index, source[index]);
}

static uint64_t acq_hash_bytes(struct mCore *core, uint32_t address,
                               size_t size, uint64_t hash)
{
    for (size_t index = 0; index < size; ++index) {
        hash ^= read8(core, address + (uint32_t)index);
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

static bool acq_regions_equal(struct mCore *core, uint32_t left,
                              uint32_t right, size_t size)
{
    for (size_t index = 0; index < size; ++index) {
        if (read8(core, left + (uint32_t)index)
            != read8(core, right + (uint32_t)index))
            return false;
    }
    return true;
}

static void acq_fill_party(struct mCore *core)
{
    uint8_t image[ACQ_MON_SIZE];
    create_mon(core, ACQ_PLAYER_PARTY, ACQ_TEST_SPECIES, 20U);
    acq_read_bytes(core, ACQ_PLAYER_PARTY, image, sizeof(image));
    for (uint32_t slot = 0; slot < ACQ_PARTY_SIZE; ++slot)
        acq_write_bytes(core, ACQ_PLAYER_PARTY + slot * ACQ_MON_SIZE,
                        image, sizeof(image));
    write8(core, ACQ_PLAYER_PARTY_COUNT, ACQ_PARTY_SIZE);
}

static uint64_t acq_storage_hash(struct mCore *core,
                                 const struct AcqSymbols *symbols)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    hash = acq_hash_bytes(core, ACQ_PLAYER_PARTY,
                          ACQ_PARTY_SIZE * ACQ_MON_SIZE, hash);
    hash = acq_hash_bytes(core, ACQ_PLAYER_PARTY_COUNT, 1U, hash);
    for (uint32_t box = 0; box < ACQ_BOX_COUNT; ++box) {
        for (uint32_t position = 0; position < ACQ_BOX_CAPACITY; ++position) {
            uint32_t compressed = acq_call(
                core, symbols->get_compressed_mon_ptr, box, position, 0, 0);
            if (compressed < 0x02000000U
                || compressed + ACQ_COMPRESSED_MON_SIZE > 0x02040000U)
                acq_die("compressed-mon pointer is outside EWRAM");
            hash = acq_hash_bytes(
                core, compressed, ACQ_COMPRESSED_MON_SIZE, hash);
        }
    }
    return hash;
}

static void acq_fill_boxes(struct mCore *core,
                           const struct AcqSymbols *symbols)
{
    for (uint32_t box = 0; box < ACQ_BOX_COUNT; ++box) {
        for (uint32_t position = 0; position < ACQ_BOX_CAPACITY; ++position) {
            uint32_t compressed = acq_call(
                core, symbols->get_compressed_mon_ptr, box, position, 0, 0);
            if (compressed < 0x02000000U
                || compressed + ACQ_COMPRESSED_MON_SIZE > 0x02040000U)
                acq_die("compressed-mon pointer is outside EWRAM");
            (void)acq_call(core, symbols->create_compressed_mon,
                           ACQ_PLAYER_PARTY, compressed, 0, 0);
            acq_expect(acq_call(core, symbols->get_box_mon_data,
                                box, position, 11U, 0),
                       ACQ_TEST_SPECIES, "filled boxed-mon species");
        }
    }
}

static uint32_t acq_read_u32_bytes(struct mCore *core, uint32_t address)
{
    return (uint32_t)read8(core, address)
        | (uint32_t)read8(core, address + 1U) << 8
        | (uint32_t)read8(core, address + 2U) << 16
        | (uint32_t)read8(core, address + 3U) << 24;
}

static uint32_t acq_call(struct mCore *core, uint32_t function,
                         uint32_t r0, uint32_t r1, uint32_t r2, uint32_t r3)
{
    struct CpuState original = capture_cpu_state(core);
    uint32_t cpsr = (uint32_t)original.registers[16];
    uint32_t instructions = 0;
    write_register(core, "cpsr", cpsr | 0xA0U);
    write_register(core, "lr", 0x08000001U);
    write_register(core, "r0", r0);
    write_register(core, "r1", r1);
    write_register(core, "r2", r2);
    write_register(core, "r3", r3);
    write_register(core, "pc", function | 1U);
    while ((((uint32_t)read_register(core, "pc")) & ~1U) != 0x08000002U) {
        if (++instructions > 50000000U) {
            fprintf(stderr,
                    "mgba-acquisition-smoke: direct-call-timeout function=0x%08" PRIx32 "\n",
                    function);
            acq_die("bounded direct ROM call exceeded instruction limit");
        }
        core->step(core);
    }
    uint32_t result = (uint32_t)read_register(core, "r0");
    restore_cpu_state(core, &original);
    return result;
}

static void acq_expect(uint32_t observed, uint32_t expected, const char *label)
{
    if (observed != expected) {
        fprintf(stderr, "mgba-acquisition-smoke: %s=%" PRIu32
                " expected=%" PRIu32 "\n", label, observed, expected);
        exit(1);
    }
}

static void acq_check_physical(struct mCore *core,
                               const struct AcqSymbols *symbols)
{
    if (read8(core, symbols->validator_site) != 0x00U
        || read8(core, symbols->validator_site + 1U) != 0x4BU
        || read8(core, symbols->validator_site + 2U) != 0x18U
        || read8(core, symbols->validator_site + 3U) != 0x47U
        || read32(core, symbols->validator_site + 4U)
            != (symbols->save_validate | 1U)) {
        acq_die("save validator trampoline differs");
    }
    if (read32(core, symbols->map_header + 4U) != symbols->event_header
        || read32(core, symbols->object_record + 0x10U) != symbols->host_script
        || read8(core, symbols->host_script) != 0x6AU
        || read8(core, symbols->host_script + 1U) != 0x5AU
        || read8(core, symbols->host_script + 2U) != 0x23U
        || acq_read_u32_bytes(core, symbols->host_script + 3U)
            != (symbols->host_wrapper | 1U)) {
        acq_die("representative physical host chain differs");
    }
    if (read8(core, symbols->egg_script_site) != 0x05U
        || acq_read_u32_bytes(core, symbols->egg_script_site + 1U)
            != symbols->egg_script_runtime
        || read8(core, symbols->egg_script_runtime) != 0x69U
        || read8(core, symbols->egg_script_runtime + 1U) != 0x0FU
        || read8(core, symbols->egg_script_runtime + 2U) != 0x00U
        || acq_read_u32_bytes(core, symbols->egg_script_runtime + 3U)
            != 0x081A5D79U
        || read8(core, symbols->egg_script_runtime + 7U) != 0x09U
        || read8(core, symbols->egg_script_runtime + 8U) != 0x04U
        || read8(core, symbols->egg_script_runtime + 9U) != 0x25U
        || read16(core, symbols->egg_script_runtime + 10U) != 0x00C2U
        || read8(core, symbols->egg_script_runtime + 12U) != 0x27U
        || read8(core, symbols->egg_script_runtime + 13U) != 0x23U
        || acq_read_u32_bytes(core, symbols->egg_script_runtime + 14U)
            != (symbols->hatch_register | 1U)
        || read8(core, symbols->egg_script_runtime + 18U) != 0x6BU
        || read8(core, symbols->egg_script_runtime + 19U) != 0x02U) {
        acq_die("egg-hatch registration script chain differs");
    }
    if (read16(core, symbols->evo_pure) != 7U
        || read16(core, symbols->evo_pure + 2U) != 395U
        || read16(core, symbols->evo_pure + 4U) != symbols->evo_pure_target
        || read16(core, symbols->evo_pure + 6U) != 0U) {
        acq_die("representative link-cable evolution differs");
    }
    if (read16(core, symbols->evo_held) != 35U
        || read16(core, symbols->evo_held + 2U) != 395U
        || read16(core, symbols->evo_held + 4U) != symbols->evo_held_target
        || read16(core, symbols->evo_held + 6U) != symbols->evo_held_item) {
        acq_die("representative held-item link evolution differs");
    }
    if (read16(core, symbols->wild_a) != 255U
        || read16(core, symbols->wild_b) != 255U) {
        acq_die("wild internal species correction differs");
    }
}

int main(int argc, char **argv)
{
    if (argc < 4) {
        fprintf(stderr, "usage: %s ROM SHA key=value...\n", argv[0]);
        return 2;
    }
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64 || strcmp(rom_sha256, argv[2]))
        acq_die("ROM SHA-256 mismatch");
    struct AcqSymbols symbols = {0};
    for (int index = 3; index < argc; ++index) {
        char argument[192];
        if (strlen(argv[index]) >= sizeof(argument))
            acq_die("argument too long");
        strcpy(argument, argv[index]);
        char *equals = strchr(argument, '=');
        if (!equals) acq_die("argument lacks equals");
        *equals = '\0';
        acq_set(&symbols, argument, equals + 1);
    }
    if (!acq_complete(&symbols)) acq_die("required arguments are incomplete");

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {.sample = NULL, .unixTime = fixed_unix_time,
                             .serialize = NULL, .deserialize = NULL};
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) acq_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1])) acq_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    run_trace_prefix(core);
    if (log_problem_count) acq_die("mGBA warned/errored during field boot");

    acq_check_physical(core, &symbols);
    acq_expect(acq_call(core, symbols.probe, 0, 0, 0, 0), 0xAC51U, "core probe");
    acq_expect(acq_call(core, symbols.adapter_probe, 0, 0, 0, 0), 0xA926U,
               "adapter probe");

    acq_clear(core, ACQ_SCRATCH, ACQ_SAVE_SIZE);
    (void)acq_call(core, symbols.save_init, ACQ_SCRATCH, 0, 0, 0);
    acq_expect(acq_call(core, symbols.save_validate, ACQ_SCRATCH,
                        ACQ_SAVE_SIZE, 0, 0), 0U, "outer zero-inner validation");
    acq_expect(acq_call(core, symbols.inner_validate,
                        ACQ_SCRATCH + ACQ_INNER_OFFSET, 0, 0, 0), 0U,
               "zero inner validation");
    (void)acq_call(core, symbols.inner_init,
                   ACQ_SCRATCH + ACQ_INNER_OFFSET, 0, 0, 0);
    (void)acq_call(core, symbols.save_finalize, ACQ_SCRATCH, 0, 0, 0);
    acq_expect(acq_call(core, symbols.inner_validate,
                        ACQ_SCRATCH + ACQ_INNER_OFFSET, 0, 0, 0), 1U,
               "initialized inner validation");
    acq_expect(acq_call(core, symbols.save_validate, ACQ_SCRATCH,
                        ACQ_SAVE_SIZE, 0, 0), 0U, "nested outer validation");
    write8(core, ACQ_SCRATCH + ACQ_INNER_OFFSET + 32U,
           read8(core, ACQ_SCRATCH + ACQ_INNER_OFFSET + 32U) ^ 1U);
    (void)acq_call(core, symbols.save_finalize, ACQ_SCRATCH, 0, 0, 0);
    acq_expect(acq_call(core, symbols.save_validate, ACQ_SCRATCH,
                        ACQ_SAVE_SIZE, 0, 0), 15U, "nested CRC rejection");
    (void)acq_call(core, symbols.inner_finalize,
                   ACQ_SCRATCH + ACQ_INNER_OFFSET, 0, 0, 0);

    acq_clear(core, ACQ_SAVE, ACQ_SAVE_SIZE);
    (void)acq_call(core, symbols.save_init, ACQ_SAVE, 0, 0, 0);
    acq_expect(acq_call(core, symbols.begin, 0xFFFFU, 0, 0, 0), 8U,
               "invalid selection after migration");
    acq_expect(acq_call(core, symbols.save_validate, ACQ_SAVE,
                        ACQ_SAVE_SIZE, 0, 0), 0U, "migrated outer validation");
    acq_expect(acq_call(core, symbols.inner_validate,
                        ACQ_SAVE + ACQ_INNER_OFFSET, 0, 0, 0), 1U,
               "migrated inner validation");
    acq_expect(acq_call(core, symbols.save_validate, ACQ_FLASH_SAVE,
                        ACQ_SAVE_SIZE, 0, 0), 0U,
               "migrated flash validation");
    if (!acq_regions_equal(core, ACQ_SAVE, ACQ_FLASH_SAVE, ACQ_SAVE_SIZE))
        acq_die("first migration was not serialized to the save sector");
    acq_expect(acq_call(core, symbols.recover, 0, 0, 0, 0), 0U,
               "empty recovery");
    struct Snapshot ready = take_snapshot(core);

    acq_expect(acq_call(core, symbols.begin, ACQ_EVENT_CAPTURE, 0, 0, 0), 3U,
               "locked capture");
    restore_snapshot(core, &ready);
    write8(core, ACQ_SAVE + ACQ_HOF_OFFSET, 1U);
    (void)acq_call(core, symbols.save_finalize, ACQ_SAVE, 0, 0, 0);
    struct Snapshot unlocked = take_snapshot(core);

    acq_expect(acq_call(core, symbols.begin, ACQ_EVENT_CAPTURE, 0, 0, 0), 1U,
               "capture begin for reset");
    uint8_t serialized[ACQ_SAVE_SIZE];
    {
        uint32_t prepared_status = acq_call(
            core, symbols.save_validate, ACQ_FLASH_SAVE,
            ACQ_SAVE_SIZE, 0, 0);
        if (prepared_status != 0U) {
            fprintf(stderr,
                    "prepared-debug status=%" PRIu32
                    " flash=%02x%02x%02x%02x ram=%02x%02x%02x%02x\n",
                    prepared_status,
                    read8(core, ACQ_FLASH_SAVE),
                    read8(core, ACQ_FLASH_SAVE + 1U),
                    read8(core, ACQ_FLASH_SAVE + 2U),
                    read8(core, ACQ_FLASH_SAVE + 3U),
                    read8(core, ACQ_SAVE), read8(core, ACQ_SAVE + 1U),
                    read8(core, ACQ_SAVE + 2U), read8(core, ACQ_SAVE + 3U));
        }
        acq_expect(prepared_status, 0U, "prepared flash validation");
    }
    acq_read_bytes(core, ACQ_FLASH_SAVE, serialized, sizeof(serialized));
    acq_clear(core, ACQ_SAVE, ACQ_SAVE_SIZE);
    acq_write_bytes(core, ACQ_SAVE, serialized, sizeof(serialized));
    acq_expect(acq_call(core, symbols.save_validate, ACQ_SAVE,
                        ACQ_SAVE_SIZE, 0, 0), 0U,
               "serialized reload validation");
    acq_expect(acq_call(core, symbols.recover, 0, 0, 0, 0), 14U,
               "capture reset recovery");
    if (!acq_regions_equal(core, ACQ_SAVE, ACQ_FLASH_SAVE, ACQ_SAVE_SIZE))
        acq_die("recovered acquisition save was not reserialized");

    restore_snapshot(core, &unlocked);
    acq_expect(acq_call(core, symbols.begin, ACQ_EVENT_CAPTURE, 0, 0, 0), 1U,
               "capture begin");
    acq_expect(acq_call(core, symbols.resolve, 1U, 0, 0, 0), 0U,
               "capture commit");
    acq_expect(acq_call(core, symbols.begin, ACQ_EVENT_CAPTURE, 0, 0, 0), 4U,
               "capture duplicate");

    restore_snapshot(core, &unlocked);
    acq_expect(acq_call(core, symbols.begin, ACQ_EVENT_GIFT, 0, 0, 0), 0U,
               "gift commit");
    acq_expect(acq_call(core, symbols.begin, ACQ_EVENT_GIFT, 0, 0, 0), 4U,
               "gift duplicate");

    restore_snapshot(core, &unlocked);
    acq_clear(core, ACQ_PLAYER_PARTY, ACQ_PARTY_SIZE * ACQ_MON_SIZE);
    write8(core, ACQ_PLAYER_PARTY_COUNT, 0U);
    acq_expect(acq_call(core, symbols.begin, ACQ_EVENT_EGG, 0, 0, 0), 0U,
               "egg commit");
    acq_expect(read8(core, ACQ_PLAYER_PARTY_COUNT), 1U,
               "egg party delivery count");
    acq_expect(acq_call(core, ACQ_GET_MON_DATA, ACQ_PLAYER_PARTY,
                        ACQ_MON_DATA_SPECIES, 0, 0),
               symbols.egg_species, "egg delivered species");
    acq_expect(acq_call(core, symbols.is_registered,
                        symbols.egg_species, 0, 0, 0),
               0U, "egg registration before hatch");
    write16(core, ACQ_VAR_8004, 0U);
    acq_expect(acq_call(core, symbols.hatch_register, 0, 0, 0, 0), 0U,
               "hatch registration");
    acq_expect(acq_call(core, symbols.is_registered,
                        symbols.egg_species, 0, 0, 0),
               1U, "egg registration after hatch");
    if (!acq_regions_equal(core, ACQ_SAVE, ACQ_FLASH_SAVE, ACQ_SAVE_SIZE))
        acq_die("hatch registration was not serialized to sector 31");
    acq_clear(core, ACQ_PLAYER_PARTY, ACQ_PARTY_SIZE * ACQ_MON_SIZE);
    write8(core, ACQ_PLAYER_PARTY_COUNT, 0U);
    acq_clear(core, ACQ_SAVE, ACQ_SAVE_SIZE);
    acq_expect(acq_call(core, symbols.save_load, 0, 0, 0, 0), 1U,
               "standard save reload after hatch");
    acq_expect(read8(core, ACQ_PLAYER_PARTY_COUNT), 1U,
               "durable egg party count");
    acq_expect(acq_call(core, ACQ_GET_MON_DATA, ACQ_PLAYER_PARTY,
                        ACQ_MON_DATA_SPECIES, 0, 0),
               symbols.egg_species, "durable egg party species");
    acq_expect(acq_call(core, symbols.recover, 0, 0, 0, 0), 0U,
               "durable acquisition ledger reload");
    acq_expect(acq_call(core, symbols.is_registered,
                        symbols.egg_species, 0, 0, 0),
               1U, "durable hatch registration");
    acq_expect(acq_call(core, symbols.begin, ACQ_EVENT_EGG, 0, 0, 0), 4U,
               "egg duplicate");

    restore_snapshot(core, &unlocked);
    acq_fill_party(core);
    uint64_t full_party_before = acq_hash_bytes(
        core, ACQ_PLAYER_PARTY, ACQ_PARTY_SIZE * ACQ_MON_SIZE,
        UINT64_C(14695981039346656037));
    acq_expect(acq_call(core, symbols.begin, ACQ_EVENT_GIFT, 0, 0, 0), 0U,
               "party-full gift routed to PC");
    if (full_party_before != acq_hash_bytes(
            core, ACQ_PLAYER_PARTY, ACQ_PARTY_SIZE * ACQ_MON_SIZE,
            UINT64_C(14695981039346656037)))
        acq_die("party-full gift mutated the full party");

    restore_snapshot(core, &unlocked);
    acq_fill_party(core);
    acq_fill_boxes(core, &symbols);
    uint64_t storage_before = acq_storage_hash(core, &symbols);
    acq_expect(acq_call(core, symbols.begin, ACQ_EVENT_GIFT, 0, 0, 0), 6U,
               "all-storage-full rejection");
    if (storage_before != acq_storage_hash(core, &symbols))
        acq_die("all-storage-full rejection mutated storage");

    restore_snapshot(core, &unlocked);
    acq_expect(acq_call(core, ACQ_ADD_BAG_ITEM, ACQ_FOSSIL_ITEM, 1U, 0, 0), 1U,
               "fossil input grant");
    acq_expect(acq_call(core, symbols.begin, ACQ_EVENT_FOSSIL, 0, 0, 0), 0U,
               "fossil commit");
    acq_expect(acq_call(core, symbols.begin, ACQ_EVENT_FOSSIL, 0, 0, 0), 4U,
               "fossil duplicate");

    restore_snapshot(core, &unlocked);
    acq_expect(acq_call(core, symbols.begin, ACQ_EVENT_EVOLUTION, 0, 0, 0), 0U,
               "evolution support");
    restore_snapshot(core, &unlocked);
    acq_expect(acq_call(core, symbols.begin, ACQ_EVENT_TRADE, 0, 0, 0), 0U,
               "trade emulator");
    acq_expect(acq_call(core, symbols.begin, ACQ_EVENT_TRADE, 0, 0, 0), 0U,
               "repeat trade emulator");
    restore_snapshot(core, &unlocked);
    acq_expect(acq_call(core, symbols.begin, ACQ_EVENT_SERVICE, 0, 0, 0), 0U,
               "service");
    acq_expect(acq_call(core, symbols.begin, ACQ_EVENT_SERVICE, 0, 0, 0), 0U,
               "repeat service");

    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"fixture\":\"acquisition_runtime_v1\","
           "\"rom_sha256\":\"%s\",\"read_only_host\":true,"
           "\"warnings_errors\":0,\"physical_host_chain\":true,"
           "\"egg_hatch_hook\":true,"
           "\"save\":{\"legacy_zero_inner\":true,"
           "\"nested_crc_rejection\":true,\"migration_persisted\":true,"
           "\"save_sector_round_trip\":true,"
           "\"standard_party_round_trip\":true},"
           "\"modes\":{\"capture\":true,\"gift\":true,\"egg\":true,"
           "\"egg_hatch_registration\":true,"
           "\"fossil\":true,\"evolution_support\":true,"
           "\"trade_emulator\":true,\"service\":true},"
           "\"transactions\":{\"locked\":true,\"reset_retry\":true,"
           "\"success\":true,\"duplicate_guard\":true,"
           "\"repeatable_service\":true,"
           "\"party_full_routes_to_pc\":true,"
           "\"all_storage_full_rejected\":true},"
           "\"rom_tables\":{\"evolution_routes\":true,"
           "\"wild_corrections\":true},\"artifacts_written\":[]}\n",
           rom_sha256);

    free(ready.bytes);
    free(unlocked.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
