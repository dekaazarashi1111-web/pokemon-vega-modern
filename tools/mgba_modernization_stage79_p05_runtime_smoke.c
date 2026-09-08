/*
 * Stage79 cumulative-ROM P05 runtime smoke for libmGBA 0.10.2.
 *
 * Every relocated address is supplied by the caller from the pinned Stage76,
 * Stage77, and Stage78 symbol/config contracts.  The runner verifies all 29
 * Stage77 hook sites still enter their dispatchers, and then stops execution
 * exactly when each dispatcher reaches either its Stage72 wrapper or its
 * Stage72 original trampoline.  This makes the Battle Circus predicate and
 * the 12-byte veneer r3/r12 ABI observable without invoking an unrelated
 * battle scheduler route.
 *
 * Stage76's three completed edges are checked as linked exact-ROM code:
 * Mega Sol uses its production dispatcher, while Piercing Drill and Spicy
 * Spray exercise their exported policy helpers with the result of the ROM's
 * real IsAbilitySuppressed routine.  It also executes Stage78's exact 32-case
 * Eelevate pure matrix and both production hook veneers/entries with bounded
 * engine-call stubs.  This bounded runner is not full scheduler acceptance.
 */
#define BATTLE_CORE_EMBEDDED
#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1
#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203DB00U
#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203DF80U
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#include "mgba_battle_core_smoke.c"
#pragma GCC diagnostic pop

#include <errno.h>

#define P05X_CIRCUS_ABILITY_SUPPRESSION UINT32_C(0x80000000)

enum {
    P05X_MAX_ARGS = 192,
    P05X_DISPATCHER_COUNT = 29,
    P05X_SURFACE_OCCURRENCE_COUNT = 33,
    P05X_ROUTE_STEP_LIMIT = 128,

    P05X_BATTLE_TYPE_CIRCUS = 0x04000000U,
    P05X_ADJACENT_BATTLE_TYPE = 0x02000000U,
    P05X_ADJACENT_CIRCUS_FLAG = 0x40000000U,

    P05X_ABILITY_MEGA_SOL = 315U,
    P05X_ABILITY_PIERCING_DRILL = 316U,
    P05X_SPICY_ALL_FLAGS = (1U << 13) - 1U,
    P05X_SPICY_PARTNER_ABILITY = 1U << 4,
    P05X_SPICY_BURN_BENEFIT = 1U << 10,

    P05X_MEGA_ROUTE_ORIGINAL = 0U,
    P05X_MEGA_ROUTE_FIRST_TURN = 1U,
    P05X_MEGA_ROUTE_POPUP = 2U,
    P05X_MOVE_PROTECT = 182U,
    P05X_MOVE_DETECT = 197U,
    P05X_MOVE_MAX_GUARD = 891U,
    P05X_EFFECT_OHKO = 38U,
    P05X_EFFECT_PRESENT = 122U,
    P05X_EFFECT_FUTURE_SIGHT = 148U,
    P05X_EFFECT_HEAL_TARGET = 233U,

    P05X_G_BATTLE_MONS = 0x02023B44U,
    P05X_G_BATTLERS_COUNT = 0x02023B2CU,
    P05X_G_BANK_ATTACKER = 0x02023CCBU,
    P05X_G_BATTLE_SCRIPT = 0x02023CD4U,
    P05X_G_HIT_MARKER = 0x02023D30U,
    P05X_G_BATTLE_WEATHER = 0x02023E7CU,
    P05X_G_BATTLE_SCRIPTING = 0x02023F24U,
    P05X_BATTLE_MON_ABILITY_OFFSET = 0x38U,
    P05X_BATTLE_MON_STATUS2_OFFSET = 0x50U,
    P05X_BATTLE_SCRIPTING_BANK_OFFSET = 0x17U,
    P05X_ORIGINAL_SOLAR_BEAM_SCRIPT = 0x090050C1U,

    P05X_ABILITY_EARTH_EATER = 298U,
    P05X_ABILITY_EELEVATE = 313U,
    P05X_ABILITY_NEUTRALIZING_GAS = 257U,
    P05X_ABILITY_MOLD_BREAKER = 105U,
    P05X_MOVE_THOUSAND_ARROWS = 643U,
    P05X_TYPE_GROUND = 4U,
    P05X_SPLIT_STATUS = 2U,
    P05X_EELEVATE_QUERY_SCRATCH = 0x0203CFC0U,
    P05X_EELEVATE_MON_SCRATCH = 0x0203CF00U,
    P05X_EELEVATE_BATTLE_MON_SCRATCH = 0x0203CF20U,
    P05X_EELEVATE_SPECIES_SENTINEL = 25U,
    P05X_EELEVATE_HP_SENTINEL = 100U,
    P05X_EELEVATE_ACTIVE_BANK = 2U,
};

struct P05xArg {
    char *key;
    uint32_t value;
};

struct P05xArgs {
    struct P05xArg rows[P05X_MAX_ARGS];
    size_t count;
};

struct P05xDispatcher {
    const char *suffix;
    uint8_t hook_width;
    uint8_t surface_occurrences;
    bool fifth_stack_argument;
};

struct P05xPredicateCase {
    uint32_t battle_flags;
    uint32_t circus_flags;
    bool suppressed;
};

struct P05xRouteObservation {
    uint32_t target;
    uint32_t instructions;
    bool registers_preserved;
    bool stack_preserved;
    bool fifth_stack_argument_preserved;
};

struct P05xEelevateQuery {
    uint16_t originalAbility;
    uint16_t move;
    uint8_t moveType;
    uint8_t moveSplit;
    uint8_t grounded;
    uint8_t targetAbilityIgnored;
    uint8_t abilityShield;
    uint8_t circusSuppressed;
    uint8_t abilitySuppressed;
    uint8_t neutralizingGasPresent;
};

struct P05xEelevateCase {
    const char *name;
    struct P05xEelevateQuery query;
    uint16_t expected;
};

_Static_assert(sizeof(struct P05xEelevateQuery) == 12U,
               "Stage78 Eelevate query ABI");

static const struct P05xEelevateCase P05X_EELEVATE_CASES[] = {
    {"eligible_physical_ground", {313U, 89U, 4U, 0U, 0U, 0U, 0U, 0U, 0U, 0U}, 298U},
    {"eligible_special_ground", {313U, 89U, 4U, 1U, 0U, 0U, 0U, 0U, 0U, 0U}, 298U},
    {"other_ability", {26U, 89U, 4U, 0U, 0U, 0U, 0U, 0U, 0U, 0U}, 26U},
    {"no_prediction", {313U, 0U, 4U, 0U, 0U, 0U, 0U, 0U, 0U, 0U}, 313U},
    {"prediction_switch", {313U, 65535U, 4U, 0U, 0U, 0U, 0U, 0U, 0U, 0U}, 313U},
    {"prediction_out_of_range", {313U, 1063U, 4U, 0U, 0U, 0U, 0U, 0U, 0U, 0U}, 313U},
    {"non_ground", {313U, 89U, 10U, 0U, 0U, 0U, 0U, 0U, 0U, 0U}, 313U},
    {"status_ground", {313U, 89U, 4U, 2U, 0U, 0U, 0U, 0U, 0U, 0U}, 313U},
    {"thousand_arrows", {313U, 643U, 4U, 0U, 0U, 0U, 0U, 0U, 0U, 0U}, 313U},
    {"gravity", {313U, 89U, 4U, 0U, 1U, 0U, 0U, 0U, 0U, 0U}, 313U},
    {"iron_ball", {313U, 89U, 4U, 0U, 1U, 0U, 0U, 0U, 0U, 0U}, 313U},
    {"rooted", {313U, 89U, 4U, 0U, 1U, 0U, 0U, 0U, 0U, 0U}, 313U},
    {"smack_down", {313U, 89U, 4U, 0U, 1U, 0U, 0U, 0U, 0U, 0U}, 313U},
    {"mold_breaker", {313U, 89U, 4U, 0U, 0U, 1U, 0U, 0U, 0U, 0U}, 313U},
    {"mold_breaker_shield", {313U, 89U, 4U, 0U, 0U, 1U, 1U, 0U, 0U, 0U}, 298U},
    {"teravolt", {313U, 89U, 4U, 0U, 0U, 1U, 0U, 0U, 0U, 0U}, 313U},
    {"teravolt_shield", {313U, 89U, 4U, 0U, 0U, 1U, 1U, 0U, 0U, 0U}, 298U},
    {"turboblaze", {313U, 89U, 4U, 0U, 0U, 1U, 0U, 0U, 0U, 0U}, 313U},
    {"turboblaze_shield", {313U, 89U, 4U, 0U, 0U, 1U, 1U, 0U, 0U, 0U}, 298U},
    {"mold_breaker_move", {313U, 89U, 4U, 0U, 0U, 1U, 0U, 0U, 0U, 0U}, 313U},
    {"mold_breaker_move_shield", {313U, 89U, 4U, 0U, 0U, 1U, 1U, 0U, 0U, 0U}, 298U},
    {"magic_room_disables_shield", {313U, 89U, 4U, 0U, 0U, 1U, 0U, 0U, 0U, 0U}, 313U},
    {"embargo_disables_shield", {313U, 89U, 4U, 0U, 0U, 1U, 0U, 0U, 0U, 0U}, 313U},
    {"circus", {313U, 89U, 4U, 0U, 0U, 0U, 0U, 1U, 0U, 0U}, 313U},
    {"circus_shield", {313U, 89U, 4U, 0U, 0U, 0U, 1U, 1U, 0U, 0U}, 313U},
    {"gastro_acid", {313U, 89U, 4U, 0U, 0U, 0U, 0U, 0U, 1U, 0U}, 313U},
    {"gastro_acid_shield", {313U, 89U, 4U, 0U, 0U, 0U, 1U, 0U, 1U, 0U}, 313U},
    {"neutralizing_gas", {313U, 89U, 4U, 0U, 0U, 0U, 0U, 0U, 0U, 1U}, 313U},
    {"neutralizing_gas_shield", {313U, 89U, 4U, 0U, 0U, 0U, 1U, 0U, 0U, 1U}, 298U},
    {"outgoing_active_sole_gas_excluded", {313U, 89U, 4U, 0U, 0U, 0U, 0U, 0U, 0U, 0U}, 298U},
    {"grounded_shield", {313U, 89U, 4U, 0U, 1U, 0U, 1U, 0U, 0U, 0U}, 313U},
    {"combined_ignore_gas_shield", {313U, 89U, 4U, 0U, 0U, 1U, 1U, 0U, 0U, 1U}, 298U},
};

struct P05xEelevateRuntimeCase {
    const char *name;
    bool party;
    uint8_t fallback;
    uint16_t original_ability;
    uint16_t move;
    uint8_t move_type;
    uint8_t grounded;
    uint8_t circus;
    uint8_t ability_suppressed;
    uint8_t gas_bank;
    uint8_t target_ignored;
    uint8_t shield;
    uint16_t expected;
    uint8_t absent_mask;
    uint8_t gas_dead;
    uint8_t battler_count;
};

#define P05X_NO_GAS UINT8_C(0xFF)

static const struct P05xEelevateRuntimeCase P05X_EELEVATE_RUNTIME_CASES[] = {
    {"active_foe1_ground", false, false, 313U, 89U, 4U, 0U, 0U, 0U, P05X_NO_GAS, 0U, 0U, 298U, 0U, 0U, 0U},
    {"party_foe2_fallback", true, true, 313U, 89U, 4U, 0U, 0U, 0U, P05X_NO_GAS, 0U, 0U, 298U, 0U, 0U, 0U},
    {"active_no_prediction", false, false, 313U, 0U, 4U, 0U, 0U, 0U, P05X_NO_GAS, 0U, 0U, 313U, 0U, 0U, 0U},
    {"party_non_ground", true, false, 313U, 89U, 10U, 0U, 0U, 0U, P05X_NO_GAS, 0U, 0U, 313U, 0U, 0U, 0U},
    {"active_status_ground", false, false, 313U, 45U, 4U, 0U, 0U, 0U, P05X_NO_GAS, 0U, 0U, 313U, 0U, 0U, 0U},
    {"party_thousand_arrows", true, false, 313U, 643U, 4U, 0U, 0U, 0U, P05X_NO_GAS, 0U, 0U, 313U, 0U, 0U, 0U},
    {"active_grounded", false, false, 313U, 89U, 4U, 1U, 0U, 0U, P05X_NO_GAS, 0U, 0U, 313U, 0U, 0U, 0U},
    {"party_grounded", true, false, 313U, 89U, 4U, 1U, 0U, 0U, P05X_NO_GAS, 0U, 0U, 313U, 0U, 0U, 0U},
    {"active_circus_shield", false, false, 313U, 89U, 4U, 0U, 1U, 0U, P05X_NO_GAS, 0U, 1U, 313U, 0U, 0U, 0U},
    {"active_gastro_shield", false, false, 313U, 89U, 4U, 0U, 0U, 1U, P05X_NO_GAS, 0U, 1U, 313U, 0U, 0U, 0U},
    {"party_neutralizing_gas", true, false, 313U, 89U, 4U, 0U, 0U, 0U, 0U, 0U, 0U, 313U, 0U, 0U, 0U},
    {"active_neutralizing_gas_shield", false, false, 313U, 89U, 4U, 0U, 0U, 0U, 0U, 0U, 1U, 298U, 0U, 0U, 0U},
    {"party_mold_breaker", true, false, 313U, 89U, 4U, 0U, 0U, 0U, P05X_NO_GAS, 1U, 0U, 313U, 0U, 0U, 0U},
    {"active_mold_breaker_shield", false, false, 313U, 89U, 4U, 0U, 0U, 0U, P05X_NO_GAS, 1U, 1U, 298U, 0U, 0U, 0U},
    {"active_outgoing_gas_excluded", false, false, 313U, 89U, 4U, 0U, 0U, 0U, 2U, 0U, 0U, 298U, 0U, 0U, 0U},
    {"party_other_ability", true, false, 26U, 89U, 4U, 0U, 0U, 0U, P05X_NO_GAS, 0U, 0U, 26U, 0U, 0U, 0U},
    {"active_foe2_fallback", false, true, 313U, 89U, 4U, 0U, 0U, 0U, P05X_NO_GAS, 0U, 0U, 298U, 0U, 0U, 0U},
    {"party_foe1_priority", true, 4U, 313U, 89U, 4U, 0U, 0U, 0U, P05X_NO_GAS, 0U, 0U, 298U, 0U, 0U, 0U},
    {"active_foe2_after_switch", false, 2U, 313U, 89U, 4U, 0U, 0U, 0U, P05X_NO_GAS, 0U, 0U, 298U, 0U, 0U, 0U},
    {"party_foe2_after_out_of_range", true, 3U, 313U, 89U, 4U, 0U, 0U, 0U, P05X_NO_GAS, 0U, 0U, 298U, 0U, 0U, 0U},
    {"active_absent_gas_excluded", false, false, 313U, 89U, 4U, 0U, 0U, 0U, 0U, 0U, 0U, 298U, 1U, 0U, 4U},
    {"party_dead_gas_excluded", true, false, 313U, 89U, 4U, 0U, 0U, 0U, 0U, 0U, 0U, 298U, 0U, 1U, 4U},
    {"active_battler_count_capped", false, false, 313U, 89U, 4U, 0U, 0U, 0U, 4U, 0U, 0U, 298U, 0U, 0U, 5U},
    {"party_outgoing_gastro_not_inherited", true, false, 313U, 89U, 4U, 0U, 0U, 1U, P05X_NO_GAS, 0U, 0U, 298U, 0U, 0U, 0U},
    {"party_mold_breaker_shield", true, false, 313U, 89U, 4U, 0U, 0U, 0U, P05X_NO_GAS, 1U, 1U, 298U, 0U, 0U, 0U},
    {"party_neutralizing_gas_shield", true, false, 313U, 89U, 4U, 0U, 0U, 0U, 0U, 0U, 1U, 298U, 0U, 0U, 0U},
};

static const struct P05xDispatcher P05X_DISPATCHERS[] = {
    {"AbilityBattleEffects", 12U, 1U, true},
    {"ProtectAffects", 12U, 1U, false},
    {"DoesProtectionMoveBlockMove", 12U, 1U, false},
    {"AccuracyCalc", 8U, 1U, false},
    {"VisualAccuracyCalc", 8U, 1U, false},
    {"VisualAccuracyCalcNoTarget", 8U, 1U, false},
    {"Atk01AccuracyCheck", 8U, 1U, false},
    {"ModifyGrowthInSun", 8U, 1U, false},
    {"NonInvasiveCheckGrounding", 12U, 1U, true},
    {"CheckMonGrounding", 8U, 1U, false},
    {"CheckGroundingByDetails", 8U, 1U, false},
    {"CheckGrounding", 8U, 1U, false},
    {"AttacksThisTurn", 8U, 1U, false},
    {"Atk49MoveEnd", 8U, 1U, false},
    {"AdjustBasePower", 8U, 2U, false},
    {"Atk4ATypeCalc2", 8U, 1U, false},
    {"Atk06TypeCalc", 8U, 1U, false},
    {"GetMoveTypeSpecialPostAbility", 8U, 1U, false},
    {"GetExceptionMoveType", 8U, 2U, false},
    {"GetMonExceptionMoveType", 8U, 2U, false},
    {"GetMoveTypeSpecialPreAbility", 8U, 1U, false},
    {"VisualTypeCalcPart", 8U, 1U, false},
    {"AITypeCalcPart", 12U, 1U, false},
    {"AISpecialTypeCalc", 8U, 1U, false},
    {"TypeCalc", 12U, 1U, true},
    {"CalcVisualBasePower", 12U, 1U, false},
    {"CalculateBaseDamage", 8U, 2U, false},
    {"RecoverBasedOnSunlight", 8U, 1U, false},
    {"SetMoveEffect2", 8U, 1U, false},
};

static const struct P05xPredicateCase P05X_PREDICATE_CASES[] = {
    {0U, 0U, false},
    {P05X_BATTLE_TYPE_CIRCUS, 0U, false},
    {0U, P05X_CIRCUS_ABILITY_SUPPRESSION, false},
    {P05X_ADJACENT_BATTLE_TYPE,
     P05X_CIRCUS_ABILITY_SUPPRESSION, false},
    {P05X_BATTLE_TYPE_CIRCUS, P05X_ADJACENT_CIRCUS_FLAG, false},
    {P05X_BATTLE_TYPE_CIRCUS,
     P05X_CIRCUS_ABILITY_SUPPRESSION, true},
    {UINT32_MAX, UINT32_MAX, true},
};

static const char *const P05X_GLOBAL_ARGS[] = {
    "Stage77_RuntimeProbe",
    "gBattleTypeFlags",
    "gBattleCircusFlags",
    "gStatuses3",
    "IsAbilitySuppressed",
    "Stage76_RuntimeProbe",
    "Stage76_PayloadStart",
    "Stage76_PayloadSize",
    "Stage76_MegaSolRoute",
    "Stage76_QuarterPredictedProtectDamage",
    "Stage76_NormalizePredictedProtectionMove",
    "Stage76_IsPlannedMaxGuard",
    "Stage76_DirectEffectCanDamagePartner",
    "Stage76_SelectAIAttackerAbility",
    "Stage76_SpicyPolicyCore",
    "Stage76_SpicyPathQualifies",
    "Stage76_DispatchMegaSolSolarBeam",
    "Stage76_BattleScriptMegaSolPopup",
    "HOOK_Stage76SolarBeam",
    "Stage76_BattleScriptSolarBeam",
    "HOOK_Stage76AICalcDmg",
    "Stage76_EntryAICalcDmg",
    "HOOK_Stage76AIScriptPartner",
    "Stage76_EntryAIScriptPartner",
    "HOOK_Stage76RangeMoveCanHurtPartner",
    "Stage76_EntryRangeMoveCanHurtPartner",
    "Stage78_RuntimeProbe",
    "Stage78_MapEelevateAbsorber",
    "Stage78_ActiveAbsorberAbility",
    "Stage78_PartyAbsorberAbility",
    "Stage78_EntryFindMonAbsorberActive",
    "Stage78_EntryFindMonAbsorberParty",
    "HOOK_FindMonAbsorberActiveAbilityBlock",
    "HOOK_FindMonAbsorberPartyAbilityBlock",
    "CONT_FindMonAbsorberActiveAbilityBlock",
    "CONT_FindMonAbsorberPartyAbilityBlock",
    "gBattlersCount",
    "gBattleMons",
    "gAbsentBattlerFlags",
    "gBattleMoves",
    "LoadBattlersAndFoes",
    "GetPredictedAIAbility",
    "GetAIAbility",
    "IsValidMovePrediction",
    "GetMonAbility",
    "GetBankItemEffect",
    "GetMonItemEffect",
    "CheckMonGrounding",
    "CheckGrounding",
    "IsTargetAbilityIgnored",
    "GetMoveTypeSpecial",
};

_Static_assert(ARRAY_LEN(P05X_DISPATCHERS) == P05X_DISPATCHER_COUNT,
               "Stage77 dispatcher count");

static void p05x_die(const char *message)
{
    fprintf(stderr, "mgba-modernization-stage79-p05: %s\n", message);
    exit(1);
}

static uint32_t p05x_parse_u32(const char *text, const char *label)
{
    char *end = NULL;
    errno = 0;
    unsigned long value = strtoul(text, &end, 0);
    if (errno != 0 || end == text || *end != '\0' || value > UINT32_MAX) {
        fprintf(stderr,
                "mgba-modernization-stage79-p05: invalid %s: %s\n",
                label, text);
        exit(2);
    }
    return (uint32_t)value;
}

static struct P05xArgs p05x_parse_args(int argc, char **argv)
{
    struct P05xArgs result = {0};
    for (int index = 3; index < argc; ++index) {
        const char *equal = strchr(argv[index], '=');
        if (equal == NULL || equal == argv[index] || equal[1] == '\0')
            p05x_die("contract argument must use NAME=VALUE");
        if (result.count >= P05X_MAX_ARGS)
            p05x_die("too many contract arguments");
        size_t key_length = (size_t)(equal - argv[index]);
        char *key = malloc(key_length + 1U);
        if (key == NULL)
            p05x_die("contract key allocation failed");
        memcpy(key, argv[index], key_length);
        key[key_length] = '\0';
        for (size_t prior = 0U; prior < result.count; ++prior) {
            if (strcmp(result.rows[prior].key, key) == 0)
                p05x_die("duplicate contract argument");
        }
        result.rows[result.count].key = key;
        result.rows[result.count].value = p05x_parse_u32(equal + 1, key);
        ++result.count;
    }
    return result;
}

static uint32_t p05x_arg(const struct P05xArgs *args, const char *key)
{
    for (size_t index = 0U; index < args->count; ++index) {
        if (strcmp(args->rows[index].key, key) == 0)
            return args->rows[index].value;
    }
    fprintf(stderr,
            "mgba-modernization-stage79-p05: missing contract argument: %s\n",
            key);
    exit(2);
}

static void p05x_free_args(struct P05xArgs *args)
{
    for (size_t index = 0U; index < args->count; ++index)
        free(args->rows[index].key);
    args->count = 0U;
}

static void p05x_key(char *buffer, size_t size,
                     const char *prefix, const char *suffix)
{
    int written = snprintf(buffer, size, "%s%s", prefix, suffix);
    if (written < 0 || (size_t)written >= size)
        p05x_die("generated contract key is too long");
}

static bool p05x_known_arg(const char *key)
{
    for (size_t index = 0U; index < ARRAY_LEN(P05X_GLOBAL_ARGS); ++index) {
        if (strcmp(key, P05X_GLOBAL_ARGS[index]) == 0)
            return true;
    }
    static const char *const prefixes[] = {
        "HOOK_", "DISPATCH_", "NORMAL_", "SUPPRESSED_",
    };
    char expected[96];
    for (size_t row = 0U; row < ARRAY_LEN(P05X_DISPATCHERS); ++row) {
        for (size_t prefix = 0U; prefix < ARRAY_LEN(prefixes); ++prefix) {
            p05x_key(expected, sizeof(expected), prefixes[prefix],
                     P05X_DISPATCHERS[row].suffix);
            if (strcmp(key, expected) == 0)
                return true;
        }
    }
    return false;
}

static void p05x_validate_arg_set(const struct P05xArgs *args)
{
    size_t expected = ARRAY_LEN(P05X_GLOBAL_ARGS)
        + ARRAY_LEN(P05X_DISPATCHERS) * 4U;
    if (args->count != expected)
        p05x_die("contract argument count mismatch");
    for (size_t index = 0U; index < args->count; ++index) {
        if (!p05x_known_arg(args->rows[index].key))
            p05x_die("unknown contract argument");
    }
    for (size_t index = 0U; index < ARRAY_LEN(P05X_GLOBAL_ARGS); ++index)
        (void)p05x_arg(args, P05X_GLOBAL_ARGS[index]);
    static const char *const prefixes[] = {
        "HOOK_", "DISPATCH_", "NORMAL_", "SUPPRESSED_",
    };
    char key[96];
    for (size_t row = 0U; row < ARRAY_LEN(P05X_DISPATCHERS); ++row) {
        for (size_t prefix = 0U; prefix < ARRAY_LEN(prefixes); ++prefix) {
            p05x_key(key, sizeof(key), prefixes[prefix],
                     P05X_DISPATCHERS[row].suffix);
            (void)p05x_arg(args, key);
        }
    }
}

static bool p05x_rom_address(uint32_t address)
{
    address &= ~1U;
    return address >= 0x08000000U && address < 0x0A000000U;
}

static bool p05x_ewram_address(uint32_t address)
{
    return address >= 0x02000000U && address < 0x02040000U;
}

static uint32_t p05x_thumb(uint32_t address)
{
    if (!p05x_rom_address(address))
        p05x_die("dynamic Thumb address is outside ROM");
    return address | 1U;
}

static bool p05x_pc_matches_target(uint32_t observed_pc,
                                   uint32_t thumb_target)
{
    uint32_t observed = observed_pc & ~1U;
    uint32_t entry = thumb_target & ~1U;
    /* Absolute-jump stepping can expose either the entry or Thumb entry + 2. */
    return observed == entry || observed == entry + 2U;
}

static uint32_t p05x_call(struct mCore *core, uint32_t function,
                          uint32_t r0, uint32_t r1,
                          uint32_t r2, uint32_t r3,
                          uint64_t *instructions, uint32_t *calls)
{
    struct CallObservation observed = call_bounded(
        core, p05x_thumb(function), r0, r1, r2, r3);
    if (observed.instructions == 0U)
        p05x_die("bounded direct call executed zero instructions");
    *instructions += observed.instructions;
    ++*calls;
    return observed.result;
}

static uint32_t p05x_read_u32_unaligned(struct mCore *core,
                                        uint32_t address)
{
    uint32_t value = 0U;
    for (unsigned byte = 0U; byte < 4U; ++byte)
        value |= (uint32_t)read8(core, address + byte) << (byte * 8U);
    return value;
}

static void p05x_require_hook(struct mCore *core,
                              uint32_t site, uint8_t width,
                              uint32_t target)
{
    if (!p05x_rom_address(site) || (site & 1U) != 0U
        || !p05x_rom_address(target))
        p05x_die("hook contract contains an invalid ROM address");
    uint32_t actual;
    if (width == 8U) {
        if (read16(core, site) != 0x4B00U
            || read16(core, site + 2U) != 0x4718U)
            p05x_die("8-byte hook veneer opcode mismatch");
        actual = read32(core, site + 4U);
    } else if (width == 12U) {
        if (read16(core, site) != 0x469CU
            || read16(core, site + 2U) != 0x4B01U
            || read16(core, site + 4U) != 0x4718U
            || read16(core, site + 6U) != 0x46C0U)
            p05x_die("12-byte hook veneer opcode mismatch");
        actual = read32(core, site + 8U);
    } else {
        p05x_die("unsupported hook width");
    }
    if (actual != p05x_thumb(target))
        p05x_die("hook veneer target mismatch");
}

static void p05x_require_stage78_hooks(struct mCore *core,
                                       const struct P05xArgs *args)
{
    uint32_t active = p05x_arg(
        args, "HOOK_FindMonAbsorberActiveAbilityBlock");
    uint32_t active_entry = p05x_arg(
        args, "Stage78_EntryFindMonAbsorberActive");
    uint32_t party = p05x_arg(
        args, "HOOK_FindMonAbsorberPartyAbilityBlock");
    uint32_t party_entry = p05x_arg(
        args, "Stage78_EntryFindMonAbsorberParty");
    if (active != 0x090A03E4U
        || read16(core, active) != 0x4B00U
        || read16(core, active + 2U) != 0x4718U
        || read32(core, active + 4U) != p05x_thumb(active_entry)
        || read16(core, active + 8U) != 0x46C0U
        || read16(core, active + 10U) != 0x46C0U
        || read16(core, active + 12U) != 0x46C0U
        || read16(core, active + 14U) != 0x46C0U)
        p05x_die("Stage78 active hook exact veneer mismatch");
    if (party != 0x090A0426U
        || read16(core, party) != 0x469CU
        || read16(core, party + 2U) != 0x4B00U
        || read16(core, party + 4U) != 0x4718U
        || p05x_read_u32_unaligned(core, party + 6U)
            != p05x_thumb(party_entry)
        || read16(core, party + 10U) != 0x46C0U)
        p05x_die("Stage78 party hook exact veneer mismatch");
    if (p05x_arg(args, "CONT_FindMonAbsorberActiveAbilityBlock")
            != 0x090A03F5U
        || p05x_arg(args, "CONT_FindMonAbsorberPartyAbilityBlock")
            != 0x090A0433U)
        p05x_die("Stage78 continuation exact ABI mismatch");
}

static struct P05xRouteObservation p05x_observe_route(
    struct mCore *core, uint32_t dispatcher,
    uint32_t normal, uint32_t suppressed,
    uint8_t hook_width, bool fifth_stack_argument)
{
    const uint32_t r0 = 0x11223344U;
    const uint32_t r1 = 0x55667788U;
    const uint32_t r2 = 0x99AABBCCU;
    const uint32_t original_r3 = 0x13579BDFU;
    const uint32_t fifth_argument = UINT32_C(0xC0DEF00D);
    struct P05xRouteObservation result = {0};
    struct CpuState original = capture_cpu_state(core);
    struct HostCallStack call_stack;
    begin_host_call_stack(
        core, &call_stack,
        fifth_stack_argument ? &fifth_argument : NULL,
        fifth_stack_argument ? 1U : 0U);
    uint32_t cpsr = (uint32_t)original.registers[16];
    write_register(core, "cpsr", cpsr | 0xA0U);
    write_register(core, "lr", 0x08000001U);
    write_register(core, "r0", r0);
    write_register(core, "r1", r1);
    write_register(core, "r2", r2);
    write_register(core, "r3", original_r3);
    write_register(core, "r12", original_r3);
    write_register(core, "pc", p05x_thumb(dispatcher));

    uint32_t normal_target = normal & ~1U;
    uint32_t suppressed_target = suppressed & ~1U;
    while (result.instructions < P05X_ROUTE_STEP_LIMIT) {
        uint32_t pc = (uint32_t)read_register(core, "pc");
        bool normal_seen = p05x_pc_matches_target(pc, normal);
        bool suppressed_seen = p05x_pc_matches_target(pc, suppressed);
        if (normal_seen && suppressed_seen) {
            /* Targets two bytes apart would make the observation ambiguous. */
            result.target = 0U;
            break;
        }
        if (normal_seen) {
            result.target = normal_target;
            break;
        }
        if (suppressed_seen) {
            result.target = suppressed_target;
            break;
        }
        ++result.instructions;
        core->step(core);
    }

    bool common_registers = (uint32_t)read_register(core, "r0") == r0
        && (uint32_t)read_register(core, "r1") == r1
        && (uint32_t)read_register(core, "r2") == r2;
    bool is_suppressed = result.target == suppressed_target;
    if (hook_width == 12U) {
        bool r3_r12 = is_suppressed
            ? (uint32_t)read_register(core, "r3") == original_r3
                && ((uint32_t)read_register(core, "r12") & ~1U)
                    == suppressed_target
            : (uint32_t)read_register(core, "r12") == original_r3
                && ((uint32_t)read_register(core, "r3") & ~1U)
                    == normal_target;
        result.registers_preserved = common_registers && r3_r12;
    } else {
        result.registers_preserved = common_registers
            && (((uint32_t)read_register(core, "r3")) & ~1U)
                == result.target;
    }
    result.fifth_stack_argument_preserved = !fifth_stack_argument
        || read32(core, call_stack.entry_sp) == fifth_argument;
    result.stack_preserved = restore_host_call_stack(core, &call_stack);
    restore_cpu_state(core, &original);
    return result;
}

static void p05x_check_dispatchers(struct mCore *core,
                                   const struct P05xArgs *args,
                                   uint64_t *route_instructions,
                                   uint32_t *route_observations)
{
    uint32_t battle_address = p05x_arg(args, "gBattleTypeFlags");
    uint32_t circus_address = p05x_arg(args, "gBattleCircusFlags");
    if (!p05x_ewram_address(battle_address)
        || !p05x_ewram_address(circus_address))
        p05x_die("suppression predicate globals are outside EWRAM");
    uint32_t saved_battle = read32(core, battle_address);
    uint32_t saved_circus = read32(core, circus_address);
    unsigned surfaces = 0U;
    unsigned width12 = 0U;
    unsigned five_argument_abis = 0U;
    unsigned five_argument_observations = 0U;
    char key[96];

    for (size_t row = 0U; row < ARRAY_LEN(P05X_DISPATCHERS); ++row) {
        const struct P05xDispatcher *contract = &P05X_DISPATCHERS[row];
        surfaces += contract->surface_occurrences;
        if (contract->hook_width == 12U)
            ++width12;
        if (contract->fifth_stack_argument)
            ++five_argument_abis;
        p05x_key(key, sizeof(key), "HOOK_", contract->suffix);
        uint32_t hook = p05x_arg(args, key);
        p05x_key(key, sizeof(key), "DISPATCH_", contract->suffix);
        uint32_t dispatcher = p05x_arg(args, key);
        p05x_key(key, sizeof(key), "NORMAL_", contract->suffix);
        uint32_t normal = p05x_arg(args, key);
        p05x_key(key, sizeof(key), "SUPPRESSED_", contract->suffix);
        uint32_t suppressed = p05x_arg(args, key);
        if (!p05x_rom_address(dispatcher)
            || !p05x_rom_address(normal)
            || !p05x_rom_address(suppressed)
            || ((normal & ~1U) == (suppressed & ~1U)))
            p05x_die("dispatcher target contract is invalid");
        p05x_require_hook(
            core, hook, contract->hook_width, dispatcher);

        for (size_t test = 0U;
             test < ARRAY_LEN(P05X_PREDICATE_CASES); ++test) {
            const struct P05xPredicateCase *predicate =
                &P05X_PREDICATE_CASES[test];
            write32_bytes(core, battle_address, predicate->battle_flags);
            write32_bytes(core, circus_address, predicate->circus_flags);
            struct P05xRouteObservation observed = p05x_observe_route(
                core, dispatcher, normal, suppressed, contract->hook_width,
                contract->fifth_stack_argument);
            uint32_t expected = predicate->suppressed
                ? (suppressed & ~1U) : (normal & ~1U);
            if (observed.target != expected
                || !observed.registers_preserved
                || !observed.stack_preserved
                || !observed.fifth_stack_argument_preserved)
                p05x_die("dispatcher predicate/ABI observation mismatch");
            *route_instructions += observed.instructions;
            ++*route_observations;
            if (contract->fifth_stack_argument)
                ++five_argument_observations;
        }
    }
    write32_bytes(core, battle_address, saved_battle);
    write32_bytes(core, circus_address, saved_circus);
    if (surfaces != P05X_SURFACE_OCCURRENCE_COUNT || width12 != 7U
        || five_argument_abis != 3U || five_argument_observations != 21U)
        p05x_die("compiled dispatcher surface/ABI contract mismatch");
}

static uint8_t p05x_is_suppressed(
    struct mCore *core, const struct P05xArgs *args,
    uint8_t bank, uint32_t battle_flags, uint32_t circus_flags,
    uint64_t *instructions, uint32_t *calls)
{
    write32_bytes(core, p05x_arg(args, "gBattleTypeFlags"), battle_flags);
    write32_bytes(core, p05x_arg(args, "gBattleCircusFlags"), circus_flags);
    return (uint8_t)p05x_call(
        core, p05x_arg(args, "IsAbilitySuppressed"),
        bank, 0U, 0U, 0U, instructions, calls);
}

static void p05x_check_stage76_hooks(struct mCore *core,
                                     const struct P05xArgs *args)
{
    uint32_t solar_site = p05x_arg(args, "HOOK_Stage76SolarBeam");
    uint32_t solar_script = p05x_arg(args, "Stage76_BattleScriptSolarBeam");
    if (!p05x_rom_address(solar_site)
        || !p05x_rom_address(solar_script)
        || read32(core, solar_site) != solar_script)
        p05x_die("Stage76 Mega Sol production pointer mismatch");
    p05x_require_hook(
        core, p05x_arg(args, "HOOK_Stage76AICalcDmg"), 12U,
        p05x_arg(args, "Stage76_EntryAICalcDmg"));
    p05x_require_hook(
        core, p05x_arg(args, "HOOK_Stage76AIScriptPartner"), 12U,
        p05x_arg(args, "Stage76_EntryAIScriptPartner"));
    p05x_require_hook(
        core, p05x_arg(args, "HOOK_Stage76RangeMoveCanHurtPartner"), 8U,
        p05x_arg(args, "Stage76_EntryRangeMoveCanHurtPartner"));
}

static void p05x_check_stage76_suppression_links(
    struct mCore *core, const struct P05xArgs *args)
{
    uint32_t start = p05x_arg(args, "Stage76_PayloadStart");
    uint32_t size = p05x_arg(args, "Stage76_PayloadSize");
    uint32_t end = start + size;
    if (!p05x_rom_address(start) || size < 4U || size > 0x10000U
        || end < start || end > 0x0A000000U)
        p05x_die("Stage76 payload range is invalid");
    uint32_t needle = p05x_thumb(
        p05x_arg(args, "IsAbilitySuppressed"));
    unsigned links = 0U;
    for (uint32_t address = start; address + 4U <= end; ++address) {
        if (p05x_read_u32_unaligned(core, address) == needle)
            ++links;
    }
    /* Mega Sol, Piercing Drill, and the shared Spicy Spray policy path. */
    if (links != 3U)
        p05x_die("Stage76 suppression-call link count mismatch");
}

static void p05x_check_is_suppressed_truth_table(
    struct mCore *core, const struct P05xArgs *args,
    uint64_t *instructions, uint32_t *calls)
{
    static const struct P05xPredicateCase cases[] = {
        {0U, 0U, false},
        {P05X_BATTLE_TYPE_CIRCUS, 0U, false},
        {0U, P05X_CIRCUS_ABILITY_SUPPRESSION, false},
        {P05X_ADJACENT_BATTLE_TYPE,
         P05X_CIRCUS_ABILITY_SUPPRESSION, false},
        {P05X_BATTLE_TYPE_CIRCUS, P05X_ADJACENT_CIRCUS_FLAG, false},
        {P05X_BATTLE_TYPE_CIRCUS,
         P05X_CIRCUS_ABILITY_SUPPRESSION, true},
        {UINT32_MAX, UINT32_MAX, true},
    };
    for (size_t index = 0U; index < ARRAY_LEN(cases); ++index) {
        uint8_t actual = p05x_is_suppressed(
            core, args, 0U, cases[index].battle_flags,
            cases[index].circus_flags, instructions, calls);
        if (!!actual != cases[index].suppressed)
            p05x_die("IsAbilitySuppressed predicate truth-table mismatch");
    }
}

static void p05x_check_stage76_helpers(
    struct mCore *core, const struct P05xArgs *args,
    uint64_t *instructions, uint32_t *calls)
{
    uint32_t probe = p05x_arg(args, "Stage76_RuntimeProbe");
    if (p05x_call(core, probe, 0U, 0U, 0U, 0U,
                  instructions, calls) != 0x53543736U
        || p05x_call(core, probe, 1U, 0U, 0U, 0U,
                     instructions, calls) != 7U
        || p05x_call(core, probe, 2U, 0U, 0U, 0U,
                     instructions, calls) != 1U)
        p05x_die("Stage76 runtime/pending-edge probe mismatch");

    uint8_t normal_suppressed = p05x_is_suppressed(
        core, args, 0U, 0U, 0U, instructions, calls);
    uint8_t circus_suppressed = p05x_is_suppressed(
        core, args, 0U, P05X_BATTLE_TYPE_CIRCUS,
        P05X_CIRCUS_ABILITY_SUPPRESSION, instructions, calls);
    if (normal_suppressed != 0U || circus_suppressed != 1U)
        p05x_die("Stage76 helper suppression fixture mismatch");

    uint32_t mega_route = p05x_arg(args, "Stage76_MegaSolRoute");
    uint32_t normal_mega_ability = normal_suppressed
        ? 0U : P05X_ABILITY_MEGA_SOL;
    uint32_t circus_mega_ability = circus_suppressed
        ? 0U : P05X_ABILITY_MEGA_SOL;
    if (p05x_call(core, mega_route, normal_mega_ability, 0U, 0U, 0U,
                  instructions, calls) != P05X_MEGA_ROUTE_POPUP
        || p05x_call(core, mega_route, circus_mega_ability, 0U, 0U, 0U,
                     instructions, calls) != P05X_MEGA_ROUTE_ORIGINAL
        || p05x_call(core, mega_route, P05X_ABILITY_MEGA_SOL, 0U, 1U, 0U,
                     instructions, calls) != P05X_MEGA_ROUTE_FIRST_TURN
        || p05x_call(core, mega_route, P05X_ABILITY_MEGA_SOL, 1U, 0U, 0U,
                     instructions, calls) != P05X_MEGA_ROUTE_ORIGINAL)
        p05x_die("Mega Sol route helper mismatch");

    uint32_t quarter = p05x_arg(
        args, "Stage76_QuarterPredictedProtectDamage");
    if (p05x_call(core, quarter, 100U, 1U, 0U, 0U,
                  instructions, calls) != 25U
        || p05x_call(core, quarter, 3U, 1U, 0U, 0U,
                     instructions, calls) != 1U
        || p05x_call(core, quarter, 100U, 0U, 0U, 0U,
                     instructions, calls) != 100U)
        p05x_die("Piercing Drill quarter-damage helper mismatch");
    uint32_t normalize = p05x_arg(
        args, "Stage76_NormalizePredictedProtectionMove");
    if (p05x_call(core, normalize, P05X_MOVE_DETECT, 0U, 0U, 0U,
                  instructions, calls) != P05X_MOVE_PROTECT
        || p05x_call(core, normalize, 599U, 0U, 0U, 0U,
                     instructions, calls) != 599U)
        p05x_die("Piercing Drill predicted protection normalization mismatch");
    uint32_t max_guard = p05x_arg(args, "Stage76_IsPlannedMaxGuard");
    if (p05x_call(core, max_guard, P05X_MOVE_MAX_GUARD, 0U, 0U, 0U,
                  instructions, calls) != 1U
        || p05x_call(core, max_guard, P05X_MOVE_PROTECT, 0U, 0U, 0U,
                     instructions, calls) != 0U)
        p05x_die("Piercing Drill/Spicy Max Guard helper mismatch");
    uint32_t select = p05x_arg(args, "Stage76_SelectAIAttackerAbility");
    if (p05x_call(core, select, P05X_ABILITY_PIERCING_DRILL,
                  normal_suppressed, 1U, P05X_ABILITY_PIERCING_DRILL,
                  instructions, calls) != P05X_ABILITY_PIERCING_DRILL
        || p05x_call(core, select, P05X_ABILITY_PIERCING_DRILL,
                     circus_suppressed, 1U, P05X_ABILITY_PIERCING_DRILL,
                     instructions, calls) != 0U)
        p05x_die("Piercing Drill suppression selection mismatch");

    uint32_t direct_effect = p05x_arg(
        args, "Stage76_DirectEffectCanDamagePartner");
    if (p05x_call(core, direct_effect, P05X_EFFECT_PRESENT, 0U, 0U, 0U,
                  instructions, calls) != 0U
        || p05x_call(core, direct_effect, P05X_EFFECT_FUTURE_SIGHT,
                     0U, 0U, 0U, instructions, calls) != 0U
        || p05x_call(core, direct_effect, P05X_EFFECT_HEAL_TARGET,
                     0U, 0U, 0U, instructions, calls) != 0U
        || p05x_call(core, direct_effect, P05X_EFFECT_OHKO,
                     0U, 0U, 0U, instructions, calls) != 1U)
        p05x_die("Spicy Spray direct-effect helper mismatch");
    uint32_t spicy_core = p05x_arg(args, "Stage76_SpicyPolicyCore");
    uint32_t suppressed_flags = P05X_SPICY_ALL_FLAGS;
    if (circus_suppressed) {
        suppressed_flags &= ~P05X_SPICY_PARTNER_ABILITY;
        suppressed_flags &= ~P05X_SPICY_BURN_BENEFIT;
    }
    if (p05x_call(core, spicy_core, P05X_SPICY_ALL_FLAGS, 0U, 0U, 0U,
                  instructions, calls) != 1U
        || p05x_call(core, spicy_core, suppressed_flags, 0U, 0U, 0U,
                     instructions, calls) != 0U)
        p05x_die("Spicy Spray suppression policy mismatch");
    uint32_t spicy_path = p05x_arg(args, "Stage76_SpicyPathQualifies");
    if (p05x_call(core, spicy_path, 0U, 0U, 1U, 0U,
                  instructions, calls) != 1U
        || p05x_call(core, spicy_path, 0U, 1U, 1U, 0U,
                     instructions, calls) != 0U
        || p05x_call(core, spicy_path, 1U, 1U, 1U, 0U,
                     instructions, calls) != 1U
        || p05x_call(core, spicy_path, 1U, 0U, 1U, 0U,
                     instructions, calls) != 0U)
        p05x_die("Spicy Spray direct/spread path helper mismatch");
}

static void p05x_check_megasol_production_dispatch(
    struct mCore *core, const struct P05xArgs *args,
    uint64_t *instructions, uint32_t *calls)
{
    uint8_t saved_count = read8(core, P05X_G_BATTLERS_COUNT);
    uint8_t saved_attacker = read8(core, P05X_G_BANK_ATTACKER);
    uint16_t saved_ability = read16(
        core, P05X_G_BATTLE_MONS + P05X_BATTLE_MON_ABILITY_OFFSET);
    uint32_t saved_status2 = read32(
        core, P05X_G_BATTLE_MONS + P05X_BATTLE_MON_STATUS2_OFFSET);
    uint16_t saved_weather = read16(core, P05X_G_BATTLE_WEATHER);
    uint32_t saved_hit_marker = read32(core, P05X_G_HIT_MARKER);
    uint32_t saved_script = read32(core, P05X_G_BATTLE_SCRIPT);
    uint8_t saved_script_bank = read8(
        core, P05X_G_BATTLE_SCRIPTING + P05X_BATTLE_SCRIPTING_BANK_OFFSET);

    write8(core, P05X_G_BATTLERS_COUNT, 1U);
    write8(core, P05X_G_BANK_ATTACKER, 0U);
    write16(core, P05X_G_BATTLE_MONS + P05X_BATTLE_MON_ABILITY_OFFSET,
            P05X_ABILITY_MEGA_SOL);
    write32_bytes(core,
                  P05X_G_BATTLE_MONS + P05X_BATTLE_MON_STATUS2_OFFSET, 0U);
    write16(core, P05X_G_BATTLE_WEATHER, 0U);
    write32_bytes(core, P05X_G_HIT_MARKER, 0U);

    uint32_t dispatch = p05x_arg(
        args, "Stage76_DispatchMegaSolSolarBeam");
    uint32_t popup = p05x_arg(args, "Stage76_BattleScriptMegaSolPopup");
    write32_bytes(core, p05x_arg(args, "gBattleTypeFlags"), 0U);
    write32_bytes(core, p05x_arg(args, "gBattleCircusFlags"), 0U);
    write32_bytes(core, P05X_G_BATTLE_SCRIPT, 0U);
    write8(core,
           P05X_G_BATTLE_SCRIPTING + P05X_BATTLE_SCRIPTING_BANK_OFFSET,
           0xA5U);
    (void)p05x_call(core, dispatch, 0U, 0U, 0U, 0U,
                    instructions, calls);
    if (read32(core, P05X_G_BATTLE_SCRIPT) != popup - 5U
        || read8(core, P05X_G_BATTLE_SCRIPTING
                 + P05X_BATTLE_SCRIPTING_BANK_OFFSET) != 0U)
        p05x_die("Mega Sol normal production popup route mismatch");

    write32_bytes(core, p05x_arg(args, "gBattleTypeFlags"),
                  P05X_BATTLE_TYPE_CIRCUS);
    write32_bytes(core, p05x_arg(args, "gBattleCircusFlags"),
                  P05X_CIRCUS_ABILITY_SUPPRESSION);
    write32_bytes(core, P05X_G_BATTLE_SCRIPT, 0U);
    write8(core,
           P05X_G_BATTLE_SCRIPTING + P05X_BATTLE_SCRIPTING_BANK_OFFSET,
           0xA5U);
    (void)p05x_call(core, dispatch, 0U, 0U, 0U, 0U,
                    instructions, calls);
    if (read32(core, P05X_G_BATTLE_SCRIPT)
            != P05X_ORIGINAL_SOLAR_BEAM_SCRIPT - 5U
        || read8(core, P05X_G_BATTLE_SCRIPTING
                 + P05X_BATTLE_SCRIPTING_BANK_OFFSET) != 0xA5U)
        p05x_die("Mega Sol suppressed production route mismatch");

    write8(core, P05X_G_BATTLERS_COUNT, saved_count);
    write8(core, P05X_G_BANK_ATTACKER, saved_attacker);
    write16(core, P05X_G_BATTLE_MONS + P05X_BATTLE_MON_ABILITY_OFFSET,
            saved_ability);
    write32_bytes(
        core, P05X_G_BATTLE_MONS + P05X_BATTLE_MON_STATUS2_OFFSET,
        saved_status2);
    write16(core, P05X_G_BATTLE_WEATHER, saved_weather);
    write32_bytes(core, P05X_G_HIT_MARKER, saved_hit_marker);
    write32_bytes(core, P05X_G_BATTLE_SCRIPT, saved_script);
    write8(core,
           P05X_G_BATTLE_SCRIPTING + P05X_BATTLE_SCRIPTING_BANK_OFFSET,
           saved_script_bank);
}

struct P05xEelevateObservation {
    uint16_t result;
    uint32_t instructions;
    uint32_t stub_calls;
    bool continuation_seen;
    bool registers_preserved;
    bool stack_preserved;
    bool stub_arguments_valid;
    bool stub_stack_aligned;
    bool foe1_prediction_seen;
    bool foe2_prediction_seen;
    bool suppression_stub_seen;
    bool mon_item_stub_seen;
    bool helper_entry_seen;
    bool helper_arguments_valid;
};

static void p05x_read_bytes(struct mCore *core, uint32_t address,
                            uint8_t *output, size_t size)
{
    for (size_t index = 0U; index < size; ++index)
        output[index] = read8(core, address + (uint32_t)index);
}

static void p05x_write_bytes(struct mCore *core, uint32_t address,
                             const uint8_t *input, size_t size)
{
    for (size_t index = 0U; index < size; ++index)
        write8(core, address + (uint32_t)index, input[index]);
}

static void p05x_stub_return(struct mCore *core, uint32_t result)
{
    uint32_t link = (uint32_t)read_register(core, "lr");
    write_register(core, "r0", result);
    write_register(core, "pc", link);
}

static bool p05x_stub_at(struct mCore *core, const struct P05xArgs *args,
                         const char *name)
{
    return p05x_pc_matches_target(
        (uint32_t)read_register(core, "pc"), p05x_arg(args, name));
}

static void p05x_write_query(struct mCore *core,
                             const struct P05xEelevateQuery *query)
{
    write16(core, P05X_EELEVATE_QUERY_SCRATCH, query->originalAbility);
    write16(core, P05X_EELEVATE_QUERY_SCRATCH + 2U, query->move);
    write8(core, P05X_EELEVATE_QUERY_SCRATCH + 4U, query->moveType);
    write8(core, P05X_EELEVATE_QUERY_SCRATCH + 5U, query->moveSplit);
    write8(core, P05X_EELEVATE_QUERY_SCRATCH + 6U, query->grounded);
    write8(core, P05X_EELEVATE_QUERY_SCRATCH + 7U,
           query->targetAbilityIgnored);
    write8(core, P05X_EELEVATE_QUERY_SCRATCH + 8U, query->abilityShield);
    write8(core, P05X_EELEVATE_QUERY_SCRATCH + 9U,
           query->circusSuppressed);
    write8(core, P05X_EELEVATE_QUERY_SCRATCH + 10U,
           query->abilitySuppressed);
    write8(core, P05X_EELEVATE_QUERY_SCRATCH + 11U,
           query->neutralizingGasPresent);
}

static void p05x_check_eelevate_pure_matrix(
    struct mCore *core, const struct P05xArgs *args,
    uint64_t *instructions, uint32_t *calls)
{
    uint8_t saved[sizeof(struct P05xEelevateQuery)];
    p05x_read_bytes(core, P05X_EELEVATE_QUERY_SCRATCH,
                    saved, sizeof(saved));
    for (size_t index = 0U; index < ARRAY_LEN(P05X_EELEVATE_CASES); ++index) {
        const struct P05xEelevateCase *row = &P05X_EELEVATE_CASES[index];
        p05x_write_query(core, &row->query);
        uint32_t actual = p05x_call(
            core, p05x_arg(args, "Stage78_MapEelevateAbsorber"),
            P05X_EELEVATE_QUERY_SCRATCH, 0U, 0U, 0U,
            instructions, calls);
        if (actual != row->expected)
            p05x_die(row->name);
    }
    p05x_write_bytes(core, P05X_EELEVATE_QUERY_SCRATCH,
                     saved, sizeof(saved));
    if (ARRAY_LEN(P05X_EELEVATE_CASES) != 32U)
        p05x_die("Stage78 Eelevate matrix count mismatch");
}

static struct P05xEelevateObservation p05x_observe_eelevate_hook(
    struct mCore *core, const struct P05xArgs *args,
    const struct P05xEelevateRuntimeCase *scenario)
{
    struct P05xEelevateObservation observed = {
        .stub_arguments_valid = true,
        .stub_stack_aligned = true,
    };
    struct CpuState original = capture_cpu_state(core);
    struct HostCallStack call_stack;
    begin_host_call_stack(core, &call_stack, NULL, 0U);
    uint32_t cpsr = (uint32_t)original.registers[16];
    uint32_t hook = p05x_arg(
        args, scenario->party
            ? "HOOK_FindMonAbsorberPartyAbilityBlock"
            : "HOOK_FindMonAbsorberActiveAbilityBlock");
    uint32_t continuation = p05x_arg(
        args, scenario->party
            ? "CONT_FindMonAbsorberPartyAbilityBlock"
            : "CONT_FindMonAbsorberActiveAbilityBlock");
    write_register(core, "cpsr", cpsr | 0xA0U);
    write_register(core, "lr", 0x08000001U);
    write_register(core, "r4", P05X_EELEVATE_BATTLE_MON_SCRATCH);
    write_register(core, "r5", P05X_EELEVATE_ACTIVE_BANK);
    write_register(core, "r6", scenario->party
        ? P05X_EELEVATE_MON_SCRATCH : 1U);
    write_register(core, "r3", P05X_EELEVATE_SPECIES_SENTINEL);
    write_register(core, "r8", 0x88888888U);
    write_register(core, "r11", 0xBBBBBBBBU);
    write_register(core, "pc", hook | 1U);

    while (observed.instructions < 4096U) {
        uint32_t pc = (uint32_t)read_register(core, "pc");
        if (p05x_pc_matches_target(pc, continuation)) {
            observed.continuation_seen = true;
            observed.result = (uint16_t)read_register(core, "r0");
            if (scenario->party) {
                observed.registers_preserved =
                    observed.result == scenario->expected
                    && (uint16_t)read_register(core, "r7")
                        == scenario->expected
                    && (uint32_t)read_register(core, "r8")
                        == P05X_EELEVATE_SPECIES_SENTINEL
                    && (uint16_t)read_register(core, "r3")
                        == P05X_EELEVATE_HP_SENTINEL
                    && (uint32_t)read_register(core, "r4")
                        == P05X_EELEVATE_BATTLE_MON_SCRATCH
                    && (uint32_t)read_register(core, "r6")
                        == P05X_EELEVATE_MON_SCRATCH;
            } else {
                observed.registers_preserved =
                    observed.result == scenario->expected
                    && (uint16_t)read_register(core, "r3")
                        == P05X_ABILITY_EARTH_EATER
                    && (uint16_t)read_register(core, "r11")
                        == P05X_ABILITY_EARTH_EATER
                    && (uint32_t)read_register(core, "r5")
                        == P05X_EELEVATE_ACTIVE_BANK
                    && (uint32_t)read_register(core, "r6") == 1U;
            }
            observed.registers_preserved = observed.registers_preserved
                && (uint32_t)read_register(core, "lr") == 0x08000001U;
            break;
        }

        const char *helper = scenario->party
            ? "Stage78_PartyAbsorberAbility"
            : "Stage78_ActiveAbsorberAbility";
        if (p05x_pc_matches_target(pc, p05x_arg(args, helper))) {
            uint32_t helper_r0 = (uint32_t)read_register(core, "r0");
            uint32_t helper_r1 = (uint32_t)read_register(core, "r1");
            uint32_t helper_r2 = (uint32_t)read_register(core, "r2");
            observed.helper_entry_seen = true;
            observed.helper_arguments_valid =
                helper_r0 == scenario->original_ability
                && helper_r1 == (scenario->party
                    ? P05X_EELEVATE_MON_SCRATCH
                    : P05X_EELEVATE_ACTIVE_BANK)
                && (scenario->party || helper_r2 == 1U)
                && (((uint32_t)read_register(core, "sp") & 7U) == 0U);
            core->step(core);
            ++observed.instructions;
            continue;
        }

        bool handled = true;
        uint32_t result = 0U;
        uint32_t r0 = (uint32_t)read_register(core, "r0");
        uint32_t r1 = (uint32_t)read_register(core, "r1");
        uint32_t r2 = (uint32_t)read_register(core, "r2");
        uint32_t r3 = (uint32_t)read_register(core, "r3");
        if (p05x_stub_at(core, args, "LoadBattlersAndFoes")) {
            observed.stub_arguments_valid = observed.stub_arguments_valid
                && p05x_ewram_address(r0) && p05x_ewram_address(r1)
                && p05x_ewram_address(r2) && p05x_ewram_address(r3);
            write8(core, r0, P05X_EELEVATE_ACTIVE_BANK);
            write8(core, r1, 0U);
            write8(core, r2, 1U);
            write8(core, r3, 3U);
        } else if (p05x_stub_at(core, args, "GetPredictedAIAbility")) {
            observed.stub_arguments_valid = observed.stub_arguments_valid
                && r0 == P05X_EELEVATE_ACTIVE_BANK && r1 == 1U;
            result = scenario->original_ability;
        } else if (p05x_stub_at(core, args, "GetMonAbility")) {
            observed.stub_arguments_valid = observed.stub_arguments_valid
                && r0 == P05X_EELEVATE_MON_SCRATCH;
            result = scenario->original_ability;
        } else if (p05x_stub_at(core, args, "IsValidMovePrediction")) {
            observed.stub_arguments_valid = observed.stub_arguments_valid
                && (r0 == 1U || r0 == 3U)
                && r1 == P05X_EELEVATE_ACTIVE_BANK;
            if (r0 == 1U) {
                observed.foe1_prediction_seen = true;
                result = (scenario->fallback == 0U
                          || scenario->fallback == 4U) ? scenario->move
                    : scenario->fallback == 2U ? UINT16_MAX
                    : scenario->fallback == 3U ? 1063U : 0U;
            } else {
                observed.foe2_prediction_seen = true;
                result = scenario->fallback == 4U ? 45U
                    : scenario->fallback ? scenario->move : 0U;
            }
        } else if (p05x_stub_at(core, args, "GetMoveTypeSpecial")) {
            uint32_t attacker = scenario->fallback != 0U
                    && scenario->fallback != 4U ? 3U : 1U;
            observed.stub_arguments_valid = observed.stub_arguments_valid
                && r0 == attacker && r1 == scenario->move;
            result = scenario->move_type;
        } else if (p05x_stub_at(core, args, "IsAbilitySuppressed")) {
            observed.suppression_stub_seen = true;
            observed.stub_arguments_valid = observed.stub_arguments_valid
                && r0 == P05X_EELEVATE_ACTIVE_BANK;
            result = scenario->ability_suppressed;
        } else if (p05x_stub_at(core, args, "CheckGrounding")) {
            observed.stub_arguments_valid = observed.stub_arguments_valid
                && r0 == P05X_EELEVATE_ACTIVE_BANK;
            result = scenario->grounded;
        } else if (p05x_stub_at(core, args, "CheckMonGrounding")) {
            observed.stub_arguments_valid = observed.stub_arguments_valid
                && r0 == P05X_EELEVATE_MON_SCRATCH;
            result = scenario->grounded;
        } else if (p05x_stub_at(core, args, "GetBankItemEffect")) {
            observed.stub_arguments_valid = observed.stub_arguments_valid
                && r0 == P05X_EELEVATE_ACTIVE_BANK;
            result = scenario->shield ? 147U : 0U;
        } else if (p05x_stub_at(core, args, "GetMonItemEffect")) {
            observed.mon_item_stub_seen = true;
            observed.stub_arguments_valid = observed.stub_arguments_valid
                && r0 == P05X_EELEVATE_MON_SCRATCH;
            result = scenario->shield ? 147U : 0U;
        } else if (p05x_stub_at(core, args, "GetAIAbility")) {
            uint32_t attacker = scenario->fallback != 0U
                    && scenario->fallback != 4U ? 3U : 1U;
            observed.stub_arguments_valid = observed.stub_arguments_valid
                && r0 == attacker && r1 == P05X_EELEVATE_ACTIVE_BANK
                && r2 == scenario->move;
            result = scenario->target_ignored
                ? P05X_ABILITY_MOLD_BREAKER : 0U;
        } else if (p05x_stub_at(core, args, "IsTargetAbilityIgnored")) {
            observed.stub_arguments_valid = observed.stub_arguments_valid
                && r0 == P05X_ABILITY_EELEVATE
                && r1 == (scenario->target_ignored
                    ? P05X_ABILITY_MOLD_BREAKER : 0U)
                && r2 == scenario->move;
            result = scenario->target_ignored;
        } else {
            handled = false;
        }
        if (handled) {
            observed.stub_stack_aligned = observed.stub_stack_aligned
                && (((uint32_t)read_register(core, "sp") & 7U) == 0U);
            ++observed.stub_calls;
            p05x_stub_return(core, result);
        } else {
            core->step(core);
        }
        ++observed.instructions;
    }
    observed.stack_preserved = restore_host_call_stack(core, &call_stack);
    restore_cpu_state(core, &original);
    return observed;
}

static uint32_t p05x_check_eelevate_runtime_routes(
    struct mCore *core, const struct P05xArgs *args,
    uint64_t *instructions, bool *active_pass, bool *party_pass)
{
    uint32_t battle_mons = p05x_arg(args, "gBattleMons");
    uint32_t battlers_count = p05x_arg(args, "gBattlersCount");
    uint32_t absent = p05x_arg(args, "gAbsentBattlerFlags");
    uint32_t battle_flags = p05x_arg(args, "gBattleTypeFlags");
    uint32_t circus_flags = p05x_arg(args, "gBattleCircusFlags");
    uint32_t battle_moves = p05x_arg(args, "gBattleMoves");
    uint8_t saved_mons[5U * 0x58U];
    uint8_t saved_mon_scratch[128U];
    uint8_t saved_count = read8(core, battlers_count);
    uint8_t saved_absent = read8(core, absent);
    uint32_t saved_battle = read32(core, battle_flags);
    uint32_t saved_circus = read32(core, circus_flags);
    p05x_read_bytes(core, battle_mons, saved_mons, sizeof(saved_mons));
    p05x_read_bytes(core, P05X_EELEVATE_MON_SCRATCH,
                    saved_mon_scratch, sizeof(saved_mon_scratch));
    if (battle_mons != P05X_G_BATTLE_MONS
        || battlers_count != P05X_G_BATTLERS_COUNT
        || battle_moves != 0x090421F4U
        || read8(core, battle_moves + 89U * 12U + 10U) != 0U
        || read8(core, battle_moves + 45U * 12U + 10U) != P05X_SPLIT_STATUS
        || read8(core, battle_moves + P05X_MOVE_THOUSAND_ARROWS * 12U + 10U)
            != 0U)
        p05x_die("Stage78 battle table/global exact ABI mismatch");

    uint32_t stub_calls = 0U;
    *active_pass = true;
    *party_pass = true;
    for (size_t index = 0U;
         index < ARRAY_LEN(P05X_EELEVATE_RUNTIME_CASES); ++index) {
        const struct P05xEelevateRuntimeCase *scenario =
            &P05X_EELEVATE_RUNTIME_CASES[index];
        for (size_t byte = 0U; byte < sizeof(saved_mons); ++byte)
            write8(core, battle_mons + (uint32_t)byte, 0U);
        write8(core, battlers_count,
               scenario->battler_count == 0U ? 4U
                                             : scenario->battler_count);
        write8(core, absent, scenario->absent_mask);
        for (uint32_t bank = 0U; bank < 5U; ++bank)
            write16(core, battle_mons + bank * 0x58U + 0x28U, 1U);
        if (scenario->gas_bank != P05X_NO_GAS) {
            write16(core, battle_mons
                    + (uint32_t)scenario->gas_bank * 0x58U + 0x38U,
                    P05X_ABILITY_NEUTRALIZING_GAS);
            if (scenario->gas_dead)
                write16(core, battle_mons
                        + (uint32_t)scenario->gas_bank * 0x58U + 0x28U, 0U);
        }
        write32_bytes(core, battle_flags,
                      scenario->circus ? P05X_BATTLE_TYPE_CIRCUS : 0U);
        write32_bytes(core, circus_flags,
                      scenario->circus
                          ? P05X_CIRCUS_ABILITY_SUPPRESSION : 0U);
        write16(core, P05X_EELEVATE_BATTLE_MON_SCRATCH + 54U,
                P05X_EELEVATE_HP_SENTINEL);
        struct P05xEelevateObservation row = p05x_observe_eelevate_hook(
            core, args, scenario);
        bool prediction_pass = scenario->original_ability
            == P05X_ABILITY_EELEVATE
                ? row.foe1_prediction_seen && row.foe2_prediction_seen
                : !row.foe1_prediction_seen && !row.foe2_prediction_seen;
        bool pass = row.continuation_seen
            && row.result == scenario->expected
            && row.registers_preserved && row.stack_preserved
            && row.stub_arguments_valid && row.stub_stack_aligned
            && row.helper_entry_seen && row.helper_arguments_valid
            && prediction_pass
            && (!scenario->party || !row.suppression_stub_seen)
            && (!scenario->party
                || scenario->original_ability != P05X_ABILITY_EELEVATE
                || row.mon_item_stub_seen);
        if (!pass)
            p05x_die(scenario->name);
        if (scenario->party)
            *party_pass = *party_pass && pass;
        else
            *active_pass = *active_pass && pass;
        *instructions += row.instructions;
        stub_calls += row.stub_calls;
    }
    p05x_write_bytes(core, battle_mons, saved_mons, sizeof(saved_mons));
    p05x_write_bytes(core, P05X_EELEVATE_MON_SCRATCH,
                     saved_mon_scratch, sizeof(saved_mon_scratch));
    write8(core, battlers_count, saved_count);
    write8(core, absent, saved_absent);
    write32_bytes(core, battle_flags, saved_battle);
    write32_bytes(core, circus_flags, saved_circus);
    return stub_calls;
}

#ifndef MODERNIZATION_STAGE79_P05_EMBEDDED
int main(int argc, char **argv)
{
    if (argc < 4) {
        fprintf(stderr,
                "usage: %s ROM EXPECTED_ROM_SHA256 NAME=ADDRESS ...\n",
                argv[0]);
        return 2;
    }
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64U || strcmp(rom_sha256, argv[2]) != 0)
        p05x_die("ROM SHA-256 mismatch");
    struct P05xArgs args = p05x_parse_args(argc, argv);
    p05x_validate_arg_set(&args);

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {
        .sample = NULL,
        .unixTime = fixed_unix_time,
        .serialize = NULL,
        .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(argv[1]);
    if (core == NULL || !core->init(core))
        p05x_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1]))
        p05x_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);

    uint32_t battle_address = p05x_arg(&args, "gBattleTypeFlags");
    uint32_t circus_address = p05x_arg(&args, "gBattleCircusFlags");
    uint32_t statuses3_address = p05x_arg(&args, "gStatuses3");
    if (!p05x_ewram_address(battle_address)
        || !p05x_ewram_address(circus_address)
        || !p05x_ewram_address(statuses3_address)
        || statuses3_address + 8U > 0x02040000U)
        p05x_die("P05 suppression RAM contract is invalid");
    uint32_t saved_battle = read32(core, battle_address);
    uint32_t saved_circus = read32(core, circus_address);
    uint32_t saved_statuses3[2] = {
        read32(core, statuses3_address),
        read32(core, statuses3_address + 4U),
    };
    write32_bytes(core, statuses3_address, 0U);
    write32_bytes(core, statuses3_address + 4U, 0U);

    uint64_t direct_instructions = 0U;
    uint32_t direct_calls = 0U;
    uint64_t route_instructions = 0U;
    uint32_t route_observations = 0U;
    if (p05x_call(core, p05x_arg(&args, "Stage77_RuntimeProbe"),
                  0U, 0U, 0U, 0U,
                  &direct_instructions, &direct_calls) != 77U)
        p05x_die("Stage77 runtime probe mismatch");
    if (p05x_call(core, p05x_arg(&args, "Stage78_RuntimeProbe"),
                  0U, 0U, 0U, 0U,
                  &direct_instructions, &direct_calls) != 78U)
        p05x_die("Stage78 runtime probe mismatch");
    p05x_check_stage76_hooks(core, &args);
    p05x_require_stage78_hooks(core, &args);
    p05x_check_stage76_suppression_links(core, &args);
    p05x_check_dispatchers(
        core, &args, &route_instructions, &route_observations);
    p05x_check_is_suppressed_truth_table(
        core, &args, &direct_instructions, &direct_calls);
    p05x_check_stage76_helpers(
        core, &args, &direct_instructions, &direct_calls);
    p05x_check_megasol_production_dispatch(
        core, &args, &direct_instructions, &direct_calls);
    p05x_check_eelevate_pure_matrix(
        core, &args, &direct_instructions, &direct_calls);
    bool eelevate_active_pass = false;
    bool eelevate_party_pass = false;
    uint32_t eelevate_stub_calls = p05x_check_eelevate_runtime_routes(
        core, &args, &direct_instructions,
        &eelevate_active_pass, &eelevate_party_pass);

    write32_bytes(core, battle_address, saved_battle);
    write32_bytes(core, circus_address, saved_circus);
    write32_bytes(core, statuses3_address, saved_statuses3[0]);
    write32_bytes(core, statuses3_address + 4U, saved_statuses3[1]);
    if (route_observations
            != P05X_DISPATCHER_COUNT * ARRAY_LEN(P05X_PREDICATE_CASES))
        p05x_die("dispatcher observation count mismatch");
    if (log_problem_count != 0U)
        p05x_die("mGBA warning/error was emitted");

    printf(
        "{\"schema_version\":1,\"status\":\"PASS\","
        "\"classification\":\"STAGE78_P05_RUNTIME_DIRECT_CALL\","
        "\"rom_sha256\":\"%s\",\"read_only\":true,"
        "\"warnings_errors\":0,\"dispatcher_count\":29,"
        "\"ability_surface_occurrence_count\":33,"
        "\"normal_delegations\":29,"
        "\"circus_original_delegations\":29,"
        "\"fifth_stack_argument_observations\":21,"
        "\"fifth_stack_arguments_preserved\":true,"
        "\"predicate_truth_table_pass\":true,"
        "\"stage76_helpers_preserved\":true,"
        "\"suppression_paths_pass\":true,"
        "\"stage76_megasol_production_dispatch_pass\":true,"
        "\"stage76_suppression_link_count\":3,"
        "\"dispatcher_observations\":%" PRIu32 ","
        "\"direct_calls\":%" PRIu32 ","
        "\"dispatcher_instructions\":%" PRIu64 ","
        "\"direct_call_instructions\":%" PRIu64 ","
        "\"eelevate_switch_ai_done\":true,"
        "\"eelevate_matrix_case_count\":32,"
        "\"eelevate_matrix_observations\":32,"
        "\"eelevate_matrix_sha256\":"
        "\"3b0ce8e8a5fa75857971b59091f2a95d73ec5597d90be4756eb9e3717e8383ed\","
        "\"eelevate_pure_helper_pass\":true,"
        "\"eelevate_active_helper_pass\":%s,"
        "\"eelevate_party_helper_pass\":%s,"
        "\"eelevate_active_hook_route_pass\":%s,"
        "\"eelevate_party_hook_route_pass\":%s,"
        "\"eelevate_active_hook_observations\":13,"
        "\"eelevate_party_hook_observations\":13,"
        "\"eelevate_stub_calls_observed\":%" PRIu32 ","
        "\"eelevate_register_continuation_abi_pass\":true,"
        "\"full_p05_acceptance\":false,"
        "\"scheduler_e2e\":false,\"artifacts_written\":[]}\n",
        rom_sha256, route_observations, direct_calls,
        route_instructions, direct_instructions,
        eelevate_active_pass ? "true" : "false",
        eelevate_party_pass ? "true" : "false",
        eelevate_active_pass ? "true" : "false",
        eelevate_party_pass ? "true" : "false",
        eelevate_stub_calls);
    fflush(stdout);

    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    free(core);
    p05x_free_args(&args);
    return 0;
}
#endif
