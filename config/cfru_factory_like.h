#ifndef POKEMON_VEGA_CFRU_FACTORY_LIKE_H
#define POKEMON_VEGA_CFRU_FACTORY_LIKE_H

/*
 * CFRU-JP e24a16fe39e27ae162faf5b78596d1f3df18489d 用のFactory-like候補overlay。
 * 使い捨て source sandbox の src/config.h 末尾へ内容を展開する。
 * 参照Factory設定の復元値ではなく、Facility比較用の明示的な候補である。
 */

#if defined(POKEMON_VEGA_CFRU_MINIMAL_H)
#error "cfru_factory_like.h と cfru_minimal.h は同時に使用できません"
#endif

#define POKEMON_VEGA_CFRU_PROFILE_FACTORY_LIKE 1

/* 保存拡張とFacilityのruntime ID/var割当を固定commitの値で保持する。 */
#ifndef SAVE_BLOCK_EXPANSION
#define SAVE_BLOCK_EXPANSION
#endif
/* repointall が無条件参照する gItemData を供給する実測hard dependency。 */
#ifndef EXPANDED_NEW_ITEMS
#define EXPANDED_NEW_ITEMS
#endif
#ifndef FLAG_BATTLE_FACILITY
#define FLAG_BATTLE_FACILITY 0x930
#endif
#ifndef VAR_BATTLE_FACILITY_POKE_NUM
#define VAR_BATTLE_FACILITY_POKE_NUM 0x5015
#endif
#ifndef VAR_BATTLE_FACILITY_POKE_LEVEL
#define VAR_BATTLE_FACILITY_POKE_LEVEL 0x5016
#endif
#ifndef VAR_BATTLE_FACILITY_BATTLE_TYPE
#define VAR_BATTLE_FACILITY_BATTLE_TYPE 0x5017
#endif
#ifndef VAR_BATTLE_FACILITY_TIER
#define VAR_BATTLE_FACILITY_TIER 0x5018
#endif
#ifndef VAR_BATTLE_FACILITY_TRAINER1_NAME
#define VAR_BATTLE_FACILITY_TRAINER1_NAME 0x5019
#endif
#ifndef VAR_BATTLE_FACILITY_TRAINER2_NAME
#define VAR_BATTLE_FACILITY_TRAINER2_NAME 0x501A
#endif
#ifndef VAR_BATTLE_FACILITY_SONG_OVERRIDE
#define VAR_BATTLE_FACILITY_SONG_OVERRIDE 0x501B
#endif

/* TM/HM/Tutor 拡張はitem.cのfallbackが不足する実測hard dependency。 */
#ifndef EXPANDED_TMSHMS
#define EXPANDED_TMSHMS
#endif
#ifndef EXPANDED_MOVE_TUTORS
#define EXPANDED_MOVE_TUTORS
#endif
#ifndef REUSABLE_TMS
#define REUSABLE_TMS
#endif
#ifndef DISPLAY_REAL_POWER_ON_MENU
#define DISPLAY_REAL_POWER_ON_MENU
#endif
#ifndef NUM_TMS
#define NUM_TMS 120
#endif
#ifndef NUM_HMS
#define NUM_HMS 8
#endif
#ifndef NUM_MOVE_TUTORS
#define NUM_MOVE_TUTORS 152
#endif
#ifndef LAST_TOTAL_TUTOR_NUM
#define LAST_TOTAL_TUTOR_NUM 160
#endif

/* Facility AIをVega全体の難度・level scale・通常trainer EVへ波及させない。 */
#undef UNBOUND
#undef VAR_GAME_DIFFICULTY
#undef SCALED_TRAINERS
#undef TRAINERS_WITH_EVS
#undef WILD_ALWAYS_SMART

/* pinned-currentでも無効な実験・debug経路を明示的に無効化する。 */
#undef DEBUG_MEGA
#undef DEBUG_DYNAMAX
#undef DEBUG_TERASTAL
#undef DEXNAV_DETECTOR_MODE
#undef FATHER_PASSES_TMS
#undef INHERIT_MASTER_CHERISH_BALL
#undef SEND_EGGS_TO_PC_IF_MAX_PARTY
#undef VAR_DAYCARE_NUM_EGGS
#undef OLD_EXP_SHARE
#undef OLD_EXP_SPLIT
#undef INSTANT_TEXT

/* Factory比較に不要なfield/UI clusterは候補profileから外す。 */
#undef TIME_ENABLED
#undef DNS_IN_BATTLE
#undef TRAINER_CLASS_POKE_BALLS
#undef DISPLAY_REAL_MOVE_TYPE_ON_MENU
#undef DISPLAY_REAL_ACCURACY_ON_MENU
#undef DISPLAY_EFFECTIVENESS_ON_MENU
#undef SELECT_FROM_PC
/* debug_menu.cが無条件参照するため数値IDは保持し、runtime flagをsetしない。 */
#ifndef FLAG_SYS_DEXNAV
#define FLAG_SYS_DEXNAV 0x91E
#endif
#undef DEXNAV_POKEMON_MOVE_IN_CAVES_WATER
#undef AUTOSCROLL_TEXT_BY_HOLDING_R
#undef FRIENDSHIP_HEART_ON_SUMMARY_SCREEN
#undef CAPTURE_EXPERIENCE
#undef EXP_AFFECTION_BOOST

/*
 * pinned battle engineのFacility分岐を比較できるようgimmickを保持する。
 * 参照ROM測定で不一致なら機能ごとに外し、Factory由来と推定してはならない。
 */
#ifndef MEGA_EVOLUTION_FEATURE
#define MEGA_EVOLUTION_FEATURE
#endif
#ifndef DYNAMAX_FEATURE
#define DYNAMAX_FEATURE
#endif
#ifndef TERASTAL_FEATURE
#define TERASTAL_FEATURE
#endif
/*
 * UNBOUND側のrich spread/trainer tableは使用しない。
 * Factory-like実行にはVega用に生成した非空tableを別途sandboxへ投入する必要がある。
 */

#endif /* POKEMON_VEGA_CFRU_FACTORY_LIKE_H */
