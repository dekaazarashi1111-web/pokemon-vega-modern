#ifndef PR16_LEARNSET_PROGRESS_H
#define PR16_LEARNSET_PROGRESS_H
#include "pr16_learnset_runtime.h"
#define PR16_PROGRESS_END 255u
/* Only a prepared LEVEL_UP view is accepted. No fallback or conditional rows.
 * Initial returns the last four raw eligible rows, retaining source order and
 * duplicates: the existing GiveMoveToBoxMon owns duplicate/PP semantics. */
uint8_t Pr16ProgressInitial(const struct Pr16RuntimeView *view, uint8_t level,
                           uint16_t *moves, uint8_t capacity);
/* The caller advances even after FULL/ALREADY_KNOWN, as the native UI expects.
 * END is absorbing until firstMove resets it. No persistent/global state here. */
uint16_t Pr16ProgressNext(const struct Pr16RuntimeView *view, uint8_t level,
                          uint8_t firstMove, uint8_t *cursor);
#endif
