#ifndef VEGA_ACQUISITION_EVENT_DEFS_H
#define VEGA_ACQUISITION_EVENT_DEFS_H
#include <stdint.h>
#define VEGA_ACQ_EVENT_COUNT 201u
#define VEGA_ACQ_NO_INDEX 0xFFFFu
typedef struct VegaAcqEventDef {
    const char *event_key; const char *species_key; const char *unlock_key;
    const char *claim_key; const char *source_item_key;
    uint16_t species_id; uint16_t claim_bit_index; uint16_t bounded_counter_index;
    uint8_t mode; uint8_t level; uint8_t max_claims; uint8_t policy_flags;
} VegaAcqEventDef;
extern const VegaAcqEventDef gVegaAcqEventDefs[VEGA_ACQ_EVENT_COUNT];
#endif
