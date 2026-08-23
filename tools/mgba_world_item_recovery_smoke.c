/* Stage49 smoke: boot the exact ROM, traverse the patched map-event graph,
 * inspect the low-Raid Thumb bridge, and audit trainer/item ABI bytes. */
#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <inttypes.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include <mgba/core/config.h>
#include <mgba/core/core.h>
#include <mgba/core/log.h>

#define ROM_BASE UINT32_C(0x08000000)
#define ROM_END UINT32_C(0x0A000000)
#define MAP_ROOT_SITE UINT32_C(0x08054B0C)
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
    fprintf(stderr, "mgba-world-item-recovery: %s\n", message);
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
        fprintf(stderr, "mgba-world-item-recovery: invalid %s\n", label);
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

static void write16(struct mCore *core, uint32_t address, uint16_t value)
{
    core->rawWrite16(core, address, -1, value);
}

static void write8(struct mCore *core, uint32_t address, uint8_t value)
{
    core->rawWrite8(core, address, -1, value);
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
            die("Focus Sash predicate instruction limit");
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

static void require_map(struct mCore *core, uint32_t root,
                        uint8_t group, uint8_t map,
                        uint8_t objects, uint8_t bg)
{
    uint32_t events = map_events(core, root, group, map);
    if (read8(core, events) != objects || read8(core, events + 3U) != bg)
        die("patched map event counts differ");
    uint32_t object_array = read32(core, events + 4U);
    uint32_t bg_array = read32(core, events + 16U);
    if (objects && !rom_pointer(object_array))
        die("patched object array pointer invalid");
    if (bg && !rom_pointer(bg_array))
        die("patched bg array pointer invalid");
    bool live_script = objects == 0U;
    for (uint32_t index = 0; index < objects; ++index) {
        uint32_t script = read32(core, object_array + index * 0x18U + 0x10U);
        if (rom_pointer(script))
            live_script = true;
    }
    if (!live_script)
        die("patched map has no live object script");
}

int main(int argc, char **argv)
{
    if (argc != 8) {
        fprintf(stderr, "usage: %s ROM MAP_ROOT PAYLOAD_START PAYLOAD_END LOW_RAID TRAINER_ROOT SHINICHI_COMMAND\n", argv[0]);
        return 2;
    }
    uint32_t map_root = parse_u32(argv[2], "map root");
    uint32_t payload_start = parse_u32(argv[3], "payload start");
    uint32_t payload_end = parse_u32(argv[4], "payload end");
    uint32_t low_raid = parse_u32(argv[5], "low-Raid wrapper");
    uint32_t trainer_root = parse_u32(argv[6], "trainer root");
    uint32_t shinichi = parse_u32(argv[7], "Shinichi command");
    if (!rom_pointer(map_root) || !rom_pointer(payload_start)
        || payload_end <= payload_start || !rom_pointer(payload_end - 1U)
        || !rom_pointer(low_raid) || !rom_pointer(trainer_root)
        || !rom_pointer(shinichi))
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
    if (transitions < 10U)
        die("boot framebuffer did not transition");
    if (read32(core, MAP_ROOT_SITE) != map_root)
        die("map root differs from metadata");

    require_map(core, map_root, 96U, 5U, 11U, 5U);
    require_map(core, map_root, 96U, 12U, 3U, 1U);
    require_map(core, map_root, 3U, 19U, 7U, 3U);
    require_map(core, map_root, 3U, 21U, 16U, 3U);
    require_map(core, map_root, 3U, 23U, 10U, 3U);

    uint32_t sash = ITEM_TABLE + FOCUS_SASH * ITEM_STRIDE;
    if (read16(core, sash + 10U) != FOCUS_SASH
        || read8(core, sash + 14U) != 39U || read8(core, sash + 15U) != 100U
        || read8(core, sash + 21U) != 1U || read8(core, sash + 36U) != 0U)
        die("Focus Sash 40-byte ABI differs");
    write16(core, G_BATTLE_MONS + 0x2EU, FOCUS_SASH);
    write16(core, G_BATTLE_MONS + 0x2CU, 100U);
    write16(core, G_BATTLE_MONS + 0x28U, 100U);
    uint32_t sash_effect = call_thumb(core, ITEM_GET_HOLD_EFFECT, FOCUS_SASH);
    uint32_t sash_mystery = call_thumb(core, ITEM_GET_MYSTERY2, FOCUS_SASH);
    if (sash_effect != 39U || sash_mystery != 1U) {
        fprintf(stderr, "mgba-world-item-recovery: Focus Sash accessors effect=%" PRIu32
                " mystery=%" PRIu32 "\n", sash_effect, sash_mystery);
        die("Focus Sash runtime item accessors differ");
    }
    for (uint32_t offset = 0; offset < UINT32_C(0x4000); offset += 4U)
        write32(core, NEW_BATTLE_STRUCT_SCRATCH + offset, 0U);
    write32(core, G_NEW_BATTLE_STRUCT, NEW_BATTLE_STRUCT_SCRATCH);
    uint32_t sash_holding = call_thumb(core, IS_HOLDING_FOCUS_SASH, 0U);
    uint32_t sash_full = call_thumb(core, IS_AFFECTED_BY_FOCUS_SASH, 0U);
    if (sash_holding != 1U || sash_full != 1U) {
        fprintf(stderr, "mgba-world-item-recovery: Focus Sash holding=%" PRIu32
                " full=%" PRIu32 " gNewBS=%08" PRIX32 "\n",
                sash_holding, sash_full, read32(core, G_NEW_BATTLE_STRUCT));
        die("Focus Sash full-HP predicate rejected");
    }
    write16(core, G_BATTLE_MONS + 0x28U, 99U);
    if (call_thumb(core, IS_AFFECTED_BY_FOCUS_SASH, 0U) != 0U)
        die("Focus Sash non-full predicate accepted");
    write16(core, G_BATTLE_MONS + 0x28U, 1U);
    if (call_thumb(core, IS_AFFECTED_BY_FOCUS_SASH, 0U) != 0U)
        die("Focus Sash HP1 predicate accepted");
    write16(core, G_BATTLE_MONS + 0x28U, 100U);
    write16(core, G_BATTLE_MONS + 0x2EU, 0U);
    if (call_thumb(core, IS_AFFECTED_BY_FOCUS_SASH, 0U) != 0U)
        die("Focus Sash missing-item predicate accepted");
    write16(core, G_BATTLE_MONS + 0x2EU, FOCUS_SASH);
    write8(core, G_ACTIVE_BATTLER, 0U);
    write32(core, G_BATTLE_EXEC_BUFFER, 0U);
    write8(core, G_BANK_TARGET, 0U);
    write8(core, BATTLE_SCRIPT_SCRATCH, 0x6AU);
    write8(core, BATTLE_SCRIPT_SCRATCH + 1U, 0U); /* BANK_TARGET */
    write32(core, G_BATTLE_SCRIPT_CURSOR, BATTLE_SCRIPT_SCRATCH);
    (void)call_thumb(core, REMOVE_ITEM_COMMAND, 0U);
    if (read16(core, G_BATTLE_MONS + 0x2EU) != 0U
        || read32(core, G_BATTLE_SCRIPT_CURSOR) != BATTLE_SCRIPT_SCRATCH + 2U)
        die("Focus Sash canonical removeitem path did not consume");

    uint32_t trainer = trainer_root + 299U * 32U;
    if (read8(core, trainer) != 3U || read8(core, trainer + 0x18U) != 5U
        || !rom_pointer(read32(core, trainer + 0x1CU))
        || read8(core, shinichi) != 0x5CU
        || read16u(core, shinichi + 2U) != 299U)
        die("Shinichi exact trainer binding differs");

    /* The called CFRU configurator already has exact-mGBA policy coverage.
     * Here verify the Stage49 bridge itself: Thumb prologue, fifth stack
     * argument=1, r0..r3=(0,0,0,10), BLX and canonical target literal. */
    static const uint16_t wrapper[] = {
        0xB510U, 0xB082U, 0x2001U, 0x9000U, 0x2000U, 0x2100U,
        0x2200U, 0x230AU, 0x4C01U, 0x47A0U, 0xB002U, 0xBD10U,
    };
    uint32_t wrapper_address = low_raid & ~1U;
    for (size_t index = 0; index < sizeof(wrapper) / sizeof(wrapper[0]); ++index) {
        if (read16(core, wrapper_address + (uint32_t)index * 2U) != wrapper[index])
            die("low-Raid Thumb wrapper ABI differs");
    }
    uint32_t raid_target = read32(core, wrapper_address + 24U);
    if (raid_target != UINT32_C(0x0912632D))
        die("low-Raid configurator target differs");

    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"checks\":{\"boot\":true,\"map_events\":true,"
           "\"focus_sash_abi\":true,\"focus_sash_predicate\":true,"
           "\"focus_sash_consumption\":true,"
           "\"shinichi_binding\":true,"
           "\"low_raid_thumb_abi\":true},\"framebuffer_transitions\":%" PRIu32
           ",\"raid_target\":%" PRIu32 "}\n", transitions, raid_target);
    free(video);
    core->deinit(core);
    return 0;
}
