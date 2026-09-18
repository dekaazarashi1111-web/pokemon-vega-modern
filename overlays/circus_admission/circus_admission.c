#include "circus_admission.h"

/* raw Var403A、save、battle type、Circus効果bitには書き込まない。
 * 既存の受付が成功させたpendingを検査し、所有APIでnumberだけを更新する。
 * 効果の供給元は別途、正規sp072の抽選経路へ接続する。
 */
cfru_u8 VegaCircusAdmissionSelectPending(void)
{
    static const cfru_u8 tiers[CFRU_FACILITY_RULE_COUNT] = {
        0, 4, 6, 1, 2, 3, 7, 5
    };
    CfruPendingBattleCommand before, after;
    const unsigned char *left = (const unsigned char *)&before;
    const unsigned char *right = (const unsigned char *)&after;
    cfru_u8 index, party_size, battle_type;

    if (!cfru_integration_pending_copy(&before)
        || before.active != CFRU_TRUE || before.facility_active != CFRU_TRUE
        || before.ai_profile != CFRU_AI_FULL_SMART
        || before.mechanic_mode != CFRU_MECHANIC_STANDARD
        || before.facility_format >= CFRU_FACILITY_FORMAT_COUNT
        || before.facility_rule >= CFRU_FACILITY_RULE_COUNT
        || before.mirage_mask || before.raid_active || before.reserved
        || before.raid_boss_party_index || before.raid_partner_mask
        || before.raid_shield_count || before.raid_turn_limit
        || before.raid_capture_allowed)
        return VEGA_CIRCUS_ADMISSION_REJECTED;
    for (index = 0; index < CFRU_PARTY_SIZE; ++index)
        if (before.mirage_virtual_items[index])
            return VEGA_CIRCUS_ADMISSION_REJECTED;

    party_size = before.facility_format == CFRU_FACILITY_SINGLE_3V3 ? 3
               : before.facility_format == CFRU_FACILITY_DOUBLE_4V4 ? 4 : 2;
    battle_type = (cfru_u8)(before.facility_format
        + (before.facility_rule == CFRU_FACILITY_RANDOM ? 4 : 0));
    if ((before.facility_state[0] != 0
         && before.facility_state[0] != VEGA_CIRCUS_FACILITY_NUMBER)
        || before.facility_state[1] != party_size
        || before.facility_state[2] != 50
        || before.facility_state[3] != battle_type
        || before.facility_state[4] != tiers[before.facility_rule])
        return VEGA_CIRCUS_ADMISSION_REJECTED;

    if (before.facility_state[0] == VEGA_CIRCUS_FACILITY_NUMBER)
        return VEGA_CIRCUS_ADMISSION_SELECTED;
    cfru_integration_pending_facility_set(VEGA_CIRCUS_STATE_NUMBER,
                                        VEGA_CIRCUS_FACILITY_NUMBER);
    before.facility_state[0] = VEGA_CIRCUS_FACILITY_NUMBER;
    if (!cfru_integration_pending_copy(&after))
        return VEGA_CIRCUS_ADMISSION_REJECTED;
    for (index = 0; index < sizeof(before); ++index)
        if (left[index] != right[index])
            return VEGA_CIRCUS_ADMISSION_REJECTED;
    return VEGA_CIRCUS_ADMISSION_SELECTED;
}
