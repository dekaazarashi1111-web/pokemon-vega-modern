#include "event_design.h"

#include <stddef.h>
#include <stdint.h>

#include "event_design_generated.h"
#include "../save_migration/save_migration.h"

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

#define PTR(type, address) ((type)(uintptr_t)(address))

typedef u8 (*FlagGetFn)(u16);
typedef void (*FlagChangeFn)(u16);
typedef u8 (*BagFn)(u16, u16);
typedef u8 (*QolFeatureFn)(u16);
typedef u32 (*QolDispatchFn)(u16, u32, u32, u32);
typedef u8 (*TrainerFlagFn)(u16);
typedef void (*SaveFinalizeFn)(VegaModernSaveData *);
typedef void (*SetupScriptFn)(const u8 *);

#define FN_FLAG_GET PTR(FlagGetFn, 0x0806DEC5u)
#define FN_FLAG_SET PTR(FlagChangeFn, 0x0806DE75u)
#define FN_CHECK_BAG_SPACE PTR(BagFn, 0x08099A09u)
#define FN_ADD_BAG_ITEM PTR(BagFn, 0x08099A8Du)
#define FN_REMOVE_BAG_ITEM PTR(BagFn, 0x08099BE1u)
#define FN_QOL_FEATURE PTR(QolFeatureFn, EVENT_DESIGN_QOL_FEATURE_ADDRESS)
#define FN_QOL_DISPATCH PTR(QolDispatchFn, EVENT_DESIGN_QOL_DISPATCH_ADDRESS)
#define FN_TRAINER_DEFEATED PTR(TrainerFlagFn, EVENT_DESIGN_TRAINER_DEFEATED_ADDRESS)
#define FN_SAVE_FINALIZE PTR(SaveFinalizeFn, EVENT_DESIGN_SAVE_FINALIZE_ADDRESS)
#define FN_SCRIPT_CONTEXT_SETUP PTR(SetupScriptFn, 0x080693A5u)

#define VAR_8000 (*(volatile u16 *)(uintptr_t)0x02036FECu)
#define VAR_8001 (*(volatile u16 *)(uintptr_t)0x02036FEEu)
#define VAR_RESULT (*(volatile u16 *)(uintptr_t)0x02037004u)

#if defined(__GNUC__)
#define EVENT_EXPORT __attribute__((used, externally_visible, section(".text.EventDesign_")))
#else
#define EVENT_EXPORT
#endif

static u8 state_is_set(u16 state_index)
{
    if (state_index >= EVENT_DESIGN_STATE_COUNT)
        return 0u;
    return FN_FLAG_GET(gEventDesignStateFlags[state_index]);
}

EVENT_EXPORT
u32 EventDesign_Probe(u32 selector)
{
    switch (selector) {
    case EVENT_DESIGN_PROBE_MAGIC: return EVENT_DESIGN_MAGIC;
    case EVENT_DESIGN_PROBE_STATE_COUNT: return EVENT_DESIGN_STATE_COUNT;
    case EVENT_DESIGN_PROBE_CONDITION_COUNT: return EVENT_DESIGN_CONDITION_COUNT;
    case EVENT_DESIGN_PROBE_EVENT_COUNT: return EVENT_DESIGN_EVENT_COUNT;
    case EVENT_DESIGN_PROBE_PLACEMENT_COUNT: return EVENT_DESIGN_PLACEMENT_COUNT;
    case EVENT_DESIGN_PROBE_DIALOGUE_COUNT: return EVENT_DESIGN_DIALOGUE_COUNT;
    case EVENT_DESIGN_PROBE_BATCH_COUNT: return EVENT_DESIGN_BATCH_COUNT;
    case EVENT_DESIGN_PROBE_REWARD_COUNT: return EVENT_DESIGN_REWARD_COUNT;
    default: return 0u;
    }
}

EVENT_EXPORT
u8 EventDesign_CheckUnlock(u16 unlock_index)
{
    const EventDesignUnlock *unlock;
    if (unlock_index >= EVENT_DESIGN_UNLOCK_COUNT)
        return 0u;
    unlock = &gEventDesignUnlocks[unlock_index];
    switch (unlock->kind) {
    case EVENT_DESIGN_UNLOCK_FLAG:
        return FN_FLAG_GET(unlock->value);
    case EVENT_DESIGN_UNLOCK_CERT:
        return FN_FLAG_GET((u16)(EVENT_DESIGN_CERT_OWNER_FLAG_BASE + unlock->value));
    case EVENT_DESIGN_UNLOCK_QOL:
        return FN_QOL_FEATURE(unlock->value);
    case EVENT_DESIGN_UNLOCK_KANTO_EARLY:
        return (u8)(gVegaModernSaveData->kanto_travel_unlocked
                    || FN_FLAG_GET(EVENT_DESIGN_FLAG_HALL_OF_FAME)
                    || (FN_FLAG_GET(EVENT_DESIGN_FLAG_BADGE_5)
                        && FN_FLAG_GET(EVENT_DESIGN_FLAG_DH_CLEAR)));
    case EVENT_DESIGN_UNLOCK_KANTO_LEAGUE:
        return (u8)(FN_FLAG_GET(EVENT_DESIGN_CERT_OWNER_FLAG_BASE + 7u)
                    && (FN_FLAG_GET(EVENT_DESIGN_FLAG_HALL_OF_FAME)
                        || gVegaModernSaveData->vega_hall_of_fame));
    case EVENT_DESIGN_UNLOCK_KANTO_LEAGUE_CLEAR:
        return (u8)(state_is_set(EVENT_DESIGN_STATE_KANTO_LEAGUE_CLEAR)
                    || FN_FLAG_GET(EVENT_DESIGN_KANTO_CHAMPION_OWNER_FLAG)
                    || gVegaModernSaveData->league_ii_cleared);
    case EVENT_DESIGN_UNLOCK_SPHERE_COMPLETE:
        return (u8)(state_is_set(EVENT_DESIGN_STATE_KANTO_LEAGUE_CLEAR)
                    && state_is_set(EVENT_DESIGN_STATE_CAVE_RESONANCE));
    case EVENT_DESIGN_UNLOCK_FINAL_LEAGUE_CLEARED:
        return state_is_set(EVENT_DESIGN_STATE_FINAL_LEAGUE_CLEARED);
    default:
        return 0u;
    }
}

static u8 term_satisfied(const EventDesignTerm *term)
{
    u8 observed;
    switch (term->kind) {
    case EVENT_DESIGN_TERM_STATE:
        observed = state_is_set(term->value);
        break;
    case EVENT_DESIGN_TERM_QOL_FEATURE:
        observed = FN_QOL_FEATURE(term->value);
        break;
    case EVENT_DESIGN_TERM_TRAINER_DEFEATED:
        observed = FN_TRAINER_DEFEATED(term->value);
        break;
    case EVENT_DESIGN_TERM_ACQUISITION_CLAIMED:
        /* The existing acquisition wrapper owns durable claim state.  Its
         * SUCCESS/ALREADY_CLAIMED result is mirrored into VAR_8001 only for
         * the immediately following authored condition. */
        observed = (u8)(VAR_8001 != 0u);
        break;
    default:
        return 0u;
    }
    return (u8)(observed == term->expected);
}

EVENT_EXPORT
u8 EventDesign_CheckCondition(u16 condition_index)
{
    const EventDesignCondition *condition;
    u16 index;
    if (condition_index >= EVENT_DESIGN_CONDITION_COUNT)
        return 0u;
    condition = &gEventDesignConditions[condition_index];
    for (index = 0u; index < condition->count; ++index) {
        if (!term_satisfied(&gEventDesignTerms[condition->first + index]))
            return 0u;
    }
    return 1u;
}

EVENT_EXPORT
u8 EventDesign_EventRank(u16 event_index)
{
    const EventDesignEvent *event;
    if (event_index >= EVENT_DESIGN_EVENT_COUNT)
        return 0u;
    event = &gEventDesignEvents[event_index];
    if (!EventDesign_CheckUnlock(event->unlock_index))
        return 0u;
    if (event->condition_index != EVENT_DESIGN_NO_INDEX
        && !EventDesign_CheckCondition(event->condition_index))
        return 0u;
    if (event->completion_state != EVENT_DESIGN_NO_INDEX
        && !state_is_set(event->completion_state))
        return 3u; /* an unfinished stateful event always wins */
    if (event->repeatable)
        return 2u;
    return 1u; /* completed revisit */
}

static void synchronize_state_owner(u16 state_index)
{
    u16 cert;
    for (cert = 0u; cert < 8u; ++cert) {
        if (gEventDesignCertificationStates[cert] == state_index) {
            FN_FLAG_SET((u16)(EVENT_DESIGN_CERT_OWNER_FLAG_BASE + cert));
            gVegaModernSaveData->kanto_certifications |= (u8)(1u << cert);
            FN_SAVE_FINALIZE(gVegaModernSaveData);
            return;
        }
    }
    if (state_index == EVENT_DESIGN_STATE_KANTO_LEAGUE_CLEAR) {
        /* T19 treats league_ii_cleared as the production KANTO_LEAGUE_CLEAR
         * capability.  Keep league_i coherent so save normalization cannot
         * clear the owner bit. */
        gVegaModernSaveData->league_i_cleared = 1u;
        gVegaModernSaveData->league_ii_cleared = 1u;
        FN_SAVE_FINALIZE(gVegaModernSaveData);
    } else if (state_index == EVENT_DESIGN_STATE_FINAL_LEAGUE_CLEARED) {
        gVegaModernSaveData->league_i_cleared = 1u;
        gVegaModernSaveData->league_ii_cleared = 1u;
        FN_SAVE_FINALIZE(gVegaModernSaveData);
    }
}

EVENT_EXPORT
u8 EventDesign_SetState(u16 state_index)
{
    u16 flag;
    if (state_index >= EVENT_DESIGN_STATE_COUNT)
        return 0u;
    if (state_is_set(state_index))
        return 1u;
    if (state_index == EVENT_DESIGN_STATE_DAYCARE_COMPLETE
        && FN_QOL_DISPATCH(EVENT_DESIGN_QOL_SERVICE_SET_DAYCARE_QUEST,
                           1u, 0u, 0u) != 0u)
        return 0u;
    flag = gEventDesignStateFlags[state_index];
    synchronize_state_owner(state_index);
    FN_FLAG_SET(flag);
    return FN_FLAG_GET(flag);
}

EVENT_EXPORT
u8 EventDesign_GrantReward(u16 reward_index)
{
    const EventDesignReward *reward;
    u16 claim_flag;
    if (reward_index >= EVENT_DESIGN_REWARD_COUNT)
        return 0u;
    reward = &gEventDesignRewards[reward_index];
    claim_flag = gEventDesignStateFlags[reward->claim_state];
    if (FN_FLAG_GET(claim_flag))
        return 1u;
    if (!FN_CHECK_BAG_SPACE(reward->item, reward->quantity)
        || !FN_ADD_BAG_ITEM(reward->item, reward->quantity))
        return 0u;
    FN_FLAG_SET(claim_flag);
    if (!FN_FLAG_GET(claim_flag)) {
        (void)FN_REMOVE_BAG_ITEM(reward->item, reward->quantity);
        return 0u;
    }
    return 1u;
}

EVENT_EXPORT
u8 EventDesign_OpenEggBasket(void)
{
    return (u8)(FN_QOL_DISPATCH(EVENT_DESIGN_QOL_SERVICE_SET_EGG_BASKET,
                                1u, 0u, 0u) == 0u);
}

EVENT_EXPORT
void EventDesign_ScriptCheckUnlock(void)
{
    VAR_RESULT = EventDesign_CheckUnlock(VAR_8000);
}

EVENT_EXPORT
void EventDesign_ScriptCheckCondition(void)
{
    VAR_RESULT = EventDesign_CheckCondition(VAR_8000);
}

EVENT_EXPORT
void EventDesign_ScriptEventRank(void)
{
    VAR_RESULT = EventDesign_EventRank(VAR_8000);
}

EVENT_EXPORT
void EventDesign_ScriptSetState(void)
{
    VAR_RESULT = EventDesign_SetState(VAR_8000);
}

EVENT_EXPORT
void EventDesign_ScriptGrantReward(void)
{
    VAR_RESULT = EventDesign_GrantReward(VAR_8000);
}

EVENT_EXPORT
void EventDesign_ScriptOpenEggBasket(void)
{
    VAR_RESULT = EventDesign_OpenEggBasket();
}

EVENT_EXPORT
void EventDesign_ScriptSchedule(void)
{
    u32 address = (u32)VAR_8000 | ((u32)VAR_8001 << 16);
    if (address >= 0x08000000u && address < 0x0A000000u)
        FN_SCRIPT_CONTEXT_SETUP((const u8 *)(uintptr_t)address);
}
