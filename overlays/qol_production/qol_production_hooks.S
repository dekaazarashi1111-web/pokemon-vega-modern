.syntax unified
.thumb

.section .text.VegaQolProductionHooks, "ax", %progbits
.align 2

.global VegaQolProduction_OriginalReadKeys
.type VegaQolProduction_OriginalReadKeys, %function
.thumb_func
VegaQolProduction_OriginalReadKeys:
    push {lr}
    ldr r0, =0x04000130
    ldrh r1, [r0]
    ldr r2, =0x000003ff
    ldr r3, =0x080005f1
    bx r3
.size VegaQolProduction_OriginalReadKeys, .-VegaQolProduction_OriginalReadKeys

.global VegaQolProduction_OriginalPrintSkillsPage
.type VegaQolProduction_OriginalPrintSkillsPage, %function
.thumb_func
VegaQolProduction_OriginalPrintSkillsPage:
    push {r4, r5, r6, lr}
    mov r6, r9
    mov r5, r8
    push {r5, r6}
    ldr r3, =0x081378bd
    bx r3
.size VegaQolProduction_OriginalPrintSkillsPage, .-VegaQolProduction_OriginalPrintSkillsPage

.global VegaQolProduction_OriginalTrySavingData
.type VegaQolProduction_OriginalTrySavingData, %function
.thumb_func
VegaQolProduction_OriginalTrySavingData:
    push {r4, r5, lr}
    lsls r0, r0, #24
    lsrs r5, r0, #24
    ldr r0, =0x03005044
    ldr r4, [r0]
    ldr r3, =0x080db357
    bx r3
.size VegaQolProduction_OriginalTrySavingData, .-VegaQolProduction_OriginalTrySavingData

.global VegaQolProduction_OriginalFlagSet
.type VegaQolProduction_OriginalFlagSet, %function
.thumb_func
VegaQolProduction_OriginalFlagSet:
    push {r4, lr}
    lsls r0, r0, #16
    lsrs r4, r0, #16
    movs r0, r4
    ldr r3, =0x0806de7d
    bx r3
.size VegaQolProduction_OriginalFlagSet, .-VegaQolProduction_OriginalFlagSet

.global VegaQolProduction_OriginalFlagClear
.type VegaQolProduction_OriginalFlagClear, %function
.thumb_func
VegaQolProduction_OriginalFlagClear:
    push {r4, lr}
    lsls r0, r0, #16
    lsrs r4, r0, #16
    movs r0, r4
    ldr r3, =0x0806dea5
    bx r3
.size VegaQolProduction_OriginalFlagClear, .-VegaQolProduction_OriginalFlagClear

/* Relocated daycare acceptance branch.  The original Japanese event prints
 * its success text and fanfare before GiveEgg, then clears the pending flag
 * even when a cross-store save fails.  This script performs the status-returning
 * special first and keeps every success-only command behind an explicit OK
 * branch.  Command bytes follow the pinned FireRed event-script ABI. */
.section .text.VegaQolProduction_DaycareReceiveScript, "ax", %progbits
.align 2
.global VegaQolProduction_DaycareReceiveScript
.type VegaQolProduction_DaycareReceiveScript, %object
VegaQolProduction_DaycareReceiveScript:
    .byte 0x26
    .hword 0x800d
    .hword 0x00b8
    .byte 0x21
    .hword 0x800d
    .hword 0x0000
    .byte 0x06, 0x01
    .word .Ldaycare_receive_success
    .byte 0xc7, 0x03
    .byte 0x67
    .word gVegaQolDaycarePersistFailedText
    .byte 0x04
    .word 0x08193f43
    .byte 0x6d
    .byte 0x6c, 0x02
.Ldaycare_receive_success:
    .byte 0xc7, 0x03
    .byte 0x67
    .word 0x081a5ae5
    .byte 0x04
    .word 0x08193f43
    .byte 0x31
    .hword 0x0101
    .byte 0x32, 0x6d
    .byte 0x0f, 0x00
    .word 0x081a5b00
    .byte 0x09, 0x04
    .byte 0x2a
    .hword 0x0266
    .byte 0x6c, 0x02
.size VegaQolProduction_DaycareReceiveScript, .-VegaQolProduction_DaycareReceiveScript

.section .text.VegaQolProductionHooks, "ax", %progbits
.align 2

.global VegaQolProduction_OriginalEggHatchCallback
.type VegaQolProduction_OriginalEggHatchCallback, %function
.thumb_func
VegaQolProduction_OriginalEggHatchCallback:
    push {r4, r5, r6, lr}
    mov r6, r10
    mov r5, r9
    mov r4, r8
    ldr r3, =0x080468c9
    bx r3
.size VegaQolProduction_OriginalEggHatchCallback, .-VegaQolProduction_OriginalEggHatchCallback

.global VegaQolProduction_OriginalDoNamingScreen
.type VegaQolProduction_OriginalDoNamingScreen, %function
.thumb_func
VegaQolProduction_OriginalDoNamingScreen:
    push {r4, r5, r6, r7, lr}
    mov r7, r8
    push {r7}
    mov r8, r1
    ldr r3, =0x0809d399
    bx r3
.size VegaQolProduction_OriginalDoNamingScreen, .-VegaQolProduction_OriginalDoNamingScreen

.global VegaQolProduction_OriginalPartyMenuTryEvolution
.type VegaQolProduction_OriginalPartyMenuTryEvolution, %function
.thumb_func
VegaQolProduction_OriginalPartyMenuTryEvolution:
    push {r4, r5, r6, r7, lr}
    lsls r0, r0, #24
    lsrs r5, r0, #24
    ldr r6, =0x0203b014
    ldr r3, =0x08127051
    bx r3
.size VegaQolProduction_OriginalPartyMenuTryEvolution, .-VegaQolProduction_OriginalPartyMenuTryEvolution

.global VegaQolProduction_FixInstantTextSpeedHook
.type VegaQolProduction_FixInstantTextSpeedHook, %function
.thumb_func
VegaQolProduction_FixInstantTextSpeedHook:
    cmp r5, #0x7f
    bne 1f
    movs r5, #1
1:
    ldr r0, =0x02020010
    movs r2, #0
    movs r1, #1
    strb r1, [r0, #27]
    ldr r3, =0x08002d15
    bx r3
.size VegaQolProduction_FixInstantTextSpeedHook, .-VegaQolProduction_FixInstantTextSpeedHook

.global VegaQolProduction_RunTextPrintersHook
.type VegaQolProduction_RunTextPrintersHook, %function
.thumb_func
VegaQolProduction_RunTextPrintersHook:
    bl VegaQolProduction_RunTextPrintersForInstantText
    /* The C adapter reproduces one exact stock tick for normal speed and for
     * every nonzero control state, so no mid-function continuation is used. */
    ldr r3, =0x08002e35
    bx r3
.size VegaQolProduction_RunTextPrintersHook, .-VegaQolProduction_RunTextPrintersHook

.global VegaQolProduction_EggStepHook
.type VegaQolProduction_EggStepHook, %function
.thumb_func
VegaQolProduction_EggStepHook:
    movs r1, r4
    bl VegaQolProduction_SubtractEggSteps
    str r0, [sp]
    movs r0, r4
    movs r1, #32
    ldr r3, =0x0804592d
    bx r3
.size VegaQolProduction_EggStepHook, .-VegaQolProduction_EggStepHook

.global VegaQolProduction_PssCallsiteHook
.type VegaQolProduction_PssCallsiteHook, %function
.thumb_func
VegaQolProduction_PssCallsiteHook:
    bl VegaQolProduction_PssHandleInputAdapter
    lsls r0, r0, #24
    lsrs r0, r0, #24
    ldr r3, =0x0808cd51
    bx r3
.size VegaQolProduction_PssCallsiteHook, .-VegaQolProduction_PssCallsiteHook

.global VegaQolProduction_ShouldEggHatchCallsiteHook
.type VegaQolProduction_ShouldEggHatchCallsiteHook, %function
.thumb_func
VegaQolProduction_ShouldEggHatchCallsiteHook:
    bl VegaQolProduction_ShouldEggHatchAdapter
    lsls r0, r0, #24
    cmp r0, #0
    ldr r3, =0x0806cf01
    bx r3
.size VegaQolProduction_ShouldEggHatchCallsiteHook, .-VegaQolProduction_ShouldEggHatchCallsiteHook

.global VegaQolProduction_EndWildBattleHook
.type VegaQolProduction_EndWildBattleHook, %function
.thumb_func
VegaQolProduction_EndWildBattleHook:
    push {lr}
    bl VegaQolProduction_ClearBattleAutoState
    sub sp, #4
    mov r1, sp
    movs r0, #0
    ldr r3, =0x0807f279
    bx r3
.size VegaQolProduction_EndWildBattleHook, .-VegaQolProduction_EndWildBattleHook

.global VegaQolProduction_OvalCharmHook
.type VegaQolProduction_OvalCharmHook, %function
.thumb_func
VegaQolProduction_OvalCharmHook:
    bl VegaQolProduction_ModifyBreedingScore
    movs r4, r0
    ldr r3, =0x0804448d
    bl .Lqol_call_r3
    ldr r3, =0x080458b3
    bx r3
.Lqol_call_r3:
    bx r3
.size VegaQolProduction_OvalCharmHook, .-VegaQolProduction_OvalCharmHook

/* Stage35 still used the vanilla fixed-width (ability * 19) description
 * lookup even though CFRU-JP had replaced the table at 0x0904cc28 with an
 * array of pointers.  Copying from the middle of that pointer table walked
 * through ROM until a stray 0xff and overwrote the Summary control block.
 * Keep the low-ROM BufferMonSkills ABI (r4=ability, r6=&summary pointer) and
 * select the expanded description through the actual pointer table. */
.global VegaQolProduction_SummaryAbilityDescriptionHook
.type VegaQolProduction_SummaryAbilityDescriptionHook, %function
.thumb_func
VegaQolProduction_SummaryAbilityDescriptionHook:
    ldr r0, [r6]
    ldr r2, =0x00003198
    adds r0, r0, r2
    lsls r1, r4, #2
    ldr r2, =0x0904cc28
    adds r1, r1, r2
    ldr r1, [r1]
    ldr r3, =0x08008901
    bl .Lqol_call_r3
    ldr r3, =0x08136f1b
    bx r3
.size VegaQolProduction_SummaryAbilityDescriptionHook, .-VegaQolProduction_SummaryAbilityDescriptionHook

.macro RESTORE_AND_BRANCH target
    pop {r4, r5, r6}
    pop {r3}
    mov lr, r3
    ldr r3, =\target
    bx r3
.endm

.global VegaQolProduction_ReusableTmCheck1
.type VegaQolProduction_ReusableTmCheck1, %function
.thumb_func
VegaQolProduction_ReusableTmCheck1:
    push {r4, r5, r6, lr}
    movs r4, r1
    movs r0, r1
    bl VegaQolProduction_IsReusableTm
    cmp r0, #0
    bne 1f
    movs r0, r4
    RESTORE_AND_BRANCH 0x0812580f
1:
    RESTORE_AND_BRANCH 0x08125815
.size VegaQolProduction_ReusableTmCheck1, .-VegaQolProduction_ReusableTmCheck1

.global VegaQolProduction_ReusableTmCheck2
.type VegaQolProduction_ReusableTmCheck2, %function
.thumb_func
VegaQolProduction_ReusableTmCheck2:
    push {r4, r5, r6, lr}
    movs r4, r1
    movs r0, r1
    bl VegaQolProduction_IsReusableTm
    cmp r0, #0
    bne 2f
    movs r0, r4
    RESTORE_AND_BRANCH 0x081258db
2:
    RESTORE_AND_BRANCH 0x081258e1
.size VegaQolProduction_ReusableTmCheck2, .-VegaQolProduction_ReusableTmCheck2

.global VegaQolProduction_ReusableTmCheck3
.type VegaQolProduction_ReusableTmCheck3, %function
.thumb_func
VegaQolProduction_ReusableTmCheck3:
    push {r4, r5, r6, lr}
    movs r5, r4
    movs r0, r4
    bl VegaQolProduction_IsReusableTm
    cmp r0, #0
    bne 3f
    movs r0, r5
    RESTORE_AND_BRANCH 0x081265cb
3:
    RESTORE_AND_BRANCH 0x081265d1
.size VegaQolProduction_ReusableTmCheck3, .-VegaQolProduction_ReusableTmCheck3

.pool
