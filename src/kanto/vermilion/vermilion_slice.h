#ifndef VEGA_VERMILION_SLICE_H
#define VEGA_VERMILION_SLICE_H

#include <stdint.h>

#include "../../../overlays/save_migration/save_migration.h"

#define VEGA_SHIOU_BADGE_FLAG 0x0824u
#define VEGA_DH_CLEAR_FLAG 0x114Bu
#define VEGA_VERMILION_REQUIRED_CERTS 2u

typedef enum VegaShipBattleResult {
    VEGA_SHIP_DECLINED = 0,
    VEGA_SHIP_WON = 1,
    VEGA_SHIP_LOST = 2,
    VEGA_SHIP_QUIT = 3
} VegaShipBattleResult;

typedef struct VegaVermilionRuntime {
    uint8_t shiou_badge_flag;
    uint8_t dh_clear_flag;
    uint8_t national_dex;
    uint8_t warning_accepted;
    uint8_t gym_puzzle_voltage;
    uint8_t gym_puzzle_complete;
    uint8_t gym_reward_claimed;
    uint8_t forced_battles_on_safe_route;
    uint8_t field_moves_on_safe_route;
    uint8_t payments_on_safe_route;
} VegaVermilionRuntime;

uint8_t VegaVermilionCanUnlock(const VegaModernSaveData *save,
                               const VegaVermilionRuntime *runtime);
VegaSaveStatus VegaVermilionLatchTravel(VegaModernSaveData *save,
                                        const VegaVermilionRuntime *runtime,
                                        VegaPersistCallback persist,
                                        void *context);
VegaSaveStatus VegaVermilionEnter(VegaModernSaveData *save,
                                  VegaVermilionRuntime *runtime,
                                  VegaWarpAnchor tohoku_return,
                                  VegaWarpAnchor vermilion_terminal,
                                  VegaPersistCallback persist,
                                  void *context);
VegaSaveStatus VegaVermilionReturn(VegaModernSaveData *save,
                                   VegaPersistCallback persist,
                                   void *context);
VegaSaveStatus VegaVermilionResolveWhiteout(VegaModernSaveData *save,
                                            VegaPersistCallback persist,
                                            void *context);
uint8_t VegaVermilionApplyShipResult(VegaModernSaveData *save,
                                     VegaShipBattleResult result);
uint8_t VegaVermilionGymAvailable(const VegaModernSaveData *save);
void VegaVermilionGymReset(VegaVermilionRuntime *runtime);
uint8_t VegaVermilionGymAdjustVoltage(VegaVermilionRuntime *runtime,
                                     uint8_t terminal,
                                     uint8_t voltage);
uint8_t VegaVermilionGymClaimReward(VegaModernSaveData *save,
                                    VegaVermilionRuntime *runtime);
uint8_t VegaVermilionSafeRouteIsClear(const VegaVermilionRuntime *runtime);

#endif
