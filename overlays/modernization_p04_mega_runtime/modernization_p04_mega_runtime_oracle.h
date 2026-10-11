#ifndef MODERNIZATION_P04_MEGA_RUNTIME_ORACLE_H
#define MODERNIZATION_P04_MEGA_RUNTIME_ORACLE_H

#include <stddef.h>
#include <stdint.h>

enum {
    P04_MEGA_EVO_NONE = 0,
    P04_MEGA_EVO_METHOD = 0xFE,
    P04_MEGA_VARIANT_STANDARD = 0,
    P04_MEGA_SPECIES_NONE = 0
};

typedef struct P04MegaEvolutionEntry {
    uint16_t method;
    uint16_t parameter;
    uint16_t target_species;
    uint16_t variant;
} P04MegaEvolutionEntry;

typedef enum P04MegaBoundary {
    P04_MEGA_BOUNDARY_SWITCH = 0,
    P04_MEGA_BOUNDARY_FAINT = 1,
    P04_MEGA_BOUNDARY_BATTLE_END = 2,
    P04_MEGA_BOUNDARY_INTERRUPT = 3,
    P04_MEGA_BOUNDARY_SAVE = 4
} P04MegaBoundary;

typedef enum P04MegaBattleMode {
    P04_MEGA_MODE_NORMAL = 0,
    P04_MEGA_MODE_FRONTIER = 1,
    P04_MEGA_MODE_LINK = 2,
    P04_MEGA_MODE_BRAWL = 3
} P04MegaBattleMode;

typedef struct P04MegaUsageState {
    int bank_done;
    int partner_done;
} P04MegaUsageState;

int P04MegaRuntime_ProjectPolicyAllows(
    int configured_mega_mode,
    int side_used);

int P04MegaRuntime_ProjectPolicyMark(
    int configured_mega_mode,
    int *side_used);

int P04MegaRuntime_KeystoneEnabled(
    P04MegaBattleMode mode,
    int owns_mega_ring);

int P04MegaRuntime_UpstreamOwnerAlreadyUsed(
    int bank_done,
    int partner_done,
    int separate_owner);

P04MegaUsageState P04MegaRuntime_UpstreamMark(
    P04MegaBattleMode mode,
    P04MegaUsageState state,
    int separate_owner);

uint16_t P04MegaRuntime_Resolve(
    const P04MegaEvolutionEntry *entries,
    size_t entry_count,
    uint16_t held_item,
    int project_policy_allowed,
    int has_keystone,
    int owner_already_used_mega);

uint16_t P04MegaRuntime_Revert(
    const P04MegaEvolutionEntry *entries,
    size_t entry_count);

uint16_t P04MegaRuntime_NormalizeBoundary(
    uint16_t current_species,
    const P04MegaEvolutionEntry *entries,
    size_t entry_count,
    P04MegaBoundary boundary);

#endif
