#include "vermilion_slice.h"

#include <string.h>

static VegaSaveStatus PersistCopy(VegaModernSaveData *save,
                                  VegaModernSaveData *next,
                                  VegaPersistCallback persist,
                                  void *context)
{
    if (persist == NULL || !persist(next, sizeof(*next), context))
        return VEGA_SAVE_PERSIST_FAILED;
    memcpy(save, next, sizeof(*save));
    return VEGA_SAVE_OK;
}

uint8_t VegaVermilionCanUnlock(const VegaModernSaveData *save,
                               const VegaVermilionRuntime *runtime)
{
    if (save == NULL || runtime == NULL)
        return 0;
    return (uint8_t)(save->kanto_travel_unlocked || save->vega_hall_of_fame
                     || (runtime->shiou_badge_flag && runtime->dh_clear_flag));
}

VegaSaveStatus VegaVermilionLatchTravel(VegaModernSaveData *save,
                                        const VegaVermilionRuntime *runtime,
                                        VegaPersistCallback persist,
                                        void *context)
{
    VegaModernSaveData next;
    if (save == NULL || runtime == NULL)
        return VEGA_SAVE_INVALID_ARGUMENT;
    if (!VegaVermilionCanUnlock(save, runtime))
        return VEGA_SAVE_NOT_ALLOWED;
    if (save->kanto_travel_unlocked)
        return VEGA_SAVE_OK;
    memcpy(&next, save, sizeof(next));
    next.kanto_travel_unlocked = 1;
    VegaSaveFinalize(&next);
    return PersistCopy(save, &next, persist, context);
}

VegaSaveStatus VegaVermilionEnter(VegaModernSaveData *save,
                                  VegaVermilionRuntime *runtime,
                                  VegaWarpAnchor tohoku_return,
                                  VegaWarpAnchor vermilion_terminal,
                                  VegaPersistCallback persist,
                                  void *context)
{
    VegaModernSaveData next;
    if (save == NULL || runtime == NULL)
        return VEGA_SAVE_INVALID_ARGUMENT;
    if (!save->kanto_travel_unlocked || !runtime->warning_accepted
        || !VegaVermilionSafeRouteIsClear(runtime))
        return VEGA_SAVE_NOT_ALLOWED;
    memcpy(&next, save, sizeof(next));
    next.first_kanto_warning_seen = 1;
    next.kanto_visited = 1;
    next.current_region = VEGA_REGION_KANTO;
    next.return_anchor[VEGA_REGION_TOHOKU] = tohoku_return;
    next.return_anchor[VEGA_REGION_KANTO] = vermilion_terminal;
    next.heal_anchor[VEGA_REGION_KANTO] = vermilion_terminal;
    VegaSaveFinalize(&next);
    return PersistCopy(save, &next, persist, context);
}

VegaSaveStatus VegaVermilionReturn(VegaModernSaveData *save,
                                   VegaPersistCallback persist,
                                   void *context)
{
    VegaModernSaveData next;
    if (save == NULL || !save->kanto_travel_unlocked)
        return VEGA_SAVE_NOT_ALLOWED;
    memcpy(&next, save, sizeof(next));
    next.current_region = VEGA_REGION_TOHOKU;
    VegaSaveFinalize(&next);
    return PersistCopy(save, &next, persist, context);
}

VegaSaveStatus VegaVermilionResolveWhiteout(VegaModernSaveData *save,
                                            VegaPersistCallback persist,
                                            void *context)
{
    VegaModernSaveData next;
    if (save == NULL)
        return VEGA_SAVE_INVALID_ARGUMENT;
    memcpy(&next, save, sizeof(next));
    if (next.current_region == VEGA_REGION_KANTO) {
        next.kanto_visited = 1;
        next.current_region = VEGA_REGION_KANTO;
    }
    VegaSaveFinalize(&next);
    return PersistCopy(save, &next, persist, context);
}

uint8_t VegaVermilionApplyShipResult(VegaModernSaveData *save,
                                     VegaShipBattleResult result)
{
    if (save == NULL || result > VEGA_SHIP_QUIT)
        return 0;
    return save->kanto_travel_unlocked;
}

uint8_t VegaVermilionGymAvailable(const VegaModernSaveData *save)
{
    uint8_t mask = (uint8_t)((1u << VEGA_VERMILION_REQUIRED_CERTS) - 1u);
    return (uint8_t)(save != NULL && (save->kanto_certifications & mask) == mask);
}

void VegaVermilionGymReset(VegaVermilionRuntime *runtime)
{
    if (runtime != NULL) {
        runtime->gym_puzzle_voltage = 0;
        runtime->gym_puzzle_complete = 0;
    }
}

uint8_t VegaVermilionGymAdjustVoltage(VegaVermilionRuntime *runtime,
                                     uint8_t terminal,
                                     uint8_t voltage)
{
    static const uint8_t expected[3] = {2, 1, 3};
    if (runtime == NULL || terminal >= 3 || voltage != expected[terminal]) {
        VegaVermilionGymReset(runtime);
        return 0;
    }
    runtime->gym_puzzle_voltage |= (uint8_t)(1u << terminal);
    runtime->gym_puzzle_complete = (uint8_t)(runtime->gym_puzzle_voltage == 0x07u);
    return runtime->gym_puzzle_complete;
}

uint8_t VegaVermilionGymClaimReward(VegaModernSaveData *save,
                                    VegaVermilionRuntime *runtime)
{
    if (!VegaVermilionGymAvailable(save) || runtime == NULL
        || !runtime->gym_puzzle_complete || runtime->gym_reward_claimed)
        return 0;
    runtime->gym_reward_claimed = 1;
    save->kanto_certifications |= (uint8_t)(1u << 2);
    VegaSaveFinalize(save);
    return 1;
}

uint8_t VegaVermilionSafeRouteIsClear(const VegaVermilionRuntime *runtime)
{
    return (uint8_t)(runtime != NULL && runtime->forced_battles_on_safe_route == 0
                     && runtime->field_moves_on_safe_route == 0
                     && runtime->payments_on_safe_route == 0);
}
