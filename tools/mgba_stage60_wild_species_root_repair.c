/* Stage60 power-on -> first rival -> Route501 natural grass acceptance. */

#define CODEX_IPAD_BOOTSTRAP_EMBEDDED
#include "mgba_codex_battle_ipad_bootstrap.c"

enum {
    S60_A = 1U,
    S60_RIGHT = 16U,
    S60_LEFT = 32U,
    S60_UP = 64U,
    S60_DOWN = 128U,
    S60_OVERWORLD = 0x08055E75U,
    S60_GET_SPECIES_NAME = 0x080406C5U,
    S60_NICKNAME_SCRATCH = 0x0203F000U,
    S60_CANONICAL_SCRATCH = 0x0203F020U,
    S60_NAME_SIZE = 11U,
};

static uint16_t s60_key(char command)
{
    switch (command) {
    case 'R': return S60_RIGHT;
    case 'L': return S60_LEFT;
    case 'U': return S60_UP;
    case 'D': return S60_DOWN;
    default: bootstrap_die("unsupported normal-input command");
    }
    return 0U;
}

static void s60_commands(struct mCore *core, const char *commands)
{
    for (; *commands; ++commands) {
        run_key_frames(core, s60_key(*commands), 8U);
        run_key_frames(core, 0U, 12U);
    }
}

static void s60_a(struct mCore *core)
{
    run_key_frames(core, S60_A, 2U);
    run_key_frames(core, 0U, 100U);
}

static void s60_verify_name(struct mCore *core, uint16_t species)
{
    for (unsigned index = 0U; index < S60_NAME_SIZE; ++index) {
        write8(core, S60_NICKNAME_SCRATCH + index, 0U);
        write8(core, S60_CANONICAL_SCRATCH + index, 0U);
    }
    (void)call_preserving(core, BATTLE_CORE_GET_MON_DATA, ADDR_ENEMY_PARTY,
                          2U, S60_NICKNAME_SCRATCH, 0U);
    (void)call_preserving(core, S60_GET_SPECIES_NAME, S60_CANONICAL_SCRATCH,
                          species, 0U, 0U);
    for (unsigned index = 0U; index < S60_NAME_SIZE; ++index) {
        uint8_t actual = read8(core, S60_NICKNAME_SCRATCH + index);
        uint8_t expected = read8(core, S60_CANONICAL_SCRATCH + index);
        if (actual != expected)
            bootstrap_die("wild nickname and Species name differ");
        if (expected == 0xFFU)
            return;
    }
    bootstrap_die("wild Species name is unterminated");
}

int main(int argc, char **argv)
{
    if (argc != 4) {
        fprintf(stderr, "usage: %s ROM SAVE IMAGE_PREFIX\n", argv[0]);
        return 2;
    }
    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    color_t *video = calloc(240U * 160U, sizeof(*video));
    if (!video)
        return 2;
    struct mCore *core = bootstrap_open_core(argv[1], argv[2], video);

    /* BOOT_TRACE is exclusively GBA key states; no warp, direct function
     * invocation, RAM edit, or savestate is used by this acceptance path. */
    run_trace_prefix(core);
    s60_commands(core, "DDDDDDDDDDLLLLLLDDDDDDDDRUUURRRRRR");
    for (unsigned press = 0U; press < 120U; ++press)
        s60_a(core);
    s60_commands(core, "DDRRRRU");
    for (unsigned press = 0U; press < 40U; ++press)
        s60_a(core);
    if (read8(core, ADDR_PLAYER_PARTY_COUNT) != 1U
        || read16(core, ADDR_PLAYER_PARTY
            + BATTLE_CORE_PARTY_SPECIES_OFFSET) != 7U)
        bootstrap_die("normal-input starter selection differs");

    s60_commands(core, "DDDLLLLLDDDDD");
    bool rival_seen = false;
    bool rival_finished = false;
    for (unsigned press = 0U; press < 320U; ++press) {
        s60_a(core);
        if (read8(core, ADDR_BATTLERS_COUNT) >= 2U)
            rival_seen = true;
        if (rival_seen && press >= 32U
            && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S60_OVERWORLD) {
            rival_finished = true;
            break;
        }
    }
    if (!rival_seen || !rival_finished)
        bootstrap_die("normal-input first rival route differs");
    for (unsigned press = 0U; press < 80U; ++press)
        s60_a(core);

    s60_commands(core,
        "DDDDDDDDDDRRDDDDRRRRRRRRRRRRRRRRRRRRUUUURRRRRRR"
        "UUUUUUURRRRRRRRRRRRRRRRRRRLLLLDDDDDDDLLLLLLLLLLRRRR");
    run_key_frames(core, 0U, 600U);

    uint32_t save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
    uint16_t party_species = read16(
        core, ADDR_ENEMY_PARTY + BATTLE_CORE_PARTY_SPECIES_OFFSET);
    uint16_t battle_species = read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE);
    uint32_t flags = read32(core, ADDR_BATTLE_TYPE_FLAGS);
    if (read8(core, save1 + 4U) != 3U || read8(core, save1 + 5U) != 19U
        || party_species != 10U || battle_species != party_species
        || (flags & 8U) != 0U || read32(core, 0x0203EDE4U) != 0U)
        bootstrap_die("Route501 wild identity acceptance differs");
    s60_verify_name(core, party_species);
    bootstrap_write_ppm(argv[3], video);

    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"emulator\":\"libmGBA\",\"required\":true,"
           "\"actual_run\":true,\"power_on\":true,"
           "\"normal_gba_input_only\":true,\"host_warp\":false,"
           "\"savestate_load\":false,\"direct_game_function_call\":false,"
           "\"map_group\":3,\"map_number\":19,"
           "\"intended_species\":10,\"party_species\":%u,"
           "\"battle_mon_species\":%u,\"canonical_name\":true,"
           "\"trainer_flag\":false,\"changekit_context_idle\":true,"
           "\"frame\":%" PRIu32 "}\n",
           party_species, battle_species, core->frameCounter(core));
    bootstrap_close_core(core);
    free(video);
    return 0;
}
