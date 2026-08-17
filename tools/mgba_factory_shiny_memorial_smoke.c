/* Focused Stage31 exact-ROM smoke for the Factory 100-streak shiny memorial. */
#define main mgba_regression_smoke_embedded_main
#include "mgba_regression_smoke.c"
#undef main

#include <stddef.h>
#include <string.h>

#include "../overlays/save_migration/save_migration.h"
#include "../vendor/vega_acquisition/generated/acquisition_save_layout.h"

#define SMOKE_MAX_CALL_STEPS UINT64_C(60000000)
#define SMOKE_SAVE_FILE_SIZE UINT32_C(0x20000)
#define SMOKE_ABI_MARKER UINT32_C(0xB931)
#define SMOKE_LEDGER UINT32_C(0x0203D000)
#define SMOKE_LEDGER_SIZE UINT32_C(0x800)
#define SMOKE_FLASH_LEDGER UINT32_C(0x0E01F064)
#define SMOKE_SECTOR_IMAGE UINT32_C(0x0203CF9C)
#define SMOKE_SECTOR_BUFFER UINT32_C(0x020399B0)
#define SMOKE_SECTOR_DATA_SIZE UINT32_C(0x0FF0)
#define SMOKE_SECTOR_SIZE UINT32_C(0x1000)
#define SMOKE_SECTOR_ID UINT32_C(31)
#define SMOKE_PLAYER_PARTY UINT32_C(0x020241E4)
#define SMOKE_PLAYER_PARTY_COUNT UINT32_C(0x02023F89)
#define SMOKE_SPECIAL_BOX UINT32_C(0x0203700A)
#define SMOKE_SPECIAL_POS UINT32_C(0x0203700C)
#define SMOKE_RNG_STATE UINT32_C(0x03005040)
#define SMOKE_SAVE_BLOCK1_PTR UINT32_C(0x03005048)
#define SMOKE_SAVE_BLOCK2_PTR UINT32_C(0x0300504C)
#define SMOKE_SCRATCH UINT32_C(0x0203E300)
#define SMOKE_MON_SIZE UINT32_C(100)
#define SMOKE_BOX_MON_SIZE UINT32_C(80)
#define SMOKE_COMPRESSED_MON_SIZE UINT32_C(58)
#define SMOKE_COMPRESSED_SCRATCH (SMOKE_SCRATCH + UINT32_C(0x80))
#define SMOKE_PARTY_CAPACITY UINT32_C(6)
#define SMOKE_BOX_COUNT UINT32_C(14)
#define SMOKE_BOX_CAPACITY UINT32_C(30)
#define SMOKE_BOX_TOTAL (SMOKE_BOX_COUNT * SMOKE_BOX_CAPACITY)
#define SMOKE_CREATE_MON UINT32_C(0x0803D1C1)
#define SMOKE_GET_MON_DATA UINT32_C(0x0803F355)
#define SMOKE_GET_SET_DEX UINT32_C(0x08088A51)
#define SMOKE_SPECIES_TO_NATIONAL UINT32_C(0x08042989)
#define SMOKE_TRY_WRITE_SECTOR UINT32_C(0x080DA9C1)
#define SMOKE_TRY_SAVE UINT32_C(0x080DB34D)
#define SMOKE_TRY_WRITE_SECTOR_EVEN UINT32_C(0x080DA9C0)
#define SMOKE_TRY_SAVE_EVEN UINT32_C(0x080DB34C)
#define SMOKE_CLAIM_MASK UINT32_C(0x00000200)
#define SMOKE_PRIOR_CLAIMS UINT32_C(0x000001FF)
#define SMOKE_RESULT_CLAIMED UINT16_C(0)
#define SMOKE_RESULT_NOT_ELIGIBLE UINT16_C(1)
#define SMOKE_RESULT_NO_CAPACITY UINT16_C(3)
#define SMOKE_RESULT_PERSIST_FAILED UINT16_C(4)
#define SMOKE_RESULT_RECOVERED_COMMIT UINT16_C(5)
#define SMOKE_RESULT_RECOVERED_RETRY UINT16_C(6)
#define SMOKE_ACQ_RESULT_SUCCESS UINT16_C(0)
#define SMOKE_ACQ_RESULT_CORRUPT_PENDING UINT16_C(16)
#define SMOKE_STAGE30_RESULT UINT16_C(9)
#define SMOKE_PENDING_MODE UINT8_C(0xF1)
#define SMOKE_PENDING_RESERVED0 UINT8_C(0x53)
#define SMOKE_PENDING_RESERVED1 UINT8_C(0x31)
#define SMOKE_PHASE_PREPARED UINT8_C(1)
#define SMOKE_PHASE_STAGED UINT8_C(2)
#define SMOKE_TOKEN_PARTY UINT32_C(0x10000000)
#define SMOKE_TOKEN_BOX UINT32_C(0x20000000)
#define SMOKE_PERSONALITY_PREFIX UINT16_C(0xD300)
#define SMOKE_MON_DATA_PERSONALITY UINT32_C(0)
#define SMOKE_MON_DATA_OT_ID UINT32_C(1)
#define SMOKE_MON_DATA_SPECIES UINT32_C(11)
#define SMOKE_DEX_GET_SEEN UINT32_C(0)
#define SMOKE_DEX_GET_CAUGHT UINT32_C(1)
#define SMOKE_FACTORY_MARKER_ACTIVE UINT8_C(2)

#define SMOKE_FACTORY_ADDR \
    (SMOKE_LEDGER + (uint32_t)offsetof(VegaModernSaveData, factory))
#define SMOKE_ACQ_ADDR \
    (SMOKE_LEDGER + (uint32_t)offsetof(VegaModernSaveData, acquisition_save_block))
#define SMOKE_COLLECTION_ADDR \
    (SMOKE_ACQ_ADDR + (uint32_t)offsetof(VegaAcqSaveBlock, collection_bits))
#define SMOKE_PENDING_ADDR \
    (SMOKE_ACQ_ADDR + (uint32_t)offsetof(VegaAcqSaveBlock, pending))

_Static_assert(sizeof(VegaModernSaveData) == VEGA_SAVE_LEDGER_SIZE,
               "modern save ABI changed");
_Static_assert(sizeof(VegaAcqPendingTransaction) == 20U,
               "pending ABI changed");
_Static_assert(offsetof(VegaModernSaveData, factory) == 0x392U,
               "Factory state offset changed");

enum {
    FACTORY_BP_OFFSET = offsetof(VegaFactoryState, battle_points),
    FACTORY_CURRENT_STREAK_OFFSET = offsetof(VegaFactoryState, current_streak),
    FACTORY_BEST_STREAK_OFFSET = offsetof(VegaFactoryState, best_streak),
    FACTORY_CLAIMS_OFFSET = offsetof(VegaFactoryState, reward_claim_bits),
    FACTORY_TRANSACTION_OFFSET = offsetof(VegaFactoryState, transaction_id),
    FACTORY_MARKER_OFFSET = offsetof(VegaFactoryState, marker),
    FACTORY_SNAPSHOT_VALID_OFFSET = offsetof(VegaFactoryState, snapshot_valid),
    FACTORY_PARTY_COUNT_OFFSET = offsetof(VegaFactoryState, party_count),
    FACTORY_REWARD_PENDING_OFFSET = offsetof(VegaFactoryState, reward_pending),
    FACTORY_PARTY_SNAPSHOT_OFFSET = offsetof(VegaFactoryState, party_snapshot),
};

static void smoke_die(const char *message)
{
    fprintf(stderr, "mgba-factory-shiny-memorial-smoke: %s\n", message);
    exit(1);
}

static void smoke_phase(const char *phase)
{
    fprintf(stderr, "mgba-factory-shiny-memorial-smoke: phase=%s\n", phase);
    fflush(stderr);
}

static void smoke_initialize_save(const char *path)
{
    FILE *stream = fopen(path, "wb");
    uint8_t block[4096];
    uint32_t remaining = SMOKE_SAVE_FILE_SIZE;
    if (stream == NULL)
        smoke_die("temporary save creation failed");
    memset(block, 0xFF, sizeof(block));
    while (remaining != 0U) {
        size_t amount = remaining < sizeof(block) ? remaining : sizeof(block);
        if (fwrite(block, 1U, amount, stream) != amount) {
            (void)fclose(stream);
            smoke_die("temporary save initialization failed");
        }
        remaining -= (uint32_t)amount;
    }
    if (fclose(stream) != 0)
        smoke_die("temporary save close failed");
}

static void smoke_write8(struct mCore *core, uint32_t address, uint8_t value)
{
    core->rawWrite8(core, address, -1, value);
}

static void smoke_write16(struct mCore *core, uint32_t address, uint16_t value)
{
    core->rawWrite16(core, address, -1, value);
}

static void smoke_write32(struct mCore *core, uint32_t address, uint32_t value)
{
    smoke_write8(core, address, (uint8_t)value);
    smoke_write8(core, address + 1U, (uint8_t)(value >> 8U));
    smoke_write8(core, address + 2U, (uint8_t)(value >> 16U));
    smoke_write8(core, address + 3U, (uint8_t)(value >> 24U));
}

static uint32_t smoke_read32_unaligned(struct mCore *core, uint32_t address)
{
    return (uint32_t)read8(core, address)
        | ((uint32_t)read8(core, address + 1U) << 8U)
        | ((uint32_t)read8(core, address + 2U) << 16U)
        | ((uint32_t)read8(core, address + 3U) << 24U);
}

static void smoke_read_bytes(struct mCore *core, uint32_t address,
                             uint8_t *destination, size_t size)
{
    size_t index;
    for (index = 0U; index < size; ++index)
        destination[index] = read8(core, address + (uint32_t)index);
}

static void smoke_write_bytes(struct mCore *core, uint32_t address,
                              const uint8_t *source, size_t size)
{
    size_t index;
    for (index = 0U; index < size; ++index)
        smoke_write8(core, address + (uint32_t)index, source[index]);
}

static void smoke_clear_region(struct mCore *core, uint32_t address,
                               size_t size)
{
    size_t index;
    for (index = 0U; index < size; ++index)
        smoke_write8(core, address + (uint32_t)index, 0U);
}

static bool smoke_memory_equals(struct mCore *core, uint32_t address,
                                const uint8_t *expected, size_t size)
{
    size_t index;
    for (index = 0U; index < size; ++index) {
        if (read8(core, address + (uint32_t)index) != expected[index])
            return false;
    }
    return true;
}

static uint32_t smoke_call_thumb(struct mCore *core, uint32_t function,
                                 uint32_t r0, uint32_t r1,
                                 uint32_t r2, uint32_t r3)
{
    struct CpuContext original = capture_cpu(core);
    uint64_t steps = 0U;
    write_register(core, "cpsr", original.registers[16] | 0xA0);
    write_register(core, "lr", (int32_t)UINT32_C(0x08000001));
    write_register(core, "r0", (int32_t)r0);
    write_register(core, "r1", (int32_t)r1);
    write_register(core, "r2", (int32_t)r2);
    write_register(core, "r3", (int32_t)r3);
    write_register(core, "pc", (int32_t)function);
    while ((((uint32_t)read_register(core, "pc")) & ~1U)
           != UINT32_C(0x08000002)) {
        if (++steps > SMOKE_MAX_CALL_STEPS) {
            fprintf(stderr,
                    "mgba-factory-shiny-memorial-smoke: instruction limit "
                    "function=%#010" PRIx32 " pc=%#010" PRIx32 "\n",
                    function, (uint32_t)read_register(core, "pc"));
            smoke_die("runtime instruction limit exceeded");
        }
        core->step(core);
    }
    r0 = (uint32_t)read_register(core, "r0");
    restore_cpu(core, &original);
    return r0;
}

static uint32_t smoke_call_thumb8(struct mCore *core, uint32_t function,
                                  uint32_t r0, uint32_t r1,
                                  uint32_t r2, uint32_t r3,
                                  uint32_t a4, uint32_t a5,
                                  uint32_t a6, uint32_t a7)
{
    struct CpuContext original = capture_cpu(core);
    uint32_t original_sp = (uint32_t)original.registers[13];
    uint32_t call_sp = (original_sp - 16U) & ~7U;
    uint8_t saved_stack[16];
    uint64_t steps = 0U;
    smoke_read_bytes(core, call_sp, saved_stack, sizeof(saved_stack));
    smoke_write32(core, call_sp, a4);
    smoke_write32(core, call_sp + 4U, a5);
    smoke_write32(core, call_sp + 8U, a6);
    smoke_write32(core, call_sp + 12U, a7);
    write_register(core, "sp", (int32_t)call_sp);
    write_register(core, "cpsr", original.registers[16] | 0xA0);
    write_register(core, "lr", (int32_t)UINT32_C(0x08000001));
    write_register(core, "r0", (int32_t)r0);
    write_register(core, "r1", (int32_t)r1);
    write_register(core, "r2", (int32_t)r2);
    write_register(core, "r3", (int32_t)r3);
    write_register(core, "pc", (int32_t)function);
    while ((((uint32_t)read_register(core, "pc")) & ~1U)
           != UINT32_C(0x08000002)) {
        if (++steps > SMOKE_MAX_CALL_STEPS)
            smoke_die("eight-argument runtime instruction limit exceeded");
        core->step(core);
    }
    r0 = (uint32_t)read_register(core, "r0");
    smoke_write_bytes(core, call_sp, saved_stack, sizeof(saved_stack));
    restore_cpu(core, &original);
    return r0;
}

static uint16_t smoke_invoke(struct mCore *core, uint32_t entrypoint)
{
    uint32_t direct;
    uint16_t script;
    smoke_write16(core, SPECIAL_VAR_RESULT, UINT16_C(0xFFFF));
    direct = smoke_call_thumb(core, entrypoint, 0U, 0U, 0U, 0U);
    script = read16(core, SPECIAL_VAR_RESULT);
    if ((direct & UINT32_C(0xFFFF)) != script) {
        fprintf(stderr,
                "mgba-factory-shiny-memorial-smoke: direct/script mismatch "
                "entry=%#010" PRIx32 " direct=%" PRIu32 " script=%u\n",
                entrypoint, direct, script);
        smoke_die("entrypoint result contract failed");
    }
    return script;
}

static void smoke_finalize(struct mCore *core, uint32_t finalize)
{
    (void)smoke_call_thumb(core, finalize, SMOKE_LEDGER, 0U, 0U, 0U);
}

static bool smoke_persist_sector(struct mCore *core)
{
    uint32_t index;
    smoke_clear_region(core, SMOKE_SECTOR_BUFFER, SMOKE_SECTOR_SIZE);
    for (index = 0U; index < SMOKE_SECTOR_DATA_SIZE; ++index) {
        smoke_write8(core, SMOKE_SECTOR_BUFFER + index,
                     read8(core, SMOKE_SECTOR_IMAGE + index));
    }
    return smoke_call_thumb(core, SMOKE_TRY_WRITE_SECTOR,
                            SMOKE_SECTOR_ID, SMOKE_SECTOR_BUFFER, 0U, 0U) == 1U;
}

static bool smoke_persist_standard(struct mCore *core)
{
    return smoke_call_thumb(core, SMOKE_TRY_SAVE, 0U, 0U, 0U, 0U) == 1U;
}

static void smoke_require_flash_ledger(struct mCore *core, const char *label)
{
    uint32_t index;
    for (index = 0U; index < SMOKE_LEDGER_SIZE; ++index) {
        uint8_t ewram = read8(core, SMOKE_LEDGER + index);
        uint8_t flash = read8(core, SMOKE_FLASH_LEDGER + index);
        if (ewram != flash) {
            fprintf(stderr,
                    "mgba-factory-shiny-memorial-smoke: ledger mismatch %s "
                    "offset=%#06" PRIx32 " ewram=%#04x flash=%#04x\n",
                    label, index, ewram, flash);
            smoke_die("EWRAM ledger differs from sector 31");
        }
    }
}

static uint32_t smoke_get_pending(struct mCore *core, uint32_t get_pending)
{
    uint32_t pending = smoke_call_thumb(core, get_pending, 0U, 0U, 0U, 0U);
    if (pending != SMOKE_PENDING_ADDR)
        smoke_die("acquisition pending pointer ABI differs");
    return pending;
}

static bool smoke_pending_clear(struct mCore *core, uint32_t pending)
{
    uint32_t index;
    for (index = 0U; index < sizeof(VegaAcqPendingTransaction); ++index) {
        if (read8(core, pending + index) != 0U)
            return false;
    }
    return true;
}

static uint16_t smoke_pending_checksum(uint16_t event_index, uint16_t species,
                                       uint8_t phase, uint32_t token)
{
    uint16_t value = UINT16_C(0x31A5);
    value ^= event_index;
    value ^= species;
    value ^= (uint16_t)((uint16_t)SMOKE_PENDING_MODE << 8U);
    value ^= phase;
    value ^= (uint16_t)((uint16_t)SMOKE_PENDING_RESERVED0 << 8U);
    value ^= SMOKE_PENDING_RESERVED1;
    value ^= (uint16_t)token;
    value ^= (uint16_t)(token >> 16U);
    return value;
}

static void smoke_write_custom_pending(struct mCore *core, uint32_t pending,
                                       uint16_t pool_index, uint16_t species,
                                       uint8_t phase, uint32_t token)
{
    uint16_t encoded = (uint16_t)(UINT16_C(0x8000) | pool_index);
    smoke_clear_region(core, pending, sizeof(VegaAcqPendingTransaction));
    smoke_write32(core, pending + offsetof(VegaAcqPendingTransaction, magic),
                  VEGA_ACQ_PENDING_MAGIC);
    smoke_write32(core,
                  pending + offsetof(VegaAcqPendingTransaction, transaction_token),
                  token);
    smoke_write16(core, pending + offsetof(VegaAcqPendingTransaction, event_index),
                  encoded);
    smoke_write16(core, pending + offsetof(VegaAcqPendingTransaction, species_id),
                  species);
    smoke_write8(core, pending + offsetof(VegaAcqPendingTransaction, mode),
                 SMOKE_PENDING_MODE);
    smoke_write8(core, pending + offsetof(VegaAcqPendingTransaction, phase), phase);
    smoke_write8(core, pending + offsetof(VegaAcqPendingTransaction, reserved0),
                 SMOKE_PENDING_RESERVED0);
    smoke_write8(core, pending + offsetof(VegaAcqPendingTransaction, reserved1),
                 SMOKE_PENDING_RESERVED1);
    smoke_write16(core, pending + offsetof(VegaAcqPendingTransaction, checksum),
                  smoke_pending_checksum(encoded, species, phase, token));
}

static uint16_t smoke_pool_value(struct mCore *core, uint32_t table,
                                 uint16_t index)
{
    return read16(core, table + (uint32_t)index * 2U);
}

static uint32_t smoke_trainer_id(struct mCore *core)
{
    uint32_t save2 = read32(core, SMOKE_SAVE_BLOCK2_PTR);
    if (save2 < UINT32_C(0x02000000) || save2 >= UINT32_C(0x02040000))
        smoke_die("save block 2 pointer differs");
    return smoke_read32_unaligned(core, save2 + UINT32_C(0x0A));
}

static uint32_t smoke_mon_data(struct mCore *core, uint32_t mon, uint32_t field)
{
    return smoke_call_thumb(core, SMOKE_GET_MON_DATA, mon, field, 0U, 0U);
}

static uint32_t smoke_box_data(struct mCore *core, uint32_t get_box_data,
                               uint8_t box, uint8_t position, uint32_t field)
{
    return smoke_call_thumb(core, get_box_data, box, position, field, 0U);
}

static void smoke_create_mon(struct mCore *core, uint32_t destination,
                             uint16_t species, uint8_t level,
                             uint32_t personality)
{
    smoke_clear_region(core, destination, SMOKE_MON_SIZE);
    (void)smoke_call_thumb8(core, SMOKE_CREATE_MON, destination, species,
                            level, 32U, 1U, personality, 0U, 0U);
    if (smoke_mon_data(core, destination, SMOKE_MON_DATA_SPECIES) != species
        || smoke_mon_data(core, destination, SMOKE_MON_DATA_PERSONALITY)
            != personality)
        smoke_die("CreateMon image contract failed");
}

static void smoke_install_party(struct mCore *core,
                                const uint8_t template_mon[SMOKE_MON_SIZE],
                                uint8_t count)
{
    uint32_t slot;
    if (count > SMOKE_PARTY_CAPACITY)
        smoke_die("party setup count invalid");
    smoke_clear_region(core, SMOKE_PLAYER_PARTY,
                       SMOKE_PARTY_CAPACITY * SMOKE_MON_SIZE);
    for (slot = 0U; slot < count; ++slot) {
        smoke_write_bytes(core, SMOKE_PLAYER_PARTY + slot * SMOKE_MON_SIZE,
                          template_mon, SMOKE_MON_SIZE);
    }
    smoke_write8(core, SMOKE_PLAYER_PARTY_COUNT, count);
}

static uint32_t smoke_storage_base(struct mCore *core,
                                   uint32_t get_compressed_mon)
{
    uint32_t first = smoke_call_thumb(
        core, get_compressed_mon, 0U, 0U, 0U, 0U);
    uint32_t last = smoke_call_thumb(
        core, get_compressed_mon, 13U, 29U, 0U, 0U);
    uint32_t expected_last = first
        + (SMOKE_BOX_TOTAL - 1U) * SMOKE_COMPRESSED_MON_SIZE;
    if (first < UINT32_C(0x02000000)
        || expected_last + SMOKE_COMPRESSED_MON_SIZE > UINT32_C(0x02040000)
        || last != expected_last)
        smoke_die("compressed box storage pointer ABI differs");
    return first;
}

static void smoke_clear_boxes(struct mCore *core, uint32_t storage_base)
{
    smoke_clear_region(core, storage_base,
                       SMOKE_BOX_TOTAL * SMOKE_COMPRESSED_MON_SIZE);
}

static void smoke_fill_boxes(
    struct mCore *core, uint32_t storage_base,
    const uint8_t compressed_mon[SMOKE_COMPRESSED_MON_SIZE])
{
    uint32_t slot;
    for (slot = 0U; slot < SMOKE_BOX_TOTAL; ++slot) {
        smoke_write_bytes(
            core, storage_base + slot * SMOKE_COMPRESSED_MON_SIZE,
            compressed_mon, SMOKE_COMPRESSED_MON_SIZE);
    }
}

static bool smoke_marker_values(struct mCore *core, uint16_t species,
                                uint32_t personality, uint32_t ot_id,
                                uint32_t species_table, uint32_t pool_count,
                                uint16_t *pool_index)
{
    uint16_t high = (uint16_t)(personality >> 16U);
    uint16_t low = (uint16_t)personality;
    uint16_t index = (uint16_t)(high & UINT16_C(0x00FF));
    uint32_t owner = smoke_trainer_id(core);
    if ((high & UINT16_C(0xFF00)) != SMOKE_PERSONALITY_PREFIX
        || index >= pool_count
        || species != smoke_pool_value(core, species_table, index)
        || ot_id != owner
        || ((uint16_t)owner ^ (uint16_t)(owner >> 16U) ^ high ^ low) != 0U)
        return false;
    *pool_index = index;
    return true;
}

static bool smoke_party_marker_at(struct mCore *core, uint8_t slot,
                                  uint32_t species_table, uint32_t pool_count,
                                  uint16_t *pool_index)
{
    uint32_t mon = SMOKE_PLAYER_PARTY + (uint32_t)slot * SMOKE_MON_SIZE;
    return smoke_marker_values(
        core,
        (uint16_t)smoke_mon_data(core, mon, SMOKE_MON_DATA_SPECIES),
        smoke_mon_data(core, mon, SMOKE_MON_DATA_PERSONALITY),
        smoke_mon_data(core, mon, SMOKE_MON_DATA_OT_ID),
        species_table, pool_count, pool_index);
}

static bool smoke_box_marker_at(struct mCore *core, uint32_t get_box_data,
                                uint8_t box, uint8_t position,
                                uint32_t species_table, uint32_t pool_count,
                                uint16_t *pool_index)
{
    return smoke_marker_values(
        core,
        (uint16_t)smoke_box_data(core, get_box_data, box, position,
                                 SMOKE_MON_DATA_SPECIES),
        smoke_box_data(core, get_box_data, box, position,
                       SMOKE_MON_DATA_PERSONALITY),
        smoke_box_data(core, get_box_data, box, position,
                       SMOKE_MON_DATA_OT_ID),
        species_table, pool_count, pool_index);
}

static unsigned smoke_party_marker_count(struct mCore *core,
                                         uint32_t species_table,
                                         uint32_t pool_count)
{
    uint8_t count = read8(core, SMOKE_PLAYER_PARTY_COUNT);
    unsigned markers = 0U;
    uint8_t slot;
    for (slot = 0U; slot < count && slot < SMOKE_PARTY_CAPACITY; ++slot) {
        uint16_t ignored = 0U;
        if (smoke_party_marker_at(core, slot, species_table, pool_count, &ignored))
            ++markers;
    }
    return markers;
}

static void smoke_clear_dex_bit(struct mCore *core, uint16_t national)
{
    uint32_t save1 = read32(core, SMOKE_SAVE_BLOCK1_PTR);
    uint32_t save2 = read32(core, SMOKE_SAVE_BLOCK2_PTR);
    uint32_t byte_index;
    uint8_t mask;
    const uint32_t addresses[4] = {
        save2 + UINT32_C(0x28), save2 + UINT32_C(0x5C),
        save1 + UINT32_C(0x5F8), save1 + UINT32_C(0x3A18),
    };
    size_t index;
    if (national == 0U || national > 386U)
        smoke_die("pool national number outside legacy-safe range");
    byte_index = (uint32_t)(national - 1U) >> 3U;
    mask = (uint8_t)(1U << ((national - 1U) & 7U));
    for (index = 0U; index < 4U; ++index) {
        uint32_t address = addresses[index] + byte_index;
        smoke_write8(core, address, (uint8_t)(read8(core, address) & ~mask));
    }
}

static void smoke_clear_pool_registration(struct mCore *core,
                                          uint32_t national_table,
                                          uint32_t ledger_table,
                                          uint32_t pool_count)
{
    uint32_t index;
    for (index = 0U; index < pool_count; ++index) {
        uint16_t bit = smoke_pool_value(core, ledger_table, (uint16_t)index);
        uint16_t national = smoke_pool_value(core, national_table, (uint16_t)index);
        if (bit >= VEGA_ACQ_COLLECTION_BYTES * 8U)
            smoke_die("pool ledger bit outside acquisition collection");
        smoke_write8(core, SMOKE_COLLECTION_ADDR + (bit >> 3U),
                     (uint8_t)(read8(core, SMOKE_COLLECTION_ADDR + (bit >> 3U))
                               & (uint8_t)~(1U << (bit & 7U))));
        smoke_clear_dex_bit(core, national);
    }
}

static bool smoke_collection_bit(struct mCore *core, uint16_t bit)
{
    return (read8(core, SMOKE_COLLECTION_ADDR + ((uint32_t)bit >> 3U))
            & (uint8_t)(1U << (bit & 7U))) != 0U;
}

static void smoke_prepare_eligible(struct mCore *core, uint32_t pending,
                                   uint32_t finalize, uint16_t streak,
                                   uint8_t master, uint32_t claims,
                                   uint32_t transaction)
{
    uint32_t factory = SMOKE_FACTORY_ADDR;
    smoke_write8(core,
                 SMOKE_LEDGER + offsetof(VegaModernSaveData, league_i_cleared),
                 master);
    smoke_write8(core,
                 SMOKE_LEDGER + offsetof(VegaModernSaveData, league_ii_cleared),
                 master);
    smoke_write16(core, factory + FACTORY_CURRENT_STREAK_OFFSET, streak);
    smoke_write16(core, factory + FACTORY_BEST_STREAK_OFFSET, streak);
    smoke_write32(core, factory + FACTORY_CLAIMS_OFFSET, claims);
    smoke_write32(core, factory + FACTORY_TRANSACTION_OFFSET, transaction);
    smoke_clear_region(core, pending, sizeof(VegaAcqPendingTransaction));
    smoke_finalize(core, finalize);
}

static void smoke_prepare_completion(
    struct mCore *core, uint32_t finalize,
    const uint8_t original[SMOKE_PARTY_CAPACITY * SMOKE_MON_SIZE],
    uint8_t original_count, uint16_t bp, uint16_t streak,
    uint32_t claims, uint32_t transaction)
{
    uint32_t factory = SMOKE_FACTORY_ADDR;
    uint8_t rental[SMOKE_PARTY_CAPACITY * SMOKE_MON_SIZE];
    uint32_t index;
    for (index = 0U; index < sizeof(rental); ++index)
        rental[index] = (uint8_t)(UINT32_C(0xA5) ^ index);
    smoke_write8(core,
                 SMOKE_LEDGER + offsetof(VegaModernSaveData, league_i_cleared), 1U);
    smoke_write8(core,
                 SMOKE_LEDGER + offsetof(VegaModernSaveData, league_ii_cleared), 1U);
    smoke_write16(core, factory + FACTORY_BP_OFFSET, bp);
    smoke_write16(core, factory + FACTORY_CURRENT_STREAK_OFFSET, streak);
    smoke_write16(core, factory + FACTORY_BEST_STREAK_OFFSET, streak);
    smoke_write32(core, factory + FACTORY_CLAIMS_OFFSET, claims);
    smoke_write32(core, factory + FACTORY_TRANSACTION_OFFSET, transaction);
    smoke_write_bytes(core, factory + FACTORY_PARTY_SNAPSHOT_OFFSET,
                      original, SMOKE_PARTY_CAPACITY * SMOKE_MON_SIZE);
    smoke_write8(core, factory + FACTORY_MARKER_OFFSET,
                 SMOKE_FACTORY_MARKER_ACTIVE);
    smoke_write8(core, factory + FACTORY_SNAPSHOT_VALID_OFFSET, 1U);
    smoke_write8(core, factory + FACTORY_PARTY_COUNT_OFFSET, original_count);
    smoke_write8(core, factory + FACTORY_REWARD_PENDING_OFFSET, 3U);
    smoke_write_bytes(core, SMOKE_PLAYER_PARTY, rental, sizeof(rental));
    smoke_write8(core, SMOKE_PLAYER_PARTY_COUNT, 3U);
    smoke_finalize(core, finalize);
}

static void smoke_require_factory_cleanup(struct mCore *core)
{
    uint32_t factory = SMOKE_FACTORY_ADDR;
    if (read8(core, factory + FACTORY_MARKER_OFFSET) != 0U
        || read8(core, factory + FACTORY_SNAPSHOT_VALID_OFFSET) != 0U
        || read8(core, factory + FACTORY_PARTY_COUNT_OFFSET) != 0U
        || read8(core, factory + FACTORY_REWARD_PENDING_OFFSET) != 0U)
        smoke_die("Stage30 party restore marker was not cleared");
}

static void smoke_patch_failure(struct mCore *core, uint32_t address,
                                uint16_t *first, uint16_t *second)
{
    *first = read16(core, address);
    *second = read16(core, address + 2U);
    smoke_write16(core, address, UINT16_C(0x2000));
    smoke_write16(core, address + 2U, UINT16_C(0x4770));
}

static void smoke_restore_patch(struct mCore *core, uint32_t address,
                                uint16_t first, uint16_t second)
{
    smoke_write16(core, address, first);
    smoke_write16(core, address + 2U, second);
}

int main(int argc, char **argv)
{
    uint32_t probe;
    uint32_t complete;
    uint32_t claim;
    uint32_t recover;
    uint32_t finalize;
    uint32_t get_pending;
    uint32_t give_mon;
    uint32_t get_box_data;
    uint32_t get_compressed_mon;
    uint32_t create_compressed_mon;
    uint32_t zero_box;
    uint32_t is_registered;
    uint32_t species_table;
    uint32_t national_table;
    uint32_t ledger_table;
    uint32_t complete_script;
    uint32_t stage30_complete;
    uint32_t recovery_entry;
    uint32_t pool_count;
    const uint32_t *entry;
    size_t entry_count;
    struct mLogger logger = {.log = silent_log, .filter = NULL};
    struct mCore *core;
    color_t *video;
    uint32_t transitions;
    uint32_t pending;
    uint32_t boxes;
    uint8_t template_mon[SMOKE_MON_SIZE];
    uint8_t compressed_mon[SMOKE_COMPRESSED_MON_SIZE];
    uint8_t baseline_party[SMOKE_PARTY_CAPACITY * SMOKE_MON_SIZE];
    uint8_t party_after_claim[SMOKE_PARTY_CAPACITY * SMOKE_MON_SIZE];
    uint8_t final_party[SMOKE_PARTY_CAPACITY * SMOKE_MON_SIZE];
    uint16_t selected_index = 0U;
    uint16_t selected_species;
    uint16_t selected_national;
    uint16_t selected_ledger_bit;
    uint16_t completion_pool_index;
    uint16_t completion_species;
    uint32_t completion_transaction;
    uint16_t patch0;
    uint16_t patch1;
    if (argc != 22) {
        fprintf(stderr,
                "usage: %s ROM SAVE PROBE COMPLETE CLAIM RECOVER FINALIZE "
                "GET_PENDING GIVE_MON GET_BOX_DATA GET_COMPRESSED_MON "
                "CREATE_COMPRESSED_MON ZERO_BOX IS_REGISTERED SPECIES_TABLE "
                "NATIONAL_TABLE LEDGER_TABLE "
                "COMPLETE_SCRIPT STAGE30_COMPLETE RECOVERY_ENTRY POOL_COUNT\n",
                argv[0]);
        return 2;
    }
    probe = parse_u32(argv[3], "probe");
    complete = parse_u32(argv[4], "complete");
    claim = parse_u32(argv[5], "claim");
    recover = parse_u32(argv[6], "recover");
    finalize = parse_u32(argv[7], "finalize");
    get_pending = parse_u32(argv[8], "get pending");
    give_mon = parse_u32(argv[9], "give mon");
    get_box_data = parse_u32(argv[10], "get box data");
    get_compressed_mon = parse_u32(argv[11], "get compressed mon");
    create_compressed_mon = parse_u32(argv[12], "create compressed mon");
    zero_box = parse_u32(argv[13], "zero box");
    is_registered = parse_u32(argv[14], "is registered");
    species_table = parse_u32(argv[15], "species table");
    national_table = parse_u32(argv[16], "national table");
    ledger_table = parse_u32(argv[17], "ledger table");
    complete_script = parse_u32(argv[18], "completion script");
    stage30_complete = parse_u32(argv[19], "Stage30 complete");
    recovery_entry = parse_u32(argv[20], "recovery entry");
    pool_count = parse_u32(argv[21], "pool count");
    {
        uint32_t mutable_entrypoints[12] = {
            probe, complete, claim, recover, finalize, get_pending,
            give_mon, get_box_data, get_compressed_mon,
            create_compressed_mon, zero_box, is_registered,
        };
        entry = mutable_entrypoints;
        entry_count = sizeof(mutable_entrypoints) / sizeof(mutable_entrypoints[0]);
        for (size_t index = 0U; index < entry_count; ++index) {
            if ((entry[index] & 1U) == 0U
                || !rom_pointer(entry[index] & ~1U))
                smoke_die("runtime entrypoint contract failed");
        }
    }
    if (species_table < ROM_BASE || species_table >= ROM_END
        || national_table < ROM_BASE || national_table >= ROM_END
        || ledger_table < ROM_BASE || ledger_table >= ROM_END
        || (species_table & 1U) != 0U || (national_table & 1U) != 0U
        || (ledger_table & 1U) != 0U || !rom_pointer(complete_script)
        || (stage30_complete & 1U) == 0U || (recovery_entry & 1U) != 0U
        || pool_count != 137U || complete == stage30_complete)
        smoke_die("Stage31 ROM/data pointer contract failed");

    mLogSetDefaultLogger(&logger);
    core = mCoreFind(argv[1]);
    if (core == NULL || !core->init(core))
        smoke_die("core initialization failed");
    if (!mCoreLoadFile(core, argv[1]))
        smoke_die("ROM load failed");
    smoke_initialize_save(argv[2]);
    if (!mCoreLoadSaveFile(core, argv[2], false))
        smoke_die("temporary save attachment failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    video = calloc(GBA_WIDTH * GBA_HEIGHT, sizeof(*video));
    if (video == NULL)
        smoke_die("video allocation failed");
    core->setVideoBuffer(core, video, GBA_WIDTH);
    core->reset(core);

    smoke_phase("natural-new-game");
    transitions = run_natural_new_game(core, video);

    smoke_phase("physical-binding-and-init");
    if (read8(core, complete_script) != UINT8_C(0x23)
        || smoke_read32_unaligned(core, complete_script + 1U) != complete
        || read16(core, recovery_entry) != UINT16_C(0x4B00)
        || read16(core, recovery_entry + 2U) != UINT16_C(0x4718)
        || smoke_read32_unaligned(core, recovery_entry + 4U) != recover)
        smoke_die("Stage31 completion/recovery patch is not physically bound");
    smoke_write16(core, SPECIAL_VAR_RESULT, 0U);
    if (smoke_call_thumb(core, probe, 0U, 0U, 0U, 0U) != SMOKE_ABI_MARKER
        || read16(core, SPECIAL_VAR_RESULT) != SMOKE_ABI_MARKER)
        smoke_die("Stage31 ABI probe failed");
    pending = smoke_get_pending(core, get_pending);
    if (!smoke_pending_clear(core, pending))
        smoke_die("new save pending slot is not clear");
    boxes = smoke_storage_base(core, get_compressed_mon);

    smoke_phase("normal-recovery-trampoline");
    if (smoke_call_thumb(core, recover, 0U, 0U, 0U, 0U)
            != SMOKE_ACQ_RESULT_SUCCESS)
        smoke_die("normal empty acquisition recovery differs");
    smoke_write32(core, pending + offsetof(VegaAcqPendingTransaction, magic),
                  VEGA_ACQ_PENDING_MAGIC);
    smoke_write16(core, pending + offsetof(VegaAcqPendingTransaction, event_index),
                  UINT16_C(0x7FFF));
    smoke_write8(core, pending + offsetof(VegaAcqPendingTransaction, mode), 0U);
    smoke_write8(core, pending + offsetof(VegaAcqPendingTransaction, phase), 1U);
    smoke_finalize(core, finalize);
    if (smoke_call_thumb(core, recover, 0U, 0U, 0U, 0U)
            != SMOKE_ACQ_RESULT_CORRUPT_PENDING
        || !smoke_pending_clear(core, pending))
        smoke_die("normal acquisition recovery trampoline differs");

    smoke_phase("template-and-gates");
    smoke_create_mon(core, SMOKE_SCRATCH, 25U, 5U, UINT32_C(0x12345678));
    smoke_read_bytes(core, SMOKE_SCRATCH, template_mon, sizeof(template_mon));
    (void)smoke_call_thumb(core, create_compressed_mon,
                           SMOKE_SCRATCH, SMOKE_COMPRESSED_SCRATCH, 0U, 0U);
    smoke_read_bytes(core, SMOKE_COMPRESSED_SCRATCH, compressed_mon,
                     sizeof(compressed_mon));
    smoke_install_party(core, template_mon, 1U);
    smoke_clear_boxes(core, boxes);
    smoke_prepare_eligible(core, pending, finalize, 100U, 0U,
                           SMOKE_PRIOR_CLAIMS, 100U);
    if (smoke_invoke(core, claim) != SMOKE_RESULT_NOT_ELIGIBLE
        || (read32(core, SMOKE_FACTORY_ADDR + FACTORY_CLAIMS_OFFSET)
            & SMOKE_CLAIM_MASK) != 0U)
        smoke_die("Factory Master gate differs");
    smoke_prepare_eligible(core, pending, finalize, 99U, 1U,
                           SMOKE_PRIOR_CLAIMS, 100U);
    if (smoke_invoke(core, claim) != SMOKE_RESULT_NOT_ELIGIBLE
        || (read32(core, SMOKE_FACTORY_ADDR + FACTORY_CLAIMS_OFFSET)
            & SMOKE_CLAIM_MASK) != 0U)
        smoke_die("100-streak threshold gate differs");

    smoke_phase("completion-party-atomic-commit");
    smoke_install_party(core, template_mon, 1U);
    smoke_clear_boxes(core, boxes);
    smoke_read_bytes(core, SMOKE_PLAYER_PARTY, baseline_party,
                     sizeof(baseline_party));
    smoke_clear_pool_registration(core, national_table, ledger_table, pool_count);
    smoke_write32(core, SMOKE_RNG_STATE, 0U);
    smoke_prepare_completion(core, finalize, baseline_party, 1U, 400U, 100U,
                             SMOKE_PRIOR_CLAIMS, 500U);
    if (smoke_invoke(core, complete) != SMOKE_STAGE30_RESULT)
        smoke_die("Stage31 completion wrapper changed Stage30 result");
    if (read8(core, SMOKE_PLAYER_PARTY_COUNT) != 2U
        || !smoke_memory_equals(core, SMOKE_PLAYER_PARTY,
                                baseline_party, SMOKE_MON_SIZE)
        || !smoke_memory_equals(core, SMOKE_PLAYER_PARTY + 2U * SMOKE_MON_SIZE,
                                baseline_party + 2U * SMOKE_MON_SIZE,
                                4U * SMOKE_MON_SIZE)
        || !smoke_party_marker_at(core, 1U, species_table, pool_count,
                                  &selected_index)
        || smoke_party_marker_count(core, species_table, pool_count) != 1U)
        smoke_die("party delivery or exact Stage30 restore differs");
    selected_species = smoke_pool_value(core, species_table, selected_index);
    selected_national = smoke_pool_value(core, national_table, selected_index);
    selected_ledger_bit = smoke_pool_value(core, ledger_table, selected_index);
    completion_pool_index = selected_index;
    completion_species = selected_species;
    completion_transaction = read32(core,
        SMOKE_FACTORY_ADDR + FACTORY_TRANSACTION_OFFSET);
    {
        uint32_t claims = read32(core,
            SMOKE_FACTORY_ADDR + FACTORY_CLAIMS_OFFSET);
        uint32_t registered = smoke_call_thumb(
            core, is_registered, selected_species, 0U, 0U, 0U);
        uint32_t actual_national = smoke_call_thumb(
            core, SMOKE_SPECIES_TO_NATIONAL, selected_species, 0U, 0U, 0U);
        uint32_t seen = smoke_call_thumb(
            core, SMOKE_GET_SET_DEX, selected_national,
            SMOKE_DEX_GET_SEEN, 0U, 0U);
        uint32_t caught = smoke_call_thumb(
            core, SMOKE_GET_SET_DEX, selected_national,
            SMOKE_DEX_GET_CAUGHT, 0U, 0U);
        bool collection = smoke_collection_bit(core, selected_ledger_bit);
        bool pending_clear = smoke_pending_clear(core, pending);
        if ((claims & SMOKE_CLAIM_MASK) == 0U
            || completion_transaction <= 500U
            || !pending_clear || registered != 1U || !collection
            || seen == 0U || caught == 0U) {
            fprintf(stderr,
                    "mgba-factory-shiny-memorial-smoke: atomic actual "
                    "index=%u species=%u national=%u actual_national=%" PRIu32
                    " ledger=%u claims=%#010" PRIx32
                    " tx=%" PRIu32 " pending=%u registered=%" PRIu32
                    " collection=%u seen=%" PRIu32 " caught=%" PRIu32 "\n",
                    selected_index, selected_species, selected_national,
                    actual_national, selected_ledger_bit, claims,
                    completion_transaction,
                    pending_clear ? 1U : 0U, registered, collection ? 1U : 0U,
                    seen, caught);
            smoke_die("Pokedex/collection/claim atomic commit differs");
        }
    }
    smoke_require_factory_cleanup(core);
    smoke_require_flash_ledger(core, "party atomic commit");

    smoke_phase("once-and-stage30-coexistence");
    smoke_read_bytes(core, SMOKE_PLAYER_PARTY, party_after_claim,
                     sizeof(party_after_claim));
    smoke_write32(core, SMOKE_RNG_STATE, 0U);
    smoke_prepare_completion(
        core, finalize, party_after_claim, 2U, 410U, 100U,
        read32(core, SMOKE_FACTORY_ADDR + FACTORY_CLAIMS_OFFSET),
        completion_transaction);
    if (smoke_invoke(core, complete) != SMOKE_STAGE30_RESULT
        || read8(core, SMOKE_PLAYER_PARTY_COUNT) != 2U
        || !smoke_memory_equals(core, SMOKE_PLAYER_PARTY,
                                party_after_claim, sizeof(party_after_claim))
        || smoke_party_marker_count(core, species_table, pool_count) != 1U
        || !smoke_pending_clear(core, pending))
        smoke_die("once suppression or Stage30 coexistence differs");
    smoke_require_factory_cleanup(core);
    smoke_require_flash_ledger(core, "once coexistence");

    smoke_phase("sector31-reload-after-completion");
    smoke_clear_region(core, SMOKE_LEDGER, SMOKE_LEDGER_SIZE);
    if (smoke_get_pending(core, get_pending) != pending
        || (read32(core, SMOKE_FACTORY_ADDR + FACTORY_CLAIMS_OFFSET)
            & SMOKE_CLAIM_MASK) == 0U
        || !smoke_pending_clear(core, pending)
        || !smoke_memory_equals(core, SMOKE_PLAYER_PARTY,
                                party_after_claim, sizeof(party_after_claim)))
        smoke_die("sector31 reload after completion differs");
    smoke_require_flash_ledger(core, "completion reload");

    smoke_phase("pc-delivery");
    smoke_clear_boxes(core, boxes);
    smoke_install_party(core, template_mon, 6U);
    smoke_prepare_eligible(core, pending, finalize, 100U, 1U,
                           SMOKE_PRIOR_CLAIMS, 700U);
    smoke_write32(core, SMOKE_RNG_STATE, 0U);
    if (smoke_invoke(core, claim) != SMOKE_RESULT_CLAIMED
        || read8(core, SMOKE_PLAYER_PARTY_COUNT) != 6U
        || read16(core, SMOKE_SPECIAL_BOX) != 0U
        || read16(core, SMOKE_SPECIAL_POS) != 0U
        || !smoke_box_marker_at(core, get_box_data, 0U, 0U,
                                species_table, pool_count, &selected_index)
        || (read32(core, SMOKE_FACTORY_ADDR + FACTORY_CLAIMS_OFFSET)
            & SMOKE_CLAIM_MASK) == 0U)
        smoke_die("party-full PC delivery differs");
    smoke_require_flash_ledger(core, "PC delivery");

    smoke_phase("capacity-and-retry");
    smoke_install_party(core, template_mon, 6U);
    smoke_fill_boxes(core, boxes, compressed_mon);
    if (smoke_box_data(core, get_box_data, 0U, 0U,
                       SMOKE_MON_DATA_SPECIES) != 25U
        || smoke_box_data(core, get_box_data, 13U, 29U,
                          SMOKE_MON_DATA_SPECIES) != 25U)
        smoke_die("full box setup differs");
    smoke_prepare_eligible(core, pending, finalize, 100U, 1U,
                           SMOKE_PRIOR_CLAIMS, 800U);
    if (smoke_invoke(core, claim) != SMOKE_RESULT_NO_CAPACITY
        || (read32(core, SMOKE_FACTORY_ADDR + FACTORY_CLAIMS_OFFSET)
            & SMOKE_CLAIM_MASK) != 0U
        || !smoke_pending_clear(core, pending)
        || read8(core, SMOKE_PLAYER_PARTY_COUNT) != 6U)
        smoke_die("capacity failure consumed the claim");
    smoke_clear_region(core, boxes, SMOKE_COMPRESSED_MON_SIZE);
    smoke_write32(core, SMOKE_RNG_STATE, 0U);
    if (smoke_invoke(core, claim) != SMOKE_RESULT_CLAIMED
        || !smoke_box_marker_at(core, get_box_data, 0U, 0U,
                                species_table, pool_count, &selected_index)
        || (read32(core, SMOKE_FACTORY_ADDR + FACTORY_CLAIMS_OFFSET)
            & SMOKE_CLAIM_MASK) == 0U)
        smoke_die("capacity retry did not deliver into freed PC slot");

    smoke_phase("prepared-journal-recovery");
    smoke_clear_boxes(core, boxes);
    smoke_install_party(core, template_mon, 1U);
    smoke_prepare_eligible(core, pending, finalize, 100U, 1U,
                           SMOKE_PRIOR_CLAIMS, 900U);
    selected_index = 0U;
    selected_species = smoke_pool_value(core, species_table, selected_index);
    smoke_write_custom_pending(core, pending, selected_index, selected_species,
                               SMOKE_PHASE_PREPARED, 0U);
    smoke_finalize(core, finalize);
    if (!smoke_persist_sector(core)
        || smoke_call_thumb(core, recover, 0U, 0U, 0U, 0U)
            != SMOKE_RESULT_RECOVERED_RETRY
        || !smoke_pending_clear(core, pending)
        || (read32(core, SMOKE_FACTORY_ADDR + FACTORY_CLAIMS_OFFSET)
            & SMOKE_CLAIM_MASK) != 0U
        || smoke_party_marker_count(core, species_table, pool_count) != 0U)
        smoke_die("PREPARED journal recovery differs");

    smoke_phase("staged-journal-recovery");
    {
        uint32_t owner = smoke_trainer_id(core);
        uint16_t high = (uint16_t)(SMOKE_PERSONALITY_PREFIX | selected_index);
        uint16_t low = (uint16_t)owner ^ (uint16_t)(owner >> 16U) ^ high;
        uint32_t personality = ((uint32_t)high << 16U) | low;
        smoke_create_mon(core, SMOKE_SCRATCH, selected_species, 50U, personality);
        smoke_write_bytes(core, SMOKE_PLAYER_PARTY + SMOKE_MON_SIZE,
                          (const uint8_t[SMOKE_MON_SIZE]){0}, SMOKE_MON_SIZE);
        smoke_read_bytes(core, SMOKE_SCRATCH, template_mon, SMOKE_MON_SIZE);
        smoke_write_bytes(core, SMOKE_PLAYER_PARTY + SMOKE_MON_SIZE,
                          template_mon, SMOKE_MON_SIZE);
        smoke_write8(core, SMOKE_PLAYER_PARTY_COUNT, 2U);
        smoke_write_custom_pending(core, pending, selected_index, selected_species,
                                   SMOKE_PHASE_STAGED,
                                   SMOKE_TOKEN_PARTY | UINT32_C(1));
        smoke_finalize(core, finalize);
        if (!smoke_persist_standard(core) || !smoke_persist_sector(core)
            || smoke_call_thumb(core, recover, 0U, 0U, 0U, 0U)
                != SMOKE_RESULT_RECOVERED_COMMIT
            || !smoke_pending_clear(core, pending)
            || (read32(core, SMOKE_FACTORY_ADDR + FACTORY_CLAIMS_OFFSET)
                & SMOKE_CLAIM_MASK) == 0U
            || smoke_party_marker_count(core, species_table, pool_count) != 1U)
            smoke_die("STAGED journal recovery differs");
    }
    /* Restore the non-marker template used by the remaining reset helpers. */
    smoke_create_mon(core, SMOKE_SCRATCH, 25U, 5U, UINT32_C(0x12345678));
    smoke_read_bytes(core, SMOKE_SCRATCH, template_mon, sizeof(template_mon));
    (void)smoke_call_thumb(core, create_compressed_mon,
                           SMOKE_SCRATCH, SMOKE_COMPRESSED_SCRATCH, 0U, 0U);
    smoke_read_bytes(core, SMOKE_COMPRESSED_SCRATCH, compressed_mon,
                     sizeof(compressed_mon));

    smoke_phase("sector-write-failure-and-retry");
    smoke_clear_boxes(core, boxes);
    smoke_install_party(core, template_mon, 1U);
    smoke_prepare_eligible(core, pending, finalize, 100U, 1U,
                           SMOKE_PRIOR_CLAIMS, 1000U);
    smoke_patch_failure(core, SMOKE_TRY_WRITE_SECTOR_EVEN, &patch0, &patch1);
    if (smoke_invoke(core, claim) != SMOKE_RESULT_PERSIST_FAILED
        || (read32(core, SMOKE_FACTORY_ADDR + FACTORY_CLAIMS_OFFSET)
            & SMOKE_CLAIM_MASK) != 0U
        || !smoke_pending_clear(core, pending)
        || read8(core, SMOKE_PLAYER_PARTY_COUNT) != 1U)
        smoke_die("sector failure consumed claim or delivered a mon");
    smoke_restore_patch(core, SMOKE_TRY_WRITE_SECTOR_EVEN, patch0, patch1);
    smoke_write32(core, SMOKE_RNG_STATE, 0U);
    if (smoke_invoke(core, claim) != SMOKE_RESULT_CLAIMED
        || (read32(core, SMOKE_FACTORY_ADDR + FACTORY_CLAIMS_OFFSET)
            & SMOKE_CLAIM_MASK) == 0U
        || smoke_party_marker_count(core, species_table, pool_count) != 1U)
        smoke_die("sector failure retry did not claim");

    smoke_phase("standard-save-failure-and-recovery");
    smoke_clear_boxes(core, boxes);
    smoke_install_party(core, template_mon, 1U);
    smoke_prepare_eligible(core, pending, finalize, 100U, 1U,
                           SMOKE_PRIOR_CLAIMS, 1100U);
    smoke_write32(core, SMOKE_RNG_STATE, 0U);
    smoke_patch_failure(core, SMOKE_TRY_SAVE_EVEN, &patch0, &patch1);
    if (smoke_invoke(core, claim) != SMOKE_RESULT_PERSIST_FAILED
        || (read32(core, SMOKE_FACTORY_ADDR + FACTORY_CLAIMS_OFFSET)
            & SMOKE_CLAIM_MASK) != 0U
        || read32(core, pending + offsetof(VegaAcqPendingTransaction, magic))
            != VEGA_ACQ_PENDING_MAGIC
        || read8(core, pending + offsetof(VegaAcqPendingTransaction, phase))
            != SMOKE_PHASE_STAGED
        || smoke_party_marker_count(core, species_table, pool_count) != 1U)
        smoke_die("standard save failure transaction differs");
    smoke_restore_patch(core, SMOKE_TRY_SAVE_EVEN, patch0, patch1);
    if (smoke_call_thumb(core, recover, 0U, 0U, 0U, 0U)
            != SMOKE_RESULT_RECOVERED_COMMIT
        || (read32(core, SMOKE_FACTORY_ADDR + FACTORY_CLAIMS_OFFSET)
            & SMOKE_CLAIM_MASK) == 0U
        || !smoke_pending_clear(core, pending)
        || smoke_party_marker_count(core, species_table, pool_count) != 1U)
        smoke_die("standard save failure recovery differs");
    smoke_require_flash_ledger(core, "standard save recovery");

    smoke_phase("final-sector31-reload");
    smoke_read_bytes(core, SMOKE_PLAYER_PARTY, final_party, sizeof(final_party));
    smoke_clear_region(core, SMOKE_LEDGER, SMOKE_LEDGER_SIZE);
    if (smoke_get_pending(core, get_pending) != pending
        || (read32(core, SMOKE_FACTORY_ADDR + FACTORY_CLAIMS_OFFSET)
            & SMOKE_CLAIM_MASK) == 0U
        || !smoke_pending_clear(core, pending)
        || !smoke_memory_equals(core, SMOKE_PLAYER_PARTY,
                                final_party, sizeof(final_party)))
        smoke_die("final sector31 reload or party preservation differs");
    smoke_require_flash_ledger(core, "final reload");

    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"checks\":{\"physical_binding\":true,"
           "\"probe_and_save_init\":true,"
           "\"master_and_threshold_gates\":true,"
           "\"party_shiny_atomic_commit\":true,"
           "\"once_and_stage30_coexistence\":true,"
           "\"pc_delivery\":true,"
           "\"capacity_retry\":true,"
           "\"journal_recovery\":true,"
           "\"sector_failure_retry\":true,"
           "\"standard_save_failure_retry\":true,"
           "\"normal_recovery_trampoline\":true,"
           "\"sector31_reload_and_party_restore\":true},"
           "\"pool_count\":%" PRIu32 ","
           "\"completion_pool_index\":%u,"
           "\"completion_species\":%u,"
           "\"completion_transaction\":%" PRIu32 ","
           "\"framebuffer_transitions\":%" PRIu32 ","
           "\"artifacts_written\":[]}\n",
           pool_count, completion_pool_index, completion_species,
           completion_transaction, transitions);
    fflush(stdout);
    _Exit(EXIT_SUCCESS);
}
