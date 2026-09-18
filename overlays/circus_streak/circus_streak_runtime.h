#ifndef VEGA_CIRCUS_STREAK_RUNTIME_H
#define VEGA_CIRCUS_STREAK_RUNTIME_H
#include <stdint.h>
int CircusStreakRuntimeRecover(void);
int CircusStreakRuntimeBegin(void);
int CircusStreakRuntimeArm(void);
int CircusStreakRuntimeRecord(uint8_t outcome);
int CircusStreakRuntimeEnd(int completed);
int CircusStreakRuntimeArmed(void);
void CircusStreakRuntimeReadKeys(void);
uint8_t CircusStreakRuntimeSaveLoad(uint8_t save_type);
void CircusStreakRuntimeSelect(void);
uint16_t CircusStreakRuntimeGet(uint8_t current_or_max, uint16_t style,
                              uint16_t tier, uint16_t size, uint8_t level);
#endif
