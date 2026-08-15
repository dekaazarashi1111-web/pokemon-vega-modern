#ifndef VEGA_ACQUISITION_COLLECTION_DEFS_H
#define VEGA_ACQUISITION_COLLECTION_DEFS_H
#include <stdint.h>
#define VEGA_ACQ_CANONICAL_SPECIES_COUNT 1621u
#define VEGA_ACQ_COLLECTION_LEDGER_BIT_COUNT 1216u
#define VEGA_ACQ_COLLECTION_LEDGER_BYTES 152u
#define VEGA_ACQ_COMPLETION_TARGET_COUNT 1206u
typedef struct VegaAcqCollectionDef { uint16_t canonical_id; uint16_t ledger_bit_index; uint8_t completion_weight; uint8_t route_required; uint8_t target_class; uint8_t reserved; } VegaAcqCollectionDef;
extern const VegaAcqCollectionDef gVegaAcqCollectionDefs[VEGA_ACQ_CANONICAL_SPECIES_COUNT];
#endif
