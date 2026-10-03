#ifndef PR16_LEARNSET_RUNTIME_H
#define PR16_LEARNSET_RUNTIME_H
#include "pr16_learnset_owner.h"

/* PLR1: fixed little-endian, byte-readable on ARM7; no native pointer in data. */
#define PR16_RUNTIME_NOT_LINKED 5u
struct Pr16RuntimeView {
    const uint8_t *bytes;
    uint16_t count;
    uint16_t owner;
};
/* Return the owner action, not eligibility. Non-learning owners never get a span. */
uint8_t Pr16ReadLearnsetRuntime(const uint8_t *image, uint32_t size,
                              uint16_t species, uint8_t consumer,
                              struct Pr16RuntimeView *out);
/* All-or-nothing copy; capacity failure leaves the caller's buffer unchanged. */
uint8_t Pr16RuntimeLevelMoves(const uint8_t *image, uint32_t size,
                            uint16_t species, uint16_t *moves, uint16_t capacity);
/* Existing physical slots only. Archived moves cannot enter this predicate. */
uint8_t Pr16RuntimeMachineAllowed(const uint8_t *image, uint32_t size,
                                uint16_t species, uint16_t slot);
#endif
