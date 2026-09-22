#include "pr16_learnset_progress_bindings.h"
struct Pr16TestMon {
    uint16_t species;
    uint8_t level, egg;
    uint16_t moves[4];
    uint8_t pp[4], bonus, opaque[15];
};
const uint8_t *pr16_test_image;
uint32_t pr16_test_image_size;
uint8_t pr16_test_cursor;
uint16_t pr16_test_pending;
uint32_t Pr16TestData(const void *p, int field, uint8_t *out)
{
    const struct Pr16TestMon *mon = p;
    (void)out;
    if (field == 11) return mon->species;
    if (field == 45) return mon->egg;
    if (field == 56) return mon->level;
    if (field >= 13 && field < 17) return mon->moves[field - 13];
    return 0;
}
uint8_t Pr16TestLevel(const void *p) { return ((const struct Pr16TestMon *)p)->level; }
uint16_t Pr16TestGive(void *p, uint16_t move)
{
    struct Pr16TestMon *mon = p;
    for (unsigned i = 0; i < 4; ++i) {
        if (!mon->moves[i]) {
            mon->moves[i] = move;
            mon->pp[i] = (uint8_t)(move % 40 + 1);
            return move;
        }
        if (mon->moves[i] == move) return 0xFFFEu;
    }
    return 0xFFFFu;
}
