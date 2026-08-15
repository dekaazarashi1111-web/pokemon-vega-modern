#include "acquisition_runtime.h"

#include <stddef.h>
#include <stdint.h>

#include "acquisition_engine_adapter.h"
#include "../../generated/acquisition_event_defs.h"
#include "../../generated/acquisition_host_defs.h"

#if defined(__GNUC__)
#define VEGA_ACQ_EXPORT __attribute__((used, externally_visible))
#else
#define VEGA_ACQ_EXPORT
#endif

#define VEGA_ACQ_PROBE_MARKER 0xAC51u

_Static_assert(sizeof(VegaAcqPendingTransaction) == 20u,
               "acquisition pending ABI changed");

static void clear_bytes(void *destination, size_t size)
{
    uint8_t *out = (uint8_t *)destination;
    size_t index;
    for (index = 0; index < size; ++index)
        out[index] = 0u;
}

static int strings_equal(const char *left, const char *right)
{
    if (left == NULL || right == NULL)
        return 0;
    while (*left != '\0' && *left == *right) {
        ++left;
        ++right;
    }
    return *left == *right;
}

static uint16_t pending_checksum(const VegaAcqPendingTransaction *pending)
{
    uint32_t token = pending->transaction_token;
    uint16_t value = (uint16_t)0xA5C3u;
    value ^= pending->event_index;
    value ^= pending->species_id;
    value ^= (uint16_t)((uint16_t)pending->mode << 8);
    value ^= (uint16_t)pending->phase;
    value ^= (uint16_t)(token & 0xFFFFu);
    value ^= (uint16_t)(token >> 16);
    return value;
}

static int pending_valid(const VegaAcqPendingTransaction *pending)
{
    if (pending == NULL || pending->magic != VEGA_ACQ_PENDING_MAGIC)
        return 0;
    if (pending->event_index >= VEGA_ACQ_EVENT_COUNT)
        return 0;
    if (pending->mode > VEGA_ACQ_MODE_SERVICE)
        return 0;
    if (pending->phase < VEGA_ACQ_PHASE_PREPARED
        || pending->phase > VEGA_ACQ_PHASE_CAPTURE_ACTIVE)
        return 0;
    return pending->checksum == pending_checksum(pending);
}

static void prepare_pending(VegaAcqPendingTransaction *pending,
                            uint16_t event_index,
                            const VegaAcqEventDef *event_def,
                            uint8_t phase,
                            uint32_t token)
{
    clear_bytes(pending, sizeof(*pending));
    pending->magic = VEGA_ACQ_PENDING_MAGIC;
    pending->transaction_token = token;
    pending->event_index = event_index;
    pending->species_id = event_def->species_id;
    pending->mode = event_def->mode;
    pending->phase = phase;
    pending->checksum = pending_checksum(pending);
}

static uint16_t clear_pending_persisted(VegaAcqPendingTransaction *pending,
                                        uint16_t success_result)
{
    VegaAcqPendingTransaction previous = *pending;
    clear_bytes(pending, sizeof(*pending));
    if (!VegaAcqEngine_PersistAll()) {
        *pending = previous;
        VegaAcqEngine_FinalizeInMemory();
        return VEGA_ACQ_RESULT_PERSIST_FAILED;
    }
    return success_result;
}

static int event_grants_registered_species(const VegaAcqEventDef *event_def)
{
    if (event_def->species_id == 0u)
        return 0;
    if ((event_def->policy_flags & VEGA_ACQ_POLICY_DELIVERY_DOES_NOT_REGISTER) != 0u)
        return 0;
    return event_def->mode == VEGA_ACQ_MODE_CAPTURE
        || event_def->mode == VEGA_ACQ_MODE_GIFT
        || event_def->mode == VEGA_ACQ_MODE_FOSSIL;
}

static uint16_t commit_success(const VegaAcqEventDef *event_def,
                               VegaAcqPendingTransaction *pending,
                               uint32_t transaction_token)
{
    uint8_t old_claim = VegaAcqEngine_GetClaimCount(event_def);
    uint8_t old_registered = event_def->species_id != 0u
        ? VegaAcqEngine_IsSpeciesRegistered(event_def->species_id) : 0u;
    uint8_t new_claim = old_claim;
    VegaAcqPendingTransaction saved_pending = *pending;

    if (pending->phase != VEGA_ACQ_PHASE_OPERATION_STAGED)
        return VEGA_ACQ_RESULT_CORRUPT_PENDING;
    if (event_def->max_claims != 0u && old_claim < event_def->max_claims)
        new_claim = (uint8_t)(old_claim + 1u);
    if (new_claim != old_claim
        && !VegaAcqEngine_SetClaimCount(event_def, new_claim))
        return VEGA_ACQ_RESULT_ENGINE_REJECTED;
    if (event_grants_registered_species(event_def)
        && !VegaAcqEngine_SetSpeciesRegistered(event_def->species_id, 1u)) {
        (void)VegaAcqEngine_SetClaimCount(event_def, old_claim);
        return VEGA_ACQ_RESULT_ENGINE_REJECTED;
    }

    clear_bytes(pending, sizeof(*pending));
    if (!VegaAcqEngine_PersistAll()) {
        *pending = saved_pending;
        (void)VegaAcqEngine_SetClaimCount(event_def, old_claim);
        if (event_def->species_id != 0u)
            (void)VegaAcqEngine_SetSpeciesRegistered(event_def->species_id,
                                                     old_registered);
        VegaAcqEngine_FinalizeInMemory();
        /* The durable generation still contains OPERATION_STAGED plus the delivery.
         * Leave the operation intact so VegaAcq_RecoverPending can commit or retry. */
        return VEGA_ACQ_RESULT_PERSIST_FAILED;
    }
    VegaAcqEngine_FinalizeOperation(event_def, transaction_token);
    return VEGA_ACQ_RESULT_SUCCESS;
}

VEGA_ACQ_EXPORT uint16_t VegaAcq_Probe(void)
{
    return VEGA_ACQ_PROBE_MARKER;
}

VEGA_ACQ_EXPORT uint16_t VegaAcq_FindEventIndex(const char *event_key)
{
    uint16_t index;
    for (index = 0u; index < VEGA_ACQ_EVENT_COUNT; ++index) {
        if (strings_equal(event_key, gVegaAcqEventDefs[index].event_key))
            return index;
    }
    return VEGA_ACQ_NO_INDEX;
}

VEGA_ACQ_EXPORT uint16_t VegaAcq_Begin(uint16_t event_index)
{
    const VegaAcqEventDef *event_def;
    VegaAcqPendingTransaction *pending = VegaAcqEngine_GetPending();
    uint16_t result;
    uint32_t token = 0u;

    if (event_index >= VEGA_ACQ_EVENT_COUNT || pending == NULL)
        return VEGA_ACQ_RESULT_INVALID_SELECTION;
    if (pending_valid(pending))
        return VEGA_ACQ_RESULT_BUSY;

    event_def = &gVegaAcqEventDefs[event_index];
    if (!VegaAcqEngine_IsUnlockSatisfied(event_def->unlock_key))
        return VEGA_ACQ_RESULT_LOCKED;
    if ((event_def->policy_flags & VEGA_ACQ_POLICY_REQUIRE_REGISTERED) != 0u
        && !VegaAcqEngine_IsSpeciesRegistered(event_def->species_id))
        return VEGA_ACQ_RESULT_LOCKED;
    if (event_def->max_claims != 0u
        && VegaAcqEngine_GetClaimCount(event_def) >= event_def->max_claims)
        return VEGA_ACQ_RESULT_ALREADY_CLAIMED;
    if (!VegaAcqEngine_IsEventConditionSatisfied(event_def))
        return VEGA_ACQ_RESULT_LOCKED;

    result = VegaAcqEngine_Preflight(event_def);
    if (result != VEGA_ACQ_RESULT_SUCCESS)
        return result;

    prepare_pending(pending, event_index, event_def,
                    VEGA_ACQ_PHASE_PREPARED, 0u);
    if (!VegaAcqEngine_PersistAll()) {
        clear_bytes(pending, sizeof(*pending));
        VegaAcqEngine_FinalizeInMemory();
        return VEGA_ACQ_RESULT_PERSIST_FAILED;
    }

    if (event_def->mode == VEGA_ACQ_MODE_CAPTURE) {
        pending->phase = VEGA_ACQ_PHASE_CAPTURE_ACTIVE;
        pending->checksum = pending_checksum(pending);
        if (!VegaAcqEngine_PersistAll())
            return VEGA_ACQ_RESULT_PERSIST_FAILED;
        result = VegaAcqEngine_StartCaptureBattle(event_def);
        if (result == VEGA_ACQ_RESULT_BATTLE_STARTED)
            return result;
        return clear_pending_persisted(pending, result);
    }

    result = VegaAcqEngine_StageOperation(event_def, &token);
    if (result != VEGA_ACQ_RESULT_SUCCESS) {
        VegaAcqEngine_RollbackOperation(event_def, token);
        return clear_pending_persisted(pending, result);
    }
    {
        VegaAcqPendingTransaction prepared = *pending;
        pending->transaction_token = token;
        pending->phase = VEGA_ACQ_PHASE_OPERATION_STAGED;
        pending->checksum = pending_checksum(pending);
        if (!VegaAcqEngine_PersistAll()) {
            *pending = prepared;
            VegaAcqEngine_RollbackOperation(event_def, token);
            return clear_pending_persisted(
                pending, VEGA_ACQ_RESULT_PERSIST_FAILED);
        }
    }
    return commit_success(event_def, pending, token);
}

VEGA_ACQ_EXPORT uint16_t VegaAcq_ResolveBattle(uint16_t outcome)
{
    VegaAcqPendingTransaction *pending = VegaAcqEngine_GetPending();
    const VegaAcqEventDef *event_def;
    if (!pending_valid(pending))
        return VEGA_ACQ_RESULT_CORRUPT_PENDING;
    event_def = &gVegaAcqEventDefs[pending->event_index];
    if (event_def->mode != VEGA_ACQ_MODE_CAPTURE
        || pending->phase != VEGA_ACQ_PHASE_CAPTURE_ACTIVE)
        return VEGA_ACQ_RESULT_CORRUPT_PENDING;
    if (outcome == VEGA_ACQ_BATTLE_CAUGHT) {
        VegaAcqPendingTransaction capture_active = *pending;
        pending->phase = VEGA_ACQ_PHASE_OPERATION_STAGED;
        pending->checksum = pending_checksum(pending);
        if (!VegaAcqEngine_PersistAll()) {
            *pending = capture_active;
            VegaAcqEngine_RollbackOperation(event_def, 0u);
            return clear_pending_persisted(
                pending, VEGA_ACQ_RESULT_PERSIST_FAILED);
        }
        return commit_success(event_def, pending, 0u);
    }
    if (outcome == VEGA_ACQ_BATTLE_DEFEATED)
        return clear_pending_persisted(pending, VEGA_ACQ_RESULT_DEFEATED);
    if (outcome == VEGA_ACQ_BATTLE_ESCAPED)
        return clear_pending_persisted(pending, VEGA_ACQ_RESULT_ESCAPED);
    return clear_pending_persisted(pending, VEGA_ACQ_RESULT_CANCELLED);
}

VEGA_ACQ_EXPORT uint16_t VegaAcq_RecoverPending(void)
{
    VegaAcqPendingTransaction *pending = VegaAcqEngine_GetPending();
    const VegaAcqEventDef *event_def;
    VegaAcqPendingTransaction previous;
    uint16_t result;

    if (pending == NULL)
        return VEGA_ACQ_RESULT_CORRUPT_PENDING;
    if (pending->magic == 0u)
        return VEGA_ACQ_RESULT_SUCCESS;
    if (!pending_valid(pending)) {
        clear_bytes(pending, sizeof(*pending));
        if (!VegaAcqEngine_PersistAll())
            return VEGA_ACQ_RESULT_PERSIST_FAILED;
        return VEGA_ACQ_RESULT_CORRUPT_PENDING;
    }

    event_def = &gVegaAcqEventDefs[pending->event_index];
    previous = *pending;
    if (pending->phase == VEGA_ACQ_PHASE_OPERATION_STAGED) {
        /* The journal and delivery normally share one save generation.  Verify the
         * destination token as well so a torn/externally edited save fails closed. */
        if (!VegaAcqEngine_IsOperationDurable(
                event_def, previous.transaction_token)) {
            VegaAcqEngine_RollbackOperation(
                event_def, previous.transaction_token);
            clear_bytes(pending, sizeof(*pending));
            if (!VegaAcqEngine_PersistAll()) {
                *pending = previous;
                VegaAcqEngine_FinalizeInMemory();
                return VEGA_ACQ_RESULT_PERSIST_FAILED;
            }
            return VEGA_ACQ_RESULT_RECOVERED_RETRY;
        }
        result = commit_success(event_def, pending,
                                previous.transaction_token);
        return result == VEGA_ACQ_RESULT_SUCCESS
            ? VEGA_ACQ_RESULT_RECOVERED_COMMIT : result;
    }

    /* PREPARED or CAPTURE_ACTIVE has no durable delivery proof. */
    VegaAcqEngine_RollbackOperation(event_def, previous.transaction_token);
    clear_bytes(pending, sizeof(*pending));
    if (!VegaAcqEngine_PersistAll()) {
        *pending = previous;
        VegaAcqEngine_FinalizeInMemory();
        return VEGA_ACQ_RESULT_PERSIST_FAILED;
    }
    return VEGA_ACQ_RESULT_RECOVERED_RETRY;
}

VEGA_ACQ_EXPORT uint16_t VegaAcq_OpenHost(uint16_t host_index)
{
    const VegaAcqHostDef *host_def;
    uint16_t selected;
    uint16_t offset;
    uint16_t result;
    uint8_t belongs = 0u;

    if (host_index >= VEGA_ACQ_HOST_COUNT)
        return VEGA_ACQ_RESULT_INVALID_SELECTION;
    host_def = &gVegaAcqHostDefs[host_index];
    selected = VegaAcqEngine_SelectHostEvent(
        &gVegaAcqHostEventIndices[host_def->first_event_index],
        host_def->event_count);
    if (selected == VEGA_ACQ_ASYNC_SELECTION)
        return VEGA_ACQ_RESULT_BUSY;
    if (selected == VEGA_ACQ_NO_INDEX)
        return VEGA_ACQ_RESULT_CANCELLED;
    for (offset = 0u; offset < host_def->event_count; ++offset) {
        if (gVegaAcqHostEventIndices[host_def->first_event_index + offset]
            == selected) {
            belongs = 1u;
            break;
        }
    }
    if (!belongs)
        result = VEGA_ACQ_RESULT_INVALID_SELECTION;
    else
        result = VegaAcq_Begin(selected);
    VegaAcqEngine_ShowResult(selected, result);
    return result;
}
