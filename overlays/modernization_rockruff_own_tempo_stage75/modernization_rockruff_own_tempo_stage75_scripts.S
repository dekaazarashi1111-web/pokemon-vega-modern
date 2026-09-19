.syntax unified
.cpu arm7tdmi
.thumb

.macro STAGE75_CALLNATIVE target
    .byte 0x23
    .word \target + 1
.endm

.macro STAGE75_MSGBOX target
    .byte 0x0F, 0x00
    .word \target
    .byte 0x09, 0x04
.endm

.macro STAGE75_COMPARE variable, value
    .byte 0x21
    .hword \variable, \value
.endm

.macro STAGE75_BRANCH condition, target
    .byte 0x06, \condition
    .word \target
.endm

.macro STAGE75_GOTO target
    .byte 0x05
    .word \target
.endm

.macro STAGE75_SPECIAL value
    .byte 0x25
    .hword \value
.endm

.macro STAGE75_EXPORT name
    .balign 4
    .global \name
    .type \name, %object
\name:
.endm

.macro STAGE75_FUNCTION name
    .balign 2
    .global \name
    .type \name, %function
    .thumb_func
\name:
.endm

.section .text.Stage75Trampolines,"ax",%progbits

STAGE75_FUNCTION Stage75_OriginalGetEggSpecies
    push {r4, r5, r6, r7, lr}
    mov r7, r8
    push {r7}
    lsls r0, r0, #16
    ldr r3, =0x08044F3D
    bx r3
    .size Stage75_OriginalGetEggSpecies, .-Stage75_OriginalGetEggSpecies
    .ltorg

STAGE75_FUNCTION Stage75_OriginalGetEggMoves
    push {r4, r5, r6, r7, lr}
    mov r7, r8
    push {r7}
    mov r8, r1
    ldr r3, =0x080451F5
    bx r3
    .size Stage75_OriginalGetEggMoves, .-Stage75_OriginalGetEggMoves
    .ltorg

.section .rodata.Stage75Scripts,"a",%progbits

STAGE75_EXPORT Stage75_ItemScript
    .byte 0x6A
    STAGE75_CALLNATIVE 0x092CFFB0
    STAGE75_COMPARE 0x800D, 1
    STAGE75_BRANCH 1, Stage75_ModeMenuScript
    STAGE75_GOTO 0x092D09F8
    .size Stage75_ItemScript, .-Stage75_ItemScript

STAGE75_EXPORT Stage75_ModeMenuScript
    STAGE75_CALLNATIVE Stage75_OpenArchiveModeMenu
    STAGE75_COMPARE 0x800D, 5
    STAGE75_BRANCH 1, Stage75_FinishScript
    .byte 0x27
    STAGE75_COMPARE 0x800D, 0
    STAGE75_BRANCH 1, 0x092D07A0
    STAGE75_COMPARE 0x800D, 1
    STAGE75_BRANCH 1, 0x092D08FC
    STAGE75_COMPARE 0x800D, 2
    STAGE75_BRANCH 1, 0x092D0818
    STAGE75_COMPARE 0x800D, 3
    STAGE75_BRANCH 1, Stage75_MachineGateScript
    STAGE75_COMPARE 0x800D, 4
    STAGE75_BRANCH 1, Stage75_TutorGateScript
    STAGE75_GOTO Stage75_FinishScript
    .size Stage75_ModeMenuScript, .-Stage75_ModeMenuScript

STAGE75_EXPORT Stage75_MachineGateScript
    .byte 0x2B
    .hword 0x082C
    STAGE75_COMPARE 0x800D, 1
    STAGE75_BRANCH 1, Stage75_MachineEntryScript
    STAGE75_MSGBOX 0x0953A870
    STAGE75_GOTO Stage75_FinishScript
    .size Stage75_MachineGateScript, .-Stage75_MachineGateScript

STAGE75_EXPORT Stage75_TutorGateScript
    .byte 0x2B
    .hword 0x082C
    STAGE75_COMPARE 0x800D, 1
    STAGE75_BRANCH 1, Stage75_TutorEntryScript
    STAGE75_MSGBOX 0x0953A870
    STAGE75_GOTO Stage75_FinishScript
    .size Stage75_TutorGateScript, .-Stage75_TutorGateScript

STAGE75_EXPORT Stage75_MachineEntryScript
    STAGE75_CALLNATIVE Stage75_SetMachineMode
    STAGE75_GOTO Stage75_MachineSelectScript
    .size Stage75_MachineEntryScript, .-Stage75_MachineEntryScript

STAGE75_EXPORT Stage75_MachineSelectScript
    STAGE75_MSGBOX 0x0953A83C
    STAGE75_SPECIAL 0x00DB
    .byte 0x27
    STAGE75_COMPARE 0x8004, 6
    STAGE75_BRANCH 4, Stage75_FinishScript
    STAGE75_SPECIAL 0x0148
    STAGE75_COMPARE 0x800D, 1
    STAGE75_BRANCH 1, Stage75_MachineEggErrorScript
    STAGE75_COMPARE 0x8005, 0
    STAGE75_BRANCH 1, Stage75_MachineNoMovesScript
    STAGE75_CALLNATIVE Stage75_PrepareMachinePages
    STAGE75_COMPARE 0x800D, 0
    STAGE75_BRANCH 1, Stage75_MachineNoMovesScript
    STAGE75_COMPARE 0x800D, 1
    STAGE75_BRANCH 1, Stage75_MachinePageReadyScript
    STAGE75_GOTO Stage75_MachineChoosePageScript
    .size Stage75_MachineSelectScript, .-Stage75_MachineSelectScript

STAGE75_EXPORT Stage75_MachineChoosePageScript
    STAGE75_CALLNATIVE Stage75_OpenMachinePageMenu
    STAGE75_COMPARE 0x800D, 0xFFFE
    STAGE75_BRANCH 1, Stage75_FinishScript
    .byte 0x27
    STAGE75_CALLNATIVE Stage75_CommitMachinePage
    STAGE75_COMPARE 0x800D, 0
    STAGE75_BRANCH 1, Stage75_FinishScript
    STAGE75_CALLNATIVE Stage75_SelectedMachinePageHasMoves
    STAGE75_COMPARE 0x800D, 0
    STAGE75_BRANCH 1, Stage75_MachinePageNoMovesScript
    STAGE75_GOTO Stage75_MachineTeachScript
    .size Stage75_MachineChoosePageScript, .-Stage75_MachineChoosePageScript

STAGE75_EXPORT Stage75_MachinePageReadyScript
    STAGE75_CALLNATIVE Stage75_SelectedMachinePageHasMoves
    STAGE75_COMPARE 0x800D, 0
    STAGE75_BRANCH 1, Stage75_MachineNoMovesScript
    STAGE75_GOTO Stage75_MachineTeachScript
    .size Stage75_MachinePageReadyScript, .-Stage75_MachinePageReadyScript

STAGE75_EXPORT Stage75_MachineTeachScript
    STAGE75_SPECIAL 0x00E0
    .byte 0x27
    STAGE75_COMPARE 0x8004, 0
    STAGE75_BRANCH 1, Stage75_MachineEntryScript
    STAGE75_GOTO Stage75_FinishScript
    .size Stage75_MachineTeachScript, .-Stage75_MachineTeachScript

STAGE75_EXPORT Stage75_MachineEggErrorScript
    STAGE75_MSGBOX 0x0953A864
    STAGE75_GOTO Stage75_MachineEntryScript
    .size Stage75_MachineEggErrorScript, .-Stage75_MachineEggErrorScript

STAGE75_EXPORT Stage75_MachineNoMovesScript
    STAGE75_MSGBOX 0x0953A850
    STAGE75_GOTO Stage75_MachineEntryScript
    .size Stage75_MachineNoMovesScript, .-Stage75_MachineNoMovesScript

STAGE75_EXPORT Stage75_MachinePageNoMovesScript
    STAGE75_MSGBOX 0x0953A888
    STAGE75_GOTO Stage75_MachineChoosePageScript
    .size Stage75_MachinePageNoMovesScript, .-Stage75_MachinePageNoMovesScript

STAGE75_EXPORT Stage75_TutorEntryScript
    STAGE75_CALLNATIVE Stage75_SetTutorMode
    STAGE75_GOTO Stage75_TutorSelectScript
    .size Stage75_TutorEntryScript, .-Stage75_TutorEntryScript

STAGE75_EXPORT Stage75_TutorSelectScript
    STAGE75_MSGBOX 0x0953A83C
    STAGE75_SPECIAL 0x00DB
    .byte 0x27
    STAGE75_COMPARE 0x8004, 6
    STAGE75_BRANCH 4, Stage75_FinishScript
    STAGE75_SPECIAL 0x0148
    STAGE75_COMPARE 0x800D, 1
    STAGE75_BRANCH 1, Stage75_TutorEggErrorScript
    STAGE75_COMPARE 0x8005, 0
    STAGE75_BRANCH 1, Stage75_TutorNoMovesScript
    STAGE75_SPECIAL 0x00E0
    .byte 0x27
    STAGE75_COMPARE 0x8004, 0
    STAGE75_BRANCH 1, Stage75_TutorEntryScript
    STAGE75_GOTO Stage75_FinishScript
    .size Stage75_TutorSelectScript, .-Stage75_TutorSelectScript

STAGE75_EXPORT Stage75_TutorEggErrorScript
    STAGE75_MSGBOX 0x0953A864
    STAGE75_GOTO Stage75_TutorEntryScript
    .size Stage75_TutorEggErrorScript, .-Stage75_TutorEggErrorScript

STAGE75_EXPORT Stage75_TutorNoMovesScript
    STAGE75_MSGBOX 0x0953A850
    STAGE75_GOTO Stage75_TutorEntryScript
    .size Stage75_TutorNoMovesScript, .-Stage75_TutorNoMovesScript

STAGE75_EXPORT Stage75_FinishScript
    STAGE75_CALLNATIVE Stage75_ResetMode
    .byte 0x6C, 0x02
    .size Stage75_FinishScript, .-Stage75_FinishScript

.section .note.GNU-stack,"",%progbits
