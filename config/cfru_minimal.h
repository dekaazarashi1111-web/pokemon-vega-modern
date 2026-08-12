#ifndef POKEMON_VEGA_CFRU_MINIMAL_H
#define POKEMON_VEGA_CFRU_MINIMAL_H

/*
 * CFRU-JP e24a16fe39e27ae162faf5b78596d1f3df18489d 用の最小 overlay。
 * 使い捨て source sandbox の src/config.h 末尾へ内容を展開する。
 * 数値 ID は移動せず、任意機能の compile switch だけを明示的に絞る。
 */

#if defined(POKEMON_VEGA_CFRU_FACTORY_LIKE_H)
#error "cfru_minimal.h と cfru_factory_like.h は同時に使用できません"
#endif

#define POKEMON_VEGA_CFRU_PROFILE_MINIMAL 1

/* 保存拡張は上流自身が hard dependency としているため必ず保持する。 */
#ifndef SAVE_BLOCK_EXPANSION
#define SAVE_BLOCK_EXPANSION
#endif

/*
 * repointall が gItemData を無条件参照し、symbol本体はこのswitch配下にある。
 * 無効化buildでmissing symbolを実測したため、最小profileでも必ず保持する。
 */
#ifndef EXPANDED_NEW_ITEMS
#define EXPANDED_NEW_ITEMS
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

/* Vegaへ暗黙導入してはいけない難度・育成値・全知化profile。 */
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

/* 最小profileでは時刻、表示、field QOLを外す。 */
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

/* 最小profileでは任意の戦闘gimmickを外す。 */
#undef MEGA_EVOLUTION_FEATURE
#undef DYNAMAX_FEATURE
#undef TERASTAL_FEATURE
#undef CAPTURE_EXPERIENCE
#undef EXP_AFFECTION_BOOST

/*
 * FLAG_SCALE_* と FLAG_BATTLE_FACILITY はruntime flagの数値IDなので保持する。
 * このheaderはそれらをsetせず、facility source自体にもcompile gateはない。
 */

#endif /* POKEMON_VEGA_CFRU_MINIMAL_H */
