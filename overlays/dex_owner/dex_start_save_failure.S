/* 保存失敗をmask0成功へ変換せず、invalid MDXで破壊的repairをしない。 */
#include DEX_SAVE_FAILURE_ENTRIES
.syntax unified
.arch armv4t
.thumb
.section .text.dex_save_failure,"ax",%progbits
.balign 4
.global VegaDexSaveResultGate
.type VegaDexSaveResultGate,%function
.thumb_func
VegaDexSaveResultGate:
    cmp r0,#255
    bne 3f
    /* invalid-liveはownerを破壊する専用SaveFailed画面を起動しない。 */
    push {r4,lr}
    mov r4,sp
    movs r2,#7
    mov r3,sp
    bics r3,r2
    mov sp,r3
    ldr r0,6f
    ldr r1,7f
    ldr r3,8f
    bl 2f
    mov sp,r4
    pop {r4}
    pop {r3}
    mov lr,r3
    cmp r0,#0
    beq 1f
    ldr r0,9f
    bx r0
3:  ldr r0,4f
    ldr r0,[r0]
    cmp r0,#0
    bne 1f
    ldr r0,5f
    bx r0
1:  /* STARTの実DoSaveだけ。HOF/linkの唯一の失敗通知は消さない。 */
    cmp r5,#0
    beq 11f
    cmp r5,#4
    bne 12f
11: ldr r0,13f
    ldr r0,[r0]
    ldr r1,14f
    cmp r0,r1
    bne 12f
    ldr r0,9f
    bx r0
12: ldr r0,10f
    bx r0
2:  bx r3
.balign 4
4: .word 0x030053DC
5: .word 0x080DB385
6: .word 0x0203DB40
7: .word 522
8: .word DEX_ENTRY_VegaDexValidate
9: .word 0x080DB36F
10:.word 0x080DB369
13:.word 0x03000FA4
14:.word 0x0806F131
.size VegaDexSaveResultGate,.-VegaDexSaveResultGate
.balign 4
.global VegaDexSafeWipeGate
.type VegaDexSafeWipeGate,%function
.thumb_func
VegaDexSafeWipeGate:
    push {r4,lr}
    mov r4,sp
    movs r2,#7
    mov r3,sp
    bics r3,r2
    mov sp,r3
    ldr r0,6f
    ldr r1,7f
    ldr r3,8f
    bl 2f
    mov sp,r4
    pop {r4}
    pop {r3}
    cmp r0,#0
    beq 1f
    movs r0,#0
    bx r3
1:  mov lr,r3
    /* 元入口8byteを同じregister/12byte frameへ復元して続行。 */
    push {r4,r5,lr}
    movs r5,#0
    ldr r0,9f
    ldr r1,[r0]
    ldr r3,10f
    bx r3
2:  bx r3
.balign 4
6: .word 0x0203DB40
7: .word 522
8: .word DEX_ENTRY_VegaDexValidate
9: .word 0x030053DC
10:.word 0x080F64B1
.size VegaDexSafeWipeGate,.-VegaDexSafeWipeGate
.section .note.GNU-stack,"",%progbits
