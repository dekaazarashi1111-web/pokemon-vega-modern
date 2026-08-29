import hashlib
import json
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = ROOT / "overlays" / "trainer_changekit_final_runtime"
RUNTIME_C = RUNTIME_DIR / "trainer_changekit_final_runtime.c"
RUNTIME_H = RUNTIME_DIR / "trainer_changekit_final_runtime.h"
HOOK_CONTRACT = RUNTIME_DIR / "hook_contract_stage34.json"


GENERATED_HEADER = r"""
#ifndef TRAINER_CHANGEKIT_FINAL_GENERATED_H
#define TRAINER_CHANGEKIT_FINAL_GENERATED_H
#include <stdint.h>

#define TRAINER_CHANGEKIT_FINAL_GENERATED_ENCOUNTER_COUNT 1302u
#define TRAINER_CHANGEKIT_FINAL_GENERATED_SIDECAR_COUNT 2u
#define TRAINER_CHANGEKIT_FINAL_GENERATED_EXACT_BINDING_COUNT 6u
#define TRAINER_CHANGEKIT_FINAL_GENERATED_REMATCH_COUNT 1u
#define TRAINER_CHANGEKIT_FINAL_GENERATED_ARCHIVE_COUNT 2u
#define TRAINER_CHANGEKIT_FINAL_GENERATED_GIMMICK_COUNT 6u
#define TRAINER_CHANGEKIT_FINAL_GENERATED_FLAG_MAP_COUNT 2u
#define TRAINER_CHANGEKIT_FINAL_GENERATED_TRAINER_TABLE_COUNT 4284u
#define TRAINER_CHANGEKIT_FINAL_TRAINER_TABLE_ADDRESS UINT32_C(0x09000000)

struct __attribute__((packed)) TrainerChangeKitMemberSidecarV1 {
    uint16_t trainer_id;
    uint16_t species_id;
    uint16_t ability_id;
    uint8_t side;
    uint8_t slot;
    uint8_t nature_id;
    uint8_t ability_mode;
    uint8_t iv;
    uint8_t hp_ev;
    uint8_t atk_ev;
    uint8_t def_ev;
    uint8_t speed_ev;
    uint8_t sp_atk_ev;
    uint8_t sp_def_ev;
    uint8_t level;
};
struct __attribute__((packed)) TrainerChangeKitExactBindingV1 {
    uint32_t data_address;
    uint16_t source_trainer_id;
    uint16_t target_trainer_id;
    uint8_t kind;
    uint8_t flags;
    uint16_t dispatch_id;
};
struct __attribute__((packed)) TrainerChangeKitRematchV2 {
    uint32_t data_address;
    uint16_t stock_trainer_id;
    uint16_t target_trainer_id;
};
struct __attribute__((packed)) TrainerChangeKitArchiveBindingV1 {
    uint32_t data_address;
    uint16_t source_trainer_id;
    uint16_t target_trainer_id;
    uint16_t archive_id;
    uint16_t physical_flag;
    uint8_t kind;
    uint8_t battle_format;
    uint8_t reserved[2];
};
struct __attribute__((packed)) TrainerChangeKitGimmickV1 {
    uint16_t trainer_id;
    uint16_t dispatch_id;
    uint8_t mechanic_mode;
    uint8_t ai_profile;
    uint8_t user_slot;
    uint8_t flags;
    uint8_t tera_type;
    uint8_t reserved[3];
};
struct __attribute__((packed)) TrainerChangeKitFlagMapV1 {
    uint16_t external_flag;
    uint16_t physical_flag;
};

static const struct TrainerChangeKitMemberSidecarV1
gTrainerChangeKitMemberSidecars[2] = {
    {200u, 25u, 90u, 1u, 0u, 7u, 1u, 31u, 1u, 2u, 3u, 4u, 5u, 6u, 50u},
    {300u, 26u, 301u, 1u, 0u, 8u, 2u, 30u, 6u, 5u, 4u, 3u, 2u, 1u, 51u},
};
static const struct TrainerChangeKitExactBindingV1
gTrainerChangeKitExactBindings[6] = {
    {UINT32_C(0x1000), 10u, 100u, 0u, 0u, 0u},
    {UINT32_C(0x2000), 20u, 200u, 7u, 0u, 0u},
    {UINT32_C(0x2500), 25u, 250u, 6u, 0u, 0u},
    {UINT32_C(0x3000), 30u, 300u, 8u, 0u, 0u},
    {UINT32_C(0x4000), 40u, 400u, 0u, 0u, 0u},
    {UINT32_C(0x4000), 40u, 401u, 0u, 0u, 0u},
};
static const struct TrainerChangeKitRematchV2
gTrainerChangeKitRematchMap[1] = {
    {UINT32_C(0x2000), 20u, 201u},
};
static const struct TrainerChangeKitArchiveBindingV1
gTrainerChangeKitArchiveBindings[2] = {
    {UINT32_C(0x1000), 10u, 101u, 1u, 0x0520u, 0u, 0u, {0u, 0u}},
    {UINT32_C(0x1000), 10u, 102u, 2u, 0x0521u, 0u, 0u, {0u, 0u}},
};
static const struct TrainerChangeKitGimmickV1
gTrainerChangeKitGimmicks[6] = {
    {100u, 0u, 0u, 1u, 0u, 0u, 0u, {0u, 0u, 0u}},
    {101u, 1u, 1u, 5u, 2u, 1u, 0u, {0u, 0u, 0u}},
    {102u, 2u, 2u, 5u, 3u, 1u, 0u, {0u, 0u, 0u}},
    {200u, 0u, 3u, 3u, 1u, 3u, 0u, {0u, 0u, 0u}},
    {250u, 0u, 3u, 3u, 1u, 3u, 0u, {0u, 0u, 0u}},
    {300u, 0u, 4u, 5u, 0u, 3u, 17u, {0u, 0u, 0u}},
};
static const struct TrainerChangeKitFlagMapV1
gTrainerChangeKitFlagMap[2] = {
    {0x0565u, 0x0520u},
    {0x1500u, 0x0600u},
};
#endif
"""


HOST_FIXTURE = r"""
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "trainer_changekit_final_runtime.h"

#define CHECK(expression) do { \
    if (!(expression)) { \
        fprintf(stderr, "CHECK failed at line %d: %s\n", __LINE__, #expression); \
        return 1; \
    } \
} while (0)

uint8_t gTrainerChangeKitHostEnemyParty[600];
volatile uint16_t gTrainerChangeKitHostOpponentA;
volatile uint32_t gTrainerChangeKitHostBattleTypeFlags = 8u;
volatile uint8_t gTrainerChangeKitHostBattlersCount = 4u;
volatile uint8_t gTrainerChangeKitHostAbsentBattlerFlags;
volatile uint16_t gTrainerChangeKitHostBattlerPartyIndexes[4] = {
    0u, 2u, 0u, 1u
};
volatile uint8_t gTrainerChangeKitHostActiveBattler;
uint8_t gTrainerChangeKitHostBattleMons[352];

static const uint8_t *sCommandA;
static const uint8_t *sCommandB;
static const uint8_t *sCommandC;
static const uint8_t *sCommandD;
static const uint8_t *sCommandE;
static uint16_t sTrainerFlag = 0x0565u;
static uint16_t sLastFlag;
static uint8_t sFlags[0x700];
static unsigned sPolicyCalls;
static unsigned sPendingClears;
static unsigned sPolicyBegins;
static unsigned sPolicyEnds;
static unsigned sCanCalls;
static unsigned sMarkCalls;
static unsigned sSaveLoads;
static uint8_t sLastAi;
static uint8_t sLastMechanic;
static uint8_t sLastSaveType;
static uint8_t sPolicyShouldFail;
static uint8_t sStockRematchZero;
static uint8_t sResolveRematchDuringConfigure;
static uint16_t sConfiguredRematch;

static uint16_t read16(const uint8_t *source)
{
    return (uint16_t)(source[0] | ((uint16_t)source[1] << 8));
}

uint16_t TrainerChangeKitHost_GetTrainerFlag(void)
{
    return sTrainerFlag;
}

uint8_t TrainerChangeKitHost_FlagSet(uint16_t flag)
{
    sLastFlag = flag;
    if (flag < sizeof(sFlags))
        sFlags[flag] = 1u;
    return 1u;
}

uint8_t TrainerChangeKitHost_FlagClear(uint16_t flag)
{
    sLastFlag = flag;
    if (flag < sizeof(sFlags))
        sFlags[flag] = 0u;
    return 1u;
}

uint8_t TrainerChangeKitHost_FlagGet(uint16_t flag)
{
    sLastFlag = flag;
    return flag < sizeof(sFlags) ? sFlags[flag] : 0u;
}

uint16_t TrainerChangeKitHost_GetRematch(uint16_t trainer_id)
{
    return sStockRematchZero ? 0u : trainer_id;
}

void TrainerChangeKitHost_BuildTrainerParty(void)
{
    uint16_t species = gTrainerChangeKitHostOpponentA == 200u ? 25u : 26u;
    memset(gTrainerChangeKitHostEnemyParty, 0,
           sizeof(gTrainerChangeKitHostEnemyParty));
    gTrainerChangeKitHostEnemyParty[0x20] = (uint8_t)species;
    gTrainerChangeKitHostEnemyParty[0x21] = (uint8_t)(species >> 8);
}

void TrainerChangeKitHost_CalculateMonStats(void *raw)
{
    uint8_t *mon = raw;
    mon[0x58] = 123u;
    mon[0x59] = 0u;
}

const uint8_t *TrainerChangeKitHost_ConfigureTrainerBattle(
    const uint8_t *data)
{
    uint16_t source = read16(data + 1);
    gTrainerChangeKitHostOpponentA = source;
    if (sResolveRematchDuringConfigure)
        sConfiguredRematch =
            TrainerChangeKitFinalRuntime_GetRematchTrainerId(source);
    return data + 3;
}

uint8_t TrainerChangeKitHost_ConfigurePolicy(
    uint8_t ai_profile,
    uint8_t mechanic_mode)
{
    ++sPolicyCalls;
    sLastAi = ai_profile;
    sLastMechanic = mechanic_mode;
    return sPolicyShouldFail ? 0u : 1u;
}

void TrainerChangeKitHost_PendingClear(void)
{
    ++sPendingClears;
}

uint8_t TrainerChangeKitHost_PolicyCanMega(
    uint8_t battler, uint8_t allowed)
{
    (void)battler;
    ++sCanCalls;
    return allowed;
}

uint8_t TrainerChangeKitHost_PolicyMarkMega(uint8_t battler)
{
    (void)battler;
    ++sMarkCalls;
    return 1u;
}

uint8_t TrainerChangeKitHost_PolicyCanZ(uint8_t battler, uint8_t allowed)
{
    return TrainerChangeKitHost_PolicyCanMega(battler, allowed);
}

uint8_t TrainerChangeKitHost_PolicyMarkZ(uint8_t battler)
{
    return TrainerChangeKitHost_PolicyMarkMega(battler);
}

uint8_t TrainerChangeKitHost_PolicyCanDynamax(
    uint8_t battler, uint8_t allowed)
{
    return TrainerChangeKitHost_PolicyCanMega(battler, allowed);
}

uint8_t TrainerChangeKitHost_PolicyMarkDynamax(uint8_t battler)
{
    return TrainerChangeKitHost_PolicyMarkMega(battler);
}

uint8_t TrainerChangeKitHost_PolicyCanTera(
    uint8_t battler, uint8_t allowed)
{
    return TrainerChangeKitHost_PolicyCanMega(battler, allowed);
}

uint8_t TrainerChangeKitHost_PolicyMarkTera(uint8_t battler)
{
    return TrainerChangeKitHost_PolicyMarkMega(battler);
}

uint8_t TrainerChangeKitHost_PolicyBegin(void)
{
    ++sPolicyBegins;
    return 1u;
}

uint8_t TrainerChangeKitHost_PolicyEnd(void)
{
    ++sPolicyEnds;
    return 1u;
}

uint8_t TrainerChangeKitHost_SaveLoadGameData(uint8_t save_type)
{
    ++sSaveLoads;
    sLastSaveType = save_type;
    return (uint8_t)(save_type + 1u);
}

void TrainerChangeKitHost_LoadProperAbilityBattleData(void)
{
    unsigned offset = (unsigned)gTrainerChangeKitHostActiveBattler * 88u + 0x38u;
    gTrainerChangeKitHostBattleMons[offset] = 51u;
    gTrainerChangeKitHostBattleMons[offset + 1u] = 0u;
}

uint32_t TrainerChangeKitHost_CommandAddress(const uint8_t *data)
{
    if (data == sCommandA) return UINT32_C(0x1000);
    if (data == sCommandB) return UINT32_C(0x2000);
    if (data == sCommandC) return UINT32_C(0x3000);
    if (data == sCommandD) return UINT32_C(0x4000);
    if (data == sCommandE) return UINT32_C(0x2500);
    return 0u;
}

int main(void)
{
    static const uint8_t command_a[] = {0u, 10u, 0u};
    static const uint8_t command_b[] = {7u, 20u, 0u};
    static const uint8_t command_c[] = {8u, 30u, 0u};
    static const uint8_t command_d[] = {0u, 40u, 0u};
    static const uint8_t command_e[] = {6u, 25u, 0u};
    unsigned policy_before;
    unsigned clear_before;

    sCommandA = command_a;
    sCommandB = command_b;
    sCommandC = command_c;
    sCommandD = command_d;
    sCommandE = command_e;

    CHECK(TrainerChangeKitFinalRuntime_Probe(0) == UINT32_C(0x54434631));
    CHECK(TrainerChangeKitFinalRuntime_Probe(1) == 1302u);
    CHECK(TrainerChangeKitFinalRuntime_Probe(5) == 4284u);
    CHECK((uintptr_t)TrainerChangeKitFinalRuntime_TrainerTable()
          == UINT32_C(0x09000000));

    /* A canonical non-gimmick consumer still owns its AI policy and authored
     * ability context, while mechanic adapters fail closed after Begin. */
    policy_before = sPolicyCalls;
    CHECK(TrainerChangeKitFinalRuntime_ConfigureTrainerBattle(command_a)
          == command_a + 3);
    CHECK(gTrainerChangeKitHostOpponentA == 100u);
    CHECK(sPolicyCalls == policy_before + 1u);
    CHECK(sLastAi == 1u && sLastMechanic == 0u);
    CHECK(TrainerChangeKitFinalRuntime_Probe(9) == 1u);
    CHECK(TrainerChangeKitFinalRuntime_PolicyBeginAdapter());
    CHECK(!TrainerChangeKitFinalRuntime_CanMegaAdapter(1u, 1u));
    CHECK(TrainerChangeKitFinalRuntime_PolicyEndAdapter());

    /* The same physical command safely dispatches an authored Mega row.  The
     * production Can/Mark adapters enforce the authored opponent party slot,
     * but delegate player and non-consumer calls unchanged. */
    CHECK(TrainerChangeKitFinalRuntime_SelectArchive(1u));
    CHECK(TrainerChangeKitFinalRuntime_ConfigureTrainerBattle(command_a)
          == command_a + 3);
    CHECK(gTrainerChangeKitHostOpponentA == 101u);
    CHECK(sLastAi == 5u && sLastMechanic == 1u);
    CHECK(TrainerChangeKitFinalRuntime_Probe(9) == 1u);
    CHECK(TrainerChangeKitFinalRuntime_Probe(13) == 1u);
    CHECK(TrainerChangeKitFinalRuntime_PolicyBeginAdapter());
    CHECK(!TrainerChangeKitFinalRuntime_CanMegaAdapter(3u, 1u));
    CHECK(TrainerChangeKitFinalRuntime_CanMegaAdapter(1u, 1u));
    CHECK(TrainerChangeKitFinalRuntime_CanMegaAdapter(0u, 1u));
    CHECK(!TrainerChangeKitFinalRuntime_CanZAdapter(1u, 1u));
    CHECK(TrainerChangeKitFinalRuntime_MarkMegaAdapter(1u));
    CHECK(!TrainerChangeKitFinalRuntime_MarkMegaAdapter(1u));
    CHECK(TrainerChangeKitFinalRuntime_PolicyEndAdapter());
    CHECK(TrainerChangeKitFinalRuntime_Probe(9) == 0u);
    CHECK(sPolicyEnds == 2u);

    /* A second authored branch of the shared command reaches the Z consumer. */
    gTrainerChangeKitHostBattlerPartyIndexes[3] = 3u;
    CHECK(TrainerChangeKitFinalRuntime_DispatchArchive(2u, command_a)
          == command_a + 3);
    CHECK(gTrainerChangeKitHostOpponentA == 102u);
    CHECK(sLastMechanic == 2u);
    CHECK(TrainerChangeKitFinalRuntime_PolicyBeginAdapter());
    CHECK(TrainerChangeKitFinalRuntime_CanZAdapter(3u, 1u));
    CHECK(TrainerChangeKitFinalRuntime_MarkZAdapter(3u));
    CHECK(TrainerChangeKitFinalRuntime_PolicyEndAdapter());
    CHECK(sPolicyEnds == 3u);

    /* An archive selection cannot bleed into a different canonical command.
     * A kind-7 rematch proxy must prefer its exact row even when the stock
     * resolver returns zero for the high generated destination. */
    CHECK(TrainerChangeKitFinalRuntime_SelectArchive(1u));
    sStockRematchZero = 1u;
    sResolveRematchDuringConfigure = 1u;
    sConfiguredRematch = 0u;
    CHECK(TrainerChangeKitFinalRuntime_ConfigureTrainerBattle(command_b)
          == command_b + 3);
    sResolveRematchDuringConfigure = 0u;
    sStockRematchZero = 0u;
    CHECK(sConfiguredRematch == 201u);
    CHECK(gTrainerChangeKitHostOpponentA == 200u);
    CHECK(sLastAi == 3u && sLastMechanic == 3u);
    gTrainerChangeKitHostBattlerPartyIndexes[1] = 0u;
    gTrainerChangeKitHostBattlerPartyIndexes[3] = 1u;
    CHECK(TrainerChangeKitFinalRuntime_PolicyBeginAdapter());
    CHECK(read16(&gTrainerChangeKitHostBattleMons[88u + 0x38u]) == 90u);
    gTrainerChangeKitHostActiveBattler = 1u;
    gTrainerChangeKitHostBattleMons[88u + 0x38u] = 0u;
    TrainerChangeKitFinalRuntime_LoadProperAbilityBattleDataAdapter();
    CHECK(read16(&gTrainerChangeKitHostBattleMons[88u + 0x38u]) == 90u);
    CHECK(TrainerChangeKitFinalRuntime_CanDynamaxAdapter(3u, 1u));
    CHECK(TrainerChangeKitFinalRuntime_SaveLoadAdapter(2u) == 3u);
    CHECK(sPolicyEnds == 4u);
    CHECK(sSaveLoads == 1u && sLastSaveType == 2u);
    CHECK(TrainerChangeKitFinalRuntime_Probe(9) == 0u);

    /* Kind 6 is a DOUBLE continue-script consumer.  A real switch updates the
     * active battler's party index and revokes the departed user slot. */
    CHECK(TrainerChangeKitFinalRuntime_ConfigureTrainerBattle(command_e)
          == command_e + 3);
    CHECK(gTrainerChangeKitHostOpponentA == 250u);
    CHECK(TrainerChangeKitFinalRuntime_PolicyBeginAdapter());
    CHECK(TrainerChangeKitFinalRuntime_CanDynamaxAdapter(3u, 1u));
    gTrainerChangeKitHostBattlerPartyIndexes[3] = 4u;
    TrainerChangeKitFinalRuntime_PartySlotExit(1u, 1u);
    CHECK(!TrainerChangeKitFinalRuntime_CanDynamaxAdapter(3u, 1u));
    CHECK(TrainerChangeKitFinalRuntime_PolicyEndAdapter());
    CHECK(sPolicyEnds == 5u);

    /* Kind 8 is also DOUBLE.  PolicyBegin installs the authored Tera type only
     * after CFRU has captured its restore backup. */
    gTrainerChangeKitHostBattlerPartyIndexes[1] = 0u;
    CHECK(TrainerChangeKitFinalRuntime_ConfigureTrainerBattle(command_c)
          == command_c + 3);
    CHECK(gTrainerChangeKitHostOpponentA == 300u);
    CHECK(sLastMechanic == 4u);
    CHECK(TrainerChangeKitFinalRuntime_PolicyBeginAdapter());
    CHECK(gTrainerChangeKitHostEnemyParty[0x11] == 17u);
    /* The production scheduler builds the trainer party after policy Begin.
     * Its zeroing builder must not erase the authored Tera byte. */
    TrainerChangeKitFinalRuntime_BuildTrainerPartySetup();
    CHECK(gTrainerChangeKitHostEnemyParty[0x11] == 17u);
    CHECK(read16(&gTrainerChangeKitHostBattleMons[88u + 0x38u]) == 301u);
    CHECK(TrainerChangeKitFinalRuntime_CanTeraAdapter(1u, 1u));
    CHECK(TrainerChangeKitFinalRuntime_MarkTeraAdapter(1u));
    TrainerChangeKitFinalRuntime_BattleAbort(1u);
    CHECK(sPolicyEnds == 6u);

    /* Duplicate canonical rows fail closed to the physical source. */
    CHECK(TrainerChangeKitFinalRuntime_ConfigureTrainerBattle(command_d)
          == command_d + 3);
    CHECK(gTrainerChangeKitHostOpponentA == 40u);
    CHECK(TrainerChangeKitFinalRuntime_Probe(10) >= 1u);

    /* A stale opponent ID after a trainer battle must never grant ownership
     * of a later wild/scripted-wild party to ChangeKit. */
    gTrainerChangeKitHostOpponentA = 200u;
    gTrainerChangeKitHostBattleTypeFlags = 0u;
    TrainerChangeKitFinalRuntime_BuildTrainerPartySetup();
    CHECK(gTrainerChangeKitHostEnemyParty[0x0F] == 0u);
    CHECK(gTrainerChangeKitHostEnemyParty[0x38] == 0u);
    gTrainerChangeKitHostBattleTypeFlags = 8u;

    /* A freshly configured ChangeKit trainer still receives the Stage 34
     * 100-byte party sidecar. */
    CHECK(TrainerChangeKitFinalRuntime_ConfigureTrainerBattle(command_b)
          == command_b + 3);
    TrainerChangeKitFinalRuntime_BuildTrainerPartySetup();
    CHECK(gTrainerChangeKitHostEnemyParty[0x0F] == 8u);
    CHECK(gTrainerChangeKitHostEnemyParty[0x38] == 1u);
    CHECK(gTrainerChangeKitHostEnemyParty[0x3B] == 4u);
    CHECK(gTrainerChangeKitHostEnemyParty[0x54] == 50u);
    CHECK(gTrainerChangeKitHostEnemyParty[0x56] == 123u);
    TrainerChangeKitFinalRuntime_BattleEnd(0u);

    /* High allocated trainer flags translate only at trainer consumers. */
    CHECK(TrainerChangeKitFinalRuntime_SetTrainerFlag(4096u));
    CHECK(sLastFlag == 0x0600u);
    CHECK(TrainerChangeKitFinalRuntime_ScriptFlagSet());
    CHECK(sLastFlag == 0x0520u);

    /* Rematch fallback is compatible when a source has one destination. */
    CHECK(TrainerChangeKitFinalRuntime_GetRematchTrainerId(20u) == 201u);

    /* Failed policy configuration is fail-closed and clears CFRU pending. */
    sPolicyShouldFail = 1u;
    clear_before = sPendingClears;
    CHECK(TrainerChangeKitFinalRuntime_ConfigureTrainerBattle(command_c)
          == command_c + 3);
    CHECK(TrainerChangeKitFinalRuntime_Probe(9) == 0u);
    CHECK(sPendingClears == clear_before + 1u);
    CHECK(TrainerChangeKitFinalRuntime_Probe(11) == 1u);
    sPolicyShouldFail = 0u;

    /* A configured battle that never begins clears the pending command. */
    CHECK(TrainerChangeKitFinalRuntime_DispatchArchive(1u, command_a)
          == command_a + 3);
    clear_before = sPendingClears;
    TrainerChangeKitFinalRuntime_BattleEnd(2u);
    CHECK(sPendingClears == clear_before + 1u);

    CHECK(TrainerChangeKitFinalRuntime_SidecarTable()[0].trainer_id == 200u);
    CHECK(TrainerChangeKitFinalRuntime_SidecarTable()[0].species_id == 25u);
    CHECK(TrainerChangeKitFinalRuntime_SidecarTable()[0].ability_id == 90u);
    CHECK(TrainerChangeKitFinalRuntime_ArchiveTable()[0].archive_id == 1u);
    CHECK(TrainerChangeKitFinalRuntime_ArchiveTable()[1].archive_id == 2u);
    puts("PASS");
    return 0;
}
"""


class TrainerChangeKitFinalRuntimeTests(unittest.TestCase):
    def test_source_contract_is_consumer_scoped(self) -> None:
        source = RUNTIME_C.read_text(encoding="utf-8")
        header = RUNTIME_H.read_text(encoding="utf-8")
        self.assertIn("kind == 6u", source)
        self.assertIn("kind == 8u", source)
        self.assertIn("TRAINER_CHANGEKIT_GIMMICK_CONSUMER", source)
        self.assertIn("FN_CONFIGURE_POLICY", source)
        self.assertNotIn("#define FlagGet", source)
        self.assertIn("TrainerV5Runtime_ConfigureTrainerBattle", header)
        self.assertIn("TrainerChangeKitFinalRuntime_SaveReloadCleanup", header)
        for entrypoint in (
            "PolicyBeginAdapter",
            "PolicyEndAdapter",
            "SaveLoadAdapter",
            "CanMegaAdapter",
            "MarkMegaAdapter",
            "CanZAdapter",
            "MarkZAdapter",
            "CanDynamaxAdapter",
            "MarkDynamaxAdapter",
            "CanTeraAdapter",
            "MarkTeraAdapter",
        ):
            self.assertIn(f"TrainerChangeKitFinalRuntime_{entrypoint}", header)

    def test_stage34_hook_contract_matches_rom(self) -> None:
        contract = json.loads(HOOK_CONTRACT.read_text(encoding="utf-8"))
        baseline = ROOT / contract["baseline"]["path"]
        raw = baseline.read_bytes()
        self.assertEqual(len(raw), contract["baseline"]["size"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), contract["baseline"]["sha256"])

        hooks = contract["bl_rewrites"]
        self.assertEqual(len(hooks), 17)
        eligibility = [row for row in hooks if row["name"].startswith("can_")]
        marks = [row for row in hooks if row["name"].startswith("mark_")]
        self.assertEqual(len(eligibility), 8)
        self.assertEqual(len(marks), 7)
        for row in hooks:
            address = int(row["callsite"], 0)
            offset = address - 0x08000000
            expected = bytes.fromhex(row["expected"])
            self.assertEqual(raw[offset : offset + 4], expected, msg=row["name"])
            high = int.from_bytes(expected[:2], "little")
            low = int.from_bytes(expected[2:], "little")
            self.assertEqual(high & 0xF800, 0xF000, msg=row["name"])
            self.assertEqual(low & 0xF800, 0xF800, msg=row["name"])
            displacement = ((high & 0x07FF) << 12) | ((low & 0x07FF) << 1)
            if displacement & (1 << 22):
                displacement -= 1 << 23
            self.assertEqual(
                address + 4 + displacement,
                int(row["original_target"], 0),
                msg=row["name"],
            )

        save = contract["save_load_entry_rewrite"]
        entry = int(save["entry"], 0)
        expected = bytes.fromhex(save["expected"])
        self.assertEqual(raw[entry - 0x08000000 : entry - 0x08000000 + 8], expected)
        literal = int(save["relocation"]["original_literal_address"], 0)
        self.assertEqual(
            int.from_bytes(raw[literal - 0x08000000 : literal - 0x08000000 + 4], "little"),
            int(save["relocation"]["original_literal_value"], 0),
        )
        trampoline = bytes.fromhex(save["trampoline_bytes"])
        self.assertEqual(len(trampoline), save["trampoline_size"])
        self.assertEqual(trampoline[:6], expected[:6])
        self.assertEqual(
            int.from_bytes(trampoline[16:20], "little"),
            int(save["relocation"]["original_literal_value"], 0),
        )
        self.assertEqual(
            int.from_bytes(trampoline[20:24], "little"),
            int(save["relocation"]["resume_thumb"], 0),
        )

    def test_host_runtime_dispatch_policy_and_cleanup(self) -> None:
        compiler = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
        if compiler is None:
            self.skipTest("host C compiler is unavailable")

        with tempfile.TemporaryDirectory(prefix="trainer-changekit-runtime-") as tmp:
            directory = Path(tmp)
            (directory / "trainer_changekit_final_generated.h").write_text(
                textwrap.dedent(GENERATED_HEADER).lstrip(), encoding="ascii"
            )
            fixture = directory / "fixture.c"
            fixture.write_text(textwrap.dedent(HOST_FIXTURE).lstrip(), encoding="ascii")
            executable = directory / "fixture"
            command = [
                compiler,
                "-std=c11",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-Wno-unused-const-variable",
                "-DTRAINER_CHANGEKIT_FINAL_HOST_TEST",
                f"-I{directory}",
                f"-I{RUNTIME_DIR}",
                str(RUNTIME_C),
                str(fixture),
                "-o",
                str(executable),
            ]
            compiled = subprocess.run(
                command, cwd=ROOT, text=True, capture_output=True, check=False
            )
            self.assertEqual(
                compiled.returncode,
                0,
                msg=f"compile failed\nstdout:\n{compiled.stdout}\nstderr:\n{compiled.stderr}",
            )
            ran = subprocess.run(
                [str(executable)], cwd=ROOT, text=True, capture_output=True, check=False
            )
            self.assertEqual(
                ran.returncode,
                0,
                msg=f"fixture failed\nstdout:\n{ran.stdout}\nstderr:\n{ran.stderr}",
            )
            self.assertEqual(ran.stdout.strip(), "PASS")
            self.assertEqual(ran.stderr, "")

    def test_arm7tdmi_production_compile(self) -> None:
        compiler = shutil.which("arm-none-eabi-gcc")
        if compiler is None:
            self.skipTest("arm-none-eabi-gcc is unavailable")
        contract = json.loads(HOOK_CONTRACT.read_text(encoding="utf-8"))
        defines = dict(contract["runtime_defines"])
        defines.update(
            {
                "VEGA_GET_REMATCH_TRAMPOLINE_ADDRESS": "0x09200001",
                "VEGA_BUILD_TRAINER_PARTY_TRAMPOLINE_ADDRESS": "0x09200021",
                "VEGA_SAVE_LOAD_GAME_DATA_TRAMPOLINE_ADDRESS": "0x09200041",
            }
        )
        with tempfile.TemporaryDirectory(prefix="trainer-changekit-arm-") as tmp:
            directory = Path(tmp)
            (directory / "trainer_changekit_final_generated.h").write_text(
                textwrap.dedent(GENERATED_HEADER).lstrip(), encoding="ascii"
            )
            output = directory / "runtime.o"
            command = [
                compiler,
                "-std=c11",
                "-mthumb",
                "-mcpu=arm7tdmi",
                "-Os",
                "-ffreestanding",
                "-fno-builtin",
                "-Wall",
                "-Wextra",
                "-Werror",
                f"-I{directory}",
                f"-I{RUNTIME_DIR}",
                *[f"-D{name}={value}" for name, value in sorted(defines.items())],
                "-c",
                str(RUNTIME_C),
                "-o",
                str(output),
            ]
            compiled = subprocess.run(
                command, cwd=ROOT, text=True, capture_output=True, check=False
            )
            self.assertEqual(
                compiled.returncode,
                0,
                msg=f"ARM compile failed\nstdout:\n{compiled.stdout}\nstderr:\n{compiled.stderr}",
            )
            self.assertGreater(output.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
