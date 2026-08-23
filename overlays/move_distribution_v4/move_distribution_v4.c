#include "move_distribution_v4.h"

#include <stdint.h>

#include "move_distribution_v4_generated.h"

typedef uint8_t u8;
typedef int32_t s32;
typedef uint16_t u16;
typedef uint32_t u32;

#define PTR(type, address) ((type)(uintptr_t)(address))
#define MD_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

typedef u32 (*GetMonDataFn)(void *, s32, u8 *);
typedef void (*RemoveMonPpBonusFn)(void *, u8);
typedef void (*SetMonMoveSlotFn)(void *, u16, u8);
typedef u16 (*GiveMoveToBoxMonFn)(void *, u16);
typedef void (*DeleteFirstMoveAndGiveMoveToBoxMonFn)(void *, u16);
typedef u8 (*WildGenerateFn)(const void *, u8, u8);
typedef u16 (*FishingGenerateFn)(const void *, u8);
typedef u8 (*HiddenGenerateFn)(void);

#define FN_GET_MON_DATA PTR(GetMonDataFn, 0x0803F355u)
#define FN_REMOVE_MON_PP_BONUS PTR(RemoveMonPpBonusFn, 0x08040755u)
#define FN_SET_MON_MOVE_SLOT PTR(SetMonMoveSlotFn, 0x09114699u)
#define FN_GIVE_MOVE_TO_BOX_MON PTR(GiveMoveToBoxMonFn, 0x0803E01Du)
#define FN_DELETE_FIRST_MOVE_AND_GIVE_MOVE_TO_BOX_MON \
    PTR(DeleteFirstMoveAndGiveMoveToBoxMonFn, 0x0803E3ADu)
#define FN_WILD_GENERATE PTR(WildGenerateFn, MD_QOL_WILD_GENERATE_ADDRESS)
#define FN_FISHING_GENERATE PTR(FishingGenerateFn, MD_QOL_FISHING_GENERATE_ADDRESS)
#define FN_HIDDEN_GENERATE PTR(HiddenGenerateFn, MD_QOL_HIDDEN_GENERATE_ADDRESS)

enum {
    MD_MON_DATA_SPECIES = 11,
    MD_SPECIES_COUNT = 1621,
    MD_LEVEL_SCAN_LIMIT = 256,
    MD_FORM_RECORD_SIZE = 14
};

static u16 read16(const u8 *source)
{
    return (u16)(source[0] | (u16)source[1] << 8);
}

MD_EXPORT(MoveDistributionV4_Probe)
u32 MoveDistributionV4_Probe(u32 selector)
{
    switch (selector) {
    case 0: return 0x4D443439u; /* MD49 */
    case 1: return MD_LEVEL_UP_ROW_COUNT;
    case 2: return MD_EGG_ROW_COUNT;
    case 3: return MD_TM_TUTOR_CHANGE_COUNT;
    case 4: return MD_FORM_RECORD_COUNT;
    case 5: return MD_WILD_ROW_COUNT;
    case 6: return MD_LEVEL_UP_ROOT_ADDRESS;
    case 7: return MD_EGG_ROOT_ADDRESS;
    case 8: return MD_TMHM_ROOT_ADDRESS;
    case 9: return MD_TUTOR_ROOT_ADDRESS;
    default: return 0;
    }
}

MD_EXPORT(MoveDistributionV4_ResolveFormDomain)
u16 MoveDistributionV4_ResolveFormDomain(u16 record, u8 domain)
{
    const u8 *row;
    if (record >= MD_FORM_RECORD_COUNT || domain > MOVE_DISTRIBUTION_DOMAIN_WILD)
        return 0xFFFFu;
    row = PTR(const u8 *, MD_FORM_TABLE_ADDRESS)
        + (u32)record * MD_FORM_RECORD_SIZE;
    if (domain == MOVE_DISTRIBUTION_DOMAIN_LEVEL_UP)
        return read16(row + 4);
    if (domain == MOVE_DISTRIBUTION_DOMAIN_EGG)
        return read16(row + 6);
    if (domain == MOVE_DISTRIBUTION_DOMAIN_TM_TUTOR)
        return read16(row + 8);
    return read16(row + 10);
}

MD_EXPORT(MoveDistributionV4_ApplyWildInitialMoves)
u8 MoveDistributionV4_ApplyWildInitialMoves(void *mon)
{
    const u8 *row;
    u16 species;
    u8 slot;
    if (mon == (void *)0)
        return 0;
    species = (u16)FN_GET_MON_DATA(mon, MD_MON_DATA_SPECIES, (u8 *)0);
    if (species >= MD_SPECIES_COUNT)
        return 0;
    row = PTR(const u8 *, MD_WILD_TABLE_ADDRESS) + (u32)species * 8u;
    if (read16(row) == 0u)
        return 0;
    for (slot = 0; slot < 4u; ++slot) {
        u16 move = read16(row + (u32)slot * 2u);
        if (move == 0u)
            return 0;
        FN_REMOVE_MON_PP_BONUS(mon, slot);
        FN_SET_MON_MOVE_SLOT(mon, move, slot);
    }
    return 1;
}

MD_EXPORT(MoveDistributionV4_GiveInitialMoves)
void MoveDistributionV4_GiveInitialMoves(void *box_mon, u16 species, u8 level)
{
    const u8 *const *root;
    const u8 *row;
    u16 index;
    if (box_mon == (void *)0 || species >= MD_SPECIES_COUNT)
        return;
    root = PTR(const u8 *const *, MD_LEVEL_UP_ROOT_ADDRESS);
    row = root[species];
    for (index = 0; index < MD_LEVEL_SCAN_LIMIT; ++index, row += 3) {
        u16 move = read16(row);
        u8 learned_at = row[2];
        if (move == 0u && learned_at == 0xFFu)
            break;
        if (learned_at > level)
            break;
        if (move == 0u)
            continue;
        if (FN_GIVE_MOVE_TO_BOX_MON(box_mon, move) == 0xFFFFu)
            FN_DELETE_FIRST_MOVE_AND_GIVE_MOVE_TO_BOX_MON(box_mon, move);
    }
}

MD_EXPORT(MoveDistributionV4_TryGenerateWildMonAdapter)
u8 MoveDistributionV4_TryGenerateWildMonAdapter(const void *info, u8 area,
                                                  u8 flags)
{
    u8 result = FN_WILD_GENERATE(info, area, flags);
    if (result)
        (void)MoveDistributionV4_ApplyWildInitialMoves(
            PTR(void *, MD_ENEMY_PARTY_ADDRESS));
    return result;
}

MD_EXPORT(MoveDistributionV4_GenerateFishingEncounterAdapter)
u16 MoveDistributionV4_GenerateFishingEncounterAdapter(const void *info, u8 rod)
{
    u16 species = FN_FISHING_GENERATE(info, rod);
    if (species != 0u)
        (void)MoveDistributionV4_ApplyWildInitialMoves(
            PTR(void *, MD_ENEMY_PARTY_ADDRESS));
    return species;
}

MD_EXPORT(MoveDistributionV4_TryHiddenEncounterAdapter)
u8 MoveDistributionV4_TryHiddenEncounterAdapter(void)
{
    u8 result = FN_HIDDEN_GENERATE();
    if (result)
        (void)MoveDistributionV4_ApplyWildInitialMoves(
            PTR(void *, MD_ENEMY_PARTY_ADDRESS));
    return result;
}
