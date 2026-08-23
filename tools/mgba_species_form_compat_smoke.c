/* Stage 48 exact-ROM regression for canonical Species-dependent forms. */

/*
 * scripts/build_species_form_compat.py prepends
 * mgba_species_runtime_smoke.c after renaming that file's main function.
 * Keeping the extension separate avoids changing the already-published
 * Stage09 runner identity while still reusing its exact-ROM helpers.
 */

#ifndef COMPAT_FORMS_REVERT
#define COMPAT_FORMS_REVERT UINT32_C(0x09100C41)
#endif

enum {
    COMPAT_MON_DATA_SPECIES = 11,
    COMPAT_PARTY_BACKUP_SPECIES = 0x1C,
    COMPAT_BASE_STATS_POINTER = 0x080001BC,
    COMPAT_BASE_STATS_STRIDE = 32,
    COMPAT_BASE_STATS_TYPE1 = 6,
    COMPAT_BASE_STATS_TYPE2 = 7,
    COMPAT_BATTLE_MON_ATTACK = 0x02,
    COMPAT_BATTLE_MON_DEFENSE = 0x04,
    COMPAT_BATTLE_MON_SPEED = 0x06,
    COMPAT_BATTLE_MON_SP_ATTACK = 0x08,
    COMPAT_BATTLE_MON_SP_DEFENSE = 0x0A,
    COMPAT_HIT_MARKER = 0x02023DD0,
    COMPAT_DISABLE_STRUCTS = 0x02023D6C,
    COMPAT_DISABLE_IS_FIRST_TURN = 0x16,
    COMPAT_LAST_USED_ABILITY = 0x0203DFAC,
    COMPAT_MIMIKYU = 1176,
    COMPAT_MIMIKYU_BUSTED = 1253,
    COMPAT_MORPEKO = 1350,
    COMPAT_MORPEKO_HANGRY = 1385,
    COMPAT_ABILITY_SPEED_BOOST = 3,
    COMPAT_ABILITY_INTIMIDATE = 22,
};

static uint16_t compat_party_species(struct mCore *core)
{
    return (uint16_t)call_preserving(
        core, BATTLE_CORE_GET_MON_DATA, ADDR_PLAYER_PARTY,
        COMPAT_MON_DATA_SPECIES, 0U, 0U);
}

static void compat_apply_form_controller(struct mCore *core,
                                         uint16_t base_species,
                                         uint16_t form_species)
{
    /* Mirror REQUEST_FORM_CHANGE_BATTLE's player-controller party update. */
    set_mon_data_u32(core, ADDR_PLAYER_PARTY,
                     COMPAT_MON_DATA_SPECIES, form_species);
    if (read16(core, ADDR_PLAYER_PARTY + COMPAT_PARTY_BACKUP_SPECIES) == 0U)
        write16(core, ADDR_PLAYER_PARTY + COMPAT_PARTY_BACKUP_SPECIES,
                base_species);
    write32_bytes(core, BATTLE_EXEC_BUFFER, 0U);
}

static void compat_require_form_surface(struct mCore *core, uint16_t species,
                                        uint16_t ability, const char *label)
{
    uint32_t stats = read32(core, COMPAT_BASE_STATS_POINTER)
        + (uint32_t)species * COMPAT_BASE_STATS_STRIDE;
    uint32_t mon = ADDR_BATTLE_MONS;
    if (read16(core, mon) != species
        || read16(core, mon + BATTLE_MON_ABILITY) != ability
        || read8(core, mon + BATTLE_CORE_MON_TYPE1)
               != read8(core, stats + COMPAT_BASE_STATS_TYPE1)
        || read8(core, mon + BATTLE_CORE_MON_TYPE2)
               != read8(core, stats + COMPAT_BASE_STATS_TYPE2)
        || read16(core, mon + COMPAT_BATTLE_MON_ATTACK) == 0U
        || read16(core, mon + COMPAT_BATTLE_MON_DEFENSE) == 0U
        || read16(core, mon + COMPAT_BATTLE_MON_SPEED) == 0U
        || read16(core, mon + COMPAT_BATTLE_MON_SP_ATTACK) == 0U
        || read16(core, mon + COMPAT_BATTLE_MON_SP_DEFENSE) == 0U) {
        fprintf(stderr,
                "mgba-species-form-compat: %s species/type/stats/ability mismatch\n",
                label);
        battle_core_die("form-change battle surface is not canonical");
    }
    verify_display_species(core, species);
}

static void compat_end_turn(struct mCore *core, uint16_t expected,
                            const char *label)
{
    uint32_t battle_struct = read32(core, BATTLE_STRUCT_POINTER);
    if (battle_struct < 0x02000000U || battle_struct >= 0x02040000U)
        battle_core_die("Stage48 BattleStruct pointer is invalid");
    write32_bytes(core, BATTLE_EXEC_BUFFER, 0U);
    write8(core, battle_struct, TURN_EFFECT_FORM_CHANGE);
    write8(core, battle_struct + 1U, 0U);
    write8(core, BANKS_BY_TURN_ORDER, 0U);
    write8(core, BANKS_BY_TURN_ORDER + 1U, 1U);
    if (call_preserving(core, TURN_BASED_EFFECTS, 0U, 0U, 0U, 0U) != 1U)
        battle_core_die("Stage48 end-turn form handler did not activate");
    require_form_species(core, expected, label);
}

static void compat_verify_hunger_switch(struct mCore *core,
                                        const struct Snapshot *field)
{
    static const uint16_t expected[] = {
        COMPAT_MORPEKO_HANGRY, COMPAT_MORPEKO,
        COMPAT_MORPEKO_HANGRY, COMPAT_MORPEKO,
    };
    prepare_form_battle(
        core, field, COMPAT_MORPEKO, ABILITY_HUNGER_SWITCH);
    for (unsigned turn = 0; turn < ARRAY_LEN(expected); ++turn) {
        compat_end_turn(core, expected[turn], "Morpeko four-turn alternation");
        compat_apply_form_controller(core, COMPAT_MORPEKO, expected[turn]);
        compat_require_form_surface(
            core, expected[turn], ABILITY_HUNGER_SWITCH,
            "Morpeko four-turn alternation");
        if (compat_party_species(core) != expected[turn])
            battle_core_die("Morpeko party form did not follow battle form");
    }
}

static void compat_damage_call(struct mCore *core, uint32_t damage)
{
    write8(core, BANK_ATTACKER, 1U);
    write8(core, BANK_TARGET, 0U);
    write16(core, CURRENT_MOVE, BATTLE_CORE_MOVE_TACKLE);
    write32_bytes(core, BATTLE_MOVE_DAMAGE, damage);
    write32_bytes(core, MOVE_RESULT_FLAGS, 0U);
    write32_bytes(core, COMPAT_HIT_MARKER, 0U);
    write32_bytes(core, BATTLE_EXEC_BUFFER, 0U);
    write8(core, FORM_SCRIPT_SCRATCH, 0x0CU);
    write8(core, FORM_SCRIPT_SCRATCH + 1U, 0U);
    write32_bytes(core, BATTLE_SCRIPT_POINTER, FORM_SCRIPT_SCRATCH);
    (void)call_preserving(core, ATK0C_DATA_HP_UPDATE, 0U, 0U, 0U, 0U);
}

static void compat_verify_disguise(struct mCore *core,
                                   const struct Snapshot *field)
{
    prepare_form_battle(core, field, COMPAT_MIMIKYU, ABILITY_DISGUISE);
    uint16_t max_hp = read16(core, ADDR_BATTLE_MONS + BATTLE_MON_MAX_HP);
    uint32_t disguise_damage = max_hp / 8U;
    if (disguise_damage == 0U)
        battle_core_die("Mimikyu fixture maximum HP is too small");

    compat_damage_call(core, 10U);
    require_form_species(core, COMPAT_MIMIKYU_BUSTED,
                         "Mimikyu first Disguise hit");
    if (read32(core, BATTLE_MOVE_DAMAGE) != disguise_damage
        || read16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_HP) != max_hp)
        battle_core_die("Disguise first hit is not exact base HP / 8");
    compat_apply_form_controller(core, COMPAT_MIMIKYU,
                                 COMPAT_MIMIKYU_BUSTED);
    compat_require_form_surface(core, COMPAT_MIMIKYU_BUSTED,
                                ABILITY_DISGUISE,
                                "Mimikyu busted form");
    if (compat_party_species(core) != COMPAT_MIMIKYU_BUSTED)
        battle_core_die("Mimikyu party form did not follow battle form");

    compat_damage_call(core, 10U);
    require_form_species(core, COMPAT_MIMIKYU_BUSTED,
                         "Mimikyu second normal hit");
    if (read32(core, BATTLE_MOVE_DAMAGE) != 10U
        || read16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_HP)
               != (uint16_t)(max_hp - 10U))
        battle_core_die("Mimikyu second hit did not take normal damage");
}

static void compat_verify_party_revert(struct mCore *core,
                                       const struct Snapshot *field,
                                       uint16_t base_species,
                                       uint16_t form_species,
                                       const char *label)
{
    restore_snapshot(core, field);
    clear_parties(core);
    create_mon(core, ADDR_PLAYER_PARTY, base_species, 100U);
    set_mon_data_u32(core, ADDR_PLAYER_PARTY,
                     COMPAT_MON_DATA_SPECIES, form_species);
    write16(core, ADDR_PLAYER_PARTY + COMPAT_PARTY_BACKUP_SPECIES,
            base_species);
    (void)call_preserving(core, COMPAT_FORMS_REVERT,
                          ADDR_PLAYER_PARTY, 0U, 0U, 0U);
    if (compat_party_species(core) != base_species
        || read16(core, ADDR_PLAYER_PARTY + COMPAT_PARTY_BACKUP_SPECIES) != 0U) {
        fprintf(stderr,
                "mgba-species-form-compat: %s restore species=%u backup=%u\n",
                label, compat_party_species(core),
                read16(core, ADDR_PLAYER_PARTY
                       + COMPAT_PARTY_BACKUP_SPECIES));
        battle_core_die("battle-end form restoration differs");
    }
}

static void compat_verify_display_matrix(struct mCore *core,
                                         const struct Snapshot *field)
{
    static const uint16_t display_samples[] = {
        7U,    /* Vega既存 */
        418U,  /* Gen 1 */
        649U,  /* Gen 3 surface canary */
        1007U, /* Zygarde */
        1019U, /* Zygarde Complete */
        1055U, /* Mega */
        1176U, /* Mimikyu */
        1253U, /* Mimikyu busted */
        1348U, /* Eiscue */
        1383U, /* Eiscue Noice */
        1350U, /* Morpeko */
        1385U, /* Morpeko Hangry */
        1448U, /* Gigantamax */
        1484U, /* Gen 9 */
    };
    for (unsigned index = 0; index < ARRAY_LEN(display_samples); ++index)
        verify_display_species(core, display_samples[index]);

    static const uint16_t player_back_samples[] = {
        7U, 1007U, 1019U, 1055U, 1253U, 1385U, 1484U,
    };
    for (unsigned index = 0; index < ARRAY_LEN(player_back_samples); ++index)
        verify_battle_name_surface(
            core, field, player_back_samples[index], 1288U);
}

static void compat_verify_core_abilities(struct mCore *core,
                                         const struct Snapshot *field)
{
    prepare_form_battle(core, field, 7U, COMPAT_ABILITY_INTIMIDATE);
    if (call_preserving(core, ABILITY_BATTLE_EFFECTS,
                        0U, 0U, 0U, 0U) != 1U)
        battle_core_die("canonical Intimidate switch-in path did not activate");

    prepare_form_battle(core, field, 261U, COMPAT_ABILITY_SPEED_BOOST);
    write8(core, COMPAT_DISABLE_STRUCTS + COMPAT_DISABLE_IS_FIRST_TURN, 0U);
    uint32_t effect = call_preserving(core, ABILITY_BATTLE_EFFECTS,
                                      1U, 0U, 0U, 0U);
    if (effect != 1U) {
        fprintf(stderr,
                "mgba-species-form-compat: Speed Boost effect=%u ability=%u "
                "stage=%u firstTurn=%u hp=%u last=%u\n",
                effect, read16(core, ADDR_BATTLE_MONS + BATTLE_MON_ABILITY),
                read8(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_STAT_STAGES
                      + 2U),
                read8(core, COMPAT_DISABLE_STRUCTS
                      + COMPAT_DISABLE_IS_FIRST_TURN),
                read16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_HP),
                read16(core, COMPAT_LAST_USED_ABILITY));
        battle_core_die("canonical Speed Boost end-turn path did not activate");
    }
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "usage: %s ROM\n", argv[0]);
        return 2;
    }
    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {.sample = NULL, .unixTime = fixed_unix_time,
                             .serialize = NULL, .deserialize = NULL};
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core) || !mCoreLoadFile(core, argv[1]))
        battle_core_die("Stage48 core/ROM initialization failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    run_trace_prefix(core);
    struct Snapshot field = take_snapshot(core);

    compat_verify_hunger_switch(core, &field);
    compat_verify_disguise(core, &field);
    compat_verify_party_revert(core, &field, COMPAT_MORPEKO,
                               COMPAT_MORPEKO_HANGRY, "Morpeko");
    compat_verify_party_revert(core, &field, COMPAT_MIMIKYU,
                               COMPAT_MIMIKYU_BUSTED, "Mimikyu");
    verify_canonical_form_abilities(core, &field);
    compat_verify_core_abilities(core, &field);
    compat_verify_display_matrix(core, &field);

    printf(
        "{\"status\":\"PASS\",\"warnings\":0,"
        "\"canonical_species_count\":1621,"
        "\"canonical_ability_count\":312,"
        "\"form_ability_families\":7,\"form_transitions\":8,"
        "\"hunger_switch_turns\":4,\"hunger_switch_alternating\":true,"
        "\"disguise_first_hit_base_hp_fraction\":8,"
        "\"disguise_second_hit_normal\":true,"
        "\"party_restoration_cases\":2,"
        "\"form_species_type_stats_ability\":true,"
        "\"display_matrix_species\":14,"
        "\"player_back_sprite_cases\":7,"
        "\"back_sprite_dimensions\":\"64x64\","
        "\"back_sprite_obj_tile_bytes\":2048,"
        "\"battle_bond_ko\":true,\"schooling\":true,"
        "\"zen_mode\":true,\"ice_face\":true,"
        "\"power_construct\":true,\"intimidate\":true,"
        "\"speed_boost\":true}\n");

    free(field.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
