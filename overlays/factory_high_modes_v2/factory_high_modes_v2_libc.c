#include <stddef.h>
#include <stdint.h>

void *memcpy(void *destination, const void *source, size_t size)
{
    uint8_t *out = (uint8_t *)destination;
    const uint8_t *in = (const uint8_t *)source;
    size_t index;
    for (index = 0; index < size; ++index)
        out[index] = in[index];
    return destination;
}

void *memset(void *destination, int value, size_t size)
{
    uint8_t *out = (uint8_t *)destination;
    size_t index;
    for (index = 0; index < size; ++index)
        out[index] = (uint8_t)value;
    return destination;
}
