.syntax unified
.cpu arm7tdmi
.thumb

/*
 * Every Original trampoline reproduces exactly the bytes replaced at the
 * pinned CFRU-JP entry, then branches to the first untouched halfword.
 * The temporary push keeps r3 intact while loading an absolute continuation.
 */
.macro STAGE72_JUMP_CONTINUATION address
    push {r3}
    ldr r3, =\address
    mov r12, r3
    pop {r3}
    bx r12
.endm

.macro STAGE72_R3_ENTRY name, target
    .global \name
    .type \name, %function
    .thumb_func
\name:
    mov r3, r12
    push {r2}
    ldr r2, =\target
    mov r12, r2
    pop {r2}
    bx r12
    .size \name, .-\name
.endm

STAGE72_R3_ENTRY Stage72_EntryAbilityBattleEffects, Stage72_AbilityBattleEffects
STAGE72_R3_ENTRY Stage72_EntryDoesProtectionMoveBlockMove, Stage72_DoesProtectionMoveBlockMove
STAGE72_R3_ENTRY Stage72_EntryProtectAffects, Stage72_ProtectAffects
STAGE72_R3_ENTRY Stage72_EntryNonInvasiveCheckGrounding, Stage72_NonInvasiveCheckGrounding
STAGE72_R3_ENTRY Stage72_EntryTypeCalc, Stage72_TypeCalc
STAGE72_R3_ENTRY Stage72_EntryAITypeCalcPart, Stage72_AITypeCalcPart
STAGE72_R3_ENTRY Stage72_EntryCalcVisualBasePower, Stage72_CalcVisualBasePower
.ltorg

.macro STAGE72_FUNCTION name
    .global \name
    .type \name, %function
    .thumb_func
\name:
.endm

STAGE72_FUNCTION Stage72_OriginalAbilityBattleEffects
    push {r4, r5, r6, r7, lr}
    mov r7, r10
    mov r6, r9
    mov r5, r8
    mov lr, r11
    push {r5, r6, r7, lr}
    STAGE72_JUMP_CONTINUATION 0x090B6689
    .size Stage72_OriginalAbilityBattleEffects, .-Stage72_OriginalAbilityBattleEffects
    .ltorg

STAGE72_FUNCTION Stage72_OriginalProtectAffects
    push {r4, r5, r6, r7, lr}
    mov lr, r11
    mov r7, r10
    mov r5, r8
    mov r6, r9
    movs r4, #2
    STAGE72_JUMP_CONTINUATION 0x090BC1F5
    .size Stage72_OriginalProtectAffects, .-Stage72_OriginalProtectAffects
    .ltorg

STAGE72_FUNCTION Stage72_OriginalDoesProtectionMoveBlockMove
    push {r4, r5, r6, r7, lr}
    movs r4, r2
    mov lr, r10
    mov r7, r9
    mov r6, r8
    push {r6, r7, lr}
    STAGE72_JUMP_CONTINUATION 0x090BC4CD
    .size Stage72_OriginalDoesProtectionMoveBlockMove, .-Stage72_OriginalDoesProtectionMoveBlockMove
    .ltorg

STAGE72_FUNCTION Stage72_OriginalNonInvasiveCheckGrounding
    push {r3, r4, r5, r6, r7, lr}
    mov r7, r10
    mov r6, r9
    mov r5, r8
    mov lr, r11
    push {r5, r6, r7, lr}
    STAGE72_JUMP_CONTINUATION 0x090D4305
    .size Stage72_OriginalNonInvasiveCheckGrounding, .-Stage72_OriginalNonInvasiveCheckGrounding
    .ltorg

STAGE72_FUNCTION Stage72_OriginalTypeCalc
    push {r4, r5, r6, r7, lr}
    mov lr, r11
    mov r7, r10
    mov r6, r9
    mov r5, r8
    push {r5, r6, r7, lr}
    STAGE72_JUMP_CONTINUATION 0x090E66E1
    .size Stage72_OriginalTypeCalc, .-Stage72_OriginalTypeCalc
    .ltorg

STAGE72_FUNCTION Stage72_OriginalAITypeCalcPart
    push {r4, r5, r6, r7, lr}
    mov lr, r11
    mov r7, r10
    mov r6, r9
    mov r5, r8
    push {r5, r6, r7, lr}
    STAGE72_JUMP_CONTINUATION 0x090E5ED9
    .size Stage72_OriginalAITypeCalcPart, .-Stage72_OriginalAITypeCalcPart
    .ltorg

STAGE72_FUNCTION Stage72_OriginalCalcVisualBasePower
    push {r4, r5, r6, r7, lr}
    mov lr, r8
    push {lr}
    sub sp, #96
    mov r8, r3
    mov r3, sp
    STAGE72_JUMP_CONTINUATION 0x090E8071
    .size Stage72_OriginalCalcVisualBasePower, .-Stage72_OriginalCalcVisualBasePower
    .ltorg

STAGE72_FUNCTION Stage72_OriginalGetMoveTypeSpecialPostAbility
    push {r4, lr}
    lsls r4, r0, #1
    ldr r3, =0x090421F4
    adds r4, r4, r0
    STAGE72_JUMP_CONTINUATION 0x090E53BD
    .size Stage72_OriginalGetMoveTypeSpecialPostAbility, .-Stage72_OriginalGetMoveTypeSpecialPostAbility
    .ltorg

STAGE72_FUNCTION Stage72_OriginalGetMoveTypeSpecialPreAbility
    push {r3, r4, r5, r6, r7, lr}
    lsls r5, r0, #1
    ldr r3, =0x090421F4
    adds r5, r5, r0
    STAGE72_JUMP_CONTINUATION 0x090E59D9
    .size Stage72_OriginalGetMoveTypeSpecialPreAbility, .-Stage72_OriginalGetMoveTypeSpecialPreAbility
    .ltorg

STAGE72_FUNCTION Stage72_OriginalAdjustBasePower
    push {r4, r5, r6, r7, lr}
    mov r7, r10
    mov r5, r8
    mov lr, r11
    STAGE72_JUMP_CONTINUATION 0x090E3139
    .size Stage72_OriginalAdjustBasePower, .-Stage72_OriginalAdjustBasePower
    .ltorg

STAGE72_FUNCTION Stage72_OriginalCalculateBaseDamage
    push {r4, r5, r6, r7, lr}
    mov r7, r10
    mov r5, r8
    mov lr, r11
    STAGE72_JUMP_CONTINUATION 0x090E83DD
    .size Stage72_OriginalCalculateBaseDamage, .-Stage72_OriginalCalculateBaseDamage
    .ltorg

STAGE72_FUNCTION Stage72_OriginalGetExceptionMoveType
    push {r3, r4, r5, r6, r7, lr}
    mov lr, r11
    mov r7, r10
    mov r6, r9
    STAGE72_JUMP_CONTINUATION 0x090E541D
    .size Stage72_OriginalGetExceptionMoveType, .-Stage72_OriginalGetExceptionMoveType
    .ltorg

STAGE72_FUNCTION Stage72_OriginalGetMonExceptionMoveType
    push {r3, r4, r5, r6, r7, lr}
    mov lr, r9
    mov r7, r8
    lsls r2, r1, #1
    STAGE72_JUMP_CONTINUATION 0x090E579D
    .size Stage72_OriginalGetMonExceptionMoveType, .-Stage72_OriginalGetMonExceptionMoveType
    .ltorg

STAGE72_FUNCTION Stage72_OriginalAttacksThisTurn
    push {r3, r4, r5, r6, r7, lr}
    lsls r3, r1, #1
    ldr r2, =0x090421F4
    adds r3, r3, r1
    STAGE72_JUMP_CONTINUATION 0x090D6585
    .size Stage72_OriginalAttacksThisTurn, .-Stage72_OriginalAttacksThisTurn
    .ltorg

STAGE72_FUNCTION Stage72_OriginalCheckGrounding
    push {r4, r5, r6, lr}
    ldr r6, =0x02023D5C
    lsls r5, r0, #2
    ldr r2, [r6, r5]
    STAGE72_JUMP_CONTINUATION 0x090D4721
    .size Stage72_OriginalCheckGrounding, .-Stage72_OriginalCheckGrounding
    .ltorg

STAGE72_FUNCTION Stage72_OriginalCheckMonGrounding
    push {r4, r5, r6, lr}
    movs r2, #0
    ldr r5, =0x0803F355
    movs r1, #11
    STAGE72_JUMP_CONTINUATION 0x090D43DD
    .size Stage72_OriginalCheckMonGrounding, .-Stage72_OriginalCheckMonGrounding
    .ltorg

STAGE72_FUNCTION Stage72_OriginalCheckGroundingByDetails
    push {r4, r5, r6, lr}
    movs r4, r0
    movs r5, r2
    movs r0, r1
    STAGE72_JUMP_CONTINUATION 0x090D4465
    .size Stage72_OriginalCheckGroundingByDetails, .-Stage72_OriginalCheckGroundingByDetails
    .ltorg

STAGE72_FUNCTION Stage72_OriginalAISpecialTypeCalc
    push {r4, r5, r6, r7, lr}
    mov lr, r11
    mov r6, r9
    mov r5, r8
    STAGE72_JUMP_CONTINUATION 0x090E6281
    .size Stage72_OriginalAISpecialTypeCalc, .-Stage72_OriginalAISpecialTypeCalc
    .ltorg

STAGE72_FUNCTION Stage72_OriginalVisualTypeCalcPart
    push {r4, r5, r6, r7, lr}
    mov lr, r11
    mov r5, r8
    mov r7, r10
    STAGE72_JUMP_CONTINUATION 0x090E5A69
    .size Stage72_OriginalVisualTypeCalcPart, .-Stage72_OriginalVisualTypeCalcPart
    .ltorg

STAGE72_FUNCTION Stage72_OriginalAtk06TypeCalc
    push {r4, r5, r6, r7, lr}
    mov lr, r11
    mov r5, r8
    mov r7, r10
    STAGE72_JUMP_CONTINUATION 0x090E4A89
    .size Stage72_OriginalAtk06TypeCalc, .-Stage72_OriginalAtk06TypeCalc
    .ltorg

STAGE72_FUNCTION Stage72_OriginalAtk4ATypeCalc2
    push {r4, r5, r6, r7, lr}
    mov r7, r10
    mov r6, r9
    mov lr, r11
    STAGE72_JUMP_CONTINUATION 0x090E4789
    .size Stage72_OriginalAtk4ATypeCalc2, .-Stage72_OriginalAtk4ATypeCalc2
    .ltorg

STAGE72_FUNCTION Stage72_OriginalAtk49MoveEnd
    push {r4, r5, r6, r7, lr}
    mov lr, r11
    mov r6, r9
    mov r7, r10
    STAGE72_JUMP_CONTINUATION 0x090DF7A9
    .size Stage72_OriginalAtk49MoveEnd, .-Stage72_OriginalAtk49MoveEnd
    .ltorg

STAGE72_FUNCTION Stage72_OriginalSetMoveEffect2
    movs r3, #64
    push {r4, r5, r6, r7, lr}
    mov r6, r9
    mov lr, r11
    STAGE72_JUMP_CONTINUATION 0x0912B96D
    .size Stage72_OriginalSetMoveEffect2, .-Stage72_OriginalSetMoveEffect2
    .ltorg

STAGE72_FUNCTION Stage72_OriginalRecoverBasedOnSunlight
    movs r2, #88
    push {r4, r5, r6, lr}
    ldr r4, =0x02023CCB
    ldrb r0, [r4]
    STAGE72_JUMP_CONTINUATION 0x0910C1F5
    .size Stage72_OriginalRecoverBasedOnSunlight, .-Stage72_OriginalRecoverBasedOnSunlight
    .ltorg

STAGE72_FUNCTION Stage72_OriginalAtk01AccuracyCheck
    push {r4, r5, r6, r7, lr}
    mov r6, r9
    mov lr, r11
    mov r7, r10
    STAGE72_JUMP_CONTINUATION 0x090BCAE5
    .size Stage72_OriginalAtk01AccuracyCheck, .-Stage72_OriginalAtk01AccuracyCheck
    .ltorg

STAGE72_FUNCTION Stage72_OriginalAccuracyCalc
    push {r4, r5, r6, r7, lr}
    movs r4, r2
    movs r2, #88
    muls r2, r4
    STAGE72_JUMP_CONTINUATION 0x090BC691
    .size Stage72_OriginalAccuracyCalc, .-Stage72_OriginalAccuracyCalc
    .ltorg

STAGE72_FUNCTION Stage72_OriginalVisualAccuracyCalc
    push {r4, r5, r6, r7, lr}
    mov lr, r9
    mov r7, r8
    push {r7, lr}
    STAGE72_JUMP_CONTINUATION 0x090BC6C1
    .size Stage72_OriginalVisualAccuracyCalc, .-Stage72_OriginalVisualAccuracyCalc
    .ltorg

STAGE72_FUNCTION Stage72_OriginalVisualAccuracyCalcNoTarget
    push {r4, r5, r6, r7, lr}
    mov lr, r11
    mov r6, r9
    mov r5, r8
    STAGE72_JUMP_CONTINUATION 0x090BC7D5
    .size Stage72_OriginalVisualAccuracyCalcNoTarget, .-Stage72_OriginalVisualAccuracyCalcNoTarget
    .ltorg

STAGE72_FUNCTION Stage72_OriginalModifyGrowthInSun
    ldr r3, =0x02023CAA
    ldrh r3, [r3]
    push {r4, lr}
    cmp r3, #74
    STAGE72_JUMP_CONTINUATION 0x090C8EF9
    .size Stage72_OriginalModifyGrowthInSun, .-Stage72_OriginalModifyGrowthInSun
    .ltorg

.section .note.GNU-stack,"",%progbits
