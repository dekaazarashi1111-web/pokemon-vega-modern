#ifndef VEGA_ACQUISITION_HOST_DEFS_H
#define VEGA_ACQUISITION_HOST_DEFS_H
#include <stdint.h>
#define VEGA_ACQ_HOST_COUNT 24u
#define VEGA_ACQ_HOST_EVENT_INDEX_COUNT 201u
typedef struct VegaAcqHostDef { const char *host_key; uint16_t first_event_index; uint16_t event_count; } VegaAcqHostDef;
extern const VegaAcqHostDef gVegaAcqHostDefs[VEGA_ACQ_HOST_COUNT];
extern const uint16_t gVegaAcqHostEventIndices[VEGA_ACQ_HOST_EVENT_INDEX_COUNT];
#endif
