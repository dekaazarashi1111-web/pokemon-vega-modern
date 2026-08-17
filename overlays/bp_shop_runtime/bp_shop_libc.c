/* Minimal freestanding libc surface used by save_migration.c. */
#include <stddef.h>

void *memcpy(void *destination, const void *source, size_t size)
{
    unsigned char *out = (unsigned char *)destination;
    const unsigned char *in = (const unsigned char *)source;
    size_t index;
    for (index = 0; index < size; ++index)
        out[index] = in[index];
    return destination;
}

void *memset(void *destination, int value, size_t size)
{
    unsigned char *out = (unsigned char *)destination;
    size_t index;
    for (index = 0; index < size; ++index)
        out[index] = (unsigned char)value;
    return destination;
}
