#ifndef VEGA_REWARD_ENCOUNTERS_V2_H
#define VEGA_REWARD_ENCOUNTERS_V2_H

#include <stdint.h>

#define VEGA_REWARD_ENCOUNTERS_V2_ABI_VERSION 0x52453231u /* "RE21" */
#define VEGA_REWARD_ENCOUNTER_TIER_COUNT 4u
#define VEGA_REWARD_ENCOUNTER_POOL_SIZE 6u
#define VEGA_REWARD_ENCOUNTER_ENTRY_COUNT 24u
#define VEGA_REWARD_ENCOUNTER_DIALOGUE_COUNT 56u
#define VEGA_REWARD_ENCOUNTER_SOURCE_COUNT 10u
#define VEGA_REWARD_ENCOUNTER_GENERATOR_VERSION 2u
#define VEGA_REWARD_ENCOUNTER_VOLATILE_ADDRESS 0x0203F110u
#define VEGA_REWARD_ENCOUNTER_VOLATILE_SIZE 256u

typedef enum VegaRewardEncounterTier {
    VEGA_REWARD_TIER_RANDOM = 0,
    VEGA_REWARD_TIER_HABITAT = 1,
    VEGA_REWARD_TIER_TYPE = 2,
    VEGA_REWARD_TIER_RARE = 3
} VegaRewardEncounterTier;

typedef enum VegaRewardPayment {
    VEGA_REWARD_PAYMENT_TYPED_CREDIT = 0,
    VEGA_REWARD_PAYMENT_BP_DIRECT = 1,
    VEGA_REWARD_PAYMENT_CANCEL = 2
} VegaRewardPayment;

typedef enum VegaRewardEncounterResult {
    VEGA_REWARD_OK = 0,
    VEGA_REWARD_EFFECTLESS = 1,
    VEGA_REWARD_CANCELLED = 2,
    VEGA_REWARD_LOCKED = 3,
    VEGA_REWARD_CAPACITY_FULL = 4,
    VEGA_REWARD_PENDING_EXISTS = 5,
    VEGA_REWARD_NO_PENDING = 6,
    VEGA_REWARD_INSUFFICIENT = 7,
    VEGA_REWARD_PERSIST_FAILED = 8,
    VEGA_REWARD_BUSY = 9,
    VEGA_REWARD_INVALID = 10,
    VEGA_REWARD_FACTORY_ACTIVE = 11,
    VEGA_REWARD_ENGINE_REJECTED = 12,
    VEGA_REWARD_CREDIT_FULL = 13
} VegaRewardEncounterResult;

uint32_t RewardEncountersV2_Probe(uint32_t query);
uint16_t RewardEncountersV2_Purchase(uint16_t tier, uint16_t payment);
uint16_t RewardEncounterPurchaseWithBp(uint16_t tier);
uint16_t RewardEncountersV2_PurchaseVoucher(uint16_t tier);
uint16_t RewardEncountersV2_StartPendingBattle(void);
uint16_t RewardEncounterCompleteNormalCapture(void);
uint16_t RewardEncountersV2_FieldScientist(void);
void RewardEncountersV2_EndWildBattleCommitInternal(void);
void RewardEncountersV2_EndWildBattleAdapter(void);

/* Exact-ROM smoke entrypoints.  They execute the production transaction code
 * with flash and engine services replaced only at the final I/O boundary. */
uint16_t RewardEncountersV2_TestInitialize(void);
uint16_t RewardEncountersV2_TestResetVolatile(void);
uint16_t RewardEncountersV2_TestSetBalances(uint16_t tier,
                                            uint16_t credit,
                                            uint16_t battle_points);
uint16_t RewardEncountersV2_TestSetCapacity(uint16_t mode);
uint16_t RewardEncountersV2_TestSetPersistenceFault(uint16_t enabled);
uint16_t RewardEncountersV2_TestSetCaughtMask(uint32_t mask);
uint16_t RewardEncountersV2_TestGetCredit(uint16_t tier);
uint16_t RewardEncountersV2_TestGetBattlePoints(void);
uint32_t RewardEncountersV2_TestGetPendingHash(void);
uint32_t RewardEncountersV2_TestGetGeneration(void);
uint16_t RewardEncountersV2_TestGetPendingField(uint16_t field);
uint16_t RewardEncountersV2_TestSimulateOutcome(uint16_t outcome,
                                                uint16_t mutate_side_effects);
uint16_t RewardEncountersV2_TestCreditActivity(uint16_t activity,
                                               uint16_t newly_caught,
                                               uint32_t source_token);
uint32_t RewardEncountersV2_TestGetSideEffectHash(void);
uint32_t RewardEncountersV2_TestGetCaughtMask(void);

#endif /* VEGA_REWARD_ENCOUNTERS_V2_H */
