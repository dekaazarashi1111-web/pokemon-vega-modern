#include "save_migration.h"

#include <string.h>

_Static_assert(sizeof(VegaWarpAnchor) == 8, "warp anchor ABI changed");
_Static_assert(sizeof(VegaModernSaveData) == VEGA_SAVE_LEDGER_SIZE, "save ledger must fill its allocation");
_Static_assert(sizeof(VegaResearchEconomyState) == 64u,
               "research economy owner must be exactly 64 bytes");
_Static_assert(offsetof(VegaModernSaveData, research_economy) == 0x73Fu,
               "research economy owner must start at the v1 reserved tail");
_Static_assert(offsetof(VegaModernSaveData, reserved) == 0x77Fu,
               "v2 remaining reserved tail offset changed");
_Static_assert(VEGA_DEX_MIGRATION_RESERVED_BYTES == 15u,
               "acquisition block must preserve the v1 save offsets");
_Static_assert(offsetof(VegaModernSaveData, acquisition_save_block) % 4u == 0u,
               "acquisition block must be aligned for ARM7TDMI u32 access");
_Static_assert(offsetof(VegaModernSaveData, factory) + offsetof(VegaFactoryState, party_snapshot)
                   + VEGA_PARTY_CAPACITY * VEGA_PARTY_MON_SIZE
               <= VEGA_SAVE_LEDGER_SIZE,
               "factory snapshot exceeds the ledger");

#if defined(VEGA_SAVE_ROM_RUNTIME)
#define VEGA_SAVE_DECLARE_BEFORE() VegaModernSaveData *before = gVegaSaveRollbackData
#else
#define VEGA_SAVE_DECLARE_BEFORE() \
    VegaModernSaveData before_storage; \
    VegaModernSaveData *before = &before_storage
#endif

static uint8_t IsErasedOrZero(const VegaModernSaveData *data)
{
    const uint8_t *bytes = (const uint8_t *)data;
    uint8_t all_zero = 1;
    uint8_t all_ff = 1;
    size_t i;

    for (i = 0; i < sizeof(*data); ++i) {
        all_zero = (uint8_t)(all_zero && bytes[i] == 0);
        all_ff = (uint8_t)(all_ff && bytes[i] == 0xFFu);
    }
    return (uint8_t)(all_zero || all_ff);
}

static uint8_t BytesAreZero(const uint8_t *bytes, size_t size)
{
    size_t i;
    for (i = 0; i < size; ++i) {
        if (bytes[i] != 0)
            return 0;
    }
    return 1;
}

#define VEGA_ACQUISITION_SAVE_MAGIC 0x51434156u /* "VACQ" */
#define VEGA_ACQUISITION_SAVE_VERSION 1u
#define VEGA_ACQUISITION_CRC_OFFSET 8u

static uint32_t ReadU32(const uint8_t *bytes)
{
    return (uint32_t)bytes[0]
        | ((uint32_t)bytes[1] << 8)
        | ((uint32_t)bytes[2] << 16)
        | ((uint32_t)bytes[3] << 24);
}

static uint16_t ReadU16(const uint8_t *bytes)
{
    return (uint16_t)((uint16_t)bytes[0] | ((uint16_t)bytes[1] << 8));
}

static uint32_t AcquisitionChecksum(const uint8_t *bytes)
{
    uint32_t crc = 0xFFFFFFFFu;
    size_t index;
    uint8_t bit;
    for (index = 0; index < VEGA_ACQUISITION_SAVE_BYTES; ++index) {
        uint8_t value = (index >= VEGA_ACQUISITION_CRC_OFFSET
                         && index < VEGA_ACQUISITION_CRC_OFFSET + 4u)
            ? 0u : bytes[index];
        crc ^= value;
        for (bit = 0u; bit < 8u; ++bit)
            crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}

static uint8_t AcquisitionBlockIsValid(const uint8_t *bytes)
{
    if (BytesAreZero(bytes, VEGA_ACQUISITION_SAVE_BYTES))
        return 1u; /* v1.3.9以前のsaveは初回アクセス時に移行する。 */
    return (uint8_t)(
        ReadU32(bytes) == VEGA_ACQUISITION_SAVE_MAGIC
        && ReadU16(bytes + 4u) == VEGA_ACQUISITION_SAVE_VERSION
        && ReadU16(bytes + 6u) == VEGA_ACQUISITION_SAVE_BYTES
        && ReadU32(bytes + VEGA_ACQUISITION_CRC_OFFSET)
            == AcquisitionChecksum(bytes));
}

uint32_t VegaSaveChecksum(const VegaModernSaveData *data)
{
    const uint8_t *bytes = (const uint8_t *)data;
    const size_t checksum_start = offsetof(VegaModernSaveData, checksum);
    const size_t checksum_end = checksum_start + sizeof(data->checksum);
    uint32_t hash = 2166136261u;
    size_t i;

    if (data == NULL)
        return 0;
    for (i = 0; i < sizeof(*data); ++i) {
        const uint8_t value = (i >= checksum_start && i < checksum_end) ? 0 : bytes[i];
        hash ^= value;
        hash *= 16777619u;
    }
    return hash;
}

static void InitializeResearchEconomyOwner(VegaModernSaveData *data)
{
    memset(&data->research_economy, 0, sizeof(data->research_economy));
    data->research_economy.owner_schema_version = 1u;
    data->research_economy.owner_struct_size =
        (uint8_t)sizeof(data->research_economy);
    data->research_economy.economy_rank = 1u;
    data->research_economy.next_transaction_id = 1u;
}

void VegaSaveFinalize(VegaModernSaveData *data)
{
    if (data == NULL)
        return;
    if (data->version == VEGA_SAVE_LEGACY_VERSION) {
        /* 壊れたv1予約末尾を初期値で隠してv2へ昇格してはならない。 */
        if (!BytesAreZero((const uint8_t *)&data->research_economy,
                          sizeof(data->research_economy))
            || !BytesAreZero(data->reserved, sizeof(data->reserved)))
            return;
        InitializeResearchEconomyOwner(data);
    } else if (data->version == 0u && data->magic == 0u) {
        /* VegaSaveInitNewがzero初期化した新規台帳。 */
        InitializeResearchEconomyOwner(data);
    } else if (data->version != VEGA_SAVE_VERSION) {
        return;
    }
    data->magic = VEGA_SAVE_MAGIC;
    data->version = VEGA_SAVE_VERSION;
    data->struct_size = (uint16_t)sizeof(*data);
    data->checksum = 0;
    data->checksum = VegaSaveChecksum(data);
}

static void Normalize(VegaModernSaveData *data)
{
    size_t region;

    if (data->current_region >= VEGA_REGION_COUNT)
        data->current_region = VEGA_REGION_TOHOKU;
    if (data->text_speed > VEGA_TEXT_NORMAL)
        data->text_speed = VEGA_TEXT_INSTANT;
    if (data->hatch_mode > VEGA_HATCH_SKIP)
        data->hatch_mode = VEGA_HATCH_FAST;
    data->exp_share_enabled = (uint8_t)(data->exp_share_enabled != 0);
    data->kanto_travel_unlocked = (uint8_t)(data->kanto_travel_unlocked != 0);
    data->kanto_visited = (uint8_t)(data->kanto_visited != 0);
    data->vega_hall_of_fame = (uint8_t)(data->vega_hall_of_fame != 0);
    data->kanto_certifications &= (uint8_t)((1u << VEGA_CERTIFICATION_COUNT) - 1u);
    for (region = 0; region < VEGA_REGION_COUNT; ++region) {
        if (data->encounter_profile[region] > VEGA_PROFILE_RESEARCH)
            data->encounter_profile[region] = VEGA_PROFILE_NORMAL;
    }
    if (!data->league_i_cleared)
        data->league_ii_cleared = 0;
    if (data->egg_queue_count > VEGA_EGG_QUEUE_CAPACITY) {
        data->egg_queue_count = 0;
        data->egg_queue_head = 0;
        memset(data->egg_queue, 0, sizeof(data->egg_queue));
    }
    if (data->egg_queue_head >= VEGA_EGG_QUEUE_CAPACITY)
        data->egg_queue_head = 0;
    if (data->factory.battle_points > VEGA_BP_CAP)
        data->factory.battle_points = VEGA_BP_CAP;
    if (data->factory.party_count > VEGA_PARTY_CAPACITY)
        data->factory.party_count = VEGA_PARTY_CAPACITY;
    if (data->factory.marker > VEGA_FACTORY_RESTORE_PENDING) {
        data->factory.marker = VEGA_FACTORY_OUTSIDE;
        data->factory.snapshot_valid = 0;
    }
}

VegaSaveStatus VegaSaveValidate(const VegaModernSaveData *data, size_t available_size)
{
    if (data == NULL)
        return VEGA_SAVE_INVALID_ARGUMENT;
    if (available_size < sizeof(*data))
        return VEGA_SAVE_BAD_SIZE;
    if (IsErasedOrZero(data))
        return VEGA_SAVE_EMPTY_OR_LEGACY;
    if (data->magic != VEGA_SAVE_MAGIC)
        return VEGA_SAVE_BAD_MAGIC;
    if (data->version != VEGA_SAVE_LEGACY_VERSION
        && data->version != VEGA_SAVE_VERSION)
        return VEGA_SAVE_UNSUPPORTED_VERSION;
    if (data->struct_size != sizeof(*data))
        return VEGA_SAVE_BAD_SIZE;
    if (data->checksum != VegaSaveChecksum(data))
        return VEGA_SAVE_BAD_CHECKSUM;
    if (!BytesAreZero(data->reserved_dex_migration_prefix,
                      sizeof(data->reserved_dex_migration_prefix))
        || !AcquisitionBlockIsValid(data->acquisition_save_block)
        || !BytesAreZero(data->reserved_dex_migration,
                         sizeof(data->reserved_dex_migration)))
        return VEGA_SAVE_RESERVED_NONZERO;
    if (data->version == VEGA_SAVE_LEGACY_VERSION) {
        if (!BytesAreZero((const uint8_t *)&data->research_economy,
                          sizeof(data->research_economy))
            || !BytesAreZero(data->reserved, sizeof(data->reserved)))
            return VEGA_SAVE_RESERVED_NONZERO;
        return VEGA_SAVE_OK;
    }
    if (data->research_economy.owner_schema_version != 1u
        || data->research_economy.owner_struct_size
            != sizeof(data->research_economy)
        || data->research_economy.research_point_balance > 9999u
        || data->research_economy.economy_rank < 1u
        || data->research_economy.economy_rank > 7u
        || data->research_economy.minutes_into_research_day >= 60u
        || data->research_economy.pending_kind > 4u
        || data->research_economy.pending_phase > 1u
        || !BytesAreZero(data->research_economy.owner_reserved,
                         sizeof(data->research_economy.owner_reserved))
        || !BytesAreZero(data->reserved, sizeof(data->reserved)))
        return VEGA_SAVE_RESERVED_NONZERO;
    return VEGA_SAVE_OK;
}

VegaSaveStatus VegaSaveMigrateV1(VegaModernSaveData *data,
                                 size_t available_size)
{
    VegaSaveStatus status = VegaSaveValidate(data, available_size);
    if (status != VEGA_SAVE_OK)
        return status;
    if (data->version == VEGA_SAVE_VERSION)
        return VEGA_SAVE_OK;
    InitializeResearchEconomyOwner(data);
    /* v1のchecksumと予約末尾は上で検証済み。Finalizeへ移行済みと伝える。 */
    data->version = VEGA_SAVE_VERSION;
    VegaSaveFinalize(data);
    return VEGA_SAVE_OK;
}

VegaSaveStatus VegaSaveLoad(VegaModernSaveData *data, size_t available_size)
{
    VegaSaveStatus status = VegaSaveValidate(data, available_size);
    if (status != VEGA_SAVE_OK)
        return status;
    status = VegaSaveMigrateV1(data, available_size);
    if (status != VEGA_SAVE_OK)
        return status;
    Normalize(data);
    VegaSaveFinalize(data);
    return VEGA_SAVE_OK;
}

void VegaSaveInitNew(VegaModernSaveData *data, uint8_t first_badge_owned)
{
    if (data == NULL)
        return;
    memset(data, 0, sizeof(*data));
    data->current_region = VEGA_REGION_TOHOKU;
    data->text_speed = VEGA_TEXT_INSTANT;
    data->hatch_mode = VEGA_HATCH_FAST;
    data->exp_share_enabled = (uint8_t)(first_badge_owned != 0);
    VegaSaveFinalize(data);
}

VegaSaveStatus VegaSaveMigrateLegacy(VegaModernSaveData *data, const VegaLegacySignals *legacy)
{
    if (data == NULL || legacy == NULL)
        return VEGA_SAVE_INVALID_ARGUMENT;
    if (!legacy->recognized_vega_signature || !legacy->legacy_checksum_valid)
        return VEGA_SAVE_BAD_CHECKSUM;

    VegaSaveInitNew(data, legacy->first_badge_owned);
    data->legacy_migration_done = 1;
    data->vega_hall_of_fame = (uint8_t)(legacy->hall_of_fame != 0);
    data->kanto_travel_unlocked = (uint8_t)(legacy->hall_of_fame
                                           || (legacy->shiou_complete_flag_0824
                                               && legacy->dh_complete_flag_114b));
    memcpy(data->item_obtained_flags, legacy->item_obtained_flags,
           sizeof(legacy->item_obtained_flags));
    VegaSaveFinalize(data);
    return VEGA_SAVE_OK;
}

static uint8_t AnchorIsValid(VegaWarpAnchor anchor)
{
    return (uint8_t)(anchor.valid && anchor.map_group < 0x7Fu && anchor.map_num < 0x7Fu
                     && anchor.warp_id < 0x7Fu);
}

VegaWarpAnchor VegaSaveResolveAnchor(const VegaModernSaveData *data,
                                     VegaRegion region,
                                     uint8_t use_return_anchor,
                                     VegaWarpAnchor tohoku_fallback,
                                     VegaWarpAnchor kanto_fallback)
{
    VegaWarpAnchor fallback = region == VEGA_REGION_KANTO ? kanto_fallback : tohoku_fallback;
    VegaWarpAnchor stored;

    if (data == NULL || region >= VEGA_REGION_COUNT)
        return tohoku_fallback;
    stored = use_return_anchor ? data->return_anchor[region] : data->heal_anchor[region];
    return AnchorIsValid(stored) ? stored : fallback;
}

VegaSaveStatus VegaSaveSetRegion(VegaModernSaveData *data, VegaRegion region)
{
    if (data == NULL || region >= VEGA_REGION_COUNT)
        return VEGA_SAVE_RANGE_ERROR;
    if (region == VEGA_REGION_KANTO && !data->kanto_travel_unlocked)
        return VEGA_SAVE_NOT_ALLOWED;
    data->current_region = (uint8_t)region;
    if (region == VEGA_REGION_KANTO)
        data->kanto_visited = 1;
    VegaSaveFinalize(data);
    return VEGA_SAVE_OK;
}

VegaSaveStatus VegaSaveSetEncounterProfile(VegaModernSaveData *data,
                                           VegaRegion region,
                                           VegaEncounterProfile profile)
{
    if (data == NULL || region >= VEGA_REGION_COUNT || profile > VEGA_PROFILE_RESEARCH)
        return VEGA_SAVE_RANGE_ERROR;
    data->encounter_profile[region] = (uint8_t)profile;
    VegaSaveFinalize(data);
    return VEGA_SAVE_OK;
}

static VegaSaveStatus BitSet(uint8_t *bits, uint16_t key, uint16_t count)
{
    if (bits == NULL || key >= count)
        return VEGA_SAVE_RANGE_ERROR;
    bits[key >> 3] |= (uint8_t)(1u << (key & 7u));
    return VEGA_SAVE_OK;
}

static uint8_t BitGet(const uint8_t *bits, uint16_t key, uint16_t count)
{
    return (uint8_t)(bits != NULL && key < count && (bits[key >> 3] & (1u << (key & 7u))) != 0);
}

VegaSaveStatus VegaSaveMarkSpecialCaptured(VegaModernSaveData *data, uint16_t shared_key)
{
    VegaSaveStatus status;
    if (data == NULL)
        return VEGA_SAVE_INVALID_ARGUMENT;
    status = BitSet(data->shared_special_capture, shared_key, VEGA_SPECIAL_CAPTURE_COUNT);
    if (status == VEGA_SAVE_OK)
        VegaSaveFinalize(data);
    return status;
}

uint8_t VegaSaveIsSpecialCaptured(const VegaModernSaveData *data, uint16_t shared_key)
{
    return data == NULL ? 0 : BitGet(data->shared_special_capture, shared_key, VEGA_SPECIAL_CAPTURE_COUNT);
}

VegaSaveStatus VegaSaveAdvanceLeague(VegaModernSaveData *data, VegaLeagueStage stage)
{
    if (data == NULL)
        return VEGA_SAVE_INVALID_ARGUMENT;
    if (stage == VEGA_LEAGUE_STAGE_I && !data->league_i_cleared)
        data->league_i_cleared = 1;
    else if (stage == VEGA_LEAGUE_STAGE_II && data->league_i_cleared && !data->league_ii_cleared)
        data->league_ii_cleared = 1;
    else
        return VEGA_SAVE_NOT_ALLOWED;
    VegaSaveFinalize(data);
    return VEGA_SAVE_OK;
}

VegaSaveStatus VegaEggQueuePush(VegaModernSaveData *data, const uint8_t box_mon[VEGA_BOX_MON_SIZE])
{
    uint8_t tail;
    if (data == NULL || box_mon == NULL)
        return VEGA_SAVE_INVALID_ARGUMENT;
    if (data->egg_queue_count >= VEGA_EGG_QUEUE_CAPACITY)
        return VEGA_SAVE_QUEUE_FULL;
    tail = (uint8_t)((data->egg_queue_head + data->egg_queue_count) % VEGA_EGG_QUEUE_CAPACITY);
    memcpy(data->egg_queue[tail], box_mon, VEGA_BOX_MON_SIZE);
    data->egg_queue_count++;
    VegaSaveFinalize(data);
    return VEGA_SAVE_OK;
}

VegaSaveStatus VegaEggQueuePop(VegaModernSaveData *data, uint8_t box_mon[VEGA_BOX_MON_SIZE])
{
    if (data == NULL || box_mon == NULL)
        return VEGA_SAVE_INVALID_ARGUMENT;
    if (data->egg_queue_count == 0)
        return VEGA_SAVE_QUEUE_EMPTY;
    memcpy(box_mon, data->egg_queue[data->egg_queue_head], VEGA_BOX_MON_SIZE);
    memset(data->egg_queue[data->egg_queue_head], 0, VEGA_BOX_MON_SIZE);
    data->egg_queue_head = (uint8_t)((data->egg_queue_head + 1u) % VEGA_EGG_QUEUE_CAPACITY);
    data->egg_queue_count--;
    if (data->egg_queue_count == 0)
        data->egg_queue_head = 0;
    VegaSaveFinalize(data);
    return VEGA_SAVE_OK;
}

VegaSaveStatus VegaFactoryAddBattlePoints(VegaModernSaveData *data, uint16_t amount)
{
    uint32_t result;
    if (data == NULL)
        return VEGA_SAVE_INVALID_ARGUMENT;
    result = (uint32_t)data->factory.battle_points + amount;
    data->factory.battle_points = (uint16_t)(result > VEGA_BP_CAP ? VEGA_BP_CAP : result);
    VegaSaveFinalize(data);
    return VEGA_SAVE_OK;
}

VegaSaveStatus VegaFactorySpendBattlePoints(VegaModernSaveData *data, uint16_t amount)
{
    if (data == NULL)
        return VEGA_SAVE_INVALID_ARGUMENT;
    if (amount > data->factory.battle_points)
        return VEGA_SAVE_INSUFFICIENT_CREDIT;
    data->factory.battle_points = (uint16_t)(data->factory.battle_points - amount);
    VegaSaveFinalize(data);
    return VEGA_SAVE_OK;
}

static VegaSaveStatus Commit(VegaModernSaveData *data,
                             const VegaModernSaveData *before,
                             VegaPersistCallback persist,
                             void *context)
{
    data->generation++;
    Normalize(data);
    VegaSaveFinalize(data);
    if (persist == NULL || !persist(data, sizeof(*data), context)) {
        memcpy(data, before, sizeof(*data));
        return VEGA_SAVE_PERSIST_FAILED;
    }
    return VEGA_SAVE_OK;
}

VegaSaveStatus VegaFactoryEnter(VegaModernSaveData *data,
                                const uint8_t party[VEGA_PARTY_CAPACITY][VEGA_PARTY_MON_SIZE],
                                uint8_t party_count,
                                VegaPersistCallback persist,
                                void *context)
{
    VEGA_SAVE_DECLARE_BEFORE();
    if (data == NULL || party == NULL || party_count > VEGA_PARTY_CAPACITY)
        return VEGA_SAVE_INVALID_ARGUMENT;
    if (data->factory.marker != VEGA_FACTORY_OUTSIDE || data->factory.snapshot_valid)
        return VEGA_SAVE_NOT_ALLOWED;
    memcpy(before, data, sizeof(*before));
    memcpy(data->factory.party_snapshot, party, sizeof(data->factory.party_snapshot));
    data->factory.party_count = party_count;
    data->factory.snapshot_valid = 1;
    data->factory.marker = VEGA_FACTORY_SNAPSHOT_COMMITTED;
    data->factory.transaction_id++;
    return Commit(data, before, persist, context);
}

VegaSaveStatus VegaFactorySetBattleActive(VegaModernSaveData *data,
                                          VegaPersistCallback persist,
                                          void *context)
{
    VEGA_SAVE_DECLARE_BEFORE();
    if (data == NULL || data->factory.marker != VEGA_FACTORY_SNAPSHOT_COMMITTED
        || !data->factory.snapshot_valid)
        return VEGA_SAVE_NOT_ALLOWED;
    memcpy(before, data, sizeof(*before));
    data->factory.marker = VEGA_FACTORY_BATTLE_ACTIVE;
    return Commit(data, before, persist, context);
}

VegaSaveStatus VegaFactoryRestore(VegaModernSaveData *data,
                                  uint8_t party[VEGA_PARTY_CAPACITY][VEGA_PARTY_MON_SIZE],
                                  uint8_t *party_count,
                                  VegaPersistCallback persist,
                                  void *context)
{
    VEGA_SAVE_DECLARE_BEFORE();
    if (data == NULL || party == NULL || party_count == NULL)
        return VEGA_SAVE_INVALID_ARGUMENT;
    if (!data->factory.snapshot_valid)
        return VEGA_SAVE_NOT_ALLOWED;

    memcpy(before, data, sizeof(*before));
    data->factory.marker = VEGA_FACTORY_RESTORE_PENDING;
    memcpy(party, data->factory.party_snapshot, sizeof(data->factory.party_snapshot));
    *party_count = data->factory.party_count;
    memset(data->factory.party_snapshot, 0, sizeof(data->factory.party_snapshot));
    data->factory.party_count = 0;
    data->factory.snapshot_valid = 0;
    data->factory.marker = VEGA_FACTORY_OUTSIDE;
    data->factory.transaction_id++;
    return Commit(data, before, persist, context);
}

VegaSaveStatus VegaFactoryClaimReward(VegaModernSaveData *data,
                                      uint8_t reward_index,
                                      uint16_t bp_amount,
                                      VegaPersistCallback persist,
                                      void *context)
{
    VEGA_SAVE_DECLARE_BEFORE();
    uint32_t bit;
    uint32_t result;
    if (data == NULL || reward_index >= 32u)
        return VEGA_SAVE_RANGE_ERROR;
    bit = 1u << reward_index;
    if ((data->factory.reward_claim_bits & bit) != 0)
        return VEGA_SAVE_ALREADY_CLAIMED;
    memcpy(before, data, sizeof(*before));
    result = (uint32_t)data->factory.battle_points + bp_amount;
    data->factory.battle_points = (uint16_t)(result > VEGA_BP_CAP ? VEGA_BP_CAP : result);
    data->factory.reward_claim_bits |= bit;
    data->factory.reward_pending = 0;
    data->factory.transaction_id++;
    return Commit(data, before, persist, context);
}

VegaSaveStatus VegaSavePurchaseEncounter(VegaModernSaveData *data,
                                         const VegaEncounterRequest *request,
                                         VegaPersistCallback persist,
                                         void *context)
{
    VEGA_SAVE_DECLARE_BEFORE();
    VegaPendingEncounter *pending;
    if (data == NULL || request == NULL || request->credit_kind >= VEGA_ENCOUNTER_CREDIT_TYPE_COUNT)
        return VEGA_SAVE_INVALID_ARGUMENT;
    if (data->pending_encounter.valid)
        return VEGA_SAVE_PENDING_EXISTS;
    if (data->encounter_credits[request->credit_kind] < request->cost)
        return VEGA_SAVE_INSUFFICIENT_CREDIT;

    memcpy(before, data, sizeof(*before));
    data->encounter_credits[request->credit_kind] =
        (uint16_t)(data->encounter_credits[request->credit_kind] - request->cost);
    pending = &data->pending_encounter;
    memset(pending, 0, sizeof(*pending));
    pending->valid = 1;
    pending->encounter_kind = request->encounter_kind;
    pending->pool = request->pool;
    pending->species = request->species;
    pending->form = request->form;
    pending->level = request->level;
    pending->nature = request->nature;
    pending->ability = request->ability;
    pending->shiny = (uint8_t)(request->shiny != 0);
    pending->tera_type = request->tera_type;
    pending->credit_kind = request->credit_kind;
    memcpy(pending->ivs, request->ivs, sizeof(pending->ivs));
    pending->personality = request->personality;
    pending->generator_version = request->generator_version;
    memcpy(pending->generator_fingerprint, request->generator_fingerprint,
           sizeof(pending->generator_fingerprint));
    pending->transaction_id = data->generation + 1u;
    return Commit(data, before, persist, context);
}

VegaSaveStatus VegaSaveCompleteCapture(VegaModernSaveData *data,
                                       uint16_t shared_key,
                                       VegaPersistCallback persist,
                                       void *context)
{
    VEGA_SAVE_DECLARE_BEFORE();
    VegaSaveStatus status;
    if (data == NULL || !data->pending_encounter.valid)
        return VEGA_SAVE_NOT_ALLOWED;
    memcpy(before, data, sizeof(*before));
    status = BitSet(data->shared_special_capture, shared_key, VEGA_SPECIAL_CAPTURE_COUNT);
    if (status != VEGA_SAVE_OK)
        return status;
    memset(&data->pending_encounter, 0, sizeof(data->pending_encounter));
    return Commit(data, before, persist, context);
}

VegaSaveStatus VegaRaidClaimReward(VegaModernSaveData *data,
                                   uint16_t shared_key,
                                   VegaPersistCallback persist,
                                   void *context)
{
    VEGA_SAVE_DECLARE_BEFORE();
    if (data == NULL || shared_key >= VEGA_SPECIAL_CAPTURE_COUNT)
        return VEGA_SAVE_RANGE_ERROR;
    if (BitGet(data->raid_reward_claimed, shared_key, VEGA_SPECIAL_CAPTURE_COUNT))
        return VEGA_SAVE_ALREADY_CLAIMED;
    memcpy(before, data, sizeof(*before));
    BitSet(data->raid_reward_claimed, shared_key, VEGA_SPECIAL_CAPTURE_COUNT);
    return Commit(data, before, persist, context);
}

VegaSaveStatus VegaRaidSetRetry(VegaModernSaveData *data,
                                uint16_t shared_key,
                                uint8_t pending,
                                VegaPersistCallback persist,
                                void *context)
{
    VEGA_SAVE_DECLARE_BEFORE();
    if (data == NULL || shared_key >= VEGA_SPECIAL_CAPTURE_COUNT)
        return VEGA_SAVE_RANGE_ERROR;
    memcpy(before, data, sizeof(*before));
    if (pending)
        BitSet(data->raid_retry_pending, shared_key, VEGA_SPECIAL_CAPTURE_COUNT);
    else
        data->raid_retry_pending[shared_key >> 3] &= (uint8_t)~(1u << (shared_key & 7u));
    return Commit(data, before, persist, context);
}

VegaSaveStatus VegaRaidSetBonusTier(VegaModernSaveData *data,
                                    uint16_t shared_key,
                                    uint8_t tier,
                                    VegaPersistCallback persist,
                                    void *context)
{
    VEGA_SAVE_DECLARE_BEFORE();
    if (data == NULL || shared_key >= VEGA_SPECIAL_CAPTURE_COUNT || tier > 3u)
        return VEGA_SAVE_RANGE_ERROR;
    if (tier < data->raid_bonus_tier[shared_key])
        return VEGA_SAVE_NOT_ALLOWED;
    memcpy(before, data, sizeof(*before));
    data->raid_bonus_tier[shared_key] = tier;
    return Commit(data, before, persist, context);
}
