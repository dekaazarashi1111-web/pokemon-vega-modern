#include "pr16_learnset_runtime.h"

static uint16_t read16(const uint8_t *p)
{
    return (uint16_t)(p[0] | ((uint16_t)p[1] << 8));
}
static uint32_t read32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8)
        | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static uint8_t range(uint32_t start, uint32_t count, uint32_t limit)
{
    return start <= limit && count <= limit - start;
}
uint8_t Pr16ReadLearnsetRuntime(const uint8_t *image, uint32_t size,
                              uint16_t species, uint8_t consumer,
                              struct Pr16RuntimeView *out)
{
    uint32_t policy, index, level, machine, at, end;
    uint16_t count, slot, owner, i;
    uint8_t action;
    if (!out)
        return PR16_OWNER_INVALID;
    out->bytes = (const uint8_t *)0;
    out->count = 0;
    out->owner = PR16_LEARNSET_NO_OWNER;
    if (!image || size < 32u || read32(image) != 0x31524C50u
        || read16(image + 4) != 1u || read16(image + 6) != 1671u
        || read32(image + 24) != size || read32(image + 28) != 0u)
        return PR16_OWNER_INVALID;
    policy = read32(image + 8);
    index = read32(image + 12);
    level = read32(image + 16);
    machine = read32(image + 20);
    if (policy != 32u || index != 1704u || level != 15072u
        || (machine & 3u) || machine < level
        || !range(machine, 1483u * 16u, size) || machine + 1483u * 16u != size)
        return PR16_OWNER_INVALID;
    action = Pr16ResolveLearnsetOwner(image + policy, 1671u, species, consumer, &owner);
    if (action == PR16_OWNER_INVALID)
        return action;
    at = index + (uint32_t)owner * 8u;
    count = read16(image + at + 4u);
    slot = read16(image + at + 6u);
    at = read32(image + at);
    if (action == PR16_OWNER_PRESERVE_IDENTITY || action == PR16_OWNER_CARRY_EXISTING) {
        if (at != 0xFFFFFFFFu || count != 0u || slot != 0xFFFFu)
            return PR16_OWNER_INVALID;
        out->owner = owner;
        return action;
    }
    if (count > 40u || slot >= 1483u || at < level
        || !range(at, ((uint32_t)count + 1u) * 3u, machine))
        return PR16_OWNER_INVALID;
    end = at + (uint32_t)count * 3u;
    if (read16(image + end) != 0u || image[end + 2u] != 255u)
        return PR16_OWNER_INVALID;
    for (i = 0; i < count; ++i) {
        const uint8_t *p = image + at + (uint32_t)i * 3u;
        uint16_t move = read16(p);
        if (!move || move > 1062u || !p[2] || p[2] > 100u)
            return PR16_OWNER_INVALID;
    }
    out->owner = owner;
    if (consumer == PR16_CONSUMER_LEVEL_UP) {
        out->bytes = image + at;
        out->count = count;
        return PR16_OWNER_PREPARED_LOOKUP;
    }
    if (consumer == PR16_CONSUMER_MACHINE) {
        out->bytes = image + machine + (uint32_t)slot * 16u;
        out->count = 128u;
        return PR16_OWNER_PREPARED_LOOKUP;
    }
    /* Do not turn an unconnected egg/evolution/condition into a direct grant. */
    return action == PR16_OWNER_CONDITION_REQUIRED ? action : PR16_RUNTIME_NOT_LINKED;
}
uint8_t Pr16RuntimeLevelMoves(const uint8_t *image, uint32_t size,
                            uint16_t species, uint16_t *moves, uint16_t capacity)
{
    struct Pr16RuntimeView view;
    uint16_t i;
    if (!moves || Pr16ReadLearnsetRuntime(image, size, species, PR16_CONSUMER_LEVEL_UP, &view)
        != PR16_OWNER_PREPARED_LOOKUP || view.count > capacity)
        return 0;
    for (i = 0; i < view.count; ++i)
        moves[i] = read16(view.bytes + (uint32_t)i * 3u);
    return (uint8_t)view.count;
}
uint8_t Pr16RuntimeMachineAllowed(const uint8_t *image, uint32_t size,
                                uint16_t species, uint16_t slot)
{
    struct Pr16RuntimeView view;
    if (slot >= 128u || Pr16ReadLearnsetRuntime(image, size, species, PR16_CONSUMER_MACHINE, &view)
        != PR16_OWNER_PREPARED_LOOKUP)
        return 0;
    return (view.bytes[slot >> 3] >> (slot & 7u)) & 1u;
}
