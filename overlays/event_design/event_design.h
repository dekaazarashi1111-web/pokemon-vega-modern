#ifndef VEGA_EVENT_DESIGN_H
#define VEGA_EVENT_DESIGN_H

#include <stdint.h>

#define EVENT_DESIGN_MAGIC 0x45443230u /* "ED20" */

enum EventDesignProbeSelector {
    EVENT_DESIGN_PROBE_MAGIC = 0,
    EVENT_DESIGN_PROBE_STATE_COUNT = 1,
    EVENT_DESIGN_PROBE_CONDITION_COUNT = 2,
    EVENT_DESIGN_PROBE_EVENT_COUNT = 3,
    EVENT_DESIGN_PROBE_PLACEMENT_COUNT = 4,
    EVENT_DESIGN_PROBE_DIALOGUE_COUNT = 5,
    EVENT_DESIGN_PROBE_BATCH_COUNT = 6,
    EVENT_DESIGN_PROBE_REWARD_COUNT = 7,
};

uint32_t EventDesign_Probe(uint32_t selector);
uint8_t EventDesign_CheckUnlock(uint16_t unlock_index);
uint8_t EventDesign_CheckCondition(uint16_t condition_index);
uint8_t EventDesign_EventRank(uint16_t event_index);
uint8_t EventDesign_SetState(uint16_t state_index);
uint8_t EventDesign_GrantReward(uint16_t reward_index);
uint8_t EventDesign_OpenEggBasket(void);

/* Field-script ABI: VAR_8000 is the index input and VAR_RESULT is the output. */
void EventDesign_ScriptCheckUnlock(void);
void EventDesign_ScriptCheckCondition(void);
void EventDesign_ScriptEventRank(void);
void EventDesign_ScriptSetState(void);
void EventDesign_ScriptGrantReward(void);
void EventDesign_ScriptOpenEggBasket(void);
void EventDesign_ScriptSchedule(void);

#endif
