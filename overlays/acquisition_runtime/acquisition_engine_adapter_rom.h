#ifndef VEGA_ACQUISITION_ENGINE_ADAPTER_ROM_H
#define VEGA_ACQUISITION_ENGINE_ADAPTER_ROM_H

#include <stdint.h>

#define VEGA_ACQ_VOLATILE_STATE_ADDRESS 0x0203EC10u
#define VEGA_ACQ_VOLATILE_STATE_BYTES 288u

void VegaAcq_PostHost(void);
uint16_t VegaAcq_RegisterHatchedPartyMon(void);
uint16_t VegaAcq_MineFossil(void);
uint16_t VegaAcqAdapter_Probe(void);

#endif /* VEGA_ACQUISITION_ENGINE_ADAPTER_ROM_H */
