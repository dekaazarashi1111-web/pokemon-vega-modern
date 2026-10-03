.syntax unified
.cpu arm7tdmi
.thumb

.macro STAGE74_CALLNATIVE target
    .byte 0x23
    .word \target + 1
.endm

.macro STAGE74_MSGBOX target
    .byte 0x0F, 0x00
    .word \target
    .byte 0x09, 0x04
.endm

.macro STAGE74_COMPARE variable, value
    .byte 0x21
    .hword \variable, \value
.endm

.macro STAGE74_BRANCH condition, target
    .byte 0x06, \condition
    .word \target
.endm

.macro STAGE74_GOTO target
    .byte 0x05
    .word \target
.endm

.macro STAGE74_SPECIAL value
    .byte 0x25
    .hword \value
.endm

.macro STAGE74_EXPORT name
    .balign 4
    .global \name
    .type \name, %object
\name:
.endm

.macro STAGE74_FUNCTION name
    .balign 2
    .global \name
    .type \name, %function
    .thumb_func
\name:
.endm

.section .text.Stage74OriginalBuildLearnableMoveset,"ax",%progbits

/* Exact 8-byte parent prologue replay, then resume at the first untouched op. */
STAGE74_FUNCTION Stage74_OriginalBuildLearnableMoveset
    push {r4, r5, r6, r7, lr}
    mov lr, r10
    mov r7, r9
    mov r6, r8
    push {r3}
    ldr r3, =0x091143C1
    mov r12, r3
    pop {r3}
    bx r12
    .size Stage74_OriginalBuildLearnableMoveset, .-Stage74_OriginalBuildLearnableMoveset
    .ltorg

.section .rodata.Stage74Scripts,"a",%progbits

/* Bag Move Memory entry.  Direct NPC remember/forget entries stay untouched. */
STAGE74_EXPORT Stage74_ItemScript
    .byte 0x6A                         /* lock */
    STAGE74_CALLNATIVE 0x092CFFB0     /* VegaMoveMemory_CheckContext */
    STAGE74_COMPARE 0x800D, 1
    STAGE74_BRANCH 1, Stage74_ModeMenuScript
    STAGE74_GOTO 0x092D09F8           /* existing context rejection */
    .size Stage74_ItemScript, .-Stage74_ItemScript

STAGE74_EXPORT Stage74_ModeMenuScript
    STAGE74_CALLNATIVE Stage74_OpenArchiveModeMenu
    STAGE74_COMPARE 0x800D, 5
    STAGE74_BRANCH 1, Stage74_FinishScript
    .byte 0x27                         /* waitstate */
    STAGE74_COMPARE 0x800D, 0
    STAGE74_BRANCH 1, 0x092D07A0      /* existing normal remember */
    STAGE74_COMPARE 0x800D, 1
    STAGE74_BRANCH 1, 0x092D08FC      /* existing forget */
    STAGE74_COMPARE 0x800D, 2
    STAGE74_BRANCH 1, 0x092D0818      /* existing egg mode */
    STAGE74_COMPARE 0x800D, 3
    STAGE74_BRANCH 1, Stage74_MachineGateScript
    STAGE74_COMPARE 0x800D, 4
    STAGE74_BRANCH 1, Stage74_TutorGateScript
    STAGE74_GOTO Stage74_FinishScript
    .size Stage74_ModeMenuScript, .-Stage74_ModeMenuScript

STAGE74_EXPORT Stage74_MachineGateScript
    .byte 0x2B
    .hword 0x082C                     /* Hall of Fame */
    STAGE74_COMPARE 0x800D, 1
    STAGE74_BRANCH 1, Stage74_MachineEntryScript
    STAGE74_MSGBOX Stage74_TextArchiveLocked
    STAGE74_GOTO Stage74_FinishScript
    .size Stage74_MachineGateScript, .-Stage74_MachineGateScript

STAGE74_EXPORT Stage74_TutorGateScript
    .byte 0x2B
    .hword 0x082C                     /* Hall of Fame */
    STAGE74_COMPARE 0x800D, 1
    STAGE74_BRANCH 1, Stage74_TutorEntryScript
    STAGE74_MSGBOX Stage74_TextArchiveLocked
    STAGE74_GOTO Stage74_FinishScript
    .size Stage74_TutorGateScript, .-Stage74_TutorGateScript

STAGE74_EXPORT Stage74_MachineEntryScript
    STAGE74_CALLNATIVE Stage74_SetMachineMode
    STAGE74_GOTO Stage74_MachineSelectScript
    .size Stage74_MachineEntryScript, .-Stage74_MachineEntryScript

STAGE74_EXPORT Stage74_MachineSelectScript
    STAGE74_MSGBOX Stage74_TextChooseMon
    STAGE74_SPECIAL 0x00DB            /* ChoosePartyMonForMoveRelearner */
    .byte 0x27
    STAGE74_COMPARE 0x8004, 6
    STAGE74_BRANCH 4, Stage74_FinishScript
    STAGE74_SPECIAL 0x0148            /* IsSelectedMonEgg */
    STAGE74_COMPARE 0x800D, 1
    STAGE74_BRANCH 1, Stage74_MachineEggErrorScript
    STAGE74_COMPARE 0x8005, 0         /* probe found no unknown archive move */
    STAGE74_BRANCH 1, Stage74_MachineNoMovesScript
    STAGE74_CALLNATIVE Stage74_PrepareMachinePages
    STAGE74_COMPARE 0x800D, 0
    STAGE74_BRANCH 1, Stage74_MachineNoMovesScript
    STAGE74_COMPARE 0x800D, 1
    STAGE74_BRANCH 1, Stage74_MachinePageReadyScript
    STAGE74_GOTO Stage74_MachineChoosePageScript
    .size Stage74_MachineSelectScript, .-Stage74_MachineSelectScript

STAGE74_EXPORT Stage74_MachineChoosePageScript
    STAGE74_CALLNATIVE Stage74_OpenMachinePageMenu
    STAGE74_COMPARE 0x800D, 0xFFFE
    STAGE74_BRANCH 1, Stage74_FinishScript
    .byte 0x27
    STAGE74_CALLNATIVE Stage74_CommitMachinePage
    STAGE74_COMPARE 0x800D, 0
    STAGE74_BRANCH 1, Stage74_FinishScript
    STAGE74_CALLNATIVE Stage74_SelectedMachinePageHasMoves
    STAGE74_COMPARE 0x800D, 0
    STAGE74_BRANCH 1, Stage74_MachinePageNoMovesScript
    STAGE74_GOTO Stage74_MachineTeachScript
    .size Stage74_MachineChoosePageScript, .-Stage74_MachineChoosePageScript

STAGE74_EXPORT Stage74_MachinePageReadyScript
    STAGE74_CALLNATIVE Stage74_SelectedMachinePageHasMoves
    STAGE74_COMPARE 0x800D, 0
    STAGE74_BRANCH 1, Stage74_MachineNoMovesScript
    STAGE74_GOTO Stage74_MachineTeachScript
    .size Stage74_MachinePageReadyScript, .-Stage74_MachinePageReadyScript

STAGE74_EXPORT Stage74_MachineTeachScript
    STAGE74_SPECIAL 0x00E0            /* TeachMoveRelearnerMove */
    .byte 0x27
    STAGE74_COMPARE 0x8004, 0
    STAGE74_BRANCH 1, Stage74_MachineEntryScript
    STAGE74_GOTO Stage74_FinishScript
    .size Stage74_MachineTeachScript, .-Stage74_MachineTeachScript

STAGE74_EXPORT Stage74_MachineEggErrorScript
    STAGE74_MSGBOX Stage74_TextEggRejected
    STAGE74_GOTO Stage74_MachineEntryScript
    .size Stage74_MachineEggErrorScript, .-Stage74_MachineEggErrorScript

STAGE74_EXPORT Stage74_MachineNoMovesScript
    STAGE74_MSGBOX Stage74_TextNoMoves
    STAGE74_GOTO Stage74_MachineEntryScript
    .size Stage74_MachineNoMovesScript, .-Stage74_MachineNoMovesScript

STAGE74_EXPORT Stage74_MachinePageNoMovesScript
    STAGE74_MSGBOX Stage74_TextPageNoMoves
    STAGE74_GOTO Stage74_MachineChoosePageScript
    .size Stage74_MachinePageNoMovesScript, .-Stage74_MachinePageNoMovesScript

STAGE74_EXPORT Stage74_TutorEntryScript
    STAGE74_CALLNATIVE Stage74_SetTutorMode
    STAGE74_GOTO Stage74_TutorSelectScript
    .size Stage74_TutorEntryScript, .-Stage74_TutorEntryScript

STAGE74_EXPORT Stage74_TutorSelectScript
    STAGE74_MSGBOX Stage74_TextChooseMon
    STAGE74_SPECIAL 0x00DB
    .byte 0x27
    STAGE74_COMPARE 0x8004, 6
    STAGE74_BRANCH 4, Stage74_FinishScript
    STAGE74_SPECIAL 0x0148
    STAGE74_COMPARE 0x800D, 1
    STAGE74_BRANCH 1, Stage74_TutorEggErrorScript
    STAGE74_COMPARE 0x8005, 0
    STAGE74_BRANCH 1, Stage74_TutorNoMovesScript
    STAGE74_SPECIAL 0x00E0
    .byte 0x27
    STAGE74_COMPARE 0x8004, 0
    STAGE74_BRANCH 1, Stage74_TutorEntryScript
    STAGE74_GOTO Stage74_FinishScript
    .size Stage74_TutorSelectScript, .-Stage74_TutorSelectScript

STAGE74_EXPORT Stage74_TutorEggErrorScript
    STAGE74_MSGBOX Stage74_TextEggRejected
    STAGE74_GOTO Stage74_TutorEntryScript
    .size Stage74_TutorEggErrorScript, .-Stage74_TutorEggErrorScript

STAGE74_EXPORT Stage74_TutorNoMovesScript
    STAGE74_MSGBOX Stage74_TextNoMoves
    STAGE74_GOTO Stage74_TutorEntryScript
    .size Stage74_TutorNoMovesScript, .-Stage74_TutorNoMovesScript

STAGE74_EXPORT Stage74_FinishScript
    STAGE74_CALLNATIVE Stage74_ResetMode
    .byte 0x6C, 0x02                  /* release; end */
    .size Stage74_FinishScript, .-Stage74_FinishScript

STAGE74_EXPORT Stage74_TextChooseMon
    .byte 0x45,0x19,0x00,0x9F,0x59,0x73,0x7E,0x16,0x00
    .byte 0x12,0x06,0x02,0x1F,0x0D,0x06,0xAC,0xFF
    .size Stage74_TextChooseMon, .-Stage74_TextChooseMon

STAGE74_EXPORT Stage74_TextNoMoves
    .byte 0x05,0x23,0x02,0x41,0x0E,0x29,0x00,0x2C,0x3C
    .byte 0x37,0x00,0x01,0x28,0x1F,0x0E,0x2E,0xFF
    .size Stage74_TextNoMoves, .-Stage74_TextNoMoves

STAGE74_EXPORT Stage74_TextEggRejected
    .byte 0x60,0x6F,0x8B,0x1A,0x00,0x04,0x27,0x49,0x1F,0x0E,0x2E,0xFF
    .size Stage74_TextEggRejected, .-Stage74_TextEggRejected

STAGE74_EXPORT Stage74_TextArchiveLocked
    .byte 0x51,0xAE,0x56,0x52,0x98,0x1A,0x00,0x44,0x2E,0x45,0x03
    .byte 0x02,0x28,0x3B,0x16,0x00,0x12,0x06,0x04,0x1F,0x0D,0xFF
    .size Stage74_TextArchiveLocked, .-Stage74_TextArchiveLocked

STAGE74_EXPORT Stage74_TextPageNoMoves
    .byte 0x0A,0x19,0x9E,0xAE,0x8D,0x16,0x00,0x2C,0x3C
    .byte 0x37,0x00,0x01,0x28,0x1F,0x0E,0x2E,0xFF
    .size Stage74_TextPageNoMoves, .-Stage74_TextPageNoMoves

.section .note.GNU-stack,"",%progbits
