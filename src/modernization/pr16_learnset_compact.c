#include "pr16_learnset_compact.h"
#ifndef PR16_OWNER_GATE
#define PR16_OWNER_GATE Pr16ResolveLearnsetOwner
#endif
static uint16_t get16(const uint8_t *p)
{ return (uint16_t)(p[0] | ((uint16_t)p[1] << 8)); }
static uint32_t get32(const uint8_t *p)
{ return (uint32_t)get16(p) | ((uint32_t)get16(p + 2) << 16); }
uint8_t Pr16ReadCompactConditional(const uint8_t *image, uint32_t size,
    uint16_t species, uint8_t consumer, struct Pr16RuntimeView *out)
{
    uint16_t owner, offset, tag, count, i;
    uint32_t length;
    uint8_t action, column;
    if (!out) return PR16_OWNER_INVALID;
    out->bytes = (const uint8_t *)0; out->count = 0;
    out->owner = PR16_LEARNSET_NO_OWNER;
    if (!image || size < 18416u || size >= 65535u ||
        get32(image) != 0x32434C50u || get16(image + 4) != 1u ||
        get16(image + 6) != 1671u || get32(image + 8) != 32u ||
        get32(image + 12) != 1704u || get32(image + 16) != 18416u ||
        get32(image + 20) != size || get32(image + 24) != 0x1C3u ||
        get32(image + 28) != 0u || image[1703] || get16(image + 18414))
        return PR16_OWNER_INVALID;
    action = PR16_OWNER_GATE(image + 32, 1671u, species, consumer, &owner);
    if (action == PR16_OWNER_INVALID || owner >= 1671u) return PR16_OWNER_INVALID;
    switch (consumer) {
    case PR16_CONSUMER_EGG: column = 0; break;
    case PR16_CONSUMER_EVOLUTION: column = 1; break;
    case PR16_CONSUMER_REMINDER: column = 2; break;
    case PR16_CONSUMER_SHARED_EGG: column = 3; break;
    case PR16_CONSUMER_TUTOR: column = 4; break;
    default:
        return action == PR16_OWNER_CONDITION_REQUIRED ? action : PR16_RUNTIME_NOT_LINKED;
    }
    offset = get16(image + 1704u + ((uint32_t)owner * 5u + column) * 2u);
    if (action != PR16_OWNER_PREPARED_LOOKUP) {
        if (offset != 65535u) return PR16_OWNER_INVALID;
        out->owner = owner; return action;
    }
    if (offset < 18416u || (offset & 1u) || offset > size || size - offset < 2u)
        return PR16_OWNER_INVALID;
    tag = get16(image + offset);
    if (consumer == PR16_CONSUMER_TUTOR) {
        if (tag != 0x8040u) return PR16_OWNER_INVALID;
        count = 64u; length = 16u;
    } else {
        if (tag > 50u) return PR16_OWNER_INVALID;
        count = tag; length = (uint32_t)count * 2u;
    }
    if (length > size - offset - 2u) return PR16_OWNER_INVALID;
    if (consumer == PR16_CONSUMER_TUTOR) {
        for (i = 8u; i < 16u; ++i) if (image[offset + 2u + i]) return PR16_OWNER_INVALID;
    } else {
        for (i = 0u; i < count; ++i) {
            uint16_t move = get16(image + offset + 2u + (uint32_t)i * 2u);
            if (!move || move > 1062u) return PR16_OWNER_INVALID;
        }
    }
    out->bytes = image + offset + 2u; out->count = count; out->owner = owner;
    return PR16_OWNER_PREPARED_LOOKUP;
}
