.syntax unified
.thumb

.section .text.VegaBattleUI_InitMoveSelectionTrampoline, "ax", %progbits
.align 2
.global vega_battle_ui_init_move_selection_trampoline
.type vega_battle_ui_init_move_selection_trampoline, %function
.thumb_func
vega_battle_ui_init_move_selection_trampoline:
    /* Replay the 8 bytes replaced at InitMoveSelectionsVarsAndStrings. */
    push {r4-r7, lr}
    mov lr, r11
    mov r6, r9
    mov r7, r10
    ldr r3, 1f
    bx r3
.align 2
1:
    .word VEGA_UI_INIT_MOVE_SELECTION_CONTINUE_ADDRESS
.size vega_battle_ui_init_move_selection_trampoline, . - vega_battle_ui_init_move_selection_trampoline

.section .text.VegaBattleUI_HandleInputChooseMoveTrampoline, "ax", %progbits
.align 2
.global vega_battle_ui_handle_input_choose_move_trampoline
.type vega_battle_ui_handle_input_choose_move_trampoline, %function
.thumb_func
vega_battle_ui_handle_input_choose_move_trampoline:
    /* Replay the 8 bytes replaced at HandleInputChooseMove. */
    movs r2, #144
    push {r4-r7, lr}
    mov r6, r9
    mov r7, r10
    ldr r3, 2f
    bx r3
.align 2
2:
    .word VEGA_UI_HANDLE_CHOOSE_MOVE_CONTINUE_ADDRESS
.size vega_battle_ui_handle_input_choose_move_trampoline, . - vega_battle_ui_handle_input_choose_move_trampoline
