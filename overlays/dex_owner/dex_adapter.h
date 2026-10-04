#ifndef VEGA_DEX_ADAPTER_H
#define VEGA_DEX_ADAPTER_H
#include "dex_owner.h"
#define VEGA_DEX_SPECIES_SLOTS 1670u
#define VEGA_DEX_OFFICIAL_COUNT 1025u
#define VEGA_DEX_BIT_SNAPSHOT_SIZE 4u
VegaDexStatus VegaDexSpeciesFlags(uint8_t *live,size_t size,uint16_t sid,uint8_t mode,uint8_t *value);
VegaDexStatus VegaDexOfficialFlags(uint8_t *live,size_t size,uint16_t national,uint8_t mode,uint8_t *value);
VegaDexStatus VegaDexOfficialCount(const uint8_t *live,size_t size,uint8_t mode,uint16_t *count);
VegaDexStatus VegaDexOfficialRepresentative(uint16_t national,uint16_t *sid);
/* Factory transactionの対象ownerを固定。別ownerへsnapshotを流用しない。 */
VegaDexStatus VegaDexSnapshotSpecies(const uint8_t *live,size_t size,uint16_t sid,uint8_t *snapshot,size_t snapshot_size);
VegaDexStatus VegaDexRestoreSpecies(uint8_t *live,size_t size,uint16_t sid,const uint8_t *snapshot,size_t snapshot_size);
/* Codexのseenだけを巻き戻す。新caughtがある場合は曖昧に消さず拒否。 */
VegaDexStatus VegaDexSnapshotSeen(const uint8_t *live,size_t size,uint8_t *snapshot,size_t snapshot_size);
VegaDexStatus VegaDexRestoreSeen(uint8_t *live,size_t size,const uint8_t *snapshot,size_t snapshot_size);
#endif
