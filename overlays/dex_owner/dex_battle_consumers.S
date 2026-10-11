/* 古いThumb callerのSP%8=4も許容し、C ABI境界だけ8byte整列する。 */
.syntax unified
.arch armv4t
.thumb
.section .text.dex_consumer_entries,"ax",%progbits
.balign 4
.global VegaDexBattleSeen
.type VegaDexBattleSeen,%function
.thumb_func
VegaDexBattleSeen:
    /* 14byteのSID窓がr1へ明示的なThumb continuationを渡す。 */
    mov lr,r1
    push {r4,lr}
    mov r4,sp
    movs r2,#7
    mov r3,sp
    bics r3,r2
    mov sp,r3
    bl VegaDexBattleSeenC
    mov sp,r4
    pop {r4,pc}
.size VegaDexBattleSeen,.-VegaDexBattleSeen
.balign 4
.global VegaDexBattleOfficialCount
.type VegaDexBattleOfficialCount,%function
.thumb_func
VegaDexBattleOfficialCount:
    push {r4,lr}
    mov r4,sp
    movs r2,#7
    mov r3,sp
    bics r3,r2
    mov sp,r3
    bl VegaDexBattleOfficialCountC
    mov sp,r4
    pop {r4,pc}
.size VegaDexBattleOfficialCount,.-VegaDexBattleOfficialCount
.section .note.GNU-stack,"",%progbits
