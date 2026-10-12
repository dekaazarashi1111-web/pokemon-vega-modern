/* HOF保存callerだけ。失敗を明示し、破壊的共通画面/自動再保存へ入らない。 */
.syntax unified
.arch armv4t
.thumb
.section .text.dex_hof_failure,"ax",%progbits
.balign 4
.global VegaDexHofSaveResultGate
.type VegaDexHofSaveResultGate,%function
.thumb_func
VegaDexHofSaveResultGate:
    cmp r5,#3
    bne 4f
    ldr r1,[sp,#8]
    ldr r2,5f
    cmp r1,r2
    bne 4f
    ldr r1,[sp,#16]
    ldr r2,6f
    cmp r1,r2
    bne 4f
    cmp r0,#255
    beq 3f
    ldr r1,7f
    ldr r1,[r1]
    cmp r1,#0
    beq 4f
    /* sector31だけのstale bitは実outer write/readbackへ渡す。clearしない。 */
    cmp r0,#0
    bne 3f
    movs r2,#1
    lsls r2,r2,#31
    cmp r1,r2
    bne 3f
    ldr r3,8f
    bx r3
3:  ldr r3,9f
    bx r3
4:  ldr r3,10f
    bx r3
.balign 4
5: .word 0x0937767B
6: .word 0x080F3195
7: .word 0x030053DC
8: .word 0x080DB385
9: .word 0x080DB36F
10:.word 0x09FFFBA9
.size VegaDexHofSaveResultGate,.-VegaDexHofSaveResultGate

.balign 4
.global VegaDexHofSaveNotifyTail
.type VegaDexHofSaveNotifyTail,%function
.thumb_func
VegaDexHofSaveNotifyTail:
    /* 元taskのframe8/r4=taskIdは維持。outerまで終わったattemptだけ読む。 */
    ldr r0,5f
    ldrh r0,[r0]
    cmp r0,#1
    bne 1f
    movs r0,#48
    ldr r3,6f
    bl 4f
    ldr r1,7f
    lsls r0,r4,#2
    ldr r3,8f
    bx r3
1:  /* 原callerのr5を退避し、既存windowだけへ同期描画。 */
    push {r5,r6}
    mov r5,sp
    mov r0,sp
    movs r1,#7
    bics r0,r1
    mov sp,r0
    sub sp,#16
    movs r0,#0
    movs r1,#17
    ldr r3,9f
    bl 4f
    movs r0,#0
    str r0,[sp]
    movs r0,#2
    str r0,[sp,#4]
    movs r0,#1
    str r0,[sp,#8]
    movs r0,#3
    str r0,[sp,#12]
    movs r0,#0
    movs r1,#2
    ldr r2,10f
    movs r3,#0
    ldr r6,11f
    bl 3f
    movs r0,#0
    movs r1,#3
    ldr r3,12f
    bl 4f
    mov sp,r5
    pop {r5,r6}
    ldr r1,7f
    lsls r0,r4,#2
    adds r0,r0,r4
    lsls r0,r0,#3
    adds r0,r0,r1
    ldr r1,13f
    str r1,[r0]
    ldr r3,14f
    bx r3
3:  bx r6
4:  bx r3
.balign 4
5: .word 0x03005470
6: .word 0x08071A71
7: .word 0x030050D0
8: .word 0x080F319F
9: .word 0x08004429
10:.word 0x083E045B
11:.word 0x080F7D29
12:.word 0x08003EED
13:.word VegaDexHofSaveFailureWait
14:.word 0x080F31AD
.size VegaDexHofSaveNotifyTail,.-VegaDexHofSaveNotifyTail

.balign 4
.global VegaDexHofSaveFailureWait
.type VegaDexHofSaveFailureWait,%function
.thumb_func
VegaDexHofSaveFailureWait:
    ldr r1,1f
    ldrh r1,[r1]
    movs r2,#1
    tst r1,r2
    beq 2f
    ldr r3,3f
    bx r3
2:  bx lr
.balign 4
1: .word 0x0300315E
3: .word 0x080F31F5
.size VegaDexHofSaveFailureWait,.-VegaDexHofSaveFailureWait
.section .note.GNU-stack,"",%progbits
