/* Host-only typed seams; production uses a generated fixed-JP header. */
#ifndef PR16_PROGRESS_FIXTURE_BINDINGS_H
#define PR16_PROGRESS_FIXTURE_BINDINGS_H
#include "pr16_learnset_runtime.h"
extern const uint8_t *pr16_test_image;
extern uint32_t pr16_test_image_size;
extern uint8_t pr16_test_cursor;
extern uint16_t pr16_test_pending;
uint32_t Pr16TestData(const void *, int, uint8_t *);
uint8_t Pr16TestLevel(const void *);
uint16_t Pr16TestGive(void *, uint16_t);
#define PR16_GET_BOX_DATA Pr16TestData
#define PR16_GET_MON_DATA Pr16TestData
#define PR16_GET_BOX_LEVEL Pr16TestLevel
#define PR16_GIVE_BOX_MOVE Pr16TestGive
#define PR16_GIVE_MON_MOVE Pr16TestGive
#define PR16_IMAGE pr16_test_image
#define PR16_IMAGE_SIZE pr16_test_image_size
#define PR16_READ_VIEW Pr16ReadLearnsetRuntime
#define PR16_LEARNING_CURSOR (&pr16_test_cursor)
#define PR16_PENDING_MOVE (&pr16_test_pending)
#endif
