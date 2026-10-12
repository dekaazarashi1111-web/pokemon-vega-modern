#include "modernization_rockruff_own_tempo_stage75.h"

enum {
    STAGE75_SPECIES_COUNT = 1671,
    STAGE75_SPECIES_ROCKRUFF = 1142,
    STAGE75_SPECIES_LYCANROC_DUSK = 1263,
    STAGE75_SPECIES_ROCKRUFF_OWN_TEMPO = 1670,
    STAGE75_MON_DATA_PERSONALITY = 0,
    STAGE75_MON_DATA_SPECIES = 11,
    STAGE75_MON_DATA_MOVE1 = 13,
    STAGE75_MON_DATA_LEVEL = 56,
    STAGE75_MON_DATA_SPECIES2 = 65,
    STAGE75_MAX_MON_MOVES = 4,
    STAGE75_MAX_LEVEL_ROWS = 40,
    STAGE75_PAGE_SIZE = 40,
    STAGE75_BUILD_LEARNABLE_CAPACITY = 429,
    STAGE75_PARTY_SIZE = 6,
    STAGE75_POKEMON_SIZE = 100,
    STAGE75_MODE_NORMAL = 0,
    STAGE75_MODE_EGG = 1,
    STAGE75_MODE_MACHINE_PROBE = 2,
    STAGE75_MODE_MACHINE_PAGE_0 = 3,
    STAGE75_MODE_MACHINE_PAGE_3 = 6,
    STAGE75_MODE_TUTOR = 7
};

typedef Stage75U32 (*Stage75GetMonDataFn)(const void *, int, Stage75U8 *);
typedef void (*Stage75SetMonDataFn)(void *, int, const void *);
typedef void (*Stage75CalculateStatsFn)(void *);
typedef Stage75U8 (*Stage75WildFn)(const void *, Stage75U8, Stage75U8);
typedef Stage75U8 (*Stage75GetMovesFn)(void *, Stage75U16 *);
typedef Stage75U16 (*Stage75BuildMovesFn)(void *, Stage75U16 *);
typedef void (*Stage75VoidFn)(void);

#define STAGE75_PTR(type, address) ((type)(Stage75U32)(address))
#define STAGE75_GET_MON_DATA STAGE75_PTR(Stage75GetMonDataFn, 0x0803F355u)
#define STAGE75_SET_MON_DATA STAGE75_PTR(Stage75SetMonDataFn, 0x0803FA71u)
#define STAGE75_CALCULATE_STATS STAGE75_PTR(Stage75CalculateStatsFn, 0x0803DBE9u)
#define STAGE75_PARENT_WILD STAGE75_PTR(Stage75WildFn, 0x094141BDu)
#define STAGE75_STAGE74_GET_MOVES STAGE75_PTR(Stage75GetMovesFn, 0x0953A0A9u)
#define STAGE75_STAGE74_BUILD_MOVES STAGE75_PTR(Stage75BuildMovesFn, 0x0953A115u)
#define STAGE75_STAGE74_PREPARE_PAGES STAGE75_PTR(Stage75VoidFn, 0x0953A1D5u)
#define STAGE75_STAGE74_COMMIT_PAGE STAGE75_PTR(Stage75VoidFn, 0x0953A1FDu)
#define STAGE75_STAGE74_PAGE_HAS_MOVES STAGE75_PTR(Stage75VoidFn, 0x0953A23Du)
#define STAGE75_STAGE74_OPEN_ARCHIVE STAGE75_PTR(Stage75VoidFn, 0x0953A299u)
#define STAGE75_STAGE74_OPEN_PAGE STAGE75_PTR(Stage75VoidFn, 0x0953A2B1u)

#define STAGE75_PLAYER_PARTY ((volatile Stage75U8 *)0x020241E4u)
#define STAGE75_ENEMY_PARTY ((volatile Stage75U8 *)0x02023F8Cu)
#define STAGE75_MOVE_MEMORY_MODE (*(volatile Stage75U8 *)0x0203EC00u)
#define STAGE75_SPECIAL_VAR_8004 (*(volatile Stage75U16 *)0x02036FF4u)
#define STAGE75_SPECIAL_RESULT (*(volatile Stage75U16 *)0x02037004u)

#define STAGE75_SHARED_INDEX ((const Stage75U16 *)0x09534C9Eu)
#define STAGE75_SHARED_MOVES ((const Stage75U16 *)0x0953594Au)
#define STAGE75_REMINDER_INDEX ((const Stage75U16 *)0x09538088u)
#define STAGE75_REMINDER_MOVES ((const Stage75U16 *)0x09538D34u)
#define STAGE75_MACHINE_INDEX ((const Stage75U16 *)0x0953A89Au)
#define STAGE75_MACHINE_MOVES ((const Stage75U16 *)0x0953B546u)
#define STAGE75_TUTOR_INDEX ((const Stage75U16 *)0x09548294u)
#define STAGE75_TUTOR_MOVES ((const Stage75U16 *)0x09548F40u)
#define STAGE75_PRESERVATION_INDEX ((const Stage75U16 *)0x09549222u)
#define STAGE75_PRESERVATION_MOVES ((const Stage75U16 *)0x09549ECEu)

extern const Stage75U32 Stage75_Table_species_level_up_pointers[STAGE75_SPECIES_COUNT];
extern const Stage75U16 Stage75_OwnTempoEggMoves[4];
extern Stage75U16 Stage75_OriginalGetEggSpecies(Stage75U16 species);
extern Stage75U8 Stage75_OriginalGetEggMoves(void *mon, Stage75U16 *moves);

struct Stage75Evolution {
    Stage75U16 method;
    Stage75U16 param;
    Stage75U16 target_species;
    Stage75U16 unknown;
};

extern const struct Stage75Evolution
    Stage75_Table_evolution[STAGE75_SPECIES_COUNT][16];

static Stage75U8 Stage75_MoveKnown(const void *mon, Stage75U16 move)
{
    Stage75U8 slot;
    for (slot = 0u; slot < STAGE75_MAX_MON_MOVES; ++slot) {
        if ((Stage75U16)STAGE75_GET_MON_DATA(
                mon, STAGE75_MON_DATA_MOVE1 + slot, (Stage75U8 *)0
            ) == move)
            return 1u;
    }
    return 0u;
}

static Stage75U8 Stage75_AppendUnique(
    Stage75U16 *moves,
    Stage75U8 count,
    Stage75U8 capacity,
    Stage75U16 move,
    const void *mon,
    Stage75U8 ignore_known
)
{
    Stage75U8 index;
    if (move == 0u || count >= capacity)
        return count;
    if (ignore_known && Stage75_MoveKnown(mon, move))
        return count;
    for (index = 0u; index < count; ++index) {
        if (moves[index] == move)
            return count;
    }
    moves[count] = move;
    return (Stage75U8)(count + 1u);
}

static Stage75U8 Stage75_AppendIndexed(
    const Stage75U16 *index,
    const Stage75U16 *table,
    Stage75U16 donor,
    void *mon,
    Stage75U16 *moves,
    Stage75U8 page,
    Stage75U8 probe
)
{
    Stage75U16 start = index[donor];
    Stage75U16 end = index[(Stage75U16)(donor + 1u)];
    Stage75U16 row_count = (Stage75U16)(end - start);
    Stage75U16 cursor;
    Stage75U16 page_start;
    Stage75U16 page_end;
    Stage75U8 count = 0u;
    if (probe)
        page_end = end;
    else {
        page_start = (Stage75U16)((Stage75U16)page * STAGE75_PAGE_SIZE);
        if (page_start >= row_count)
            return 0u;
        start = (Stage75U16)(start + page_start);
        page_end = (Stage75U16)(start + STAGE75_PAGE_SIZE);
        if (page_end > end)
            page_end = end;
    }
    for (cursor = start; cursor < page_end; ++cursor) {
        count = Stage75_AppendUnique(
            moves, count, probe ? 1u : STAGE75_PAGE_SIZE,
            table[cursor], mon, 1u
        );
        if (probe && count != 0u)
            break;
    }
    return count;
}

static Stage75U8 Stage75_NormalMoves(void *mon, Stage75U16 *moves)
{
    const volatile Stage75U8 *learnset;
    Stage75U32 address = Stage75_Table_species_level_up_pointers[
        STAGE75_SPECIES_ROCKRUFF_OWN_TEMPO
    ];
    Stage75U8 level = (Stage75U8)STAGE75_GET_MON_DATA(
        mon, STAGE75_MON_DATA_LEVEL, (Stage75U8 *)0
    );
    Stage75U8 count = 0u;
    Stage75U8 row;
    Stage75U16 cursor;
    Stage75U16 end;
    if (address < 0x08000000u || address >= 0x0A000000u)
        return 0u;
    learnset = (const volatile Stage75U8 *)address;
    for (row = 0u; row < STAGE75_MAX_LEVEL_ROWS; ++row) {
        Stage75U16 move = (Stage75U16)(
            learnset[0] | (Stage75U16)learnset[1] << 8
        );
        Stage75U8 move_level = learnset[2];
        learnset += 3;
        if (move == 0u && move_level == 0xFFu)
            break;
        if (move != 0u && move_level <= level) {
            count = Stage75_AppendUnique(
                moves, count, STAGE75_PAGE_SIZE, move, mon, 1u
            );
        }
    }
    cursor = STAGE75_REMINDER_INDEX[STAGE75_SPECIES_ROCKRUFF];
    end = STAGE75_REMINDER_INDEX[STAGE75_SPECIES_ROCKRUFF + 1u];
    while (cursor < end) {
        count = Stage75_AppendUnique(
            moves, count, STAGE75_PAGE_SIZE,
            STAGE75_REMINDER_MOVES[cursor], mon, 1u
        );
        ++cursor;
    }
    return count;
}

static Stage75U8 Stage75_EggMemoryMoves(void *mon, Stage75U16 *moves)
{
    Stage75U8 count = 0u;
    Stage75U8 row;
    Stage75U16 cursor;
    Stage75U16 end;
    for (row = 0u; row < 4u; ++row) {
        count = Stage75_AppendUnique(
            moves, count, STAGE75_PAGE_SIZE,
            Stage75_OwnTempoEggMoves[row], mon, 1u
        );
    }
    cursor = STAGE75_SHARED_INDEX[STAGE75_SPECIES_ROCKRUFF];
    end = STAGE75_SHARED_INDEX[STAGE75_SPECIES_ROCKRUFF + 1u];
    while (cursor < end) {
        count = Stage75_AppendUnique(
            moves, count, STAGE75_PAGE_SIZE,
            STAGE75_SHARED_MOVES[cursor], mon, 1u
        );
        ++cursor;
    }
    return count;
}

Stage75U16 Stage75_GetEggSpecies(Stage75U16 species)
{
    if (species == STAGE75_SPECIES_LYCANROC_DUSK
        || species == STAGE75_SPECIES_ROCKRUFF_OWN_TEMPO)
        return STAGE75_SPECIES_ROCKRUFF_OWN_TEMPO;
    return Stage75_OriginalGetEggSpecies(species);
}

Stage75U8 Stage75_GetEggMoves(void *mon, Stage75U16 *moves)
{
    Stage75U16 species = (Stage75U16)STAGE75_GET_MON_DATA(
        mon, STAGE75_MON_DATA_SPECIES, (Stage75U8 *)0
    );
    Stage75U8 row;
    if (species != STAGE75_SPECIES_ROCKRUFF_OWN_TEMPO)
        return Stage75_OriginalGetEggMoves(mon, moves);
    for (row = 0u; row < 4u; ++row)
        moves[row] = Stage75_OwnTempoEggMoves[row];
    return 4u;
}

Stage75U8 Stage75_TryGenerateWildMonAdapter(
    const void *info, Stage75U8 area, Stage75U8 flags
)
{
    Stage75U8 result = STAGE75_PARENT_WILD(info, area, flags);
    if (result) {
        Stage75U16 species = (Stage75U16)STAGE75_GET_MON_DATA(
            (const void *)STAGE75_ENEMY_PARTY,
            STAGE75_MON_DATA_SPECIES2,
            (Stage75U8 *)0
        );
        Stage75U32 personality = STAGE75_GET_MON_DATA(
            (const void *)STAGE75_ENEMY_PARTY,
            STAGE75_MON_DATA_PERSONALITY,
            (Stage75U8 *)0
        );
        Stage75U32 mixed = personality ^ (personality >> 16);
        mixed *= 0x9E3779B1u;
        mixed ^= mixed >> 16;
        if (species == STAGE75_SPECIES_ROCKRUFF
            && (mixed & 7u) == 0u) {
            Stage75U16 target = STAGE75_SPECIES_ROCKRUFF_OWN_TEMPO;
            STAGE75_SET_MON_DATA(
                (void *)STAGE75_ENEMY_PARTY,
                STAGE75_MON_DATA_SPECIES,
                &target
            );
            STAGE75_CALCULATE_STATS((void *)STAGE75_ENEMY_PARTY);
        }
    }
    return result;
}

Stage75U8 Stage75_GetMoveRelearnerMoves(void *mon, Stage75U16 *moves)
{
    Stage75U16 species = (Stage75U16)STAGE75_GET_MON_DATA(
        mon, STAGE75_MON_DATA_SPECIES, (Stage75U8 *)0
    );
    Stage75U8 mode;
    if (species != STAGE75_SPECIES_ROCKRUFF_OWN_TEMPO)
        return STAGE75_STAGE74_GET_MOVES(mon, moves);
    mode = STAGE75_MOVE_MEMORY_MODE;
    if (mode == STAGE75_MODE_NORMAL)
        return Stage75_NormalMoves(mon, moves);
    if (mode == STAGE75_MODE_EGG)
        return Stage75_EggMemoryMoves(mon, moves);
    if (mode == STAGE75_MODE_MACHINE_PROBE) {
        return Stage75_AppendIndexed(
            STAGE75_MACHINE_INDEX, STAGE75_MACHINE_MOVES,
            STAGE75_SPECIES_ROCKRUFF, mon, moves, 0u, 1u
        );
    }
    if (mode >= STAGE75_MODE_MACHINE_PAGE_0
        && mode <= STAGE75_MODE_MACHINE_PAGE_3) {
        return Stage75_AppendIndexed(
            STAGE75_MACHINE_INDEX, STAGE75_MACHINE_MOVES,
            STAGE75_SPECIES_ROCKRUFF, mon, moves,
            (Stage75U8)(mode - STAGE75_MODE_MACHINE_PAGE_0), 0u
        );
    }
    if (mode == STAGE75_MODE_TUTOR) {
        return Stage75_AppendIndexed(
            STAGE75_TUTOR_INDEX, STAGE75_TUTOR_MOVES,
            STAGE75_SPECIES_ROCKRUFF, mon, moves, 0u, 0u
        );
    }
    return 0u;
}

static Stage75U16 Stage75_AppendLearnableRange(
    const Stage75U16 *table,
    Stage75U16 start,
    Stage75U16 end,
    Stage75U16 *moves,
    Stage75U16 count
)
{
    Stage75U16 cursor;
    for (cursor = start;
         cursor < end && count < STAGE75_BUILD_LEARNABLE_CAPACITY;
         ++cursor) {
        Stage75U16 move = table[cursor];
        Stage75U16 index;
        Stage75U8 duplicate = 0u;
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

Stage75U16 Stage75_BuildLearnableMoveset(void *mon, Stage75U16 *moves)
{
    Stage75U16 species = (Stage75U16)STAGE75_GET_MON_DATA(
        mon, STAGE75_MON_DATA_SPECIES, (Stage75U8 *)0
    );
    Stage75U16 count = STAGE75_STAGE74_BUILD_MOVES(mon, moves);
    if (count > STAGE75_BUILD_LEARNABLE_CAPACITY)
        count = STAGE75_BUILD_LEARNABLE_CAPACITY;
    if (species != STAGE75_SPECIES_ROCKRUFF_OWN_TEMPO)
        return count;
    count = Stage75_AppendLearnableRange(
        STAGE75_MACHINE_MOVES,
        STAGE75_MACHINE_INDEX[STAGE75_SPECIES_ROCKRUFF],
        STAGE75_MACHINE_INDEX[STAGE75_SPECIES_ROCKRUFF + 1u],
        moves, count
    );
    count = Stage75_AppendLearnableRange(
        STAGE75_TUTOR_MOVES,
        STAGE75_TUTOR_INDEX[STAGE75_SPECIES_ROCKRUFF],
        STAGE75_TUTOR_INDEX[STAGE75_SPECIES_ROCKRUFF + 1u],
        moves, count
    );
    count = Stage75_AppendLearnableRange(
        STAGE75_PRESERVATION_MOVES,
        STAGE75_PRESERVATION_INDEX[STAGE75_SPECIES_ROCKRUFF],
        STAGE75_PRESERVATION_INDEX[STAGE75_SPECIES_ROCKRUFF + 1u],
        moves, count
    );
    return Stage75_AppendLearnableRange(
        Stage75_OwnTempoEggMoves, 0u, 4u, moves, count
    );
}

static Stage75U16 Stage75_SelectedMachineRowCount(void)
{
    Stage75U16 slot = STAGE75_SPECIAL_VAR_8004;
    Stage75U16 species;
    if (slot >= STAGE75_PARTY_SIZE)
        return 0u;
    species = (Stage75U16)STAGE75_GET_MON_DATA(
        (const void *)(STAGE75_PLAYER_PARTY
            + (Stage75U32)slot * STAGE75_POKEMON_SIZE),
        STAGE75_MON_DATA_SPECIES,
        (Stage75U8 *)0
    );
    if (species != STAGE75_SPECIES_ROCKRUFF_OWN_TEMPO)
        return 0u;
    return (Stage75U16)(
        STAGE75_MACHINE_INDEX[STAGE75_SPECIES_ROCKRUFF + 1u]
        - STAGE75_MACHINE_INDEX[STAGE75_SPECIES_ROCKRUFF]
    );
}

void Stage75_SetMachineMode(void)
{
    STAGE75_MOVE_MEMORY_MODE = STAGE75_MODE_MACHINE_PROBE;
}

void Stage75_SetTutorMode(void)
{
    STAGE75_MOVE_MEMORY_MODE = STAGE75_MODE_TUTOR;
}

void Stage75_ResetMode(void)
{
    STAGE75_MOVE_MEMORY_MODE = STAGE75_MODE_NORMAL;
}

void Stage75_PrepareMachinePages(void)
{
    Stage75U16 slot = STAGE75_SPECIAL_VAR_8004;
    Stage75U16 species = 0u;
    if (slot < STAGE75_PARTY_SIZE) {
        species = (Stage75U16)STAGE75_GET_MON_DATA(
            (const void *)(STAGE75_PLAYER_PARTY
                + (Stage75U32)slot * STAGE75_POKEMON_SIZE),
            STAGE75_MON_DATA_SPECIES,
            (Stage75U8 *)0
        );
    }
    if (species != STAGE75_SPECIES_ROCKRUFF_OWN_TEMPO) {
        STAGE75_STAGE74_PREPARE_PAGES();
        return;
    }
    if (Stage75_SelectedMachineRowCount() != 0u) {
        STAGE75_MOVE_MEMORY_MODE = STAGE75_MODE_MACHINE_PAGE_0;
        STAGE75_SPECIAL_RESULT = 1u;
    } else {
        STAGE75_MOVE_MEMORY_MODE = STAGE75_MODE_MACHINE_PROBE;
        STAGE75_SPECIAL_RESULT = 0u;
    }
}

void Stage75_SelectedMachinePageHasMoves(void)
{
    Stage75U16 slot = STAGE75_SPECIAL_VAR_8004;
    Stage75U16 species = 0u;
    if (slot < STAGE75_PARTY_SIZE) {
        void *mon = (void *)(STAGE75_PLAYER_PARTY
            + (Stage75U32)slot * STAGE75_POKEMON_SIZE);
        Stage75U16 scratch[STAGE75_PAGE_SIZE];
        species = (Stage75U16)STAGE75_GET_MON_DATA(
            mon, STAGE75_MON_DATA_SPECIES, (Stage75U8 *)0
        );
        if (species == STAGE75_SPECIES_ROCKRUFF_OWN_TEMPO) {
            STAGE75_SPECIAL_RESULT =
                Stage75_GetMoveRelearnerMoves(mon, scratch) != 0u ? 1u : 0u;
            return;
        }
    }
    STAGE75_STAGE74_PAGE_HAS_MOVES();
}

void Stage75_OpenArchiveModeMenu(void)
{
    STAGE75_STAGE74_OPEN_ARCHIVE();
}

void Stage75_OpenMachinePageMenu(void)
{
    STAGE75_STAGE74_OPEN_PAGE();
}

void Stage75_CommitMachinePage(void)
{
    STAGE75_STAGE74_COMMIT_PAGE();
}

__attribute__((section(".text.Stage75_RuntimeProbe"), used, noinline))
Stage75U32 Stage75_RuntimeProbe(Stage75U32 query)
{
    switch (query) {
    case 0u: return 0x50333735u; /* "P375" */
    case 1u: return STAGE75_SPECIES_COUNT;
    case 2u: return STAGE75_SPECIES_ROCKRUFF_OWN_TEMPO;
    case 3u: return STAGE75_SPECIES_ROCKRUFF;
    case 4u: return STAGE75_SPECIES_LYCANROC_DUSK;
    case 5u: return STAGE75_BUILD_LEARNABLE_CAPACITY;
    default: return 0u;
    }
}
