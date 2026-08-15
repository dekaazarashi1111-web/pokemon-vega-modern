#ifndef VEGA_ACQUISITION_SAVE_LAYOUT_H
#define VEGA_ACQUISITION_SAVE_LAYOUT_H
#include <stdint.h>
#include "../overlays/acquisition_runtime/acquisition_runtime.h"
#define VEGA_ACQ_SAVE_MAGIC 0x51434156u
#define VEGA_ACQ_SAVE_VERSION 1u
#define VEGA_ACQ_COLLECTION_BYTES 152u
#define VEGA_ACQ_EVENT_CLAIM_BITS 176u
#define VEGA_ACQ_EVENT_CLAIM_BYTES 22u
#define VEGA_ACQ_BOUNDED_COUNTER_COUNT 1u
#define VEGA_ACQ_ALIGNMENT_PADDING_BYTES 1u
#define VEGA_ACQ_EVOLUTION_COUNTER_BYTES 32u
#define VEGA_ACQ_SAVE_BLOCK_BYTES 240u
typedef struct VegaAcqSaveBlock {
    uint32_t magic; uint16_t version; uint16_t size; uint32_t crc32;
    uint8_t collection_bits[VEGA_ACQ_COLLECTION_BYTES];
    uint8_t event_claim_bits[VEGA_ACQ_EVENT_CLAIM_BYTES];
    uint8_t bounded_claim_counters[VEGA_ACQ_BOUNDED_COUNTER_COUNT];
    uint8_t alignment_padding[VEGA_ACQ_ALIGNMENT_PADDING_BYTES];
    uint8_t evolution_counters[VEGA_ACQ_EVOLUTION_COUNTER_BYTES];
    VegaAcqPendingTransaction pending;
} VegaAcqSaveBlock;
_Static_assert(sizeof(VegaAcqSaveBlock) == VEGA_ACQ_SAVE_BLOCK_BYTES,
               "acquisition save ABI changed");
#endif
