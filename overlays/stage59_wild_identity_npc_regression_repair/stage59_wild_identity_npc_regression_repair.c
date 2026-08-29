/*
 * USER-20260829-STAGE59-WILD-IDENTITY-NPC-REGRESSION-REPAIR
 *
 * Stage57 already makes Collection Supply's Species writes atomic and wraps
 * the land/water generator.  Stage59 closes the remaining entry-point gap by
 * applying the same canonical wild-name postcondition to land/water, fishing,
 * and hidden/scanner encounters.  Fishing and hidden encounters intentionally
 * keep their authored move sets: only the default nickname is normalized.
 */

#include <stdint.h>

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

#define PTR(type, address) ((type)(uintptr_t)(address))
#define STAGE59_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

enum {
    STAGE59_ABI_VERSION = 0x35394449u, /* "ID95" in little endian */
    STAGE59_SPECIES_COUNT = 1621u,
};

typedef u16 (*NormalizeMonIdentityFn)(void *, u8);
typedef u8 (*LandWaterGenerateFn)(const void *, u8, u8);
typedef u16 (*FishingGenerateFn)(const void *, u8);
typedef u8 (*HiddenGenerateFn)(void);

/* Exact Stage58 delegates, pinned by the Stage58 ROM SHA-256 and guarded by
 * expected bytes in the Stage59 builder. */
#define FN_STAGE57_NORMALIZE \
    PTR(NormalizeMonIdentityFn, 0x09414159u)
#define FN_STAGE58_LAND_WATER \
    PTR(LandWaterGenerateFn, 0x094141BDu)
#define FN_STAGE58_FISHING \
    PTR(FishingGenerateFn, 0x093BEA69u)
#define FN_STAGE58_HIDDEN \
    PTR(HiddenGenerateFn, 0x093BEA99u)
#define G_ENEMY_PARTY PTR(void *, 0x02023F8Cu)

STAGE59_EXPORT(Stage59Repair_NormalizeEnemyPartyIdentity)
u16 Stage59Repair_NormalizeEnemyPartyIdentity(void)
{
    /* reset_wild_moves=0 keeps fishing/hidden research-profile egg moves and
     * other authored post-generation move changes intact. */
    return FN_STAGE57_NORMALIZE(G_ENEMY_PARTY, 0u);
}

STAGE59_EXPORT(Stage59Repair_TryGenerateWildMonAdapter)
u8 Stage59Repair_TryGenerateWildMonAdapter(const void *info, u8 area, u8 flags)
{
    u8 result = FN_STAGE58_LAND_WATER(info, area, flags);
    if (result)
        (void)Stage59Repair_NormalizeEnemyPartyIdentity();
    return result;
}

STAGE59_EXPORT(Stage59Repair_GenerateFishingEncounterAdapter)
u16 Stage59Repair_GenerateFishingEncounterAdapter(const void *info, u8 rod)
{
    u16 species = FN_STAGE58_FISHING(info, rod);
    if (species != 0u)
        (void)Stage59Repair_NormalizeEnemyPartyIdentity();
    return species;
}

STAGE59_EXPORT(Stage59Repair_TryHiddenEncounterAdapter)
u8 Stage59Repair_TryHiddenEncounterAdapter(void)
{
    u8 result = FN_STAGE58_HIDDEN();
    if (result)
        (void)Stage59Repair_NormalizeEnemyPartyIdentity();
    return result;
}

STAGE59_EXPORT(Stage59Repair_Probe)
u32 Stage59Repair_Probe(u32 query)
{
    if (query == 0u)
        return STAGE59_ABI_VERSION;
    if (query == 1u)
        return STAGE59_SPECIES_COUNT;
    if (query == 2u)
        return 0x094141BDu;
    if (query == 3u)
        return 0x093BEA69u;
    if (query == 4u)
        return 0x093BEA99u;
    if (query == 5u)
        return 0x09414159u;
    return 0u;
}
