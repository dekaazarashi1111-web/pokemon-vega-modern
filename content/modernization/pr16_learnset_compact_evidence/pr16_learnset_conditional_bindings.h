#ifndef PR16_CONDITIONAL_BINDINGS_H
#define PR16_CONDITIONAL_BINDINGS_H
#include "pr16_learnset_runtime.h"
#define PR16_IMAGE ((const uint8_t *)0x95dee7cu)
#define PR16_IMAGE_SIZE 108008u
#define PR16_READ_VIEW ((uint8_t (*)(const uint8_t *,uint32_t,uint16_t,uint8_t,struct Pr16RuntimeView *))0x95f94d3u)
#define PR16_GET_MON_DATA ((uint32_t (*)(const void *,int,uint8_t *))0x0803F355u)
#define PR16_GET_BOX_DATA ((uint32_t (*)(const void *,int,uint8_t *))0x0803F4B1u)
#define PR16_GET_BOX_LEVEL ((uint8_t (*)(const void *))0x0803DF9Du)
#define PR16_GIVE_MON_MOVE ((uint16_t (*)(void *,uint16_t))0x0803E009u)
#define PR16_GIVE_BOX_MOVE ((uint16_t (*)(void *,uint16_t))0x0803E01Du)
#define PR16_LEARNING_CURSOR ((volatile uint8_t *)0x02023F88u)
#define PR16_PENDING_MOVE ((volatile uint16_t *)0x02023F82u)

extern const uint8_t Pr16ConditionalImage[];
#define PR16_CONDITIONAL_IMAGE Pr16ConditionalImage
#define PR16_CONDITIONAL_IMAGE_SIZE 31014u
#include "pr16_learnset_compact.h"
#define PR16_READ_CONDITIONAL Pr16ReadCompactConditional
#define PR16_OWNER_GATE ((uint8_t (*)(const uint8_t *,uint16_t,uint16_t,uint8_t,uint16_t *))0x95f9465u)
#define PR16_MEMORY_MODE ((volatile uint8_t *)0x0203EC00u)
#define PR16_PARENT_ARCHIVE_MOVES ((uint8_t (*)(void *,uint16_t *))0x95ddbe9u)
#endif
