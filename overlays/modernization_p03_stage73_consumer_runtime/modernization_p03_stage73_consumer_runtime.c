#include "modernization_p03_stage73_consumer_runtime.h"

/*
 * Stage73 P03 consumer adapters.
 *
 * The generated tables are separate from the C translation unit so the fixed
 * 82 MiB source ZIP remains the sole authoring input.  No carry-only route is
 * flattened into a direct level/egg row here.
 */

enum {
    STAGE73_SPECIES_COUNT = 1621,
    STAGE73_INDEX_COUNT = 1622,
    STAGE73_MAX_RELEARNER_MOVES = 40,
    STAGE73_EGG_MOVE_BUFFER_COUNT = 50,
    STAGE73_MAX_LEVEL_ROWS = 40,
    STAGE73_MAX_MON_MOVES = 4,
    STAGE73_MOVE_NONE = 0,
    STAGE73_MON_DATA_SPECIES = 11,
    STAGE73_MON_DATA_MOVE1 = 13,
    STAGE73_MON_DATA_PP1 = 17,
    STAGE73_MON_DATA_PP_BONUSES = 21,
    STAGE73_MON_DATA_LEVEL = 56,
    STAGE73_MON_DATA_SPECIES2 = 65,
    STAGE73_MOVE_MEMORY_MODE_EGG = 1,
    STAGE73_COLLECTION_RESULT_SUCCESS = 0,
    STAGE73_COLLECTION_RESULT_EFFECTLESS = 1,
    STAGE73_COLLECTION_PARTY_SIZE = 6,
    STAGE73_POKEMON_SIZE = 100,
    STAGE73_SPECIES_ROTOM = 742,
    STAGE73_SPECIES_ROTOM_HEAT = 894,
    STAGE73_SPECIES_ROTOM_WASH = 895,
    STAGE73_SPECIES_ROTOM_FROST = 896,
    STAGE73_SPECIES_ROTOM_FAN = 897,
    STAGE73_SPECIES_ROTOM_MOW = 898,
    STAGE73_MOVE_OVERHEAT = 315,
    STAGE73_MOVE_HYDRO_PUMP = 56,
    STAGE73_MOVE_BLIZZARD = 59,
    STAGE73_MOVE_AIR_SLASH = 373,
    STAGE73_MOVE_LEAF_STORM = 401,
    STAGE73_COLLECTION_ROTOM_FIRST_INDEX = 37,
    STAGE73_COLLECTION_ROTOM_LAST_INDEX = 41
};

typedef Stage73U32 (*Stage73GetMonDataFn)(const void *, int, Stage73U8 *);
typedef void (*Stage73SetMonDataFn)(void *, int, const void *);
typedef void (*Stage73SetMonMoveSlotFn)(void *, Stage73U16, Stage73U8);
typedef void (*Stage73RemoveMonPpBonusFn)(void *, Stage73U8);
typedef void (*Stage73ShiftMoveSlotFn)(void *, Stage73U8, Stage73U8);
typedef Stage73U8 (*Stage73U8ArgFn)(Stage73U8);

#define STAGE73_PTR(type, address) ((type)(Stage73U32)(address))
#define STAGE73_GET_MON_DATA \
    STAGE73_PTR(Stage73GetMonDataFn, 0x0803F355u)
#define STAGE73_SET_MON_DATA \
    STAGE73_PTR(Stage73SetMonDataFn, 0x0803FA71u)
#define STAGE73_SET_MON_MOVE_SLOT \
    STAGE73_PTR(Stage73SetMonMoveSlotFn, 0x09114699u)
#define STAGE73_REMOVE_MON_PP_BONUS \
    STAGE73_PTR(Stage73RemoveMonPpBonusFn, 0x08040755u)
#define STAGE73_SHIFT_MOVE_SLOT \
    STAGE73_PTR(Stage73ShiftMoveSlotFn, 0x080C0C79u)
#define STAGE73_TRY_SAVING_DATA \
    STAGE73_PTR(Stage73U8ArgFn, 0x093789E5u)

#define STAGE73_MOVE_MEMORY_MODE (*(volatile Stage73U8 *)0x0203EC00u)
#define STAGE73_PLAYER_PARTY ((volatile Stage73U8 *)0x020241E4u)
#define STAGE73_SPECIAL_VAR_8004 (*(volatile Stage73U16 *)0x02036FF4u)
#define STAGE73_SPECIAL_RESULT (*(volatile Stage73U16 *)0x02037004u)
#define STAGE73_COLLECTION_LAST_RESULT \
    (*(volatile Stage73U16 *)0x0203F728u)
#define STAGE73_COLLECTION_PENDING_INDEX \
    (*(volatile Stage73U16 *)0x0203F72Au)
#define STAGE73_COLLECTION_TEST_MODE (*(volatile Stage73U8 *)0x0203F73Bu)

/* Emitted from the generated assembler table object. */
extern const Stage73U16 Stage73_SharedIndex[STAGE73_INDEX_COUNT];
extern const Stage73U16 Stage73_SharedMoves[];
extern const Stage73U16 Stage73_ReminderIndex[STAGE73_INDEX_COUNT];
extern const Stage73U16 Stage73_ReminderMoves[];
extern const Stage73U16 Stage73_ExactEggIndex[STAGE73_INDEX_COUNT];
extern const Stage73U16 Stage73_ExactEggMoves[];

/* Replays the exact parent prologues before their untouched continuations. */
extern Stage73U8 Stage73_OriginalGetAllEggMoves(
    void *, Stage73U16 *, Stage73U8
);
extern Stage73U16 Stage73_OriginalCollectionApplySelectedForm(void);

static Stage73U8 Stage73_MoveKnown(
    const void *mon,
    Stage73U16 move
)
{
    Stage73U8 slot;

    for (slot = 0; slot < STAGE73_MAX_MON_MOVES; ++slot) {
        if ((Stage73U16)STAGE73_GET_MON_DATA(
                mon, STAGE73_MON_DATA_MOVE1 + slot, (Stage73U8 *)0
            ) == move)
            return 1;
    }
    return 0;
}

static Stage73U8 Stage73_AppendUnique(
    Stage73U16 *moves,
    Stage73U8 count,
    Stage73U8 capacity,
    Stage73U16 move,
    const void *mon,
    Stage73U8 ignore_known
)
{
    Stage73U8 index;

    if (move == STAGE73_MOVE_NONE || count >= capacity)
        return count;
    if (ignore_known && Stage73_MoveKnown(mon, move))
        return count;
    for (index = 0; index < count; ++index) {
        if (moves[index] == move)
            return count;
    }
    moves[count] = move;
    return (Stage73U8)(count + 1u);
}

static Stage73U8 Stage73_AppendTable(
    const Stage73U16 *index,
    const Stage73U16 *table,
    Stage73U16 species,
    Stage73U16 *moves,
    Stage73U8 count,
    Stage73U8 capacity,
    const void *mon,
    Stage73U8 ignore_known
)
{
    Stage73U16 cursor;
    Stage73U16 end;

    if (species >= STAGE73_SPECIES_COUNT)
        return count;
    cursor = index[species];
    end = index[(Stage73U16)(species + 1u)];
    while (cursor < end && count < capacity) {
        count = Stage73_AppendUnique(
            moves, count, capacity, table[cursor], mon, ignore_known
        );
        ++cursor;
    }
    return count;
}

Stage73U8 Stage73_IsExactEggConflictSpecies(Stage73U16 species)
{
    switch (species) {
    case 203u:
    case 324u:
    case 364u:
    case 608u:
    case 719u:
    case 724u:
    case 727u:
        return 1;
    default:
        return 0;
    }
}

Stage73U8 Stage73_GetAllEggMoves(
    void *mon,
    Stage73U16 *moves,
    Stage73U8 ignore_already_known
)
{
    Stage73U16 species = (Stage73U16)STAGE73_GET_MON_DATA(
        mon, STAGE73_MON_DATA_SPECIES, (Stage73U8 *)0
    );

    /* Only the seven audited collisions bypass legacy baby/incense union. */
    if (!Stage73_IsExactEggConflictSpecies(species))
        return Stage73_OriginalGetAllEggMoves(
            mon, moves, ignore_already_known
        );
    return Stage73_AppendTable(
        Stage73_ExactEggIndex,
        Stage73_ExactEggMoves,
        species,
        moves,
        0,
        STAGE73_MAX_RELEARNER_MOVES,
        mon,
        ignore_already_known
    );
}

static Stage73U8 Stage73_NormalRelearnerMoves(
    void *mon,
    Stage73U16 *moves
)
{
    const volatile Stage73U8 *learnset;
    Stage73U32 root_address;
    Stage73U16 species;
    Stage73U8 level;
    Stage73U8 count = 0;
    Stage73U8 index;

    species = (Stage73U16)STAGE73_GET_MON_DATA(
        mon, STAGE73_MON_DATA_SPECIES, (Stage73U8 *)0
    );
    level = (Stage73U8)STAGE73_GET_MON_DATA(
        mon, STAGE73_MON_DATA_LEVEL, (Stage73U8 *)0
    );
    if (species >= STAGE73_SPECIES_COUNT)
        return 0;
    root_address = *(const volatile Stage73U32 *)0x0804346Cu;
    if (root_address < 0x08000000u || root_address >= 0x0A000000u)
        return 0;
    root_address = *(const volatile Stage73U32 *)(
        root_address + (Stage73U32)species * 4u
    );
    if (root_address < 0x08000000u || root_address >= 0x0A000000u)
        return 0;
    learnset = (const volatile Stage73U8 *)root_address;

    /* Preserve the Stage25 Move Memory 40-row level ABI exactly. */
    for (index = 0; index < STAGE73_MAX_LEVEL_ROWS; ++index) {
        Stage73U16 move = (Stage73U16)(
            learnset[0] | (Stage73U16)learnset[1] << 8
        );
        Stage73U8 move_level = learnset[2];
        learnset += 3;
        if (move == STAGE73_MOVE_NONE && move_level == 0xFFu)
            break;
        if (move != STAGE73_MOVE_NONE && move_level <= level) {
            count = Stage73_AppendUnique(
                moves,
                count,
                STAGE73_MAX_RELEARNER_MOVES,
                move,
                mon,
                1
            );
        }
    }
    return Stage73_AppendTable(
        Stage73_ReminderIndex,
        Stage73_ReminderMoves,
        species,
        moves,
        count,
        STAGE73_MAX_RELEARNER_MOVES,
        mon,
        1
    );
}

Stage73U8 Stage73_GetMoveRelearnerMoves(void *mon, Stage73U16 *moves)
{
    Stage73U16 egg_moves[STAGE73_EGG_MOVE_BUFFER_COUNT];
    Stage73U16 species;
    Stage73U8 egg_count;
    Stage73U8 count;
    Stage73U8 index;

    if (STAGE73_MOVE_MEMORY_MODE != STAGE73_MOVE_MEMORY_MODE_EGG)
        return Stage73_NormalRelearnerMoves(mon, moves);
    species = (Stage73U16)STAGE73_GET_MON_DATA(
        mon, STAGE73_MON_DATA_SPECIES, (Stage73U8 *)0
    );
    /*
     * Keep the already-connected normal egg pool, then add the distinct
     * shared-egg consumer.  The shared rows never enter GetEggMoves/daycare.
     */
    egg_count = Stage73_GetAllEggMoves(mon, egg_moves, 1);
    count = 0;
    for (index = 0;
         index < egg_count && index < STAGE73_EGG_MOVE_BUFFER_COUNT;
         ++index) {
        count = Stage73_AppendUnique(
            moves,
            count,
            STAGE73_MAX_RELEARNER_MOVES,
            egg_moves[index],
            mon,
            1
        );
    }
    return Stage73_AppendTable(
        Stage73_SharedIndex,
        Stage73_SharedMoves,
        species,
        moves,
        count,
        STAGE73_MAX_RELEARNER_MOVES,
        mon,
        1
    );
}

Stage73U16 Stage73_RotomSignatureMove(Stage73U16 species)
{
    switch (species) {
    case STAGE73_SPECIES_ROTOM_HEAT:
        return STAGE73_MOVE_OVERHEAT;
    case STAGE73_SPECIES_ROTOM_WASH:
        return STAGE73_MOVE_HYDRO_PUMP;
    case STAGE73_SPECIES_ROTOM_FROST:
        return STAGE73_MOVE_BLIZZARD;
    case STAGE73_SPECIES_ROTOM_FAN:
        return STAGE73_MOVE_AIR_SLASH;
    case STAGE73_SPECIES_ROTOM_MOW:
        return STAGE73_MOVE_LEAF_STORM;
    default:
        return STAGE73_MOVE_NONE;
    }
}

typedef struct Stage73MoveSnapshot {
    Stage73U16 moves[STAGE73_MAX_MON_MOVES];
    Stage73U8 pp[STAGE73_MAX_MON_MOVES];
    Stage73U8 pp_bonuses;
} Stage73MoveSnapshot;

static void Stage73_ReadMoveSnapshot(
    void *mon,
    Stage73MoveSnapshot *snapshot
)
{
    Stage73U8 slot;

    for (slot = 0; slot < STAGE73_MAX_MON_MOVES; ++slot) {
        snapshot->moves[slot] = (Stage73U16)STAGE73_GET_MON_DATA(
            mon, STAGE73_MON_DATA_MOVE1 + slot, (Stage73U8 *)0
        );
        snapshot->pp[slot] = (Stage73U8)STAGE73_GET_MON_DATA(
            mon, STAGE73_MON_DATA_PP1 + slot, (Stage73U8 *)0
        );
    }
    snapshot->pp_bonuses = (Stage73U8)STAGE73_GET_MON_DATA(
        mon, STAGE73_MON_DATA_PP_BONUSES, (Stage73U8 *)0
    );
}

static void Stage73_RestoreMoveSnapshot(
    void *mon,
    const Stage73MoveSnapshot *snapshot
)
{
    Stage73U8 slot;

    for (slot = 0; slot < STAGE73_MAX_MON_MOVES; ++slot) {
        STAGE73_SET_MON_DATA(
            mon, STAGE73_MON_DATA_MOVE1 + slot, &snapshot->moves[slot]
        );
        STAGE73_SET_MON_DATA(
            mon, STAGE73_MON_DATA_PP1 + slot, &snapshot->pp[slot]
        );
    }
    STAGE73_SET_MON_DATA(
        mon, STAGE73_MON_DATA_PP_BONUSES, &snapshot->pp_bonuses
    );
}

static Stage73U8 Stage73_FindMoveSlot(
    const Stage73MoveSnapshot *snapshot,
    Stage73U16 move
)
{
    Stage73U8 slot;

    for (slot = 0; slot < STAGE73_MAX_MON_MOVES; ++slot) {
        if (snapshot->moves[slot] == move)
            return slot;
    }
    return STAGE73_MAX_MON_MOVES;
}

static Stage73U8 Stage73_FindAnyRotomOrEmptySlot(
    const Stage73MoveSnapshot *snapshot
)
{
    Stage73U8 slot;

    for (slot = 0; slot < STAGE73_MAX_MON_MOVES; ++slot) {
        if (Stage73_RotomSignatureMove(STAGE73_SPECIES_ROTOM_HEAT)
                == snapshot->moves[slot]
            || Stage73_RotomSignatureMove(STAGE73_SPECIES_ROTOM_WASH)
                == snapshot->moves[slot]
            || Stage73_RotomSignatureMove(STAGE73_SPECIES_ROTOM_FROST)
                == snapshot->moves[slot]
            || Stage73_RotomSignatureMove(STAGE73_SPECIES_ROTOM_FAN)
                == snapshot->moves[slot]
            || Stage73_RotomSignatureMove(STAGE73_SPECIES_ROTOM_MOW)
                == snapshot->moves[slot])
            return slot;
    }
    return Stage73_FindMoveSlot(snapshot, STAGE73_MOVE_NONE);
}

static void Stage73_RemoveMoveAndCompact(void *mon, Stage73U8 slot)
{
    Stage73U8 index;

    STAGE73_SET_MON_MOVE_SLOT(mon, STAGE73_MOVE_NONE, slot);
    STAGE73_REMOVE_MON_PP_BONUS(mon, slot);
    for (index = slot; index + 1u < STAGE73_MAX_MON_MOVES; ++index)
        STAGE73_SHIFT_MOVE_SLOT(mon, index, (Stage73U8)(index + 1u));
}

Stage73U16 Stage73_CollectionApplySelectedForm(void)
{
    Stage73U16 pending = STAGE73_COLLECTION_PENDING_INDEX;
    Stage73U16 slot = STAGE73_SPECIAL_VAR_8004;
    Stage73U16 target_species;
    Stage73U16 current_species;
    Stage73U16 signature;
    Stage73U16 result;
    Stage73U8 move_slot;
    void *mon;
    Stage73MoveSnapshot snapshot;

    if (pending < STAGE73_COLLECTION_ROTOM_FIRST_INDEX
        || pending > STAGE73_COLLECTION_ROTOM_LAST_INDEX)
        return Stage73_OriginalCollectionApplySelectedForm();
    if (slot >= STAGE73_COLLECTION_PARTY_SIZE)
        return Stage73_OriginalCollectionApplySelectedForm();

    target_species = (Stage73U16)(
        STAGE73_SPECIES_ROTOM_HEAT
        + pending - STAGE73_COLLECTION_ROTOM_FIRST_INDEX
    );
    mon = (void *)(STAGE73_PLAYER_PARTY
        + (Stage73U32)slot * STAGE73_POKEMON_SIZE);
    current_species = (Stage73U16)STAGE73_GET_MON_DATA(
        mon, STAGE73_MON_DATA_SPECIES2, (Stage73U8 *)0
    );
    if (current_species != STAGE73_SPECIES_ROTOM
        && current_species != target_species)
        return Stage73_OriginalCollectionApplySelectedForm();

    Stage73_ReadMoveSnapshot(mon, &snapshot);
    signature = Stage73_RotomSignatureMove(target_species);
    if (current_species == STAGE73_SPECIES_ROTOM) {
        move_slot = Stage73_FindAnyRotomOrEmptySlot(&snapshot);
        if (move_slot >= STAGE73_MAX_MON_MOVES) {
            /* Never silently delete a user move.  Move Memory can make room. */
            STAGE73_COLLECTION_LAST_RESULT =
                STAGE73_COLLECTION_RESULT_EFFECTLESS;
            STAGE73_SPECIAL_RESULT = STAGE73_COLLECTION_RESULT_EFFECTLESS;
            return STAGE73_COLLECTION_RESULT_EFFECTLESS;
        }
        STAGE73_SET_MON_MOVE_SLOT(mon, signature, move_slot);
    } else {
        move_slot = Stage73_FindMoveSlot(&snapshot, signature);
        if (move_slot < STAGE73_MAX_MON_MOVES)
            Stage73_RemoveMoveAndCompact(mon, move_slot);
    }

    /* The existing owner now persists species and the pre-applied move atomically. */
    result = Stage73_OriginalCollectionApplySelectedForm();
    if (result != STAGE73_COLLECTION_RESULT_SUCCESS) {
        Stage73_RestoreMoveSnapshot(mon, &snapshot);
        /*
         * The owner already made its best-effort species rollback save before
         * returning.  Persist our restored move bytes once more so a transient
         * first-write failure cannot leave the save one step behind RAM.
         */
        if (!STAGE73_COLLECTION_TEST_MODE)
            (void)STAGE73_TRY_SAVING_DATA(0);
    }
    return result;
}

Stage73U32 Stage73_RuntimeProbe(Stage73U32 query)
{
    switch (query) {
    case 0:
        return 0x50333733u; /* "P373" */
    case 1:
        return STAGE73_SPECIES_COUNT;
    case 2:
        return STAGE73_MAX_RELEARNER_MOVES;
    case 3:
        return Stage73_RotomSignatureMove(STAGE73_SPECIES_ROTOM_MOW);
    default:
        return 0;
    }
}
