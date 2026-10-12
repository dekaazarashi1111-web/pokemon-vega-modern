#include "dex_owner.h"

_Static_assert(VEGA_DEX_CAUGHT_OFFSET == VEGA_DEX_SEEN_OFFSET + VEGA_DEX_BITMAP_SIZE,
               "seen/caughtは隣接する別owner");
_Static_assert(VEGA_DEX_LEGACY_OFFSET == VEGA_DEX_CAUGHT_OFFSET + VEGA_DEX_BITMAP_SIZE,
               "legacy証拠をbitmapに使わない");
_Static_assert(VEGA_DEX_LEGACY_OFFSET + VEGA_DEX_LEGACY_SIZE == VEGA_DEX_OWNER_SIZE,
               "owner外へ書き込まない");
_Static_assert(VEGA_DEX_CHUNK13_OFFSET + VEGA_DEX_OWNER_SIZE == 0xFF0u,
               "chunk13 footerを占有しない");
_Static_assert(VEGA_DEX_OWNER_RAM + VEGA_DEX_OWNER_SIZE <= 0x0203DFB0u,
               "battle pointerへ届かない");

static uint8_t overlaps(const void *a, size_t a_size, const void *b, size_t b_size)
{
    uintptr_t x = (uintptr_t)a, y = (uintptr_t)b;
    if (a == NULL || b == NULL || a_size == 0u || b_size == 0u) return 0u;
    return (uint8_t)(x <= y ? y - x < a_size : x - y < b_size);
}
static uint16_t read16(const uint8_t *p)
{
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}
static uint32_t read32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8)
         | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static void write32(uint8_t *p, uint32_t value)
{
    size_t i;
    for (i = 0; i < 4u; ++i) p[i] = (uint8_t)(value >> (8u * i));
}
uint32_t VegaDexChecksum(const uint8_t *data, size_t size)
{
    uint32_t crc = 0xFFFFFFFFu;
    size_t i;
    uint8_t bit;
    if (data == NULL || size != VEGA_DEX_OWNER_SIZE) return 0u;
    for (i = 0; i < size; ++i) {
        crc ^= (i >= 4u && i < 8u) ? 0u : data[i];
        for (bit = 0; bit < 8u; ++bit)
            crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}
static void finalize(uint8_t *data)
{
    write32(data + 4u, VegaDexChecksum(data, VEGA_DEX_OWNER_SIZE));
}
VegaDexStatus VegaDexValidate(const uint8_t *data, size_t size)
{
    size_t i;
    if (data == NULL) return VEGA_DEX_INVALID_ARGUMENT;
    if (size != VEGA_DEX_OWNER_SIZE) return VEGA_DEX_BAD_SIZE;
    if (data[0] != 'M' || data[1] != 'D' || data[2] != 'X' || data[3] != '1')
        return VEGA_DEX_BAD_MAGIC;
    if (read16(data + 8u) != VEGA_DEX_NAMESPACE_VERSION) return VEGA_DEX_BAD_VERSION;
    if ((data[10] & (uint8_t)~VEGA_DEX_FLAG_LEGACY_SNAPSHOT) != 0u || data[11] != 0u)
        return VEGA_DEX_BAD_FLAGS;
    if (read32(data + 4u) != VegaDexChecksum(data, size)) return VEGA_DEX_BAD_CRC;
    if (((data[VEGA_DEX_CAUGHT_OFFSET - 1u] | data[VEGA_DEX_LEGACY_OFFSET - 1u])
         & 0xC0u) != 0u) return VEGA_DEX_BAD_PADDING;
    for (i = 0; i < VEGA_DEX_BITMAP_SIZE; ++i)
        if ((data[VEGA_DEX_CAUGHT_OFFSET + i]
             & (uint8_t)~data[VEGA_DEX_SEEN_OFFSET + i]) != 0u)
            return VEGA_DEX_CAUGHT_WITHOUT_SEEN;
    if (!(data[10] & VEGA_DEX_FLAG_LEGACY_SNAPSHOT))
        for (i = VEGA_DEX_LEGACY_OFFSET; i < VEGA_DEX_OWNER_SIZE; ++i)
            if (data[i] != 0u) return VEGA_DEX_BAD_FLAGS;
    return VEGA_DEX_OK;
}
VegaDexStatus VegaDexInitNew(uint8_t *data, size_t size)
{
    size_t i;
    if (data == NULL) return VEGA_DEX_INVALID_ARGUMENT;
    if (size != VEGA_DEX_OWNER_SIZE) return VEGA_DEX_BAD_SIZE;
    for (i = 0; i < size; ++i) data[i] = 0u;
    data[0] = 'M'; data[1] = 'D'; data[2] = 'X'; data[3] = '1';
    data[8] = (uint8_t)VEGA_DEX_NAMESPACE_VERSION;
    data[9] = (uint8_t)(VEGA_DEX_NAMESPACE_VERSION >> 8);
    finalize(data);
    return VEGA_DEX_OK;
}
VegaDexStatus VegaDexInitLegacy(uint8_t *data, size_t size,
                              const uint8_t *legacy, size_t legacy_size)
{
    size_t i;
    VegaDexStatus status;
    /* overlapを許すと初期化で原本を壊す。入力原本は常に別領域。 */
    if (data == NULL || legacy == NULL) return VEGA_DEX_INVALID_ARGUMENT;
    if (size != VEGA_DEX_OWNER_SIZE || legacy_size != VEGA_DEX_LEGACY_SIZE)
        return VEGA_DEX_BAD_SIZE;
    if (overlaps(data, size, legacy, legacy_size))
        return VEGA_DEX_INVALID_ARGUMENT;
    status = VegaDexInitNew(data, size);
    if (status != VEGA_DEX_OK) return status;
    for (i = 0; i < legacy_size; ++i) data[VEGA_DEX_LEGACY_OFFSET + i] = legacy[i];
    data[10] = VEGA_DEX_FLAG_LEGACY_SNAPSHOT;
    finalize(data);
    return VEGA_DEX_OK;
}
VegaDexStatus VegaDexAccess(uint8_t *data, size_t size, uint16_t owner,
                           uint8_t mode, uint8_t *value)
{
    VegaDexStatus status;
    size_t index;
    uint8_t mask;
    if (value == NULL || overlaps(data, size, value, sizeof(*value)))
        return VEGA_DEX_INVALID_ARGUMENT;
    if (owner == 0u || owner > VEGA_DEX_OWNER_COUNT) return VEGA_DEX_BAD_OWNER;
    if (mode > VEGA_DEX_CLEAR_CAUGHT) return VEGA_DEX_BAD_MODE;
    status = VegaDexValidate(data, size);
    if (status != VEGA_DEX_OK) return status;
    index = (size_t)(owner - 1u) >> 3;
    mask = (uint8_t)(1u << ((owner - 1u) & 7u));
    if (mode == VEGA_DEX_SET_SEEN || mode == VEGA_DEX_SET_CAUGHT)
        data[VEGA_DEX_SEEN_OFFSET + index] |= mask;
    if (mode == VEGA_DEX_SET_CAUGHT) data[VEGA_DEX_CAUGHT_OFFSET + index] |= mask;
    if (mode == VEGA_DEX_CLEAR_SEEN) {
        data[VEGA_DEX_SEEN_OFFSET + index] &= (uint8_t)~mask;
        data[VEGA_DEX_CAUGHT_OFFSET + index] &= (uint8_t)~mask;
    }
    if (mode == VEGA_DEX_CLEAR_CAUGHT)
        data[VEGA_DEX_CAUGHT_OFFSET + index] &= (uint8_t)~mask;
    if (mode >= VEGA_DEX_SET_SEEN) finalize(data);
    *value = (uint8_t)((data[(mode == VEGA_DEX_GET_CAUGHT
        || mode == VEGA_DEX_SET_CAUGHT || mode == VEGA_DEX_CLEAR_CAUGHT)
        ? VEGA_DEX_CAUGHT_OFFSET + index : VEGA_DEX_SEEN_OFFSET + index] & mask) != 0u);
    return VEGA_DEX_OK;
}
VegaDexStatus VegaDexCount(const uint8_t *data, size_t size, uint8_t mode,
                          uint16_t *count)
{
    VegaDexStatus status;
    size_t i;
    uint16_t total = 0u;
    if (count == NULL || overlaps(data, size, count, sizeof(*count)))
        return VEGA_DEX_INVALID_ARGUMENT;
    if (mode != VEGA_DEX_GET_SEEN && mode != VEGA_DEX_GET_CAUGHT)
        return VEGA_DEX_BAD_MODE;
    status = VegaDexValidate(data, size);
    if (status != VEGA_DEX_OK) return status;
    for (i = 0; i < VEGA_DEX_BITMAP_SIZE; ++i) {
        uint8_t value = data[(mode == VEGA_DEX_GET_CAUGHT
                           ? VEGA_DEX_CAUGHT_OFFSET : VEGA_DEX_SEEN_OFFSET) + i];
        while (value != 0u) { total += (uint16_t)(value & 1u); value >>= 1; }
    }
    *count = total;
    return VEGA_DEX_OK;
}

VegaDexStatus VegaDexLoad(uint8_t *data, size_t size, const uint8_t *record,
                         size_t record_size, const uint8_t *legacy,
                         size_t legacy_size, uint8_t parent_verified)
{
    size_t i;
    uint8_t all_zero = 1u, all_erased = 1u;
    VegaDexStatus status;
    if (data == NULL || record == NULL) return VEGA_DEX_INVALID_ARGUMENT;
    if (size != VEGA_DEX_OWNER_SIZE || record_size != VEGA_DEX_OWNER_SIZE)
        return VEGA_DEX_BAD_SIZE;
    if (parent_verified != 1u) return VEGA_DEX_PARENT_NOT_VERIFIED;
    if (data != record && overlaps(data, size, record, record_size))
        return VEGA_DEX_INVALID_ARGUMENT;
    for (i = 0; i < record_size; ++i) {
        if (record[i] != 0u) all_zero = 0u;
        if (record[i] != 0xFFu) all_erased = 0u;
    }
    if (all_zero || all_erased)
        return VegaDexInitLegacy(data, size, legacy, legacy_size);
    status = VegaDexValidate(record, record_size);
    if (status != VEGA_DEX_OK) return status;
    for (i = 0; i < size; ++i) data[i] = record[i];
    return VEGA_DEX_OK;
}
