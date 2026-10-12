.syntax unified
.cpu arm7tdmi
.thumb

/*
 * Stage72の追加特性wrapperは、通常のGastro Acid / Neutralizing Gas /
 * Mold BreakerではCFRUがactive abilityを0へ退避するため自然に不発になる。
 * Battle Circusの全特性抑制だけはraw abilityを保持するので、この後段adapterで
 * Stage72 wrapperを迂回して、固定済みoriginal trampolineへ直接委譲する。
 *
 * 8-byte hookはStage72 veneerと同じくr3をscratch扱いにする。12-byte hookは
 * hook veneerが元r3をr12へ退避するので、通常経路ではStage72 Entryへそのまま
 * 渡し、抑制経路ではr3を復元してからoriginal trampolineへtail jumpする。
 */

.equ STAGE77_G_BATTLE_TYPE_FLAGS, 0x02022AAC
.equ STAGE77_G_BATTLE_CIRCUS_FLAGS, 0x0203DFBC

.macro STAGE77_DISPATCH_R3_CLOBBER name, normal_target, suppressed_target
    .global \name
    .type \name, %function
    .thumb_func
\name:
    ldr r3, =STAGE77_G_BATTLE_TYPE_FLAGS
    ldr r3, [r3]
    lsls r3, r3, #5              /* BATTLE_TYPE_BATTLE_CIRCUS bit 26 -> N */
    bpl 1f
    ldr r3, =STAGE77_G_BATTLE_CIRCUS_FLAGS
    ldr r3, [r3]
    cmp r3, #0                   /* ABILITY_SUPPRESSION is bit 31 */
    bpl 1f
    ldr r3, =\suppressed_target
    bx r3
1:
    ldr r3, =\normal_target
    bx r3
    .ltorg
    .size \name, .-\name
.endm

.macro STAGE77_DISPATCH_R3_IN_R12 name, normal_target, suppressed_target
    .global \name
    .type \name, %function
    .thumb_func
\name:
    ldr r3, =STAGE77_G_BATTLE_TYPE_FLAGS
    ldr r3, [r3]
    lsls r3, r3, #5              /* BATTLE_TYPE_BATTLE_CIRCUS bit 26 -> N */
    bpl 1f
    ldr r3, =STAGE77_G_BATTLE_CIRCUS_FLAGS
    ldr r3, [r3]
    cmp r3, #0                   /* ABILITY_SUPPRESSION is bit 31 */
    bpl 1f
    mov r3, r12                  /* restore the fourth argument */
    push {r2}
    ldr r2, =\suppressed_target
    mov r12, r2
    pop {r2}
    bx r12
1:
    /* Stage72 Entry restores r3 from the still-intact r12. */
    ldr r3, =\normal_target
    bx r3
    .ltorg
    .size \name, .-\name
.endm

.section .text.Stage77_RuntimeProbe, "ax", %progbits
.align 2
.global Stage77_RuntimeProbe
.type Stage77_RuntimeProbe, %function
.thumb_func
Stage77_RuntimeProbe:
    movs r0, #77
    bx lr
.size Stage77_RuntimeProbe, .-Stage77_RuntimeProbe

STAGE77_DISPATCH_R3_IN_R12 Stage77_DispatchAbilityBattleEffects, 0x0953410D, 0x0953417D
STAGE77_DISPATCH_R3_IN_R12 Stage77_DispatchProtectAffects, 0x09534125, 0x09534199
STAGE77_DISPATCH_R3_IN_R12 Stage77_DispatchDoesProtectionMoveBlockMove, 0x09534119, 0x095341B5
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchAccuracyCalc, 0x095331B1, 0x09534409
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchVisualAccuracyCalc, 0x095331F7, 0x09534421
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchVisualAccuracyCalcNoTarget, 0x0953323D, 0x09534439
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchAtk01AccuracyCheck, 0x09533175, 0x095343F1
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchModifyGrowthInSun, 0x09533281, 0x09534451
STAGE77_DISPATCH_R3_IN_R12 Stage77_DispatchNonInvasiveCheckGrounding, 0x09534131, 0x095341D1
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchCheckMonGrounding, 0x0953384D, 0x09534311
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchCheckGroundingByDetails, 0x095338A5, 0x0953432D
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchCheckGrounding, 0x095337B1, 0x095342F5
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchAttacksThisTurn, 0x09533769, 0x095342D9
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchAtk49MoveEnd, 0x09533F2D, 0x095343A5
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchAdjustBasePower, 0x095333D1, 0x09534279
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchAtk4ATypeCalc2, 0x09533E75, 0x0953438D
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchAtk06TypeCalc, 0x09533D8D, 0x09534375
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchGetMoveTypeSpecialPostAbility, 0x09533375, 0x09534241
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchGetExceptionMoveType, 0x09533689, 0x095342A9
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchGetMonExceptionMoveType, 0x0953370D, 0x095342C1
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchGetMoveTypeSpecialPreAbility, 0x095332DD, 0x0953425D
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchVisualTypeCalcPart, 0x09533A35, 0x0953435D
STAGE77_DISPATCH_R3_IN_R12 Stage77_DispatchAITypeCalcPart, 0x09534149, 0x09534209
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchAISpecialTypeCalc, 0x095339D9, 0x09534345
STAGE77_DISPATCH_R3_IN_R12 Stage77_DispatchTypeCalc, 0x0953413D, 0x095341ED
STAGE77_DISPATCH_R3_IN_R12 Stage77_DispatchCalcVisualBasePower, 0x09534155, 0x09534225
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchCalculateBaseDamage, 0x095334C5, 0x09534291
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchRecoverBasedOnSunlight, 0x09533FD1, 0x095343D5
STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchSetMoveEffect2, 0x09533EF5, 0x095343BD
