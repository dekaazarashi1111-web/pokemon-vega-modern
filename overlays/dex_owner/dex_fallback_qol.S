/* C契約と同じidle fallback。元post-QOLを一度だけ呼び、255の意味を保持。 */
#include DEX_FALLBACK_ENTRIES
.syntax unified
.arch armv4t
.thumb
.section .text.dex_fallback_qol,"ax",%progbits
.balign 4
.global VegaDexFallbackQolLoad
.type VegaDexFallbackQolLoad,%function
.thumb_func
VegaDexFallbackQolLoad:
    cmp r0,#3
    bne 1f
    ldr r3,L_previous
    bx r3
1:  push {r4,r5,r6,lr}
    mov r6,sp
    mov r1,sp
    movs r2,#7
    bics r1,r2
    mov sp,r1
    ldr r3,L_previous
    bl call_r3
    cmp r0,#255
    bne done
    ldr r1,L_status
    ldrh r1,[r1]
    cmp r1,#255
    bne done
    ldr r0,L_mdx
    ldr r1,L_mdx_size
    ldr r3,L_validate_mdx
    bl call_r3
    cmp r0,#0
    bne invalid
    movs r0,#31
    movs r1,#0x64
    ldr r5,L_buffer
    movs r2,r5
    ldr r3,L_read_size
    ldr r4,L_read
    bl call_r4
    ldrh r0,[r5,#4]
    cmp r0,#2
    bne invalid
    movs r0,r5
    movs r1,#128
    lsls r1,r1,#4
    ldr r3,L_validate_qol
    bl call_r3
    cmp r0,#0
    bne invalid
    ldr r1,L_factory_snapshot
    ldr r0,[r5,r1]
    ldr r2,L_fhst
    cmp r0,r2
    beq invalid
    subs r1,#16
    ldr r0,[r5,r1]
    lsls r0,r0,#13
    bmi invalid
    adr r1,L_empty
range:
    ldrh r0,[r1]
    ldrh r2,[r1,#2]
    adds r1,#4
    cmp r2,#0
    beq publish
    adds r0,r0,r5
scan:
    ldrb r3,[r0]
    cmp r3,#0
    bne invalid
    adds r0,#1
    subs r2,#1
    bne scan
    b range
publish:
    ldr r1,L_ledger
    movs r2,#128
    lsls r2,r2,#4
copy:
    ldrb r3,[r5]
    strb r3,[r1]
    adds r5,#1
    adds r1,#1
    subs r2,#1
    bne copy
    b failed_status
invalid:
    ldr r0,L_mdx
    ldr r1,L_mdx_size
    ldr r3,L_invalidate
    bl call_r3
    ldr r1,L_status
    movs r0,#2
    strh r0,[r1]
failed_status:
    movs r0,#255
 done:
    mov sp,r6
    pop {r4,r5,r6}
    pop {r1}
    bx r1
call_r3:
    bx r3
call_r4:
    bx r4
.balign 4
L_previous: .word FALLBACK_PREVIOUS_LOAD
L_status: .word 0x030053F0
L_mdx: .word 0x0203DB40
L_mdx_size: .word 522
L_validate_mdx: .word DEX_ENTRY_VegaDexValidate
L_buffer: .word 0x020399B0
L_read_size: .word 0xF9C
L_read: .word 0x081C2A55
L_validate_qol: .word FALLBACK_SHIFTED_SAVE_VALIDATE
L_factory_snapshot: .word 0x404
L_fhst: .word 0x54534846
L_ledger: .word 0x0203D000
L_invalidate: .word DEX_ENTRY_VegaDexInvalidateSession
L_empty:
    .hword 0x01B,1, 0x120,20, 0x163,32, 0x400,4, 0x664,8
    .hword 0x694,46, 0x76B,16, 0x814,2, 0x828,8, 0x914,2
    .hword 0x952,1, 0xB18,8, 0xB24,1, 0,0
.size VegaDexFallbackQolLoad,.-VegaDexFallbackQolLoad
.section .note.GNU-stack,"",%progbits
