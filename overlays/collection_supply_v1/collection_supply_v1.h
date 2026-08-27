#ifndef VEGA_COLLECTION_SUPPLY_V1_H
#define VEGA_COLLECTION_SUPPLY_V1_H

#include <stddef.h>
#include <stdint.h>

#define COLLECTION_SUPPLY_ABI_VERSION 0x43535631u /* "CSV1" */
#define COLLECTION_SUPPLY_OWNER_ADDRESS 0x0203D900u
#define COLLECTION_SUPPLY_OWNER_SIZE 512u
#define COLLECTION_SUPPLY_VOLATILE_ADDRESS 0x0203F720u
#define COLLECTION_SUPPLY_VOLATILE_SIZE 224u

typedef enum CollectionSupplyResult {
    COLLECTION_RESULT_SUCCESS = 0,
    COLLECTION_RESULT_EFFECTLESS = 1,
    COLLECTION_RESULT_CANCELLED = 2,
    COLLECTION_RESULT_LOCKED = 3,
    COLLECTION_RESULT_INVALID = 5,
    COLLECTION_RESULT_BUSY = 9,
    COLLECTION_RESULT_INSUFFICIENT = 14,
    COLLECTION_RESULT_BAG_FULL = 15,
    COLLECTION_RESULT_ENGINE_REJECTED = 16,
    COLLECTION_RESULT_PERSIST_FAILED = 17,
    COLLECTION_RESULT_STORAGE_FULL = 18,
    COLLECTION_RESULT_FORM_REQUEST = 20,
    COLLECTION_RESULT_GMAX_REQUEST = 21,
    COLLECTION_RESULT_RAID_REQUEST = 22,
    COLLECTION_RESULT_BATTLE_STARTED = 23
} CollectionSupplyResult;

typedef struct __attribute__((packed)) CollectionSupplyOwnerV1 {
    uint32_t magic;
    uint32_t magic_inverse;
    uint16_t version;
    uint16_t struct_size;
    uint32_t crc32;
    uint32_t generation;
    uint8_t pending_phase;
    uint8_t pending_kind;
    uint8_t pending_currency;
    uint8_t pending_claim_kind;
    uint16_t pending_key;
    uint16_t pending_item;
    uint16_t pending_quantity;
    uint32_t pending_balance_before;
    uint16_t pending_bag_before;
    uint16_t pending_species;
    uint32_t pending_personality;
    uint16_t pending_host;
    uint16_t pending_entry;
    uint32_t transaction_id;
    uint16_t rotation[14];
    uint16_t raid_first_clear_bits;
    uint8_t form_gift_bits;
    uint8_t raid_form_capture_bits;
    uint8_t pending_reward_host;
    uint8_t flags;
    uint8_t reserved[428];
} CollectionSupplyOwnerV1;

typedef struct __attribute__((packed)) CollectionSupplyVolatileState {
    uint32_t magic;
    uint32_t magic_inverse;
    uint16_t last_result;
    uint16_t pending_index;
    uint16_t active_entry;
    uint16_t active_species;
    uint16_t previous_species;
    uint8_t host;
    uint8_t menu_mode;
    uint8_t service;
    uint8_t page;
    uint8_t window_id;
    uint8_t raid_active;
    uint8_t active_gmax;
    uint8_t restore_pending;
    uint8_t restore_frames;
    uint8_t test_mode;
    uint8_t test_fault;
    uint8_t reserved0;
    uint32_t active_personality;
    uint8_t balance_text[24];
    uint8_t row_text[24];
    uint32_t test_money;
    uint16_t test_bp;
    uint16_t test_research;
    uint16_t test_bag_item;
    uint16_t test_bag_quantity;
    uint16_t test_bag_capacity;
    uint16_t test_gift_species;
    uint32_t test_gift_personality;
    uint32_t test_rng;
    uint8_t reserved[118];
} CollectionSupplyVolatileState;

_Static_assert(sizeof(CollectionSupplyOwnerV1) == COLLECTION_SUPPLY_OWNER_SIZE,
               "Collection Supply owner ABI differs");
_Static_assert(offsetof(CollectionSupplyOwnerV1, crc32) == 12u,
               "Collection Supply CRC offset differs");
_Static_assert(sizeof(CollectionSupplyVolatileState)
                   == COLLECTION_SUPPLY_VOLATILE_SIZE,
               "Collection Supply volatile ABI differs");

#define gCollectionSupplyOwner \
    ((volatile CollectionSupplyOwnerV1 *)(uintptr_t) \
        COLLECTION_SUPPLY_OWNER_ADDRESS)
#define gCollectionSupplyVolatileState \
    ((volatile CollectionSupplyVolatileState *)(uintptr_t) \
        COLLECTION_SUPPLY_VOLATILE_ADDRESS)

uint32_t CollectionSupply_Probe(uint32_t query);
uint16_t CollectionSupply_FieldHost(void);
uint16_t CollectionSupply_ApplySelectedForm(void);
uint16_t CollectionSupply_ApplySelectedGmax(void);
uint16_t CollectionSupply_StartSelectedRaid(void);
uint8_t CollectionSupply_SaveLoadAdapter(uint8_t save_type);
void CollectionSupply_ReadKeysAdapter(void);
uint8_t CollectionSupply_TryGenerateWildMonAdapter(
    const void *info, uint8_t area, uint8_t flags);
void CollectionSupply_EndWildBattleAdapter(void);

/* Exact-ROM acceptance probes.  No production field script calls these. */
uint16_t CollectionSupply_TestInitialize(void);
uint16_t CollectionSupply_TestPurchase(uint16_t item_index);
uint16_t CollectionSupply_TestApplyForm(uint16_t form_index, uint16_t slot);
uint16_t CollectionSupply_TestToggleGmax(uint16_t slot);
uint16_t CollectionSupply_TestPrepareRaid(uint16_t host);
uint16_t CollectionSupply_TestCompleteRaid(uint16_t caught);
uint16_t CollectionSupply_TestGift(uint16_t gift_index);
uint16_t CollectionSupply_TestClaimRelic(uint16_t item_index);
uint32_t CollectionSupply_TestOwnerField(uint16_t field);
uint32_t CollectionSupply_TestBalance(uint16_t currency);
uint16_t CollectionSupply_TestSectorRoundTrip(void);
uint16_t CollectionSupply_TestSetFault(uint16_t fault);
uint16_t CollectionSupply_TestSetBalances(uint32_t money, uint16_t bp,
                                          uint16_t research);
uint16_t CollectionSupply_TestSetBag(uint16_t item, uint16_t quantity,
                                     uint16_t capacity);
uint16_t CollectionSupply_TestSeedParty(uint16_t species, uint16_t slot,
                                        uint16_t gmax);
uint32_t CollectionSupply_TestPartyField(uint16_t slot, uint16_t field);
uint16_t CollectionSupply_TestBagCount(uint16_t item);
uint16_t CollectionSupply_TestBagItem(void);
uint32_t CollectionSupply_TestGiftField(uint16_t field);
uint32_t CollectionSupply_TestRaidField(uint16_t field);

#endif /* VEGA_COLLECTION_SUPPLY_V1_H */
