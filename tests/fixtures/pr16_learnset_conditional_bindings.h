#ifndef PR16_CONDITIONAL_FIXTURE_BINDINGS_H
#define PR16_CONDITIONAL_FIXTURE_BINDINGS_H
#include "pr16_learnset_runtime.h"
extern uint8_t pr16_condition_cursor, pr16_condition_mode;
extern uint16_t pr16_condition_pending;
uint32_t Pr16ConditionData(const void *, int, uint8_t *);
uint16_t Pr16ConditionGive(void *, uint16_t);
uint8_t Pr16ConditionView(const uint8_t *, uint32_t, uint16_t, uint8_t, struct Pr16RuntimeView *);
uint8_t Pr16ConditionArchive(void *, uint16_t *);
#define PR16_GET_MON_DATA Pr16ConditionData
#define PR16_GIVE_MON_MOVE Pr16ConditionGive
#define PR16_IMAGE ((const uint8_t *)0)
#define PR16_IMAGE_SIZE 0u
#define PR16_CONDITIONAL_IMAGE ((const uint8_t *)0)
#define PR16_CONDITIONAL_IMAGE_SIZE 0u
#define PR16_READ_VIEW Pr16ConditionView
#define PR16_READ_CONDITIONAL Pr16ConditionView
#define PR16_LEARNING_CURSOR (&pr16_condition_cursor)
#define PR16_PENDING_MOVE (&pr16_condition_pending)
#define PR16_MEMORY_MODE (&pr16_condition_mode)
#define PR16_PARENT_ARCHIVE_MOVES Pr16ConditionArchive
#endif
