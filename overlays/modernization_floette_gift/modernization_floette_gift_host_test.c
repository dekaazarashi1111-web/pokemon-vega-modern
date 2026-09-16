#include "modernization_floette_gift.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "../save_migration/save_migration.h"
#include "../../vendor/vega_acquisition/generated/acquisition_save_layout.h"

enum {
    HOST_PARTY_SIZE = 6,
    HOST_MON_SIZE = 100,
    HOST_BOX_COUNT = 14,
    HOST_BOX_CAPACITY = 30,
    HOST_BOX_MON_SIZE = 80,
    HOST_MON_DATA_SPECIES = 11,
    HOST_MON_DATA_LEVEL = 56,
    HOST_PC_BOX_VAR = 0x4037
};

volatile uint16_t gFloetteGiftHostSpecialResult;
uint8_t gFloetteGiftHostPlayerParty[HOST_PARTY_SIZE * HOST_MON_SIZE];
volatile uint8_t gFloetteGiftHostPlayerPartyCount;
volatile uint16_t gFloetteGiftHostSpecialMonBoxId;
volatile uint16_t gFloetteGiftHostSpecialMonBoxPos;
VegaModernSaveData gFloetteGiftHostModernSave;
VegaModernSaveData gFloetteGiftHostRollbackSave;
uint8_t gFloetteGiftHostTransactionScratch[256];

static uint8_t sBoxes[HOST_BOX_COUNT][HOST_BOX_CAPACITY][HOST_BOX_MON_SIZE];
static uint8_t sHasKeyStone;
static uint8_t sClaimFlag;
static uint8_t sPendingAvailable;
static uint8_t sCreateInvalid;
static uint16_t sPcBox;
static unsigned sStandardCalls;
static unsigned sSectorCalls;
static uint32_t sStandardFailureMask;
static uint32_t sSectorFailureMask;
static unsigned sFinalizeCalls;

static void write_u16(uint8_t *bytes, uint16_t value)
{
    bytes[0] = (uint8_t)value;
    bytes[1] = (uint8_t)(value >> 8);
}

static uint16_t read_u16(const uint8_t *bytes)
{
    return (uint16_t)((uint16_t)bytes[0] | ((uint16_t)bytes[1] << 8));
}

static VegaAcqSaveBlock *acq(void)
{
    return (VegaAcqSaveBlock *)(void *)
        gFloetteGiftHostModernSave.acquisition_save_block;
}

static uint8_t collection_bit(void)
{
    const uint16_t bit = MODERNIZATION_FLOETTE_GIFT_COLLECTION_BIT;
    return (uint8_t)((acq()->collection_bits[bit >> 3] >> (bit & 7u)) & 1u);
}

static void set_collection_bit(uint8_t value)
{
    const uint16_t bit = MODERNIZATION_FLOETTE_GIFT_COLLECTION_BIT;
    const uint8_t mask = (uint8_t)(1u << (bit & 7u));
    if (value)
        acq()->collection_bits[bit >> 3] |= mask;
    else
        acq()->collection_bits[bit >> 3] &= (uint8_t)~mask;
}

static void reset_fixture(uint8_t party_count)
{
    memset(gFloetteGiftHostPlayerParty, 0,
           sizeof(gFloetteGiftHostPlayerParty));
    memset(sBoxes, 0, sizeof(sBoxes));
    memset(&gFloetteGiftHostModernSave, 0,
           sizeof(gFloetteGiftHostModernSave));
    memset(&gFloetteGiftHostRollbackSave, 0,
           sizeof(gFloetteGiftHostRollbackSave));
    memset(gFloetteGiftHostTransactionScratch, 0,
           sizeof(gFloetteGiftHostTransactionScratch));
    gFloetteGiftHostPlayerPartyCount = party_count;
    for (uint8_t slot = 0; slot < party_count && slot < HOST_PARTY_SIZE;
         ++slot) {
        write_u16(gFloetteGiftHostPlayerParty + slot * HOST_MON_SIZE,
                  (uint16_t)(slot + 1u));
    }
    gFloetteGiftHostSpecialResult = 0xFFFFu;
    gFloetteGiftHostSpecialMonBoxId = 0xFFFFu;
    gFloetteGiftHostSpecialMonBoxPos = 0xFFFFu;
    gFloetteGiftHostModernSave.magic = VEGA_SAVE_MAGIC;
    gFloetteGiftHostModernSave.version = VEGA_SAVE_VERSION;
    gFloetteGiftHostModernSave.struct_size = VEGA_SAVE_LEDGER_SIZE;
    acq()->magic = VEGA_ACQ_SAVE_MAGIC;
    acq()->version = VEGA_ACQ_SAVE_VERSION;
    acq()->size = VEGA_ACQ_SAVE_BLOCK_BYTES;
    sHasKeyStone = 1u;
    sClaimFlag = 0u;
    sPendingAvailable = 1u;
    sCreateInvalid = 0u;
    sPcBox = 7u;
    sStandardCalls = 0u;
    sSectorCalls = 0u;
    sStandardFailureMask = 0u;
    sSectorFailureMask = 0u;
    sFinalizeCalls = 0u;
}

uint8_t FloetteGiftHost_FlagSet(uint16_t flag)
{
    if (flag == MODERNIZATION_FLOETTE_GIFT_CLAIM_FLAG)
        sClaimFlag = 1u;
    return 1u;
}

uint8_t FloetteGiftHost_FlagClear(uint16_t flag)
{
    if (flag == MODERNIZATION_FLOETTE_GIFT_CLAIM_FLAG)
        sClaimFlag = 0u;
    return 1u;
}

uint8_t FloetteGiftHost_FlagGet(uint16_t flag)
{
    return flag == MODERNIZATION_FLOETTE_GIFT_CLAIM_FLAG
        ? sClaimFlag : 0u;
}

uint8_t FloetteGiftHost_CheckBagHasItem(uint16_t item, uint16_t quantity)
{
    return (uint8_t)(item == MODERNIZATION_FLOETTE_GIFT_KEY_STONE_ITEM
                     && quantity == 1u && sHasKeyStone);
}

VegaAcqPendingTransaction *FloetteGiftHost_GetPending(void)
{
    return sPendingAvailable ? &acq()->pending : NULL;
}

void FloetteGiftHost_FinalizeInMemory(void)
{
    ++sFinalizeCalls;
}

void FloetteGiftHost_CreateMon(void *mon, uint16_t species, uint8_t level,
                               uint8_t fixed_iv,
                               uint8_t has_fixed_personality,
                               uint32_t personality, uint8_t ot_id_type,
                               uint32_t fixed_ot_id)
{
    uint8_t *bytes = mon;
    (void)fixed_iv;
    (void)has_fixed_personality;
    (void)personality;
    (void)ot_id_type;
    (void)fixed_ot_id;
    memset(bytes, 0, HOST_MON_SIZE);
    write_u16(bytes, sCreateInvalid ? 1u : species);
    bytes[2] = level;
}

uint8_t FloetteGiftHost_GiveMon(void *mon)
{
    const uint8_t *bytes = mon;
    if (gFloetteGiftHostPlayerPartyCount < HOST_PARTY_SIZE) {
        memcpy(gFloetteGiftHostPlayerParty
                   + gFloetteGiftHostPlayerPartyCount * HOST_MON_SIZE,
               bytes, HOST_MON_SIZE);
        ++gFloetteGiftHostPlayerPartyCount;
        return 0u;
    }
    for (uint8_t box = 0u; box < HOST_BOX_COUNT; ++box) {
        for (uint8_t position = 0u; position < HOST_BOX_CAPACITY;
             ++position) {
            if (read_u16(sBoxes[box][position]) == 0u) {
                memcpy(sBoxes[box][position], bytes, HOST_BOX_MON_SIZE);
                gFloetteGiftHostSpecialMonBoxId = box;
                gFloetteGiftHostSpecialMonBoxPos = position;
                return 1u;
            }
        }
    }
    return 2u;
}

uint32_t FloetteGiftHost_GetMonData(const void *mon, int field,
                                    uint8_t *destination)
{
    const uint8_t *bytes = mon;
    (void)destination;
    if (field == HOST_MON_DATA_SPECIES)
        return read_u16(bytes);
    if (field == HOST_MON_DATA_LEVEL)
        return bytes[2];
    return 0u;
}

uint32_t FloetteGiftHost_GetBoxMonDataAt(uint8_t box, uint8_t position,
                                         int field)
{
    if (box >= HOST_BOX_COUNT || position >= HOST_BOX_CAPACITY
        || field != HOST_MON_DATA_SPECIES)
        return 0u;
    return read_u16(sBoxes[box][position]);
}

void FloetteGiftHost_ZeroBoxMonAt(uint8_t box, uint8_t position)
{
    if (box < HOST_BOX_COUNT && position < HOST_BOX_CAPACITY)
        memset(sBoxes[box][position], 0, HOST_BOX_MON_SIZE);
}

uint16_t FloetteGiftHost_VarGet(uint16_t variable)
{
    return variable == HOST_PC_BOX_VAR ? sPcBox : 0u;
}

uint8_t FloetteGiftHost_VarSet(uint16_t variable, uint16_t value)
{
    if (variable == HOST_PC_BOX_VAR)
        sPcBox = value;
    return 1u;
}

uint8_t FloetteGiftHost_CalculatePartyCount(void)
{
    uint8_t count = 0u;
    while (count < HOST_PARTY_SIZE
           && read_u16(gFloetteGiftHostPlayerParty
                       + count * HOST_MON_SIZE) != 0u)
        ++count;
    return count;
}

uint8_t FloetteGiftHost_TryWriteSector(uint16_t sector, const void *source)
{
    (void)source;
    if (sector != 31u)
        return 0u;
    ++sSectorCalls;
    return (uint8_t)((sSectorFailureMask & (1u << (sSectorCalls - 1u))) == 0u);
}

uint8_t FloetteGiftHost_TrySavingData(uint8_t save_type)
{
    if (save_type != 0u)
        return 0u;
    ++sStandardCalls;
    return (uint8_t)((sStandardFailureMask
                      & (1u << (sStandardCalls - 1u))) == 0u);
}

static void fill_boxes(void)
{
    for (uint8_t box = 0u; box < HOST_BOX_COUNT; ++box)
        for (uint8_t position = 0u; position < HOST_BOX_CAPACITY;
             ++position)
            write_u16(sBoxes[box][position], 25u);
}

static int check(int condition, const char *label)
{
    if (!condition) {
        fprintf(stderr, "host check failed: %s\n", label);
        return 0;
    }
    return 1;
}

#define CHECK(condition, label) \
    do { if (!check((condition), (label))) return 1; } while (0)

int main(void)
{
    uint16_t result;
    unsigned scenarios = 0u;

    reset_fixture(0u);
    CHECK(FloetteGift_Probe() == MODERNIZATION_FLOETTE_GIFT_ABI_VERSION,
          "probe ABI");
    ++scenarios;

    reset_fixture(0u);
    sHasKeyStone = 0u;
    CHECK(FloetteGift_Claim() == FLOETTE_GIFT_RESULT_LOCKED,
          "Mega Ring lock");
    CHECK(!sClaimFlag && !collection_bit() && sStandardCalls == 0u,
          "locked state unchanged");
    ++scenarios;

    reset_fixture(0u);
    sClaimFlag = 1u;
    CHECK(FloetteGift_Claim() == FLOETTE_GIFT_RESULT_ALREADY_CLAIMED,
          "one-time claim");
    CHECK(gFloetteGiftHostPlayerPartyCount == 0u,
          "duplicate delivery denied");
    ++scenarios;

    reset_fixture(0u);
    acq()->pending.magic = VEGA_ACQ_PENDING_MAGIC;
    CHECK(FloetteGift_Claim() == FLOETTE_GIFT_RESULT_BUSY,
          "shared pending busy");
    CHECK(!sClaimFlag && gFloetteGiftHostPlayerPartyCount == 0u,
          "busy state unchanged");
    ++scenarios;

    reset_fixture(HOST_PARTY_SIZE);
    fill_boxes();
    CHECK(FloetteGift_Claim() == FLOETTE_GIFT_RESULT_NO_CAPACITY,
          "party and PC full");
    CHECK(!sClaimFlag && !collection_bit() && sStandardCalls == 0u,
          "capacity failure remains unclaimed");
    ++scenarios;

    reset_fixture(5u);
    result = FloetteGift_Claim();
    CHECK(result == FLOETTE_GIFT_RESULT_SUCCESS, "party success");
    CHECK(gFloetteGiftHostPlayerPartyCount == 6u,
          "party count incremented");
    CHECK(read_u16(gFloetteGiftHostPlayerParty + 5u * HOST_MON_SIZE)
              == MODERNIZATION_FLOETTE_GIFT_SPECIES,
          "party species 1029");
    CHECK(gFloetteGiftHostPlayerParty[5u * HOST_MON_SIZE + 2u]
              == MODERNIZATION_FLOETTE_GIFT_LEVEL,
          "party level 50");
    CHECK(sClaimFlag && collection_bit(), "claim and National 670 ledger");
    CHECK(FloetteGift_IsFormObtained() == 1u
              && FloetteGift_IsNationalDexSeen() == 1u
              && FloetteGift_IsNationalDexCaught() == 1u,
          "form/seen/caught readback");
    CHECK(sStandardCalls == 1u && sSectorCalls == 1u,
          "success persistence order count");
    CHECK(FloetteGift_Claim() == FLOETTE_GIFT_RESULT_ALREADY_CLAIMED
              && gFloetteGiftHostPlayerPartyCount == 6u,
          "success re-entry idempotent");
    ++scenarios;

    reset_fixture(HOST_PARTY_SIZE);
    fill_boxes();
    memset(sBoxes[2][9], 0, HOST_BOX_MON_SIZE);
    result = FloetteGift_Claim();
    CHECK(result == FLOETTE_GIFT_RESULT_SUCCESS, "PC success");
    CHECK(read_u16(sBoxes[2][9]) == MODERNIZATION_FLOETTE_GIFT_SPECIES,
          "PC species 1029");
    CHECK(sPcBox == 7u, "PC current-box variable restored");
    CHECK(sClaimFlag && collection_bit(), "PC claim state");
    ++scenarios;

    reset_fixture(5u);
    sStandardFailureMask = 1u;
    result = FloetteGift_Claim();
    CHECK(result == FLOETTE_GIFT_RESULT_PERSIST_FAILED,
          "party save failure");
    CHECK(gFloetteGiftHostPlayerPartyCount == 5u
              && read_u16(gFloetteGiftHostPlayerParty
                          + 5u * HOST_MON_SIZE) == 0u,
          "party delivery rollback");
    CHECK(!sClaimFlag && !collection_bit(), "party flag/ledger rollback");
    CHECK(sStandardCalls == 2u && sSectorCalls == 1u,
          "party compensating persistence");
    ++scenarios;

    reset_fixture(HOST_PARTY_SIZE);
    fill_boxes();
    memset(sBoxes[4][12], 0, HOST_BOX_MON_SIZE);
    sSectorFailureMask = 1u;
    result = FloetteGift_Claim();
    CHECK(result == FLOETTE_GIFT_RESULT_PERSIST_FAILED,
          "PC sector failure");
    CHECK(read_u16(sBoxes[4][12]) == 0u, "PC delivery rollback");
    CHECK(!sClaimFlag && !collection_bit(), "PC flag/ledger rollback");
    CHECK(sStandardCalls == 2u && sSectorCalls == 2u,
          "PC compensating persistence");
    ++scenarios;

    reset_fixture(5u);
    set_collection_bit(1u);
    sStandardFailureMask = 1u;
    result = FloetteGift_Claim();
    CHECK(result == FLOETTE_GIFT_RESULT_PERSIST_FAILED,
          "existing National 670 save failure");
    CHECK(collection_bit(), "pre-existing National 670 bit preserved");
    CHECK(!sClaimFlag && gFloetteGiftHostPlayerPartyCount == 5u,
          "form remains unclaimed after rollback");
    ++scenarios;

    reset_fixture(5u);
    sStandardFailureMask = 3u;
    result = FloetteGift_Claim();
    CHECK(result == FLOETTE_GIFT_RESULT_ROLLBACK_FAILED,
          "compensation persistence failure surfaced");
    CHECK(!sClaimFlag && !collection_bit()
              && gFloetteGiftHostPlayerPartyCount == 5u,
          "rollback RAM exact despite persistence failure");
    ++scenarios;

    reset_fixture(0u);
    sPendingAvailable = 0u;
    CHECK(FloetteGift_Claim() == FLOETTE_GIFT_RESULT_ENGINE_REJECTED,
          "acquisition save init failure");
    ++scenarios;

    reset_fixture(0u);
    sCreateInvalid = 1u;
    CHECK(FloetteGift_Claim() == FLOETTE_GIFT_RESULT_ENGINE_REJECTED,
          "CreateMon postcondition failure");
    CHECK(!sClaimFlag && !collection_bit()
              && gFloetteGiftHostPlayerPartyCount == 0u,
          "creation failure unchanged");
    ++scenarios;

    CHECK(sFinalizeCalls == 0u,
          "last negative case did not finalize");
    printf("{\"status\":\"PASS\",\"scenario_count\":%u,"
           "\"party_delivery\":true,\"pc_delivery\":true,"
           "\"party_pc_full_unclaimed\":true,"
           "\"standard_save_rollback\":true,"
           "\"sector_save_rollback\":true,"
           "\"rollback_failure_surfaced\":true,"
           "\"national_670_collection_bit\":850,"
           "\"form_claim_flag\":\"0x14CD\"}\n",
           scenarios);
    return 0;
}
