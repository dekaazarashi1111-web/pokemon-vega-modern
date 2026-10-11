/* CFRU wipe後、元28byte frameを保ったままstock continuationへ戻る。 */
#include DEX_LIFECYCLE_ENTRIES
.syntax unified
.arch armv4t
.thumb
.section .text.VegaDexNewGameTail,"ax",%progbits
.balign 4
.global VegaDexNewGameTail
.type VegaDexNewGameTail, %function
.thumb_func
VegaDexNewGameTail:
    push {r4, lr}
    mov r4, sp
    mov r3, sp
    movs r2, #7
    bics r3, r2
    mov sp, r3
    ldr r0, 2f
    ldr r1, 3f
    ldr r3, 4f
    bl 1f
    mov sp, r4
    pop {r4}
    pop {r3}
    ldr r0, 5f
    bx r0
1:
    bx r3
.balign 4
2: .word 0x0203DB40
3: .word 522
4: .word DEX_ENTRY_VegaDexInitNew
5: .word 0x0805432D
.size VegaDexNewGameTail, .-VegaDexNewGameTail
.section .note.GNU-stack,"",%progbits
