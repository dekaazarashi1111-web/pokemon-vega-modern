#include "pr16_learnset_conditional.h"
#ifndef PR16_OWNER_GATE
#define PR16_OWNER_GATE Pr16ResolveLearnsetOwner
#endif

static uint16_t get16(const uint8_t *p)
{ return (uint16_t)(p[0] | ((uint16_t)p[1] << 8)); }
static uint32_t get32(const uint8_t *p)
{ return (uint32_t)get16(p) | ((uint32_t)get16(p + 2) << 16); }
static uint8_t valid_moves(const struct Pr16RuntimeView *v, uint8_t stride)
{
    uint16_t i;
    if (!v || v->owner >= 1671u || v->count > 50u || (v->count && !v->bytes))
        return 0;
    for (i = 0; i < v->count; ++i) {
        const uint8_t *p = v->bytes + (uint32_t)i * stride;
        if (!get16(p) || get16(p) > 1062u ||
            (stride == 3u && (!p[2] || p[2] > 100u)))
            return 0;
    }
    return 1;
}
uint8_t Pr16ReadLearnsetConditional(const uint8_t *image, uint32_t size,
    uint16_t species, uint8_t consumer, struct Pr16RuntimeView *out)
{
    uint32_t at, offset, length;
    uint16_t owner, count, i;
    uint8_t action, column;
    if (!out) return PR16_OWNER_INVALID;
    out->bytes = (const uint8_t *)0; out->count = 0;
    out->owner = PR16_LEARNSET_NO_OWNER;
    if (!image || size < 68544u || get32(image) != 0x31434C50u ||
        get16(image + 4) != 1u || get16(image + 6) != 1671u ||
        get32(image + 8) != 32u || get32(image + 12) != 1704u ||
        get32(image + 16) != 68544u || get32(image + 20) != size ||
        get32(image + 24) != 0x1C3u || get32(image + 28) != 0u)
        return PR16_OWNER_INVALID;
    action = PR16_OWNER_GATE(image + 32, 1671u, species, consumer, &owner);
    if (action == PR16_OWNER_INVALID) return action;
    switch (consumer) {
    case PR16_CONSUMER_EGG: column = 0; break;
    case PR16_CONSUMER_EVOLUTION: column = 1; break;
    case PR16_CONSUMER_REMINDER: column = 2; break;
    case PR16_CONSUMER_SHARED_EGG: column = 3; break;
    case PR16_CONSUMER_TUTOR: column = 4; break;
    default:
        /* 姿/進化前持越しを新しい付与経路へ昇格しない。 */
        return action == PR16_OWNER_CONDITION_REQUIRED ? action : PR16_RUNTIME_NOT_LINKED;
    }
    at = 1704u + ((uint32_t)owner * 5u + column) * 8u;
    offset = get32(image + at); count = get16(image + at + 4);
    if (get16(image + at + 6) != (uint16_t)((owner << 4) | consumer))
        return PR16_OWNER_INVALID;
    if (action != PR16_OWNER_PREPARED_LOOKUP) {
        if (offset != 0xFFFFFFFFu || count) return PR16_OWNER_INVALID;
        out->owner = owner; return action;
    }
    length = consumer == PR16_CONSUMER_TUTOR ? 16u : (uint32_t)count * 2u;
    if (offset < 68544u || offset > size || length > size - offset ||
        (offset & 1u) || (consumer == PR16_CONSUMER_TUTOR ? count != 64u : count > 50u))
        return PR16_OWNER_INVALID;
    if (consumer == PR16_CONSUMER_TUTOR) {
        for (i = 8; i < 16u; ++i) if (image[offset + i]) return PR16_OWNER_INVALID;
    } else {
        for (i = 0; i < count; ++i) {
            uint16_t move = get16(image + offset + (uint32_t)i * 2u);
            if (!move || move > 1062u) return PR16_OWNER_INVALID;
        }
    }
    out->bytes = image + offset; out->count = count; out->owner = owner;
    return PR16_OWNER_PREPARED_LOOKUP;
}
static uint8_t contains(const uint16_t *moves, uint16_t count, uint16_t move)
{
    uint16_t i;
    for (i = 0; i < count; ++i) if (moves[i] == move) return 1;
    return 0;
}
uint8_t Pr16ConditionalList(const struct Pr16RuntimeView *view,
    const uint16_t *known, uint8_t known_count, uint16_t *moves, uint16_t capacity)
{
    uint16_t tmp[50], i, n = 0;
    if (!moves || known_count > 4u || (known_count && !known) || !valid_moves(view, 2u)) return 0;
    for (i = 0; i < view->count; ++i) {
        uint16_t move = get16(view->bytes + (uint32_t)i * 2u);
        if (!contains(known, known_count, move) && !contains(tmp, n, move)) tmp[n++] = move;
    }
    if (n > capacity) return 0;
    for (i = 0; i < n; ++i) moves[i] = tmp[i];
    return (uint8_t)n;
}
uint16_t Pr16ConditionalEvolutionNext(const struct Pr16RuntimeView *evolution,
    const struct Pr16RuntimeView *levels, uint8_t level, uint8_t first, uint8_t *cursor)
{
    uint16_t index, total;
    if (!cursor || !level || level > 100u || !valid_moves(evolution, 2u) ||
        !valid_moves(levels, 3u) || evolution->owner != levels->owner) return 0;
    total = evolution->count + levels->count;
    index = first ? 0u : *cursor;
    for (; index < total; ++index) {
        const uint8_t *p;
        if (index < evolution->count) {
            p = evolution->bytes + (uint32_t)index * 2u;
        } else {
            p = levels->bytes + (uint32_t)(index - evolution->count) * 3u;
            if (p[2] != level) continue;
        }
        *cursor = (uint8_t)(index + 1u);
        return get16(p);
    }
    *cursor = (uint8_t)total;
    return 0;
}
uint8_t Pr16ConditionalReminder(const struct Pr16RuntimeView *evolution,
    const struct Pr16RuntimeView *levels, const struct Pr16RuntimeView *reminder,
    uint8_t level, const uint16_t known[4], uint16_t *moves, uint16_t capacity)
{
    uint16_t tmp[PR16_CONDITIONAL_CAPACITY], n = 0, i;
    uint8_t family;
    const struct Pr16RuntimeView *views[3];
    if (!known || !moves || !level || level > 100u || !valid_moves(evolution, 2u) ||
        !valid_moves(levels, 3u) || !valid_moves(reminder, 2u) ||
        evolution->owner != levels->owner || evolution->owner != reminder->owner) return 0;
    views[0] = evolution; views[1] = levels; views[2] = reminder;
    for (family = 0; family < 3u; ++family) {
        const struct Pr16RuntimeView *v = views[family];
        for (i = 0; i < v->count; ++i) {
            const uint8_t *p = v->bytes + (uint32_t)i * (family == 1u ? 3u : 2u);
            uint16_t move = get16(p);
            if ((family == 1u && p[2] > level) || contains(known, 4u, move) || contains(tmp, n, move)) continue;
            if (n >= PR16_CONDITIONAL_CAPACITY || n >= capacity) return 0;
            tmp[n++] = move;
        }
    }
    for (i = 0; i < n; ++i) moves[i] = tmp[i];
    return (uint8_t)n;
}
uint8_t Pr16ConditionalTutorAllowed(const uint8_t *image, uint32_t size,
    uint16_t species, uint16_t slot)
{
    struct Pr16RuntimeView view;
    if (slot >= 64u || Pr16ReadLearnsetConditional(image, size, species,
        PR16_CONSUMER_TUTOR, &view) != PR16_OWNER_PREPARED_LOOKUP) return 0;
    return (view.bytes[slot >> 3] >> (slot & 7u)) & 1u;
}
