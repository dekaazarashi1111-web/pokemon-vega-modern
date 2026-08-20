.syntax unified
.thumb

/*
 * T09のdisplaced-register ABIを保ち、Vega固定prefixを含む全Speciesを
 * Stage39の3-byte canonical level-up表へ送る。処理後は元epilogueへ戻る。
 */
.section .text.MoveDistributionV4_GiveBoxMonInitialMovesetDispatch, "ax", %progbits
.global MoveDistributionV4_GiveBoxMonInitialMovesetDispatch
.type MoveDistributionV4_GiveBoxMonInitialMovesetDispatch, %function
.thumb_func
MoveDistributionV4_GiveBoxMonInitialMovesetDispatch:
    mov r0, r8
    adds r1, r4, #0
    mov r2, r10
    bl MoveDistributionV4_GiveInitialMoves
    ldr r3, 1f
    bx r3
    .align 2
1:
    .word 0x0803E1D9
.size MoveDistributionV4_GiveBoxMonInitialMovesetDispatch, . - MoveDistributionV4_GiveBoxMonInitialMovesetDispatch
