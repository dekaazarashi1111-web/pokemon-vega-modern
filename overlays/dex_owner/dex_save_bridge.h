#ifndef VEGA_DEX_SAVE_BRIDGE_H
#define VEGA_DEX_SAVE_BRIDGE_H
#include "dex_owner.h"
/* Stage61後段接続用。stock bank検証・bank選択はcallerが先に完了する。 */
#define VEGA_DEX_SECTOR_SIZE 4096u
#define VEGA_DEX_STOCK_PC_TAIL_SIZE 2000u
#define VEGA_DEX_SAVE1_SIZE 0x3D40u
#define VEGA_DEX_SAVE2_SIZE 0x0F24u
typedef enum VegaDexRecordKind {
    VEGA_DEX_RECORD_VALID = 0,
    VEGA_DEX_RECORD_LEGACY_ZERO = 1,
    VEGA_DEX_RECORD_LEGACY_ERASED = 2,
    VEGA_DEX_RECORD_REJECT = 3
} VegaDexRecordKind;
VegaDexRecordKind VegaDexClassifyRecord(const uint8_t *record, size_t size);
/* 単独MDXだけでbankを採用しない。親CRC検証済logical13にのみ使用。 */
VegaDexStatus VegaDexCheckSector(const uint8_t *sector, size_t sector_size,
    uint32_t counter, uint8_t parent_verified);
VegaDexStatus VegaDexInjectSector(uint8_t *sector, size_t sector_size,
    const uint8_t *live, size_t live_size, uint32_t counter, uint8_t parent_verified);
VegaDexStatus VegaDexTailMatches(const uint8_t *sector, size_t sector_size,
    const uint8_t *live, size_t live_size, uint32_t counter, uint8_t parent_verified,
    uint8_t *matches);
/* stock復元後の同一bank SaveBlockからだけ旧4鏡を採る。 */
VegaDexStatus VegaDexLoadSelected(uint8_t *live, size_t live_size,
    const uint8_t *sector, size_t sector_size,
    const uint8_t *save1, size_t save1_size,
    const uint8_t *save2, size_t save2_size,
    uint32_t counter, uint8_t parent_verified);
/* failed-loadはnewgameとは異なる無効RAMへ。自動flash reloadは禁止。 */
VegaDexStatus VegaDexInvalidateSession(uint8_t *live, size_t live_size);
#endif
