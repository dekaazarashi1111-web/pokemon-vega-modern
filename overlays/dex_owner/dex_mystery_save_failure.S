/* Mystery Giftの署名済みcallerだけ。mutable latchや自動retryは導入しない。 */
.syntax unified
.arch armv4t
.thumb
.section .text.dex_mystery_failure,"ax",%progbits
.balign 4
.global VegaDexMysterySaveResultGate
.type VegaDexMysterySaveResultGate,%function
.thumb_func
VegaDexMysterySaveResultGate:
    cmp r5,#0
    bne 4f
    /* innerの12byte frame、outer QOLの8byte frameを共に確認。 */
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
    /* main成功＋bit31単独のみ。外側が実write/readbackを完了する。 */
    ldr r3,8f
    bx r3
3:  ldr r3,9f
    bx r3
4:  ldr r3,10f
    bx r3
.balign 4
5: .word 0x0937767B
6: .word 0x08143287
7: .word 0x030053DC
8: .word 0x080DB385
9: .word 0x080DB36F
10:.word 0x095FFEF1
.size VegaDexMysterySaveResultGate,.-VegaDexMysterySaveResultGate
.balign 4
.global VegaDexMysterySaveMessageTail
.type VegaDexMysterySaveMessageTail,%function
.thumb_func
VegaDexMysterySaveMessageTail:
    /* 元SaveOnMysteryGiftMenuのr4と8byte caller frameを保持。
     * 通常関数のreturnではなく元state++へ復帰する特殊tail。 */
    ldr r0,4f
    ldrh r0,[r0]
    cmp r0,#1
    bne 1f
    ldr r0,5f
    b 2f
1:  ldr r0,6f
2:  ldr r3,7f
    bl 3f
    ldr r3,8f
    bx r3
3:  bx r3
.balign 4
4: .word 0x03005470
5: .word 0x0843074C
6: .word 0x083E045B
7: .word 0x08142C09
8: .word 0x081432A1
.size VegaDexMysterySaveMessageTail,.-VegaDexMysterySaveMessageTail
.section .note.GNU-stack,"",%progbits
