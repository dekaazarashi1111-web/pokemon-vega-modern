/* Stage50 exact-ROM smoke for interaction ownership, encounter cadence,
 * flinch probability, trainer binding, and Focus Sash regressions. */
#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <inttypes.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <mgba/core/config.h>
#include <mgba/core/core.h>
#include <mgba/core/log.h>

#define ROM_BASE UINT32_C(0x08000000)
#define ROM_END UINT32_C(0x0A000000)
#define MAP_ROOT_SITE UINT32_C(0x08054B0C)
#define WILD_ROOT_SITE UINT32_C(0x0808257C)
#define COOLDOWN_BRANCH UINT32_C(0x08082F76)
#define DARK_PULSE_ROW UINT32_C(0x09043340)
#define FLINCH_CHANCE_COMPARE UINT32_C(0x0912B910)
#define RANDOM_FUNCTION UINT32_C(0x0804448D)
#define PLAYER_AVATAR UINT32_C(0x02036FAC)
#define ITEM_TABLE UINT32_C(0x0904D108)
#define ITEM_STRIDE 40U
#define FOCUS_SASH 897U
#define G_BATTLE_MONS UINT32_C(0x02023B44)
#define G_NEW_BATTLE_STRUCT UINT32_C(0x0203DFB0)
#define NEW_BATTLE_STRUCT_SCRATCH UINT32_C(0x02010000)
#define IS_AFFECTED_BY_FOCUS_SASH UINT32_C(0x090D5C25)
#define IS_HOLDING_FOCUS_SASH UINT32_C(0x090D5B51)
#define ITEM_GET_HOLD_EFFECT UINT32_C(0x0910FDD1)
#define ITEM_GET_MYSTERY2 UINT32_C(0x0809A3C5)
#define REMOVE_ITEM_COMMAND UINT32_C(0x09107FF5)
#define G_ACTIVE_BATTLER UINT32_C(0x02023B24)
#define G_BATTLE_EXEC_BUFFER UINT32_C(0x02023B28)
#define G_BANK_TARGET UINT32_C(0x02023CCC)
#define G_BATTLE_SCRIPT_CURSOR UINT32_C(0x02023CD4)
#define BATTLE_SCRIPT_SCRATCH UINT32_C(0x02015000)
#define GBA_WIDTH 240U
#define GBA_HEIGHT 160U
#define MAX_CALL_STEPS UINT64_C(2000000)

static void die(const char *message)
{
    fprintf(stderr, "mgba-interaction-ownership: %s\n", message);
    exit(1);
}

static void silent_log(struct mLogger *logger, int category,
                       enum mLogLevel level, const char *format, va_list args)
{
    (void)logger; (void)category; (void)level; (void)format; (void)args;
}

static uint32_t parse_u32(const char *text, const char *label)
{
    errno = 0;
    char *end = NULL;
    unsigned long value = strtoul(text, &end, 0);
    if (errno || end == NULL || *end != '\0' || value > UINT32_MAX) {
        fprintf(stderr, "mgba-interaction-ownership: invalid %s\n", label);
        exit(2);
    }
    return (uint32_t)value;
}

static uint8_t read8(struct mCore *core, uint32_t address)
{
    return (uint8_t)core->rawRead8(core, address, -1);
}

static uint16_t read16(struct mCore *core, uint32_t address)
{
    return (uint16_t)core->rawRead16(core, address, -1);
}

static uint16_t read16u(struct mCore *core, uint32_t address)
{
    return (uint16_t)(read8(core, address)
        | ((uint16_t)read8(core, address + 1U) << 8U));
}

static uint32_t read32(struct mCore *core, uint32_t address)
{
    return core->rawRead32(core, address, -1);
}

static void write8(struct mCore *core, uint32_t address, uint8_t value)
{
    core->rawWrite8(core, address, -1, value);
}

static void write16(struct mCore *core, uint32_t address, uint16_t value)
{
    core->rawWrite16(core, address, -1, value);
}

static void write32(struct mCore *core, uint32_t address, uint32_t value)
{
    core->rawWrite32(core, address, -1, value);
}

static bool rom_pointer(uint32_t pointer)
{
    pointer &= ~1U;
    return pointer >= ROM_BASE && pointer < ROM_END;
}

static int32_t reg_read(struct mCore *core, const char *name)
{
    int32_t value = 0;
    if (!core->readRegister(core, name, &value))
        die("register read failed");
    return value;
}

static void reg_write(struct mCore *core, const char *name, int32_t value)
{
    if (!core->writeRegister(core, name, &value))
        die("register write failed");
}

static const char *const REGS[] = {
    "r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8",
    "r9", "r10", "r11", "r12", "sp", "lr", "pc", "cpsr",
};

static uint32_t call_thumb(struct mCore *core, uint32_t function, uint32_t r0)
{
    int32_t saved[17];
    for (size_t index = 0; index < 17; ++index)
        saved[index] = reg_read(core, REGS[index]);
    reg_write(core, "cpsr", saved[16] | 0xA0);
    reg_write(core, "lr", (int32_t)UINT32_C(0x08000001));
    reg_write(core, "r0", (int32_t)r0);
    reg_write(core, "pc", (int32_t)function);
    uint64_t steps = 0;
    while ((((uint32_t)reg_read(core, "pc")) & ~1U) != UINT32_C(0x08000002)) {
        if (++steps > MAX_CALL_STEPS)
            die("Thumb call instruction limit");
        core->step(core);
    }
    uint32_t result = (uint32_t)reg_read(core, "r0");
    reg_write(core, "cpsr", saved[16]);
    for (size_t index = 0; index < 15; ++index)
        reg_write(core, REGS[index], saved[index]);
    reg_write(core, "pc", saved[15]);
    return result;
}

static uint32_t map_events(struct mCore *core, uint32_t root,
                           uint8_t group, uint8_t map)
{
    uint32_t group_table = read32(core, root + (uint32_t)group * 4U);
    uint32_t header = read32(core, group_table + (uint32_t)map * 4U);
    uint32_t events = read32(core, header + 4U);
    if (!rom_pointer(group_table) || !rom_pointer(header) || !rom_pointer(events))
        die("map event pointer graph invalid");
    return events;
}

static void check_hisui(struct mCore *core, uint32_t root, uint32_t script)
{
    uint32_t events = map_events(core, root, 3U, 5U);
    uint8_t count = read8(core, events);
    uint32_t objects = read32(core, events + 4U);
    bool found = false;
    for (uint32_t index = 0; index < count; ++index) {
        uint32_t row = objects + index * 0x18U;
        if (read8(core, row) == 4U) {
            if (read8(core, row + 1U) != 72U || read16(core, row + 4U) != 4U
                || read16(core, row + 6U) != 21U || read32(core, row + 16U) != script)
                die("Hisui local object 4 binding differs");
            found = true;
        }
    }
    if (!found)
        die("Hisui local object 4 missing");
}

static void check_codex_reception(struct mCore *core, uint32_t root)
{
    uint32_t events = map_events(core, root, 96U, 5U);
    uint8_t count = read8(core, events);
    uint32_t objects = read32(core, events + 4U);
    for (uint32_t index = 0; index < count; ++index) {
        uint32_t row = objects + index * 0x18U;
        if (read8(core, row) == 2U) {
            if (read8(core, row + 1U) != 62U || read16(core, row + 4U) != 20U
                || read16(core, row + 6U) != 19U
                || read32(core, row + 16U) != UINT32_C(0x093CDA80))
                die("Codex reception binding differs");
            return;
        }
    }
    die("Codex reception local object 2 missing");
}

static void check_511_wild(struct mCore *core)
{
    uint32_t root = read32(core, WILD_ROOT_SITE);
    if (!rom_pointer(root))
        die("wild header root invalid");
    uint32_t land = 0;
    for (uint32_t index = 0; index < 265U; ++index) {
        uint32_t row = root + index * 20U;
        if (read8(core, row) == 3U && read8(core, row + 1U) == 29U)
            land = read32(core, row + 4U);
    }
    if (!rom_pointer(land) || read8(core, land) != 21U)
        die("511 waterway land encounter owner missing");
    uint32_t slots = read32(core, land + 4U);
    if (!rom_pointer(slots))
        die("511 waterway land slots missing");
    for (uint32_t index = 0; index < 12U; ++index) {
        uint8_t low = read8(core, slots + index * 4U);
        uint8_t high = read8(core, slots + index * 4U + 1U);
        uint16_t species = read16u(core, slots + index * 4U + 2U);
        if (low < 25U || high > 31U || low > high || species == 0U)
            die("511 waterway land slot invalid");
    }
}

static uint32_t check_flinch_rng(struct mCore *core)
{
    if (read8(core, DARK_PULSE_ROW) != 31U || read8(core, DARK_PULSE_ROW + 5U) != 20U)
        die("Dark Pulse effect/chance differs");
    if (read16(core, FLINCH_CHANCE_COMPARE) != 0x4551U
        || read16(core, FLINCH_CHANCE_COMPARE + 2U) != 0xD2D3U)
        die("secondary effect strict-less-than branch differs");
    uint32_t hits = 0;
    for (uint32_t index = 0; index < 4096U; ++index)
        hits += (call_thumb(core, RANDOM_FUNCTION, 0U) & UINT32_C(0xFFFF)) % 100U < 20U;
    if (hits < 500U || hits > 1100U || hits == 4096U)
        die("Dark Pulse probability sample outside deterministic bounds");
    return hits;
}

static void check_focus_sash(struct mCore *core)
{
    uint32_t sash = ITEM_TABLE + FOCUS_SASH * ITEM_STRIDE;
    if (read16(core, sash + 10U) != FOCUS_SASH
        || read8(core, sash + 14U) != 39U || read8(core, sash + 15U) != 100U
        || read8(core, sash + 21U) != 1U || read8(core, sash + 36U) != 0U)
        die("Focus Sash 40-byte ABI differs");
    write16(core, G_BATTLE_MONS + 0x2EU, FOCUS_SASH);
    write16(core, G_BATTLE_MONS + 0x2CU, 100U);
    write16(core, G_BATTLE_MONS + 0x28U, 100U);
    if (call_thumb(core, ITEM_GET_HOLD_EFFECT, FOCUS_SASH) != 39U
        || call_thumb(core, ITEM_GET_MYSTERY2, FOCUS_SASH) != 1U)
        die("Focus Sash runtime accessor differs");
    for (uint32_t offset = 0; offset < UINT32_C(0x4000); offset += 4U)
        write32(core, NEW_BATTLE_STRUCT_SCRATCH + offset, 0U);
    write32(core, G_NEW_BATTLE_STRUCT, NEW_BATTLE_STRUCT_SCRATCH);
    if (call_thumb(core, IS_HOLDING_FOCUS_SASH, 0U) != 1U
        || call_thumb(core, IS_AFFECTED_BY_FOCUS_SASH, 0U) != 1U)
        die("Focus Sash full-HP predicate rejected");
    write16(core, G_BATTLE_MONS + 0x28U, 99U);
    if (call_thumb(core, IS_AFFECTED_BY_FOCUS_SASH, 0U) != 0U)
        die("Focus Sash non-full predicate accepted");
    write16(core, G_BATTLE_MONS + 0x28U, 100U);
    write8(core, G_ACTIVE_BATTLER, 0U);
    write32(core, G_BATTLE_EXEC_BUFFER, 0U);
    write8(core, G_BANK_TARGET, 0U);
    write8(core, BATTLE_SCRIPT_SCRATCH, 0x6AU);
    write8(core, BATTLE_SCRIPT_SCRATCH + 1U, 0U);
    write32(core, G_BATTLE_SCRIPT_CURSOR, BATTLE_SCRIPT_SCRATCH);
    (void)call_thumb(core, REMOVE_ITEM_COMMAND, 0U);
    if (read16(core, G_BATTLE_MONS + 0x2EU) != 0U
        || read32(core, G_BATTLE_SCRIPT_CURSOR) != BATTLE_SCRIPT_SCRATCH + 2U)
        die("Focus Sash removeitem path did not consume");
}

int main(int argc, char **argv)
{
    if (argc != 9 && argc != 10) {
        fprintf(stderr, "usage: %s ROM MAP_ROOT PAYLOAD_START PAYLOAD_END HISUI_SCRIPT WILD_WRAPPER TRAINER_ROOT SHINICHI_COMMAND [armv4t-tail]\n", argv[0]);
        return 2;
    }
    bool armv4t_tail = argc == 10 && strcmp(argv[9], "armv4t-tail") == 0;
    if (argc == 10 && !armv4t_tail)
        die("unknown wild-wrapper ABI");
    uint32_t map_root = parse_u32(argv[2], "map root");
    uint32_t payload_start = parse_u32(argv[3], "payload start");
    uint32_t payload_end = parse_u32(argv[4], "payload end");
    uint32_t hisui_script = parse_u32(argv[5], "Hisui script");
    uint32_t wild_wrapper = parse_u32(argv[6], "wild wrapper");
    uint32_t trainer_root = parse_u32(argv[7], "trainer root");
    uint32_t shinichi = parse_u32(argv[8], "Shinichi command");
    if (!rom_pointer(map_root) || !rom_pointer(payload_start)
        || payload_end <= payload_start || !rom_pointer(payload_end - 1U)
        || !rom_pointer(hisui_script) || !rom_pointer(wild_wrapper)
        || !rom_pointer(trainer_root) || !rom_pointer(shinichi))
        die("argument pointer contract failed");

    struct mLogger logger = {.log = silent_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = mCoreFind(argv[1]);
    if (core == NULL || !core->init(core) || !mCoreLoadFile(core, argv[1]))
        die("core/ROM initialization failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    color_t *video = calloc(GBA_WIDTH * GBA_HEIGHT, sizeof(*video));
    if (video == NULL)
        die("video allocation failed");
    core->setVideoBuffer(core, video, GBA_WIDTH);
    core->reset(core);
    uint32_t transitions = 0;
    color_t prior = 0;
    for (unsigned frame = 0; frame < 1800U; ++frame) {
        core->setKeys(core, 0);
        core->runFrame(core);
        color_t now = video[(frame * 977U) % (GBA_WIDTH * GBA_HEIGHT)];
        transitions += now != prior;
        prior = now;
    }
    if (transitions < 10U || read32(core, MAP_ROOT_SITE) != map_root)
        die("exact ROM boot/map root differs");

    check_hisui(core, map_root, hisui_script);
    check_codex_reception(core, map_root);
    check_511_wild(core);
    if (read16(core, COOLDOWN_BRANCH) != 0xE009U)
        die("minimum encounter grace branch differs");
    static const uint16_t legacy_wrapper[] = {
        0xB510U, 0x4904U, 0x7889U, 0x2902U, 0xD102U,
        0x4B03U, 0x4798U, 0xBD10U, 0x2000U, 0xBD10U,
    };
    static const uint16_t armv4t_wrapper[] = {
        0x4904U, 0x7889U, 0x2902U, 0xD101U, 0x4B03U,
        0x4718U, 0x2000U, 0x4770U, 0x46C0U, 0x46C0U,
    };
    const uint16_t *wrapper = armv4t_tail ? armv4t_wrapper : legacy_wrapper;
    size_t wrapper_count = sizeof(legacy_wrapper) / sizeof(legacy_wrapper[0]);
    uint32_t wrapper_address = wild_wrapper & ~1U;
    for (size_t index = 0; index < wrapper_count; ++index) {
        if (read16(core, wrapper_address + (uint32_t)index * 2U) != wrapper[index])
            die("moving-only wild wrapper ABI differs");
    }
    if (read32(core, wrapper_address + 20U) != PLAYER_AVATAR
        || read32(core, wrapper_address + 24U) != UINT32_C(0x08082F9D))
        die("moving-only wild wrapper target differs");
    write8(core, PLAYER_AVATAR + 2U, 1U);
    if (call_thumb(core, wild_wrapper, 0U) != 0U)
        die("turn-direction input was accepted as an encounter step");

    check_focus_sash(core);
    uint32_t flinch_hits = check_flinch_rng(core);
    uint32_t trainer = trainer_root + 299U * 32U;
    if (read8(core, trainer) != 3U || read8(core, trainer + 0x18U) != 5U
        || !rom_pointer(read32(core, trainer + 0x1CU))
        || read8(core, shinichi) != 0x5CU || read16u(core, shinichi + 2U) != 299U)
        die("Shinichi exact trainer binding differs");

    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"checks\":{\"boot\":true,\"hisui_npc\":true,"
           "\"codex_reception\":true,"
           "\"waterway_land\":true,\"turning_no_encounter\":true,"
           "%s"
           "\"minimum_grace\":true,\"dark_pulse_probability\":true,"
           "\"focus_sash\":true,\"trainer_binding\":true},"
           "\"framebuffer_transitions\":%" PRIu32 ","
           "\"flinch_hits_per_4096\":%" PRIu32 "}\n",
           armv4t_tail ? "\"armv4t_wild_wrapper\":true," : "",
           transitions, flinch_hits);
    free(video);
    core->deinit(core);
    return 0;
}
