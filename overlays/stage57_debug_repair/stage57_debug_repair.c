/*
 * USER-20260827-STAGE56-COMPREHENSIVE-DEBUG-REPAIR
 *
 * Stage56でSpeciesだけを書き換えていた経路を、nicknameと初期技まで含む
 * 一貫した個体更新へ収束させる。既存のCollection Supply ABIは変えず、
 * Stage57のcallsiteだけをこの薄いadapterへ向ける。
 */

#include <stdint.h>

typedef uint8_t u8;
typedef int32_t s32;
typedef uint16_t u16;
typedef uint32_t u32;

#define PTR(type, address) ((type)(uintptr_t)(address))
#define STAGE57_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

enum {
    STAGE57_ABI_VERSION = 0x35374442u, /* "BD75" in little endian */
    STAGE57_MON_DATA_NICKNAME = 2,
    STAGE57_MON_DATA_SPECIES = 11,
    STAGE57_SPECIES_COUNT = 1621,
    STAGE57_SPECIES_NAME_LENGTH = 11,
};

typedef u32 (*GetMonDataFn)(const void *, s32, u8 *);
typedef void (*SetMonDataFn)(void *, s32, const void *);
typedef void (*GetSpeciesNameFn)(u8 *, u16);
typedef u8 (*ApplyWildInitialMovesFn)(void *);
typedef u8 (*WildGenerateFn)(const void *, u8, u8);
typedef u8 (*MenuInitCursorFn)(u8, u8, u8, u8, u8, u8, u8);

#define FN_GET_MON_DATA PTR(GetMonDataFn, 0x0803F355u)
#define FN_SET_MON_DATA PTR(SetMonDataFn, 0x0803FA71u)
#define FN_GET_SPECIES_NAME PTR(GetSpeciesNameFn, 0x09FDA145u)
#define FN_APPLY_WILD_INITIAL_MOVES \
    PTR(ApplyWildInitialMovesFn, 0x093925F5u)
#define FN_COLLECTION_WILD_GENERATE PTR(WildGenerateFn, 0x09405DC9u)
#define FN_MENU_INIT_CURSOR PTR(MenuInitCursorFn, 0x0811030Du)
#define G_ENEMY_PARTY PTR(void *, 0x02023F8Cu)

static u8 names_equal(const u8 *left, const u8 *right)
{
    u8 index;
    for (index = 0u; index < STAGE57_SPECIES_NAME_LENGTH; ++index) {
        if (left[index] != right[index])
            return 0u;
        if (left[index] == 0xFFu)
            return 1u;
    }
    return 1u;
}

static void canonical_name(u8 *destination, u16 species)
{
    u8 index;
    for (index = 0u; index < STAGE57_SPECIES_NAME_LENGTH; ++index)
        destination[index] = 0xFFu;
    if (species < STAGE57_SPECIES_COUNT)
        FN_GET_SPECIES_NAME(destination, species);
}

/*
 * 通常のform changeではユーザーが付けたnicknameを保持する。変更前または
 * 変更後のcanonical名と一致するdefault名だけを、新Species名へ同期する。
 * wild側は下のNormalizeMonIdentityで無条件にcanonical化する。
 */
STAGE57_EXPORT(Stage57Debug_SetSpeciesWithCanonicalName)
void Stage57Debug_SetSpeciesWithCanonicalName(void *mon, s32 field,
                                               const void *value)
{
    u8 old_name[STAGE57_SPECIES_NAME_LENGTH];
    u8 new_name[STAGE57_SPECIES_NAME_LENGTH];
    u8 nickname[STAGE57_SPECIES_NAME_LENGTH];
    u16 old_species;
    u16 new_species;
    u8 default_name;

    if (mon == (void *)0 || value == (const void *)0)
        return;
    if (field != STAGE57_MON_DATA_SPECIES) {
        FN_SET_MON_DATA(mon, field, value);
        return;
    }
    old_species = (u16)FN_GET_MON_DATA(mon, STAGE57_MON_DATA_SPECIES,
                                      (u8 *)0);
    new_species = (u16)((const u8 *)value)[0]
        | (u16)((const u8 *)value)[1] << 8;
    canonical_name(old_name, old_species);
    canonical_name(new_name, new_species);
    FN_GET_MON_DATA(mon, STAGE57_MON_DATA_NICKNAME, nickname);
    default_name = (u8)(names_equal(nickname, old_name)
                        || names_equal(nickname, new_name));

    FN_SET_MON_DATA(mon, field, value);
    if (default_name)
        FN_SET_MON_DATA(mon, STAGE57_MON_DATA_NICKNAME, new_name);
}

STAGE57_EXPORT(Stage57Debug_NormalizeMonIdentity)
u16 Stage57Debug_NormalizeMonIdentity(void *mon, u8 reset_wild_moves)
{
    u8 name[STAGE57_SPECIES_NAME_LENGTH];
    u16 species;
    if (mon == (void *)0)
        return 0u;
    species = (u16)FN_GET_MON_DATA(mon, STAGE57_MON_DATA_SPECIES, (u8 *)0);
    if (species == 0u || species >= STAGE57_SPECIES_COUNT)
        return species;
    canonical_name(name, species);
    FN_SET_MON_DATA(mon, STAGE57_MON_DATA_NICKNAME, name);
    if (reset_wild_moves)
        (void)FN_APPLY_WILD_INITIAL_MOVES(mon);
    return species;
}

STAGE57_EXPORT(Stage57Debug_TryGenerateWildMonAdapter)
u8 Stage57Debug_TryGenerateWildMonAdapter(const void *info, u8 area, u8 flags)
{
    u8 result = FN_COLLECTION_WILD_GENERATE(info, area, flags);
    if (result)
        (void)Stage57Debug_NormalizeMonIdentity(G_ENEMY_PARTY, 1u);
    return result;
}

/*
 * Stage38 Factory menuはcursorHeightへchoice count、numChoicesへ0を渡して
 * いた。既存binary ABIの第5引数（count）を受け取り、engineの正しい
 * 7引数契約へ並べ直す。source側も同じ16/count契約へ修正済み。
 */
STAGE57_EXPORT(Stage57Debug_FactoryMenuInitCursorAdapter)
u8 Stage57Debug_FactoryMenuInitCursorAdapter(u8 window, u8 font, u8 left,
                                              u8 top, u8 authored_count,
                                              u8 ignored_num_choices,
                                              u8 initial_cursor)
{
    (void)ignored_num_choices;
    return FN_MENU_INIT_CURSOR(window, font, left, top, 16u,
                               authored_count, initial_cursor);
}

STAGE57_EXPORT(Stage57Debug_Probe)
u32 Stage57Debug_Probe(u32 query)
{
    if (query == 0u)
        return STAGE57_ABI_VERSION;
    if (query == 1u)
        return STAGE57_SPECIES_COUNT;
    if (query == 2u)
        return STAGE57_SPECIES_NAME_LENGTH;
    return 0u;
}
