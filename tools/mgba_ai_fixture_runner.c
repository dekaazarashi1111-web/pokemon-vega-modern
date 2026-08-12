/*
 * CFRU AI cycle fixture for mGBA 0.10.2.
 *
 * The runner boots a clean CFRU ROM through an explicit input trace, captures a
 * naturally initialized battle, then calls the ROM's own AI entry points under
 * the emulated ARM7TDMI.  No host-side AI surrogate is used.  Cold/warm differ
 * only by the CFRU prediction-cache fields copied from an actual prewarm call.
 */
#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include <mgba/core/core.h>
#include <mgba/core/log.h>
#include <mgba/core/timing.h>

#define ARRAY_LEN(value) (sizeof(value) / sizeof((value)[0]))
#define MAX_STEPS UINT64_C(100000000)

/* Active BPRJ0 RAM symbols from the pinned CFRU-JP BPRJ.ld. */
enum {
    ADDR_BATTLE_TYPE_FLAGS = 0x02022AAC,
    ADDR_BATTLE_BUFFER_B = 0x02023324,
    ADDR_ACTIVE_BATTLER = 0x02023B24,
    ADDR_BATTLERS_COUNT = 0x02023B2C,
    ADDR_BATTLER_PARTY_INDEXES = 0x02023B2E,
    ADDR_BATTLER_POSITIONS = 0x02023B36,
    ADDR_BATTLE_MONS = 0x02023B44,
    ADDR_BANK_TARGET = 0x02023CCC,
    ADDR_ABSENT_BATTLER_FLAGS = 0x02023CD0,
    ADDR_BATTLE_STRUCT_POINTER = 0x02023F48,
    ADDR_BATTLE_RESOURCES_POINTER = 0x02023F54,
    ADDR_PLAYER_PARTY_COUNT = 0x02023F89,
    ADDR_ENEMY_PARTY = 0x02023F8C,
    ADDR_PLAYER_PARTY = 0x020241E4,
    ADDR_NEW_BATTLE_STRUCT_POINTER = 0x0203DFB0,
};

enum {
    BATTLE_TYPE_DOUBLE = 0x0001,
    BATTLE_TYPE_TRAINER = 0x0008,
    PARTY_SIZE = 6,
    POKEMON_SIZE = 100,
    POKEMON_CURRENT_HP_OFFSET = 0x56,
    BATTLE_MON_SIZE = 88,
    NEWBS_RECALCULATED_DOUBLES_OFFSET = 0x00A0,
    NEWBS_CALCULATED_PREDICTIONS_BYTE = 0x0164,
    NEWBS_CALCULATED_PREDICTIONS_BIT = 0x08,
    /* ai.randSeed等の非cache状態は除外し、itemEffects以降のみをoverlayする。 */
    NEWBS_AI_CACHE_OFFSET = 0x0299,
    NEWBS_AI_RAND_SEED_OFFSET = 0x028C,
    NEWBS_AI_END = 0x0554,
    ROM_GET_MON_DATA = 0x0803F355,
    ROM_SET_MON_DATA = 0x0803FA71,
    MON_DATA_MOVE1 = 13,
    MON_DATA_PP1 = 17,
    BATTLE_MON_MOVES_OFFSET = 0x0C,
    BATTLE_MON_PP_OFFSET = 0x24,
    SET_MON_DATA_SCRATCH = 0x0203FFF0,
};

/* Each set is valid for the corresponding starter species' normal learnset. */
static const uint16_t FIXTURE_MOVES[2][4] = {
    {10, 45, 52, 108},  /* Scratch, Growl, Ember, Smokescreen */
    {33, 39, 55, 110},  /* Tackle, Tail Whip, Water Gun, Withdraw */
};

static const uint8_t FIXTURE_PP[2][4] = {
    {35, 40, 25, 20},
    {35, 30, 25, 40},
};

struct Segment {
    uint32_t frames;
    uint16_t keys;
};

#define A(wait_frames) {2, 1}, {(wait_frames), 0}

/* Trace generated from a clean save. Key bits: A=1, B=2, START=8,
 * RIGHT=16, LEFT=32, UP=64, DOWN=128. */
static const struct Segment BOOT_TRACE[] = {
    /* Boot, title, main menu, controls help. */
    {600, 0}, {600, 0}, {1, 8}, {1, 0}, {180, 0}, {300, 0},
    {2, 8}, {2, 0}, {120, 0}, {120, 0}, {2, 1}, {2, 0}, {180, 0},
    /* Oak introduction, player naming, rival naming. */
    A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20),
    A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(120),
    A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20),
    A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(20), A(120),
    A(60), A(60), A(60), A(60), A(60), A(60), A(60), A(60), A(60), A(180),
    A(100), A(100), A(100), A(100), A(100), A(100), A(100), A(100), A(100), A(200),
    A(120), A(120), A(120), A(180),
    A(120), A(120), A(120), A(120), A(120), A(200),
    A(120), A(120), A(120), A(120), A(120), A(120), A(120), A(120), A(120), A(300),
    {80, 16}, {10, 0}, {140, 64}, {180, 0}, {2, 2}, {30, 0}, {80, 32}, {120, 0},
    {60, 32}, {10, 0}, {180, 128}, {180, 0},
    {100, 16}, {10, 0}, {220, 128}, {180, 0}, {100, 32}, {10, 0}, {150, 128}, {180, 0},
    {50, 32}, {10, 0}, {80, 128}, {200, 0}, {40, 16}, {10, 0}, {60, 128}, {200, 0},
    {20, 32}, {10, 0}, {40, 64}, {10, 0}, {60, 128}, {200, 0},
    {120, 128}, {60, 32}, {300, 64}, {300, 0}, {180, 16}, {10, 0}, {300, 64}, {300, 0},
    {2, 1}, {120, 0}, {2, 1}, {120, 0}, {2, 1}, {120, 0}, {2, 1}, {120, 0},
    {2, 1}, {120, 0}, {2, 1}, {120, 0}, {2, 1}, {120, 0}, {2, 1}, {120, 0},
    {2, 1}, {120, 0}, {2, 1}, {500, 0},
    {2, 1}, {150, 0}, {2, 1}, {150, 0}, {2, 1}, {200, 0},
    {2, 1}, {150, 0}, {2, 1}, {150, 0}, {2, 1}, {200, 0},
    {2, 1}, {150, 0}, {2, 1}, {200, 0},
    {2, 1}, {150, 0}, {2, 1}, {150, 0}, {2, 1}, {200, 0},
    {2, 1}, {200, 0}, {2, 1}, {200, 0}, {2, 1}, {200, 0}, {2, 1}, {200, 0},
    {2, 1}, {300, 0},
    {60, 128}, {10, 0}, {80, 16}, {10, 0}, {40, 64}, {100, 0},
    {2, 1}, {100, 0}, {60, 16}, {10, 0}, {100, 64}, {100, 0},
    {2, 1}, {180, 0}, {2, 1}, {180, 0}, {2, 1}, {180, 0}, {2, 1}, {200, 0},
    {2, 1}, {180, 0}, {2, 128}, {10, 0}, {2, 1}, {400, 0},
    {2, 1}, {180, 0}, {2, 1}, {180, 0}, {2, 1}, {180, 0}, {2, 1}, {180, 0},
    {2, 1}, {300, 0}, {80, 32}, {10, 0}, {220, 128}, {400, 0},
    {90, 32}, {10, 0}, {220, 128}, {400, 0},
    {2, 1}, {180, 0}, {2, 1}, {180, 0}, {2, 1}, {180, 0}, {2, 1}, {180, 0},
    {2, 1}, {180, 0}, {2, 1}, {400, 0},
    {2, 1}, {160, 0}, {2, 1}, {160, 0}, {2, 1}, {160, 0}, {2, 1}, {160, 0},
    {2, 1}, {160, 0}, {2, 1}, {160, 0}, {2, 1}, {160, 0}, {2, 1}, {160, 0},
    {2, 1}, {160, 0}, {2, 1}, {160, 0}, {2, 1}, {160, 0}, {2, 1}, {160, 0},
    {2, 1}, {160, 0}, {2, 1}, {160, 0}, {2, 1}, {400, 0},
};

struct Snapshot {
    size_t size;
    uint8_t *bytes;
};

struct Measurement {
    uint64_t cycles;
    uint64_t instructions;
    uint8_t action;
    uint16_t parameter;
    uint8_t target;
    uint32_t return_value;
    uint32_t effective_ai_flags;
};

struct RomCall {
    uint64_t cycles;
    uint64_t instructions;
    uint32_t return_value;
};

static void die(const char *message) {
    fprintf(stderr, "mgba-ai-fixture: %s\n", message);
    exit(1);
}

static unsigned log_problem_count;

static void quiet_log(struct mLogger *logger, int category, enum mLogLevel level,
                      const char *format, va_list args) {
    (void) logger;
    /* GAME_ERRORはCFRU/BIOS HLE互換診断であり、mGBA自身のWARN以上とは別枠。 */
    if (!(level & (mLOG_FATAL | mLOG_ERROR | mLOG_WARN))) return;
    ++log_problem_count;
    fprintf(stderr, "mGBA[%s][0x%02x]: ", mLogCategoryName(category), (unsigned) level);
    vfprintf(stderr, format, args);
    fputc('\n', stderr);
}

static time_t fixed_unix_time(struct mRTCSource *source) {
    (void) source;
    return (time_t) 946684800; /* 2000-01-01T00:00:00Z */
}

static uint8_t read8(struct mCore *core, uint32_t address) {
    return (uint8_t) core->rawRead8(core, address, -1);
}

static uint16_t read16(struct mCore *core, uint32_t address) {
    return (uint16_t) core->rawRead16(core, address, -1);
}

static uint32_t read32(struct mCore *core, uint32_t address) {
    return core->rawRead32(core, address, -1);
}

static void write8(struct mCore *core, uint32_t address, uint8_t value) {
    core->rawWrite8(core, address, -1, value);
}

static void write16(struct mCore *core, uint32_t address, uint16_t value) {
    core->rawWrite16(core, address, -1, value);
}

static int32_t read_register(struct mCore *core, const char *name) {
    int32_t value = 0;
    if (!core->readRegister(core, name, &value)) die("register read failed");
    return value;
}

static void write_register(struct mCore *core, const char *name, uint32_t value) {
    int32_t signed_value = (int32_t) value;
    if (!core->writeRegister(core, name, &signed_value)) die("register write failed");
}

static struct Snapshot take_snapshot(struct mCore *core) {
    struct Snapshot result = {.size = core->stateSize(core), .bytes = NULL};
    result.bytes = malloc(result.size);
    if (!result.bytes || !core->saveState(core, result.bytes)) die("state save failed");
    return result;
}

static void restore_snapshot(struct mCore *core, const struct Snapshot *snapshot) {
    if (snapshot->size != core->stateSize(core) || !core->loadState(core, snapshot->bytes)) {
        die("state restore failed");
    }
}

static uint64_t fnv1a64_ram(struct mCore *core) {
    uint64_t hash = UINT64_C(14695981039346656037);
    static const struct { uint32_t start; uint32_t size; } ranges[] = {
        {0x02000000, 0x00040000}, /* EWRAM */
        {0x03000000, 0x00008000}, /* IWRAM */
    };
    for (size_t range = 0; range < ARRAY_LEN(ranges); ++range) {
        for (uint32_t offset = 0; offset < ranges[range].size; ++offset) {
            hash ^= read8(core, ranges[range].start + offset);
            hash *= UINT64_C(1099511628211);
        }
    }
    return hash;
}

struct Sha256 {
    uint32_t state[8];
    uint64_t bit_count;
    uint8_t block[64];
    size_t block_size;
};

static uint32_t rotate_right(uint32_t value, unsigned count) {
    return (value >> count) | (value << (32 - count));
}

static void sha256_transform(struct Sha256 *sha, const uint8_t block[64]) {
    static const uint32_t constants[64] = {
        0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
        0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
        0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
        0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
        0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
        0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
        0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
        0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2,
    };
    uint32_t words[64];
    for (unsigned i = 0; i < 16; ++i) {
        words[i] = ((uint32_t) block[i * 4] << 24) | ((uint32_t) block[i * 4 + 1] << 16) |
                   ((uint32_t) block[i * 4 + 2] << 8) | block[i * 4 + 3];
    }
    for (unsigned i = 16; i < 64; ++i) {
        uint32_t s0 = rotate_right(words[i - 15], 7) ^ rotate_right(words[i - 15], 18) ^ (words[i - 15] >> 3);
        uint32_t s1 = rotate_right(words[i - 2], 17) ^ rotate_right(words[i - 2], 19) ^ (words[i - 2] >> 10);
        words[i] = words[i - 16] + s0 + words[i - 7] + s1;
    }
    uint32_t a = sha->state[0], b = sha->state[1], c = sha->state[2], d = sha->state[3];
    uint32_t e = sha->state[4], f = sha->state[5], g = sha->state[6], h = sha->state[7];
    for (unsigned i = 0; i < 64; ++i) {
        uint32_t s1 = rotate_right(e, 6) ^ rotate_right(e, 11) ^ rotate_right(e, 25);
        uint32_t choice = (e & f) ^ (~e & g);
        uint32_t first = h + s1 + choice + constants[i] + words[i];
        uint32_t s0 = rotate_right(a, 2) ^ rotate_right(a, 13) ^ rotate_right(a, 22);
        uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
        uint32_t second = s0 + majority;
        h = g; g = f; f = e; e = d + first; d = c; c = b; b = a; a = first + second;
    }
    sha->state[0] += a; sha->state[1] += b; sha->state[2] += c; sha->state[3] += d;
    sha->state[4] += e; sha->state[5] += f; sha->state[6] += g; sha->state[7] += h;
}

static void sha256_update(struct Sha256 *sha, const uint8_t *data, size_t size) {
    for (size_t i = 0; i < size; ++i) {
        sha->block[sha->block_size++] = data[i];
        if (sha->block_size == sizeof(sha->block)) {
            sha256_transform(sha, sha->block);
            sha->bit_count += 512;
            sha->block_size = 0;
        }
    }
}

static void sha256_finish(struct Sha256 *sha, char output[65]) {
    sha->bit_count += sha->block_size * 8;
    sha->block[sha->block_size++] = 0x80;
    if (sha->block_size > 56) {
        while (sha->block_size < 64) sha->block[sha->block_size++] = 0;
        sha256_transform(sha, sha->block);
        sha->block_size = 0;
    }
    while (sha->block_size < 56) sha->block[sha->block_size++] = 0;
    for (unsigned i = 0; i < 8; ++i) sha->block[63 - i] = (uint8_t) (sha->bit_count >> (i * 8));
    sha256_transform(sha, sha->block);
    for (unsigned i = 0; i < 8; ++i) snprintf(output + i * 8, 9, "%08" PRIx32, sha->state[i]);
    output[64] = '\0';
}

static void sha256_file(const char *path, char output[65]) {
    struct Sha256 sha = {.state = {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
                                    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19}};
    FILE *input = fopen(path, "rb");
    if (!input) die("ROM hash input open failed");
    uint8_t buffer[65536];
    size_t count;
    while ((count = fread(buffer, 1, sizeof(buffer), input)) != 0) sha256_update(&sha, buffer, count);
    if (ferror(input) || fclose(input)) die("ROM hash input read failed");
    sha256_finish(&sha, output);
}

static void run_boot_trace(struct mCore *core) {
    for (size_t i = 0; i < ARRAY_LEN(BOOT_TRACE); ++i) {
        core->setKeys(core, BOOT_TRACE[i].keys);
        for (uint32_t frame = 0; frame < BOOT_TRACE[i].frames; ++frame) core->runFrame(core);
    }
    core->setKeys(core, 0);
}

static void make_max_party(struct mCore *core) {
    const uint32_t bases[] = {ADDR_PLAYER_PARTY, ADDR_ENEMY_PARTY};
    for (size_t side = 0; side < ARRAY_LEN(bases); ++side) {
        for (unsigned member = 1; member < PARTY_SIZE; ++member) {
            for (unsigned byte = 0; byte < POKEMON_SIZE; ++byte) {
                write8(core, bases[side] + member * POKEMON_SIZE + byte,
                       read8(core, bases[side] + byte));
            }
        }
    }
    write8(core, ADDR_PLAYER_PARTY_COUNT, PARTY_SIZE);
}

static struct RomCall call_rom_args(struct mCore *core, uint32_t function,
                                    uint32_t r0, uint32_t r1, uint32_t r2, uint32_t r3) {
    struct RomCall result = {0};
    uint32_t cpsr = (uint32_t) read_register(core, "cpsr");
    write_register(core, "cpsr", cpsr | 0xA0); /* THUMB + IRQ masked */
    write_register(core, "lr", 0x08000001);
    write_register(core, "r0", r0);
    write_register(core, "r1", r1);
    write_register(core, "r2", r2);
    write_register(core, "r3", r3);
    write_register(core, "pc", function);
    uint64_t before = mTimingGlobalTime(core->timing);
    do {
        if (++result.instructions > MAX_STEPS) die("ROM call instruction limit exceeded");
        core->step(core);
    } while ((((uint32_t) read_register(core, "pc")) & ~1u) != 0x08000002u);
    result.cycles = mTimingGlobalTime(core->timing) - before;
    result.return_value = (uint32_t) read_register(core, "r0");
    return result;
}

static void write_scratch_u32(struct mCore *core, uint32_t value) {
    for (unsigned byte = 0; byte < 4; ++byte) {
        write8(core, SET_MON_DATA_SCRATCH + byte, (uint8_t) (value >> (8 * byte)));
    }
}

static uint32_t get_mon_data(struct mCore *core, uint32_t mon, uint32_t field) {
    return call_rom_args(core, ROM_GET_MON_DATA, mon, field, 0, 0).return_value;
}

static void configure_party_moves(struct mCore *core) {
    const uint32_t bases[] = {ADDR_PLAYER_PARTY, ADDR_ENEMY_PARTY};
    uint8_t configured[2][PARTY_SIZE * POKEMON_SIZE];
    struct Snapshot original = take_snapshot(core);

    for (unsigned side = 0; side < 2; ++side) {
        for (unsigned member = 0; member < PARTY_SIZE; ++member) {
            uint32_t mon = bases[side] + member * POKEMON_SIZE;
            for (unsigned slot = 0; slot < 4; ++slot) {
                write_scratch_u32(core, FIXTURE_MOVES[side][slot]);
                (void) call_rom_args(core, ROM_SET_MON_DATA, mon,
                                     MON_DATA_MOVE1 + slot, SET_MON_DATA_SCRATCH, 0);
                write_scratch_u32(core, FIXTURE_PP[side][slot]);
                (void) call_rom_args(core, ROM_SET_MON_DATA, mon,
                                     MON_DATA_PP1 + slot, SET_MON_DATA_SCRATCH, 0);
            }
        }
    }
    for (unsigned side = 0; side < 2; ++side) {
        for (unsigned member = 0; member < PARTY_SIZE; ++member) {
            uint32_t mon = bases[side] + member * POKEMON_SIZE;
            for (unsigned slot = 0; slot < 4; ++slot) {
                if (get_mon_data(core, mon, MON_DATA_MOVE1 + slot) != FIXTURE_MOVES[side][slot] ||
                    get_mon_data(core, mon, MON_DATA_PP1 + slot) != FIXTURE_PP[side][slot]) {
                    die("SetMonData move/PP verification failed");
                }
            }
            for (unsigned byte = 0; byte < POKEMON_SIZE; ++byte) {
                configured[side][member * POKEMON_SIZE + byte] = read8(core, mon + byte);
            }
        }
    }

    /* Retain only SetMonData's encrypted/checksummed party bytes, not call CPU state. */
    restore_snapshot(core, &original);
    free(original.bytes);
    for (unsigned side = 0; side < 2; ++side) {
        for (unsigned byte = 0; byte < PARTY_SIZE * POKEMON_SIZE; ++byte) {
            write8(core, bases[side] + byte, configured[side][byte]);
        }
    }
}

static void sync_active_moves(struct mCore *core) {
    unsigned count = read8(core, ADDR_BATTLERS_COUNT);
    for (unsigned battler = 0; battler < count; ++battler) {
        unsigned side = battler & 1u;
        uint32_t battle_mon = ADDR_BATTLE_MONS + battler * BATTLE_MON_SIZE;
        for (unsigned slot = 0; slot < 4; ++slot) {
            write16(core, battle_mon + BATTLE_MON_MOVES_OFFSET + slot * 2,
                    FIXTURE_MOVES[side][slot]);
            write8(core, battle_mon + BATTLE_MON_PP_OFFSET + slot, FIXTURE_PP[side][slot]);
        }
    }
}

static void verify_party_moves(struct mCore *core) {
    const uint32_t bases[] = {ADDR_PLAYER_PARTY, ADDR_ENEMY_PARTY};
    struct Snapshot original = take_snapshot(core);
    for (unsigned side = 0; side < 2; ++side) {
        for (unsigned member = 0; member < PARTY_SIZE; ++member) {
            uint32_t mon = bases[side] + member * POKEMON_SIZE;
            for (unsigned slot = 0; slot < 4; ++slot) {
                uint32_t move = get_mon_data(core, mon, MON_DATA_MOVE1 + slot);
                uint32_t pp = get_mon_data(core, mon, MON_DATA_PP1 + slot);
                if (!move || !pp || move != FIXTURE_MOVES[side][slot] ||
                    pp != FIXTURE_PP[side][slot]) {
                    die("party move/PP invariant failed");
                }
            }
        }
    }
    restore_snapshot(core, &original);
    free(original.bytes);
}

static void verify_active_moves(struct mCore *core, unsigned expected) {
    for (unsigned battler = 0; battler < expected; ++battler) {
        unsigned side = battler & 1u;
        uint32_t battle_mon = ADDR_BATTLE_MONS + battler * BATTLE_MON_SIZE;
        for (unsigned slot = 0; slot < 4; ++slot) {
            uint16_t move = read16(core, battle_mon + BATTLE_MON_MOVES_OFFSET + slot * 2);
            uint8_t pp = read8(core, battle_mon + BATTLE_MON_PP_OFFSET + slot);
            if (!move || !pp || move != FIXTURE_MOVES[side][slot] ||
                pp != FIXTURE_PP[side][slot]) {
                die("active battler move/PP invariant failed");
            }
        }
    }
}

static void make_double(struct mCore *core) {
    uint32_t flags = read32(core, ADDR_BATTLE_TYPE_FLAGS) | BATTLE_TYPE_DOUBLE;
    for (unsigned byte = 0; byte < 4; ++byte) {
        write8(core, ADDR_BATTLE_TYPE_FLAGS + byte, (uint8_t) (flags >> (8 * byte)));
    }
    write8(core, ADDR_BATTLERS_COUNT, 4);
    write8(core, ADDR_ABSENT_BATTLER_FLAGS,
           (uint8_t) (read8(core, ADDR_ABSENT_BATTLER_FLAGS) & ~0x0F));
    for (unsigned battler = 0; battler < 4; ++battler) {
        write8(core, ADDR_BATTLER_POSITIONS + battler, (uint8_t) battler);
        write16(core, ADDR_BATTLER_PARTY_INDEXES + battler * 2, (uint16_t) (battler >> 1));
    }
    for (unsigned byte = 0; byte < BATTLE_MON_SIZE; ++byte) {
        write8(core, ADDR_BATTLE_MONS + 2 * BATTLE_MON_SIZE + byte,
               read8(core, ADDR_BATTLE_MONS + byte));
        write8(core, ADDR_BATTLE_MONS + 3 * BATTLE_MON_SIZE + byte,
               read8(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + byte));
    }
}

static void verify_fixture(struct mCore *core, bool is_double) {
    unsigned expected = is_double ? 4 : 2;
    if (!(read32(core, ADDR_BATTLE_TYPE_FLAGS) & BATTLE_TYPE_TRAINER)) {
        die("fixture is not a trainer battle");
    }
    if (read8(core, ADDR_BATTLERS_COUNT) != expected) die("active battler count mismatch");
    if (read8(core, ADDR_ABSENT_BATTLER_FLAGS) & ((1u << expected) - 1u)) {
        die("fixture marks an active battler absent");
    }
    for (unsigned battler = 0; battler < expected; ++battler) {
        if (read8(core, ADDR_BATTLER_POSITIONS + battler) != battler ||
            read16(core, ADDR_BATTLER_PARTY_INDEXES + battler * 2) != (battler >> 1)) {
            die("battler position or party index mismatch");
        }
        if (read16(core, ADDR_BATTLE_MONS + battler * BATTLE_MON_SIZE + 0x28) == 0) {
            die("fixture contains a fainted active battler");
        }
    }
    verify_active_moves(core, expected);
    for (unsigned side = 0; side < 2; ++side) {
        uint32_t base = side ? ADDR_ENEMY_PARTY : ADDR_PLAYER_PARTY;
        for (unsigned member = 0; member < PARTY_SIZE; ++member) {
            if (read16(core, base + member * POKEMON_SIZE + POKEMON_CURRENT_HP_OFFSET) == 0) {
                die("fixture party is not full and alive");
            }
        }
    }
    if (!read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) ||
        !read32(core, ADDR_BATTLE_STRUCT_POINTER) ||
        !read32(core, ADDR_BATTLE_RESOURCES_POINTER)) {
        die("battle runtime pointers are not initialized");
    }
    verify_party_moves(core);
}

static struct Measurement call_rom(struct mCore *core, uint32_t function, uint32_t r0) {
    struct Measurement result = {0};
    struct RomCall call = call_rom_args(core, function, r0, 0, 0, 0);
    result.cycles = call.cycles;
    result.instructions = call.instructions;
    result.return_value = call.return_value;
    unsigned battler = read8(core, ADDR_ACTIVE_BATTLER);
    uint32_t buffer = ADDR_BATTLE_BUFFER_B + battler * 0x200;
    result.action = read8(core, buffer + 1);
    result.parameter = read16(core, buffer + 2);
    result.target = read8(core, ADDR_BANK_TARGET);
    return result;
}

static uint32_t effective_ai_flags(struct mCore *core) {
    uint32_t resources = read32(core, ADDR_BATTLE_RESOURCES_POINTER);
    uint32_t thinking = read32(core, resources + 20); /* BattleResources.ai */
    if (!thinking) die("AI thinking structure is not initialized");
    return read32(core, thinking + 12); /* AI_ThinkingStruct.aiFlags */
}

static uint8_t *capture_prediction_cache(struct mCore *core) {
    uint32_t newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
    size_t size = NEWBS_AI_END - NEWBS_AI_CACHE_OFFSET;
    uint8_t *cache = malloc(size + 5);
    if (!cache) die("cache allocation failed");
    for (size_t i = 0; i < size; ++i) cache[i] = read8(core, newbs + NEWBS_AI_CACHE_OFFSET + i);
    for (unsigned i = 0; i < 4; ++i) cache[size + i] = read8(core, newbs + NEWBS_RECALCULATED_DOUBLES_OFFSET + i);
    cache[size + 4] = read8(core, newbs + NEWBS_CALCULATED_PREDICTIONS_BYTE);
    return cache;
}

static void overlay_prediction_cache(struct mCore *core, const uint8_t *cache) {
    uint32_t newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
    size_t size = NEWBS_AI_END - NEWBS_AI_CACHE_OFFSET;
    for (size_t i = 0; i < size; ++i) write8(core, newbs + NEWBS_AI_CACHE_OFFSET + i, cache[i]);
    for (unsigned i = 0; i < 4; ++i) write8(core, newbs + NEWBS_RECALCULATED_DOUBLES_OFFSET + i, cache[size + i]);
    uint8_t original = read8(core, newbs + NEWBS_CALCULATED_PREDICTIONS_BYTE);
    uint8_t warmed = cache[size + 4];
    write8(core, newbs + NEWBS_CALCULATED_PREDICTIONS_BYTE,
           (uint8_t) ((original & ~NEWBS_CALCULATED_PREDICTIONS_BIT) |
                      (warmed & NEWBS_CALCULATED_PREDICTIONS_BIT)));
}

static void print_measurement(const char *name, const struct Measurement *value) {
    printf("\"%s\":{\"cycles\":%" PRIu64 ",\"instructions\":%" PRIu64
           ",\"action\":%u,\"parameter\":%u,\"target\":%u,\"return_value\":%" PRIu32
           ",\"effective_ai_flags\":%" PRIu32 "}",
           name, value->cycles, value->instructions, value->action,
           value->parameter, value->target, value->return_value, value->effective_ai_flags);
}

static bool measurement_equal(const struct Measurement *left, const struct Measurement *right) {
    return left->cycles == right->cycles && left->instructions == right->instructions &&
           left->action == right->action && left->parameter == right->parameter &&
           left->target == right->target && left->return_value == right->return_value &&
           left->effective_ai_flags == right->effective_ai_flags;
}

static uint32_t parse_address(const char *text) {
    errno = 0;
    char *end = NULL;
    unsigned long value = strtoul(text, &end, 0);
    if (errno || !end || *end || value < 0x08000000ul || value > 0x09FFFFFFul) {
        die("invalid ROM function address");
    }
    return (uint32_t) value;
}

int main(int argc, char **argv) {
    if (argc != 7) {
        fprintf(stderr, "usage: %s ROM EXPECTED_ROM_SHA256 AI_TrySwitchOrUseItem BattleAI_SetupAIData BattleAI_ChooseMoveOrAction ClearCachedAIData\n", argv[0]);
        return 2;
    }
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64 || strcmp(rom_sha256, argv[2]) != 0) die("ROM SHA-256 mismatch");
    uint32_t try_action = parse_address(argv[3]);
    uint32_t setup = parse_address(argv[4]);
    uint32_t choose_move = parse_address(argv[5]);
    uint32_t clear_cache = parse_address(argv[6]);
    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {.sample = NULL, .unixTime = fixed_unix_time,
                             .serialize = NULL, .deserialize = NULL};
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1])) die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    run_boot_trace(core);
    if (log_problem_count != 0) die("mGBA emitted warning/error diagnostics");
    make_max_party(core);
    configure_party_moves(core);
    sync_active_moves(core);
    struct Snapshot natural = take_snapshot(core);

    const char *names[] = {"single_max_party", "double_four_battler"};
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"measurement_kind\":\"mGBA_0.10.2_ARM7TDMI_cycles\","
           "\"return_boundary\":\"callee_return_to_LR; action_stage includes controller_emit\","
           "\"fixed_rtc_unix\":946684800,\"provenance\":{\"rom_sha256\":\"%s\","
           "\"symbols\":{\"AI_TrySwitchOrUseItem\":\"0x%08" PRIX32 "\","
           "\"BattleAI_SetupAIData\":\"0x%08" PRIX32 "\",\"BattleAI_ChooseMoveOrAction\":\"0x%08" PRIX32 "\"," 
           "\"ClearCachedAIData\":\"0x%08" PRIX32 "\",\"GetMonData\":\"0x%08X\","
           "\"SetMonData\":\"0x%08X\"}},"
           "\"move_contract\":{\"player_species\":%u,\"enemy_species\":%u,"
           "\"player_moves\":[10,45,52,108],\"player_pp\":[35,40,25,20],"
           "\"enemy_moves\":[33,39,55,110],\"enemy_pp\":[35,30,25,40],"
           "\"party_write\":\"ROM_SetMonData\",\"party_readback\":\"ROM_GetMonData\"},"
           "\"thresholds\":{\"single_max_party\":{\"cold_max_cycles\":3300000,\"warm_max_cycles\":450000},"
           "\"double_four_battler\":{\"cold_max_cycles\":8000000,\"warm_max_cycles\":800000}},"
           "\"repeatability\":{\"runs\":2,\"status\":\"PASS\"},"
           "\"cache_contract\":{\"cold_calculatedAIPredictions\":0,\"warm_calculatedAIPredictions\":1,"
           "\"overlay_start\":\"NewBattleStruct.ai.itemEffects\",\"excluded_non_cache\":[\"ai.zMoveHelper\",\"ai.randSeed\",\"ai.sideSwitchedThisRound\",\"ai.switchingCooldown\",\"ai.typeAbsorbSwitchingCooldown\"]},"
           "\"fixtures\":{",
           rom_sha256, try_action, setup, choose_move, clear_cache,
           ROM_GET_MON_DATA, ROM_SET_MON_DATA,
           read16(core, ADDR_BATTLE_MONS),
           read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE));
    for (unsigned fixture = 0; fixture < 2; ++fixture) {
        struct Measurement reference[4] = {{0}};
        uint64_t digest = 0;
        for (unsigned run = 0; run < 2; ++run) {
            restore_snapshot(core, &natural);
            if (fixture) make_double(core);
            make_max_party(core);
            sync_active_moves(core);
            write8(core, ADDR_ACTIVE_BATTLER, 1);
            verify_fixture(core, fixture != 0);
            struct Snapshot before_clear = take_snapshot(core);
            (void) call_rom(core, clear_cache, 0);
            uint8_t *cleared_cache = capture_prediction_cache(core);
            restore_snapshot(core, &before_clear);
            overlay_prediction_cache(core, cleared_cache);
            free(cleared_cache);
            free(before_clear.bytes);
            uint32_t newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
            write8(core, newbs + NEWBS_CALCULATED_PREDICTIONS_BYTE,
                   (uint8_t) (read8(core, newbs + NEWBS_CALCULATED_PREDICTIONS_BYTE) &
                              ~NEWBS_CALCULATED_PREDICTIONS_BIT));
            if (read8(core, newbs + NEWBS_CALCULATED_PREDICTIONS_BYTE) &
                NEWBS_CALCULATED_PREDICTIONS_BIT) die("cold cache flag is not clear");
            struct Snapshot base = take_snapshot(core);
            uint64_t run_digest = fnv1a64_ram(core);
            if (run == 0) digest = run_digest;
            else if (digest != run_digest) die("fixture state digest is not repeatable");
            uint32_t base_ai_rand_seed = read32(core, newbs + NEWBS_AI_RAND_SEED_OFFSET);

            verify_active_moves(core, fixture ? 4 : 2);
            struct Measurement cold_action = call_rom(core, try_action, 0);
            if (!(read8(core, newbs + NEWBS_CALCULATED_PREDICTIONS_BYTE) &
                  NEWBS_CALCULATED_PREDICTIONS_BIT)) die("cold call did not populate prediction cache");
            uint8_t *cache = capture_prediction_cache(core);
            restore_snapshot(core, &base);
            overlay_prediction_cache(core, cache);
            if (!(read8(core, newbs + NEWBS_CALCULATED_PREDICTIONS_BYTE) &
                  NEWBS_CALCULATED_PREDICTIONS_BIT)) die("warm cache flag is not set");
            if (read32(core, newbs + NEWBS_AI_RAND_SEED_OFFSET) != base_ai_rand_seed) {
                die("warm overlay changed non-cache AI RNG state");
            }
            verify_active_moves(core, fixture ? 4 : 2);
            struct Measurement warm_action = call_rom(core, try_action, 0);
            restore_snapshot(core, &base);
            verify_active_moves(core, fixture ? 4 : 2);
            struct Measurement setup_cold = call_rom(core, setup, 0xF);
            uint32_t cold_ai_flags = effective_ai_flags(core);
            cold_action.effective_ai_flags = cold_ai_flags;
            struct Measurement move_cold = call_rom(core, choose_move, 0);
            move_cold.action = (uint8_t) move_cold.return_value;
            move_cold.effective_ai_flags = cold_ai_flags;
            restore_snapshot(core, &base);
            overlay_prediction_cache(core, cache);
            verify_active_moves(core, fixture ? 4 : 2);
            struct Measurement setup_warm = call_rom(core, setup, 0xF);
            uint32_t warm_ai_flags = effective_ai_flags(core);
            warm_action.effective_ai_flags = warm_ai_flags;
            struct Measurement move_warm = call_rom(core, choose_move, 0);
            move_warm.action = (uint8_t) move_warm.return_value;
            move_warm.effective_ai_flags = warm_ai_flags;
            free(cache);
            free(base.bytes);

            struct Measurement values[] = {cold_action, warm_action, setup_cold, move_cold,
                                            setup_warm, move_warm};
            if (cold_action.action != warm_action.action || cold_action.parameter != warm_action.parameter ||
                cold_action.target != warm_action.target || move_cold.action != move_warm.action ||
                move_cold.target != move_warm.target) {
                die("cold/warm AI output mismatch");
            }
            if (cold_action.action != 0) {
                die("fixture selected switch/item; move-stage cycles cannot be combined");
            }
            if ((cold_ai_flags & 5) != 5 || (warm_ai_flags & 5) != 5) {
                die("fixture does not include AI_FULL_SMART bits (5)");
            }
            if (run == 0) {
                memcpy(reference, values, sizeof(reference));
                reference[0] = cold_action; reference[1] = warm_action;
                reference[2].cycles = setup_cold.cycles + move_cold.cycles;
                reference[2].instructions = setup_cold.instructions + move_cold.instructions;
                reference[2].action = move_cold.action; reference[2].parameter = move_cold.parameter; reference[2].target = move_cold.target; reference[2].return_value = move_cold.return_value; reference[2].effective_ai_flags = move_cold.effective_ai_flags;
                reference[3].cycles = setup_warm.cycles + move_warm.cycles;
                reference[3].instructions = setup_warm.instructions + move_warm.instructions;
                reference[3].action = move_warm.action; reference[3].parameter = move_warm.parameter; reference[3].target = move_warm.target; reference[3].return_value = move_warm.return_value; reference[3].effective_ai_flags = move_warm.effective_ai_flags;
            } else {
                struct Measurement totals[] = {cold_action, warm_action, {setup_cold.cycles + move_cold.cycles, setup_cold.instructions + move_cold.instructions, move_cold.action, move_cold.parameter, move_cold.target, move_cold.return_value, move_cold.effective_ai_flags}, {setup_warm.cycles + move_warm.cycles, setup_warm.instructions + move_warm.instructions, move_warm.action, move_warm.parameter, move_warm.target, move_warm.return_value, move_warm.effective_ai_flags}};
                for (unsigned index = 0; index < 4; ++index) {
                    if (!measurement_equal(&reference[index], &totals[index])) die("fixture is not repeatable");
                }
            }
        }
        uint64_t total_cold = reference[0].cycles + reference[2].cycles;
        uint64_t total_warm = reference[1].cycles + reference[3].cycles;
        uint64_t cold_limit = fixture ? UINT64_C(8000000) : UINT64_C(3300000);
        uint64_t warm_limit = fixture ? UINT64_C(800000) : UINT64_C(450000);
        if (total_cold > cold_limit || total_warm > warm_limit) die("AI cycle threshold exceeded");
        if (fixture) putchar(',');
        printf("\"%s\":{\"active_battlers\":%u,\"party_size_per_side\":6,"
               "\"move_slots_per_active_battler\":4,\"move_slots_per_party_member\":4,"
               "\"moves_and_pp_nonzero\":true,\"trainer_battle\":true,"
               "\"required_ai_full_smart_bits\":5,\"selected_action\":0,"
               "\"fixture_state_fnv1a64\":\"%016" PRIx64 "\",\"threshold_status\":\"PASS\",\"action_stage\":{",
               names[fixture], fixture ? 4 : 2, digest);
        print_measurement("cold", &reference[0]); putchar(',');
        print_measurement("warm", &reference[1]);
        printf("},\"move_stage\":{");
        print_measurement("cold", &reference[2]); putchar(',');
        print_measurement("warm", &reference[3]);
        printf("},\"total_cycles\":{\"cold\":%" PRIu64 ",\"warm\":%" PRIu64 "}}",
               total_cold, total_warm);
    }
    printf("}}\n");
    free(natural.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
