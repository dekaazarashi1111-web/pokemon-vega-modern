#ifndef PR16_LEARNSET_OWNER_H
#define PR16_LEARNSET_OWNER_H

#include <stdint.h>

/* 配置前payload用のowner gate。ゲーム側callsite/ROMへの接続は別受入。 */
#define PR16_LEARNSET_SPECIES_COUNT 1671u
#define PR16_LEARNSET_NO_OWNER 65535u

enum Pr16LearnsetPolicy {
    PR16_POLICY_EXPLICIT_OWNER = 1,
    PR16_POLICY_INTERNAL = 2,
    PR16_POLICY_EXCLUDED_REMAKE = 3,
    PR16_POLICY_NON_BATTLING = 4,
    PR16_POLICY_BATTLE_COPY = 5,
    PR16_POLICY_BATTLE_FORM = 6,
    PR16_POLICY_MEGA = 7
};

enum Pr16LearnsetConsumer {
    PR16_CONSUMER_EGG = 0,
    PR16_CONSUMER_EVOLUTION = 1,
    PR16_CONSUMER_FORM_CHANGE = 2,
    PR16_CONSUMER_LEVEL_UP = 3,
    PR16_CONSUMER_MACHINE = 4,
    PR16_CONSUMER_PRE_EVOLUTION_CARRY = 5,
    PR16_CONSUMER_REMINDER = 6,
    PR16_CONSUMER_SHARED_EGG = 7,
    PR16_CONSUMER_TUTOR = 8,
    PR16_CONSUMER_COUNT = 9
};

enum Pr16LearnsetAction {
    PR16_OWNER_INVALID = 0,
    PR16_OWNER_PREPARED_LOOKUP = 1,
    PR16_OWNER_PRESERVE_IDENTITY = 2,
    PR16_OWNER_CARRY_EXISTING = 3,
    PR16_OWNER_CONDITION_REQUIRED = 4
};

/* 戻り値を検査せずownerを表indexに使わない。個体/技/PP/saveへの書込口はない。
 * 条件付き姿/進化前技は自動付与せず、専用consumerが未接続なら停止する。
 * 通常eggとshared eggも別consumer。特殊孵化条件はこのgateで満たしたことにしない。
 */
uint8_t Pr16ResolveLearnsetOwner(const uint8_t *policies, uint16_t policy_count,
                               uint16_t species, uint8_t consumer,
                               uint16_t *owner);
#endif
