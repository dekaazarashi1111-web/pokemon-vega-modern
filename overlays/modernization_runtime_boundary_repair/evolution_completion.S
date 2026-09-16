/* Thumb-v4T shim at 0x080425BC, called only after the native successful
 * evolution species commit. Preserve the original CalculateMonStats call.
 * ItemEvolutionRemoval consumes only the condition selected by CFRU's flag.
 * No host test, callback spoofing, cancellation path, or ROM-at-runtime patch. */
.syntax unified
.cpu arm7tdmi
.thumb
.balign 4
.global evolution_completion
.thumb_func
evolution_completion:
    push {r4, lr}
    movs r4, r0
    ldr r3, .Lremove
    bl .Lcall_r3
    movs r0, r4
    ldr r3, .Lstats
    bl .Lcall_r3
    pop {r4, pc}
.Lcall_r3:
    bx r3
    .hword 0x46C0 /* explicit Thumb NOP: identical GNU/LLVM alignment */
.Lremove: .word 0x090FB631
.Lstats: .word 0x0803DBE9
