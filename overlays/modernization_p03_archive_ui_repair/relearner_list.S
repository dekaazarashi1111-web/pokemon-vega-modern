.syntax unified
.cpu arm7tdmi
.thumb
.section .text,"ax",%progbits
.global Stage82_RelearnerList
.type Stage82_RelearnerList,%function
.thumb_func
/* Keep the native JP state layout, selected party byte 0x1e3 and move IDs
 * 0xe8. Relocate only menu items and 16-byte names past the native 0x9f0
 * allocation. The paired allocation patch reserves 0xdd0 bytes.
 * No modern C struct is passed to the unmodified native scheduler. */
Stage82_RelearnerList:
    push {r4-r7,lr}
    sub sp, #12
    ldr r0, .Lstruct
    ldr r4, [r0]
    ldr r0, .Lparty_offset
    ldrb r0, [r4, r0]
    movs r1, #100
    muls r0, r1
    ldr r1, .Lparty
    adds r0, r0, r1
    str r0, [sp, #0]
    lsls r1, r4, #0
    adds r1, #0xe8
    ldr r3, .Lprovider
    bl .Lcall_r3
    /* Pinned providers own a 40-u16 output contract. Fail closed if their
     * returned count violates it; never expose an out-of-range menu. */
    cmp r0, #40
    bls .Lcount_ok
    movs r0, #0
.Lcount_ok:
    lsls r6, r0, #0
    str r6, [sp, #4]
    adds r0, #1
    strb r0, [r4, #0x1a]
    movs r5, #0
    movs r7, #0xb4
    lsls r7, r7, #4
    adds r7, r7, r4
.Lloop:
    cmp r5, r6
    bhs .Lcancel
    lsls r1, r5, #1
    adds r1, #0xe8
    ldrh r1, [r4, r1]
    lsls r1, r1, #4
    ldr r2, .Lnames
    adds r1, r1, r2
    /* Fixed-width copy avoids the original nine-byte StringCopy buffers. */
    lsls r0, r7, #0
    movs r2, #16
.Lcopy:
    ldrb r3, [r1]
    strb r3, [r0]
    adds r1, #1
    adds r0, #1
    subs r2, #1
    bne .Lcopy
    /* The pinned move-name records must contain EOS within 16 bytes. */
    movs r3, #0xff
    strb r3, [r7, #15]
    movs r0, #0x9f
    lsls r0, r0, #4
    adds r0, r0, r4
    lsls r1, r5, #3
    adds r0, r0, r1
    str r7, [r0]
    str r5, [r0, #4]
    adds r7, #16
    adds r5, #1
    b .Lloop
.Lcancel:
    movs r0, #0x9f
    lsls r0, r0, #4
    adds r0, r0, r4
    str r0, [sp, #8]
    lsls r1, r5, #3
    adds r0, r0, r1
    ldr r1, .Lcancel_name
    str r1, [r0]
    movs r1, #0xfe
    str r1, [r0, #4]
    /* nickname belongs to the selected party mon, not a candidate name */
    ldr r0, [sp, #0]
    movs r1, #2
    ldr r2, .Lstring1
    ldr r3, .Lmondata
    bl .Lcall_r3
    ldr r0, .Ltemplate
    ldr r1, .Ltemplate_ram
    movs r2, #6
.Ltemplate_copy:
    ldr r3, [r0]
    str r3, [r1]
    adds r0, #4
    adds r1, #4
    subs r2, #1
    bne .Ltemplate_copy
    ldr r1, .Ltemplate_ram
    ldr r0, [sp, #8]
    str r0, [r1]
    ldr r0, [sp, #4]
    adds r0, #1
    strh r0, [r1, #12]
    add sp, #12
    pop {r4-r7,pc}
.Lcall_r3:
    bx r3
.hword 0x46c0 /* Explicit Thumb NOP: identical GNU/LLVM alignment bytes. */
.balign 4, 0
.Lstruct: .word 0x0203aa2c
.Lparty_offset: .word 0x1e3
.Lparty: .word 0x020241e4
.Lprovider: .word 0x080432d1
.Lnames: .word 0x090453c8
.Lcancel_name: .word 0x083c5bc4
.Lstring1: .word 0x02021c4c
.Lmondata: .word 0x0803f355
.Ltemplate: .word 0x083c5c6c
.Ltemplate_ram: .word 0x03005ec0
.size Stage82_RelearnerList, .-Stage82_RelearnerList
