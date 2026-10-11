#include "pr16_learnset_progress.h"

static uint16_t move_at(const struct Pr16RuntimeView *view, uint8_t i)
{
    const uint8_t *p = view->bytes + (uint32_t)i * 3u;
    return (uint16_t)(p[0] | ((uint16_t)p[1] << 8));
}
static uint8_t valid(const struct Pr16RuntimeView *view, uint8_t level)
{
    uint8_t i, previous = 0;
    if (!view || !view->bytes || view->owner >= 1671u || view->count > 40u
        || !level || level > 100u)
        return 0;
    for (i = 0; i < view->count; ++i) {
        uint8_t lv = view->bytes[(uint32_t)i * 3u + 2u];
        uint16_t move = move_at(view, i);
        if (!move || move > 1062u || !lv || lv > 100u || lv < previous)
            return 0;
        previous = lv;
    }
    return 1;
}
uint8_t Pr16ProgressInitial(const struct Pr16RuntimeView *view, uint8_t level,
                           uint16_t *moves, uint8_t capacity)
{
    uint8_t end = 0, start, count, i;
    if (!moves || !valid(view, level))
        return 0;
    while (end < view->count && view->bytes[(uint32_t)end * 3u + 2u] <= level)
        ++end;
    start = end > 4u ? end - 4u : 0u;
    count = end - start;
    if (count > capacity)
        return 0; /* All-or-nothing; caller canaries are not scratch space. */
    for (i = 0; i < count; ++i)
        moves[i] = move_at(view, start + i);
    return count;
}
uint16_t Pr16ProgressNext(const struct Pr16RuntimeView *view, uint8_t level,
                          uint8_t firstMove, uint8_t *cursor)
{
    uint8_t i;
    if (!cursor || !valid(view, level))
        return 0;
    i = firstMove ? 0u : *cursor;
    if (firstMove)
        while (i < view->count && view->bytes[(uint32_t)i * 3u + 2u] < level)
            ++i;
    if (i >= view->count || view->bytes[(uint32_t)i * 3u + 2u] != level) {
        *cursor = PR16_PROGRESS_END;
        return 0;
    }
    *cursor = i + 1u;
    return move_at(view, i);
}
