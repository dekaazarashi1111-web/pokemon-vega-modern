/* Exhaustive exact-ROM smoke for the canonical 1,621-Species creation surface. */

#define BATTLE_CORE_EMBEDDED
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#include "mgba_battle_core_smoke.c"
#pragma GCC diagnostic pop

enum {
    SPECIES_RUNTIME_COUNT = 1621,
    GET_SPECIES_NAME = 0x080406C5,
    NAME_SCRATCH = 0x0203E800,
    NAME_LENGTH = 11,
};

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
    if (!core || !core->init(core) || !mCoreLoadFile(core, argv[1])) {
        battle_core_die("Species runtime core/ROM initialization failed");
    }
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    run_trace_prefix(core);

    unsigned named = 0;
    unsigned with_moves = 0;
    for (unsigned species = 1; species < SPECIES_RUNTIME_COUNT; ++species) {
        clear_parties(core);
        seed_fixture(core);
        create_mon(core, ADDR_PLAYER_PARTY, (uint16_t)species, 5);

        bool has_move = false;
        for (unsigned slot = 0; slot < BATTLE_CORE_MOVE_SLOTS; ++slot) {
            uint32_t move = call_preserving(
                core, BATTLE_CORE_GET_MON_DATA, ADDR_PLAYER_PARTY,
                MON_DATA_MOVE1 + slot, 0, 0);
            if (move > BATTLE_CORE_CANONICAL_MOVE_MAX) {
                battle_core_die("created Species has a move outside canonical ABI");
            }
            has_move |= move != 0;
        }
        with_moves += has_move;

        for (unsigned index = 0; index < NAME_LENGTH; ++index) {
            write8(core, NAME_SCRATCH + index, 0);
        }
        (void)call_preserving(core, GET_SPECIES_NAME,
                              NAME_SCRATCH, species, 0, 0);
        bool terminated = false;
        for (unsigned index = 0; index < NAME_LENGTH; ++index) {
            if (read8(core, NAME_SCRATCH + index) == 0xFFU) {
                terminated = true;
                break;
            }
        }
        if (!terminated || read8(core, NAME_SCRATCH) == 0xFFU) {
            battle_core_die("canonical Species name is blank or unterminated");
        }
        ++named;
    }
    printf(
        "{\"status\":\"PASS\",\"species_created\":%u,"
        "\"species_named\":%u,\"species_with_level5_moves\":%u,"
        "\"canonical_species_count\":%u}\n",
        SPECIES_RUNTIME_COUNT - 1, named, with_moves, SPECIES_RUNTIME_COUNT
    );
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
