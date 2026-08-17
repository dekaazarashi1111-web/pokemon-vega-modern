#ifndef VEGA_FACTORY_REWARD_RUNTIME_H
#define VEGA_FACTORY_REWARD_RUNTIME_H

#include <stdint.h>

#define VEGA_FACTORY_REWARD_ABI_VERSION 0xB928u

uint16_t FactoryRewardRuntime_Probe(void);
uint16_t FactoryRewardRuntime_Complete(void);

#endif /* VEGA_FACTORY_REWARD_RUNTIME_H */
