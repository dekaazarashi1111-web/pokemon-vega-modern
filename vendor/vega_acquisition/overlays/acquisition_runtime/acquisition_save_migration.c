#include "acquisition_save_migration.h"

#include <stddef.h>
#include <stdint.h>

#include "../../generated/acquisition_collection_defs.h"
#include "../../generated/acquisition_event_defs.h"

static void clear_bytes(void *destination, size_t size)
{
    uint8_t *out = (uint8_t *)destination;
    size_t index;
    for (index = 0; index < size; ++index)
        out[index] = 0u;
}

static void set_bit(uint8_t *bits, uint16_t index)
{
    bits[index >> 3] |= (uint8_t)(1u << (index & 7u));
}

uint32_t VegaAcqSaveCrc32(const void *data, size_t size)
{
    const uint8_t *bytes = (const uint8_t *)data;
    uint32_t crc = 0xFFFFFFFFu;
    size_t index;
    uint8_t bit;
    for (index = 0; index < size; ++index) {
        crc ^= bytes[index];
        for (bit = 0u; bit < 8u; ++bit)
            crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}

void VegaAcqSaveFinalize(VegaAcqSaveBlock *block)
{
    if (block == NULL)
        return;
    block->magic = VEGA_ACQ_SAVE_MAGIC;
    block->version = VEGA_ACQ_SAVE_VERSION;
    block->size = (uint16_t)sizeof(*block);
    block->crc32 = 0u;
    block->crc32 = VegaAcqSaveCrc32(block, sizeof(*block));
}

uint8_t VegaAcqSaveValidate(const VegaAcqSaveBlock *block)
{
    VegaAcqSaveBlock copy;
    uint32_t expected;
    if (block == NULL || block->magic != VEGA_ACQ_SAVE_MAGIC
        || block->version != VEGA_ACQ_SAVE_VERSION
        || block->size != sizeof(*block))
        return 0u;
    copy = *block;
    expected = copy.crc32;
    copy.crc32 = 0u;
    return (uint8_t)(VegaAcqSaveCrc32(&copy, sizeof(copy)) == expected);
}

void VegaAcqSaveInitialize(VegaAcqSaveBlock *block)
{
    if (block == NULL)
        return;
    clear_bytes(block, sizeof(*block));
    VegaAcqSaveFinalize(block);
}

uint8_t VegaAcqSaveMigrate(VegaAcqSaveBlock *block,
                           VegaAcqMigrationSpeciesRegistered is_registered,
                           void *context)
{
    uint16_t index;
    if (block == NULL || is_registered == NULL)
        return 0u;
    if (VegaAcqSaveValidate(block))
        return 1u;

    clear_bytes(block, sizeof(*block));
    for (index = 0u; index < VEGA_ACQ_CANONICAL_SPECIES_COUNT; ++index) {
        const VegaAcqCollectionDef *def = &gVegaAcqCollectionDefs[index];
        if (def->ledger_bit_index != 0xFFFFu
            && is_registered(def->canonical_id, context))
            set_bit(block->collection_bits, def->ledger_bit_index);
    }
    for (index = 0u; index < VEGA_ACQ_EVENT_COUNT; ++index) {
        const VegaAcqEventDef *def = &gVegaAcqEventDefs[index];
        if (def->claim_bit_index == 0xFFFFu || def->species_id == 0u)
            continue;
        if ((def->policy_flags & VEGA_ACQ_POLICY_SEED_CLAIM_FROM_REGISTRATION) != 0u
            && is_registered(def->species_id, context))
            set_bit(block->event_claim_bits, def->claim_bit_index);
        if (def->bounded_counter_index != 0xFFFFu
            && def->bounded_counter_index < VEGA_ACQ_BOUNDED_COUNTER_COUNT
            && is_registered(def->species_id, context))
            block->bounded_claim_counters[def->bounded_counter_index] = 1u;
    }
    clear_bytes(&block->pending, sizeof(block->pending));
    VegaAcqSaveFinalize(block);
    return 1u;
}
