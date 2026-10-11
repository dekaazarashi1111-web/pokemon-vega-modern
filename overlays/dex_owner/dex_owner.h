#ifndef VEGA_DEX_OWNER_H
#define VEGA_DEX_OWNER_H
#include <stddef.h>
#include <stdint.h>

/* 公式1025種 + 既存正本のVega181種。フォーム取得台帳とは独立。 */
#define VEGA_DEX_OWNER_COUNT 1206u
#define VEGA_DEX_BITMAP_SIZE 151u
#define VEGA_DEX_LEGACY_SIZE 208u
#define VEGA_DEX_HEADER_SIZE 12u
#define VEGA_DEX_OWNER_SIZE 522u
#define VEGA_DEX_NAMESPACE_VERSION 1u
#define VEGA_DEX_OWNER_RAM 0x0203DB40u
#define VEGA_DEX_CHUNK13_OFFSET 0xDE6u
#define VEGA_DEX_SEEN_OFFSET 12u
#define VEGA_DEX_CAUGHT_OFFSET 163u
#define VEGA_DEX_LEGACY_OFFSET 314u
#define VEGA_DEX_FLAG_LEGACY_SNAPSHOT 1u

/* 外部番号を推測しない。callerは署名固定された専用mappingでownerへ変換する。 */
typedef enum VegaDexStatus {
    VEGA_DEX_OK = 0, VEGA_DEX_INVALID_ARGUMENT, VEGA_DEX_BAD_SIZE,
    VEGA_DEX_BAD_MAGIC, VEGA_DEX_BAD_VERSION, VEGA_DEX_BAD_CRC,
    VEGA_DEX_BAD_FLAGS, VEGA_DEX_BAD_PADDING, VEGA_DEX_CAUGHT_WITHOUT_SEEN,
    VEGA_DEX_BAD_OWNER, VEGA_DEX_BAD_MODE, VEGA_DEX_PARENT_NOT_VERIFIED
} VegaDexStatus;
typedef enum VegaDexMode {
    VEGA_DEX_GET_SEEN = 0, VEGA_DEX_GET_CAUGHT = 1,
    VEGA_DEX_SET_SEEN = 2, VEGA_DEX_SET_CAUGHT = 3,
    VEGA_DEX_CLEAR_SEEN = 4, VEGA_DEX_CLEAR_CAUGHT = 5
} VegaDexMode;
uint32_t VegaDexChecksum(const uint8_t *data, size_t size);
VegaDexStatus VegaDexValidate(const uint8_t *data, size_t size);
VegaDexStatus VegaDexInitNew(uint8_t *data, size_t size);
/* 全legacy鏡を証拠として保全。曖昧な旧bitを新ownerへ複製しない。 */
VegaDexStatus VegaDexInitLegacy(uint8_t *data, size_t size,
                              const uint8_t *legacy, size_t legacy_size);
VegaDexStatus VegaDexAccess(uint8_t *data, size_t size, uint16_t owner,
                           uint8_t mode, uint8_t *value);
VegaDexStatus VegaDexCount(const uint8_t *data, size_t size, uint8_t mode,
                          uint16_t *count);
VegaDexStatus VegaDexLoad(uint8_t *data, size_t size, const uint8_t *record,
                         size_t record_size, const uint8_t *legacy,
                         size_t legacy_size, uint8_t parent_verified);
#endif
