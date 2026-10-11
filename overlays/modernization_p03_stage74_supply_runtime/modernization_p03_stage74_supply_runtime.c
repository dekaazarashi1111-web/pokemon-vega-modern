#include "modernization_p03_stage74_supply_runtime.h"

/*
 * Stage74 P03 direct machine/tutor archive.
 *
 * The two generated tables remain distinct.  They are deliberately not
 * projected into the fixed 128-slot TM/HM or 64-slot tutor catalogs, and are
 * never copied to level-up or egg rows.  The existing Move Memory selection
 * and four-slot replacement flow is reused only as the archive's UI shell.
 */

enum {
    STAGE74_SPECIES_COUNT = 1621,
    STAGE74_INDEX_COUNT = 1622,
    STAGE74_PAGE_SIZE = 40,
    STAGE74_MAX_MACHINE_PAGES = 4,
    STAGE74_BUILD_LEARNABLE_CAPACITY = 429,
    STAGE74_MAX_MON_MOVES = 4,
    STAGE74_MON_DATA_SPECIES = 11,
    STAGE74_MON_DATA_MOVE1 = 13,
    STAGE74_PARTY_SIZE = 6,
    STAGE74_POKEMON_SIZE = 100,
    STAGE74_NUM_TASKS = 16,
    STAGE74_MENU_NOTHING_CHOSEN = -2,
    STAGE74_MENU_B_PRESSED = -1,
    STAGE74_MENU_WINDOW_INVALID = 0xFF,
    STAGE74_COPYWIN_BOTH = 3,
    STAGE74_SE_SELECT = 5
};

struct Stage74Task {
    void (*func)(Stage74U8 task_id);
    Stage74U8 is_active;
    Stage74U8 prev;
    Stage74U8 next;
    Stage74U8 priority;
    Stage74S16 data[16];
};

struct Stage74WindowTemplate {
    Stage74U8 bg;
    Stage74U8 tilemap_left;
    Stage74U8 tilemap_top;
    Stage74U8 width;
    Stage74U8 height;
    Stage74U8 palette_num;
    Stage74U16 base_block;
};

_Static_assert(sizeof(struct Stage74Task) == 40, "FireRed Task ABI changed");
_Static_assert(sizeof(struct Stage74WindowTemplate) == 8, "FireRed Window ABI changed");

typedef Stage74U32 (*Stage74GetMonDataFn)(const void *, int, Stage74U8 *);
typedef Stage74U8 (*Stage74GetMovesFn)(void *, Stage74U16 *);
typedef Stage74U8 (*Stage74CreateTaskFn)(void (*)(Stage74U8), Stage74U8);
typedef void (*Stage74TaskIdFn)(Stage74U8);
typedef void (*Stage74VoidFn)(void);
typedef Stage74U16 (*Stage74AddWindowFn)(const struct Stage74WindowTemplate *);
typedef void (*Stage74WindowU8Fn)(Stage74U8);
typedef void (*Stage74WindowPairFn)(Stage74U8, Stage74U8);
typedef void (*Stage74TextPrinterFn)(Stage74U8, Stage74U8, const Stage74U8 *,
                                     Stage74U8, Stage74U8, Stage74U8, void *);
typedef Stage74U8 (*Stage74MenuInitCursorFn)(Stage74U8, Stage74U8, Stage74U8,
                                             Stage74U8, Stage74U8, Stage74U8,
                                             Stage74U8);
typedef Stage74S8 (*Stage74MenuInputFn)(void);
typedef Stage74U16 (*Stage74GetBaseTileFn)(void);
typedef void (*Stage74PlaySeFn)(Stage74U16);

#define STAGE74_PTR(type, address) ((type)(Stage74U32)(address))
#define STAGE74_GET_MON_DATA STAGE74_PTR(Stage74GetMonDataFn, 0x0803F355u)
#define STAGE74_STAGE73_GET_MOVES STAGE74_PTR(Stage74GetMovesFn, 0x09534941u)
#define STAGE74_CREATE_TASK STAGE74_PTR(Stage74CreateTaskFn, 0x08076BB5u)
#define STAGE74_DESTROY_TASK STAGE74_PTR(Stage74TaskIdFn, 0x08076CA1u)
#define STAGE74_PLAY_SE STAGE74_PTR(Stage74PlaySeFn, 0x08071A71u)
#define STAGE74_SCRIPT_CONTEXT2_ENABLE STAGE74_PTR(Stage74VoidFn, 0x08069201u)
#define STAGE74_ENABLE_BOTH_SCRIPT_CONTEXTS STAGE74_PTR(Stage74VoidFn, 0x080693F5u)
#define STAGE74_ADD_WINDOW STAGE74_PTR(Stage74AddWindowFn, 0x08003CB1u)
#define STAGE74_REMOVE_WINDOW STAGE74_PTR(Stage74WindowU8Fn, 0x08003E09u)
#define STAGE74_COPY_WINDOW_TO_VRAM STAGE74_PTR(Stage74WindowPairFn, 0x08003EEDu)
#define STAGE74_PUT_WINDOW_TILEMAP STAGE74_PTR(Stage74WindowU8Fn, 0x08003F6Du)
#define STAGE74_FILL_WINDOW_PIXEL_BUFFER STAGE74_PTR(Stage74WindowPairFn, 0x08004429u)
#define STAGE74_ADD_TEXT_PRINTER STAGE74_PTR(Stage74TextPrinterFn, 0x08002C45u)
#define STAGE74_SCHEDULE_BG_COPY STAGE74_PTR(Stage74WindowU8Fn, 0x080F77FDu)
#define STAGE74_DRAW_STD_WINDOW_FRAME STAGE74_PTR(Stage74WindowPairFn, 0x080F7F7Du)
#define STAGE74_CLEAR_STD_WINDOW_FRAME STAGE74_PTR(Stage74WindowPairFn, 0x080F7FFDu)
#define STAGE74_GET_STD_WINDOW_BASE_TILE STAGE74_PTR(Stage74GetBaseTileFn, 0x080F89CDu)
#define STAGE74_MENU_INIT_CURSOR STAGE74_PTR(Stage74MenuInitCursorFn, 0x0811030Du)
#define STAGE74_MENU_PROCESS_INPUT STAGE74_PTR(Stage74MenuInputFn, 0x08110BF9u)

#define STAGE74_MOVE_MEMORY_MODE (*(volatile Stage74U8 *)0x0203EC00u)
#define STAGE74_PLAYER_PARTY ((volatile Stage74U8 *)0x020241E4u)
#define STAGE74_SPECIAL_VAR_8004 (*(volatile Stage74U16 *)0x02036FF4u)
#define STAGE74_SPECIAL_RESULT (*(volatile Stage74U16 *)0x02037004u)
#define STAGE74_TASKS ((volatile struct Stage74Task *)0x030050D0u)

extern const Stage74U16 Stage74_MachineIndex[STAGE74_INDEX_COUNT];
extern const Stage74U16 Stage74_MachineMoves[];
extern const Stage74U16 Stage74_TutorIndex[STAGE74_INDEX_COUNT];
extern const Stage74U16 Stage74_TutorMoves[];
extern const Stage74U16 Stage74_PreservationIndex[STAGE74_INDEX_COUNT];
extern const Stage74U16 Stage74_PreservationMoves[];
extern Stage74U16 Stage74_OriginalBuildLearnableMoveset(
    void *mon, Stage74U16 *moves
);

/* Encoded with the pinned CFRU-JP charmap. */
static const Stage74U8 sStage74TextRemember[] = {0x05, 0x23, 0x02, 0x41, 0x0D, 0xFF};
static const Stage74U8 sStage74TextForget[] = {0x2C, 0x0D, 0x2A, 0x0B, 0x0E, 0x29, 0xFF};
static const Stage74U8 sStage74TextEgg[] = {0x60, 0x6F, 0x8B, 0x2C, 0x3C, 0xFF};
static const Stage74U8 sStage74TextMachine[] = {0x6F, 0x5C, 0x7E, 0x2C, 0x3C, 0xFF};
static const Stage74U8 sStage74TextTutor[] = {0x05, 0x0C, 0x04, 0x2C, 0x3C, 0xFF};
static const Stage74U8 sStage74TextCancel[] = {0x24, 0x22, 0x29, 0xFF};
static const Stage74U8 sStage74TextPage1[] = {0xA2, 0x9E, 0xAE, 0x8D, 0xFF};
static const Stage74U8 sStage74TextPage2[] = {0xA3, 0x9E, 0xAE, 0x8D, 0xFF};
static const Stage74U8 sStage74TextPage3[] = {0xA4, 0x9E, 0xAE, 0x8D, 0xFF};
static const Stage74U8 sStage74TextPage4[] = {0xA5, 0x9E, 0xAE, 0x8D, 0xFF};

static const Stage74U8 *const sStage74MainMenuTexts[] = {
    sStage74TextRemember,
    sStage74TextForget,
    sStage74TextEgg,
    sStage74TextMachine,
    sStage74TextTutor,
    sStage74TextCancel
};

static const Stage74U8 *const sStage74PageMenuTexts[] = {
    sStage74TextPage1,
    sStage74TextPage2,
    sStage74TextPage3,
    sStage74TextPage4
};

static void Stage74_SetResult(Stage74U16 value)
{
    STAGE74_SPECIAL_RESULT = value;
}

Stage74U16 Stage74_PageCountForRowCount(Stage74U16 row_count)
{
    if (row_count == 0u)
        return 0u;
    return (Stage74U16)((row_count + STAGE74_PAGE_SIZE - 1u) / STAGE74_PAGE_SIZE);
}

Stage74U16 Stage74_PageStart(Stage74U8 page)
{
    return (Stage74U16)((Stage74U16)page * STAGE74_PAGE_SIZE);
}

Stage74U16 Stage74_PageEnd(Stage74U16 row_count, Stage74U8 page)
{
    Stage74U16 end = (Stage74U16)(Stage74_PageStart(page) + STAGE74_PAGE_SIZE);
    return end < row_count ? end : row_count;
}

static Stage74U8 Stage74_MoveKnown(const void *mon, Stage74U16 move)
{
    Stage74U8 slot;
    for (slot = 0u; slot < STAGE74_MAX_MON_MOVES; ++slot) {
        if ((Stage74U16)STAGE74_GET_MON_DATA(
                mon, STAGE74_MON_DATA_MOVE1 + slot, (Stage74U8 *)0
            ) == move)
            return 1u;
    }
    return 0u;
}

static Stage74U8 Stage74_AppendRange(
    const Stage74U16 *table,
    Stage74U16 start,
    Stage74U16 end,
    void *mon,
    Stage74U16 *moves,
    Stage74U8 capacity
)
{
    Stage74U8 count = 0u;
    Stage74U16 cursor;
    for (cursor = start; cursor < end && count < capacity; ++cursor) {
        Stage74U16 move = table[cursor];
        Stage74U8 duplicate = 0u;
        Stage74U8 index;
        if (move == 0u || Stage74_MoveKnown(mon, move))
            continue;
        for (index = 0u; index < count; ++index) {
            if (moves[index] == move) {
                duplicate = 1u;
                break;
            }
        }
        if (!duplicate)
            moves[count++] = move;
    }
    return count;
}

static Stage74U8 Stage74_AppendIndexedPage(
    const Stage74U16 *index,
    const Stage74U16 *table,
    void *mon,
    Stage74U16 *moves,
    Stage74U8 page,
    Stage74U8 probe
)
{
    Stage74U16 species = (Stage74U16)STAGE74_GET_MON_DATA(
        mon, STAGE74_MON_DATA_SPECIES, (Stage74U8 *)0
    );
    Stage74U16 row_start;
    Stage74U16 row_end;
    Stage74U16 count;
    if (species >= STAGE74_SPECIES_COUNT)
        return 0u;
    row_start = index[species];
    row_end = index[(Stage74U16)(species + 1u)];
    count = (Stage74U16)(row_end - row_start);
    if (probe)
        return Stage74_AppendRange(table, row_start, row_end, mon, moves, 1u);
    if (page >= Stage74_PageCountForRowCount(count))
        return 0u;
    return Stage74_AppendRange(
        table,
        (Stage74U16)(row_start + Stage74_PageStart(page)),
        (Stage74U16)(row_start + Stage74_PageEnd(count, page)),
        mon,
        moves,
        STAGE74_PAGE_SIZE
    );
}

Stage74U8 Stage74_GetMoveRelearnerMoves(void *mon, Stage74U16 *moves)
{
    Stage74U8 mode = STAGE74_MOVE_MEMORY_MODE;
    if (mode == STAGE74_MODE_MACHINE_PROBE) {
        return Stage74_AppendIndexedPage(
            Stage74_MachineIndex, Stage74_MachineMoves, mon, moves, 0u, 1u
        );
    }
    if (mode >= STAGE74_MODE_MACHINE_PAGE_0
        && mode <= STAGE74_MODE_MACHINE_PAGE_3) {
        return Stage74_AppendIndexedPage(
            Stage74_MachineIndex,
            Stage74_MachineMoves,
            mon,
            moves,
            (Stage74U8)(mode - STAGE74_MODE_MACHINE_PAGE_0),
            0u
        );
    }
    if (mode == STAGE74_MODE_TUTOR) {
        return Stage74_AppendIndexedPage(
            Stage74_TutorIndex, Stage74_TutorMoves, mon, moves, 0u, 0u
        );
    }
    return STAGE74_STAGE73_GET_MOVES(mon, moves);
}

static Stage74U16 Stage74_AppendLearnableRange(
    const Stage74U16 *table,
    Stage74U16 start,
    Stage74U16 end,
    Stage74U16 *moves,
    Stage74U16 count
)
{
    Stage74U16 cursor;
    for (cursor = start;
         cursor < end && count < STAGE74_BUILD_LEARNABLE_CAPACITY;
         ++cursor) {
        Stage74U16 move = table[cursor];
        Stage74U16 index;
        Stage74U8 duplicate = 0u;
        for (index = 0u; index < count; ++index) {
            if (moves[index] == move) {
                duplicate = 1u;
                break;
            }
        }
        if (move != 0u && !duplicate)
            moves[count++] = move;
    }
    return count;
}

/*
 * RestoreEffectBankHPStatsAndRemoveBackupSpecies validates the current four
 * moves against this full learnable set.  Archive moves therefore have to be
 * present here as well as in the interactive Move Memory provider, or a valid
 * taught move is erased.
 * The unique caller owns a 429-u16 buffer; the generated exact-ROM host audit
 * pins an all-species maximum of 238 written entries (234 unique) after both
 * direct-family appends and the target-keyed preservation-only append.  The
 * latter is never exposed by the interactive Move Memory provider.
 */
Stage74U16 Stage74_BuildLearnableMoveset(void *mon, Stage74U16 *moves)
{
    Stage74U16 count = Stage74_OriginalBuildLearnableMoveset(mon, moves);
    Stage74U16 species = (Stage74U16)STAGE74_GET_MON_DATA(
        mon, STAGE74_MON_DATA_SPECIES, (Stage74U8 *)0
    );
    if (count > STAGE74_BUILD_LEARNABLE_CAPACITY)
        return STAGE74_BUILD_LEARNABLE_CAPACITY;
    if (species >= STAGE74_SPECIES_COUNT)
        return count;
    count = Stage74_AppendLearnableRange(
        Stage74_MachineMoves,
        Stage74_MachineIndex[species],
        Stage74_MachineIndex[(Stage74U16)(species + 1u)],
        moves,
        count
    );
    count = Stage74_AppendLearnableRange(
        Stage74_TutorMoves,
        Stage74_TutorIndex[species],
        Stage74_TutorIndex[(Stage74U16)(species + 1u)],
        moves,
        count
    );
    return Stage74_AppendLearnableRange(
        Stage74_PreservationMoves,
        Stage74_PreservationIndex[species],
        Stage74_PreservationIndex[(Stage74U16)(species + 1u)],
        moves,
        count
    );
}

static Stage74U16 Stage74_SelectedMachineRowCount(void)
{
    Stage74U16 party_id = STAGE74_SPECIAL_VAR_8004;
    Stage74U16 species;
    if (party_id >= STAGE74_PARTY_SIZE)
        return 0u;
    species = (Stage74U16)STAGE74_GET_MON_DATA(
        (const void *)(STAGE74_PLAYER_PARTY
            + (Stage74U32)party_id * STAGE74_POKEMON_SIZE),
        STAGE74_MON_DATA_SPECIES,
        (Stage74U8 *)0
    );
    if (species >= STAGE74_SPECIES_COUNT)
        return 0u;
    return (Stage74U16)(
        Stage74_MachineIndex[(Stage74U16)(species + 1u)]
        - Stage74_MachineIndex[species]
    );
}

void Stage74_SetMachineMode(void)
{
    STAGE74_MOVE_MEMORY_MODE = STAGE74_MODE_MACHINE_PROBE;
}

void Stage74_SetTutorMode(void)
{
    STAGE74_MOVE_MEMORY_MODE = STAGE74_MODE_TUTOR;
}

void Stage74_ResetMode(void)
{
    STAGE74_MOVE_MEMORY_MODE = STAGE74_MODE_NORMAL;
}

void Stage74_PrepareMachinePages(void)
{
    Stage74U16 pages = Stage74_PageCountForRowCount(
        Stage74_SelectedMachineRowCount()
    );
    if (pages == 1u)
        STAGE74_MOVE_MEMORY_MODE = STAGE74_MODE_MACHINE_PAGE_0;
    else
        STAGE74_MOVE_MEMORY_MODE = STAGE74_MODE_MACHINE_PROBE;
    Stage74_SetResult(pages);
}

void Stage74_CommitMachinePage(void)
{
    Stage74U16 pages = Stage74_PageCountForRowCount(
        Stage74_SelectedMachineRowCount()
    );
    Stage74U16 selection = STAGE74_SPECIAL_RESULT;
    if (pages == 0u || pages > STAGE74_MAX_MACHINE_PAGES
        || selection >= pages) {
        STAGE74_MOVE_MEMORY_MODE = STAGE74_MODE_MACHINE_PROBE;
        Stage74_SetResult(0u);
        return;
    }
    STAGE74_MOVE_MEMORY_MODE = (Stage74U8)(
        STAGE74_MODE_MACHINE_PAGE_0 + selection
    );
    Stage74_SetResult(1u);
}

void Stage74_SelectedMachinePageHasMoves(void)
{
    Stage74U16 party_id = STAGE74_SPECIAL_VAR_8004;
    Stage74U16 scratch[STAGE74_PAGE_SIZE];
    Stage74U8 count = 0u;
    if (party_id < STAGE74_PARTY_SIZE) {
        void *mon = (void *)(STAGE74_PLAYER_PARTY
            + (Stage74U32)party_id * STAGE74_POKEMON_SIZE);
        Stage74U8 mode = STAGE74_MOVE_MEMORY_MODE;
        if (mode >= STAGE74_MODE_MACHINE_PAGE_0
            && mode <= STAGE74_MODE_MACHINE_PAGE_3) {
            count = Stage74_AppendIndexedPage(
                Stage74_MachineIndex,
                Stage74_MachineMoves,
                mon,
                scratch,
                (Stage74U8)(mode - STAGE74_MODE_MACHINE_PAGE_0),
                0u
            );
        }
    }
    Stage74_SetResult(count != 0u ? 1u : 0u);
}

static void Stage74_CloseMenu(Stage74U8 task_id, Stage74U8 selection)
{
    Stage74U8 window_id = (Stage74U8)STAGE74_TASKS[task_id].data[0];
    Stage74_SetResult(selection);
    STAGE74_PLAY_SE(STAGE74_SE_SELECT);
    STAGE74_CLEAR_STD_WINDOW_FRAME(window_id, 1u);
    STAGE74_REMOVE_WINDOW(window_id);
    STAGE74_SCHEDULE_BG_COPY(0u);
    STAGE74_DESTROY_TASK(task_id);
    STAGE74_ENABLE_BOTH_SCRIPT_CONTEXTS();
}

static void Stage74_TaskHandleMenu(Stage74U8 task_id)
{
    Stage74S8 choice = STAGE74_MENU_PROCESS_INPUT();
    Stage74U8 count = (Stage74U8)STAGE74_TASKS[task_id].data[1];
    if (choice == STAGE74_MENU_NOTHING_CHOSEN)
        return;
    if (choice == STAGE74_MENU_B_PRESSED || choice < 0
        || (Stage74U8)choice >= count)
        Stage74_CloseMenu(task_id, (Stage74U8)(count - 1u));
    else
        Stage74_CloseMenu(task_id, (Stage74U8)choice);
}

static void Stage74_OpenMenu(
    const Stage74U8 *const *texts,
    Stage74U8 count,
    Stage74U8 height,
    Stage74U16 failure_result
)
{
    struct Stage74WindowTemplate template;
    Stage74U8 task_id = STAGE74_CREATE_TASK(Stage74_TaskHandleMenu, 0x50u);
    Stage74U8 window_id;
    Stage74U8 index;
    if (task_id >= STAGE74_NUM_TASKS) {
        Stage74_SetResult(failure_result);
        return;
    }
    template.bg = 0u;
    template.tilemap_left = 12u;
    template.tilemap_top = 1u;
    template.width = 17u;
    template.height = height;
    template.palette_num = 15u;
    template.base_block = STAGE74_GET_STD_WINDOW_BASE_TILE();
    window_id = (Stage74U8)STAGE74_ADD_WINDOW(&template);
    if (window_id == STAGE74_MENU_WINDOW_INVALID) {
        STAGE74_DESTROY_TASK(task_id);
        Stage74_SetResult(failure_result);
        return;
    }
    STAGE74_TASKS[task_id].data[0] = (Stage74S16)window_id;
    STAGE74_TASKS[task_id].data[1] = (Stage74S16)count;
    STAGE74_FILL_WINDOW_PIXEL_BUFFER(window_id, 0x11u);
    STAGE74_DRAW_STD_WINDOW_FRAME(window_id, 0u);
    STAGE74_PUT_WINDOW_TILEMAP(window_id);
    for (index = 0u; index < count; ++index) {
        STAGE74_ADD_TEXT_PRINTER(
            window_id,
            2u,
            texts[index],
            8u,
            (Stage74U8)(1u + (Stage74U8)(index * 16u)),
            0u,
            (void *)0
        );
    }
    (void)STAGE74_MENU_INIT_CURSOR(window_id, 2u, 0u, 1u, 16u, count, 0u);
    STAGE74_COPY_WINDOW_TO_VRAM(window_id, STAGE74_COPYWIN_BOTH);
    STAGE74_SCHEDULE_BG_COPY(0u);
    Stage74_SetResult(0xFFFFu);
    STAGE74_SCRIPT_CONTEXT2_ENABLE();
}

void Stage74_OpenArchiveModeMenu(void)
{
    /* result=5 lets the script avoid waitstate after synchronous failure. */
    Stage74_OpenMenu(sStage74MainMenuTexts, 6u, 14u, 5u);
}

void Stage74_OpenMachinePageMenu(void)
{
    Stage74U16 pages = Stage74_PageCountForRowCount(
        Stage74_SelectedMachineRowCount()
    );
    const Stage74U8 *page_texts[STAGE74_MAX_MACHINE_PAGES + 1u];
    Stage74U8 index;
    if (pages < 2u || pages > STAGE74_MAX_MACHINE_PAGES) {
        Stage74_SetResult(0xFFFEu);
        return;
    }
    for (index = 0u; index < (Stage74U8)pages; ++index)
        page_texts[index] = sStage74PageMenuTexts[index];
    page_texts[pages] = sStage74TextCancel;
    Stage74_OpenMenu(
        page_texts,
        (Stage74U8)(pages + 1u),
        (Stage74U8)(4u + (Stage74U8)(pages * 2u)),
        0xFFFEu
    );
}

Stage74U32 Stage74_RuntimeProbe(Stage74U32 query)
{
    switch (query) {
    case 0u:
        return 0x50333734u; /* "P374" */
    case 1u:
        return STAGE74_SPECIES_COUNT;
    case 2u:
        return STAGE74_PAGE_SIZE;
    case 3u:
        return STAGE74_MAX_MACHINE_PAGES;
    case 4u:
        return STAGE74_MODE_TUTOR;
    default:
        return 0u;
    }
}
