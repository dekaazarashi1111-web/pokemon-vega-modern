#include "pr16_learnset_owner.h"

uint8_t Pr16ResolveLearnsetOwner(const uint8_t *policies, uint16_t policy_count,
                               uint16_t species, uint8_t consumer,
                               uint16_t *owner)
{
    uint8_t policy;
    if (owner == 0)
        return PR16_OWNER_INVALID;
    *owner = PR16_LEARNSET_NO_OWNER;
    if (policies == 0 || policy_count != PR16_LEARNSET_SPECIES_COUNT ||
        species >= policy_count || consumer >= PR16_CONSUMER_COUNT)
        return PR16_OWNER_INVALID;
    policy = policies[species];
    if (policy < PR16_POLICY_EXPLICIT_OWNER || policy > PR16_POLICY_MEGA)
        return PR16_OWNER_INVALID;
    /* base種へ戻さない。Own Tempo/Eternalも独立した当該ownerを保持する。 */
    *owner = species;
    if (policy >= PR16_POLICY_BATTLE_COPY)
        return PR16_OWNER_CARRY_EXISTING;
    if (policy >= PR16_POLICY_INTERNAL)
        return PR16_OWNER_PRESERVE_IDENTITY;
    if (consumer == PR16_CONSUMER_FORM_CHANGE ||
        consumer == PR16_CONSUMER_PRE_EVOLUTION_CARRY)
        return PR16_OWNER_CONDITION_REQUIRED;
    return PR16_OWNER_PREPARED_LOOKUP;
}
