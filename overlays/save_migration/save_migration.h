#ifndef VEGA_SAVE_MIGRATION_H
#define VEGA_SAVE_MIGRATION_H

#include <stddef.h>
#include <stdint.h>

#define VEGA_SAVE_MAGIC 0x31534756u /* "VGS1" (little endian) */
#define VEGA_SAVE_VERSION 1u
#define VEGA_SAVE_LEDGER_SIZE 0x800u
#define VEGA_SAVE_EWRAM_ADDRESS 0x0203D000u
#define VEGA_SAVE_PARASITE_IMAGE_OFFSET 0x1F18u
#define VEGA_SAVE_TRANSACTION_SCRATCH_ADDRESS 0x0203E300u
#define VEGA_SAVE_ROLLBACK_ADDRESS 0x0203E400u
#define VEGA_NATIONAL_DEX_COUNT 1025u
#define VEGA_DEX_BYTES ((VEGA_NATIONAL_DEX_COUNT + 7u) / 8u)
#define VEGA_SPECIAL_CAPTURE_COUNT 125u
#define VEGA_SPECIAL_CAPTURE_BYTES ((VEGA_SPECIAL_CAPTURE_COUNT + 7u) / 8u)
#define VEGA_CERTIFICATION_COUNT 8u
#define VEGA_EGG_QUEUE_CAPACITY 5u
#define VEGA_BOX_MON_SIZE 80u
#define VEGA_PARTY_MON_SIZE 100u
#define VEGA_PARTY_CAPACITY 6u
#define VEGA_FACTORY_MODE_COUNT 24u
#define VEGA_MIRAGE_MODE_COUNT 8u
#define VEGA_ENCOUNTER_CREDIT_TYPE_COUNT 8u
#define VEGA_BP_CAP 9999u
#define VEGA_ARCADE_COIN_CAP 9999u
#define VEGA_ITEM_COUNT 999u
#define VEGA_ITEM_OBTAINED_BYTES ((VEGA_ITEM_COUNT + 7u) / 8u)
#define VEGA_ACQUISITION_SAVE_BYTES 240u
#define VEGA_DEX_MIGRATION_PREFIX_BYTES 3u
#define VEGA_DEX_MIGRATION_RESERVED_BYTES \
    (2u * VEGA_DEX_BYTES - VEGA_DEX_MIGRATION_PREFIX_BYTES \
     - VEGA_ACQUISITION_SAVE_BYTES)

typedef enum VegaSaveStatus {
    VEGA_SAVE_OK = 0,
    VEGA_SAVE_EMPTY_OR_LEGACY = 1,
    VEGA_SAVE_BAD_MAGIC = 2,
    VEGA_SAVE_UNSUPPORTED_VERSION = 3,
    VEGA_SAVE_BAD_SIZE = 4,
    VEGA_SAVE_BAD_CHECKSUM = 5,
    VEGA_SAVE_INVALID_ARGUMENT = 6,
    VEGA_SAVE_RANGE_ERROR = 7,
    VEGA_SAVE_NOT_ALLOWED = 8,
    VEGA_SAVE_PERSIST_FAILED = 9,
    VEGA_SAVE_ALREADY_CLAIMED = 10,
    VEGA_SAVE_QUEUE_FULL = 11,
    VEGA_SAVE_QUEUE_EMPTY = 12,
    VEGA_SAVE_PENDING_EXISTS = 13,
    VEGA_SAVE_INSUFFICIENT_CREDIT = 14,
    VEGA_SAVE_RESERVED_NONZERO = 15
} VegaSaveStatus;

typedef enum VegaRegion {
    VEGA_REGION_TOHOKU = 0,
    VEGA_REGION_KANTO = 1,
    VEGA_REGION_COUNT = 2
} VegaRegion;

typedef enum VegaEncounterProfile {
    VEGA_PROFILE_NORMAL = 0,
    VEGA_PROFILE_RESEARCH = 1
} VegaEncounterProfile;

typedef enum VegaTextSpeed {
    VEGA_TEXT_INSTANT = 0,
    VEGA_TEXT_FAST = 1,
    VEGA_TEXT_NORMAL = 2
} VegaTextSpeed;

typedef enum VegaHatchMode {
    VEGA_HATCH_NORMAL = 0,
    VEGA_HATCH_FAST = 1,
    VEGA_HATCH_SKIP = 2
} VegaHatchMode;

typedef enum VegaFactoryMarker {
    VEGA_FACTORY_OUTSIDE = 0,
    VEGA_FACTORY_SNAPSHOT_COMMITTED = 1,
    VEGA_FACTORY_BATTLE_ACTIVE = 2,
    VEGA_FACTORY_RESULT_PENDING = 3,
    VEGA_FACTORY_RESTORE_PENDING = 4
} VegaFactoryMarker;

typedef enum VegaLeagueStage {
    VEGA_LEAGUE_STAGE_I = 1,
    VEGA_LEAGUE_STAGE_II = 2
} VegaLeagueStage;

#if defined(__GNUC__)
#define VEGA_PACKED __attribute__((packed))
#else
#define VEGA_PACKED
#endif

typedef struct VEGA_PACKED VegaWarpAnchor {
    uint8_t map_group;
    uint8_t map_num;
    uint8_t warp_id;
    uint8_t valid;
    int16_t x;
    int16_t y;
} VegaWarpAnchor;

typedef struct VEGA_PACKED VegaPendingEncounter {
    uint8_t valid;
    uint8_t encounter_kind;
    uint16_t pool;
    uint16_t species;
    uint16_t form;
    uint8_t level;
    uint8_t nature;
    uint8_t ability;
    uint8_t shiny;
    uint8_t tera_type;
    uint8_t credit_kind;
    uint8_t ivs[6];
    uint32_t personality;
    uint16_t generator_version;
    uint8_t generator_fingerprint[16];
    uint32_t transaction_id;
} VegaPendingEncounter;

typedef struct VEGA_PACKED VegaFactoryState {
    uint16_t battle_points;
    uint16_t current_streak[VEGA_FACTORY_MODE_COUNT];
    uint16_t best_streak[VEGA_FACTORY_MODE_COUNT];
    uint32_t reward_claim_bits;
    uint32_t unlock_bits;
    uint32_t transaction_id;
    uint8_t marker;
    uint8_t snapshot_valid;
    uint8_t party_count;
    uint8_t reward_pending;
    uint8_t party_snapshot[VEGA_PARTY_CAPACITY][VEGA_PARTY_MON_SIZE];
} VegaFactoryState;

typedef struct VEGA_PACKED VegaMirageState {
    uint16_t current_record[VEGA_MIRAGE_MODE_COUNT];
    uint16_t best_record[VEGA_MIRAGE_MODE_COUNT];
    uint32_t reward_claim_bits;
    uint32_t item_reward_transaction_id;
} VegaMirageState;

typedef struct VEGA_PACKED VegaModernSaveData {
    uint32_t magic;
    uint16_t version;
    uint16_t struct_size;
    uint32_t checksum;
    uint32_t generation;

    uint8_t kanto_travel_unlocked;
    uint8_t kanto_visited;
    uint8_t vega_hall_of_fame;
    uint8_t first_kanto_warning_seen;
    uint8_t league_i_cleared;
    uint8_t league_ii_cleared;
    uint8_t legacy_migration_done;
    uint8_t current_region;
    uint8_t kanto_certifications;
    uint8_t research_rank;
    uint8_t rotation_state;
    uint8_t retry_state;
    uint8_t text_speed;
    uint8_t hatch_mode;
    uint8_t exp_share_enabled;
    uint8_t encounter_profile[VEGA_REGION_COUNT];

    VegaWarpAnchor heal_anchor[VEGA_REGION_COUNT];
    VegaWarpAnchor return_anchor[VEGA_REGION_COUNT];

    /* v1の後続offsetを維持し、3 byte padで取得台帳のu32 ABIを整列する。 */
    uint8_t reserved_dex_migration_prefix[VEGA_DEX_MIGRATION_PREFIX_BYTES];
    uint8_t acquisition_save_block[VEGA_ACQUISITION_SAVE_BYTES];
    uint8_t reserved_dex_migration[VEGA_DEX_MIGRATION_RESERVED_BYTES];
    uint8_t shared_special_capture[VEGA_SPECIAL_CAPTURE_BYTES];
    uint8_t raid_reward_claimed[VEGA_SPECIAL_CAPTURE_BYTES];
    uint8_t raid_retry_pending[VEGA_SPECIAL_CAPTURE_BYTES];
    uint8_t raid_in_progress[VEGA_SPECIAL_CAPTURE_BYTES];
    uint8_t raid_bonus_tier[VEGA_SPECIAL_CAPTURE_COUNT];

    uint8_t egg_queue_count;
    uint8_t egg_queue_head;
    uint8_t egg_queue[VEGA_EGG_QUEUE_CAPACITY][VEGA_BOX_MON_SIZE];

    VegaFactoryState factory;
    VegaMirageState mirage;
    uint16_t encounter_credits[VEGA_ENCOUNTER_CREDIT_TYPE_COUNT];
    VegaPendingEncounter pending_encounter;
    uint8_t item_obtained_flags[VEGA_ITEM_OBTAINED_BYTES];
    uint8_t reserved[193];
} VegaModernSaveData;

#define gVegaModernSaveData ((VegaModernSaveData *)(uintptr_t)VEGA_SAVE_EWRAM_ADDRESS)
#define gVegaSaveTransactionScratch ((uint8_t *)(uintptr_t)VEGA_SAVE_TRANSACTION_SCRATCH_ADDRESS)
#define gVegaSaveRollbackData ((VegaModernSaveData *)(uintptr_t)VEGA_SAVE_ROLLBACK_ADDRESS)

typedef struct VegaLegacySignals {
    uint8_t recognized_vega_signature;
    uint8_t legacy_checksum_valid;
    uint8_t shiou_complete_flag_0824;
    uint8_t dh_complete_flag_114b;
    uint8_t hall_of_fame;
    uint8_t first_badge_owned;
    uint8_t item_obtained_flags[104];
} VegaLegacySignals;

typedef struct VegaEncounterRequest {
    uint8_t encounter_kind;
    uint8_t credit_kind;
    uint16_t cost;
    uint16_t pool;
    uint16_t species;
    uint16_t form;
    uint8_t level;
    uint8_t nature;
    uint8_t ability;
    uint8_t shiny;
    uint8_t tera_type;
    uint8_t ivs[6];
    uint32_t personality;
    uint16_t generator_version;
    uint8_t generator_fingerprint[16];
} VegaEncounterRequest;

typedef int (*VegaPersistCallback)(const VegaModernSaveData *data, size_t size, void *context);

uint32_t VegaSaveChecksum(const VegaModernSaveData *data);
void VegaSaveFinalize(VegaModernSaveData *data);
VegaSaveStatus VegaSaveValidate(const VegaModernSaveData *data, size_t available_size);
VegaSaveStatus VegaSaveLoad(VegaModernSaveData *data, size_t available_size);
void VegaSaveInitNew(VegaModernSaveData *data, uint8_t first_badge_owned);
VegaSaveStatus VegaSaveMigrateLegacy(VegaModernSaveData *data, const VegaLegacySignals *legacy);

VegaWarpAnchor VegaSaveResolveAnchor(const VegaModernSaveData *data,
                                     VegaRegion region,
                                     uint8_t use_return_anchor,
                                     VegaWarpAnchor tohoku_fallback,
                                     VegaWarpAnchor kanto_fallback);
VegaSaveStatus VegaSaveSetRegion(VegaModernSaveData *data, VegaRegion region);
VegaSaveStatus VegaSaveSetEncounterProfile(VegaModernSaveData *data,
                                           VegaRegion region,
                                           VegaEncounterProfile profile);
VegaSaveStatus VegaSaveMarkSpecialCaptured(VegaModernSaveData *data, uint16_t shared_key);
uint8_t VegaSaveIsSpecialCaptured(const VegaModernSaveData *data, uint16_t shared_key);
VegaSaveStatus VegaSaveAdvanceLeague(VegaModernSaveData *data, VegaLeagueStage stage);

VegaSaveStatus VegaEggQueuePush(VegaModernSaveData *data, const uint8_t box_mon[VEGA_BOX_MON_SIZE]);
VegaSaveStatus VegaEggQueuePop(VegaModernSaveData *data, uint8_t box_mon[VEGA_BOX_MON_SIZE]);

VegaSaveStatus VegaFactoryAddBattlePoints(VegaModernSaveData *data, uint16_t amount);
VegaSaveStatus VegaFactorySpendBattlePoints(VegaModernSaveData *data, uint16_t amount);
VegaSaveStatus VegaFactoryEnter(VegaModernSaveData *data,
                                const uint8_t party[VEGA_PARTY_CAPACITY][VEGA_PARTY_MON_SIZE],
                                uint8_t party_count,
                                VegaPersistCallback persist,
                                void *context);
VegaSaveStatus VegaFactorySetBattleActive(VegaModernSaveData *data,
                                          VegaPersistCallback persist,
                                          void *context);
VegaSaveStatus VegaFactoryRestore(VegaModernSaveData *data,
                                  uint8_t party[VEGA_PARTY_CAPACITY][VEGA_PARTY_MON_SIZE],
                                  uint8_t *party_count,
                                  VegaPersistCallback persist,
                                  void *context);
VegaSaveStatus VegaFactoryClaimReward(VegaModernSaveData *data,
                                      uint8_t reward_index,
                                      uint16_t bp_amount,
                                      VegaPersistCallback persist,
                                      void *context);

VegaSaveStatus VegaSavePurchaseEncounter(VegaModernSaveData *data,
                                         const VegaEncounterRequest *request,
                                         VegaPersistCallback persist,
                                         void *context);
VegaSaveStatus VegaSaveCompleteCapture(VegaModernSaveData *data,
                                       uint16_t shared_key,
                                       VegaPersistCallback persist,
                                       void *context);

VegaSaveStatus VegaRaidClaimReward(VegaModernSaveData *data,
                                   uint16_t shared_key,
                                   VegaPersistCallback persist,
                                   void *context);
VegaSaveStatus VegaRaidSetRetry(VegaModernSaveData *data,
                                uint16_t shared_key,
                                uint8_t pending,
                                VegaPersistCallback persist,
                                void *context);
VegaSaveStatus VegaRaidSetBonusTier(VegaModernSaveData *data,
                                    uint16_t shared_key,
                                    uint8_t tier,
                                    VegaPersistCallback persist,
                                    void *context);

#endif
