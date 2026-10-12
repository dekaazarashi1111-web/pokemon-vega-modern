.syntax unified
.cpu arm7tdmi
.thumb

.macro STAGE76_JUMP_CONTINUATION address
    push {r3}
    ldr r3, =\address
    mov r12, r3
    pop {r3}
    bx r12
.endm

.macro STAGE76_R3_ENTRY name, target
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

STAGE76_R3_ENTRY Stage76_EntryAICalcDmg, Stage76_AICalcDmg
STAGE76_R3_ENTRY Stage76_EntryAIScriptPartner, Stage76_AIScriptPartner
.ltorg

.global Stage76_EntryRangeMoveCanHurtPartner
.type Stage76_EntryRangeMoveCanHurtPartner, %function
.thumb_func
Stage76_EntryRangeMoveCanHurtPartner:
    ldr r3, =Stage76_RangeMoveCanHurtPartner
    bx r3
.size Stage76_EntryRangeMoveCanHurtPartner, .-Stage76_EntryRangeMoveCanHurtPartner
.ltorg

.global Stage76_OriginalAICalcDmg
.type Stage76_OriginalAICalcDmg, %function
.thumb_func
Stage76_OriginalAICalcDmg:
    push {r4, r5, r6, r7, lr}
    mov lr, r11
    mov r6, r9
    mov r5, r8
    mov r7, r10
    push {r5, r6, r7, lr}
    STAGE76_JUMP_CONTINUATION 0x090E9E71
.size Stage76_OriginalAICalcDmg, .-Stage76_OriginalAICalcDmg
.ltorg

.global Stage76_OriginalAIScriptPartner
.type Stage76_OriginalAIScriptPartner, %function
.thumb_func
Stage76_OriginalAIScriptPartner:
    push {r4, r5, r6, r7, lr}
    mov lr, r11
    mov r7, r10
    mov r6, r9
    mov r5, r8
    push {r5, r6, r7, lr}
    STAGE76_JUMP_CONTINUATION 0x090A95F1
.size Stage76_OriginalAIScriptPartner, .-Stage76_OriginalAIScriptPartner
.ltorg

.global Stage76_OriginalRangeMoveCanHurtPartner
.type Stage76_OriginalRangeMoveCanHurtPartner, %function
.thumb_func
Stage76_OriginalRangeMoveCanHurtPartner:
    push {r4, r5, r6, lr}
    movs r4, r2
    movs r2, #88
    muls r2, r4
    STAGE76_JUMP_CONTINUATION 0x090B0051
.size Stage76_OriginalRangeMoveCanHurtPartner, .-Stage76_OriginalRangeMoveCanHurtPartner
.ltorg

.section .rodata.Stage76_BattleScripts, "a", %progbits
.balign 4
.global Stage76_BattleScriptSolarBeam
.type Stage76_BattleScriptSolarBeam, %object
Stage76_BattleScriptSolarBeam:
    .byte 0xF8
    .word Stage76_DispatchMegaSolSolarBeam
.size Stage76_BattleScriptSolarBeam, .-Stage76_BattleScriptSolarBeam

.balign 4
.global Stage76_BattleScriptMegaSolPopup
.type Stage76_BattleScriptMegaSolPopup, %object
Stage76_BattleScriptMegaSolPopup:
    /* call AbilityPopUp; pause 0x10; call revert; goto solar first-turn path */
    .byte 0x41
    .word 0x09001200
    .byte 0x39
    .hword 0x0010
    .byte 0x41
    .word 0x0900120F
    .byte 0x28
    .word 0x09005110
.size Stage76_BattleScriptMegaSolPopup, .-Stage76_BattleScriptMegaSolPopup
