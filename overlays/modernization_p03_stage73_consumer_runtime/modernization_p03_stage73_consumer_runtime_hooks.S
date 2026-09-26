.syntax unified
.cpu arm7tdmi
.thumb

.macro STAGE73_JUMP address
    push {r3}
    ldr r3, =\address
    mov r12, r3
    pop {r3}
    bx r12
.endm

.macro STAGE73_FUNCTION name
    .global \name
    .type \name, %function
    .thumb_func
\name:
.endm

STAGE73_FUNCTION Stage73_OriginalGetAllEggMoves
    push {r4, r5, r6, r7, lr}
    mov lr, r11
    mov r7, r10
    mov r6, r9
    mov r5, r8
    push {r5, r6, r7, lr}
    STAGE73_JUMP 0x090EB97D
    .size Stage73_OriginalGetAllEggMoves, .-Stage73_OriginalGetAllEggMoves
    .ltorg

STAGE73_FUNCTION Stage73_OriginalCollectionApplySelectedForm
    push {r4, lr}
    ldr r3, =0x0203F720
    ldrh r0, [r3, #10]
    ldr r3, =0x02036FF4
    STAGE73_JUMP 0x09405BDD
    .size Stage73_OriginalCollectionApplySelectedForm, .-Stage73_OriginalCollectionApplySelectedForm
    .ltorg

.section .note.GNU-stack,"",%progbits
