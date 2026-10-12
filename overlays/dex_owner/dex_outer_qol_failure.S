/* QOL adapter共通出口の特殊tail。既存8byte frameからcallerへ復帰する。 */
.syntax unified
.arch armv4t
.thumb
.section .text.dex_outer_qol_failure,"ax",%progbits
.balign 4
.global VegaDexOuterQolResultTail
.type VegaDexOuterQolResultTail,%function
.thumb_func
VegaDexOuterQolResultTail:
    cmp r0,#1
    beq 1f
    movs r0,#255
    ldr r1,2f
    strh r0,[r1]
1:  /* BLが更新したLRで戻らず、元adapterのframeを一度だけ復元する。 */
    pop {r4}
    pop {r1}
    bx r1
.balign 4
2: .word 0x03005470
.size VegaDexOuterQolResultTail,.-VegaDexOuterQolResultTail
.section .note.GNU-stack,"",%progbits
