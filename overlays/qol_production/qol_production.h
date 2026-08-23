#ifndef VEGA_QOL_PRODUCTION_H
#define VEGA_QOL_PRODUCTION_H

#include <stdint.h>

#define VEGA_QOL_PRODUCTION_MAGIC 0x51504F4Cu /* "QPOL" */
#define VEGA_QOL_FEATURE_COUNT 35u
#define VEGA_QOL_BOX_COUNT 14u
#define VEGA_QOL_BOX_CAPACITY 30u
#define VEGA_QOL_BOX_MON_SIZE 80u

typedef enum VegaQolFeature {
    VEGA_QOL_TEXT_SPEED_INSTANT = 0,
    VEGA_QOL_FAST_MOVEMENT,
    VEGA_QOL_IV_EV_JUDGE,
    VEGA_QOL_PC_SEARCH_MULTISELECT,
    VEGA_QOL_EXP_SHARE,
    VEGA_QOL_EVERSTONE_SUPPLY,
    VEGA_QOL_EGG_PC_TRANSFER,
    VEGA_QOL_EGG_QUEUE_5,
    VEGA_QOL_FREE_MOVE_RELEARN,
    VEGA_QOL_PC_MOVE_EDIT,
    VEGA_QOL_EXP_CANDY_XS_S,
    VEGA_QOL_EXP_CANDY_M_ONCE,
    VEGA_QOL_ABILITY_CAPSULE_MINTS,
    VEGA_QOL_EV_RESET_ALL,
    VEGA_QOL_FIELD_PC,
    VEGA_QOL_PC_HELD_ITEM_BULK,
    VEGA_QOL_AUTO_BATTLE,
    VEGA_QOL_DESTINY_KNOT,
    VEGA_QOL_EGG_BASKET,
    VEGA_QOL_OVAL_CHARM,
    VEGA_QOL_POWER_ITEMS,
    VEGA_QOL_EXP_CANDY_M_REPEAT,
    VEGA_QOL_EXP_CANDY_L_SILVER_CAP,
    VEGA_QOL_ABILITY_PATCH_ALL_MINTS,
    VEGA_QOL_EV_RESET_ITEMS,
    VEGA_QOL_STANDARD_TRAINING_SHOP,
    VEGA_QOL_EXP_CANDY_XL_ONCE,
    VEGA_QOL_RESEARCH_PROFILE,
    VEGA_QOL_TM_REUSE_LICENSE,
    VEGA_QOL_HIDDEN_ABILITY_DEXNAV,
    VEGA_QOL_COMPETITIVE_ITEM_SUPPLY,
    VEGA_QOL_HIGH_DIFFICULTY_RAID,
    VEGA_QOL_TERA_DYNAMAX_STORY,
    VEGA_QOL_BOOST_ENERGY_UB_PARADOX,
    VEGA_QOL_EXP_CANDY_XL_GOLD_CAP
} VegaQolFeature;

typedef enum VegaQolStatus {
    VEGA_QOL_OK = 0,
    VEGA_QOL_LOCKED = 1,
    VEGA_QOL_CANCELLED = 2,
    VEGA_QOL_INVALID_ARGUMENT = 3,
    VEGA_QOL_EMPTY_SELECTION = 4,
    VEGA_QOL_CAPACITY = 5,
    VEGA_QOL_FORBIDDEN_MON = 6,
    VEGA_QOL_FORBIDDEN_ITEM = 7,
    VEGA_QOL_EFFECTLESS = 8,
    VEGA_QOL_MOVE_NOT_IN_POOL = 9,
    VEGA_QOL_CONTEXT_FORBIDDEN = 10,
    VEGA_QOL_PERSIST_FAILED = 11,
    VEGA_QOL_CORRUPT_SAVE = 12,
    VEGA_QOL_CONFIRM_REQUIRED = 13,
    VEGA_QOL_INSUFFICIENT_CURRENCY = 14,
    VEGA_QOL_ALREADY_CLAIMED = 15
} VegaQolStatus;

typedef enum VegaQolService {
    VEGA_QOL_SERVICE_PROBE = 0,
    VEGA_QOL_SERVICE_FEATURE_UNLOCKED = 1,
    VEGA_QOL_SERVICE_PC_CLEAR_SELECTION = 2,
    VEGA_QOL_SERVICE_PC_TOGGLE_SELECTION = 3,
    VEGA_QOL_SERVICE_PC_SEARCH = 4,
    VEGA_QOL_SERVICE_PC_MOVE = 5,
    VEGA_QOL_SERVICE_PC_RELEASE = 6,
    VEGA_QOL_SERVICE_PC_TAKE_ITEMS = 7,
    VEGA_QOL_SERVICE_PC_RELEARN = 8,
    VEGA_QOL_SERVICE_FIELD_PC_ALLOWED = 9,
    VEGA_QOL_SERVICE_EGG_QUEUE_CLAIM = 10,
    VEGA_QOL_SERVICE_AUTO_BATTLE_ALLOWED = 11,
    VEGA_QOL_SERVICE_SET_TEXT_SPEED = 12,
    VEGA_QOL_SERVICE_SET_EXP_SHARE = 13,
    VEGA_QOL_SERVICE_SET_HATCH_MODE = 14,
    VEGA_QOL_SERVICE_SET_RESEARCH_PROFILE = 15,
    VEGA_QOL_SERVICE_SELECTION_COUNT = 16,
    VEGA_QOL_SERVICE_HYPER_TRAIN_PARTY = 17,
    VEGA_QOL_SERVICE_EV_RESET_ALL_PARTY = 18,
    VEGA_QOL_SERVICE_SET_DAYCARE_QUEST = 19,
    VEGA_QOL_SERVICE_SET_EGG_BASKET = 20,
    VEGA_QOL_SERVICE_CLAIM_ONE_TIME_REWARD = 21,
    VEGA_QOL_SERVICE_PURCHASE_SUPPLY = 22,
    VEGA_QOL_SERVICE_SUPPLY_AVAILABLE = 23,
    VEGA_QOL_SERVICE_CONFIGURE_HIGH_RAID = 24,
    VEGA_QOL_SERVICE_CONFIGURE_LOW_RAID = 25
} VegaQolService;

typedef enum VegaQolOneTimeReward {
    VEGA_QOL_REWARD_EVERSTONE = 0,
    VEGA_QOL_REWARD_EXP_CANDY_M = 1,
    VEGA_QOL_REWARD_POWER_SET = 2,
    VEGA_QOL_REWARD_EXP_CANDY_XL = 3,
    VEGA_QOL_REWARD_DAYCARE_SET = 4
} VegaQolOneTimeReward;

typedef enum VegaQolSearchMode {
    VEGA_QOL_SEARCH_NAME = 1u << 0,
    VEGA_QOL_SEARCH_TYPE = 1u << 1,
    VEGA_QOL_SEARCH_ABILITY = 1u << 2
} VegaQolSearchMode;

typedef struct VegaQolSearchFilter {
    uint8_t modes;
    uint8_t type_id;
    uint16_t ability_id;
    uint8_t nickname[11];
} VegaQolSearchFilter;

uint32_t VegaQolProduction_Probe(uint32_t selector);
uint8_t VegaQolProduction_FeatureUnlocked(uint16_t feature);
uint32_t VegaQolProduction_Dispatch(uint16_t service, uint32_t a,
                                    uint32_t b, uint32_t c);

void VegaQolProduction_ReadKeysAdapter(void);
uint8_t VegaQolProduction_GetTextSpeedDelay(void);
uint8_t VegaQolProduction_RunTextPrintersForInstantText(void);
uint8_t VegaQolProduction_TestInjectPersistenceFault(uint8_t mode);
void VegaQolProduction_PrintSkillsPageAdapter(void);
void VegaQolProduction_SummaryInputAdapter(uint8_t task_id);
void VegaQolProduction_DoNamingScreenAdapter(
    uint8_t template_num, uint8_t *destination, uint16_t species,
    uint16_t gender, uint32_t personality, void (*return_callback)(void));
uint8_t VegaQolProduction_PssHandleInputAdapter(void);
void VegaQolProduction_HandleInputChooseActionAdapter(void);
void VegaQolProduction_HandleInputChooseMoveAdapter(void);
const uint8_t *VegaQolProduction_ConfigureTrainerBattleAdapter(
    const uint8_t *data);
uint8_t VegaQolProduction_ConfigureHighRaid(void);
uint8_t VegaQolProduction_ConfigureLowRaid(void);
void VegaQolProduction_TriggerPendingDaycareEggAdapter(void *daycare);
uint8_t VegaQolProduction_IsEggPendingAdapter(void *daycare);
void VegaQolProduction_GiveEggFromDaycareAdapter(void *daycare);
uint8_t VegaQolProduction_GiveEggFromDaycareSpecial(void);
uint8_t VegaQolProduction_CalculatePartyCountForDaycare(void);
uint8_t VegaQolProduction_TryHiddenEncounterAdapter(void);
uint8_t VegaQolProduction_ShouldEggHatchAdapter(void);
uint8_t VegaQolProduction_SaveLoadAdapter(uint8_t save_type);
uint8_t VegaQolProduction_TrySavingDataAdapter(uint8_t save_type);
uint8_t VegaQolProduction_FlagSetAdapter(uint16_t flag);
uint8_t VegaQolProduction_FlagClearAdapter(uint16_t flag);
uint8_t VegaQolProduction_StartMenuPanel(void);
uint8_t VegaQolProduction_BpShopUnlockSatisfied(uint8_t kind);
uint8_t VegaQolProduction_ClaimOneTimeReward(uint8_t reward);
uint8_t VegaQolProduction_PurchaseSupply(uint8_t catalog_index);
uint16_t VegaQolProduction_BpShopPurchaseByIndex(uint16_t catalog_index);
uint16_t VegaQolProduction_OpenSupplyShop(void);
void VegaQolProduction_PostSupplyShop(void);

uint32_t VegaQolProduction_SubtractEggSteps(uint32_t steps, void *mon);
void VegaQolProduction_TryDecrementEggSteps(void *daycare, uint8_t ignore_id);
uint8_t VegaQolProduction_ShouldSkipHatchNickname(void);
void VegaQolProduction_EggHatchPresentationAdapter(void);
uint8_t VegaQolProduction_ModifyBreedingScore(uint8_t score);

uint8_t VegaQolProduction_IsReusableTm(uint16_t item);
uint8_t VegaQolProduction_TmHmSymbolAdapter(uint16_t item);
uint8_t VegaQolProduction_TmSellableAdapter(uint16_t item);
uint8_t VegaQolProduction_TmBagQuantityAdapter(uint16_t item);
uint8_t VegaQolProduction_ApplyExpCandyQuantityAdapter(
    void *mon, uint16_t item, uint8_t choice, uint16_t available,
    void *result);
void VegaQolProduction_FieldUseExpCandyAdapter(uint8_t task_id);
void VegaQolProduction_FieldUseCommonQuantityAdapter(uint8_t task_id);
uint16_t VegaQolProduction_MonTryLearningNewMoveAdapter(
    void *mon, uint8_t first_move);
void VegaQolProduction_PartyMenuTryEvolutionAdapter(uint8_t task_id);
uint8_t VegaQolProduction_TryGenerateWildMonAdapter(
    const void *info, uint8_t area, uint8_t flags);
uint16_t VegaQolProduction_GenerateFishingEncounterAdapter(
    const void *info, uint8_t rod);
void VegaQolProduction_DoStandardWildBattleAdapter(void);
void VegaQolProduction_ClearBattleAutoState(void);

#endif
