#ifndef POKEMON_VEGA_CFRU_VEGA_MINIMAL_H
#define POKEMON_VEGA_CFRU_VEGA_MINIMAL_H

/*
 * T06 release profile for CFRU-JP
 * e24a16fe39e27ae162faf5b78596d1f3df18489d.
 *
 * This file is appended to src/config.h only inside a disposable, pinned
 * source sandbox.  The battle engine and its four optional mechanic cores are
 * compiled, while activation is owned by the T06 battle-start policy adapter.
 * No global difficulty or party-level scaling switch is enabled here.
 */

#if defined(POKEMON_VEGA_CFRU_PROFILE_MINIMAL) \
 || defined(POKEMON_VEGA_CFRU_PROFILE_FACTORY_LIKE)
#error "cfru_vega_minimal.h cannot be combined with a T01 profile"
#endif

#define POKEMON_VEGA_CFRU_PROFILE_VEGA_MINIMAL 1

/* Pinned CFRU build dependencies. */
#ifndef SAVE_BLOCK_EXPANSION
#define SAVE_BLOCK_EXPANSION
#endif
#ifndef EXPANDED_NEW_ITEMS
#define EXPANDED_NEW_ITEMS
#endif
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

/*
 * The fixed Factory raw flag/vars (0x930, 0x403A, 0x5015..0x501E) are not
 * safe Vega storage.  T06 keeps facility policy battle-local; T08 owns the
 * persistent namespace.  Sandbox source rewriting rejects every raw use.
 */
#define VEGA_CFRU_FACILITY_BATTLE_LOCAL 1

/* Compile each mechanic core; runtime selection remains mutually exclusive. */
#ifndef MEGA_EVOLUTION_FEATURE
#define MEGA_EVOLUTION_FEATURE
#endif
#ifndef DYNAMAX_FEATURE
#define DYNAMAX_FEATURE
#endif
#ifndef TERASTAL_FEATURE
#define TERASTAL_FEATURE
#endif
#define VEGA_MECHANIC_POLICY_RUNTIME 1

/* Never opt Vega into global difficulty, scaling, or omniscient-wild modes. */
#undef UNBOUND
#undef VAR_GAME_DIFFICULTY
#undef SCALED_TRAINERS
#undef TRAINERS_WITH_EVS
#undef WILD_ALWAYS_SMART
#undef FLAG_RAID_BATTLE_NO_FORCE_END
#undef DEBUG_NO_LEVEL_SCALING

/* Debug and unrelated field/UI feature clusters stay disabled. */
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
#undef TIME_ENABLED
#undef DNS_IN_BATTLE
#undef TRAINER_CLASS_POKE_BALLS
#undef DISPLAY_REAL_MOVE_TYPE_ON_MENU
#undef DISPLAY_REAL_ACCURACY_ON_MENU
#undef DISPLAY_EFFECTIVENESS_ON_MENU
#undef SELECT_FROM_PC
#undef DEXNAV_POKEMON_MOVE_IN_CAVES_WATER
#undef AUTOSCROLL_TEXT_BY_HOLDING_R
#undef FRIENDSHIP_HEART_ON_SUMMARY_SCREEN
#undef CAPTURE_EXPERIENCE
#undef EXP_AFFECTION_BOOST

/* debug_menu.c has an unconditional reference; the runtime flag is never set. */
#ifndef FLAG_SYS_DEXNAV
#define FLAG_SYS_DEXNAV 0x91E
#endif

#endif /* POKEMON_VEGA_CFRU_VEGA_MINIMAL_H */
