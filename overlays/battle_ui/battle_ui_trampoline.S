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

.section .text.VegaBattleUI_GuardHelpOpen, "ax", %progbits
.align 2
.global VegaBattleUI_GuardHelpOpen
.type VegaBattleUI_GuardHelpOpen, %function
.thumb_func
VegaBattleUI_GuardHelpOpen:
    /* This hook is reached only after the stock HELP callback has seen a new
     * L/R edge in HELP button mode.  During battle, skip the old full-screen
     * HELP so the same edge reaches CFRU's move-details controller. */
    ldr r3, 3f
    ldrb r3, [r3]
    lsls r3, r3, #30
    bmi 2f

    /* Outside battle, replay HelpSystem_IsSinglePlayer() and its two
     * following instructions, then continue the untouched field HELP path. */
    adr r1, 1f
    adds r1, #1
    mov lr, r1
    ldr r3, 4f
    bx r3
.align 2
1:
    lsls r0, r0, #24
    cmp r0, #0
    ldr r3, 5f
    bx r3

2:
    movs r0, #0
    ldr r3, 6f
    bx r3
.align 2
3:
    .word 0x03003569
4:
    .word 0x0812BC61
5:
    .word VEGA_UI_HELP_OPEN_CONTINUE_ADDRESS
6:
    .word VEGA_UI_HELP_OPEN_SUPPRESS_ADDRESS
.size VegaBattleUI_GuardHelpOpen, . - VegaBattleUI_GuardHelpOpen
