#ifndef VEGA_FACTORY_SPECIAL_EVENT_RUNTIME_H
#define VEGA_FACTORY_SPECIAL_EVENT_RUNTIME_H

#include <stdint.h>

#define VEGA_FACTORY_SPECIAL_EVENT_ABI_VERSION 0xB930u

uint16_t FactorySpecialEventRuntime_Probe(void);
uint16_t FactorySpecialEventRuntime_Complete(void);

#endif /* VEGA_FACTORY_SPECIAL_EVENT_RUNTIME_H */
