#ifndef VEGA_RESEARCH_ECONOMY_V1_H
#define VEGA_RESEARCH_ECONOMY_V1_H

#include <stdint.h>

#define RESEARCH_ECONOMY_ABI_VERSION 0x52453131u /* "RE11" */
#define RESEARCH_ECONOMY_LEDGER_ADDRESS 0x0203D000u
#define RESEARCH_ECONOMY_LEDGER_SIZE 0x800u
#define RESEARCH_ECONOMY_OWNER_OFFSET 0x73Fu
#define RESEARCH_ECONOMY_OWNER_SIZE 64u
#define RESEARCH_ECONOMY_VOLATILE_ADDRESS 0x0203F0A0u
#define RESEARCH_ECONOMY_VOLATILE_SIZE 96u
#define RESEARCH_ECONOMY_POINT_CAP 9999u

typedef enum ResearchEconomyResult {
    RESEARCH_RESULT_SUCCESS = 0,
    RESEARCH_RESULT_EFFECTLESS = 1,
    RESEARCH_RESULT_CANCELLED = 2,
    RESEARCH_RESULT_LOCKED = 3,
    RESEARCH_RESULT_DAILY_CAP = 4,
    RESEARCH_RESULT_INVALID = 5,
    RESEARCH_RESULT_PENDING = 6,
    RESEARCH_RESULT_CORRUPT_SAVE = 7,
    RESEARCH_RESULT_CAPACITY = 8,
    RESEARCH_RESULT_BUSY = 9,
    RESEARCH_RESULT_SELECTED = 10,
    RESEARCH_RESULT_PERSIST_FAILED = 13,
    RESEARCH_RESULT_INSUFFICIENT = 14,
    RESEARCH_RESULT_BAG_FULL = 15,
    RESEARCH_RESULT_ENGINE_REJECTED = 16
} ResearchEconomyResult;

typedef enum ResearchEconomyActivity {
    RESEARCH_ACTIVITY_FISHING = 0,
    RESEARCH_ACTIVITY_ECOLOGY = 1,
    RESEARCH_ACTIVITY_GAME_CORNER = 2,
    RESEARCH_ACTIVITY_BUG = 3,
    RESEARCH_ACTIVITY_MINING = 4,
    RESEARCH_ACTIVITY_PHOTO = 5,
    RESEARCH_ACTIVITY_COUNT = 6
} ResearchEconomyActivity;

uint32_t ResearchEconomy_Probe(uint32_t query);
uint32_t ResearchEconomy_SaveChecksum(const void *ledger);
uint32_t ResearchEconomy_SaveValidate(const void *ledger, uint32_t available_size);
void ResearchEconomy_SaveFinalize(void *ledger);
void ResearchEconomy_SaveInitNew(void *ledger, uint8_t first_badge_owned);
uint32_t ResearchEconomy_MigrateV1(void *ledger, uint32_t available_size);
uint8_t ResearchEconomy_SaveLoadAdapter(uint8_t save_type);
uint16_t ResearchEconomy_Recover(void);
uint16_t ResearchEconomy_GetBalance(void);
uint16_t ResearchEconomy_GetRank(void);
uint16_t ResearchEconomy_MinuteTick(void);
uint16_t ResearchEconomy_CreditActivity(uint16_t activity,
                                        uint32_t source_token,
                                        uint16_t simple_event);
uint16_t ResearchEconomy_PurchaseByIndex(uint16_t catalog_index,
                                         uint16_t confirmed);
uint16_t ResearchEconomy_ClaimNextRankReward(uint16_t confirmed);
uint16_t ResearchEconomy_OpenShop(void);
void ResearchEconomy_PostShopMenu(void);
uint16_t ResearchEconomy_PurchaseSelected(void);
uint16_t ResearchEconomy_FieldCounter(void);
uint16_t ResearchEconomy_FieldRank(void);
uint16_t ResearchEconomy_FieldBug(void);
uint16_t ResearchEconomy_FieldMining(void);
uint16_t ResearchEconomy_FieldPhoto(void);
void ResearchEconomy_PlayTimeAdapter(void);
uint8_t ResearchEconomy_TryGenerateWildMonAdapter(const void *info,
                                                   uint8_t area,
                                                   uint8_t flags);
uint16_t ResearchEconomy_GenerateFishingEncounterAdapter(const void *info,
                                                          uint8_t rod);
uint8_t ResearchEconomy_TryHiddenEncounterAdapter(void);
void ResearchEconomy_EndWildBattleAdapter(void);
void ResearchEconomy_GameCornerPayoutAdapter(uint16_t amount);

/* Exact-ROM acceptance probes.  They have no field/script route. */
uint16_t ResearchEconomy_TestInitialize(void);
uint16_t ResearchEconomy_TestSetUnlockAll(uint16_t enabled);
uint16_t ResearchEconomy_TestSetPersistenceFault(uint16_t phase);
uint16_t ResearchEconomy_TestSetBagCapacity(uint16_t available);
uint16_t ResearchEconomy_TestGetOwnerByte(uint16_t offset);
uint16_t ResearchEconomy_TestSetBalance(uint16_t balance);

#endif /* VEGA_RESEARCH_ECONOMY_V1_H */
