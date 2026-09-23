.syntax unified
.cpu arm7tdmi
.thumb
.section .text
.balign 4
.global pr16_cfru_normal_entry
.type pr16_cfru_normal_entry,%function
.thumb_func
pr16_cfru_normal_entry:
    ldr r3, [pc, #0]
    bx r3
    .word 0x09377729
.size pr16_cfru_normal_entry, .-pr16_cfru_normal_entry
