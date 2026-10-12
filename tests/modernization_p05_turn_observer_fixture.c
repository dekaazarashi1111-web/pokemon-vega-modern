/* Synthetic sample traces test ONLY the portable observer, not mGBA or a ROM. */
#include "modernization_p05_turn_observer.h"
#include <stdio.h>
#include <stdlib.h>

static const char *const cases[] = {
    "valid_hit", "valid_immune", "brief_return", "invalid_initial", "warning",
    "battle_exit", "battler_count", "absent", "wrong_species", "wrong_move",
    "wrong_ability", "wrong_type", "pp_refill", "two_player_turns", "two_enemy_turns",
    "faint", "healing", "player_damaged", "no_action_selection", "no_move_selection",
    "no_chosen_move", "wrong_chosen_action", "damage_before_move", "unattributed_damage",
    "missing_damage", "unexpected_immunity", "missing_immunity", "unexpected_damage",
    "enemy_never_moved", "no_return", "timeout", "nonmonotonic", "contradictory_controller",
    "valid_master", "initial_trainer", "live_link", "live_double", "live_route_change"
};
static bool named(const char *actual, const char *expected) { return strcmp(actual, expected) == 0; }
int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    const char *name = argv[1];
    bool known = false;
    for (unsigned i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i)
        if (named(name, cases[i])) known = true;
    if (!known) return 2;
    bool immune = named(name, "valid_immune") || named(name, "missing_immunity")
        || named(name, "unexpected_damage");
    bool success = named(name, "valid_hit") || named(name, "valid_immune")
        || named(name, "brief_return") || named(name, "valid_master");
    struct P05TurnSample s = {
        .species = {1, 1}, .moves = {33, 150}, .abilities = {312, 0},
        .hp = {1000, 1000}, .pp = {35, 40}, .types = {{11, 11}, {7, 7}},
        .count = 2, .action_ready = true,
    };
    if (named(name, "invalid_initial")) s.moves[0] = 0;
    if (named(name, "valid_master") || named(name, "live_route_change")) s.battle_flags = 4;
    if (named(name, "initial_trainer")) s.battle_flags = 8;
    struct P05TurnObserver observer;
    p05_turn_init(&observer, &s, !immune, 12);
    for (uint32_t tick = 1; tick <= 13 && observer.state == P05_TURN_RUNNING; ++tick) {
        s.frame = tick;
        s.action_ready = tick == 1 || tick >= 8;
        s.move_ready = tick == 2;
        s.chosen_move = tick >= 2 ? 33 : 0;
        s.chosen_action = 0;
        s.pp[0] = tick >= 4 ? 34 : 35;
        s.pp[1] = tick >= 6 ? 39 : 40;
        s.attacker = tick >= 6 ? 1 : 0;
        s.current_move = tick >= 6 ? 150 : 33;
        s.hp[1] = tick >= 5 && !immune ? 980 : 1000;
        s.result_flags = tick == 5 && immune ? 8 : 0;
        if (named(name, "brief_return") && tick == 9) s.action_ready = false;
        if (named(name, "warning") && tick == 5) s.warnings = 1;
        if (named(name, "live_link") && tick == 5) s.battle_flags = 2;
        if (named(name, "live_double") && tick == 5) s.battle_flags = 1;
        if (named(name, "live_route_change") && tick == 5) s.battle_flags = 0;
        if (named(name, "battle_exit") && tick == 5) s.outcome = 1;
        if (named(name, "battler_count") && tick == 5) s.count = 4;
        if (named(name, "absent") && tick == 5) s.absent = 2;
        if (named(name, "wrong_species") && tick == 5) s.species[1] = 2;
        if (named(name, "wrong_move") && tick == 5) s.moves[0] = 10;
        if (named(name, "wrong_ability") && tick == 5) s.abilities[0] = 0;
        if (named(name, "wrong_type") && tick == 5) s.types[1][0] = 0;
        if (named(name, "pp_refill") && tick == 5) s.pp[0] = 35;
        if (named(name, "two_player_turns") && tick == 5) s.pp[0] = 33;
        if (named(name, "two_enemy_turns") && tick == 7) s.pp[1] = 38;
        if (named(name, "faint") && tick == 5) s.hp[1] = 0;
        if (named(name, "healing") && tick == 6) s.hp[1] = 1000;
        if (named(name, "player_damaged") && tick == 5) s.hp[0] = 999;
        if (named(name, "no_action_selection") && tick == 1) s.action_ready = false;
        if (named(name, "no_move_selection")) s.move_ready = false;
        if (named(name, "no_chosen_move")) s.chosen_move = 0;
        if (named(name, "wrong_chosen_action")) s.chosen_action = 1;
        if (named(name, "damage_before_move") && tick == 3) s.hp[1] = 980;
        if (named(name, "unattributed_damage") && tick == 5) s.current_move = 150;
        if (named(name, "missing_damage")) s.hp[1] = 1000;
        if (named(name, "unexpected_immunity") && tick == 5) s.result_flags = 8;
        if (named(name, "missing_immunity")) s.result_flags = 0;
        if (named(name, "unexpected_damage") && tick >= 5) s.hp[1] = 980;
        if (named(name, "enemy_never_moved")) s.pp[1] = 40;
        if (named(name, "no_return") && tick >= 8) s.action_ready = false;
        if (named(name, "timeout") && tick == 3) s.frame = 13;
        if (named(name, "nonmonotonic") && tick == 3) s.frame = 2;
        if (named(name, "contradictory_controller") && tick == 2) s.action_ready = true;
        (void)p05_turn_observe(&observer, &s);
    }
    enum P05TurnState expected = success ? P05_TURN_PASS : P05_TURN_FAIL;
    if (observer.state != expected) {
        fprintf(stderr, "%s: state=%d expected=%d\n", name, observer.state, expected);
        return 1;
    }
    if (named(name, "brief_return") && observer.returned_frame != 10) return 1;
    printf("observer-fixture %s: OK (%s)\n", name,
           observer.error ? observer.error : "synthetic trace accepted");
    return 0;
}
