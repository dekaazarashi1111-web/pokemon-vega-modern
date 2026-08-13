#ifndef POKEMON_VEGA_CFRU_ROM_BRIDGE_H
#define POKEMON_VEGA_CFRU_ROM_BRIDGE_H

/*
 * This file is copied into the fixed CFRU-JP src/ directory.  Keep the
 * upstream-facing ABI in CFRU types and the policy-facing ABI in integration.h.
 */
#include "defines.h"
#include "defines_battle.h"
#include "integration.h"

enum
{
    VEGA_RAID_BOSS_PARTY_INDEX = 0,
    VEGA_RAID_INITIAL_SHIELDS = 0,
    VEGA_RAID_DEFAULT_TURN_LIMIT = 10,
    VEGA_RAID_FIRST_PARTNER_MASK = 1
};

/*
 * T12 content may call this immediately before normal battle setup.  The
 * one-shot command first lives in the reviewed 52-byte pre-battle EWRAM
 * shadow, never in Vega event vars or save data.  After the stock heap reset
 * it is transferred once into the allocator-owned NewBattleStruct policy.
 */
bool8 VegaConfigureNextBattlePolicy(u8 ai_profile, CfruMechanicMode mode);
bool8 VegaConfigureNextFacility(
    CfruFacilityFormat format,
    CfruFacilityRule rule,
    CfruMechanicMode mode
);
bool8 VegaConfigureNextMirageItem(u8 party_index, u16 virtual_item);
bool8 VegaConfigureNextRaid(
    u8 boss_party_index,
    u8 partner_mask,
    u8 shield_count,
    u8 turn_limit,
    u8 capture_allowed
);
bool8 VegaBattlePolicyPrepareStorage(void);
bool8 VegaBattlePolicyPrepareFacilityBattle(void);
u8 VegaNormalizeTrainerAIProfile(u32 trainer_ai_flags);
bool8 VegaBattlePolicyIsRaid(void);
bool8 VegaBattlePolicyRaidCaptureAllowed(void);
bool8 VegaBattlePolicyRaidCaptureSucceeded(void);
bool8 VegaBattlePolicyRaidAdvanceTurnAndExpired(void);
bool8 VegaBattlePolicyPrepareTeraTypes(void);
bool8 VegaBattlePolicyRestoreTeraTypes(void);
void VegaBattlePolicyRestoreCapturedTeraType(struct Pokemon *mon);
u8 VegaGiveCaughtMonToPlayer(struct Pokemon *mon);

/*
 * Call immediately after HandleNewBattleRamClearBeforeBattle().  At this
 * point gBattlersCount is still zero; InitBattleControllers owns its later
 * transition to 2/4 (or the raid controller's transition to 3).
 */
bool8 VegaBattlePolicyBegin(void);

/*
 * Call once at the tail of EndOfBattleThings(), after CFRU has restored its
 * parties/items/forms.  The wrapper translates gBattleOutcome and clears all
 * integration-owned battle-local state, including Mirage and Raid state.
 */
bool8 VegaBattlePolicyEnd(void);
CfruBattleExit VegaBattlePolicyMapOutcome(u8 outcome);

bool8 VegaFacilityStateIsActive(void);
u16 VegaFacilityStateGet(u16 field);
void VegaFacilityStateSet(u16 field, u16 value);
u16 VegaFacilityFirstOpponent(void);
u16 VegaFacilitySecondOpponent(void);
u16 VegaFacilityPartner(void);

/*
 * Use at the final GetAIFlags() return point.  Existing nonzero trainer,
 * Safari, roaming, tutorial, and facility flags remain authoritative.  The
 * policy profile is used only when upstream supplied no AI bits.
 */
u32 VegaBattlePolicyResolveAIProfileBits(u8 battler, u32 fallback);

/*
 * Gate each upstream Can* result through the selected battle policy.  Call the
 * matching Mark* only after the upstream mechanic activation succeeds.
 */
bool8 VegaBattlePolicyCanMega(u8 battler, bool8 upstream_allowed);
bool8 VegaBattlePolicyMarkMega(u8 battler);
bool8 VegaBattlePolicyCanZ(u8 battler, bool8 upstream_allowed);
bool8 VegaBattlePolicyMarkZ(u8 battler);
bool8 VegaBattlePolicyCanDynamax(u8 battler, bool8 upstream_allowed);
bool8 VegaBattlePolicyMarkDynamax(u8 battler);
bool8 VegaBattlePolicyCanTera(u8 battler, bool8 upstream_allowed);
bool8 VegaBattlePolicyMarkTera(u8 battler);

#endif /* POKEMON_VEGA_CFRU_ROM_BRIDGE_H */
