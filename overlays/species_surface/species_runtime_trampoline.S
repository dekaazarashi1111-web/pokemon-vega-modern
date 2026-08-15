.syntax unified
.thumb

/*
 * Enter after the native routine has already obtained Species and level.
 * IDs 0..411 execute the displaced packed-table instructions and immediately
 * resume the untouched Vega body.  Only appended IDs call the 3-byte decoder,
 * then reuse the native epilogue that unwinds the existing stack frame.
 */
.section .text.VegaSpeciesSurface_GiveBoxMonInitialMovesetDispatch, "ax", %progbits
.global VegaSpeciesSurface_GiveBoxMonInitialMovesetDispatch
.type VegaSpeciesSurface_GiveBoxMonInitialMovesetDispatch, %function
.thumb_func
VegaSpeciesSurface_GiveBoxMonInitialMovesetDispatch:
    ldr r3, 3f
    cmp r4, r3
    bhs 2f
    ldr r0, 4f
    lsls r6, r4, #2
    adds r0, r6, r0
    ldr r0, [r0]
    ldr r3, 5f
    bx r3
2:
    mov r0, r8
    adds r1, r4, #0
    mov r2, r10
    bl VegaSpeciesSurface_GiveBoxMonInitialMovesetAppended
    ldr r3, 6f
    bx r3
    .align 2
3:
    .word 412
4:
    .word 0x0821A1BC
5:
    .word 0x0803E17D
6:
    .word 0x0803E1D9
.size VegaSpeciesSurface_GiveBoxMonInitialMovesetDispatch, . - VegaSpeciesSurface_GiveBoxMonInitialMovesetDispatch
