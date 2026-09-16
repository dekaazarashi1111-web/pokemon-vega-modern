.syntax unified
.cpu arm7tdmi
.thumb

.macro STAGE78_CALL_ABSOLUTE address
    ldr r3, =\address
    bl .Lstage78_call_r3
.endm

.section .text.Stage78Entries, "ax", %progbits
.align 2

.global Stage78_EntryFindMonAbsorberActive
.type Stage78_EntryFindMonAbsorberActive, %function
.thumb_func
Stage78_EntryFindMonAbsorberActive:
    movs r3, #149
    lsls r3, r3, #1
    mov r11, r3
    movs r1, r6
    movs r0, r5
    /* AAPCS public-call boundary: keep SP 8-byte aligned. */
    push {r3, lr}
    STAGE78_CALL_ABSOLUTE 0x090B0971
    movs r2, r6
    movs r1, r5
    bl Stage78_ActiveAbsorberAbility
    pop {r2, r3}
    mov lr, r3
    mov r3, r11
    ldr r2, =0x090A03F5
    bx r2
.size Stage78_EntryFindMonAbsorberActive, .-Stage78_EntryFindMonAbsorberActive
.ltorg

.global Stage78_EntryFindMonAbsorberParty
.type Stage78_EntryFindMonAbsorberParty, %function
.thumb_func
Stage78_EntryFindMonAbsorberParty:
    mov r3, r12
    push {r3, lr}
    movs r0, r6
    STAGE78_CALL_ABSOLUTE 0x090DA23D
    movs r1, r6
    bl Stage78_PartyAbsorberAbility
    movs r7, r0
    pop {r1, r2}
    mov r8, r1
    mov lr, r2
    ldrh r3, [r4, #54]
    ldr r2, =0x090A0433
    bx r2
.size Stage78_EntryFindMonAbsorberParty, .-Stage78_EntryFindMonAbsorberParty
.ltorg

.Lstage78_call_r3:
    bx r3
