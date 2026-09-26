/* 新規供給module用。GBA BIOS/libcへ依存しない有界byte fill。 */
.syntax unified
.cpu arm7tdmi
.thumb
.section .text.Pr16SupplyMemset,"ax",%progbits
.balign 4
.global Pr16SupplyMemset
.global memset
.type Pr16SupplyMemset,%function
.thumb_func
Pr16SupplyMemset:
 movs r3,r0
 cmp r2,#0
 beq 2f
1:
 strb r1,[r3]
 adds r3,#1
 subs r2,#1
 bne 1b
2:
 bx lr
.size Pr16SupplyMemset,.-Pr16SupplyMemset
.thumb_set memset,Pr16SupplyMemset
.section .note.GNU-stack,"",%progbits
