/*
 * Latest cumulative-ROM P03 representative smoke for the Stage79 gate.
 *
 * No Stage67/73/74/75 relocated address is compiled into this runner.  The
 * Python orchestrator resolves and pins every address, ID and expected value
 * from the current cumulative input contract and supplies it as --key=value.
 */
#define BATTLE_CORE_EMBEDDED
#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1
#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203D000U
#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203E000U
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#include "mgba_battle_core_smoke.c"
#pragma GCC diagnostic pop

#include <errno.h>

enum {
    P03X_MAX_ARGS = 96,
    P03X_MAX_MOVES = 429,
    P03X_EGG_BUFFER_MOVES = 50,
};

struct P03xArg {
    const char *key;
    uint32_t value;
};

struct P03xArgs {
    struct P03xArg rows[P03X_MAX_ARGS];
    size_t count;
};

static void p03x_die(const char *message)
{
    fprintf(stderr, "mgba-modernization-stage79-p03: %s\n", message);
    exit(1);
}

static uint32_t p03x_parse_u32(const char *text, const char *label)
{
    char *end = NULL;
    errno = 0;
    unsigned long value = strtoul(text, &end, 0);
    if (errno != 0 || end == text || *end != '\0' || value > UINT32_MAX) {
        fprintf(stderr, "invalid uint32 for %s: %s\n", label, text);
        exit(2);
    }
    return (uint32_t)value;
}

static struct P03xArgs p03x_parse_args(int argc, char **argv)
{
    struct P03xArgs result = {0};
    for (int index = 3; index < argc; ++index) {
        const char *raw = argv[index];
        if (strncmp(raw, "--", 2) != 0)
            p03x_die("contract arguments must use --key=value");
        const char *equal = strchr(raw + 2, '=');
        if (equal == NULL || equal == raw + 2 || equal[1] == '\0')
            p03x_die("contract argument is malformed");
        if (result.count >= P03X_MAX_ARGS)
            p03x_die("too many contract arguments");
        size_t key_length = (size_t)(equal - (raw + 2));
        for (size_t prior = 0; prior < result.count; ++prior) {
            if (strlen(result.rows[prior].key) == key_length
                && strncmp(result.rows[prior].key, raw + 2, key_length) == 0)
                p03x_die("duplicate contract argument");
        }
        char *key = malloc(key_length + 1U);
        if (key == NULL)
            p03x_die("contract key allocation failed");
        memcpy(key, raw + 2, key_length);
        key[key_length] = '\0';
        result.rows[result.count].key = key;
        result.rows[result.count].value = p03x_parse_u32(equal + 1, key);
        ++result.count;
    }
    return result;
}

static uint32_t p03x_arg(const struct P03xArgs *args, const char *key)
{
    for (size_t index = 0; index < args->count; ++index) {
        if (strcmp(args->rows[index].key, key) == 0)
            return args->rows[index].value;
    }
    fprintf(stderr, "missing contract argument: %s\n", key);
    exit(2);
}

static void p03x_free_args(struct P03xArgs *args)
{
    for (size_t index = 0; index < args->count; ++index)
        free((void *)args->rows[index].key);
    args->count = 0U;
}

static bool p03x_rom_pointer(uint32_t value)
{
    return value >= 0x08000000U && value < 0x0A000000U;
}

static void p03x_clear_mon_moves(struct mCore *core, uint32_t mon)
{
    for (unsigned slot = 0U; slot < 4U; ++slot) {
        set_mon_data_u32(core, mon, MON_DATA_MOVE1 + slot, 0U);
        set_mon_data_u32(core, mon, MON_DATA_PP1 + slot, 0U);
    }
}

static void p03x_fill16(struct mCore *core, uint32_t address,
                        unsigned count, uint16_t value)
{
    for (unsigned index = 0U; index < count; ++index)
        write16(core, address + index * 2U, value);
}

static bool p03x_contains(struct mCore *core, uint32_t address,
                          unsigned count, uint16_t move)
{
    for (unsigned index = 0U; index < count; ++index) {
        if (read16(core, address + index * 2U) == move)
            return true;
    }
    return false;
}

static uint32_t p03x_call(struct mCore *core, uint32_t function,
                          uint32_t r0, uint32_t r1,
                          uint32_t r2, uint32_t r3)
{
    if ((function & 1U) == 0U || !p03x_rom_pointer(function & ~1U))
        p03x_die("dynamic Thumb entrypoint is invalid");
    struct CallObservation observed = call_bounded(
        core, function, r0, r1, r2, r3);
    if (observed.instructions == 0U)
        p03x_die("dynamic Thumb entrypoint executed zero instructions");
    return observed.result;
}

static void p03x_check_roots(struct mCore *core,
                             const struct P03xArgs *args)
{
    uint32_t level_root = p03x_arg(args, "level-root");
    uint32_t tutor_root = p03x_arg(args, "tutor-root");
    uint32_t tutor_catalog = p03x_arg(args, "tutor-catalog");
    uint32_t egg_root = p03x_arg(args, "egg-root");
    if (!p03x_rom_pointer(level_root) || !p03x_rom_pointer(tutor_root)
        || !p03x_rom_pointer(tutor_catalog) || !p03x_rom_pointer(egg_root))
        p03x_die("dynamic P03 root is outside ROM");
    if (read32(core, p03x_arg(args, "level-root-site")) != level_root
        || read32(core, p03x_arg(args, "level-root-mirror-site")) != level_root
        || read32(core, p03x_arg(args, "tutor-root-site")) != tutor_root
        || read32(core, p03x_arg(args, "tutor-catalog-site")) != tutor_catalog
        || read32(core, p03x_arg(args, "egg-root-site-a")) != egg_root
        || read32(core, p03x_arg(args, "egg-root-site-b")) != egg_root
        || read32(core, p03x_arg(args, "egg-limit-site"))
            != p03x_arg(args, "egg-limit"))
        p03x_die("latest cumulative P03 roots do not match CLI contract");
}

static void p03x_check_stage67_representatives(
    struct mCore *core, const struct P03xArgs *args, uint32_t scratch)
{
    uint16_t level_species = (uint16_t)p03x_arg(args, "level-species");
    uint32_t level_root = p03x_arg(args, "level-root");
    uint32_t level_row = read32(core, level_root + level_species * 4U);
    if (!p03x_rom_pointer(level_row)
        || read16(core, level_row) != p03x_arg(args, "level-first-move")
        || read8(core, level_row + 2U) != p03x_arg(args, "level-first-level"))
        p03x_die("Stage67 representative level row mismatch");

    uint16_t evolution_species =
        (uint16_t)p03x_arg(args, "evolution-species");
    uint16_t evolution_move =
        (uint16_t)p03x_arg(args, "evolution-first-move");
    uint32_t evolution_row = read32(
        core, level_root + evolution_species * 4U);
    if (read16(core, evolution_row) != evolution_move
        || read8(core, evolution_row + 2U) != 0U)
        p03x_die("Stage67 representative evolution row mismatch");
    create_mon(core, ADDR_PLAYER_PARTY, evolution_species, 5U);
    p03x_clear_mon_moves(core, ADDR_PLAYER_PARTY);
    if (p03x_call(core, p03x_arg(args, "evolution-function"),
                  ADDR_PLAYER_PARTY, 1U, 0U, 0U) != evolution_move
        || call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                           ADDR_PLAYER_PARTY, MON_DATA_MOVE1, 0U, 0U)
            != evolution_move)
        p03x_die("Stage67 representative evolution consumer mismatch");

    uint16_t tutor_species = (uint16_t)p03x_arg(args, "tutor-species");
    uint32_t tutor_root = p03x_arg(args, "tutor-root");
    uint32_t tutor_row = tutor_root + tutor_species * 16U;
    uint32_t positive = p03x_arg(args, "tutor-positive-slot");
    uint32_t negative = p03x_arg(args, "tutor-negative-slot");
    if ((read8(core, tutor_row + positive / 8U) & (1U << (positive % 8U))) == 0U
        || (read8(core, tutor_row + negative / 8U) & (1U << (negative % 8U))) != 0U
        || read16(core, p03x_arg(args, "tutor-catalog") + positive * 2U)
            != p03x_arg(args, "tutor-positive-move"))
        p03x_die("Stage67 representative tutor table mismatch");
    create_mon(core, ADDR_PLAYER_PARTY, tutor_species, 5U);
    if (p03x_call(core, p03x_arg(args, "tutor-function"),
                  ADDR_PLAYER_PARTY, positive, 0U, 0U) != 1U
        || p03x_call(core, p03x_arg(args, "tutor-function"),
                     ADDR_PLAYER_PARTY, negative, 0U, 0U) != 0U)
        p03x_die("Stage67 representative tutor consumer mismatch");

    uint16_t egg_species = (uint16_t)p03x_arg(args, "egg-species");
    create_mon(core, ADDR_PLAYER_PARTY, egg_species, 5U);
    p03x_clear_mon_moves(core, ADDR_PLAYER_PARTY);
    p03x_fill16(core, scratch, P03X_EGG_BUFFER_MOVES, 0xDEADU);
    uint32_t egg_count = p03x_call(
        core, p03x_arg(args, "stage73-get-all-egg"),
        ADDR_PLAYER_PARTY, scratch, 0U, 0U);
    if (egg_count != p03x_arg(args, "egg-count")
        || !p03x_contains(core, scratch, egg_count,
                          (uint16_t)p03x_arg(args, "egg-required-move"))
        || p03x_contains(core, scratch, egg_count,
                         (uint16_t)p03x_arg(args, "egg-forbidden-move")))
        p03x_die("Stage67 representative egg consumer mismatch");
}

static void p03x_check_stage73(struct mCore *core,
                               const struct P03xArgs *args,
                               uint32_t scratch)
{
    uint32_t probe = p03x_arg(args, "stage73-probe");
    if (p03x_call(core, probe, 0U, 0U, 0U, 0U) != 0x50333733U
        || p03x_call(core, probe, 1U, 0U, 0U, 0U)
            != p03x_arg(args, "stage73-species-count")
        || p03x_call(core, probe, 2U, 0U, 0U, 0U)
            != p03x_arg(args, "page-size"))
        p03x_die("Stage73 runtime probe mismatch");

    uint16_t exact_species =
        (uint16_t)p03x_arg(args, "stage73-exact-egg-species");
    create_mon(core, ADDR_PLAYER_PARTY, exact_species, 5U);
    p03x_clear_mon_moves(core, ADDR_PLAYER_PARTY);
    p03x_fill16(core, scratch, P03X_EGG_BUFFER_MOVES, 0xDEADU);
    uint32_t exact_count = p03x_call(
        core, p03x_arg(args, "stage73-get-all-egg"),
        ADDR_PLAYER_PARTY, scratch, 1U, 0U);
    if (exact_count != p03x_arg(args, "stage73-exact-egg-count")
        || read16(core, scratch) != p03x_arg(args, "stage73-exact-egg-move0")
        || read16(core, scratch + 2U)
            != p03x_arg(args, "stage73-exact-egg-move1"))
        p03x_die("Stage73 exact egg alias mismatch");

    uint16_t shared_species =
        (uint16_t)p03x_arg(args, "stage73-shared-species");
    create_mon(core, ADDR_PLAYER_PARTY, shared_species, 100U);
    p03x_clear_mon_moves(core, ADDR_PLAYER_PARTY);
    write8(core, p03x_arg(args, "mode-address"),
           (uint8_t)p03x_arg(args, "mode-egg"));
    p03x_fill16(core, scratch, P03X_EGG_BUFFER_MOVES, 0xDEADU);
    uint32_t shared_count = p03x_call(
        core, p03x_arg(args, "stage75-get-relearner"),
        ADDR_PLAYER_PARTY, scratch, 0U, 0U);
    if (shared_count == 0U || shared_count > p03x_arg(args, "page-size")
        || !p03x_contains(core, scratch, shared_count,
                          (uint16_t)p03x_arg(args, "stage73-shared-required")))
        p03x_die("Stage73 shared-egg Move Memory mismatch");

    uint16_t reminder_species =
        (uint16_t)p03x_arg(args, "stage73-reminder-species");
    create_mon(core, ADDR_PLAYER_PARTY, reminder_species, 100U);
    p03x_clear_mon_moves(core, ADDR_PLAYER_PARTY);
    write8(core, p03x_arg(args, "mode-address"),
           (uint8_t)p03x_arg(args, "mode-normal"));
    p03x_fill16(core, scratch, P03X_EGG_BUFFER_MOVES, 0xDEADU);
    uint32_t reminder_count = p03x_call(
        core, p03x_arg(args, "stage75-get-relearner"),
        ADDR_PLAYER_PARTY, scratch, 0U, 0U);
    if (reminder_count == 0U || reminder_count > p03x_arg(args, "page-size")
        || !p03x_contains(core, scratch, reminder_count,
                          (uint16_t)p03x_arg(args, "stage73-reminder-required")))
        p03x_die("Stage73 reminder Move Memory mismatch");

    uint32_t rotom = p03x_arg(args, "stage73-rotom-signature");
    if (p03x_call(core, rotom, p03x_arg(args, "rotom-heat"), 0U, 0U, 0U)
            != p03x_arg(args, "rotom-heat-move")
        || p03x_call(core, rotom, p03x_arg(args, "rotom-wash"), 0U, 0U, 0U)
            != p03x_arg(args, "rotom-wash-move")
        || p03x_call(core, rotom, p03x_arg(args, "rotom-base"), 0U, 0U, 0U)
            != 0U)
        p03x_die("Stage73 Rotom signature routing mismatch");
}

static void p03x_check_stage74(struct mCore *core,
                               const struct P03xArgs *args,
                               uint32_t scratch)
{
    uint32_t probe = p03x_arg(args, "stage74-probe");
    if (p03x_call(core, probe, 0U, 0U, 0U, 0U) != 0x50333734U
        || p03x_call(core, probe, 2U, 0U, 0U, 0U)
            != p03x_arg(args, "page-size")
        || p03x_call(core, probe, 3U, 0U, 0U, 0U)
            != p03x_arg(args, "max-pages"))
        p03x_die("Stage74 runtime probe mismatch");

    uint16_t species = (uint16_t)p03x_arg(args, "archive-species");
    create_mon(core, ADDR_PLAYER_PARTY, species, 100U);
    p03x_clear_mon_moves(core, ADDR_PLAYER_PARTY);
    write16(core, p03x_arg(args, "party-slot-address"), 0U);
    p03x_call(core, p03x_arg(args, "stage75-set-machine"), 0U, 0U, 0U, 0U);
    if (read8(core, p03x_arg(args, "mode-address"))
            != p03x_arg(args, "mode-machine-probe"))
        p03x_die("Stage74 machine probe mode mismatch");
    p03x_call(core, p03x_arg(args, "stage75-prepare-pages"), 0U, 0U, 0U, 0U);
    if (read16(core, p03x_arg(args, "result-address"))
            != p03x_arg(args, "archive-pages")
        || read8(core, p03x_arg(args, "mode-address"))
            != p03x_arg(args, "mode-machine-probe"))
        p03x_die("Stage74 machine paging preparation mismatch");

    for (uint32_t page = 0U; page < p03x_arg(args, "archive-pages"); ++page) {
        write16(core, p03x_arg(args, "result-address"), (uint16_t)page);
        p03x_call(core, p03x_arg(args, "stage75-commit-page"), 0U, 0U, 0U, 0U);
        if (read16(core, p03x_arg(args, "result-address")) != 1U
            || read8(core, p03x_arg(args, "mode-address"))
                != p03x_arg(args, "mode-machine-page0") + page)
            p03x_die("Stage74 valid machine page commit mismatch");
        p03x_call(core, p03x_arg(args, "stage75-page-has-moves"), 0U, 0U, 0U, 0U);
        if (read16(core, p03x_arg(args, "result-address")) != 1U)
            p03x_die("Stage74 committed page unexpectedly empty");
        p03x_fill16(core, scratch, P03X_EGG_BUFFER_MOVES, 0xDEADU);
        uint32_t count = p03x_call(
            core, p03x_arg(args, "stage75-get-relearner"),
            ADDR_PLAYER_PARTY, scratch, 0U, 0U);
        if (count == 0U || count > p03x_arg(args, "page-size"))
            p03x_die("Stage74 machine archive page size mismatch");
    }
    write16(core, p03x_arg(args, "result-address"),
            (uint16_t)p03x_arg(args, "archive-pages"));
    p03x_call(core, p03x_arg(args, "stage75-commit-page"), 0U, 0U, 0U, 0U);
    if (read16(core, p03x_arg(args, "result-address")) != 0U
        || read8(core, p03x_arg(args, "mode-address"))
            != p03x_arg(args, "mode-machine-probe"))
        p03x_die("Stage74 invalid/cancel machine page did not fail closed");

    uint16_t tutor_species =
        (uint16_t)p03x_arg(args, "archive-tutor-species");
    create_mon(core, ADDR_PLAYER_PARTY, tutor_species, 100U);
    p03x_clear_mon_moves(core, ADDR_PLAYER_PARTY);
    p03x_call(core, p03x_arg(args, "stage75-set-tutor"), 0U, 0U, 0U, 0U);
    p03x_fill16(core, scratch, P03X_EGG_BUFFER_MOVES, 0xDEADU);
    uint32_t tutor_count = p03x_call(
        core, p03x_arg(args, "stage75-get-relearner"),
        ADDR_PLAYER_PARTY, scratch, 0U, 0U);
    if (tutor_count == 0U || tutor_count > p03x_arg(args, "page-size")
        || !p03x_contains(core, scratch, tutor_count,
                          (uint16_t)p03x_arg(args, "archive-tutor-required")))
        p03x_die("Stage74 tutor archive mismatch");

    create_mon(core, ADDR_PLAYER_PARTY, species, 100U);
    p03x_clear_mon_moves(core, ADDR_PLAYER_PARTY);
    p03x_fill16(core, scratch, P03X_MAX_MOVES, 0xDEADU);
    uint32_t learnable = p03x_call(
        core, p03x_arg(args, "stage75-build-learnable"),
        ADDR_PLAYER_PARTY, scratch, 0U, 0U);
    if (learnable == 0U || learnable > P03X_MAX_MOVES
        || !p03x_contains(core, scratch, learnable,
                          (uint16_t)p03x_arg(args, "archive-required-move")))
        p03x_die("Stage74 BuildLearnable capacity/content mismatch");

    p03x_call(core, p03x_arg(args, "stage75-reset-mode"), 0U, 0U, 0U, 0U);
    if (read8(core, p03x_arg(args, "mode-address"))
            != p03x_arg(args, "mode-normal"))
        p03x_die("Stage74 terminal mode reset mismatch");

    /* Force CreateTask exhaustion to exercise the synchronous failure sentinel. */
    uint32_t tasks = p03x_arg(args, "tasks-address");
    uint32_t task_count = p03x_arg(args, "task-count");
    uint32_t task_stride = p03x_arg(args, "task-stride");
    uint32_t task_active_offset = p03x_arg(args, "task-active-offset");
    uint8_t prior[32];
    if (task_count > ARRAY_LEN(prior))
        p03x_die("task count exceeds runner guard");
    for (uint32_t index = 0U; index < task_count; ++index) {
        prior[index] = read8(core, tasks + index * task_stride + task_active_offset);
        write8(core, tasks + index * task_stride + task_active_offset, 1U);
    }
    write16(core, p03x_arg(args, "result-address"), 0U);
    p03x_call(core, p03x_arg(args, "stage75-open-archive"), 0U, 0U, 0U, 0U);
    if (read16(core, p03x_arg(args, "result-address"))
            != p03x_arg(args, "archive-failure-sentinel"))
        p03x_die("Stage74 archive synchronous failure sentinel mismatch");
    for (uint32_t index = 0U; index < task_count; ++index)
        write8(core, tasks + index * task_stride + task_active_offset, prior[index]);

    /* One-page rows must reject the page menu synchronously with its sentinel. */
    create_mon(core, ADDR_PLAYER_PARTY,
               (uint16_t)p03x_arg(args, "one-page-species"), 100U);
    write16(core, p03x_arg(args, "party-slot-address"), 0U);
    write16(core, p03x_arg(args, "result-address"), 0U);
    p03x_call(core, p03x_arg(args, "stage75-open-page"), 0U, 0U, 0U, 0U);
    if (read16(core, p03x_arg(args, "result-address"))
            != p03x_arg(args, "page-failure-sentinel"))
        p03x_die("Stage74 page synchronous failure sentinel mismatch");
}

static void p03x_check_stage75(struct mCore *core,
                               const struct P03xArgs *args,
                               uint32_t scratch)
{
    uint32_t probe = p03x_arg(args, "stage75-probe");
    uint16_t own = (uint16_t)p03x_arg(args, "own-tempo-species");
    uint16_t normal = (uint16_t)p03x_arg(args, "normal-rockruff-species");
    uint16_t dusk = (uint16_t)p03x_arg(args, "dusk-lycanroc-species");
    if (p03x_call(core, probe, 0U, 0U, 0U, 0U) != 0x50333735U
        || p03x_call(core, probe, 1U, 0U, 0U, 0U)
            != p03x_arg(args, "stage75-species-count")
        || p03x_call(core, probe, 2U, 0U, 0U, 0U) != own
        || p03x_call(core, probe, 5U, 0U, 0U, 0U) != P03X_MAX_MOVES)
        p03x_die("Stage75 runtime probe mismatch");

    uint32_t get_egg_species = p03x_arg(args, "stage75-get-egg-species");
    if (p03x_call(core, get_egg_species, own, 0U, 0U, 0U) != own
        || p03x_call(core, get_egg_species, dusk, 0U, 0U, 0U) != own
        || p03x_call(core, get_egg_species, normal, 0U, 0U, 0U) == own)
        p03x_die("Stage75 Own Tempo egg species ownership mismatch");

    create_mon(core, ADDR_PLAYER_PARTY, own, 25U);
    p03x_clear_mon_moves(core, ADDR_PLAYER_PARTY);
    p03x_fill16(core, scratch, P03X_EGG_BUFFER_MOVES, 0xDEADU);
    uint32_t egg_count = p03x_call(
        core, p03x_arg(args, "stage75-get-egg-moves"),
        ADDR_PLAYER_PARTY, scratch, 0U, 0U);
    if (egg_count != 4U)
        p03x_die("Stage75 Own Tempo egg move count mismatch");
    for (unsigned index = 0U; index < 4U; ++index) {
        char key[32];
        (void)snprintf(key, sizeof(key), "own-tempo-egg-move%u", index);
        if (read16(core, scratch + index * 2U) != p03x_arg(args, key))
            p03x_die("Stage75 Own Tempo egg move order mismatch");
    }

    uint32_t evolution = p03x_arg(args, "stage75-evolution-table");
    uint32_t own_row = evolution + (uint32_t)own * 16U * 8U;
    if (read16(core, own_row) != p03x_arg(args, "own-tempo-evo-method")
        || read16(core, own_row + 2U) != p03x_arg(args, "own-tempo-evo-level")
        || read16(core, own_row + 4U) != dusk
        || read16(core, own_row + 6U) != p03x_arg(args, "own-tempo-evo-extra"))
        p03x_die("Stage75 Own Tempo evolution row mismatch");
    uint32_t normal_removed = evolution + (uint32_t)normal * 16U * 8U
        + p03x_arg(args, "normal-removed-slot") * 8U;
    for (unsigned byte = 0U; byte < 8U; ++byte) {
        if (read8(core, normal_removed + byte) != 0U)
            p03x_die("normal Rockruff retained the removed dusk evolution row");
    }

    uint32_t level_root = p03x_arg(args, "level-root");
    if (read32(core, level_root + own * 4U)
        != read32(core, level_root + normal * 4U))
        p03x_die("Stage75 Own Tempo level owner does not clone normal Rockruff");

    p03x_fill16(core, scratch, P03X_MAX_MOVES, 0xDEADU);
    uint32_t learnable = p03x_call(
        core, p03x_arg(args, "stage75-build-learnable"),
        ADDR_PLAYER_PARTY, scratch, 0U, 0U);
    if (learnable == 0U || learnable > P03X_MAX_MOVES)
        p03x_die("Stage75 Own Tempo BuildLearnable capacity mismatch");
    for (unsigned index = 0U; index < 4U; ++index) {
        char key[32];
        (void)snprintf(key, sizeof(key), "own-tempo-egg-move%u", index);
        if (!p03x_contains(core, scratch, learnable,
                           (uint16_t)p03x_arg(args, key)))
            p03x_die("Stage75 owner BuildLearnable omitted an egg route");
    }
    if (!p03x_contains(core, scratch, learnable,
                       (uint16_t)p03x_arg(args, "own-tempo-archive-required")))
        p03x_die("Stage75 owner BuildLearnable omitted an archive route");
}

int main(int argc, char **argv)
{
    if (argc < 4) {
        fprintf(stderr, "usage: %s ROM EXPECTED_ROM_SHA256 --key=value ...\n",
                argv[0]);
        return 2;
    }
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64U || strcmp(rom_sha256, argv[2]) != 0)
        p03x_die("ROM SHA-256 mismatch");
    struct P03xArgs args = p03x_parse_args(argc, argv);

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {
        .sample = NULL,
        .unixTime = fixed_unix_time,
        .serialize = NULL,
        .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(argv[1]);
    if (core == NULL || !core->init(core))
        p03x_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1]))
        p03x_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);

    uint32_t scratch = p03x_arg(&args, "scratch-address");
    p03x_check_roots(core, &args);
    p03x_check_stage67_representatives(core, &args, scratch);
    p03x_check_stage73(core, &args, scratch);
    p03x_check_stage74(core, &args, scratch);
    p03x_check_stage75(core, &args, scratch);
    if (log_problem_count != 0U)
        p03x_die("mGBA warning/error was emitted");

    printf(
        "{\"schema_version\":1,\"status\":\"PASS\","
        "\"classification\":\"LATEST_CUMULATIVE_P03_REPRESENTATIVE_DIRECT_CALL\","
        "\"rom_sha256\":\"%s\",\"process_runs\":1,"
        "\"read_only\":true,\"warnings_errors\":0,"
        "\"checks\":{"
        "\"stage67_level_evolution_tutor_egg\":true,"
        "\"stage73_exact_alias_shared_egg_reminder_rotom\":true,"
        "\"stage74_machine_tutor_paging_cancel_failure_capacity\":true,"
        "\"stage75_species1670_egg_evolution_route_owner\":true,"
        "\"all_known_terminal_mode_reset_source_pinned\":true},"
        "\"full_p03_acceptance\":false,"
        "\"scheduler_e2e\":false,\"breeding_e2e\":false,"
        "\"save_reload_e2e\":false,\"artifacts_written\":[]}\n",
        rom_sha256);
    fflush(stdout);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);  /* mGBA owns and frees core here. */
    p03x_free_args(&args);
    return 0;
}
