#include "modernization_p04_mega_runtime_oracle.h"

/*
 * 固定CFRU-JPのmega.cをforkせず、host testが同じtable semanticsを独立に
 * 検査するためのoracle。ROMへ注入するpayloadではない。
 */
int P04MegaRuntime_ProjectPolicyAllows(
    int configured_mega_mode,
    int side_used)
{
    return configured_mega_mode && !side_used;
}

int P04MegaRuntime_ProjectPolicyMark(
    int configured_mega_mode,
    int *side_used)
{
    if (side_used == NULL
            || !P04MegaRuntime_ProjectPolicyAllows(
                configured_mega_mode, *side_used))
        return 0;
    *side_used = 1;
    return 1;
}

int P04MegaRuntime_KeystoneEnabled(
    P04MegaBattleMode mode,
    int owns_mega_ring)
{
    if (mode == P04_MEGA_MODE_FRONTIER || mode == P04_MEGA_MODE_LINK)
        return 1;
    if (mode == P04_MEGA_MODE_NORMAL || mode == P04_MEGA_MODE_BRAWL)
        return owns_mega_ring != 0;
    return 0;
}

int P04MegaRuntime_UpstreamOwnerAlreadyUsed(
    int bank_done,
    int partner_done,
    int separate_owner)
{
    return separate_owner ? bank_done : bank_done || partner_done;
}

P04MegaUsageState P04MegaRuntime_UpstreamMark(
    P04MegaBattleMode mode,
    P04MegaUsageState state,
    int separate_owner)
{
    if (mode == P04_MEGA_MODE_BRAWL)
        return state;
    if (mode != P04_MEGA_MODE_NORMAL
            && mode != P04_MEGA_MODE_FRONTIER
            && mode != P04_MEGA_MODE_LINK)
        return state;
    state.bank_done = 1;
    if (!separate_owner)
        state.partner_done = 1;
    return state;
}

uint16_t P04MegaRuntime_Resolve(
    const P04MegaEvolutionEntry *entries,
    size_t entry_count,
    uint16_t held_item,
    int project_policy_allowed,
    int has_keystone,
    int owner_already_used_mega)
{
    size_t index;
    if (entries == NULL || !project_policy_allowed)
        return P04_MEGA_SPECIES_NONE;
    if (!has_keystone)
        return P04_MEGA_SPECIES_NONE;
    for (index = 0; index < entry_count; ++index) {
        const P04MegaEvolutionEntry *entry = &entries[index];
        if (entry->method == P04_MEGA_EVO_NONE)
            break;
        if (entry->method == P04_MEGA_EVO_METHOD
                && entry->parameter != 0
                && entry->variant == P04_MEGA_VARIANT_STANDARD
                && entry->parameter == held_item) {
            if (owner_already_used_mega)
                return P04_MEGA_SPECIES_NONE;
            return entry->target_species;
        }
    }
    return P04_MEGA_SPECIES_NONE;
}

uint16_t P04MegaRuntime_Revert(
    const P04MegaEvolutionEntry *entries,
    size_t entry_count)
{
    size_t index;
    if (entries == NULL)
        return P04_MEGA_SPECIES_NONE;
    for (index = 0; index < entry_count; ++index) {
        const P04MegaEvolutionEntry *entry = &entries[index];
        if (entry->method == P04_MEGA_EVO_NONE)
            break;
        if (entry->method == P04_MEGA_EVO_METHOD && entry->parameter == 0)
            return entry->target_species;
    }
    return P04_MEGA_SPECIES_NONE;
}

uint16_t P04MegaRuntime_NormalizeBoundary(
    uint16_t current_species,
    const P04MegaEvolutionEntry *entries,
    size_t entry_count,
    P04MegaBoundary boundary)
{
    uint16_t reverted;
    if (boundary == P04_MEGA_BOUNDARY_SWITCH)
        return current_species;
    reverted = P04MegaRuntime_Revert(entries, entry_count);
    return reverted == P04_MEGA_SPECIES_NONE ? current_species : reverted;
}
