/* 59ac6688専用のshop表示後処理。可変RAMなし。旧canonicalは歴史原本。
 * pixels 0x280..0x3cf と user frame 0x214..0x21c を分離する。
 * 所有windowを追加/削除しない。stock frame getter/loader/drawerだけ呼ぶ。
 */
.syntax unified
.cpu arm7tdmi
.thumb
.section .text,"ax",%progbits
.balign 4
.global RS_PixelBase
.type RS_PixelBase,%function
.thumb_func
RS_PixelBase:
    movs r0, #0x28
    lsls r0, r0, #4
    bx lr
.size RS_PixelBase, .-RS_PixelBase
.balign 4
.global RS_DrawFrame
.type RS_DrawFrame,%function
.thumb_func
RS_DrawFrame:
    push {r4,r5,r6,lr}
    movs r4,r0
    movs r5,r1
    ldr r3,.Lgetter
    bl .Linvoke
    movs r1,r0
    movs r0,r4
    movs r2,#0xf0
    ldr r3,.Lloader
    bl .Linvoke
    movs r0,r4
    movs r1,r5
    ldr r3,.Ldrawer
    bl .Linvoke
    pop {r4,r5,r6,pc}
.Linvoke:
    bx r3
.balign 4
.Lgetter: .word 0x080f89cd
.Lloader: .word 0x081530e1
.Ldrawer: .word 0x080f7f7d
.size RS_DrawFrame, .-RS_DrawFrame
