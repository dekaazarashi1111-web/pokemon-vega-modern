/* Passive, fail-closed observer for one controller-driven P05 turn.
 * This header has no mGBA dependency: tests feed samples, not a fake emulator.
 */
#ifndef MODERNIZATION_P05_TURN_OBSERVER_H
#define MODERNIZATION_P05_TURN_OBSERVER_H
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

enum P05TurnState { P05_TURN_RUNNING, P05_TURN_PASS, P05_TURN_FAIL };
struct P05TurnSample {
    uint32_t frame;
    uint32_t warnings;
    uint32_t battle_flags;
    uint16_t species[2];
    uint16_t moves[2];
    uint16_t abilities[2];
    uint16_t hp[2];
    uint8_t pp[2];
    uint8_t types[2][2];
    uint8_t count;
    uint8_t absent;
    uint8_t outcome;
    uint8_t attacker;
    uint16_t current_move;
    uint8_t result_flags;
    uint16_t chosen_move;
    uint8_t chosen_action;
    bool action_ready;
    bool move_ready;
};
struct P05TurnObserver {
    struct P05TurnSample initial;
    uint32_t last_frame;
    uint32_t max_frames;
    uint32_t action_frame;
    uint32_t move_frame;
    uint32_t player_spent_frame;
    uint32_t enemy_spent_frame;
    uint32_t returned_frame;
    uint32_t hit_frame;
    uint32_t immune_frame;
    uint32_t stable_return_frames;
    uint8_t previous_pp[2];
    uint16_t previous_hp[2];
    bool expect_hit;
    bool action_seen;
    bool move_seen;
    bool selected_seen;
    bool left_selection;
    enum P05TurnState state;
    const char *error;
};
/* The production single-wild classifier allows only IS_MASTER bookkeeping.
 * overlays/qol_production/qol_production.c: auto_battle_allowed_values.
 * No LINK, TRAINER, DOUBLE, facility or unknown route bit is accepted. */
static inline bool p05_ordinary_single_wild(uint32_t flags)
{
    return (flags & ~UINT32_C(4)) == 0;
}
static inline enum P05TurnState p05_turn_fail(
    struct P05TurnObserver *o, const char *message)
{
    o->state = P05_TURN_FAIL;
    o->error = message;
    return o->state;
}
static inline void p05_turn_init(struct P05TurnObserver *o,
    const struct P05TurnSample *s, bool expect_hit, uint32_t max_frames)
{
    memset(o, 0, sizeof(*o));
    o->initial = *s;
    o->last_frame = s->frame;
    o->max_frames = max_frames;
    o->expect_hit = expect_hit;
    memcpy(o->previous_pp, s->pp, sizeof(o->previous_pp));
    memcpy(o->previous_hp, s->hp, sizeof(o->previous_hp));
    if (!p05_ordinary_single_wild(s->battle_flags)
        || s->count != 2 || s->absent != 0 || s->outcome != 0
        || s->warnings != 0 || !s->action_ready || s->move_ready
        || s->species[0] == 0 || s->species[1] == 0
        || s->moves[0] != 33 || s->moves[1] != 150
        || s->pp[0] < 2 || s->pp[1] < 2
        || s->hp[0] < 2 || s->hp[1] < 2 || max_frames < 8)
        (void)p05_turn_fail(o, "invalid initial action-selection fixture");
}
static inline enum P05TurnState p05_turn_observe(
    struct P05TurnObserver *o, const struct P05TurnSample *s)
{
    if (o->state != P05_TURN_RUNNING)
        return o->state;
    if (s->frame <= o->last_frame)
        return p05_turn_fail(o, "non-monotonic sample frame");
    if (s->frame - o->initial.frame > o->max_frames)
        return p05_turn_fail(o, "turn timeout");
    o->last_frame = s->frame;
    if (!p05_ordinary_single_wild(s->battle_flags)
        || s->battle_flags != o->initial.battle_flags
        || s->warnings || s->count != 2 || s->absent || s->outcome)
        return p05_turn_fail(o, "warning or unexpected battle exit");
    if (s->action_ready && s->move_ready)
        return p05_turn_fail(o, "contradictory controller state");
    for (unsigned b = 0; b < 2; ++b) {
        if (s->species[b] != o->initial.species[b]
            || s->moves[b] != o->initial.moves[b]
            || s->abilities[b] != o->initial.abilities[b]
            || memcmp(s->types[b], o->initial.types[b], 2) != 0)
            return p05_turn_fail(o, "live fixture identity changed");
        if (s->pp[b] > o->previous_pp[b]
            || s->pp[b] + 1U < o->initial.pp[b])
            return p05_turn_fail(o, "PP restored or multiple turns executed");
        if (s->hp[b] == 0 || s->hp[b] > o->previous_hp[b])
            return p05_turn_fail(o, "faint or unexplained healing");
        o->previous_pp[b] = s->pp[b];
        o->previous_hp[b] = s->hp[b];
    }
    if (s->hp[0] != o->initial.hp[0])
        return p05_turn_fail(o, "Splash opponent damaged the player");
    if (!o->player_spent_frame && s->action_ready) {
        if (!o->action_seen) o->action_frame = s->frame;
        o->action_seen = true;
    }
    if (!o->player_spent_frame && s->move_ready) {
        if (!o->action_seen)
            return p05_turn_fail(o, "move selection preceded action selection");
        if (!o->move_seen) o->move_frame = s->frame;
        o->move_seen = true;
    }
    if (o->move_seen && s->chosen_action == 0 && s->chosen_move == 33)
        o->selected_seen = true;
    if (s->pp[0] + 1U == o->initial.pp[0] && !o->player_spent_frame) {
        if (!o->move_seen || !o->selected_seen)
            return p05_turn_fail(o, "PP spent without controller selection");
        o->player_spent_frame = s->frame;
    }
    if (s->pp[1] + 1U == o->initial.pp[1] && !o->enemy_spent_frame)
        o->enemy_spent_frame = s->frame;
    if (o->player_spent_frame && !s->action_ready && !s->move_ready)
        o->left_selection = true;
    if (s->hp[1] < o->initial.hp[1] && !o->hit_frame) {
        if (!o->player_spent_frame || s->attacker != 0
            || s->current_move != 33)
            return p05_turn_fail(o, "damage not attributed to selected Tackle");
        o->hit_frame = s->frame;
    }
    if (o->player_spent_frame && s->attacker == 0
        && s->current_move == 33 && (s->result_flags & 8U)
        && !o->immune_frame)
        o->immune_frame = s->frame;
    if (s->action_ready && o->player_spent_frame && o->enemy_spent_frame
        && o->left_selection) {
        if (!o->returned_frame) o->returned_frame = s->frame;
        ++o->stable_return_frames;
        if (o->stable_return_frames >= 2) {
            if (o->expect_hit) {
                if (!o->hit_frame || o->immune_frame
                    || s->hp[1] >= o->initial.hp[1])
                    return p05_turn_fail(o, "expected damage was not observed");
            } else if (o->hit_frame || !o->immune_frame
                       || s->hp[1] != o->initial.hp[1]) {
                return p05_turn_fail(o, "expected Ghost immunity was not observed");
            }
            o->state = P05_TURN_PASS;
        }
    } else {
        o->returned_frame = 0;
        o->stable_return_frames = 0;
    }
    return o->state;
}
#endif
