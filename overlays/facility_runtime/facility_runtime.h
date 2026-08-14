#ifndef VEGA_FACILITY_RUNTIME_H
#define VEGA_FACILITY_RUNTIME_H

#include <stdint.h>

/* Script-callable entry points embedded by scripts/build_facility_runtime.py. */
uint16_t FacilityRuntime_Probe(void);
void FacilityRuntime_Recover(void);
void FacilityRuntime_Enter(void);
void FacilityRuntime_CommitSelection(void);
void FacilityRuntime_PrepareBattle(void);
void FacilityRuntime_AfterBattle(void);
void FacilityRuntime_BeginExchange(void);
void FacilityRuntime_CommitExchange(void);
void FacilityRuntime_SkipExchange(void);
void FacilityRuntime_Complete(void);
void FacilityRuntime_Abort(void);

#endif /* VEGA_FACILITY_RUNTIME_H */
