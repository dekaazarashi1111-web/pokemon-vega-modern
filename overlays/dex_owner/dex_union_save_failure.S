/* Union Room Chatの署名済み保存callerと完了画面だけ。 */
.syntax unified
.arch armv4t
.thumb
.section .text.dex_union_failure,"ax",%progbits
.balign 4
.global VegaDexUnionSaveResultGate
.type VegaDexUnionSaveResultGate,%function
.thumb_func
VegaDexUnionSaveResultGate:
    cmp r5,#0
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
6: .word 0x08129A93
7: .word 0x030053DC
8: .word 0x080DB385
9: .word 0x080DB36F
10:.word 0x09FFFB29
.size VegaDexUnionSaveResultGate,.-VegaDexUnionSaveResultGate

.balign 4
.global VegaDexUnionSaveTextTail
.type VegaDexUnionSaveTextTail,%function
.thumb_func
VegaDexUnionSaveTextTail:
    /* 原関数のr6だけが文字列。handler17からのmessage9に限定する。
     * 元56byte frameのLRはsp+52。元wide-windowの幾何と描画を保持。 */
    cmp r7,#9
    bne 2f
    ldr r0,[sp,#52]
    ldr r1,4f
    cmp r0,r1
    bne 2f
    ldr r0,5f
    ldrh r0,[r0]
    cmp r0,#1
    beq 2f
    ldr r6,6f
2:  mov r0,r9
    lsls r1,r0,#8
    movs r0,#0
    movs r2,#0
    ldr r3,7f
    bl 3f
    mov r1,r8
    ldr r3,8f
    bx r3
3:  bx r3
.balign 4
4: .word 0x0812ACBF
5: .word 0x03005470
6: .word 0x083E045B
7: .word 0x08001D09
8: .word 0x0812AF71
.size VegaDexUnionSaveTextTail,.-VegaDexUnionSaveTextTail

.balign 4
.global VegaDexUnionSaveWaitTail
.type VegaDexUnionSaveWaitTail,%function
.thumb_func
VegaDexUnionSaveWaitTail:
    ldr r0,5f
    ldrh r0,[r0]
    cmp r0,#1
    bne 1f
    /* 成功は元SEとclear、state10/120frame待機を保持。 */
    movs r0,#48
    ldr r3,6f
    bl 4f
    ldr r3,7f
    bl 4f
    ldr r0,8f
    ldr r3,9f
    bx r3
1:  /* 失敗は音を鳴らさず新規A/Bまで表示し続ける。 */
    ldr r0,10f
    ldrh r0,[r0]
    movs r1,#3
    tst r0,r1
    beq 3f
    ldr r3,7f
    bl 4f
    ldr r0,8f
    ldr r1,[r0]
    movs r0,#12
    strh r0,[r1,#6]
3:  ldr r3,11f
    bx r3
4:  bx r3
.balign 4
5: .word 0x03005470
6: .word 0x08071A71
7: .word 0x0804B995
8: .word 0x0203B054
9: .word 0x08129AD1
10:.word 0x0300315E
11:.word 0x08129B3F
.size VegaDexUnionSaveWaitTail,.-VegaDexUnionSaveWaitTail
/* 元handler17だけ。同期的placeholder展開中の32byteをstackへ退避し、
 * 完了済みwindow bufferだけを残して、Factoryの全byteを復元する。 */
.balign 4
.global VegaDexUnionResultDisplayGuard
.type VegaDexUnionResultDisplayGuard,%function
.thumb_func
VegaDexUnionResultDisplayGuard:
    push {r4,r5,r6,lr}
    ldr r4,2f
    ldmia r4!,{r1,r2,r3,r5}
    push {r1,r2,r3,r5}
    ldmia r4!,{r1,r2,r3,r5}
    push {r1,r2,r3,r5}
    ldr r3,3f
    bl 1f
    subs r4,#16
    pop {r1,r2,r3,r5}
    stmia r4!,{r1,r2,r3,r5}
    subs r4,#32
    pop {r1,r2,r3,r5}
    stmia r4!,{r1,r2,r3,r5}
    .global VegaDexUnionResultDisplayRestored
    .type VegaDexUnionResultDisplayRestored,%function
    .thumb_func
VegaDexUnionResultDisplayRestored:
    pop {r4,r5,r6}
    pop {r1}
    bx r1
    .size VegaDexUnionResultDisplayRestored,6
1:  bx r3
.balign 4
2: .word 0x0203F2C0
3: .word 0x0812AC99
.size VegaDexUnionResultDisplayGuard,.-VegaDexUnionResultDisplayGuard
.section .note.GNU-stack,"",%progbits
