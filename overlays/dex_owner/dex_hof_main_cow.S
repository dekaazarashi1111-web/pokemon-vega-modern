/* mode3 jump-table専用。元stock frameを保持しmainだけ既存COWへ接続する。 */
.syntax unified
.arch armv4t
.thumb

.section .text.hof_cow_entry,"ax",%progbits
.balign 4
.global VegaDexHofMainCow
.type VegaDexHofMainCow,%function
.thumb_func
VegaDexHofMainCow:
    /* stockが保存したr4,r5,r6,LRは元SPに残す。r6は旧vblank pointer。 */
    mov r4,sp
    mov r0,sp
    movs r1,#7
    bics r0,r1
    mov sp,r0
    bl VegaDexHofCowPrepare
    cmp r0,#1
    bne 1f
    movs r0,#0
    ldr r3,2f
    bl VegaDexHofCowCall
1:  bl VegaDexHofCowReturn
.global VegaDexHofCowCall
.type VegaDexHofCowCall,%function
.thumb_func
VegaDexHofCowCall:
    bx r3
.balign 4
2:  .word 0x094493A1
.size VegaDexHofMainCow,.-VegaDexHofMainCow

.section .text.hof_cow_return,"ax",%progbits
.balign 4
.global VegaDexHofCowReturn
.type VegaDexHofCowReturn,%function
.thumb_func
VegaDexHofCowReturn:
    ldr r1,1f
    str r6,[r1]
    mov sp,r4
    pop {r4,r5,r6}
    pop {r1}
    bx r1
.balign 4
1:  .word 0x03003150
.size VegaDexHofCowReturn,.-VegaDexHofCowReturn

.section .text.hof_cow_prepare,"ax",%progbits
.balign 4
.global VegaDexHofCowPrepare
.type VegaDexHofCowPrepare,%function
.thumb_func
VegaDexHofCowPrepare:
    push {r4,lr}
    movs r0,#10
    ldr r3,2f
    bl VegaDexHofCowCall
    ldr r1,3f
    cmp r0,r1
    bhi 1f
    movs r0,#10
    ldr r3,4f
    bl VegaDexHofCowCall
1:  bl VegaDexHofCowFirst
    pop {r4}
    pop {r1}
    bx r1
.balign 4
2:  .word 0x08054785
3:  .word 998
4:  .word 0x08054751
.size VegaDexHofCowPrepare,.-VegaDexHofCowPrepare

.section .text.hof_cow_first,"ax",%progbits
.balign 4
.global VegaDexHofCowFirst
.type VegaDexHofCowFirst,%function
.thumb_func
VegaDexHofCowFirst:
    push {r4,lr}
    ldr r4,2f
    movs r0,#28
    movs r1,r4
    movs r2,#248
    lsls r2,r2,#4
    ldr r3,3f
    bl VegaDexHofCowCall
    cmp r0,#1
    bne 1f
    ldr r3,4f
    bx r3
1:  movs r0,#255
    pop {r4}
    pop {r1}
    bx r1
.balign 4
2:  .word 0x0201C000
3:  .word 0x080DA949
4:  .word VegaDexHofCowSecond
.size VegaDexHofCowFirst,.-VegaDexHofCowFirst

.section .text.hof_cow_second,"ax",%progbits
.balign 4
.global VegaDexHofCowSecond
.type VegaDexHofCowSecond,%function
.thumb_func
VegaDexHofCowSecond:
    movs r0,#29
    movs r1,r4
    movs r2,#248
    lsls r2,r2,#4
    adds r1,r1,r2
    ldr r3,2f
    bl VegaDexHofCowCall
    cmp r0,#1
    beq 1f
    movs r0,#255
1:  pop {r4}
    pop {r1}
    bx r1
.balign 4
2:  .word 0x080DA949
.size VegaDexHofCowSecond,.-VegaDexHofCowSecond
.section .note.GNU-stack,"",%progbits
