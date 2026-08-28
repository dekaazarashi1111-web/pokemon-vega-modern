/*
 * Stage58 exact-ROM smoke for the Codex preparation hub and Kanto encounters.
 *
 * This runner deliberately exercises the three new objects through normal GBA
 * input after a stock warp.  The ROM graph is checked first so a coincidental
 * UI or direct engine call can never be promoted to object-path evidence.
 * QOL effect-item coverage belongs to its dedicated Stage58 runner.  This
 * executable reports only the hub, thin-event, and wild domains it executes.
 */
#define _POSIX_C_SOURCE 200809L
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
/* libmGBA's public mCore ABI conditionally includes debugger members.  Load
 * the installed build flags before core.h so post-debugger methods such as
 * savedataClone resolve at the library's actual vtable offsets. */
#include <mgba/flags.h>
/* This test-only interval is outside every LIVE EWRAM owner in
 * config/ram_layout.csv and ends before the next stock field global at
 * 0x0203DFA0 (Codex mailbox/state themselves are at 0x0203F800/FA00).
 * Each host-direct call snapshots and restores the complete interval. */
#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1
#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203DB00U
#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203DF80U
#define QOL_PRODUCTION_EMBEDDED
#include "mgba_qol_production_smoke.c"

#include <ctype.h>

enum {
    S58_STAGE = 58U,
    S58_MAP_HEADER_ROOT_MIN = 0x08000000U,
    S58_ROM_END = 0x0A000000U,
    S58_KANTO_WARP = 0x09220861U,
    S58_CB2_OVERWORLD = 0x08055E75U,
    /* Japanese FireRed gObjectEvents.  Live coordinates include the stock
     * seven-tile map border; authored template/SaveBlock coordinates do not. */
    S58_OBJECT_EVENTS = 0x02036D6CU,
    S58_OBJECT_EVENT_SIZE = 0x24U,
    S58_OBJECT_EVENT_CAPACITY = 16U,
    S58_PLAYER_AVATAR = 0x02036FACU,
    S58_VMAP = 0x03005080U,
    S58_FIELD_LOCK = 0x03000F9CU,
    S58_QUEST_LOG_STATE = 0x0203AD72U,
    S58_QUEST_LOG_PLAYBACK_STATE = 0x03005ED8U,
    S58_KEY_RIGHT = 0x0010U,
    S58_KEY_LEFT = 0x0020U,
    S58_KEY_UP = 0x0040U,
    S58_KEY_DOWN = 0x0080U,
    S58_PLAYER_MON = 0x020241E4U,
    S58_PLAYER_COUNT = 0x02023F89U,
    S58_MAILBOX = 0x0203F900U,
    S58_CODEX_REQUEST = S58_MAILBOX + 160U,
    S58_MAILBOX_MAGIC = 0x32524243U,
    S58_CODEX_EXTERNAL_CAPABILITIES = 0x7FFFU,
    S58_CODEX_STATE = 0x0203FA00U,
    S58_CODEX_PHASE_IDLE = 1U,
    S58_CODEX_PHASE_CONFIGURING = 2U,
    S58_CODEX_PHASE_TEAM_PREVIEW = 3U,
    S58_CODEX_PHASE_PLAYER_SELECTION = 4U,
    S58_CODEX_PHASE_ACTION = 6U,
    S58_CODEX_PHASE_RESOLVING = 9U,
    S58_CODEX_PHASE_RESULT = 10U,
    S58_CODEX_PHASE_CPU = 11U,
    S58_CODEX_STATUS_ACCEPTED = 2U,
    S58_CODEX_COMMAND_CONFIGURE = 1U,
    S58_CODEX_COMMAND_UPLOAD = 2U,
    S58_CODEX_COMMAND_COMMIT = 3U,
    S58_CODEX_COMMAND_CHOOSE_TEAM = 4U,
    S58_CODEX_COMMAND_DISCONNECT_CPU = 8U,
    S58_CODEX_COMMAND_DISCONNECT_FORFEIT = 9U,
    S58_CODEX_COMMAND_REWARD_CLOSE = 14U,
    S58_CONTROLLER_CHOOSE_POKEMON = 22U,
    S58_CODEX_TEST_INITIALIZE = 0x093CB8D1U,
    S58_CODEX_OPPONENT_ACTION_POINTER = 0x0820D484U,
    S58_CODEX_SELECTED = 0x0203C6C8U,
    S58_REWARD_OWNER = 0x0203D800U,
    S58_REWARD_OWNER_SIZE = 128U,
    S58_REWARD_MAGIC = 0x31525743U,
    S58_REWARD_WINDOW_CLOSED = 0U,
    S58_REWARD_WINDOW_OPEN = 1U,
    S58_REWARD_PHASE_COMMITTED = 3U,
    S58_SAVE2_KEY_OFFSET = 0x0F20U,
    S58_SAVE1_MONEY_OFFSET = 0x0290U,
    S58_SAVE1_SEEN_PRIMARY_OFFSET = 0x05F8U,
    S58_SAVE1_SEEN_SECONDARY_OFFSET = 0x3A18U,
    S58_SAVE2_POKEDEX_PERSONALITY_OFFSET = 0x001CU,
    S58_SAVE2_POKEDEX_OWNED_OFFSET = 0x0028U,
    S58_SAVE2_POKEDEX_SEEN_OFFSET = 0x005CU,
    S58_POKEDEX_BITMAP_SIZE = 52U,
    S58_POKEDEX_PERSONALITY_SIZE = 8U,
    S58_ITEM_TABLE = 0x0904D108U,
    S58_ITEM_STRIDE = 40U,
    S58_ITEM_POCKET_OFFSET = 22U,
    S58_SET_BAG_POCKETS_POINTERS = 0x0809984DU,
    S58_BAG_POCKETS = 0x020397D8U,
    S58_ADD_BAG_ITEM = 0x08099A8DU,
    S58_REMOVE_BAG_ITEM = 0x08099BE1U,
    S58_BAG_MENU_STATE = 0x0203AC74U,
    S58_BAG_MAIN_CALLBACK = 0x081089E5U,
    /* These are the rooted production entry sites, not the private serializer.
     * Their currently installed jump chains own encounter generation and write
     * gEnemyParty through the same adapters used by ordinary field play. */
    S58_WILD_LAND_WATER_ROCK_OWNER = 0x080826D8U,
    S58_WILD_FISHING_OWNER = 0x08082750U,
    S58_WILD_AREA_LAND = 0U,
    S58_WILD_AREA_WATER = 1U,
    S58_WILD_AREA_ROCK = 2U,
    S58_WILD_RATE_LAND = 7U,
    S58_WILD_RATE_WATER = 2U,
    S58_WILD_RATE_ROCK = 25U,
    S58_WILD_RATE_FISHING = 20U,
    S58_MAP_GRID_FIELD = 0x08058805U,
    S58_MAP_GRID_COLLISION = 0x08058681U,
    S58_FIELD_BORDER = 7U,
    S58_ENCOUNTER_ATTRIBUTE = 4U,
    S58_ENCOUNTER_LAND = 1U,
    S58_ENCOUNTER_WATER = 2U,
    S58_PLAYER_RUNNING_STATE_OFFSET = 2U,
    S58_PLAYER_TILE_TRANSITION_STATE_OFFSET = 3U,
    S58_PLAYER_MOVING = 2U,
    S58_PLAYER_TILE_CENTER = 2U,
    S58_REGISTERED_ITEM_OFFSET = 0x0296U,
    S58_ITEM_OLD_ROD = 262U,
    S58_ITEM_GOOD_ROD = 263U,
    S58_ITEM_SUPER_ROD = 264U,
    S58_MOVE_SURF = 57U,
    S58_MOVE_ROCK_SMASH = 249U,
    S58_FLAG_BADGE05 = 0x0824U,
    S58_FLAG_BADGE06 = 0x0825U,
    S58_ROCK_SMASH_SCRIPT = 0x081A47E3U,
    S58_WILD_HEADER_LIMIT = 1024U,
    S58_SCRIPT_SCAN = 96U,
    S58_MART_LIMIT = 64U,
    S58_MART_ITEMS_CAPACITY = 13U,
    S58_STARTMENU_SAVE = 4U,
    S58_STARTMENU_SAVE_CALLBACK = 0x0806EDB9U,
    S58_THIN_LIMIT = 16U,
    S58_WARP_FRAMES = 1800U,
    S58_FIELD_SETTLE = 180U,
    S58_TITLE_FRAMES = 1200U,
    S58_CONTINUE_PULSES = 24U,
    S58_MAP_VIEW_OFFSET = 0x898U,
    S58_MAP_VIEW_WIDTH = 15U,
    S58_MAP_VIEW_HEIGHT = 14U,
    S58_MAP_VIEW_COUNT = 210U,
    S58_DEPOSIT_SPECIES = 25U,
    S58_DEPOSIT_LEVEL = 20U,
    S58_DEPOSIT_BOX = 0U,
    S58_DEPOSIT_SLOT = 0U,
    S58_MON_DATA_MOVE1 = 13U,
};

struct JsonSpan {
    const char *begin;
    const char *end;
};

struct HubObject {
    uint32_t local_id;
    uint32_t graphics_id;
    uint32_t x;
    uint32_t y;
    uint32_t script;
    uint32_t special;
    uint32_t entry_special;
    uint32_t storage_script;
};

struct HubCases {
    uint32_t group;
    uint32_t map;
    uint32_t object_count;
    struct HubObject npc;
    struct HubObject pc;
    struct HubObject healer;
    struct HubObject mart;
    uint16_t mart_items[S58_MART_LIMIT];
    unsigned mart_item_count;
};

struct ThinEvent {
    uint8_t group;
    uint8_t map;
    uint8_t local_id;
    uint16_t item_id;
    uint16_t flag;
    uint16_t quantity;
    uint16_t x;
    uint16_t y;
    uint8_t object_count;
    uint32_t script;
    bool script_given;
};

struct CodexResultRoute {
    char kind[8];
    uint32_t site;
    uint32_t expected;
    uint32_t replacement;
};

struct CodexResultCompat {
    uint32_t end_turn_function_table;
    uint32_t inherited_return_to_field_adapter;
    uint32_t nonpunitive_result_script;
    uint32_t return_to_field_adapter;
    struct CodexResultRoute rows[3];
    unsigned row_count;
};

struct Stage58Cases {
    char rom_sha256[65];
    uint32_t schema_version;
    uint32_t stage;
    uint32_t map_groups_root;
    uint32_t wild_headers_root;
    uint32_t effect_item_count;
    struct HubCases hub;
    struct ThinEvent thin_events[S58_THIN_LIMIT];
    unsigned thin_event_count;
    struct CodexResultCompat codex_result;
    struct JsonSpan wild_representatives;
    char *source;
};

static const unsigned s58_mode_slots[4] = {12U, 5U, 5U, 10U};
static const char *const s58_mode_names[4] = {
    "land", "water", "rock", "fishing",
};
static color_t s58_video[240U * 160U];
static struct mCore *s58_log_core;
static bool s58_quest_log_observed;
static bool s58_quest_log_recorded;
static uint64_t s58_quest_log_before_hash;
static uint64_t s58_quest_log_saved_hash;
static bool s58_ewram_pointer(uint32_t value);

static uint64_t s58_quest_log_hash(struct mCore *core)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    if (!s58_ewram_pointer(save1))
        return 0U;
    uint64_t hash = UINT64_C(14695981039346656037);
    for (uint32_t offset = 0x1300U; offset < 0x2CA0U; ++offset) {
        hash ^= read8(core, save1 + offset);
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

static void s58_die(const char *message)
{
    fprintf(stderr, "mgba-stage58-convenience: %s\n", message);
    exit(1);
}

static void s58_log(struct mLogger *logger, int category,
                    enum mLogLevel level, const char *format, va_list args)
{
    (void)logger;
    if (!(level & (mLOG_FATAL | mLOG_ERROR | mLOG_WARN)))
        return;
    if (strstr(mLogCategoryName(category), "Savedata") != NULL
        && strstr(format, "Savegame time offset set") != NULL)
        return;
    ++log_problem_count;
    if (log_problem_count <= 12U) {
        uint32_t pc = s58_log_core
            ? (uint32_t)read_register(s58_log_core, "pc") : 0U;
        uint32_t sp = s58_log_core
            ? (uint32_t)read_register(s58_log_core, "sp") : 0U;
        fprintf(stderr, "mGBA[%s][0x%02x] pc=%08" PRIx32
                " lr=%08" PRIx32 " sp=%08" PRIx32
                " r0=%08" PRIx32 " r1=%08" PRIx32
                " r2=%08" PRIx32 " r3=%08" PRIx32
                " r4=%08" PRIx32 " r5=%08" PRIx32
                " r6=%08" PRIx32 " r7=%08" PRIx32,
                mLogCategoryName(category), (unsigned)level,
                pc,
                s58_log_core
                    ? (uint32_t)read_register(s58_log_core, "lr") : 0U,
                sp,
                s58_log_core
                    ? (uint32_t)read_register(s58_log_core, "r0") : 0U,
                s58_log_core
                    ? (uint32_t)read_register(s58_log_core, "r1") : 0U,
                s58_log_core
                    ? (uint32_t)read_register(s58_log_core, "r2") : 0U,
                s58_log_core
                    ? (uint32_t)read_register(s58_log_core, "r3") : 0U,
                s58_log_core
                    ? (uint32_t)read_register(s58_log_core, "r4") : 0U,
                s58_log_core
                    ? (uint32_t)read_register(s58_log_core, "r5") : 0U,
                s58_log_core
                    ? (uint32_t)read_register(s58_log_core, "r6") : 0U,
                s58_log_core
                    ? (uint32_t)read_register(s58_log_core, "r7") : 0U);
        if (s58_log_core && pc >= 0x081C7A5CU && pc <= 0x081C7A60U)
            fprintf(stderr, " assert_args=%08" PRIx32 ",%08" PRIx32
                    ",%08" PRIx32 ",%08" PRIx32
                    " assert_caller=%08" PRIx32
                    " free_internal_return=%08" PRIx32
                    " free_caller=%08" PRIx32,
                    read32(s58_log_core, sp),
                    read32(s58_log_core, sp + 4U),
                    read32(s58_log_core, sp + 8U),
                    read32(s58_log_core, sp + 12U),
                    read32(s58_log_core, sp + 20U),
                    read32(s58_log_core, sp + 40U),
                    read32(s58_log_core, sp + 44U));
        fputs(": ", stderr);
        vfprintf(stderr, format, args);
        fputc('\n', stderr);
    }
}

static bool s58_rom_pointer(uint32_t value)
{
    value &= ~1U;
    return value >= S58_MAP_HEADER_ROOT_MIN && value < S58_ROM_END;
}

static bool s58_ewram_pointer(uint32_t value)
{
    return value >= 0x02000000U && value < 0x02040000U;
}

static uint16_t s58_read16u(struct mCore *core, uint32_t address)
{
    return (uint16_t)(read8(core, address)
        | (uint16_t)read8(core, address + 1U) << 8U);
}

static uint32_t s58_read32u(struct mCore *core, uint32_t address)
{
    return (uint32_t)read8(core, address)
        | (uint32_t)read8(core, address + 1U) << 8U
        | (uint32_t)read8(core, address + 2U) << 16U
        | (uint32_t)read8(core, address + 3U) << 24U;
}

static char *s58_read_text(const char *path)
{
    FILE *stream = fopen(path, "rb");
    if (!stream)
        s58_die("cases JSONを開けません");
    if (fseek(stream, 0L, SEEK_END) != 0)
        s58_die("cases JSON seek失敗");
    long length = ftell(stream);
    if (length <= 0L || length > 16L * 1024L * 1024L)
        s58_die("cases JSON size不正");
    rewind(stream);
    char *text = malloc((size_t)length + 1U);
    if (!text || fread(text, 1U, (size_t)length, stream) != (size_t)length)
        s58_die("cases JSON read失敗");
    if (fclose(stream) != 0)
        s58_die("cases JSON close失敗");
    text[length] = '\0';
    return text;
}

static const char *s58_skip_space(const char *cursor, const char *end)
{
    while (cursor < end && isspace((unsigned char)*cursor))
        ++cursor;
    return cursor;
}

static struct JsonSpan s58_value_span(const char *cursor, const char *end)
{
    cursor = s58_skip_space(cursor, end);
    if (cursor >= end)
        s58_die("JSON value欠落");
    struct JsonSpan result = {cursor, cursor};
    if (*cursor == '{' || *cursor == '[') {
        char open = *cursor;
        char close = open == '{' ? '}' : ']';
        unsigned depth = 0U;
        bool string = false;
        bool escape = false;
        for (const char *scan = cursor; scan < end; ++scan) {
            char value = *scan;
            if (string) {
                if (escape)
                    escape = false;
                else if (value == '\\')
                    escape = true;
                else if (value == '"')
                    string = false;
                continue;
            }
            if (value == '"') {
                string = true;
                continue;
            }
            if (value == open)
                ++depth;
            else if (value == close && --depth == 0U) {
                result.end = scan + 1;
                return result;
            }
        }
        s58_die("JSON container終端欠落");
    }
    if (*cursor == '"') {
        bool escape = false;
        for (const char *scan = cursor + 1; scan < end; ++scan) {
            if (escape)
                escape = false;
            else if (*scan == '\\')
                escape = true;
            else if (*scan == '"') {
                result.end = scan + 1;
                return result;
            }
        }
        s58_die("JSON string終端欠落");
    }
    const char *scan = cursor;
    while (scan < end && *scan != ',' && *scan != '}' && *scan != ']'
           && !isspace((unsigned char)*scan))
        ++scan;
    result.end = scan;
    return result;
}

static bool s58_member(struct JsonSpan object, const char *key,
                       struct JsonSpan *value)
{
    if (object.begin >= object.end || *object.begin != '{')
        return false;
    size_t key_length = strlen(key);
    const char *cursor = object.begin + 1;
    while (cursor < object.end - 1) {
        cursor = s58_skip_space(cursor, object.end - 1);
        if (*cursor == ',') {
            ++cursor;
            continue;
        }
        if (*cursor != '"')
            return false;
        const char *name = ++cursor;
        while (cursor < object.end && *cursor != '"') {
            if (*cursor == '\\' && cursor + 1 < object.end)
                ++cursor;
            ++cursor;
        }
        if (cursor >= object.end)
            return false;
        bool match = (size_t)(cursor - name) == key_length
            && memcmp(name, key, key_length) == 0;
        cursor = s58_skip_space(cursor + 1, object.end);
        if (cursor >= object.end || *cursor != ':')
            return false;
        struct JsonSpan candidate = s58_value_span(cursor + 1, object.end);
        if (match) {
            *value = candidate;
            return true;
        }
        cursor = candidate.end;
    }
    return false;
}

static struct JsonSpan s58_require_member(struct JsonSpan object,
                                          const char *key)
{
    struct JsonSpan value = {0};
    if (!s58_member(object, key, &value)) {
        fprintf(stderr, "mgba-stage58-convenience: JSON key欠落: %s\n", key);
        exit(1);
    }
    return value;
}

static uint32_t s58_u32(struct JsonSpan value, const char *label)
{
    const char *cursor = s58_skip_space(value.begin, value.end);
    errno = 0;
    char *end = NULL;
    unsigned long parsed = strtoul(cursor, &end, 0);
    if (errno || end == cursor || end > value.end || parsed > UINT32_MAX) {
        fprintf(stderr, "mgba-stage58-convenience: JSON number不正: %s\n",
                label);
        exit(1);
    }
    return (uint32_t)parsed;
}

static uint32_t s58_member_u32(struct JsonSpan object, const char *key)
{
    return s58_u32(s58_require_member(object, key), key);
}

static uint32_t s58_member_u32_alias(struct JsonSpan object,
                                     const char *first, const char *second)
{
    struct JsonSpan value = {0};
    if (s58_member(object, first, &value) || s58_member(object, second, &value))
        return s58_u32(value, first);
    fprintf(stderr, "mgba-stage58-convenience: JSON key欠落: %s/%s\n",
            first, second);
    exit(1);
}

static bool s58_null(struct JsonSpan value)
{
    value.begin = s58_skip_space(value.begin, value.end);
    return value.end - value.begin == 4
        && memcmp(value.begin, "null", 4U) == 0;
}

static void s58_string(struct JsonSpan value, char *output, size_t capacity,
                       const char *label)
{
    if (value.end - value.begin < 2 || *value.begin != '"'
        || value.end[-1] != '"'
        || (size_t)(value.end - value.begin - 2) >= capacity) {
        fprintf(stderr, "mgba-stage58-convenience: JSON string不正: %s\n",
                label);
        exit(1);
    }
    size_t length = (size_t)(value.end - value.begin - 2);
    memcpy(output, value.begin + 1, length);
    output[length] = '\0';
}

static bool s58_array_next(struct JsonSpan array, const char **cursor,
                           struct JsonSpan *value)
{
    const char *scan = *cursor ? *cursor : array.begin + 1;
    scan = s58_skip_space(scan, array.end - 1);
    if (*scan == ',')
        scan = s58_skip_space(scan + 1, array.end - 1);
    if (scan >= array.end - 1)
        return false;
    *value = s58_value_span(scan, array.end - 1);
    *cursor = value->end;
    return true;
}

static struct JsonSpan s58_array_at(struct JsonSpan array, unsigned wanted)
{
    const char *cursor = NULL;
    struct JsonSpan value = {0};
    for (unsigned index = 0U; s58_array_next(array, &cursor, &value); ++index) {
        if (index == wanted)
            return value;
    }
    s58_die("JSON array index欠落");
    return value;
}

static struct HubObject s58_load_object(struct JsonSpan object,
                                        uint32_t default_graphics)
{
    struct JsonSpan graphics = {0};
    uint32_t graphics_id = default_graphics;
    if (s58_member(object, "gfx", &graphics)
        || s58_member(object, "graphics_id", &graphics))
        graphics_id = s58_u32(graphics, "graphics_id");
    struct HubObject result = {
        .local_id = s58_member_u32(object, "local_id"),
        .graphics_id = graphics_id,
        .x = s58_member_u32(object, "x"),
        .y = s58_member_u32(object, "y"),
        .script = s58_member_u32(object, "script"),
        .special = 0U,
    };
    struct JsonSpan optional = {0};
    if (s58_member(object, "special", &optional))
        result.special = s58_u32(optional, "special");
    if (s58_member(object, "entry_special", &optional))
        result.entry_special = s58_u32(optional, "entry_special");
    if (s58_member(object, "storage_script", &optional))
        result.storage_script = s58_u32(optional, "storage_script");
    return result;
}

static struct Stage58Cases s58_load_cases(const char *path)
{
    struct Stage58Cases result = {0};
    result.source = s58_read_text(path);
    struct JsonSpan root = {result.source, result.source + strlen(result.source)};
    struct JsonSpan hub = s58_require_member(root, "codex_hub");
    struct JsonSpan codex_result = s58_require_member(
        root, "codex_result_compat");
    struct JsonSpan qol = s58_require_member(root, "qol");
    result.schema_version = s58_member_u32(root, "schema_version");
    result.stage = s58_member_u32(root, "stage");
    s58_string(s58_require_member(root, "rom_sha256"), result.rom_sha256,
               sizeof(result.rom_sha256), "rom_sha256");
    result.map_groups_root = s58_member_u32(root, "map_groups_root");
    result.wild_headers_root = s58_member_u32(root, "wild_headers_root");
    result.wild_representatives = s58_require_member(root,
                                                     "wild_representatives");
    struct JsonSpan thin_events = s58_require_member(root, "thin_events");
    result.effect_item_count = s58_member_u32(qol, "effect_item_count");
    result.hub.group = s58_member_u32(hub, "group");
    result.hub.map = s58_member_u32(hub, "map");
    result.hub.object_count = s58_member_u32(hub, "object_count");
    result.hub.npc = s58_load_object(s58_require_member(hub, "npc"), 62U);
    result.hub.pc = s58_load_object(
        s58_require_member(hub, "pc"), UINT32_MAX);
    result.hub.healer = s58_load_object(
        s58_require_member(hub, "healer"), UINT32_MAX);
    result.hub.mart = s58_load_object(
        s58_require_member(hub, "mart"), UINT32_MAX);
    struct JsonSpan items = s58_require_member(
        s58_require_member(hub, "mart"), "items");
    const char *cursor = NULL;
    struct JsonSpan item = {0};
    while (s58_array_next(items, &cursor, &item)) {
        if (result.hub.mart_item_count >= S58_MART_LIMIT)
            s58_die("mart item数が上限超過");
        result.hub.mart_items[result.hub.mart_item_count++] =
            (uint16_t)s58_u32(item, "mart item");
    }
    cursor = NULL;
    while (s58_array_next(thin_events, &cursor, &item)) {
        if (result.thin_event_count >= S58_THIN_LIMIT)
            s58_die("thin event数が上限超過");
        struct ThinEvent *event =
            &result.thin_events[result.thin_event_count++];
        event->group = (uint8_t)s58_member_u32(item, "group");
        event->map = (uint8_t)s58_member_u32(item, "map");
        event->local_id = (uint8_t)s58_member_u32(item, "local_id");
        event->item_id = (uint16_t)s58_member_u32(item, "item_id");
        event->flag = (uint16_t)s58_member_u32(item, "flag");
        event->quantity = (uint16_t)s58_member_u32(item, "quantity");
        event->x = (uint16_t)s58_member_u32(item, "x");
        event->y = (uint16_t)s58_member_u32(item, "y");
        event->object_count =
            (uint8_t)s58_member_u32(item, "object_count_after");
        struct JsonSpan optional = {0};
        if (s58_member(item, "script", &optional)) {
            event->script = s58_u32(optional, "thin script");
            event->script_given = true;
        }
    }
    result.codex_result.end_turn_function_table = s58_member_u32(
        codex_result, "end_turn_function_table");
    result.codex_result.inherited_return_to_field_adapter = s58_member_u32(
        codex_result, "inherited_return_to_field_adapter");
    result.codex_result.nonpunitive_result_script = s58_member_u32(
        codex_result, "nonpunitive_result_script");
    result.codex_result.return_to_field_adapter = s58_member_u32(
        codex_result, "return_to_field_adapter");
    struct JsonSpan result_rows = s58_require_member(codex_result, "rows");
    cursor = NULL;
    while (s58_array_next(result_rows, &cursor, &item)) {
        if (result.codex_result.row_count
            >= ARRAY_LEN(result.codex_result.rows))
            s58_die("Codex result route数が上限超過");
        struct CodexResultRoute *route =
            &result.codex_result.rows[result.codex_result.row_count++];
        s58_string(s58_require_member(item, "kind"), route->kind,
                   sizeof(route->kind), "Codex result kind");
        route->site = s58_member_u32(item, "site");
        route->expected = s58_member_u32(item, "expected");
        route->replacement = s58_member_u32(item, "replacement");
    }
    return result;
}

static uint32_t s58_map_events(struct mCore *core,
                               const struct Stage58Cases *cases)
{
    uint32_t group_table = read32(core, cases->map_groups_root
                                  + cases->hub.group * 4U);
    uint32_t header = read32(core, group_table + cases->hub.map * 4U);
    uint32_t events = read32(core, header + 4U);
    if (!s58_rom_pointer(cases->map_groups_root)
        || !s58_rom_pointer(group_table) || !s58_rom_pointer(header)
        || !s58_rom_pointer(events))
        s58_die("Codex hub map pointer graph不正");
    return events;
}

static uint32_t s58_map_events_at(struct mCore *core,
                                  const struct Stage58Cases *cases,
                                  uint8_t group, uint8_t map)
{
    uint32_t group_table = read32(core, cases->map_groups_root
                                 + (uint32_t)group * 4U);
    uint32_t header = s58_rom_pointer(group_table)
        ? read32(core, group_table + (uint32_t)map * 4U) : 0U;
    uint32_t events = s58_rom_pointer(header) ? read32(core, header + 4U) : 0U;
    return s58_rom_pointer(events) ? events : 0U;
}

static uint32_t s58_find_template(struct mCore *core, uint32_t events,
                                  uint32_t local_id)
{
    uint8_t count = read8(core, events);
    uint32_t objects = read32(core, events + 4U);
    if (!s58_rom_pointer(objects))
        s58_die("Codex hub object pointer不正");
    for (uint32_t index = 0U; index < count; ++index) {
        uint32_t row = objects + index * 0x18U;
        if (read8(core, row) == local_id)
            return row;
    }
    return 0U;
}

static bool s58_template_matches(struct mCore *core, uint32_t row,
                                 const struct HubObject *expected)
{
    return row != 0U
        && read8(core, row) == expected->local_id
        && read8(core, row + 1U) == expected->graphics_id
        && read16(core, row + 4U) == expected->x
        && read16(core, row + 6U) == expected->y
        && read32(core, row + 16U) == expected->script;
}

static bool s58_script_has_special(struct mCore *core, uint32_t script,
                                   uint32_t special, unsigned scan)
{
    if (!s58_rom_pointer(script))
        return false;
    for (unsigned offset = 0U; offset + 2U < scan; ++offset) {
        if (read8(core, script + offset) == 0x25U
            && s58_read16u(core, script + offset + 1U) == special)
            return true;
    }
    return false;
}

static bool s58_script_has_pointer(struct mCore *core, uint32_t script,
                                   uint32_t pointer, unsigned scan)
{
    if (!s58_rom_pointer(script) || !s58_rom_pointer(pointer))
        return false;
    for (unsigned offset = 0U; offset + 3U < scan; ++offset) {
        if (s58_read32u(core, script + offset) == pointer)
            return true;
    }
    return false;
}

static bool s58_script_has_flag_opcode(struct mCore *core, uint32_t script,
                                       uint8_t opcode, uint16_t flag)
{
    if (!s58_rom_pointer(script))
        return false;
    for (unsigned offset = 0U; offset + 2U < S58_SCRIPT_SCAN; ++offset) {
        if (read8(core, script + offset) == opcode
            && s58_read16u(core, script + offset + 1U) == flag)
            return true;
    }
    return false;
}

static uint32_t s58_mart_list(struct mCore *core, uint32_t script)
{
    if (!s58_rom_pointer(script))
        return 0U;
    for (unsigned offset = 0U; offset + 4U < S58_SCRIPT_SCAN; ++offset) {
        if (read8(core, script + offset) == 0x86U) {
            uint32_t list = s58_read32u(core, script + offset + 1U);
            if (s58_rom_pointer(list))
                return list;
        }
    }
    return 0U;
}

static bool s58_hub_graph(struct mCore *core,
                          const struct Stage58Cases *cases)
{
    uint32_t events = s58_map_events(core, cases);
    if (read8(core, events) != cases->hub.object_count
        || cases->hub.object_count > S58_OBJECT_EVENT_CAPACITY)
        return false;
    const struct HubObject *objects[] = {
        &cases->hub.npc, &cases->hub.pc, &cases->hub.healer, &cases->hub.mart,
    };
    for (unsigned index = 0U; index < ARRAY_LEN(objects); ++index) {
        uint32_t row = s58_find_template(core, events, objects[index]->local_id);
        if (!s58_template_matches(core, row, objects[index]))
            return false;
    }
    /* Canonical EventScript_PC first performs its quest-log guard, then
     * dispatches through the stock PC menu to AccessPokemonStorage.  Require
     * that exact graph rather than finding an unrelated special 60 nearby. */
    bool pc_graph = cases->hub.pc.entry_special != 0U
        && s58_rom_pointer(cases->hub.pc.storage_script)
        && s58_script_has_special(core, cases->hub.pc.script,
                                  cases->hub.pc.entry_special,
                                  S58_SCRIPT_SCAN)
        && s58_script_has_pointer(core, cases->hub.pc.script,
                                  cases->hub.pc.storage_script, 256U)
        && s58_script_has_special(core, cases->hub.pc.storage_script,
                                  cases->hub.pc.special,
                                  S58_SCRIPT_SCAN);
    if (!pc_graph
        || !s58_script_has_special(core, cases->hub.healer.script,
                                   cases->hub.healer.special,
                                   S58_SCRIPT_SCAN))
        return false;
    uint32_t list = s58_mart_list(core, cases->hub.mart.script);
    if (!s58_rom_pointer(list) || cases->hub.mart_item_count == 0U)
        return false;
    for (unsigned index = 0U; index < cases->hub.mart_item_count; ++index) {
        if (read16(core, list + index * 2U) != cases->hub.mart_items[index])
            return false;
    }
    return read16(core, list + cases->hub.mart_item_count * 2U) == 0U;
}

static bool s58_codex_result_graph(struct mCore *core,
                                   const struct Stage58Cases *cases)
{
    static const char *const kinds[3] = {"win", "loss", "draw"};
    const struct CodexResultCompat *compat = &cases->codex_result;
    if (compat->row_count != ARRAY_LEN(kinds)
        || !s58_rom_pointer(compat->end_turn_function_table)
        || !s58_rom_pointer(compat->inherited_return_to_field_adapter)
        || !s58_rom_pointer(compat->nonpunitive_result_script)
        || !s58_rom_pointer(compat->return_to_field_adapter))
        return false;
    for (unsigned index = 0U; index < ARRAY_LEN(kinds); ++index) {
        const struct CodexResultRoute *route = &compat->rows[index];
        uint32_t exact_site = compat->end_turn_function_table
            + 4U + index * 4U;
        if (strcmp(route->kind, kinds[index]) != 0
            || route->site != exact_site
            || !s58_rom_pointer(route->expected)
            || !s58_rom_pointer(route->replacement)
            || read32(core, route->site) != route->replacement)
            return false;
    }
    return true;
}

static bool s58_native_flag_runtime_exact(struct mCore *core,
                                          uint32_t getter,
                                          uint32_t setter)
{
    static const uint16_t get_code[22] = {
        0x480A, 0x8800, 0x08C1, 0x2307, 0x4018, 0x4A09,
        0x6812, 0x23EE, 0x011B, 0x18D2, 0x1852, 0x7812,
        0x2301, 0x4083, 0x401A, 0x2A00, 0xD000, 0x2201,
        0x4803, 0x8002, 0x4770, 0x46C0,
    };
    static const uint16_t set_code[18] = {
        0x4808, 0x8800, 0x08C1, 0x2307, 0x4018, 0x4A07,
        0x6812, 0x23EE, 0x011B, 0x18D2, 0x1852, 0x7811,
        0x2301, 0x4083, 0x4319, 0x7011, 0x4770, 0x46C0,
    };
    getter &= ~1U;
    setter &= ~1U;
    if (!s58_rom_pointer(getter) || !s58_rom_pointer(setter))
        return false;
    for (unsigned index = 0U; index < ARRAY_LEN(get_code); ++index) {
        if (read16(core, getter + index * 2U) != get_code[index])
            return false;
    }
    for (unsigned index = 0U; index < ARRAY_LEN(set_code); ++index) {
        if (read16(core, setter + index * 2U) != set_code[index])
            return false;
    }
    return read32(core, getter + 44U) == 0x02036FECU
        && read32(core, getter + 48U) == QOL_SAVE_BLOCK1_SLOT
        && read32(core, getter + 52U) == 0x02037004U
        && read32(core, setter + 36U) == 0x02036FECU
        && read32(core, setter + 40U) == QOL_SAVE_BLOCK1_SLOT;
}

static bool s58_thin_native_script(struct mCore *core, uint32_t script,
                                   uint16_t flag,
                                   uint32_t *getter_out,
                                   uint32_t *setter_out)
{
    if (read8(core, script) != 0x6AU
        || read8(core, script + 1U) != 0x5AU
        || read8(core, script + 2U) != 0x1AU
        || s58_read16u(core, script + 3U) != 0x8000U
        || s58_read16u(core, script + 5U) != flag
        || read8(core, script + 7U) != 0x23U) {
        fprintf(stderr, "thin native prefix %02x %02x %02x %04x %04x %02x\n",
                read8(core, script), read8(core, script + 1U),
                read8(core, script + 2U), s58_read16u(core, script + 3U),
                s58_read16u(core, script + 5U), read8(core, script + 7U));
        return false;
    }
    uint32_t getter = read32(core, script + 8U);
    static const uint8_t compare_true[7] = {
        0x21, 0x0D, 0x80, 0x01, 0x00, 0x06, 0x01,
    };
    for (unsigned index = 0U; index < ARRAY_LEN(compare_true); ++index) {
        if (read8(core, script + 12U + index) != compare_true[index])
            {
                fprintf(stderr, "thin native compare offset=%u got=%02x"
                        " expected=%02x\n", index,
                        read8(core, script + 12U + index),
                        compare_true[index]);
                return false;
            }
    }
    uint32_t setter = 0U;
    for (unsigned offset = 19U; offset + 12U < S58_SCRIPT_SCAN; ++offset) {
        if (read8(core, script + offset) == 0x1AU
            && s58_read16u(core, script + offset + 1U) == 0x8000U
            && s58_read16u(core, script + offset + 3U) == flag
            && read8(core, script + offset + 5U) == 0x23U) {
            setter = s58_read32u(core, script + offset + 6U);
            break;
        }
    }
    if ((getter & 1U) == 0U || (setter & 1U) == 0U) {
        fprintf(stderr, "thin native pointers getter=%08" PRIx32
                " setter=%08" PRIx32 "\n", getter, setter);
        return false;
    }
    *getter_out = getter;
    *setter_out = setter;
    return true;
}

static bool s58_thin_graph(struct mCore *core,
                           const struct Stage58Cases *cases)
{
    if (cases->thin_event_count != 6U)
        return false;
    uint32_t native_getter = 0U, native_setter = 0U;
    for (unsigned index = 0U; index < cases->thin_event_count; ++index) {
        const struct ThinEvent *expected = &cases->thin_events[index];
        uint32_t events = s58_map_events_at(
            core, cases, expected->group, expected->map);
        if (!events || read8(core, events) != expected->object_count)
            return false;
        uint32_t row = s58_find_template(core, events, expected->local_id);
        uint32_t script = row ? read32(core, row + 16U) : 0U;
        uint32_t getter = 0U, setter = 0U;
        bool row_valid = row && read16(core, row + 4U) == expected->x
            && read16(core, row + 6U) == expected->y
            && s58_rom_pointer(script)
            && s58_thin_native_script(
                core, script, expected->flag, &getter, &setter)
            && (!expected->script_given || script == expected->script);
        if (!row_valid) {
            fprintf(stderr, "thin graph[%u] row=%08" PRIx32
                    " count=%u/%u xy=%u,%u/%u,%u script=%08" PRIx32
                    " expected=%08" PRIx32 " given=%u getter=%08" PRIx32
                    " setter=%08" PRIx32 "\n", index, row,
                    read8(core, events), expected->object_count,
                    row ? read16(core, row + 4U) : 0U,
                    row ? read16(core, row + 6U) : 0U,
                    expected->x, expected->y, script, expected->script,
                    expected->script_given, getter, setter);
            return false;
        }
        if (!row || read16(core, row + 4U) != expected->x
            || read16(core, row + 6U) != expected->y
            || !s58_rom_pointer(script)
            || !s58_thin_native_script(
                core, script, expected->flag, &getter, &setter)
            || (expected->script_given
                && script != expected->script))
            return false;
        if (index == 0U) {
            native_getter = getter;
            native_setter = setter;
        } else if (getter != native_getter || setter != native_setter) {
            return false;
        }
    }
    bool native = s58_native_flag_runtime_exact(
        core, native_getter, native_setter);
    if (!native)
        fprintf(stderr, "thin native graph getter=%08" PRIx32
                " setter=%08" PRIx32 "\n",
                native_getter, native_setter);
    return native;
}

static uint32_t s58_find_wild_header(struct mCore *core, uint32_t root,
                                     uint8_t group, uint8_t map)
{
    if (!s58_rom_pointer(root))
        s58_die("wild header root不正");
    for (unsigned index = 0U; index < S58_WILD_HEADER_LIMIT; ++index) {
        uint32_t row = root + index * 20U;
        uint8_t actual_group = read8(core, row);
        uint8_t actual_map = read8(core, row + 1U);
        if (actual_group == 0xFFU && actual_map == 0xFFU)
            return 0U;
        if (actual_group == group && actual_map == map)
            return row;
    }
    s58_die("wild header sentinel欠落");
    return 0U;
}

static bool s58_wild_mode(struct mCore *core, uint32_t actual_info,
                          struct JsonSpan expected, unsigned slot_count)
{
    if (s58_null(expected))
        return actual_info == 0U;
    if (!s58_rom_pointer(actual_info))
        return false;
    uint32_t rate = s58_member_u32(expected, "rate");
    struct JsonSpan slots = s58_require_member(expected, "slots");
    uint32_t actual_slots = read32(core, actual_info + 4U);
    if (read8(core, actual_info) != rate || !s58_rom_pointer(actual_slots))
        return false;
    const char *cursor = NULL;
    struct JsonSpan slot = {0};
    unsigned index = 0U;
    while (s58_array_next(slots, &cursor, &slot)) {
        if (index >= slot_count)
            return false;
        uint32_t row = actual_slots + index * 4U;
        uint32_t low, high, species;
        if (*slot.begin == '[') {
            low = s58_u32(s58_array_at(slot, 0U), "slot low");
            high = s58_u32(s58_array_at(slot, 1U), "slot high");
            species = s58_u32(s58_array_at(slot, 2U), "slot species");
        } else {
            low = s58_member_u32(slot, "low");
            high = s58_member_u32(slot, "high");
            species = s58_member_u32(slot, "species");
        }
        if (read8(core, row) != low
            || read8(core, row + 1U) != high
            || read16(core, row + 2U) != species)
            return false;
        ++index;
    }
    return index == slot_count;
}

static bool s58_wild_contract(struct mCore *core,
                              const struct Stage58Cases *cases,
                              unsigned *representatives_out,
                              unsigned *modes_out, unsigned *slots_out)
{
    const char *cursor = NULL;
    struct JsonSpan representative = {0};
    unsigned representatives = 0U;
    unsigned modes = 0U;
    unsigned slots = 0U;
    while (s58_array_next(cases->wild_representatives, &cursor,
                          &representative)) {
        uint8_t group = (uint8_t)s58_member_u32(representative, "group");
        uint8_t map = (uint8_t)s58_member_u32(representative, "map");
        struct JsonSpan expected_modes = s58_require_member(representative,
                                                           "modes");
        uint32_t header = s58_find_wild_header(
            core, cases->wild_headers_root, group, map);
        bool any = false;
        for (unsigned mode = 0U; mode < 4U; ++mode) {
            struct JsonSpan expected = s58_require_member(
                expected_modes, s58_mode_names[mode]);
            uint32_t actual = header ? read32(core, header + 4U + mode * 4U)
                                     : 0U;
            if (!s58_wild_mode(core, actual, expected, s58_mode_slots[mode]))
                return false;
            if (!s58_null(expected)) {
                any = true;
                ++modes;
                slots += s58_mode_slots[mode];
            }
        }
        /* A no-encounter map may be omitted from the header list or retained
         * as an explicit all-NULL row; both encode the same engine contract. */
        if (any && header == 0U)
            return false;
        ++representatives;
    }
    bool physical_modes[4] = {false, false, false, false};
    for (unsigned index = 0U; index < S58_WILD_HEADER_LIMIT; ++index) {
        uint32_t row = cases->wild_headers_root + index * 20U;
        uint8_t group = read8(core, row);
        uint8_t map = read8(core, row + 1U);
        if (group == 0xFFU && map == 0xFFU)
            break;
        if (group < 96U)
            continue;
        for (unsigned mode = 0U; mode < ARRAY_LEN(physical_modes); ++mode)
            physical_modes[mode] = physical_modes[mode]
                || s58_rom_pointer(read32(core, row + 4U + mode * 4U));
    }
    unsigned physical_mode_count = 0U;
    for (unsigned mode = 0U; mode < ARRAY_LEN(physical_modes); ++mode)
        physical_mode_count += physical_modes[mode] ? 1U : 0U;
    *representatives_out = representatives;
    *modes_out = physical_mode_count;
    *slots_out = slots;
    return representatives == 4U && modes == 4U
        && physical_mode_count == 4U;
}

struct S58WildRuntimeResult {
    bool land;
    bool water;
    bool rock;
    bool fishing;
    bool fishing_rng_boundaries;
    unsigned generated;
    unsigned fishing_rng_samples;
    struct {
        const char *method;
        uint8_t group;
        uint8_t map;
        uint16_t x;
        uint16_t y;
        uint16_t behavior;
        uint16_t facing;
        uint16_t required_item_or_move;
        uint16_t species;
        uint8_t level;
        char source_key[40];
    } evidence[6];
    unsigned evidence_count;
};

static uint32_t s58_call_scheduler_safe(struct mCore *core,
                                        uint32_t function,
                                        uint32_t r0, uint32_t r1,
                                        uint32_t r2, uint32_t r3);
static uint32_t s58_active_local(struct mCore *core, uint8_t local_id);
static bool s58_face_and_interact(struct mCore *core,
                                  const struct HubObject *object);

static uint32_t s58_rng_seed_for_mod100(unsigned wanted)
{
    for (uint32_t seed = 0U; seed <= UINT16_MAX; ++seed) {
        uint32_t next = seed * UINT32_C(1103515245) + UINT32_C(24691);
        if (((next >> 16U) & 0xFFFFU) % 100U == wanted)
            return seed;
    }
    return UINT32_MAX;
}

static bool s58_fishing_rng_boundary_audit(
    struct mCore *core, struct S58WildRuntimeResult *result)
{
    size_t state_size = core->stateSize(core);
    void *state = malloc(state_size);
    if (!state || !core->saveState(core, state)) {
        free(state);
        return false;
    }
    uint32_t info = QOL_PARTY_SCRATCH + 0x200U;
    uint32_t slots = QOL_PARTY_SCRATCH + 0x210U;
    write8(core, info, 20U);
    qol_write32(core, info + 4U, slots);
    for (unsigned slot = 0U; slot < 10U; ++slot) {
        write8(core, slots + slot * 4U, 5U);
        write8(core, slots + slot * 4U + 1U, 5U);
        write16(core, slots + slot * 4U + 2U, (uint16_t)(slot + 1U));
    }
    static const unsigned starts[3] = {0U, 2U, 5U};
    static const unsigned ends[3] = {2U, 5U, 10U};
    unsigned counts[3][10] = {{0}};
    for (unsigned rod = 0U; rod < 3U; ++rod) {
        for (unsigned roll = 0U; roll < 100U; ++roll) {
            uint32_t seed = s58_rng_seed_for_mod100(roll);
            if (seed == UINT32_MAX) {
                fprintf(stderr, "fishing RNG seed missing roll=%u\n", roll);
                goto failure;
            }
            qol_write32(core, BATTLE_CORE_GLOBAL_RNG, seed);
            uint32_t generated = call_bounded(
                core, S58_WILD_FISHING_OWNER,
                info, rod, 0U, 0U).result;
            if (generated == 0U) {
                fprintf(stderr, "fishing RNG owner rejected rod=%u roll=%u"
                        " seed=%08" PRIx32 "\n", rod, roll, seed);
                goto failure;
            }
            uint16_t species = (uint16_t)call_bounded(
                core, BATTLE_CORE_GET_MON_DATA, QOL_ENEMY_PARTY,
                QOL_MON_DATA_SPECIES, 0U, 0U).result;
            if (species == 0U || species > 10U) {
                fprintf(stderr, "fishing RNG species invalid rod=%u roll=%u"
                        " generated=%" PRIu32 " species=%u\n",
                        rod, roll, generated, species);
                goto failure;
            }
            unsigned selected = species - 1U;
            if (selected < starts[rod] || selected >= ends[rod]) {
                fprintf(stderr, "fishing RNG tier leak rod=%u roll=%u"
                        " selected=%u\n", rod, roll, selected);
                goto failure;
            }
            ++counts[rod][selected];
            ++result->fishing_rng_samples;
        }
    }
    result->fishing_rng_boundaries =
        counts[0][0] == 70U && counts[0][1] == 30U
        && counts[1][2] == 60U && counts[1][3] == 20U
        && counts[1][4] == 20U
        && counts[2][5] == 40U && counts[2][6] == 40U
        && counts[2][7] == 15U && counts[2][8] == 4U
        && counts[2][9] == 1U
        && result->fishing_rng_samples == 300U;
    if (!result->fishing_rng_boundaries)
        fprintf(stderr, "fishing RNG counts old=%u/%u good=%u/%u/%u"
                " super=%u/%u/%u/%u/%u samples=%u\n",
                counts[0][0], counts[0][1], counts[1][2], counts[1][3],
                counts[1][4], counts[2][5], counts[2][6], counts[2][7],
                counts[2][8], counts[2][9], result->fishing_rng_samples);
    if (!core->loadState(core, state))
        result->fishing_rng_boundaries = false;
    free(state);
    return result->fishing_rng_boundaries;

failure:
    (void)core->loadState(core, state);
    free(state);
    return false;
}

static uint32_t s58_call_synced(struct mCore *core, uint32_t function,
                                uint32_t r0, uint32_t r1,
                                uint32_t r2, uint32_t r3);
static bool s58_warp(struct mCore *core, uint8_t group, uint8_t map,
                     uint16_t x, uint16_t y);
static uint32_t s58_item_quantity(struct mCore *core, uint16_t item);

static bool s58_sync_host_call_pc(struct mCore *core)
{
    /* libmGBA runFrame may yield exactly on the GBA IRQ vector (0x18/0x20).
     * A host trampoline must never preserve that transient PC as its return
     * continuation.  Advance released-key frames until ordinary ROM code owns
     * the CPU; this changes no game result and closes a runner-only soft-reset
     * path observed after short native event scripts. */
    for (unsigned frame = 0U; frame < 120U; ++frame) {
        if (s58_rom_pointer((uint32_t)read_register(core, "pc")))
            return true;
        run_key_frames(core, 0U, 1U);
    }
    return false;
}

static uint32_t s58_call_scheduler_safe(struct mCore *core,
                                        uint32_t function,
                                        uint32_t r0, uint32_t r1,
                                        uint32_t r2, uint32_t r3)
{
    if (!s58_sync_host_call_pc(core))
        s58_die("host ROM call前scheduler PC同期失敗");
    uint32_t resume_pc = (uint32_t)read_register(core, "pc");
    uint32_t resume_cpsr = (uint32_t)read_register(core, "cpsr");
    uint32_t pipeline = (resume_cpsr & 0x20U) ? 2U : 4U;
    uint32_t result = call_bounded(core, function, r0, r1, r2, r3).result;
    if ((uint32_t)read_register(core, "pc") != resume_pc) {
        write_register(core, "pc", resume_pc - pipeline);
        if ((uint32_t)read_register(core, "pc") != resume_pc)
            s58_die("wild owner call後scheduler PC復元失敗");
    }
    run_key_frames(core, 0U, 1U);
    return result;
}

static bool s58_wild_generated_matches_info(struct mCore *core,
                                             uint32_t info,
                                             unsigned slot_count,
                                             uint16_t species,
                                             uint8_t level)
{
    uint32_t slots = read32(core, info + 4U);
    if (!s58_rom_pointer(info) || !s58_rom_pointer(slots)
        || species == 0U || level == 0U)
        return false;
    for (unsigned slot = 0U; slot < slot_count; ++slot) {
        uint32_t row = slots + slot * 4U;
        uint8_t low = read8(core, row);
        uint8_t high = read8(core, row + 1U);
        if (read16(core, row + 2U) == species
            && level >= (low < high ? low : high)
            && level <= (low < high ? high : low))
            return true;
    }
    return false;
}

struct S58MapRom {
    uint32_t header;
    uint32_t layout;
    uint32_t events;
    uint32_t blocks;
    uint32_t primary_attributes;
    uint32_t secondary_attributes;
    uint32_t width;
    uint32_t height;
};

static bool s58_map_rom(struct mCore *core,
                        const struct Stage58Cases *cases,
                        uint8_t group, uint8_t map,
                        struct S58MapRom *result)
{
    memset(result, 0, sizeof(*result));
    uint32_t group_table = read32(core, cases->map_groups_root
                                 + (uint32_t)group * 4U);
    result->header = s58_rom_pointer(group_table)
        ? read32(core, group_table + (uint32_t)map * 4U) : 0U;
    result->layout = s58_rom_pointer(result->header)
        ? read32(core, result->header) : 0U;
    result->events = s58_rom_pointer(result->header)
        ? read32(core, result->header + 4U) : 0U;
    if (!s58_rom_pointer(result->layout)
        || !s58_rom_pointer(result->events))
        return false;
    result->width = read32(core, result->layout);
    result->height = read32(core, result->layout + 4U);
    result->blocks = read32(core, result->layout + 12U);
    uint32_t primary = read32(core, result->layout + 16U);
    uint32_t secondary = read32(core, result->layout + 20U);
    result->primary_attributes = s58_rom_pointer(primary)
        ? read32(core, primary + 20U) : 0U;
    result->secondary_attributes = s58_rom_pointer(secondary)
        ? read32(core, secondary + 20U) : 0U;
    return result->width != 0U && result->height != 0U
        && result->width <= 1024U && result->height <= 1024U
        && s58_rom_pointer(result->blocks)
        && s58_rom_pointer(result->primary_attributes)
        && s58_rom_pointer(result->secondary_attributes);
}

static uint32_t s58_map_attributes(struct mCore *core,
                                   const struct S58MapRom *map,
                                   uint16_t x, uint16_t y)
{
    if (x >= map->width || y >= map->height)
        return UINT32_MAX;
    uint16_t block = read16(core, map->blocks
                            + 2U * ((uint32_t)y * map->width + x));
    unsigned metatile = block & 0x03FFU;
    uint32_t attributes = metatile < 640U
        ? map->primary_attributes + metatile * 4U
        : map->secondary_attributes + (metatile - 640U) * 4U;
    return read32(core, attributes);
}

static bool s58_map_passable(struct mCore *core,
                             const struct S58MapRom *map,
                             uint16_t x, uint16_t y)
{
    if (x >= map->width || y >= map->height)
        return false;
    uint16_t block = read16(core, map->blocks
                            + 2U * ((uint32_t)y * map->width + x));
    return ((block >> 10U) & 3U) == 0U;
}

static bool s58_map_event_tile(struct mCore *core, uint32_t events,
                               uint16_t x, uint16_t y)
{
    if (!s58_rom_pointer(events))
        return true;
    const uint8_t counts[4] = {
        read8(core, events), read8(core, events + 1U),
        read8(core, events + 2U), read8(core, events + 3U),
    };
    const uint32_t roots[4] = {
        read32(core, events + 4U), read32(core, events + 8U),
        read32(core, events + 12U), read32(core, events + 16U),
    };
    const unsigned strides[4] = {24U, 8U, 16U, 12U};
    for (unsigned kind = 0U; kind < 4U; ++kind) {
        if (counts[kind] != 0U && !s58_rom_pointer(roots[kind]))
            return true;
        for (unsigned index = 0U; index < counts[kind]; ++index) {
            uint32_t row = roots[kind] + index * strides[kind];
            unsigned offset = kind == 0U ? 4U : 0U;
            if (read16(core, row + offset) == x
                && read16(core, row + offset + 2U) == y)
                return true;
        }
    }
    return false;
}

static bool s58_find_land_pair(struct mCore *core,
                               const struct Stage58Cases *cases,
                               uint8_t group, uint8_t map,
                               uint16_t *x, uint16_t *y,
                               uint16_t *behavior)
{
    struct S58MapRom rom;
    if (!s58_map_rom(core, cases, group, map, &rom))
        return false;
    for (uint16_t row = 1U; row + 1U < rom.height; ++row) {
        for (uint16_t column = 1U; column + 2U < rom.width; ++column) {
            uint32_t first = s58_map_attributes(core, &rom, column, row);
            uint32_t second = s58_map_attributes(core, &rom, column + 1U, row);
            if (((first >> 24U) & 7U) == S58_ENCOUNTER_LAND
                && ((second >> 24U) & 7U) == S58_ENCOUNTER_LAND
                && s58_map_passable(core, &rom, column, row)
                && s58_map_passable(core, &rom, column + 1U, row)
                && !s58_map_event_tile(core, rom.events, column, row)
                && !s58_map_event_tile(core, rom.events, column + 1U, row)) {
                *x = column;
                *y = row;
                *behavior = (uint16_t)(first & 0x1FFU);
                return true;
            }
        }
    }
    return false;
}

static bool s58_wild_battle_ready(struct mCore *core,
                                  uint16_t *species, uint8_t *level)
{
    uint32_t enemy = ADDR_BATTLE_MONS + BATTLE_MON_SIZE;
    bool battle_callback_seen = false;
    unsigned callback_frames = 0U;
    for (unsigned frame = 0U; frame < 2400U; frame += 15U) {
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58_CB2_OVERWORLD) {
            battle_callback_seen = true;
            callback_frames += 15U;
        }
        *species = read16(core, enemy);
        *level = read8(core, enemy + BATTLE_CORE_MON_LEVEL);
        /* gBattleMons and the battle heap are intentionally retained for a
         * short teardown window.  Require a fresh non-field callback and let
         * its initializer own 120 frames before accepting those globals. */
        if (battle_callback_seen && callback_frames >= 120U
            && read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U
            && read8(core, ADDR_BATTLERS_COUNT) >= 2U
            && read16(core, enemy + BATTLE_CORE_MON_HP) != 0U
            && *species != 0U && *level != 0U)
            return true;
        run_key_frames(core, 0U, 15U);
    }
    return false;
}

static bool s58_wild_flee(struct mCore *core)
{
    bool battle_seen = false;
    for (unsigned pulse = 0U; pulse < 1200U; ++pulse) {
        if (read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U
            || read8(core, ADDR_BATTLERS_COUNT) != 0U)
            battle_seen = true;
        if (battle_seen
            && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S58_CB2_OVERWORLD
            && read8(core, S58_FIELD_LOCK) == 0U) {
            run_key_frames(core, 0U, 120U);
            return read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                == S58_CB2_OVERWORLD && read8(core, S58_FIELD_LOCK) == 0U;
        }
        if (pulse % 5U == 0U) {
            qol_press(core, S58_KEY_RIGHT, 16U);
            qol_press(core, S58_KEY_DOWN, 16U);
        }
        qol_press(core, QOL_KEY_A, BATTLE_CORE_MENU_INPUT_WAIT);
        if (pulse % 7U == 6U)
            qol_press(core, QOL_KEY_B, 30U);
    }
    return false;
}

static bool s58_walk_step(struct mCore *core, uint16_t key,
                          uint16_t *x, uint16_t *y)
{
    uint16_t start_x = *x, start_y = *y;
    bool changed = false;
    for (unsigned frame = 0U; frame < 40U; ++frame) {
        run_key_frames(core, key, 1U);
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58_CB2_OVERWORLD) {
            core->setKeys(core, 0U);
            return false;
        }
        uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
        if (!s58_ewram_pointer(save1))
            return false;
        *x = read16(core, save1);
        *y = read16(core, save1 + 2U);
        changed = *x != start_x || *y != start_y;
        if (changed
            && read8(core, S58_PLAYER_AVATAR
                           + S58_PLAYER_RUNNING_STATE_OFFSET)
                == S58_PLAYER_MOVING
            && read8(core, S58_PLAYER_AVATAR
                           + S58_PLAYER_TILE_TRANSITION_STATE_OFFSET)
                == S58_PLAYER_TILE_CENTER) {
            core->setKeys(core, 0U);
            run_key_frames(core, 0U, 45U);
            return read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                == S58_CB2_OVERWORLD;
        }
    }
    core->setKeys(core, 0U);
    run_key_frames(core, 0U, 4U);
    return false;
}

static bool s58_wild_natural_land(struct mCore *core,
                                  const struct Stage58Cases *cases,
                                  uint8_t group, uint8_t map, uint32_t info,
                                  struct S58WildRuntimeResult *result)
{
    uint16_t x = 0U, y = 0U, behavior = 0U;
    if (!s58_find_land_pair(core, cases, group, map, &x, &y, &behavior)
        || !s58_warp(core, group, map, x, y))
        return false;
    uint16_t species = 0U;
    uint8_t level = 0U;
    uint16_t key = S58_KEY_RIGHT;
    for (unsigned attempt = 0U; attempt < 600U; ++attempt) {
        bool moved = s58_walk_step(core, key, &x, &y);
        if (!moved
            && read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58_CB2_OVERWORLD) {
            if (!s58_wild_battle_ready(core, &species, &level))
                return false;
            break;
        }
        key = key == S58_KEY_RIGHT ? S58_KEY_LEFT : S58_KEY_RIGHT;
    }
    if (!s58_wild_generated_matches_info(core, info, 12U, species, level)
        || !s58_wild_flee(core))
        return false;
    unsigned slot = result->evidence_count++;
    result->evidence[slot].method = "land";
    result->evidence[slot].group = group;
    result->evidence[slot].map = map;
    result->evidence[slot].x = x;
    result->evidence[slot].y = y;
    result->evidence[slot].behavior = behavior;
    result->evidence[slot].facing = key;
    result->evidence[slot].species = species;
    result->evidence[slot].level = level;
    snprintf(result->evidence[slot].source_key,
             sizeof(result->evidence[slot].source_key),
             "KANTO_WILD_%u_%u_land", group, map);
    return true;
}

static bool s58_surfable_behavior(uint16_t behavior)
{
    return behavior == 0x10U || behavior == 0x12U
        || behavior == 0x15U || behavior == 0x1AU
        || behavior == 0x1BU
        || (behavior >= 0x50U && behavior <= 0x53U);
}

struct S58WaterEdge {
    uint16_t land_x;
    uint16_t land_y;
    uint16_t water_x;
    uint16_t water_y;
    uint16_t next_x;
    uint16_t next_y;
    uint16_t face_key;
    uint16_t next_key;
    uint16_t behavior;
};

static bool s58_find_water_edge(struct mCore *core,
                                const struct Stage58Cases *cases,
                                uint8_t group, uint8_t map,
                                struct S58WaterEdge *edge)
{
    struct S58MapRom rom;
    if (!s58_map_rom(core, cases, group, map, &rom))
        return false;
    static const int8_t offsets[4][2] = {
        {0, -1}, {1, 0}, {0, 1}, {-1, 0},
    };
    static const uint16_t keys[4] = {
        S58_KEY_UP, S58_KEY_RIGHT, S58_KEY_DOWN, S58_KEY_LEFT,
    };
    for (uint16_t y = 1U; y + 1U < rom.height; ++y) {
        for (uint16_t x = 1U; x + 1U < rom.width; ++x) {
            uint32_t land_attrs = s58_map_attributes(core, &rom, x, y);
            if (!s58_map_passable(core, &rom, x, y)
                || ((land_attrs >> 24U) & 7U) != 0U
                || s58_map_event_tile(core, rom.events, x, y))
                continue;
            for (unsigned direction = 0U; direction < 4U; ++direction) {
                uint16_t wx = (uint16_t)((int32_t)x + offsets[direction][0]);
                uint16_t wy = (uint16_t)((int32_t)y + offsets[direction][1]);
                uint32_t water_attrs = s58_map_attributes(core, &rom, wx, wy);
                uint16_t behavior = (uint16_t)(water_attrs & 0x1FFU);
                if (((water_attrs >> 24U) & 7U) != S58_ENCOUNTER_WATER
                    || !s58_surfable_behavior(behavior)
                    || s58_map_event_tile(core, rom.events, wx, wy))
                    continue;
                for (unsigned next = 0U; next < 4U; ++next) {
                    uint16_t nx = (uint16_t)((int32_t)wx + offsets[next][0]);
                    uint16_t ny = (uint16_t)((int32_t)wy + offsets[next][1]);
                    uint32_t next_attrs = s58_map_attributes(
                        core, &rom, nx, ny);
                    if (((next_attrs >> 24U) & 7U) == S58_ENCOUNTER_WATER
                        && s58_surfable_behavior(
                            (uint16_t)(next_attrs & 0x1FFU))
                        && !s58_map_event_tile(core, rom.events, nx, ny)) {
                        edge->land_x = x;
                        edge->land_y = y;
                        edge->water_x = wx;
                        edge->water_y = wy;
                        edge->next_x = nx;
                        edge->next_y = ny;
                        edge->face_key = keys[direction];
                        edge->next_key = keys[next];
                        edge->behavior = behavior;
                        return true;
                    }
                }
            }
        }
    }
    return false;
}

static bool s58_prepare_field_move(struct mCore *core, uint16_t move,
                                   uint16_t badge)
{
    if (read8(core, S58_PLAYER_COUNT) == 0U)
        create_mon(core, S58_PLAYER_MON, 25U, 50U);
    write8(core, S58_PLAYER_COUNT, 1U);
    qol_set_mon_data(core, S58_PLAYER_MON,
                     S58_MON_DATA_MOVE1, move, 2U);
    /* FlagSet is void in stock FireRed; its r0 value is not a success result.
     * Read the native flag owner back after a released scheduler frame. */
    (void)s58_call_synced(core, QOL_FLAG_SET, badge, 0U, 0U, 0U);
    run_key_frames(core, 0U, 30U);
    return s58_call_synced(
        core, QOL_FLAG_GET, badge, 0U, 0U, 0U) == 1U;
}

static bool s58_wild_natural_water(struct mCore *core,
                                   const struct Stage58Cases *cases,
                                   uint8_t group, uint8_t map, uint32_t info,
                                   struct S58WildRuntimeResult *result)
{
    struct S58WaterEdge edge = {0};
    if (!s58_find_water_edge(core, cases, group, map, &edge)) {
        fprintf(stderr, "wild water: ROM上のland-water-water辺がない"
                " map=%u/%u\n", group, map);
        return false;
    }
    if (!s58_warp(core, group, map, edge.land_x, edge.land_y)) {
        fprintf(stderr, "wild water: warp失敗 map=%u/%u land=%u,%u\n",
                group, map, edge.land_x, edge.land_y);
        return false;
    }
    if (!s58_prepare_field_move(
            core, S58_MOVE_SURF, S58_FLAG_BADGE05)) {
        fprintf(stderr, "wild water: Surf/flag fixture失敗 move=%u flag=%04x\n",
                S58_MOVE_SURF, S58_FLAG_BADGE05);
        return false;
    }
    qol_press(core, edge.face_key, 12U);
    qol_press(core, QOL_KEY_A, 90U);
    for (unsigned confirm = 0U; confirm < 8U; ++confirm) {
        uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
        if (s58_ewram_pointer(save1)
            && read16(core, save1) == edge.water_x
            && read16(core, save1 + 2U) == edge.water_y)
            break;
        qol_press(core, QOL_KEY_A, 120U);
    }
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    if (!s58_ewram_pointer(save1)
        || read16(core, save1) != edge.water_x
        || read16(core, save1 + 2U) != edge.water_y) {
        fprintf(stderr, "wild water: 通常Surf後座標不一致 map=%u/%u"
                " land=%u,%u water=%u,%u got=%u,%u behavior=%03x"
                " facing=%04x cb=%08" PRIx32 " lock=%u avatar=%02x/%u/%u\n",
                group, map, edge.land_x, edge.land_y,
                edge.water_x, edge.water_y,
                s58_ewram_pointer(save1) ? read16(core, save1) : 0U,
                s58_ewram_pointer(save1) ? read16(core, save1 + 2U) : 0U,
                edge.behavior, edge.face_key,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, S58_FIELD_LOCK), read8(core, S58_PLAYER_AVATAR),
                read8(core, S58_PLAYER_AVATAR + 2U),
                read8(core, S58_PLAYER_AVATAR + 3U));
        return false;
    }
    uint16_t x = edge.water_x, y = edge.water_y;
    uint16_t key = edge.next_key;
    uint16_t species = 0U;
    uint8_t level = 0U;
    for (unsigned attempt = 0U; attempt < 1000U; ++attempt) {
        bool moved = s58_walk_step(core, key, &x, &y);
        if (!moved
            && read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58_CB2_OVERWORLD) {
            if (!s58_wild_battle_ready(core, &species, &level)) {
                fprintf(stderr, "wild water: battle遷移後生成mon未確定"
                        " cb=%08" PRIx32 " ptr=%08" PRIx32 " battlers=%u\n",
                        read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                        read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
                        read8(core, ADDR_BATTLERS_COUNT));
                return false;
            }
            break;
        }
        key = key == edge.next_key
            ? (edge.next_key == S58_KEY_RIGHT ? S58_KEY_LEFT
               : edge.next_key == S58_KEY_LEFT ? S58_KEY_RIGHT
               : edge.next_key == S58_KEY_UP ? S58_KEY_DOWN : S58_KEY_UP)
            : edge.next_key;
    }
    if (!s58_wild_generated_matches_info(core, info, 5U, species, level)) {
        fprintf(stderr, "wild water: species/level slot不一致"
                " species=%u level=%u\n", species, level);
        return false;
    }
    if (!s58_wild_flee(core)) {
        fprintf(stderr, "wild water: 通常逃走/field復帰失敗"
                " species=%u level=%u cb=%08" PRIx32 "\n",
                species, level, read32(core, BATTLE_CORE_MAIN_CALLBACK2));
        return false;
    }
    unsigned slot = result->evidence_count++;
    result->evidence[slot].method = "water";
    result->evidence[slot].group = group;
    result->evidence[slot].map = map;
    result->evidence[slot].x = edge.water_x;
    result->evidence[slot].y = edge.water_y;
    result->evidence[slot].behavior = edge.behavior;
    result->evidence[slot].facing = edge.face_key;
    result->evidence[slot].required_item_or_move = S58_MOVE_SURF;
    result->evidence[slot].species = species;
    result->evidence[slot].level = level;
    snprintf(result->evidence[slot].source_key,
             sizeof(result->evidence[slot].source_key),
             "KANTO_WILD_%u_%u_water", group, map);
    return true;
}

static bool s58_wild_natural_fishing(struct mCore *core,
                                     const struct Stage58Cases *cases,
                                     uint8_t group, uint8_t map,
                                     uint32_t info, unsigned rod,
                                     struct S58WildRuntimeResult *result)
{
    static const uint16_t rods[3] = {
        S58_ITEM_OLD_ROD, S58_ITEM_GOOD_ROD, S58_ITEM_SUPER_ROD,
    };
    static const char *const methods[3] = {
        "fishing_old", "fishing_good", "fishing_super",
    };
    if (rod >= 3U)
        return false;
    struct S58WaterEdge edge = {0};
    if (!s58_find_water_edge(core, cases, group, map, &edge)) {
        fprintf(stderr, "wild fishing: ROM上のfishable water辺がない"
                " rod=%u map=%u/%u\n", rod, group, map);
        return false;
    }
    uint16_t species = 0U;
    uint8_t level = 0U;
    if (!s58_warp(core, group, map, edge.land_x, edge.land_y)) {
        fprintf(stderr, "wild fishing: warp失敗 rod=%u\n", rod);
        return false;
    }
    if (s58_item_quantity(core, rods[rod]) == 0U
        && s58_call_synced(core, S58_ADD_BAG_ITEM,
                           rods[rod], 1U, 0U, 0U) == 0U) {
        fprintf(stderr, "wild fishing: rod fixture失敗 rod=%u item=%u\n",
                rod, rods[rod]);
        return false;
    }
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    if (!s58_ewram_pointer(save1))
        return false;
    write16(core, save1 + S58_REGISTERED_ITEM_OFFSET, rods[rod]);
    run_key_frames(core, 0U, 30U);
    for (unsigned attempt = 0U; attempt < 24U && species == 0U; ++attempt) {
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58_CB2_OVERWORLD
            || read8(core, S58_FIELD_LOCK) != 0U) {
            fprintf(stderr, "wild fishing: retry前field不安定"
                    " rod=%u attempt=%u cb=%08" PRIx32 " lock=%u\n",
                    rod, attempt,
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                    read8(core, S58_FIELD_LOCK));
            return false;
        }
        qol_press(core, edge.face_key, 12U);
        qol_press(core, QOL_KEY_SELECT, 4U);
        bool script_seen = false;
        unsigned unlocked_frames = 0U;
        for (unsigned reaction = 0U; reaction < 2400U; ++reaction) {
            if (read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                != S58_CB2_OVERWORLD)
                break;
            uint8_t locked = read8(core, S58_FIELD_LOCK);
            if (locked != 0U) {
                script_seen = true;
                unlocked_frames = 0U;
            } else if (script_seen) {
                ++unlocked_frames;
            }
            /* A fishing task can release its script context shortly before
             * StartWildBattle changes callback2.  A single unlocked frame is
             * therefore not a "no bite" result; require five seconds of
             * continuously ordinary field ownership. */
            if (unlocked_frames >= 300U)
                break;
            if (locked != 0U && reaction % 12U == 0U)
                qol_press(core, QOL_KEY_A, 4U);
            else
                run_key_frames(core, 0U, 1U);
        }
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58_CB2_OVERWORLD) {
            if (!s58_wild_battle_ready(core, &species, &level)) {
                fprintf(stderr, "wild fishing: battle遷移後生成mon未確定"
                        " rod=%u attempt=%u cb=%08" PRIx32 "\n",
                        rod, attempt,
                        read32(core, BATTLE_CORE_MAIN_CALLBACK2));
                return false;
            }
        } else {
            run_key_frames(core, 0U, 30U);
        }
    }
    unsigned slot_count = rod == 0U ? 2U : rod == 1U ? 3U : 5U;
    unsigned slot_start = rod == 0U ? 0U : rod == 1U ? 2U : 5U;
    uint32_t rooted_slots = read32(core, info + 4U);
    bool matched = false;
    for (unsigned index = 0U; index < slot_count; ++index) {
        uint32_t row = rooted_slots + (slot_start + index) * 4U;
        uint8_t low = read8(core, row), high = read8(core, row + 1U);
        if (read16(core, row + 2U) == species
            && level >= (low < high ? low : high)
            && level <= (low < high ? high : low))
            matched = true;
    }
    if (!matched) {
        fprintf(stderr, "wild fishing: rod tier slot不一致"
                " rod=%u species=%u level=%u start=%u count=%u\n",
                rod, species, level, slot_start, slot_count);
        return false;
    }
    if (!s58_wild_flee(core)) {
        fprintf(stderr, "wild fishing: 通常逃走/field復帰失敗"
                " rod=%u species=%u level=%u cb=%08" PRIx32 "\n",
                rod, species, level,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2));
        return false;
    }
    unsigned slot = result->evidence_count++;
    result->evidence[slot].method = methods[rod];
    result->evidence[slot].group = group;
    result->evidence[slot].map = map;
    result->evidence[slot].x = edge.land_x;
    result->evidence[slot].y = edge.land_y;
    result->evidence[slot].behavior = edge.behavior;
    result->evidence[slot].facing = edge.face_key;
    result->evidence[slot].required_item_or_move = rods[rod];
    result->evidence[slot].species = species;
    result->evidence[slot].level = level;
    snprintf(result->evidence[slot].source_key,
             sizeof(result->evidence[slot].source_key),
             "KANTO_WILD_%u_%u_%s", group, map, methods[rod]);
    return true;
}

static bool s58_find_rock_object(struct mCore *core,
                                 const struct Stage58Cases *cases,
                                 uint8_t group, uint8_t map,
                                 struct HubObject *object,
                                 uint16_t *stand_x, uint16_t *stand_y,
                                 uint16_t *behavior)
{
    struct S58MapRom rom;
    if (!s58_map_rom(core, cases, group, map, &rom))
        return false;
    uint8_t count = read8(core, rom.events);
    uint32_t objects = read32(core, rom.events + 4U);
    if (count == 0U || !s58_rom_pointer(objects))
        return false;
    static const int8_t offsets[4][2] = {
        {0, -1}, {1, 0}, {0, 1}, {-1, 0},
    };
    for (unsigned index = 0U; index < count; ++index) {
        uint32_t row = objects + index * 24U;
        if (read32(core, row + 16U) != S58_ROCK_SMASH_SCRIPT)
            continue;
        uint16_t x = read16(core, row + 4U);
        uint16_t y = read16(core, row + 6U);
        for (unsigned direction = 0U; direction < 4U; ++direction) {
            int32_t sx = (int32_t)x + offsets[direction][0];
            int32_t sy = (int32_t)y + offsets[direction][1];
            if (sx < 0 || sy < 0 || (uint32_t)sx >= rom.width
                || (uint32_t)sy >= rom.height
                || !s58_map_passable(core, &rom, (uint16_t)sx, (uint16_t)sy)
                || s58_map_event_tile(
                    core, rom.events, (uint16_t)sx, (uint16_t)sy))
                continue;
            object->local_id = read8(core, row);
            object->graphics_id = read8(core, row + 1U);
            object->x = x;
            object->y = y;
            object->script = read32(core, row + 16U);
            *stand_x = (uint16_t)sx;
            *stand_y = (uint16_t)sy;
            *behavior = (uint16_t)(
                s58_map_attributes(core, &rom, x, y) & 0x1FFU);
            return true;
        }
    }
    return false;
}

static bool s58_wild_natural_rock(struct mCore *core,
                                  const struct Stage58Cases *cases,
                                  uint8_t group, uint8_t map, uint32_t info,
                                  struct S58WildRuntimeResult *result)
{
    struct HubObject rock = {0};
    uint16_t stand_x = 0U, stand_y = 0U, behavior = 0U;
    if (!s58_find_rock_object(core, cases, group, map, &rock,
                              &stand_x, &stand_y, &behavior))
        return false;
    uint16_t species = 0U;
    uint8_t level = 0U;
    for (unsigned attempt = 0U; attempt < 48U && species == 0U; ++attempt) {
        /* removeobject sets a temporary local-id flag for the loaded map.
         * Leave the map between trials so the next trial again owns a real
         * rock object; directly clearing that flag would fake the field path. */
        if (attempt != 0U
            && !s58_warp(core, (uint8_t)cases->hub.group,
                         (uint8_t)cases->hub.map,
                         (uint16_t)cases->hub.pc.x,
                         (uint16_t)(cases->hub.pc.y + 1U))) {
            fprintf(stderr, "wild rock: trial間map離脱失敗 attempt=%u\n",
                    attempt);
            return false;
        }
        if (!s58_warp(core, group, map, stand_x, stand_y)) {
            fprintf(stderr, "wild rock: warp失敗 attempt=%u map=%u/%u"
                    " stand=%u,%u\n", attempt, group, map,
                    stand_x, stand_y);
            return false;
        }
        if (!s58_prepare_field_move(
                core, S58_MOVE_ROCK_SMASH, S58_FLAG_BADGE06)) {
            fprintf(stderr, "wild rock: Rock Smash/flag fixture失敗"
                    " attempt=%u\n", attempt);
            return false;
        }
        if (!s58_face_and_interact(core, &rock)) {
            fprintf(stderr, "wild rock: 通常A対象rock不在 attempt=%u"
                    " local=%u object_active=%08" PRIx32 "\n",
                    attempt, rock.local_id,
                    s58_active_local(core, (uint8_t)rock.local_id));
            return false;
        }
        for (unsigned input = 0U; input < 80U; ++input) {
            if (read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                != S58_CB2_OVERWORLD)
                break;
            if (input % 4U == 0U)
                qol_press(core, QOL_KEY_A, 30U);
            else
                run_key_frames(core, 0U, 1U);
        }
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58_CB2_OVERWORLD) {
            if (!s58_wild_battle_ready(core, &species, &level)) {
                fprintf(stderr, "wild rock: battle遷移後生成mon未確定"
                        " attempt=%u\n", attempt);
                return false;
            }
        } else {
            for (unsigned clear = 0U; clear < 4U; ++clear)
                qol_press(core, QOL_KEY_B, 60U);
        }
    }
    if (!s58_wild_generated_matches_info(core, info, 5U, species, level)) {
        fprintf(stderr, "wild rock: 48 trialsでslot一致遭遇なし"
                " species=%u level=%u\n", species, level);
        return false;
    }
    if (!s58_wild_flee(core)) {
        fprintf(stderr, "wild rock: 通常逃走/field復帰失敗"
                " species=%u level=%u cb=%08" PRIx32 "\n",
                species, level, read32(core, BATTLE_CORE_MAIN_CALLBACK2));
        return false;
    }
    unsigned slot = result->evidence_count++;
    result->evidence[slot].method = "rock";
    result->evidence[slot].group = group;
    result->evidence[slot].map = map;
    result->evidence[slot].x = stand_x;
    result->evidence[slot].y = stand_y;
    result->evidence[slot].behavior = behavior;
    result->evidence[slot].required_item_or_move = S58_MOVE_ROCK_SMASH;
    result->evidence[slot].species = species;
    result->evidence[slot].level = level;
    snprintf(result->evidence[slot].source_key,
             sizeof(result->evidence[slot].source_key),
             "KANTO_WILD_%u_%u_rock", group, map);
    return true;
}

static bool s58_wild_runtime_one(struct mCore *core,
                                 const struct Stage58Cases *cases,
                                 uint8_t group, uint8_t map, uint32_t info,
                                 unsigned mode, uint8_t expected_rate,
                                 struct S58WildRuntimeResult *result)
{
    static const unsigned slot_counts[4] = {12U, 5U, 5U, 10U};
    if (mode >= ARRAY_LEN(slot_counts) || !s58_rom_pointer(info)
        || read8(core, info) != expected_rate)
        return false;
    if (mode == S58_WILD_AREA_LAND)
        return s58_wild_natural_land(
            core, cases, group, map, info, result);
    if (mode == S58_WILD_AREA_WATER)
        return s58_wild_natural_water(
            core, cases, group, map, info, result);
    if (mode == S58_WILD_AREA_ROCK)
        return s58_wild_natural_rock(
            core, cases, group, map, info, result);
    if (mode == 3U)
        return s58_wild_natural_fishing(
                core, cases, group, map, info, 0U, result)
            && s58_wild_natural_fishing(
                core, cases, group, map, info, 1U, result)
            && s58_wild_natural_fishing(
                core, cases, group, map, info, 2U, result);
    return false;
}

static bool s58_find_runtime_mode(struct mCore *core,
                                  const struct Stage58Cases *cases,
                                  unsigned mode, uint8_t *group_out,
                                  uint8_t *map_out, uint32_t *info_out)
{
    for (unsigned index = 0U; index < S58_WILD_HEADER_LIMIT; ++index) {
        uint32_t row = cases->wild_headers_root + index * 20U;
        uint8_t group = read8(core, row);
        uint8_t map = read8(core, row + 1U);
        if (group == 0xFFU && map == 0xFFU)
            break;
        /* Stage58's rebuilt Kanto ownership begins at imported groups 96/97.
         * Do not let an older Vega row satisfy this domain. */
        if (group < 96U)
            continue;
        uint32_t info = read32(core, row + 4U + mode * 4U);
        if (s58_rom_pointer(info)) {
            *group_out = group;
            *map_out = map;
            *info_out = info;
            return true;
        }
    }
    return false;
}

static bool s58_wild_runtime_path(struct mCore *core,
                                  const struct Stage58Cases *cases,
                                  struct S58WildRuntimeResult *result)
{
    if (!s58_fishing_rng_boundary_audit(core, result))
        return false;
    const uint8_t rates[4] = {
        S58_WILD_RATE_LAND, S58_WILD_RATE_WATER,
        S58_WILD_RATE_ROCK, S58_WILD_RATE_FISHING,
    };
    bool *outputs[4] = {
        &result->land, &result->water, &result->rock, &result->fishing,
    };
    for (unsigned mode = 0U; mode < 4U; ++mode) {
        uint8_t group = 0U, map = 0U;
        uint32_t info = 0U;
        if (!s58_find_runtime_mode(
                core, cases, mode, &group, &map, &info))
            return false;
        *outputs[mode] = s58_wild_runtime_one(
            core, cases, group, map, info, mode, rates[mode], result);
        if (!*outputs[mode])
            return false;
        ++result->generated;
    }
    return result->generated == 4U && result->evidence_count == 6U
        && s58_warp(core, (uint8_t)cases->hub.group,
                    (uint8_t)cases->hub.map,
                    (uint16_t)cases->hub.pc.x,
                    (uint16_t)(cases->hub.pc.y + 1U));
}

static uint64_t s58_video_hash(void)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    for (unsigned index = 0U; index < ARRAY_LEN(s58_video); ++index) {
        uint32_t pixel = (uint32_t)s58_video[index];
        for (unsigned byte = 0U; byte < sizeof(s58_video[index]); ++byte) {
            hash ^= (uint8_t)(pixel >> (byte * 8U));
            hash *= UINT64_C(1099511628211);
        }
    }
    return hash;
}

static struct mCore *s58_open(const char *rom, const char *save,
                              bool blank_save)
{
    static struct mRTCSource rtc = {
        .sample = NULL, .unixTime = fixed_unix_time,
        .serialize = NULL, .deserialize = NULL,
    };
    if (blank_save)
        qol_initialize_save(save);
    struct mCore *core = mCoreFind(rom);
    if (!core || !core->init(core))
        s58_die("mGBA core初期化失敗");
    if (!mCoreLoadFile(core, rom) || !mCoreLoadSaveFile(core, save, false))
        s58_die("ROM/save attachment失敗");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->setVideoBuffer(core, s58_video, 240U);
    core->reset(core);
    s58_log_core = core;
    qol_log_core = core;
    if (getenv("MGBA_STAGE58_TRACE") != NULL)
        fprintf(stderr, "open reset mailbox=%08" PRIx32
                " cap=%04x request=%u/%" PRIu32
                " state=%u/%u pss=%08" PRIx32 "\n",
                read32(core, S58_MAILBOX), read16(core, S58_MAILBOX + 24U),
                read16(core, S58_CODEX_REQUEST + 10U),
                read32(core, S58_CODEX_REQUEST + 92U),
                read8(core, S58_CODEX_STATE + 20U),
                read16(core, S58_CODEX_STATE + 16U),
                read32(core, QOL_PSS_DATA));
    return core;
}

static uint32_t s58_call_synced(struct mCore *core, uint32_t function,
                                uint32_t r0, uint32_t r1,
                                uint32_t r2, uint32_t r3)
{
    if (read8(core, S58_FIELD_LOCK) != 0U)
        s58_die("script稼働中のhost ROM callは禁止");
    if (!s58_sync_host_call_pc(core))
        s58_die("host ROM call前scheduler PC同期失敗");
    uint32_t result = call_preserving(core, function, r0, r1, r2, r3);
    /* mGBA host calls execute outside the natural field scheduler.  A real
     * released-key frame is mandatory before another call or GBA input. */
    run_key_frames(core, 0U, 1U);
    return result;
}

static bool s58_warp(struct mCore *core, uint8_t group, uint8_t map,
                     uint16_t x, uint16_t y)
{
    run_key_frames(core, 0U, 2U);
    if (getenv("MGBA_STAGE58_TRACE") != NULL)
        fprintf(stderr, "warp begin wanted=%u/%u %u,%u"
                " cb=%08" PRIx32 " saved=%08" PRIx32
                " keys=%04x/%04x/%04x/%04x/%04x lock=%u pc=%08" PRIx32
                "\n", group, map, x, y,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2 + 4U),
                read16(core, 0x03003158U), read16(core, 0x0300315AU),
                read16(core, 0x0300315CU), read16(core, 0x0300315EU),
                read16(core, 0x03003160U), read8(core, S58_FIELD_LOCK),
                (uint32_t)read_register(core, "pc"));
    (void)s58_call_synced(core, S58_KANTO_WARP, group, map, x, y);
    run_key_frames(core, 0U, S58_WARP_FRAMES);
    if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58_CB2_OVERWORLD)
        run_key_frames(core, 0U, S58_WARP_FRAMES);
    if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58_CB2_OVERWORLD) {
        qol_press(core, QOL_KEY_B, 180U);
        run_key_frames(core, 0U, S58_WARP_FRAMES);
    }
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    bool passed = s58_ewram_pointer(save1)
        && read8(core, save1 + 4U) == group
        && read8(core, save1 + 5U) == map
        && read16(core, save1) == x && read16(core, save1 + 2U) == y
        && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S58_CB2_OVERWORLD
        && read8(core, S58_FIELD_LOCK) == 0U;
    if (!passed)
        fprintf(stderr, "warp debug save=%08" PRIx32
                " wanted=%u/%u %u,%u got=%u/%u %u,%u cb=%08" PRIx32
                " script=%" PRIu32 "\n", save1, group, map, x, y,
                s58_ewram_pointer(save1) ? read8(core, save1 + 4U) : 0U,
                s58_ewram_pointer(save1) ? read8(core, save1 + 5U) : 0U,
                s58_ewram_pointer(save1) ? read16(core, save1) : 0U,
                s58_ewram_pointer(save1) ? read16(core, save1 + 2U) : 0U,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                (uint32_t)read8(core, S58_FIELD_LOCK));
    if (!passed)
        fprintf(stderr, "warp failure state saved=%08" PRIx32
                " keys=%04x/%04x/%04x/%04x/%04x pc=%08" PRIx32
                " pss=%08" PRIx32 "\n",
                read32(core, BATTLE_CORE_MAIN_CALLBACK2 + 4U),
                read16(core, 0x03003158U), read16(core, 0x0300315AU),
                read16(core, 0x0300315CU), read16(core, 0x0300315EU),
                read16(core, 0x03003160U),
                (uint32_t)read_register(core, "pc"),
                read32(core, QOL_PSS_DATA));
    return passed;
}

static bool s58_prepare_map_view(struct mCore *core)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    uint32_t width = read32(core, S58_VMAP);
    uint32_t height = read32(core, S58_VMAP + 4U);
    uint32_t map = read32(core, S58_VMAP + 8U);
    if (!s58_ewram_pointer(save1) || !s58_ewram_pointer(save2)
        || !s58_ewram_pointer(map) || (map & 1U)
        || width < S58_MAP_VIEW_WIDTH || height < S58_MAP_VIEW_HEIGHT)
        return false;
    int16_t x = (int16_t)read16(core, save1);
    int16_t y = (int16_t)read16(core, save1 + 2U);
    if (x < 0 || y < 0
        || (uint32_t)x + S58_MAP_VIEW_WIDTH > width
        || (uint32_t)y + S58_MAP_VIEW_HEIGHT > height)
        return false;
    unsigned index = 0U;
    unsigned distinct = 0U;
    uint16_t values[S58_MAP_VIEW_COUNT];
    for (unsigned row = 0U; row < S58_MAP_VIEW_HEIGHT; ++row) {
        for (unsigned column = 0U; column < S58_MAP_VIEW_WIDTH; ++column) {
            uint32_t source = map + 2U * (width * ((uint32_t)y + row)
                                      + (uint32_t)x + column);
            values[index] = read16(core, source);
            write16(core, save2 + S58_MAP_VIEW_OFFSET + index * 2U,
                    values[index]);
            ++index;
        }
    }
    for (unsigned outer = 0U; outer < S58_MAP_VIEW_COUNT; ++outer) {
        bool first = true;
        for (unsigned inner = 0U; inner < outer; ++inner) {
            if (values[inner] == values[outer]) {
                first = false;
                break;
            }
        }
        if (first)
            ++distinct;
    }
    return index == S58_MAP_VIEW_COUNT && distinct >= 8U;
}

static bool s58_hub_position(struct mCore *core,
                             const struct Stage58Cases *cases,
                             uint16_t x, uint16_t y)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    return s58_ewram_pointer(save1)
        && read8(core, save1 + 4U) == cases->hub.group
        && read8(core, save1 + 5U) == cases->hub.map
        && read16(core, save1) == x && read16(core, save1 + 2U) == y;
}

static bool s58_map_position(struct mCore *core, uint8_t group, uint8_t map,
                             uint16_t x, uint16_t y)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    return s58_ewram_pointer(save1)
        && read8(core, save1 + 4U) == group
        && read8(core, save1 + 5U) == map
        && read16(core, save1) == x && read16(core, save1 + 2U) == y
        && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S58_CB2_OVERWORLD
        && read8(core, S58_FIELD_LOCK) == 0U;
}

static bool s58_bind_bag_pockets(struct mCore *core)
{
    /* FireRed JP's five runtime descriptors are not initialized by a bare
     * Continue in every field path.  Saving with an unbound descriptor table
     * rotates the quantity key without re-encrypting that pocket. */
    static const uint8_t capacities[5] = {42U, 30U, 13U, 58U, 43U};
    (void)s58_call_synced(core, S58_SET_BAG_POCKETS_POINTERS,
                          0U, 0U, 0U, 0U);
    for (unsigned pocket = 0U; pocket < ARRAY_LEN(capacities); ++pocket) {
        uint32_t descriptor = S58_BAG_POCKETS + pocket * 8U;
        uint32_t slots = read32(core, descriptor);
        if (!s58_ewram_pointer(slots) || (slots & 1U) != 0U
            || read8(core, descriptor + 4U) != capacities[pocket])
            return false;
    }
    return true;
}

static bool s58_savedata_hash(struct mCore *core, uint64_t *hash_out)
{
    void *sram = NULL;
    size_t size = core->savedataClone(core, &sram);
    if (sram == NULL || size != QOL_SAVE_SIZE) {
        if (getenv("MGBA_STAGE58_TRACE") != NULL)
            fprintf(stderr, "savedata clone invalid size=%zu ptr=%p\n",
                    size, sram);
        free(sram);
        return false;
    }
    uint64_t hash = UINT64_C(14695981039346656037);
    const uint8_t *bytes = sram;
    for (size_t index = 0U; index < size; ++index) {
        hash ^= bytes[index];
        hash *= UINT64_C(1099511628211);
    }
    free(sram);
    *hash_out = hash;
    return true;
}

static bool s58_normal_menu_save(struct mCore *core,
                                 uint64_t quest_log_before,
                                 uint64_t *quest_log_after)
{
    if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58_CB2_OVERWORLD
        || read8(core, S58_FIELD_LOCK) != 0U
        || !s58_bind_bag_pockets(core))
        return false;
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    if (!s58_ewram_pointer(save2))
        return false;
    uint64_t savedata_before = 0U;
    if (!s58_savedata_hash(core, &savedata_before))
        return false;
    qol_press(core, QOL_KEY_START, 120U);
    if (read32(core, QOL_START_MENU_CALLBACK) != QOL_START_MENU_INPUT)
        return false;
    uint8_t count = read8(core, QOL_START_MENU_COUNT);
    uint8_t cursor = read8(core, QOL_START_MENU_CURSOR);
    if (count == 0U || count > 9U || cursor >= count)
        return false;
    uint8_t target = count;
    for (uint8_t index = 0U; index < count; ++index) {
        if (read8(core, QOL_START_MENU_ORDER + index) == S58_STARTMENU_SAVE) {
            target = index;
            break;
        }
    }
    if (target >= count)
        return false;
    unsigned down = (unsigned)(target + count - cursor) % count;
    unsigned up = (unsigned)(cursor + count - target) % count;
    uint16_t key = down <= up ? QOL_KEY_DOWN : QOL_KEY_UP;
    unsigned steps = down <= up ? down : up;
    for (unsigned step = 0U; step < steps; ++step)
        qol_press(core, key, 30U);
    if (read8(core, QOL_START_MENU_CURSOR) != target
        || read8(core, QOL_START_MENU_ORDER + target)
            != S58_STARTMENU_SAVE)
        return false;
    qol_press(core, QOL_KEY_A, 120U);
    bool recorded = false;
    bool save_started = false;
    for (unsigned prompt = 0U; prompt < 32U; ++prompt) {
        uint32_t menu_callback = read32(core, QOL_START_MENU_CALLBACK);
        uint64_t savedata_now = 0U;
        bool savedata_read = s58_savedata_hash(core, &savedata_now);
        if (menu_callback == S58_STARTMENU_SAVE_CALLBACK)
            save_started = true;
        *quest_log_after = s58_quest_log_hash(core);
        if (*quest_log_after != 0U
            && (quest_log_before == 0U
                || *quest_log_after != quest_log_before))
            recorded = true;
        if (getenv("MGBA_STAGE58_TRACE") != NULL)
            fprintf(stderr, "normal save prompt=%u menu=%08" PRIx32
                    " started=%u recorded=%u key=%04x"
                    " savedata=%016" PRIx64 "/%016" PRIx64
                    " cb=%08" PRIx32 " lock=%u\n",
                    prompt, menu_callback, save_started, recorded,
                    read16(core, save2 + S58_SAVE2_KEY_OFFSET),
                    savedata_before, savedata_now,
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                    read8(core, S58_FIELD_LOCK));
        /* JP FireRed's success results (1/3) clear, unfreeze and unlock, then
         * destroy the save task and return directly to field.  The callback
         * global deliberately remains the stale 0x0806EDB9 owner.  Result 2
         * is cancel and uniquely restores the Start-menu input callback. */
        if (save_started && recorded && savedata_read
            && savedata_now != savedata_before
            && menu_callback == S58_STARTMENU_SAVE_CALLBACK
            && read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                == S58_CB2_OVERWORLD
            && read8(core, S58_FIELD_LOCK) == 0U) {
            run_key_frames(core, 0U, S58_FIELD_SETTLE);
            *quest_log_after = s58_quest_log_hash(core);
            uint64_t savedata_after = 0U;
            return s58_savedata_hash(core, &savedata_after)
                && savedata_after != savedata_before
                && *quest_log_after != 0U
                && (quest_log_before == 0U
                    || *quest_log_after != quest_log_before)
                && read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                    == S58_CB2_OVERWORLD
                && read8(core, S58_FIELD_LOCK) == 0U;
        }
        /* Same-file save is DefaultYes in the JP owner.  Ordinary A advances
         * text and confirms it; directional guessing would risk Result 2. */
        qol_press(core, QOL_KEY_A, 180U);
    }
    fprintf(stderr, "thin Quest Log normal save failed"
            " before=%016" PRIx64 " after=%016" PRIx64
            " cb=%08" PRIx32 " lock=%u menu=%08" PRIx32
            " cursor=%u/%u\n",
            quest_log_before, *quest_log_after,
            read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            read8(core, S58_FIELD_LOCK),
            read32(core, QOL_START_MENU_CALLBACK),
            read8(core, QOL_START_MENU_CURSOR),
            read8(core, QOL_START_MENU_COUNT));
    return false;
}

static bool s58_prepare_hub_save(struct mCore *core,
                                 const struct Stage58Cases *cases)
{
    if (!qol_run_field_trace(core)
        || !s58_warp(core, (uint8_t)cases->hub.group,
                     (uint8_t)cases->hub.map,
                     (uint16_t)cases->hub.pc.x,
                     (uint16_t)(cases->hub.pc.y + 1U))
        || !s58_prepare_map_view(core))
        return false;
    uint64_t save_hash = 0U;
    return s58_normal_menu_save(core, 0U, &save_hash)
        && save_hash != 0U;
}

static bool s58_continue_to_hub(struct mCore *core,
                                const struct Stage58Cases *cases)
{
    if (getenv("MGBA_STAGE58_TRACE") != NULL)
        fprintf(stderr, "continue begin pc=%08" PRIx32 " cap=%08" PRIx32
                " active=%u phase=%u\n",
                (uint32_t)read_register(core, "pc"),
                read32(core, S58_MAILBOX + 24U),
                read8(core, S58_CODEX_STATE + 20U),
                read16(core, S58_CODEX_STATE + 16U));
    run_key_frames(core, 0U, S58_TITLE_FRAMES);
    if (getenv("MGBA_STAGE58_TRACE") != NULL)
        fprintf(stderr, "continue after-title pc=%08" PRIx32
                " cap=%08" PRIx32 " active=%u phase=%u\n",
                (uint32_t)read_register(core, "pc"),
                read32(core, S58_MAILBOX + 24U),
                read8(core, S58_CODEX_STATE + 20U),
                read16(core, S58_CODEX_STATE + 16U));
    for (unsigned pulse = 0U; pulse < S58_CONTINUE_PULSES; ++pulse) {
        qol_press(core, pulse == 0U ? QOL_KEY_START : QOL_KEY_A, 180U);
        if (read8(core, S58_QUEST_LOG_STATE) != 0U
            || read8(core, S58_QUEST_LOG_PLAYBACK_STATE) != 0U)
            s58_quest_log_observed = true;
        if (getenv("MGBA_STAGE58_TRACE") != NULL)
            fprintf(stderr, "continue pulse=%u pc=%08" PRIx32
                    " cap=%08" PRIx32 " active=%u phase=%u cb=%08" PRIx32
                    "\n", pulse, (uint32_t)read_register(core, "pc"),
                    read32(core, S58_MAILBOX + 24U),
                    read8(core, S58_CODEX_STATE + 20U),
                    read16(core, S58_CODEX_STATE + 16U),
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2));
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58_CB2_OVERWORLD
            || !s58_hub_position(core, cases,
                                 (uint16_t)cases->hub.pc.x,
                                 (uint16_t)(cases->hub.pc.y + 1U)))
            continue;
        run_key_frames(core, 0U, 300U);
        for (unsigned attempt = 0U; attempt < 8U; ++attempt) {
            if (read8(core, S58_QUEST_LOG_STATE) != 0U
                || read8(core, S58_QUEST_LOG_PLAYBACK_STATE) != 0U)
                s58_quest_log_observed = true;
            if (read8(core, S58_QUEST_LOG_STATE) == 0U
                && read8(core, S58_QUEST_LOG_PLAYBACK_STATE) == 0U) {
                run_key_frames(core, 0U, S58_WARP_FRAMES);
                if (read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                        == S58_CB2_OVERWORLD
                    && read8(core, S58_FIELD_LOCK) == 0U
                    && s58_hub_position(
                        core, cases, (uint16_t)cases->hub.pc.x,
                        (uint16_t)(cases->hub.pc.y + 1U)))
                    return true;
            }
            qol_press(core, QOL_KEY_B, 180U);
        }
        break;
    }
    fprintf(stderr, "continue debug cb=%08" PRIx32
            " map_position=%u field_lock=%u quest=%u/%u\n",
            read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            s58_hub_position(core, cases,
                             (uint16_t)cases->hub.pc.x,
                             (uint16_t)(cases->hub.pc.y + 1U)),
            read8(core, S58_FIELD_LOCK), read8(core, S58_QUEST_LOG_STATE),
            read8(core, S58_QUEST_LOG_PLAYBACK_STATE));
    return false;
}

static bool s58_walk_to(struct mCore *core,
                        const struct Stage58Cases *cases,
                        uint16_t target_x, uint16_t target_y)
{
    for (unsigned step = 0U; step < 24U; ++step) {
        uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
        if (!s58_ewram_pointer(save1))
            return false;
        uint16_t x = read16(core, save1);
        uint16_t y = read16(core, save1 + 2U);
        if (x == target_x && y == target_y)
            return s58_hub_position(core, cases, target_x, target_y)
                && read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                    == S58_CB2_OVERWORLD;
        uint16_t key = x < target_x ? S58_KEY_RIGHT
            : x > target_x ? S58_KEY_LEFT
            : y < target_y ? S58_KEY_DOWN : S58_KEY_UP;
        qol_press(core, key, 30U);
    }
    return false;
}

static uint32_t s58_active_local(struct mCore *core, uint8_t local_id)
{
    for (unsigned index = 0U; index < S58_OBJECT_EVENT_CAPACITY; ++index) {
        uint32_t row = S58_OBJECT_EVENTS + index * S58_OBJECT_EVENT_SIZE;
        if ((read8(core, row) & 1U) && read8(core, row + 8U) == local_id)
            return row;
    }
    return 0U;
}

static bool s58_face_and_interact(struct mCore *core,
                                  const struct HubObject *object)
{
    uint32_t active = s58_active_local(core, (uint8_t)object->local_id);
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    if (!active || read16(core, active + 0x10U) != object->x + 7U
        || read16(core, active + 0x12U) != object->y + 7U
        || !s58_ewram_pointer(save1))
        return false;
    uint16_t x = read16(core, save1);
    uint16_t y = read16(core, save1 + 2U);
    uint16_t facing = 0U;
    if (x == object->x && y == object->y + 1U)
        facing = S58_KEY_UP;
    else if (x == object->x && y + 1U == object->y)
        facing = S58_KEY_DOWN;
    else if (x == object->x + 1U && y == object->y)
        facing = S58_KEY_LEFT;
    else if (x + 1U == object->x && y == object->y)
        facing = S58_KEY_RIGHT;
    if (facing == 0U)
        return false;
    qol_press(core, facing, 12U);
    if (getenv("MGBA_STAGE58_TRACE") != NULL) {
        fprintf(stderr, "interact trace after-face target=%u save=%d,%d"
                " active=%u pos=%u,%u cb=%08" PRIx32 "\n",
                object->local_id, (int16_t)read16(core, save1),
                (int16_t)read16(core, save1 + 2U), read8(core, active) & 1U,
                read16(core, active + 0x10U), read16(core, active + 0x12U),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2));
    }
    qol_press(core, QOL_KEY_A, 45U);
    return true;
}

static bool s58_wait_field(struct mCore *core, unsigned presses)
{
    for (unsigned attempt = 0U; attempt < presses; ++attempt) {
        if (getenv("MGBA_STAGE58_TRACE") != NULL)
            fprintf(stderr, "return trace attempt=%u cb=%08" PRIx32
                    " script=%" PRIu32 " pss=%08" PRIx32 "\n", attempt,
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                    (uint32_t)read8(core, S58_FIELD_LOCK),
                    read32(core, QOL_PSS_DATA));
        bool field = read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                == S58_CB2_OVERWORLD
            && read8(core, S58_FIELD_LOCK) == 0U;
        if (field) {
            run_key_frames(core, 0U, S58_FIELD_SETTLE);
            return read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                    == S58_CB2_OVERWORLD
                && read8(core, S58_FIELD_LOCK) == 0U;
        }
        qol_press(core, QOL_KEY_B, 180U);
    }
    return false;
}

static bool s58_exit_storage_to_field(struct mCore *core,
                                      const struct Stage58Cases *cases)
{
    /* B first backs out of the box cursor layers.  Space each press far enough
     * apart for the PSS state machine, then stop injecting keys on the exact
     * frame that its heap is released. */
    bool released = false;
    uint32_t trace_callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
    for (unsigned back = 0U; back < 5U && !released; ++back) {
        qol_pss_chord(core, QOL_KEY_B);
        for (unsigned frame = 0U; frame < 600U; ++frame) {
            run_key_frames(core, 0U, 1U);
            uint32_t callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
            if (getenv("MGBA_STAGE58_TRACE") != NULL
                && callback != trace_callback) {
                fprintf(stderr, "PSS exit trace back=%u frame=%u cb=%08"
                        PRIx32 " pss=%08" PRIx32 " fieldcb=%08" PRIx32
                        " task0=%08" PRIx32 " save=%u,%u\n",
                        back, frame, callback,
                        read32(core, QOL_PSS_DATA),
                        read32(core, QOL_FIELD_CALLBACK_SLOT),
                        read32(core, QOL_TASKS),
                        read16(core, read32(core, QOL_SAVE_BLOCK1_SLOT)),
                        read16(core, read32(core, QOL_SAVE_BLOCK1_SLOT) + 2U));
                trace_callback = callback;
            }
            if (!s58_ewram_pointer(read32(core, QOL_PSS_DATA))) {
                released = true;
                break;
            }
        }
    }
    if (!released)
        return false;
    for (unsigned frame = 0U; frame < 1800U; ++frame) {
        run_key_frames(core, 0U, 1U);
        uint32_t callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
        if (getenv("MGBA_STAGE58_TRACE") != NULL
            && callback != trace_callback) {
            fprintf(stderr, "PSS return trace frame=%u cb=%08" PRIx32
                    " fieldcb=%08" PRIx32 "\n", frame, callback,
                    read32(core, QOL_FIELD_CALLBACK_SLOT));
            trace_callback = callback;
        }
        if (callback == S58_CB2_OVERWORLD)
            break;
    }
    if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58_CB2_OVERWORLD)
        return false;
    /* B leaves the withdraw/deposit/move menu, then the parent PC menu.  Do
     * not call ScriptContext2_IsEnabled while those stock menu tasks are live:
     * libmGBA's host-call trampoline perturbs that asynchronous return path
     * and can manufacture a soft reset.  Six sparse, ordinary B pulses are
     * harmless after the field is already free and close every parent layer. */
    for (unsigned menu = 0U; menu < 6U; ++menu) {
        run_key_frames(core, 0U, 300U);
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58_CB2_OVERWORLD)
            return false;
        qol_press(core, QOL_KEY_B, 298U);
    }
    run_key_frames(core, 0U, 600U);
    return !s58_ewram_pointer(read32(core, QOL_PSS_DATA))
        && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S58_CB2_OVERWORLD
        && read8(core, S58_FIELD_LOCK) == 0U
        && s58_hub_position(core, cases, (uint16_t)cases->hub.pc.x,
                            (uint16_t)(cases->hub.pc.y + 1U));
}

static uint32_t s58_crc_byte(uint32_t crc, uint8_t value)
{
    crc ^= value;
    for (unsigned bit = 0U; bit < 8U; ++bit)
        crc = (crc >> 1U) ^ ((crc & 1U) ? UINT32_C(0xEDB88320) : 0U);
    return crc;
}

static uint32_t s58_reward_crc(struct mCore *core)
{
    uint32_t crc = UINT32_C(0xFFFFFFFF);
    for (unsigned index = 0U; index < S58_REWARD_OWNER_SIZE; ++index) {
        uint8_t value = index >= 12U && index < 16U
            ? 0U : read8(core, S58_REWARD_OWNER + index);
        crc = s58_crc_byte(crc, value);
    }
    return crc ^ UINT32_C(0xFFFFFFFF);
}

static uint64_t s58_codex_owner_hash(struct mCore *core)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    const uint32_t roots[] = {
        S58_REWARD_OWNER, S58_MAILBOX, S58_CODEX_STATE,
    };
    const unsigned sizes[] = {S58_REWARD_OWNER_SIZE, 256U, 256U};
    for (unsigned range = 0U; range < ARRAY_LEN(roots); ++range) {
        for (unsigned byte = 0U; byte < sizes[range]; ++byte) {
            hash ^= read8(core, roots[range] + byte);
            hash *= UINT64_C(1099511628211);
        }
    }
    return hash;
}

static bool s58_reward_valid_window(struct mCore *core, uint8_t window)
{
    return read32(core, S58_REWARD_OWNER) == S58_REWARD_MAGIC
        && read32(core, S58_REWARD_OWNER + 4U)
            == ~(uint32_t)S58_REWARD_MAGIC
        && read16(core, S58_REWARD_OWNER + 8U) == 1U
        && read16(core, S58_REWARD_OWNER + 10U) == S58_REWARD_OWNER_SIZE
        && read32(core, S58_REWARD_OWNER + 12U) == s58_reward_crc(core)
        && read8(core, S58_REWARD_OWNER + 20U) == window
        && read8(core, S58_REWARD_OWNER + 21U)
            <= S58_REWARD_PHASE_COMMITTED;
}

static bool s58_codex_boundaries(struct mCore *core)
{
    bool runtime_idle = read8(core, S58_CODEX_STATE + 20U) == 0U
        && ((read32(core, S58_MAILBOX) == S58_MAILBOX_MAGIC
             && read32(core, S58_MAILBOX + 4U) != 0U
             && read16(core, S58_CODEX_STATE + 16U)
                == S58_CODEX_PHASE_IDLE)
            || (read32(core, S58_MAILBOX) == 0U
                && read16(core, S58_CODEX_STATE + 16U) == 0U));
    bool passed = runtime_idle
        && s58_reward_valid_window(core, S58_REWARD_WINDOW_CLOSED);
    if (!passed)
        fprintf(stderr, "Codex boundary debug mailbox=%08" PRIx32
                " header=%08" PRIx32 " active=%u phase=%u"
                " owner=%08" PRIx32 "/%08" PRIx32
                " version=%u size=%u crc=%08" PRIx32 "/%08" PRIx32
                " window=%u reward_phase=%u\n",
                read32(core, S58_MAILBOX), read32(core, S58_MAILBOX + 4U),
                read8(core, S58_CODEX_STATE + 20U),
                read16(core, S58_CODEX_STATE + 16U),
                read32(core, S58_REWARD_OWNER),
                read32(core, S58_REWARD_OWNER + 4U),
                read16(core, S58_REWARD_OWNER + 8U),
                read16(core, S58_REWARD_OWNER + 10U),
                read32(core, S58_REWARD_OWNER + 12U),
                s58_reward_crc(core), read8(core, S58_REWARD_OWNER + 20U),
                read8(core, S58_REWARD_OWNER + 21U));
    return passed;
}

static uint32_t s58_item_quantity(struct mCore *core, uint16_t item)
{
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    uint8_t pocket = read8(core, S58_ITEM_TABLE
                           + (uint32_t)item * S58_ITEM_STRIDE
                           + S58_ITEM_POCKET_OFFSET);
    if (!s58_ewram_pointer(save2) || pocket == 0U || pocket > 5U)
        return 0U;
    uint32_t descriptor = S58_BAG_POCKETS + (pocket - 1U) * 8U;
    uint32_t slots = read32(core, descriptor);
    uint8_t capacity = read8(core, descriptor + 4U);
    if (!s58_ewram_pointer(slots) || capacity == 0U || capacity > 58U)
        return 0U;
    uint16_t key = read16(core, save2 + S58_SAVE2_KEY_OFFSET);
    for (unsigned slot = 0U; slot < capacity; ++slot) {
        uint32_t row = slots + slot * 4U;
        if (read16(core, row) == item)
            return read16(core, row + 2U) ^ key;
    }
    return 0U;
}

static uint16_t s58_item_raw_quantity(struct mCore *core, uint16_t item,
                                      uint32_t *descriptor_slots)
{
    uint8_t pocket = read8(core, S58_ITEM_TABLE
                           + (uint32_t)item * S58_ITEM_STRIDE
                           + S58_ITEM_POCKET_OFFSET);
    uint32_t descriptor = pocket > 0U && pocket <= 5U
        ? S58_BAG_POCKETS + (pocket - 1U) * 8U : 0U;
    uint32_t slots = descriptor ? read32(core, descriptor) : 0U;
    uint8_t capacity = descriptor ? read8(core, descriptor + 4U) : 0U;
    *descriptor_slots = slots;
    if (!s58_ewram_pointer(slots))
        return 0U;
    for (unsigned slot = 0U; slot < capacity; ++slot) {
        uint32_t row = slots + slot * 4U;
        if (read16(core, row) == item)
            return read16(core, row + 2U);
    }
    return 0U;
}

struct S58BagTraceState {
    uint32_t save1;
    uint32_t save2;
    uint32_t slots;
    uint16_t key;
    uint16_t raw;
};

struct S58CodexSaveSentinel {
    uint8_t seen_primary[S58_POKEDEX_BITMAP_SIZE];
    uint8_t seen_secondary[S58_POKEDEX_BITMAP_SIZE];
    uint8_t seen_save2[S58_POKEDEX_BITMAP_SIZE];
    uint8_t personality[S58_POKEDEX_PERSONALITY_SIZE];
    uint8_t owned[S58_POKEDEX_BITMAP_SIZE];
};

static bool s58_codex_save_sentinel_read(
    struct mCore *core, struct S58CodexSaveSentinel *sentinel)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    if (!s58_ewram_pointer(save1) || !s58_ewram_pointer(save2))
        return false;
    for (unsigned index = 0U; index < S58_POKEDEX_BITMAP_SIZE; ++index) {
        sentinel->seen_primary[index] = read8(
            core, save1 + S58_SAVE1_SEEN_PRIMARY_OFFSET + index);
        sentinel->seen_secondary[index] = read8(
            core, save1 + S58_SAVE1_SEEN_SECONDARY_OFFSET + index);
        sentinel->seen_save2[index] = read8(
            core, save2 + S58_SAVE2_POKEDEX_SEEN_OFFSET + index);
        sentinel->owned[index] = read8(
            core, save2 + S58_SAVE2_POKEDEX_OWNED_OFFSET + index);
    }
    for (unsigned index = 0U; index < S58_POKEDEX_PERSONALITY_SIZE;
         ++index)
        sentinel->personality[index] = read8(
            core, save2 + S58_SAVE2_POKEDEX_PERSONALITY_OFFSET + index);
    return true;
}

static uint64_t s58_sentinel_hash(const uint8_t *bytes, size_t size,
                                  uint64_t hash)
{
    for (size_t index = 0U; index < size; ++index) {
        hash ^= bytes[index];
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

static void s58_codex_save_sentinel_hashes(
    const struct S58CodexSaveSentinel *sentinel,
    uint64_t *seen, uint64_t *personality, uint64_t *owned)
{
    *seen = s58_sentinel_hash(
        sentinel->seen_primary, sizeof(sentinel->seen_primary),
        UINT64_C(14695981039346656037));
    *seen = s58_sentinel_hash(
        sentinel->seen_secondary, sizeof(sentinel->seen_secondary), *seen);
    *seen = s58_sentinel_hash(
        sentinel->seen_save2, sizeof(sentinel->seen_save2), *seen);
    *personality = s58_sentinel_hash(
        sentinel->personality, sizeof(sentinel->personality),
        UINT64_C(14695981039346656037));
    *owned = s58_sentinel_hash(
        sentinel->owned, sizeof(sentinel->owned),
        UINT64_C(14695981039346656037));
}

static bool s58_codex_save_sentinel_seed(
    struct mCore *core, struct S58CodexSaveSentinel *sentinel,
    uint64_t *seen, uint64_t *personality, uint64_t *owned)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    if (!s58_ewram_pointer(save1) || !s58_ewram_pointer(save2))
        return false;
    /* Fixture input only.  Zero seen mirrors make a natural opponent-seen
     * update observable to the ROM transaction; the adapter must restore the
     * exact prebattle value.  Personalities use a nonzero sentinel, while the
     * owned bitmap is never host-modified and must remain naturally stable. */
    for (unsigned index = 0U; index < S58_POKEDEX_BITMAP_SIZE; ++index) {
        write8(core, save1 + S58_SAVE1_SEEN_PRIMARY_OFFSET + index, 0U);
        write8(core, save1 + S58_SAVE1_SEEN_SECONDARY_OFFSET + index, 0U);
        write8(core, save2 + S58_SAVE2_POKEDEX_SEEN_OFFSET + index, 0U);
    }
    for (unsigned index = 0U; index < S58_POKEDEX_PERSONALITY_SIZE;
         ++index)
        write8(core, save2 + S58_SAVE2_POKEDEX_PERSONALITY_OFFSET + index,
               (uint8_t)(0xA5U ^ (index * 29U)));
    if (!s58_codex_save_sentinel_read(core, sentinel))
        return false;
    s58_codex_save_sentinel_hashes(
        sentinel, seen, personality, owned);
    return true;
}

static bool s58_codex_save_sentinel_matches(
    struct mCore *core, const struct S58CodexSaveSentinel *expected,
    uint64_t *seen, uint64_t *personality, uint64_t *owned)
{
    struct S58CodexSaveSentinel actual;
    if (!s58_codex_save_sentinel_read(core, &actual))
        return false;
    s58_codex_save_sentinel_hashes(&actual, seen, personality, owned);
    return memcmp(&actual, expected, sizeof(actual)) == 0;
}

static void s58_trace_bag_transition(struct mCore *core, const char *label,
                                     unsigned tick,
                                     struct S58BagTraceState *state)
{
    if (getenv("MGBA_STAGE58_TRACE") == NULL)
        return;
    struct S58BagTraceState current = {
        .save1 = read32(core, QOL_SAVE_BLOCK1_SLOT),
        .save2 = read32(core, QOL_SAVE_BLOCK2_SLOT),
    };
    current.key = s58_ewram_pointer(current.save2)
        ? read16(core, current.save2 + S58_SAVE2_KEY_OFFSET) : 0U;
    current.raw = s58_item_raw_quantity(core, 84U, &current.slots);
    if (memcmp(&current, state, sizeof(current)) == 0)
        return;
    fprintf(stderr, "%s tick=%u save1=%08" PRIx32 "/%08" PRIx32
            " save2=%08" PRIx32 "/%08" PRIx32
            " key=%04x/%04x slots=%08" PRIx32 "/%08" PRIx32
            " raw=%04x/%04x pc=%08" PRIx32 " lr=%08" PRIx32 "\n",
            label, tick, state->save1, current.save1,
            state->save2, current.save2, state->key, current.key,
            state->slots, current.slots, state->raw, current.raw,
            (uint32_t)read_register(core, "pc"),
            (uint32_t)read_register(core, "lr"));
    *state = current;
}

static void s58_trace_bag_item(struct mCore *core, const char *label,
                               uint16_t item)
{
    if (getenv("MGBA_STAGE58_TRACE") == NULL)
        return;
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    uint8_t pocket = read8(core, S58_ITEM_TABLE
                           + (uint32_t)item * S58_ITEM_STRIDE
                           + S58_ITEM_POCKET_OFFSET);
    uint32_t descriptor = pocket > 0U && pocket <= 5U
        ? S58_BAG_POCKETS + (pocket - 1U) * 8U : 0U;
    uint32_t slots = descriptor ? read32(core, descriptor) : 0U;
    uint8_t capacity = descriptor ? read8(core, descriptor + 4U) : 0U;
    uint16_t key = s58_ewram_pointer(save2)
        ? read16(core, save2 + S58_SAVE2_KEY_OFFSET) : 0U;
    uint16_t raw = 0U;
    if (s58_ewram_pointer(slots)) {
        for (unsigned slot = 0U; slot < capacity; ++slot) {
            uint32_t row = slots + slot * 4U;
            if (read16(core, row) == item) {
                raw = read16(core, row + 2U);
                break;
            }
        }
    }
    fprintf(stderr, "bag trace %s item=%u pocket=%u ptr=%08" PRIx32
            " cap=%u save=%08" PRIx32 "/%08" PRIx32
            " key=%04x raw=%04x qty=%u pc=%08" PRIx32
            " lr=%08" PRIx32 "\n",
            label, item, pocket, slots, capacity, save1, save2,
            key, raw, s58_item_quantity(core, item),
            (uint32_t)read_register(core, "pc"),
            (uint32_t)read_register(core, "lr"));
}

static bool s58_thin_quantities_exact(struct mCore *core,
                                      const struct Stage58Cases *cases)
{
    static const uint16_t offsets[5] = {
        0x0310U, 0x03B8U, 0x0430U, 0x0464U, 0x054CU,
    };
    static const uint8_t capacities[5] = {42U, 30U, 13U, 58U, 43U};
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    if (cases->thin_event_count != 6U || !s58_ewram_pointer(save1))
        return false;
    /* This is a read-only boundary assertion.  A host SetBag call immediately
     * before the natural ReadKeys/Codex scheduler can perturb its frame owner,
     * so require the stock field owner to have bound every exact descriptor. */
    for (unsigned pocket = 0U; pocket < ARRAY_LEN(offsets); ++pocket) {
        uint32_t descriptor = S58_BAG_POCKETS + pocket * 8U;
        if (read32(core, descriptor) != save1 + offsets[pocket]
            || read8(core, descriptor + 4U) != capacities[pocket])
            return false;
    }
    for (unsigned index = 0U; index < cases->thin_event_count; ++index) {
        const struct ThinEvent *event = &cases->thin_events[index];
        uint32_t actual = s58_item_quantity(core, event->item_id);
        if (actual != event->quantity) {
            fprintf(stderr, "thin quantity boundary mismatch index=%u"
                    " item=%u qty=%" PRIu32 "/%u\n",
                    index, event->item_id, actual, event->quantity);
            return false;
        }
    }
    return true;
}

static uint32_t s58_money(struct mCore *core)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    if (!s58_ewram_pointer(save1) || !s58_ewram_pointer(save2))
        return UINT32_MAX;
    return read32(core, save1 + S58_SAVE1_MONEY_OFFSET)
        ^ read32(core, save2 + S58_SAVE2_KEY_OFFSET);
}

static void s58_set_money(struct mCore *core, uint32_t money)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    if (!s58_ewram_pointer(save1) || !s58_ewram_pointer(save2))
        s58_die("money fixture SaveBlock不正");
    qol_write32(core, save1 + S58_SAVE1_MONEY_OFFSET,
                money ^ read32(core, save2 + S58_SAVE2_KEY_OFFSET));
}

struct S58PocketSnapshot {
    uint8_t pocket;
    uint8_t capacity;
    uint16_t items[58U];
    uint16_t quantities[58U];
};

static bool s58_pocket_snapshot(struct mCore *core, uint16_t item,
                                struct S58PocketSnapshot *snapshot)
{
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    snapshot->pocket = read8(core, S58_ITEM_TABLE
                            + (uint32_t)item * S58_ITEM_STRIDE
                            + S58_ITEM_POCKET_OFFSET);
    uint32_t descriptor = snapshot->pocket > 0U && snapshot->pocket <= 5U
        ? S58_BAG_POCKETS + (snapshot->pocket - 1U) * 8U : 0U;
    uint32_t slots = descriptor ? read32(core, descriptor) : 0U;
    snapshot->capacity = descriptor ? read8(core, descriptor + 4U) : 0U;
    if (!s58_ewram_pointer(save2) || !s58_ewram_pointer(slots)
        || snapshot->capacity == 0U || snapshot->capacity > 58U)
        return false;
    uint16_t key = read16(core, save2 + S58_SAVE2_KEY_OFFSET);
    for (unsigned slot = 0U; slot < snapshot->capacity; ++slot) {
        uint32_t row = slots + slot * 4U;
        snapshot->items[slot] = read16(core, row);
        snapshot->quantities[slot] = read16(core, row + 2U) ^ key;
    }
    return true;
}

static bool s58_pocket_restore(struct mCore *core,
                               const struct S58PocketSnapshot *snapshot)
{
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    uint32_t descriptor = snapshot->pocket > 0U && snapshot->pocket <= 5U
        ? S58_BAG_POCKETS + (snapshot->pocket - 1U) * 8U : 0U;
    uint32_t slots = descriptor ? read32(core, descriptor) : 0U;
    if (!s58_ewram_pointer(save2) || !s58_ewram_pointer(slots)
        || read8(core, descriptor + 4U) != snapshot->capacity)
        return false;
    uint16_t key = read16(core, save2 + S58_SAVE2_KEY_OFFSET);
    for (unsigned slot = 0U; slot < snapshot->capacity; ++slot) {
        uint32_t row = slots + slot * 4U;
        write16(core, row, snapshot->items[slot]);
        write16(core, row + 2U,
                (uint16_t)(snapshot->quantities[slot] ^ key));
    }
    run_key_frames(core, 0U, 1U);
    return true;
}

static bool s58_pocket_fill(struct mCore *core, uint16_t target,
                            const struct S58PocketSnapshot *snapshot)
{
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    uint32_t descriptor = S58_BAG_POCKETS
        + (snapshot->pocket - 1U) * 8U;
    uint32_t slots = read32(core, descriptor);
    if (!s58_ewram_pointer(save2) || !s58_ewram_pointer(slots)
        || read8(core, descriptor + 4U) != snapshot->capacity)
        return false;
    uint16_t key = read16(core, save2 + S58_SAVE2_KEY_OFFSET);
    unsigned candidate = 1U;
    for (unsigned slot = 0U; slot < snapshot->capacity; ++slot) {
        uint16_t fill_item = slot == 0U ? target : 0U;
        while (fill_item == 0U && candidate < 1200U) {
            if (candidate != target
                && read8(core, S58_ITEM_TABLE
                               + candidate * S58_ITEM_STRIDE
                               + S58_ITEM_POCKET_OFFSET)
                    == snapshot->pocket)
                fill_item = (uint16_t)candidate;
            ++candidate;
        }
        if (fill_item == 0U)
            return false;
        uint32_t row = slots + slot * 4U;
        write16(core, row, fill_item);
        write16(core, row + 2U,
                (uint16_t)((slot == 0U ? 999U : 1U) ^ key));
    }
    run_key_frames(core, 0U, 1U);
    return s58_item_quantity(core, target) == 999U;
}

static bool s58_flag_get_direct(struct mCore *core, uint16_t flag)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    if (!s58_ewram_pointer(save1) || flag == 0U || flag > 0x3FFFU
        || read8(core, S58_QUEST_LOG_STATE) != 0U)
        return false;
    return (read8(core, save1 + 0x0EE0U + (flag >> 3U))
            & (1U << (flag & 7U))) != 0U;
}

static uint8_t s58_flag_byte_direct(struct mCore *core, uint16_t flag)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    return s58_ewram_pointer(save1) && flag != 0U && flag <= 0x3FFFU
        ? read8(core, save1 + 0x0EE0U + (flag >> 3U)) : 0U;
}

static bool s58_thin_event_tile(struct mCore *core, uint32_t events,
                                uint16_t x, uint16_t y)
{
    if (!s58_rom_pointer(events))
        return true;
    const uint8_t counts[4] = {
        read8(core, events), read8(core, events + 1U),
        read8(core, events + 2U), read8(core, events + 3U),
    };
    const uint32_t roots[4] = {
        read32(core, events + 4U), read32(core, events + 8U),
        read32(core, events + 12U), read32(core, events + 16U),
    };
    const unsigned strides[4] = {24U, 8U, 16U, 12U};
    for (unsigned kind = 0U; kind < ARRAY_LEN(counts); ++kind) {
        if (counts[kind] != 0U && !s58_rom_pointer(roots[kind]))
            return true;
        for (unsigned index = 0U; index < counts[kind]; ++index) {
            uint32_t row = roots[kind] + index * strides[kind];
            uint32_t coordinate_offset = kind == 0U ? 4U : 0U;
            if (read16(core, row + coordinate_offset) == x
                && read16(core, row + coordinate_offset + 2U) == y)
                return true;
        }
    }
    return false;
}

static bool s58_thin_blockdata_adjacent(struct mCore *core,
                                        const struct Stage58Cases *cases,
                                        const struct ThinEvent *event,
                                        uint16_t *x_out, uint16_t *y_out)
{
    uint32_t group_table = read32(core, cases->map_groups_root
                                 + (uint32_t)event->group * 4U);
    uint32_t header = s58_rom_pointer(group_table)
        ? read32(core, group_table + (uint32_t)event->map * 4U) : 0U;
    uint32_t layout = s58_rom_pointer(header) ? read32(core, header) : 0U;
    uint32_t width = s58_rom_pointer(layout) ? read32(core, layout) : 0U;
    uint32_t height = s58_rom_pointer(layout) ? read32(core, layout + 4U) : 0U;
    uint32_t blocks = s58_rom_pointer(layout)
        ? read32(core, layout + 12U) : 0U;
    uint32_t events = s58_rom_pointer(header)
        ? read32(core, header + 4U) : 0U;
    if (width == 0U || height == 0U || width > 1024U || height > 1024U
        || !s58_rom_pointer(blocks) || !s58_rom_pointer(events))
        return false;
    /* Deterministic clockwise order begins above the object, but selection is
     * data-driven: collision bits 10..11 must encode a passable block and no
     * object/warp/coord/background event may own the candidate tile. */
    static const int8_t offsets[4][2] = {
        {0, -1}, {1, 0}, {0, 1}, {-1, 0},
    };
    for (unsigned direction = 0U; direction < ARRAY_LEN(offsets);
         ++direction) {
        int32_t candidate_x = (int32_t)event->x + offsets[direction][0];
        int32_t candidate_y = (int32_t)event->y + offsets[direction][1];
        if (candidate_x < 0 || candidate_y < 0
            || (uint32_t)candidate_x >= width
            || (uint32_t)candidate_y >= height)
            continue;
        uint16_t x = (uint16_t)candidate_x;
        uint16_t y = (uint16_t)candidate_y;
        uint16_t block = read16(core, blocks
                                + 2U * ((uint32_t)y * width + x));
        if (((block >> 10U) & 3U) != 0U
            || s58_thin_event_tile(core, events, x, y))
            continue;
        *x_out = x;
        *y_out = y;
        return true;
    }
    return false;
}

static bool s58_thin_warp_adjacent(struct mCore *core,
                                   const struct Stage58Cases *cases,
                                   const struct ThinEvent *event)
{
    uint16_t x = 0U, y = 0U;
    return s58_thin_blockdata_adjacent(
            core, cases, event, &x, &y)
        && s58_warp(core, event->group, event->map, x, y)
        && s58_map_position(core, event->group, event->map, x, y);
}

static bool s58_thin_adjacent_position(struct mCore *core,
                                       const struct ThinEvent *event)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    if (!s58_ewram_pointer(save1)
        || read8(core, save1 + 4U) != event->group
        || read8(core, save1 + 5U) != event->map)
        return false;
    uint16_t x = read16(core, save1);
    uint16_t y = read16(core, save1 + 2U);
    uint32_t distance_x = x < event->x ? event->x - x : x - event->x;
    uint32_t distance_y = y < event->y ? event->y - y : y - event->y;
    return distance_x + distance_y == 1U
        && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S58_CB2_OVERWORLD
        && read8(core, S58_FIELD_LOCK) == 0U;
}

static bool s58_thin_pickup_here(struct mCore *core,
                                 const struct ThinEvent *event,
                                 uint32_t quantity_before,
                                 uint64_t owner_hash)
{
    struct HubObject object = {
        .local_id = event->local_id, .x = event->x, .y = event->y,
    };
    return !s58_flag_get_direct(core, event->flag)
        && s58_face_and_interact(core, &object)
        && s58_wait_field(core, 16U)
        && s58_item_quantity(core, event->item_id)
            == quantity_before + event->quantity
        && s58_flag_get_direct(core, event->flag)
        && s58_thin_adjacent_position(core, event)
        && s58_codex_owner_hash(core) == owner_hash;
}

static bool s58_thin_pickup(struct mCore *core,
                            const struct Stage58Cases *cases,
                            const struct ThinEvent *event,
                            uint32_t quantity_before,
                            uint64_t owner_hash)
{
    return s58_thin_warp_adjacent(core, cases, event)
        && s58_thin_pickup_here(core, event, quantity_before, owner_hash);
}

static bool s58_thin_repeat(struct mCore *core,
                            const struct ThinEvent *event,
                            uint32_t quantity_after,
                            uint64_t owner_hash)
{
    struct HubObject object = {
        .local_id = event->local_id, .x = event->x, .y = event->y,
    };
    bool engine_flag = s58_flag_get_direct(core, event->flag)
        && s58_call_synced(core, QOL_FLAG_GET,
                           event->flag, 0U, 0U, 0U) == 1U;
    if (getenv("MGBA_STAGE58_TRACE") != NULL)
        fprintf(stderr, "thin repeat pre-A qty=%" PRIu32
                " flag=%u engine=%u\n",
                s58_item_quantity(core, event->item_id),
                s58_flag_get_direct(core, event->flag), engine_flag);
    uint8_t flag_byte_before = s58_flag_byte_direct(core, event->flag);
    if (!engine_flag
        || !s58_face_and_interact(core, &object)
        || !s58_wait_field(core, 8U))
        return false;
    /* These scripts remain visible and branch on their own completion flag;
     * the second ordinary A must return without another GiveItem. */
    bool passed = read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S58_CB2_OVERWORLD
        && read8(core, S58_FIELD_LOCK) == 0U
        && s58_item_quantity(core, event->item_id) == quantity_after
        && s58_flag_get_direct(core, event->flag)
        && s58_flag_byte_direct(core, event->flag) == flag_byte_before
        && s58_codex_owner_hash(core) == owner_hash;
    if (!passed && getenv("MGBA_STAGE58_TRACE") != NULL)
        fprintf(stderr, "thin repeat detail cb=%08" PRIx32
                " lock=%u qty=%" PRIu32 "/%" PRIu32
                " flag=%u owner=%016" PRIx64 "/%016" PRIx64 "\n",
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, S58_FIELD_LOCK),
                s58_item_quantity(core, event->item_id), quantity_after,
                s58_flag_get_direct(core, event->flag),
                s58_codex_owner_hash(core), owner_hash);
    return passed;
}

static bool s58_thin_full_retry(struct mCore *core,
                                const struct Stage58Cases *cases,
                                const struct ThinEvent *event,
                                uint64_t owner_hash,
                                uint32_t quantity_before)
{
    struct S58PocketSnapshot snapshot = {0};
    struct HubObject object = {
        .local_id = event->local_id, .x = event->x, .y = event->y,
    };
    if (!s58_thin_warp_adjacent(core, cases, event)
        || !s58_pocket_snapshot(core, event->item_id, &snapshot)
        || !s58_pocket_fill(core, event->item_id, &snapshot)
        || s58_flag_get_direct(core, event->flag))
        return false;
    uint8_t flag_bit = (uint8_t)(1U << (event->flag & 7U));
    uint8_t flag_byte_before = s58_flag_byte_direct(core, event->flag);
    if (!s58_face_and_interact(core, &object)
        || !s58_wait_field(core, 16U))
        return false;
    uint8_t rejected_flag_byte = s58_flag_byte_direct(core, event->flag);
    bool rejected = s58_item_quantity(core, event->item_id) == 999U
        && !s58_flag_get_direct(core, event->flag)
        && rejected_flag_byte == flag_byte_before
        && s58_codex_owner_hash(core) == owner_hash;
    if (!rejected || !s58_pocket_restore(core, &snapshot)
        || s58_item_quantity(core, event->item_id) != quantity_before)
        return false;
    bool picked = s58_thin_pickup_here(
        core, event, quantity_before, owner_hash);
    return picked
        && s58_flag_byte_direct(core, event->flag)
            == (uint8_t)(flag_byte_before | flag_bit);
}

static bool s58_thin_path(struct mCore *core,
                          const struct Stage58Cases *cases,
                          bool *initial, bool *repeat, bool *retry,
                          unsigned *covered)
{
    *initial = false;
    *repeat = false;
    *retry = false;
    *covered = 0U;
    if (cases->thin_event_count != 6U || !s58_codex_boundaries(core))
        return false;
    (void)s58_call_synced(core, S58_SET_BAG_POCKETS_POINTERS,
                          0U, 0U, 0U, 0U);
    uint64_t owner_hash = s58_codex_owner_hash(core);
    bool initial_all = true;
    bool repeat_all = true;
    bool retry_all = true;
    for (unsigned index = 0U; index < cases->thin_event_count; ++index) {
        const struct ThinEvent *event = &cases->thin_events[index];
        uint32_t before = s58_item_quantity(core, event->item_id);
        bool picked = s58_thin_full_retry(
            core, cases, event, owner_hash, before);
        uint32_t after = s58_item_quantity(core, event->item_id);
        bool repeated = picked
            && s58_thin_repeat(core, event, after, owner_hash);
        initial_all = initial_all && picked;
        repeat_all = repeat_all && repeated;
        retry_all = retry_all && picked;
        if (picked && repeated)
            ++*covered;
        if (!picked || !repeated) {
            if (getenv("MGBA_STAGE58_TRACE") != NULL)
                fprintf(stderr, "thin event[%u] failed pickup=%u repeat=%u"
                        " qty=%" PRIu32 "/%" PRIu32 " flag=%u\n", index,
                        picked, repeated, before, after,
                        s58_flag_get_direct(core, event->flag));
            break;
        }
    }
    *initial = initial_all && *covered == cases->thin_event_count;
    *repeat = repeat_all && *covered == cases->thin_event_count;
    *retry = retry_all && *covered == cases->thin_event_count;
    bool hub_return = *initial && *repeat && *retry
        && s58_warp(core, (uint8_t)cases->hub.group,
                    (uint8_t)cases->hub.map,
                    (uint16_t)cases->hub.healer.x,
                    (uint16_t)(cases->hub.healer.y + 1U));
    return hub_return && s58_codex_owner_hash(core) == owner_hash
        && s58_codex_boundaries(core);
}

static bool s58_thin_post_questlog_path(
    struct mCore *core, const struct Stage58Cases *cases)
{
    if (!s58_quest_log_observed || cases->thin_event_count != 6U
        || !s58_codex_boundaries(core))
        return false;
    (void)s58_call_synced(core, S58_SET_BAG_POCKETS_POINTERS,
                          0U, 0U, 0U, 0U);
    uint64_t owner_hash = s58_codex_owner_hash(core);
    for (unsigned index = 0U; index < cases->thin_event_count; ++index) {
        const struct ThinEvent *event = &cases->thin_events[index];
        uint32_t quantity = s58_item_quantity(core, event->item_id);
        if (!s58_flag_get_direct(core, event->flag)
            || quantity < event->quantity
            || !s58_thin_warp_adjacent(core, cases, event)
            || !s58_thin_repeat(core, event, quantity, owner_hash))
            return false;
    }
    return s58_warp(core, (uint8_t)cases->hub.group,
                    (uint8_t)cases->hub.map,
                    (uint16_t)cases->hub.npc.x,
                    (uint16_t)(cases->hub.npc.y + 1U))
        && s58_codex_owner_hash(core) == owner_hash
        && s58_codex_boundaries(core);
}

static bool s58_mart_purchase_attempt(struct mCore *core,
                                      const struct Stage58Cases *cases,
                                      uint16_t item, unsigned pulse_limit,
                                      bool expect_purchase,
                                      unsigned *pulses_used)
{
    uint32_t quantity_before = s58_item_quantity(core, item);
    uint32_t money_before = s58_money(core);
    *pulses_used = 0U;
    if (!s58_face_and_interact(core, &cases->hub.mart)) {
        if (getenv("MGBA_STAGE58_TRACE") != NULL)
            fprintf(stderr, "mart purchase interaction missing\n");
        return false;
    }
    bool changed = false;
    for (unsigned pulse = 0U; pulse < pulse_limit && !changed; ++pulse) {
        run_key_frames(core, 0U, 90U);
        qol_press(core, QOL_KEY_A, 120U);
        *pulses_used = pulse + 1U;
        changed = s58_item_quantity(core, item) > quantity_before;
    }
    uint32_t quantity_after = s58_item_quantity(core, item);
    uint32_t money_after = s58_money(core);
    for (unsigned pulse = 0U; pulse < 12U; ++pulse)
        qol_press(core, QOL_KEY_B, 90U);
    bool returned = s58_wait_field(core, 12U);
    bool passed = returned && (expect_purchase
        ? changed && quantity_after == quantity_before + 1U
            && money_after < money_before
        : !changed && quantity_after == quantity_before
            && money_after == money_before);
    if (!passed && getenv("MGBA_STAGE58_TRACE") != NULL)
        fprintf(stderr, "mart attempt expected=%u changed=%u returned=%u"
                " pulses=%u/%u"
                " qty=%" PRIu32 "/%" PRIu32 " money=%" PRIu32
                "/%" PRIu32 " cb=%08" PRIx32 " lock=%u\n",
                expect_purchase, changed, returned, *pulses_used, pulse_limit,
                quantity_before,
                quantity_after, money_before, money_after,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, S58_FIELD_LOCK));
    return passed;
}

struct S58MartSales {
    bool ball;
    bool item;
    uint16_t ball_id;
    uint16_t item_id;
    uint32_t final_money;
};

static int s58_item_slot(struct mCore *core, uint16_t item)
{
    uint8_t pocket = read8(core, S58_ITEM_TABLE
                           + (uint32_t)item * S58_ITEM_STRIDE
                           + S58_ITEM_POCKET_OFFSET);
    uint32_t descriptor = pocket > 0U && pocket <= 5U
        ? S58_BAG_POCKETS + (pocket - 1U) * 8U : 0U;
    uint32_t slots = descriptor ? read32(core, descriptor) : 0U;
    uint8_t capacity = descriptor ? read8(core, descriptor + 4U) : 0U;
    if (!s58_ewram_pointer(slots) || capacity == 0U || capacity > 58U)
        return -1;
    for (unsigned slot = 0U; slot < capacity; ++slot) {
        if (read16(core, slots + slot * 4U) == item)
            return (int)slot;
    }
    return -1;
}

static bool s58_prepare_sale_fixture(struct mCore *core, uint16_t item)
{
    uint32_t quantity = s58_item_quantity(core, item);
    if (quantity != 0U
        && s58_call_scheduler_safe(core, S58_REMOVE_BAG_ITEM,
                                   item, quantity, 0U, 0U) != 1U)
        return false;
    if (s58_call_scheduler_safe(core, S58_ADD_BAG_ITEM,
                                item, 1U, 0U, 0U) != 1U
        || s58_item_quantity(core, item) != 1U)
        return false;
    uint8_t pocket = read8(core, S58_ITEM_TABLE
                           + (uint32_t)item * S58_ITEM_STRIDE
                           + S58_ITEM_POCKET_OFFSET);
    int slot = s58_item_slot(core, item);
    if (pocket == 0U || pocket > 5U || slot < 0)
        return false;
    /* OPEN_BAG_LAST consumes this normal persistent UI cursor state.  It is
     * fixture setup before interaction, never a transaction/result write. */
    write16(core, S58_BAG_MENU_STATE + 6U, pocket - 1U);
    write16(core, S58_BAG_MENU_STATE + 8U + (pocket - 1U) * 2U,
            (uint16_t)slot);
    write16(core, S58_BAG_MENU_STATE + 18U + (pocket - 1U) * 2U, 0U);
    run_key_frames(core, 0U, 1U);
    return true;
}

static bool s58_mart_sell_one(struct mCore *core,
                              const struct Stage58Cases *cases,
                              uint16_t item)
{
    uint16_t price = read16(core, S58_ITEM_TABLE
                            + (uint32_t)item * S58_ITEM_STRIDE + 12U);
    if (price == 0U || !s58_prepare_sale_fixture(core, item))
        return false;
    uint32_t money_before = s58_money(core);
    if (!s58_face_and_interact(core, &cases->hub.mart))
        return false;
    /* script_codex_mart prints one greeting before constructing the stock
     * Buy/Sell/Quit menu.  Every transition below is ordinary GBA input. */
    run_key_frames(core, 0U, 600U);
    qol_press(core, QOL_KEY_A, 600U);
    qol_press(core, QOL_KEY_DOWN, 60U);
    qol_press(core, QOL_KEY_A, 900U);
    if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58_BAG_MAIN_CALLBACK
        || read8(core, S58_BAG_MENU_STATE + 4U) != 2U) {
        if (getenv("MGBA_STAGE58_TRACE") != NULL)
            fprintf(stderr, "mart sell bag missing item=%u cb=%08" PRIx32
                    " location=%u pocket=%u\n", item,
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                    read8(core, S58_BAG_MENU_STATE + 4U),
                    read16(core, S58_BAG_MENU_STATE + 6U));
        return false;
    }
    bool changed = false;
    for (unsigned pulse = 0U; pulse < 8U && !changed; ++pulse) {
        qol_press(core, QOL_KEY_A, 240U);
        changed = s58_item_quantity(core, item) == 0U;
    }
    uint32_t money_after = s58_money(core);
    for (unsigned pulse = 0U; pulse < 14U; ++pulse)
        qol_press(core, QOL_KEY_B, 120U);
    bool field = s58_wait_field(core, 12U)
        && s58_hub_position(core, cases, (uint16_t)cases->hub.mart.x,
                            (uint16_t)(cases->hub.mart.y + 1U));
    bool passed = changed && s58_item_quantity(core, item) == 0U
        && money_after == money_before + price / 2U
        && s58_money(core) == money_after && field;
    if (!passed && getenv("MGBA_STAGE58_TRACE") != NULL)
        fprintf(stderr, "mart sell item=%u price=%u changed=%u"
                " qty=%" PRIu32 " money=%" PRIu32 "/%" PRIu32
                "/%" PRIu32 " field=%u cb=%08" PRIx32 " lock=%u\n",
                item, price, changed, s58_item_quantity(core, item),
                money_before, money_after, s58_money(core), field,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, S58_FIELD_LOCK));
    return passed;
}

static bool s58_pc_path(struct mCore *core, const struct Stage58Cases *cases,
                        bool *normal_ui_deposit)
{
    *normal_ui_deposit = false;
    if (getenv("MGBA_STAGE58_TRACE") != NULL)
        fprintf(stderr, "PC begin mailbox=%08" PRIx32
                " cap=%04x request=%u/%" PRIu32
                " last=%" PRIu32 " state=%u/%u pss=%08" PRIx32 "\n",
                read32(core, S58_MAILBOX), read16(core, S58_MAILBOX + 24U),
                read16(core, S58_CODEX_REQUEST + 10U),
                read32(core, S58_CODEX_REQUEST + 92U),
                read32(core, S58_CODEX_STATE + 68U),
                read8(core, S58_CODEX_STATE + 20U),
                read16(core, S58_CODEX_STATE + 16U),
                read32(core, QOL_PSS_DATA));
    if (!s58_walk_to(core, cases, (uint16_t)cases->hub.pc.x,
                     (uint16_t)(cases->hub.pc.y + 1U)))
        return false;
    bool box_was_empty = s58_call_synced(
            core, QOL_GET_BOX_MON_DATA_AT,
            S58_DEPOSIT_BOX, S58_DEPOSIT_SLOT,
            QOL_MON_DATA_SPECIES, 0U) == 0U;
    bool deposit_source_exact = read8(core, S58_PLAYER_COUNT) == 2U
        && s58_call_synced(core, BATTLE_CORE_GET_MON_DATA,
                           S58_PLAYER_MON, QOL_MON_DATA_SPECIES, 0U, 0U)
            == S58_DEPOSIT_SPECIES;
    if (!box_was_empty || !deposit_source_exact)
        return false;
    uint32_t pss_before = read32(core, QOL_PSS_DATA);
    uint64_t video_before = s58_video_hash();
    if (!s58_face_and_interact(core, &cases->hub.pc)) {
        uint32_t active = s58_active_local(
            core, (uint8_t)cases->hub.pc.local_id);
        fprintf(stderr, "PC debug active=%08" PRIx32 " pos=%u,%u\n",
                active, active ? read16(core, active + 0x10U) : 0U,
                active ? read16(core, active + 0x12U) : 0U);
        return false;
    }
    /* Canonical EventScript_PC has boot/access messages and two stock menus;
     * the legacy direct-special fixture has only the final menu.  Advance one
     * default A choice at a time and stop immediately when the real PSS owns
     * its heap, covering both without calling an engine entry point directly. */
    uint32_t pss = 0U;
    for (unsigned pulse = 0U; pulse < 16U; ++pulse) {
        run_key_frames(core, 0U, 180U);
        pss = read32(core, QOL_PSS_DATA);
        if (getenv("MGBA_STAGE58_TRACE") != NULL)
            fprintf(stderr, "PC trace pulse=%u before pss=%08" PRIx32
                    " cb=%08" PRIx32 " script=%" PRIu32 " task0=%08" PRIx32
                    "\n", pulse, pss,
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                    (uint32_t)read8(core, S58_FIELD_LOCK),
                    read32(core, QOL_TASKS));
        if (s58_ewram_pointer(pss))
            break;
        if (pulse == 4U)
            qol_press(core, QOL_KEY_DOWN, 60U);
        qol_press(core, QOL_KEY_A, 420U);
        pss = read32(core, QOL_PSS_DATA);
        if (getenv("MGBA_STAGE58_TRACE") != NULL)
            fprintf(stderr, "PC trace pulse=%u after  pss=%08" PRIx32
                    " cb=%08" PRIx32 " script=%" PRIu32 " task0=%08" PRIx32
                    "\n", pulse, pss,
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                    (uint32_t)read8(core, S58_FIELD_LOCK),
                    read32(core, QOL_TASKS));
        if (s58_ewram_pointer(pss))
            break;
    }
    bool storage_callback = s58_ewram_pointer(pss)
        && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == 0x0808C801U;
    if (!storage_callback) {
        fprintf(stderr, "PC debug storage callback missing pss=%08" PRIx32
                "/%08" PRIx32 " cb=%08" PRIx32
                " script=%" PRIu32 " video=%016" PRIx64 "/%016" PRIx64
                "\n", pss_before, read32(core, QOL_PSS_DATA),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                (uint32_t)read8(core, S58_FIELD_LOCK),
                video_before, s58_video_hash());
        return false;
    }
    uint8_t party_before = read8(core, S58_PLAYER_COUNT);
    /* Deposit was selected in the stock storage-mode menu immediately before
     * PSS launch.  Select party slot 1 and confirm its visible Deposit action. */
    qol_pss_chord(core, QOL_KEY_A);
    run_key_frames(core, 0U, 300U);
    qol_pss_chord(core, QOL_KEY_A);
    run_key_frames(core, 0U, 300U);
    qol_pss_chord(core, QOL_KEY_A);
    run_key_frames(core, 0U, 600U);
    bool field = s58_exit_storage_to_field(core, cases);
    if (field)
        run_key_frames(core, 0U, S58_WARP_FRAMES);
    field = field
        && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S58_CB2_OVERWORLD
        && read8(core, S58_FIELD_LOCK) == 0U
        && s58_hub_position(core, cases, (uint16_t)cases->hub.pc.x,
                            (uint16_t)(cases->hub.pc.y + 1U));
    bool box = s58_call_synced(core, QOL_GET_BOX_MON_DATA_AT,
                               S58_DEPOSIT_BOX, S58_DEPOSIT_SLOT,
                               QOL_MON_DATA_SPECIES, 0U)
        == S58_DEPOSIT_SPECIES;
    bool party_mutated = party_before > 0U
        && read8(core, S58_PLAYER_COUNT) == party_before - 1U;
    *normal_ui_deposit = box_was_empty && deposit_source_exact
        && party_before == 2U && box && party_mutated;
    bool boundaries = s58_codex_boundaries(core);
    if (!field || !box || !party_mutated || !boundaries)
        fprintf(stderr, "PC debug return field=%u box=%u party=%u boundaries=%u"
                " cb=%08" PRIx32 " script=%" PRIu32 "\n",
                field, box, party_mutated, boundaries,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                (uint32_t)read8(core, S58_FIELD_LOCK));
    return field && *normal_ui_deposit && boundaries;
}

static void s58_clear_party(struct mCore *core)
{
    for (unsigned byte = 0U; byte < 6U * QOL_PARTY_MON_SIZE; ++byte)
        write8(core, S58_PLAYER_MON + byte, 0U);
    write8(core, S58_PLAYER_COUNT, 0U);
    run_key_frames(core, 0U, 1U);
}

static void s58_create_mon_scheduler_safe(struct mCore *core,
                                          uint32_t destination,
                                          uint16_t species, uint8_t level)
{
    uint32_t resume_pc = (uint32_t)read_register(core, "pc");
    uint32_t resume_cpsr = (uint32_t)read_register(core, "cpsr");
    uint32_t pipeline = (resume_cpsr & 0x20U) ? 2U : 4U;
    create_mon(core, destination, species, level);
    if ((uint32_t)read_register(core, "pc") != resume_pc) {
        write_register(core, "pc", resume_pc - pipeline);
        if ((uint32_t)read_register(core, "pc") != resume_pc)
            s58_die("CreateMon後scheduler PC復元失敗");
    }
    run_key_frames(core, 0U, 1U);
}

static uint32_t s58_party_data(struct mCore *core, uint32_t field)
{
    return s58_call_scheduler_safe(core, BATTLE_CORE_GET_MON_DATA,
                                   S58_PLAYER_MON, field, 0U, 0U);
}

static void s58_set_party_data(struct mCore *core, uint32_t field,
                               uint32_t value, unsigned size)
{
    uint32_t scratch = QOL_PARTY_SCRATCH + 0x100U;
    if (size == 1U)
        write8(core, scratch, (uint8_t)value);
    else if (size == 2U)
        write16(core, scratch, (uint16_t)value);
    else
        qol_write32(core, scratch, value);
    (void)s58_call_scheduler_safe(core, QOL_SET_BOX_MON_DATA,
                                  S58_PLAYER_MON, field, scratch, 0U);
}

static bool s58_healer_empty_case(struct mCore *core,
                                  const struct Stage58Cases *cases)
{
    s58_clear_party(core);
    return s58_face_and_interact(core, &cases->hub.healer)
        && s58_wait_field(core, 12U)
        && read8(core, S58_PLAYER_COUNT) == 0U
        && s58_hub_position(core, cases, (uint16_t)cases->hub.healer.x,
                            (uint16_t)(cases->hub.healer.y + 1U))
        && s58_codex_boundaries(core);
}

static bool s58_healer_mon_case(struct mCore *core,
                                const struct Stage58Cases *cases,
                                bool egg, bool fainted)
{
    s58_clear_party(core);
    s58_create_mon_scheduler_safe(
        core, S58_PLAYER_MON, S58_DEPOSIT_SPECIES, S58_DEPOSIT_LEVEL);
    write8(core, S58_PLAYER_COUNT, 1U);
    bool two_normal = !egg && !fainted;
    if (two_normal) {
        s58_create_mon_scheduler_safe(
            core, S58_PLAYER_MON + QOL_PARTY_MON_SIZE,
            1U, S58_DEPOSIT_LEVEL);
        write8(core, S58_PLAYER_COUNT, 2U);
    }
    if (egg)
        s58_set_party_data(core, QOL_MON_DATA_IS_EGG, 1U, 1U);
    s58_set_party_data(core, QOL_MON_DATA_HP, fainted ? 0U : 1U, 2U);
    s58_set_party_data(core, QOL_MON_DATA_PP1, 0U, 1U);
    s58_set_party_data(core, QOL_MON_DATA_STATUS, 8U, 4U);
    uint32_t maximum = s58_party_data(core, QOL_MON_DATA_MAX_HP);
    bool interacted = maximum > 1U
        && s58_face_and_interact(core, &cases->hub.healer);
    bool returned = interacted && s58_wait_field(core, 12U);
    if (!returned) {
        if (getenv("MGBA_STAGE58_TRACE") != NULL)
            fprintf(stderr, "healer precheck egg=%u fainted=%u max=%" PRIu32
                    " interacted=%u returned=%u cb=%08" PRIx32
                    " lock=%u count=%u\n", egg, fainted, maximum,
                    interacted, returned,
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                    read8(core, S58_FIELD_LOCK),
                    read8(core, S58_PLAYER_COUNT));
        return false;
    }
    uint32_t hp = s58_party_data(core, QOL_MON_DATA_HP);
    uint32_t pp = s58_party_data(core, QOL_MON_DATA_PP1);
    uint32_t status = s58_party_data(core, QOL_MON_DATA_STATUS);
    uint32_t is_egg = s58_party_data(core, QOL_MON_DATA_IS_EGG);
    bool passed = read8(core, S58_PLAYER_COUNT) == (two_normal ? 2U : 1U)
        && hp == maximum && pp != 0U && status == 0U
        && (!egg || is_egg == 1U) && s58_codex_boundaries(core);
    if (!passed && getenv("MGBA_STAGE58_TRACE") != NULL)
        fprintf(stderr, "healer result egg=%u fainted=%u count=%u/%u"
                " hp=%" PRIu32 "/%" PRIu32 " pp=%" PRIu32
                " status=%" PRIu32 " isegg=%" PRIu32 "\n",
                egg, fainted, read8(core, S58_PLAYER_COUNT),
                two_normal ? 2U : 1U, hp, maximum, pp, status, is_egg);
    return passed;
}

static bool s58_healer_path(struct mCore **core_io,
                            const char *rom, const char *save,
                            const struct Stage58Cases *cases,
                            bool *empty, bool *egg,
                            bool *fainted, bool *normal)
{
    struct mCore *core = *core_io;
    bool *results[4] = {empty, egg, fainted, normal};
    for (unsigned boundary = 0U; boundary < 4U; ++boundary) {
        if (boundary != 0U) {
            qol_close(core);
            core = s58_open(rom, save, false);
            *core_io = core;
            if (!s58_continue_to_hub(core, cases))
                return false;
        }
        if (!s58_thin_quantities_exact(core, cases)
            || !s58_walk_to(core, cases, (uint16_t)cases->hub.healer.x,
                         (uint16_t)(cases->hub.healer.y + 1U)))
            return false;
        if (boundary == 0U)
            *results[boundary] = s58_healer_empty_case(core, cases);
        else if (boundary == 1U)
            *results[boundary] = s58_healer_mon_case(
                core, cases, true, false);
        else if (boundary == 2U)
            *results[boundary] = s58_healer_mon_case(
                core, cases, false, true);
        else
            *results[boundary] = s58_healer_mon_case(
                core, cases, false, false);
        if (!*results[boundary]
            || !s58_thin_quantities_exact(core, cases))
            return false;
    }
    return *empty && *egg && *fainted && *normal;
}

struct S58CodexBattleResult {
    bool request_owned;
    bool battle_start_finish_field_return;
    bool reward_closed_open_closed;
    bool cpu_controller_uninstalled;
    bool cpu_normal_input_field_reward_return;
    bool external_capabilities_preserved;
    bool request_window_preserved;
    bool forfeit_result_kind;
    bool cpu_win_result_kind;
    bool cpu_thin_quantities_preserved;
    bool forfeit_thin_quantities_preserved;
    bool cpu_save_layout_restored;
    bool forfeit_save_layout_restored;
    unsigned natural_requests;
    unsigned natural_cpu_requests;
    uint32_t last_sequence;
    uint32_t external_capabilities;
    uint16_t request_command;
    uint8_t outcome;
    uint8_t result_kind;
    uint8_t cpu_outcome;
    uint8_t cpu_result_kind;
    uint64_t save_seen_before_hash;
    uint64_t save_personality_before_hash;
    uint64_t save_owned_before_hash;
    uint64_t save_seen_cpu_hash;
    uint64_t save_personality_cpu_hash;
    uint64_t save_owned_cpu_hash;
    uint64_t save_seen_forfeit_hash;
    uint64_t save_personality_forfeit_hash;
    uint64_t save_owned_forfeit_hash;
};

static void s58_put16(uint8_t *destination, unsigned offset, uint16_t value)
{
    destination[offset] = (uint8_t)value;
    destination[offset + 1U] = (uint8_t)(value >> 8U);
}

static void s58_put32(uint8_t *destination, unsigned offset, uint32_t value)
{
    for (unsigned byte = 0U; byte < 4U; ++byte)
        destination[offset + byte] = (uint8_t)(value >> (byte * 8U));
}

static uint32_t s58_crc_bytes(const uint8_t *bytes, unsigned size)
{
    uint32_t crc = UINT32_C(0xFFFFFFFF);
    for (unsigned index = 0U; index < size; ++index)
        crc = s58_crc_byte(crc, bytes[index]);
    return crc ^ UINT32_C(0xFFFFFFFF);
}

static uint32_t s58_codex_next_sequence(struct mCore *core)
{
    uint32_t sequence = read32(core, S58_CODEX_STATE + 68U) + 1U;
    return sequence ? sequence : 1U;
}

static void s58_codex_build_request(struct mCore *core, uint8_t request[96],
                                    uint16_t command, const uint8_t *payload,
                                    uint16_t size, uint32_t sequence)
{
    memset(request, 0, 96U);
    s58_put32(request, 0U, read32(core, S58_CODEX_STATE + 8U));
    s58_put32(request, 4U, read32(core, S58_CODEX_STATE + 12U));
    s58_put16(request, 8U, read16(core, S58_CODEX_STATE + 16U));
    s58_put16(request, 10U, command);
    s58_put16(request, 12U, read16(core, S58_CODEX_STATE + 28U));
    s58_put16(request, 14U, size);
    if (payload != NULL && size <= 64U)
        memcpy(request + 20U, payload, size);
    s58_put32(request, 16U,
              s58_crc_bytes(request + 20U, size <= 64U ? size : 0U));
    s58_put32(request, 84U, s58_crc_bytes(request, 84U));
    s58_put32(request, 88U, ~sequence);
    s58_put32(request, 92U, sequence);
}

static void s58_codex_write_request(struct mCore *core,
                                    const uint8_t request[96])
{
    /* The external side owns only this 96-byte request window.  Runtime,
     * result, battle outcome and reward-owner fields remain ROM-owned. */
    for (unsigned byte = 0U; byte < 96U; ++byte)
        write8(core, S58_CODEX_REQUEST + byte, request[byte]);
}

static bool s58_codex_request_accepted(struct mCore *core,
                                       uint32_t sequence,
                                       uint16_t command,
                                       uint16_t phase)
{
    return read32(core, S58_MAILBOX) == S58_MAILBOX_MAGIC
        && read32(core, S58_MAILBOX + 72U) == sequence
        && read16(core, S58_MAILBOX + 80U) == S58_CODEX_STATUS_ACCEPTED
        && read16(core, S58_MAILBOX + 82U) == 0U
        && read16(core, S58_MAILBOX + 84U) == command
        && read32(core, S58_MAILBOX + 88U) == sequence
        && read32(core, S58_MAILBOX + 24U)
            == S58_CODEX_EXTERNAL_CAPABILITIES
        && read16(core, S58_CODEX_REQUEST + 10U) == command
        && read32(core, S58_CODEX_REQUEST + 88U) == ~sequence
        && read32(core, S58_CODEX_REQUEST + 92U) == sequence
        && read32(core, S58_CODEX_STATE + 68U) == sequence
        && (read16(core, S58_CODEX_STATE + 16U) == phase
            || (command == S58_CODEX_COMMAND_DISCONNECT_CPU
                && phase == S58_CODEX_PHASE_RESOLVING
                && read16(core, S58_CODEX_STATE + 16U)
                    == S58_CODEX_PHASE_CPU));
}

static bool s58_codex_send_field(struct mCore *core, uint16_t command,
                                 const uint8_t *payload, uint16_t size,
                                 uint16_t phase)
{
    uint32_t sequence = s58_codex_next_sequence(core);
    uint32_t hook_before = read32(core, S58_MAILBOX + 56U);
    uint8_t request[96];
    s58_codex_build_request(core, request, command, payload, size, sequence);
    s58_codex_write_request(core, request);
    /* The external side publishes the request only.  Consumption belongs to
     * the installed ReadKeys owner chain during ordinary emulated frames. */
    for (unsigned frame = 0U; frame < 360U; ++frame) {
        run_key_frames(core, 0U, 1U);
        if (read32(core, S58_MAILBOX + 72U) == sequence)
            break;
    }
    bool accepted = s58_codex_request_accepted(
        core, sequence, command, phase);
    if (!accepted && getenv("MGBA_STAGE58_TRACE") != NULL)
        fprintf(stderr, "Codex field request fail command=%u"
                " wanted=%" PRIu32 " mailbox=%" PRIu32
                " status=%u error=%u echoed=%u/%" PRIu32
                " state_seq=%" PRIu32 " phase=%u/%u"
                " cap=%08" PRIx32 " hook=%" PRIu32 "/%" PRIu32
                " pc=%08" PRIx32 "\n",
                command, sequence, read32(core, S58_MAILBOX + 72U),
                read16(core, S58_MAILBOX + 80U),
                read16(core, S58_MAILBOX + 82U),
                read16(core, S58_MAILBOX + 84U),
                read32(core, S58_MAILBOX + 88U),
                read32(core, S58_CODEX_STATE + 68U),
                read16(core, S58_CODEX_STATE + 16U), phase,
                read32(core, S58_MAILBOX + 24U),
                hook_before, read32(core, S58_MAILBOX + 56U),
                (uint32_t)read_register(core, "pc"));
    return accepted;
}

static bool s58_codex_send_live(struct mCore *core, uint16_t command,
                                const uint8_t *payload, uint16_t size,
                                uint16_t phase, uint32_t *sequence_out)
{
    uint32_t sequence = s58_codex_next_sequence(core);
    uint32_t hook_before = read32(core, S58_MAILBOX + 56U);
    uint8_t request[96];
    s58_codex_build_request(core, request, command, payload, size, sequence);
    s58_codex_write_request(core, request);
    for (unsigned frame = 0U; frame < 360U; ++frame) {
        run_key_frames(core, 0U, 1U);
        if (read32(core, S58_MAILBOX + 72U) == sequence)
            break;
    }
    *sequence_out = sequence;
    bool accepted = s58_codex_request_accepted(
        core, sequence, command, phase);
    if (!accepted && getenv("MGBA_STAGE58_TRACE") != NULL)
        fprintf(stderr, "Codex request fail command=%u wanted=%" PRIu32
                " mailbox=%" PRIu32 " status=%u error=%u echoed=%u/%"
                PRIu32 " state_seq=%" PRIu32 " phase=%u/%u\n",
                command, sequence, read32(core, S58_MAILBOX + 72U),
                read16(core, S58_MAILBOX + 80U),
                read16(core, S58_MAILBOX + 82U),
                read16(core, S58_MAILBOX + 84U),
                read32(core, S58_MAILBOX + 88U),
                read32(core, S58_CODEX_STATE + 68U),
                read16(core, S58_CODEX_STATE + 16U), phase);
    if (!accepted && getenv("MGBA_STAGE58_TRACE") != NULL)
        fprintf(stderr, "Codex hook/request counter=%" PRIu32 "/%" PRIu32
                " request=%u seq=%" PRIu32 "/%" PRIu32
                " session=%08" PRIx32 "/%08" PRIx32
                " match=%08" PRIx32 "/%08" PRIx32 "\n",
                hook_before, read32(core, S58_MAILBOX + 56U),
                read16(core, S58_CODEX_REQUEST + 10U),
                read32(core, S58_CODEX_REQUEST + 92U),
                ~read32(core, S58_CODEX_REQUEST + 88U),
                read32(core, S58_CODEX_REQUEST),
                read32(core, S58_CODEX_STATE + 8U),
                read32(core, S58_CODEX_REQUEST + 4U),
                read32(core, S58_CODEX_STATE + 12U));
    return accepted;
}

static void s58_codex_member(uint8_t member[32], uint16_t species,
                             uint16_t item)
{
    memset(member, 0, 32U);
    s58_put16(member, 0U, species);
    member[2] = 5U;
    s58_put16(member, 4U, item);
    s58_put16(member, 6U, 150U); /* Splash: deterministic non-damaging move. */
    member[29] = 3U;             /* held item and move-1 are present. */
}

static bool s58_codex_prepare_external_team(struct mCore *core,
                                             unsigned *natural_requests)
{
    *natural_requests = 0U;
    uint32_t nonce = UINT32_C(0x58C0D001);
    if (getenv("MGBA_STAGE58_TRACE") != NULL)
        fprintf(stderr, "Codex prep before initialize pc=%08" PRIx32
                " cap=%08" PRIx32 " active=%u phase=%u\n",
                (uint32_t)read_register(core, "pc"),
                read32(core, S58_MAILBOX + 24U),
                read8(core, S58_CODEX_STATE + 20U),
                read16(core, S58_CODEX_STATE + 16U));
    if (s58_call_scheduler_safe(core, S58_CODEX_TEST_INITIALIZE,
                                nonce, 0U, 0U, 0U) != nonce)
        return false;
    if (getenv("MGBA_STAGE58_TRACE") != NULL)
        fprintf(stderr, "Codex prep after initialize pc=%08" PRIx32
                " cap=%08" PRIx32 " active=%u phase=%u\n",
                (uint32_t)read_register(core, "pc"),
                read32(core, S58_MAILBOX + 24U),
                read8(core, S58_CODEX_STATE + 20U),
                read16(core, S58_CODEX_STATE + 16U));
    s58_clear_party(core);
    for (unsigned slot = 0U; slot < 6U; ++slot)
        s58_create_mon_scheduler_safe(
            core, S58_PLAYER_MON + slot * QOL_PARTY_MON_SIZE,
            (uint16_t)(slot + 1U), 100U);
    /* CreateMon's level-up move result is species-table dependent.  Seed the
     * selected lead with one deterministic legal damaging move as prebattle
     * fixture state, then let the stock battle UI/controller own its use and
     * every resulting HP/outcome transition. */
    s58_set_party_data(core, S58_MON_DATA_MOVE1, 33U, 2U);
    s58_set_party_data(core, QOL_MON_DATA_PP1, 35U, 1U);
    write8(core, S58_PLAYER_COUNT, 6U);
    for (unsigned slot = 0U; slot < 6U; ++slot)
        write8(core, S58_CODEX_SELECTED + slot, (uint8_t)(0xA0U + slot));
    uint8_t level_mode[1] = {1U};
    if (!s58_codex_send_field(core, S58_CODEX_COMMAND_CONFIGURE,
                              level_mode, sizeof(level_mode),
                              S58_CODEX_PHASE_CONFIGURING))
        return false;
    ++*natural_requests;
    for (unsigned slot = 0U; slot < 6U; ++slot) {
        uint8_t payload[33];
        payload[0] = (uint8_t)slot;
        s58_codex_member(payload + 1U, (uint16_t)(slot + 1U),
                         (uint16_t)(179U + slot));
        if (!s58_codex_send_field(core, S58_CODEX_COMMAND_UPLOAD,
                                  payload, sizeof(payload),
                                  S58_CODEX_PHASE_CONFIGURING))
            return false;
        ++*natural_requests;
    }
    const uint8_t selection[3] = {1U, 2U, 3U};
    if (!s58_codex_send_field(core, S58_CODEX_COMMAND_COMMIT,
                              NULL, 0U, S58_CODEX_PHASE_TEAM_PREVIEW))
        return false;
    ++*natural_requests;
    if (!s58_codex_send_field(core, S58_CODEX_COMMAND_CHOOSE_TEAM,
                              selection, sizeof(selection),
                              S58_CODEX_PHASE_TEAM_PREVIEW))
        return false;
    ++*natural_requests;
    return true;
}

static bool s58_codex_enter_action(struct mCore *core,
                                   const struct Stage58Cases *cases,
                                   unsigned *natural_requests)
{
    if (!s58_codex_boundaries(core)
        || !s58_codex_prepare_external_team(core, natural_requests)
        || !s58_walk_to(core, cases, (uint16_t)cases->hub.npc.x,
                        (uint16_t)(cases->hub.npc.y + 1U))
        || !s58_face_and_interact(core, &cases->hub.npc))
        return false;
    for (unsigned prompt = 0U; prompt < 20U
            && read16(core, S58_CODEX_STATE + 16U)
                != S58_CODEX_PHASE_PLAYER_SELECTION; ++prompt)
        qol_press(core, QOL_KEY_A, 180U);
    if (read16(core, S58_CODEX_STATE + 16U)
            != S58_CODEX_PHASE_PLAYER_SELECTION)
        return false;

    /* Select the first three party members and confirm through the stock
     * party UI.  No selected-slot or phase field is written by the host. */
    for (unsigned slot = 0U; slot < 3U; ++slot) {
        qol_press(core, QOL_KEY_A, 90U);
        qol_press(core, QOL_KEY_A, 120U);
        if (slot < 2U)
            qol_press(core, QOL_KEY_DOWN, 60U);
    }
    for (unsigned confirm = 0U; confirm < 8U; ++confirm) {
        qol_press(core, QOL_KEY_A, 120U);
        if (read16(core, S58_CODEX_STATE + 16U)
                != S58_CODEX_PHASE_PLAYER_SELECTION)
            break;
    }
    for (unsigned pulse = 0U; pulse < 1600U; ++pulse) {
        if (read8(core, S58_CODEX_STATE + 20U) != 0U
            && read16(core, S58_CODEX_STATE + 16U)
                == S58_CODEX_PHASE_ACTION
            && s58_rom_pointer(
                read32(core, S58_CODEX_OPPONENT_ACTION_POINTER))
            && (read32(core, S58_CODEX_OPPONENT_ACTION_POINTER) & 1U)
            && read8(core, S58_CODEX_STATE + 47U) != 0U)
            return true;
        qol_press(core, QOL_KEY_A, 8U);
    }
    return false;
}

static bool s58_codex_cpu_disconnect_path(
    struct mCore *core, const struct Stage58Cases *cases,
    struct S58CodexBattleResult *result)
{
    uint32_t sequence = 0U;
    s58_trace_bag_item(core, "cpu-before-enter", 84U);
    if (!s58_codex_enter_action(
            core, cases, &result->natural_cpu_requests))
        return false;
    s58_trace_bag_item(core, "cpu-after-enter", 84U);
    bool cpu = s58_codex_send_live(
        core, S58_CODEX_COMMAND_DISCONNECT_CPU,
        NULL, 0U, S58_CODEX_PHASE_RESOLVING, &sequence);
    if (cpu)
        ++result->natural_cpu_requests;
    s58_trace_bag_item(core, "cpu-after-command8", 84U);
    for (unsigned frame = 0U; cpu && frame < 360U; ++frame) {
        uint16_t live_phase = read16(core, S58_CODEX_STATE + 16U);
        bool advanced = live_phase == S58_CODEX_PHASE_CPU
            || live_phase == S58_CODEX_PHASE_RESOLVING
            || live_phase == S58_CODEX_PHASE_RESULT
            || read8(core, ADDR_BATTLERS_COUNT) != 0U
            || read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58_CB2_OVERWORLD;
        if (read8(core, S58_CODEX_STATE + 45U) == 1U
            && read8(core, S58_CODEX_STATE + 47U) == 0U
            && advanced)
            break;
        run_key_frames(core, 0U, 1U);
    }
    uint16_t live_phase = read16(core, S58_CODEX_STATE + 16U);
    bool advanced = live_phase == S58_CODEX_PHASE_CPU
        || live_phase == S58_CODEX_PHASE_RESOLVING
        || live_phase == S58_CODEX_PHASE_RESULT
        || read8(core, ADDR_BATTLERS_COUNT) != 0U
        || read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58_CB2_OVERWORLD;
    result->cpu_controller_uninstalled = cpu
        && read8(core, S58_CODEX_STATE + 45U) == 1U
        && read8(core, S58_CODEX_STATE + 47U) == 0U
        && advanced;
    if (!result->cpu_controller_uninstalled)
        return false;

    bool battle_seen = false;
    bool reward_open = false;
    bool reward_closed = false;
    struct S58BagTraceState trace_bag = {
        .save1 = read32(core, QOL_SAVE_BLOCK1_SLOT),
        .save2 = read32(core, QOL_SAVE_BLOCK2_SLOT),
    };
    trace_bag.key = s58_ewram_pointer(trace_bag.save2)
        ? read16(core, trace_bag.save2 + S58_SAVE2_KEY_OFFSET) : 0U;
    trace_bag.raw = s58_item_raw_quantity(
        core, 84U, &trace_bag.slots);
    for (unsigned pulse = 0U; pulse < 6000U; ++pulse) {
        s58_trace_bag_transition(
            core, "Codex CPU bag transition", pulse, &trace_bag);
        if (getenv("MGBA_STAGE58_TRACE") != NULL && pulse % 25U == 0U)
            fprintf(stderr, "Codex CPU pulse=%u pc=%08" PRIx32
                    " cb1=%08" PRIx32 " cb2=%08" PRIx32
                    " saved=%08" PRIx32 " flags=%08" PRIx32
                    " battlers=%u activeb=%u exec=%08" PRIx32
                    " commands=%u/%u controllers=%08" PRIx32
                    "/%08" PRIx32 " main=%08" PRIx32
                    " keys=%04x/%04x cursors=%u/%u"
                    " chosen=%u/%u"
                    " bmoves=%u,%u,%u,%u bpp=%u,%u,%u,%u"
                    " hp=%u/%u outcome=%u phase=%u controller=%u/%u\n",
                    pulse, (uint32_t)read_register(core, "pc"),
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2 - 4U),
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2 + 4U),
                    read32(core, ADDR_BATTLE_TYPE_FLAGS),
                    read8(core, ADDR_BATTLERS_COUNT),
                    read8(core, 0x02023B24U),
                    read32(core, 0x02023B28U),
                    read8(core, 0x02022B24U),
                    read8(core, 0x02022D24U),
                    read32(core, 0x03005020U),
                    read32(core, 0x03005024U),
                    read32(core, 0x03004FC4U),
                    read16(core, 0x03003158U),
                    read16(core, 0x0300315EU),
                    read8(core, BATTLE_CORE_ACTION_SELECTION_CURSOR),
                    read8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR),
                    read8(core, BATTLE_CORE_CHOSEN_ACTIONS),
                    read16(core, BATTLE_CORE_CHOSEN_MOVES),
                    read16(core, ADDR_BATTLE_MONS + BATTLE_MON_MOVES_OFFSET),
                    read16(core, ADDR_BATTLE_MONS
                                      + BATTLE_MON_MOVES_OFFSET + 2U),
                    read16(core, ADDR_BATTLE_MONS
                                      + BATTLE_MON_MOVES_OFFSET + 4U),
                    read16(core, ADDR_BATTLE_MONS
                                      + BATTLE_MON_MOVES_OFFSET + 6U),
                    read8(core, ADDR_BATTLE_MONS + BATTLE_MON_PP_OFFSET),
                    read8(core, ADDR_BATTLE_MONS
                                     + BATTLE_MON_PP_OFFSET + 1U),
                    read8(core, ADDR_BATTLE_MONS
                                     + BATTLE_MON_PP_OFFSET + 2U),
                    read8(core, ADDR_BATTLE_MONS
                                     + BATTLE_MON_PP_OFFSET + 3U),
                    read16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_HP),
                    read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                                      + BATTLE_CORE_MON_HP),
                    read8(core, BATTLE_CORE_BATTLE_OUTCOME),
                    read16(core, S58_CODEX_STATE + 16U),
                    read8(core, S58_CODEX_STATE + 47U),
                    read8(core, S58_CODEX_STATE + 45U));
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58_CB2_OVERWORLD
            || read8(core, ADDR_BATTLERS_COUNT) != 0U)
            battle_seen = true;
        if (!reward_open
            && s58_reward_valid_window(core, S58_REWARD_WINDOW_OPEN)) {
            reward_open = true;
            result->cpu_outcome = read8(core, BATTLE_CORE_BATTLE_OUTCOME);
            result->cpu_result_kind = read8(
                core, S58_REWARD_OWNER + 22U);
            result->cpu_win_result_kind = result->cpu_outcome == 1U
                && result->cpu_result_kind == 1U;
        }
        if (reward_open && !reward_closed) {
            bool closed = s58_codex_send_live(
                core, S58_CODEX_COMMAND_REWARD_CLOSE,
                NULL, 0U, S58_CODEX_PHASE_IDLE, &sequence);
            if (closed)
                ++result->natural_cpu_requests;
            reward_closed = closed
                && s58_reward_valid_window(
                    core, S58_REWARD_WINDOW_CLOSED);
        }
        bool field = read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                == S58_CB2_OVERWORLD
            && read8(core, S58_FIELD_LOCK) == 0U
            && s58_hub_position(core, cases,
                                (uint16_t)cases->hub.npc.x,
                                (uint16_t)(cases->hub.npc.y + 1U));
        if (battle_seen && reward_open && reward_closed && field
            && read8(core, S58_CODEX_STATE + 20U) == 0U) {
            run_key_frames(core, 0U, S58_FIELD_SETTLE);
            result->cpu_normal_input_field_reward_return =
                result->natural_cpu_requests == 11U
                && result->cpu_win_result_kind
                && read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                    == S58_CB2_OVERWORLD
                && read8(core, S58_FIELD_LOCK) == 0U
                && read32(core, S58_MAILBOX + 24U)
                    == S58_CODEX_EXTERNAL_CAPABILITIES;
            return result->cpu_normal_input_field_reward_return;
        }
        /* After command 8 the stock opponent CPU owns its controller.  Match
         * the stock battle-runner cadence: a two-frame ordinary A press and
         * a full menu/animation release window.  When set battle style offers
         * an optional switch after an opponent faint, the real player
         * controller opens CONTROLLER_CHOOSEPOKEMON; ordinary B declines it
         * so selecting the already-active first slot cannot loop forever. */
        uint16_t key = read8(core, 0x02022B24U)
                == S58_CONTROLLER_CHOOSE_POKEMON
            ? QOL_KEY_B : QOL_KEY_A;
        if (getenv("MGBA_STAGE58_TRACE") == NULL) {
            qol_press(core, key, BATTLE_CORE_MENU_INPUT_WAIT);
        } else {
            for (unsigned frame = 0U;
                 frame < 2U + BATTLE_CORE_MENU_INPUT_WAIT; ++frame) {
                run_key_frames(core, frame < 2U ? key : 0U, 1U);
                s58_trace_bag_transition(
                    core, "Codex CPU bag frame",
                    pulse * (2U + BATTLE_CORE_MENU_INPUT_WAIT) + frame,
                    &trace_bag);
            }
        }
    }
    fprintf(stderr, "Codex CPU disconnect debug pc=%08" PRIx32
            " cb1=%08" PRIx32 " cb2=%08" PRIx32
            " saved=%08" PRIx32 " flags=%08" PRIx32
            " lock=%u active=%u phase=%u controller=%u mode=%u"
            " reward=%u/%u requests=%u\n",
            (uint32_t)read_register(core, "pc"),
            read32(core, BATTLE_CORE_MAIN_CALLBACK2 - 4U),
            read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            read32(core, BATTLE_CORE_MAIN_CALLBACK2 + 4U),
            read32(core, ADDR_BATTLE_TYPE_FLAGS),
            read8(core, S58_FIELD_LOCK),
            read8(core, S58_CODEX_STATE + 20U),
            read16(core, S58_CODEX_STATE + 16U),
            read8(core, S58_CODEX_STATE + 47U),
            read8(core, S58_CODEX_STATE + 45U), reward_open, reward_closed,
            result->natural_cpu_requests);
    return false;
}

static bool s58_codex_battle_path(struct mCore *core,
                                  const struct Stage58Cases *cases,
    struct S58CodexBattleResult *result)
{
    bool closed_before = s58_codex_boundaries(core);
    if (!closed_before || !s58_codex_enter_action(
            core, cases, &result->natural_requests))
        return false;

    bool battle_started = false;
    bool forfeit = false;
    bool forfeit_attempted = false;
    bool reward_open = false;
    bool reward_closed = false;
    uint32_t sequence = 0U;
    for (unsigned pulse = 0U; pulse < 1600U; ++pulse) {
        if (getenv("MGBA_STAGE58_TRACE") != NULL && pulse % 100U == 0U)
            fprintf(stderr, "Codex battle pulse=%u phase=%u active=%u"
                    " cb=%08" PRIx32 " battlers=%u newbs=%08" PRIx32
                    " controller=%08" PRIx32 "/%u"
                    " forfeit=%u reward=%u/%u outcome=%u\n", pulse,
                    read16(core, S58_CODEX_STATE + 16U),
                    read8(core, S58_CODEX_STATE + 20U),
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                    read8(core, ADDR_BATTLERS_COUNT),
                    read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
                    read32(core, S58_CODEX_OPPONENT_ACTION_POINTER),
                    read8(core, S58_CODEX_STATE + 47U), forfeit,
                    reward_open, reward_closed, result->outcome);
        if (read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U
            || read8(core, ADDR_BATTLERS_COUNT) != 0U)
            battle_started = true;
        uint8_t outcome = read8(core, BATTLE_CORE_BATTLE_OUTCOME);
        if (outcome != 0U)
            result->outcome = outcome;
        if (!forfeit_attempted && battle_started
            && read8(core, S58_CODEX_STATE + 20U) != 0U
            && read16(core, S58_CODEX_STATE + 16U)
                == S58_CODEX_PHASE_ACTION
            && s58_rom_pointer(
                read32(core, S58_CODEX_OPPONENT_ACTION_POINTER))
            && (read32(core, S58_CODEX_OPPONENT_ACTION_POINTER) & 1U)
            && read8(core, S58_CODEX_STATE + 47U) != 0U) {
            if (getenv("MGBA_STAGE58_TRACE") != NULL)
                fprintf(stderr, "Codex forfeit send pulse=%u cb=%08" PRIx32
                        " battlers=%u newbs=%08" PRIx32
                        " battle_heap=%08" PRIx32 "/%08" PRIx32
                        " anim_heap=%08" PRIx32 "/%08" PRIx32
                        " battle_flags=%08" PRIx32
                        " phase=%u turn=%u\n", pulse,
                        read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                        read8(core, ADDR_BATTLERS_COUNT),
                        read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
                        read32(core, 0x02023F4CU),
                        read32(core, 0x02023F50U),
                        read32(core, 0x02022B18U),
                        read32(core, 0x02022B1CU),
                        read32(core, 0x02022AACU),
                        read16(core, S58_CODEX_STATE + 16U),
                        read16(core, S58_CODEX_STATE + 28U));
            forfeit_attempted = true;
            forfeit = s58_codex_send_live(
                core, S58_CODEX_COMMAND_DISCONNECT_FORFEIT,
                NULL, 0U, S58_CODEX_PHASE_RESOLVING, &sequence);
            if (forfeit)
                ++result->natural_requests;
            result->request_owned = forfeit;
            result->last_sequence = sequence;
            if (!forfeit)
                goto failure;
        }
        if (!reward_open
            && s58_reward_valid_window(core, S58_REWARD_WINDOW_OPEN)) {
            reward_open = true;
            result->result_kind = read8(core, S58_REWARD_OWNER + 22U);
            result->forfeit_result_kind = result->result_kind == 4U;
        }
        if (reward_open && !reward_closed) {
            bool closed = s58_codex_send_live(
                core, S58_CODEX_COMMAND_REWARD_CLOSE,
                NULL, 0U, S58_CODEX_PHASE_IDLE, &sequence);
            if (closed)
                ++result->natural_requests;
            reward_closed = closed
                && s58_reward_valid_window(
                    core, S58_REWARD_WINDOW_CLOSED);
            result->last_sequence = sequence;
        }
        bool field = read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                == S58_CB2_OVERWORLD
            && read8(core, S58_FIELD_LOCK) == 0U
            && s58_hub_position(core, cases,
                                (uint16_t)cases->hub.npc.x,
                                (uint16_t)(cases->hub.npc.y + 1U));
        if (battle_started && forfeit && reward_open && reward_closed
            && field && read8(core, S58_CODEX_STATE + 20U) == 0U) {
            run_key_frames(core, 0U, S58_FIELD_SETTLE);
            result->battle_start_finish_field_return =
                read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                    == S58_CB2_OVERWORLD
                && read8(core, S58_FIELD_LOCK) == 0U;
            result->reward_closed_open_closed = closed_before
                && s58_reward_valid_window(
                    core, S58_REWARD_WINDOW_CLOSED);
            result->external_capabilities =
                read32(core, S58_MAILBOX + 24U);
            result->request_command =
                read16(core, S58_CODEX_REQUEST + 10U);
            result->external_capabilities_preserved =
                result->external_capabilities
                    == S58_CODEX_EXTERNAL_CAPABILITIES;
            result->request_window_preserved =
                result->request_command == S58_CODEX_COMMAND_REWARD_CLOSE
                && read32(core, S58_CODEX_REQUEST + 88U) == ~sequence
                && read32(core, S58_CODEX_REQUEST + 92U) == sequence;
            return result->request_owned
                && result->natural_requests == 11U
                && result->forfeit_result_kind
                && result->battle_start_finish_field_return
                && result->reward_closed_open_closed
                && result->external_capabilities_preserved
                && result->request_window_preserved;
        }
        qol_press(core, QOL_KEY_A, 30U);
    }

failure:
    fprintf(stderr, "Codex normal battle debug cb=%08" PRIx32
            " lock=%u active=%u phase=%u turn=%u battlers=%u"
            " newbs=%08" PRIx32 " outcome=%u request=%u"
            " reward=%u/%u owner=%u field=%u\n",
            read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            read8(core, S58_FIELD_LOCK),
            read8(core, S58_CODEX_STATE + 20U),
            read16(core, S58_CODEX_STATE + 16U),
            read16(core, S58_CODEX_STATE + 28U),
            read8(core, ADDR_BATTLERS_COUNT),
            read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER), result->outcome,
            result->request_owned,
            s58_reward_valid_window(core, S58_REWARD_WINDOW_OPEN),
            s58_reward_valid_window(core, S58_REWARD_WINDOW_CLOSED),
            read8(core, S58_REWARD_OWNER + 20U),
            s58_hub_position(core, cases,
                             (uint16_t)cases->hub.npc.x,
                             (uint16_t)(cases->hub.npc.y + 1U)));
    return false;
}

static bool s58_mart_path(struct mCore *core,
                          const struct Stage58Cases *cases,
                          bool *purchase, bool *bag_full,
                          struct S58MartSales *sales)
{
    /* The JP engine derives every pocket pointer from the current rotated
     * SaveBlock.  Establish that runtime table while the field is quiescent;
     * fixed English/decomp SaveBlock offsets are deliberately not used. */
    (void)s58_call_synced(core, S58_SET_BAG_POCKETS_POINTERS,
                          0U, 0U, 0U, 0U);
    if (!s58_walk_to(core, cases, (uint16_t)cases->hub.mart.x,
                     (uint16_t)(cases->hub.mart.y + 1U))) {
        if (getenv("MGBA_STAGE58_TRACE") != NULL) {
            uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
            fprintf(stderr, "mart walk failed cb=%08" PRIx32
                    " lock=%u save=%u,%u\n",
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                    read8(core, S58_FIELD_LOCK), read16(core, save1),
                    read16(core, save1 + 2U));
        }
        return false;
    }
    uint32_t quantities[S58_MART_LIMIT] = {0};
    for (unsigned index = 0U; index < cases->hub.mart_item_count; ++index)
        quantities[index] = s58_item_quantity(
            core, cases->hub.mart_items[index]);
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    if (!s58_ewram_pointer(save1) || !s58_ewram_pointer(save2))
        return false;
    uint32_t encrypted_money = read32(core, save1 + S58_SAVE1_MONEY_OFFSET);
    uint32_t encryption_key = read32(core, save2 + S58_SAVE2_KEY_OFFSET);
    uint64_t video_before = s58_video_hash();
    if (!s58_face_and_interact(core, &cases->hub.mart)) {
        if (getenv("MGBA_STAGE58_TRACE") != NULL) {
            fprintf(stderr, "mart interaction object missing\n");
            for (unsigned index = 0U; index < S58_OBJECT_EVENT_CAPACITY;
                 ++index) {
                uint32_t row = S58_OBJECT_EVENTS
                    + index * S58_OBJECT_EVENT_SIZE;
                if (read8(core, row) & 1U)
                    fprintf(stderr, "active[%u] local=%u pos=%u,%u\n", index,
                            read8(core, row + 8U), read16(core, row + 0x10U),
                            read16(core, row + 0x12U));
            }
        }
        return false;
    }
    bool shop_visible = false;
    for (unsigned pulse = 0U; pulse < 8U && !shop_visible; ++pulse) {
        run_key_frames(core, 0U, 90U);
        shop_visible = read8(core, S58_FIELD_LOCK) != 0U
            && s58_video_hash() != video_before;
        if (!shop_visible)
            qol_press(core, QOL_KEY_A, 60U);
    }
    if (!shop_visible)
        return false;
    qol_press(core, QOL_KEY_DOWN, 30U);
    qol_press(core, QOL_KEY_UP, 30U);
    for (unsigned pulse = 0U; pulse < 10U; ++pulse)
        qol_press(core, QOL_KEY_B, 90U);
    bool unchanged = read32(core, save1 + S58_SAVE1_MONEY_OFFSET)
            == encrypted_money
        && read32(core, save2 + S58_SAVE2_KEY_OFFSET) == encryption_key;
    for (unsigned index = 0U; index < cases->hub.mart_item_count; ++index)
        unchanged = unchanged && s58_item_quantity(
            core, cases->hub.mart_items[index]) == quantities[index];
    bool cancelled = shop_visible && unchanged && s58_wait_field(core, 12U)
        && s58_codex_boundaries(core);
    if (!cancelled || cases->hub.mart_item_count == 0U) {
        if (getenv("MGBA_STAGE58_TRACE") != NULL)
            fprintf(stderr, "mart cancel failed visible=%u unchanged=%u"
                    " cancelled=%u count=%u cb=%08" PRIx32 " lock=%u\n",
                    shop_visible, unchanged, cancelled,
                    cases->hub.mart_item_count,
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                    read8(core, S58_FIELD_LOCK));
        return false;
    }

    uint16_t target = cases->hub.mart_items[0];
    uint32_t target_price = read32(core, S58_ITEM_TABLE
                                  + (uint32_t)target * S58_ITEM_STRIDE + 12U);
    uint8_t pocket = read8(core, S58_ITEM_TABLE
                           + (uint32_t)target * S58_ITEM_STRIDE
                           + S58_ITEM_POCKET_OFFSET);
    uint32_t descriptor = pocket > 0U && pocket <= 5U
        ? S58_BAG_POCKETS + (pocket - 1U) * 8U : 0U;
    uint32_t pocket_slots = descriptor ? read32(core, descriptor) : 0U;
    uint8_t pocket_capacity = descriptor
        ? read8(core, descriptor + 4U) : 0U;
    if (!s58_ewram_pointer(pocket_slots)
        || pocket_capacity != S58_MART_ITEMS_CAPACITY) {
        if (getenv("MGBA_STAGE58_TRACE") != NULL)
            fprintf(stderr, "mart target pocket differs item=%u pocket=%u\n",
                    target, pocket);
        return false;
    }

    /* First complete exactly one ordinary purchase.  The pulse at which the
     * quantity changes is the transaction boundary; stop there so the runner
     * cannot accidentally buy several copies through A-repeat. */
    s58_set_money(core, 100000U);
    unsigned purchase_pulses = 0U;
    *purchase = s58_mart_purchase_attempt(
            core, cases, target, 18U, true, &purchase_pulses)
        && purchase_pulses != 0U
        && s58_item_quantity(core, target) == quantities[0] + 1U
        && target_price != 0U && target_price <= 100000U
        && s58_money(core) == 100000U - target_price;
    if (!*purchase)
        return false;

    /* Preserve that purchased copy, then replace only the runtime-resolved
     * pocket with a full fixture.  The failure path receives the same number
     * of A confirmations as the successful transaction and no more. */
    uint32_t purchased_money = s58_money(core);
    save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    descriptor = S58_BAG_POCKETS + (pocket - 1U) * 8U;
    pocket_slots = read32(core, descriptor);
    pocket_capacity = read8(core, descriptor + 4U);
    if (!s58_ewram_pointer(save2) || !s58_ewram_pointer(pocket_slots)
        || pocket_capacity == 0U || pocket_capacity > 58U)
        return false;
    uint16_t quantity_key = read16(core, save2 + S58_SAVE2_KEY_OFFSET);
    uint16_t pocket_items[58U] = {0};
    uint16_t pocket_quantities[58U] = {0};
    for (unsigned slot = 0U; slot < pocket_capacity; ++slot) {
        uint32_t row = pocket_slots + slot * 4U;
        pocket_items[slot] = read16(core, row);
        pocket_quantities[slot] = read16(core, row + 2U) ^ quantity_key;
    }
    unsigned candidate = 1U;
    for (unsigned slot = 0U; slot < pocket_capacity; ++slot) {
        uint16_t item = slot == 0U ? target : 0U;
        while (item == 0U && candidate < 1000U) {
            if (candidate != target
                && read8(core, S58_ITEM_TABLE
                               + candidate * S58_ITEM_STRIDE
                               + S58_ITEM_POCKET_OFFSET) == pocket)
                item = (uint16_t)candidate;
            ++candidate;
        }
        if (item == 0U)
            return false;
        uint32_t row = pocket_slots + slot * 4U;
        write16(core, row, item);
        write16(core, row + 2U,
                (uint16_t)((slot == 0U ? 999U : 1U) ^ quantity_key));
    }
    s58_set_money(core, purchased_money);
    unsigned failure_pulses = 0U;
    *bag_full = s58_mart_purchase_attempt(
            core, cases, target, purchase_pulses, false, &failure_pulses)
        && failure_pulses == purchase_pulses;

    save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    if (!s58_ewram_pointer(save1) || !s58_ewram_pointer(save2))
        return false;
    descriptor = S58_BAG_POCKETS + (pocket - 1U) * 8U;
    pocket_slots = read32(core, descriptor);
    if (!s58_ewram_pointer(pocket_slots)
        || read8(core, descriptor + 4U) != pocket_capacity)
        return false;
    quantity_key = read16(core, save2 + S58_SAVE2_KEY_OFFSET);
    for (unsigned slot = 0U; slot < pocket_capacity; ++slot) {
        uint32_t row = pocket_slots + slot * 4U;
        write16(core, row, pocket_items[slot]);
        write16(core, row + 2U,
                (uint16_t)(pocket_quantities[slot] ^ quantity_key));
    }
    s58_set_money(core, purchased_money);
    *bag_full = *bag_full
        && s58_item_quantity(core, target) == quantities[0] + 1U
        && s58_money(core) == purchased_money;
    for (unsigned index = 0U; index < cases->hub.mart_item_count; ++index) {
        uint16_t candidate_item = cases->hub.mart_items[index];
        uint8_t candidate_pocket = read8(
            core, S58_ITEM_TABLE + (uint32_t)candidate_item * S58_ITEM_STRIDE
                      + S58_ITEM_POCKET_OFFSET);
        uint16_t candidate_price = read16(
            core, S58_ITEM_TABLE + (uint32_t)candidate_item * S58_ITEM_STRIDE
                      + 12U);
        if (candidate_price == 0U || candidate_item == target)
            continue;
        if (candidate_pocket == 3U && sales->ball_id == 0U)
            sales->ball_id = candidate_item;
        if (candidate_pocket == 1U && sales->item_id == 0U)
            sales->item_id = candidate_item;
    }
    if (!*bag_full || sales->ball_id == 0U || sales->item_id == 0U)
        return false;
    sales->ball = s58_mart_sell_one(core, cases, sales->ball_id);
    sales->item = sales->ball
        && s58_mart_sell_one(core, cases, sales->item_id);
    sales->final_money = s58_money(core);
    if (getenv("MGBA_STAGE58_TRACE") != NULL)
        fprintf(stderr, "mart results cancel=%u full=%u purchase=%u"
                " target=%u qty=%" PRIu32 "/%" PRIu32
                " money=%" PRIu32 " cb=%08" PRIx32 " lock=%u\n",
                cancelled, *bag_full, *purchase, target, quantities[0],
                s58_item_quantity(core, target), s58_money(core),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, S58_FIELD_LOCK));
    return cancelled && *bag_full && *purchase && sales->ball && sales->item
        && s58_codex_boundaries(core);
}

static bool s58_phase1(struct mCore **core_io,
                       const char *rom, const char *save,
                       const struct Stage58Cases *cases,
                       bool *pc, bool *pc_ui_deposit,
                       bool *healer, bool *mart, bool *saved,
                       bool *healer_empty, bool *healer_egg,
                       bool *healer_fainted, bool *healer_normal,
                       bool *mart_purchase, bool *mart_bag_full,
                       struct S58MartSales *mart_sales,
                       bool *thin_initial, bool *thin_repeat,
                       bool *thin_retry, bool *thin_questlog,
                       bool *thin_quantities_preserved,
                       unsigned *thin_covered,
                       bool *codex_unchanged,
                       struct S58CodexBattleResult *codex_battle,
                       struct S58WildRuntimeResult *wild_runtime)
{
    struct mCore *core = *core_io;
    *codex_unchanged = false;
    bool wild_dynamic = s58_wild_runtime_path(core, cases, wild_runtime);
    uint64_t wild_save_hash = 0U;
    bool wild_checkpoint = wild_dynamic
        && s58_prepare_map_view(core)
        && s58_normal_menu_save(core, 0U, &wild_save_hash)
        && wild_save_hash != 0U;
    if (!wild_checkpoint)
        return false;
    qol_close(core);
    core = s58_open(rom, save, false);
    *core_io = core;
    if (!s58_continue_to_hub(core, cases))
        return false;
    s58_quest_log_before_hash = s58_quest_log_hash(core);
    bool thin = s58_thin_path(core, cases, thin_initial, thin_repeat,
                              thin_retry, thin_covered);
    *thin_quantities_preserved = thin
        && s58_thin_quantities_exact(core, cases);
    s58_trace_bag_item(core, "after-thin", 84U);
    /* A completed ordinary Pokemart transaction is a stock Quest Log owner:
     * closing its normal UI calls SetQuestLogEvent and starts a real recorded
     * scene.  Run the already-required mart boundary here so the following
     * Start-menu Save cuts/serializes that scene before fresh-core replay. */
    *mart = *thin_quantities_preserved
        && s58_mart_path(core, cases, mart_purchase, mart_bag_full,
                         mart_sales);
    bool normal_quest_save = *mart
        && s58_walk_to(core, cases, (uint16_t)cases->hub.pc.x,
                       (uint16_t)(cases->hub.pc.y + 1U))
        && s58_normal_menu_save(
            core, s58_quest_log_before_hash, &s58_quest_log_saved_hash);
    s58_trace_bag_item(core, "after-thin-normal-save", 84U);
    *thin_quantities_preserved = s58_thin_quantities_exact(core, cases)
        && *thin_quantities_preserved;
    s58_quest_log_recorded = normal_quest_save
        && s58_quest_log_before_hash != 0U
        && s58_quest_log_saved_hash != 0U
        && s58_quest_log_before_hash != s58_quest_log_saved_hash;
    if (!s58_quest_log_recorded)
        fprintf(stderr, "thin Quest Log pre-save unchanged"
                " before=%016" PRIx64 " after=%016" PRIx64
                " state=%u playback=%u map=%u/%u\n",
                s58_quest_log_before_hash, s58_quest_log_saved_hash,
                read8(core, S58_QUEST_LOG_STATE),
                read8(core, S58_QUEST_LOG_PLAYBACK_STATE),
                read8(core, read32(core, QOL_SAVE_BLOCK1_SLOT) + 4U),
                read8(core, read32(core, QOL_SAVE_BLOCK1_SLOT) + 5U));
    bool thin_checkpoint = thin && s58_quest_log_recorded;
    if (!thin_checkpoint)
        return false;
    /* Imported-map warps and six script transactions are complete.  Resume
     * their saved state in a fresh core before exercising unrelated hub tasks
     * so no libmGBA host-call trampoline state crosses domain ownership. */
    qol_close(core);
    core = s58_open(rom, save, false);
    *core_io = core;
    s58_quest_log_observed = false;
    if (!s58_continue_to_hub(core, cases))
        return false;
    *thin_quantities_preserved = s58_thin_quantities_exact(core, cases)
        && *thin_quantities_preserved;
    s58_trace_bag_item(core, "after-thin-fresh-load", 84U);
    uint64_t quest_log_reload_hash = s58_quest_log_hash(core);
    s58_quest_log_observed = s58_quest_log_recorded
        && quest_log_reload_hash == s58_quest_log_saved_hash;
    if (!s58_quest_log_observed)
        fprintf(stderr, "thin Quest Log reload mismatch recorded=%u"
                " before=%016" PRIx64 " saved=%016" PRIx64
                " reload=%016" PRIx64 " state=%u playback=%u\n",
                s58_quest_log_recorded, s58_quest_log_before_hash,
                s58_quest_log_saved_hash, quest_log_reload_hash,
                read8(core, S58_QUEST_LOG_STATE),
                read8(core, S58_QUEST_LOG_PLAYBACK_STATE));
    *thin_questlog = s58_thin_post_questlog_path(core, cases);
    if (!*thin_questlog)
        return false;
    /* Quest Log playback/next-input has deliberately traversed six foreign
     * maps.  End that domain with another ordinary Start-menu Save and a
     * fresh core before initializing the Codex mailbox.  This proves that
     * natural ReadKeys requests are not relying on transient playback state. */
    uint64_t post_quest_save_hash = 0U;
    bool post_quest_checkpoint = s58_walk_to(
            core, cases, (uint16_t)cases->hub.pc.x,
            (uint16_t)(cases->hub.pc.y + 1U))
        && s58_normal_menu_save(core, 0U, &post_quest_save_hash)
        && post_quest_save_hash != 0U;
    s58_trace_bag_item(core, "after-post-quest-save", 84U);
    *thin_quantities_preserved = s58_thin_quantities_exact(core, cases)
        && *thin_quantities_preserved;
    if (!post_quest_checkpoint)
        return false;
    qol_close(core);
    core = s58_open(rom, save, false);
    *core_io = core;
    if (!s58_continue_to_hub(core, cases))
        return false;
    *thin_quantities_preserved = s58_thin_quantities_exact(core, cases)
        && *thin_quantities_preserved;
    s58_trace_bag_item(core, "before-codex", 84U);
    struct S58CodexSaveSentinel codex_save_sentinel;
    bool codex_save_sentinel_ready = s58_codex_save_sentinel_seed(
        core, &codex_save_sentinel,
        &codex_battle->save_seen_before_hash,
        &codex_battle->save_personality_before_hash,
        &codex_battle->save_owned_before_hash);
    bool codex_cpu_path = codex_save_sentinel_ready
        && s58_codex_cpu_disconnect_path(core, cases, codex_battle);
    codex_battle->cpu_save_layout_restored = codex_cpu_path
        && s58_codex_save_sentinel_matches(
            core, &codex_save_sentinel,
            &codex_battle->save_seen_cpu_hash,
            &codex_battle->save_personality_cpu_hash,
            &codex_battle->save_owned_cpu_hash);
    bool codex_cpu = codex_cpu_path
        && codex_battle->cpu_save_layout_restored;
    bool cpu_thin_quantities_exact = s58_thin_quantities_exact(core, cases);
    codex_battle->cpu_thin_quantities_preserved =
        codex_cpu && cpu_thin_quantities_exact;
    *thin_quantities_preserved =
        cpu_thin_quantities_exact
        && *thin_quantities_preserved;
    bool codex_path = codex_cpu
        && s58_codex_battle_path(core, cases, codex_battle);
    codex_battle->forfeit_save_layout_restored = codex_path
        && s58_codex_save_sentinel_matches(
            core, &codex_save_sentinel,
            &codex_battle->save_seen_forfeit_hash,
            &codex_battle->save_personality_forfeit_hash,
            &codex_battle->save_owned_forfeit_hash);
    bool codex = codex_path
        && codex_battle->forfeit_save_layout_restored;
    bool forfeit_thin_quantities_exact =
        s58_thin_quantities_exact(core, cases);
    codex_battle->forfeit_thin_quantities_preserved =
        codex && forfeit_thin_quantities_exact;
    *thin_quantities_preserved =
        forfeit_thin_quantities_exact
        && *thin_quantities_preserved;
    uint64_t codex_save_hash = 0U;
    bool codex_checkpoint = codex
        && s58_walk_to(core, cases, (uint16_t)cases->hub.pc.x,
                       (uint16_t)(cases->hub.pc.y + 1U))
        && s58_prepare_map_view(core)
        && s58_normal_menu_save(core, 0U, &codex_save_hash)
        && codex_save_hash != 0U;
    s58_trace_bag_item(core, "after-codex-checkpoint", 84U);
    *thin_quantities_preserved = s58_thin_quantities_exact(core, cases)
        && *thin_quantities_preserved;
    if (!codex_checkpoint)
        return false;
    qol_close(core);
    core = s58_open(rom, save, false);
    *core_io = core;
    if (!s58_continue_to_hub(core, cases))
        return false;
    *thin_quantities_preserved = s58_thin_quantities_exact(core, cases)
        && *thin_quantities_preserved;
    s58_trace_bag_item(core, "before-healer", 84U);
    *healer = s58_healer_path(core_io, rom, save, cases,
                              healer_empty, healer_egg,
                              healer_fainted, healer_normal);
    core = *core_io;
    *thin_quantities_preserved = s58_thin_quantities_exact(core, cases)
        && *thin_quantities_preserved;
    uint64_t healer_save_hash = 0U;
    bool checkpoint = *healer && *mart
        && s58_walk_to(core, cases, (uint16_t)cases->hub.pc.x,
                       (uint16_t)(cases->hub.pc.y + 1U))
        && s58_prepare_map_view(core)
        && s58_normal_menu_save(core, 0U, &healer_save_hash)
        && healer_save_hash != 0U;
    s58_trace_bag_item(core, "after-healer-checkpoint", 84U);
    *thin_quantities_preserved = s58_thin_quantities_exact(core, cases)
        && *thin_quantities_preserved;
    if (!checkpoint)
        return false;
    qol_close(core);
    core = s58_open(rom, save, false);
    *core_io = core;
    if (!s58_continue_to_hub(core, cases))
        return false;
    *thin_quantities_preserved = s58_thin_quantities_exact(core, cases)
        && *thin_quantities_preserved;
    s58_trace_bag_item(core, "before-pc", 84U);
    if (!s58_hub_position(core, cases, (uint16_t)cases->hub.pc.x,
                          (uint16_t)(cases->hub.pc.y + 1U)))
        return false;
    *pc = s58_pc_path(core, cases, pc_ui_deposit);
    *thin_quantities_preserved = s58_thin_quantities_exact(core, cases)
        && *thin_quantities_preserved;
    s58_trace_bag_item(core, "after-pc", 84U);
    bool final_view = *pc && s58_prepare_map_view(core);
    bool final_bag_bound = final_view && s58_bind_bag_pockets(core);
    uint64_t final_save_hash = 0U;
    *saved = final_view && final_bag_bound
        && s58_normal_menu_save(core, 0U, &final_save_hash)
        && final_save_hash != 0U;
    *thin_quantities_preserved = s58_thin_quantities_exact(core, cases)
        && *thin_quantities_preserved;
    s58_trace_bag_item(core, "after-final-save", 84U);
    if (!*saved)
        fprintf(stderr, "final save debug pc=%u view=%u bag=%u"
                " hash=%016" PRIx64
                " cb=%08" PRIx32 " lock=%u\n",
                *pc, final_view, final_bag_bound, final_save_hash,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, S58_FIELD_LOCK));
    /* s58_thin_path compares the exact owner hash before/after every off-hub
     * event.  Fresh-core boundaries legitimately refresh volatile mailbox
     * bytes, so hub domains use the version/CRC/IDLE/closed invariants. */
    *codex_unchanged = thin && *thin_questlog
        && codex && *pc && *healer && *mart;
    return wild_dynamic && thin && *thin_questlog
        && *thin_quantities_preserved
        && codex && *pc && *pc_ui_deposit
        && *healer && *mart && *saved
        && *codex_unchanged;
}

static bool s58_reload(struct mCore *core,
                       const struct Stage58Cases *cases,
                       bool *box, bool *party, bool *field,
                       bool *pc_deposit, bool *mart_purchase,
                       bool *mart_sales_persisted,
                       bool *thin_persisted,
                       bool *codex_closed_reset,
                       bool *codex_mailbox_reset)
{
    run_key_frames(core, 0U, 180U);
    *box = s58_call_synced(core, QOL_GET_BOX_MON_DATA_AT,
                           S58_DEPOSIT_BOX, S58_DEPOSIT_SLOT,
                           QOL_MON_DATA_SPECIES, 0U) == S58_DEPOSIT_SPECIES;
    uint32_t maximum = s58_call_synced(
        core, BATTLE_CORE_GET_MON_DATA,
        S58_PLAYER_MON, QOL_MON_DATA_MAX_HP, 0U, 0U);
    *party = read8(core, S58_PLAYER_COUNT) == 1U && maximum > 1U
        && s58_call_synced(core, BATTLE_CORE_GET_MON_DATA,
                           S58_PLAYER_MON, QOL_MON_DATA_HP, 0U, 0U) == maximum
        && s58_call_synced(core, BATTLE_CORE_GET_MON_DATA,
                           S58_PLAYER_MON, QOL_MON_DATA_STATUS, 0U, 0U) == 0U
        && s58_call_synced(core, BATTLE_CORE_GET_MON_DATA,
                           S58_PLAYER_MON, QOL_MON_DATA_PP1, 0U, 0U) != 0U;
    *pc_deposit = *box && *party;
    (void)s58_call_synced(core, S58_SET_BAG_POCKETS_POINTERS,
                          0U, 0U, 0U, 0U);
    uint16_t mart_item = cases->hub.mart_items[0];
    uint32_t mart_price = read16(core, S58_ITEM_TABLE
                                + (uint32_t)mart_item * S58_ITEM_STRIDE + 12U);
    uint8_t mart_pocket = read8(core, S58_ITEM_TABLE
                               + (uint32_t)mart_item * S58_ITEM_STRIDE
                               + S58_ITEM_POCKET_OFFSET);
    uint32_t mart_descriptor = mart_pocket > 0U && mart_pocket <= 5U
        ? S58_BAG_POCKETS + (mart_pocket - 1U) * 8U : 0U;
    uint16_t sale_ball = 0U, sale_item = 0U;
    for (unsigned index = 0U; index < cases->hub.mart_item_count; ++index) {
        uint16_t candidate = cases->hub.mart_items[index];
        uint8_t candidate_pocket = read8(
            core, S58_ITEM_TABLE + (uint32_t)candidate * S58_ITEM_STRIDE
                      + S58_ITEM_POCKET_OFFSET);
        uint16_t candidate_price = read16(
            core, S58_ITEM_TABLE + (uint32_t)candidate * S58_ITEM_STRIDE + 12U);
        if (candidate == mart_item || candidate_price == 0U)
            continue;
        if (candidate_pocket == 3U && sale_ball == 0U)
            sale_ball = candidate;
        if (candidate_pocket == 1U && sale_item == 0U)
            sale_item = candidate;
    }
    uint32_t sale_ball_price = sale_ball ? read16(
        core, S58_ITEM_TABLE + (uint32_t)sale_ball * S58_ITEM_STRIDE + 12U) : 0U;
    uint32_t sale_item_price = sale_item ? read16(
        core, S58_ITEM_TABLE + (uint32_t)sale_item * S58_ITEM_STRIDE + 12U) : 0U;
    uint32_t expected_money = 100000U - mart_price
        + sale_ball_price / 2U + sale_item_price / 2U;
    *mart_purchase = s58_item_quantity(core, mart_item) == 1U
        && mart_descriptor != 0U
        && read8(core, mart_descriptor + 4U) == S58_MART_ITEMS_CAPACITY
        && mart_price <= 100000U;
    *mart_sales_persisted = sale_ball != 0U && sale_item != 0U
        && s58_item_quantity(core, sale_ball) == 0U
        && s58_item_quantity(core, sale_item) == 0U
        && s58_money(core) == expected_money;
    *thin_persisted = cases->thin_event_count == 6U;
    for (unsigned index = 0U; index < cases->thin_event_count; ++index) {
        const struct ThinEvent *event = &cases->thin_events[index];
        bool flag = s58_flag_get_direct(core, event->flag);
        uint8_t flag_byte = s58_flag_byte_direct(core, event->flag);
        uint32_t quantity = s58_item_quantity(core, event->item_id);
        bool row = flag && quantity == event->quantity;
        if (!row)
            fprintf(stderr, "thin reload mismatch index=%u map=%u/%u"
                    " item=%u flag=%u byte=%02x qty=%" PRIu32 "/%u"
                    " key=%04x\n", index, event->group, event->map,
                    event->item_id, flag, flag_byte, quantity,
                    event->quantity,
                    read16(core, read32(core, QOL_SAVE_BLOCK2_SLOT)
                                      + S58_SAVE2_KEY_OFFSET));
        *thin_persisted = *thin_persisted && row;
    }
    *field = read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S58_CB2_OVERWORLD
        && read8(core, S58_FIELD_LOCK) == 0U
        && s58_hub_position(core, cases,
                            (uint16_t)cases->hub.pc.x,
                            (uint16_t)(cases->hub.pc.y + 1U))
        && s58_codex_boundaries(core);
    *codex_closed_reset = *field
        && read8(core, S58_CODEX_STATE + 20U) == 0U
        && read16(core, S58_CODEX_STATE + 16U) == 0U
        && s58_reward_valid_window(core, S58_REWARD_WINDOW_CLOSED);
    *codex_mailbox_reset = read32(core, S58_MAILBOX) == 0U
        && read32(core, S58_MAILBOX + 24U) == 0U
        && read16(core, S58_CODEX_REQUEST + 10U) == 0U;
    return *pc_deposit && *mart_purchase && *mart_sales_persisted
        && *thin_persisted && *field
        && *codex_closed_reset && *codex_mailbox_reset;
}

#ifndef S58_CONVENIENCE_EMBEDDED
int main(int argc, char **argv)
{
    if (argc != 5 || (strcmp(argv[4], "phase1") != 0
                      && strcmp(argv[4], "reload") != 0)) {
        fprintf(stderr, "usage: %s ROM CASES SAVE phase1|reload\n", argv[0]);
        return 2;
    }
    struct Stage58Cases cases = s58_load_cases(argv[2]);
    if (cases.schema_version != 1U || cases.stage != S58_STAGE
        || strlen(cases.rom_sha256) != 64U)
        s58_die("Stage58 cases identity不一致");
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strcmp(rom_sha256, cases.rom_sha256) != 0)
        s58_die("exact ROM SHA-256不一致");

    log_problem_count = 0U;
    memset(s58_video, 0, sizeof(s58_video));
    struct mLogger logger = {.log = s58_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    bool phase1 = strcmp(argv[4], "phase1") == 0;
    struct mCore *core = s58_open(argv[1], argv[3], phase1);
    if (getenv("MGBA_STAGE58_TRACE") != NULL) {
        uint64_t initial_savedata_hash = 0U;
        bool cloned = s58_savedata_hash(core, &initial_savedata_hash);
        fprintf(stderr, "savedata initial cloned=%u hash=%016" PRIx64 "\n",
                cloned, initial_savedata_hash);
    }
    bool graph = s58_hub_graph(core, &cases);
    bool codex_result_graph = s58_codex_result_graph(core, &cases);
    bool thin_graph = s58_thin_graph(core, &cases);
    unsigned wild_representatives = 0U, wild_modes = 0U, wild_slots = 0U;
    bool wild = s58_wild_contract(
        core, &cases, &wild_representatives, &wild_modes, &wild_slots);
    bool pc = false, pc_ui_deposit = false;
    bool healer = false, mart = false, saved = false;
    bool healer_empty = false, healer_egg = false;
    bool healer_fainted = false, healer_normal = false;
    bool mart_purchase = false, mart_bag_full = false;
    struct S58MartSales mart_sales = {0};
    bool thin_initial = false, thin_repeat = false, thin_retry = false;
    bool thin_questlog = false, thin_quantities_preserved = false;
    bool codex_unchanged = false;
    unsigned thin_covered = 0U;
    bool box = false, party = false, field = false;
    bool reload_pc_deposit = false, reload_mart_purchase = false;
    bool reload_mart_sales = false;
    bool reload_thin_persisted = false;
    bool reload_codex_closed_reset = false;
    bool reload_codex_mailbox_reset = false;
    struct S58WildRuntimeResult wild_runtime = {0};
    struct S58CodexBattleResult codex_battle = {0};
    bool prepared = true;
    if (phase1) {
        prepared = s58_prepare_hub_save(core, &cases);
        qol_close(core);
        core = s58_open(argv[1], argv[3], false);
    }
    bool continued = prepared && s58_continue_to_hub(core, &cases);
    bool dynamic = continued && (phase1
        ? s58_phase1(&core, argv[1], argv[3], &cases,
                     &pc, &pc_ui_deposit, &healer, &mart, &saved,
                     &healer_empty, &healer_egg,
                     &healer_fainted, &healer_normal,
                     &mart_purchase, &mart_bag_full,
                     &mart_sales,
                     &thin_initial, &thin_repeat, &thin_retry,
                     &thin_questlog, &thin_quantities_preserved,
                     &thin_covered,
                     &codex_unchanged, &codex_battle, &wild_runtime)
        : s58_reload(core, &cases, &box, &party, &field,
                     &reload_pc_deposit, &reload_mart_purchase,
                     &reload_mart_sales,
                     &reload_thin_persisted,
                     &reload_codex_closed_reset,
                     &reload_codex_mailbox_reset));
    bool passed = graph && codex_result_graph && thin_graph && wild && dynamic
        && log_problem_count == 0U;

    printf("{\"schema_version\":1,\"task\":"
           "\"USER-20260828-STAGE57-QOL-WORLD-CONVENIENCE-DEBUG\","
           "\"stage\":58,\"phase\":\"%s\",\"status\":\"%s\","
           "\"rom_sha256\":\"%s\",\"tests\":{",
           argv[4], passed ? "PASS" : "FAIL", rom_sha256);
    if (phase1) {
        printf("\"hub_exact_graph\":%s,\"thin_events_exact_graph\":%s,"
               "\"codex_result_win_loss_draw_table_exact\":%s,"
               "\"wild_exact_slots\":%s,"
               "\"kanto_wild_runtime_land_rate_species_level_field_return\":%s,"
               "\"kanto_wild_runtime_water_rate_species_level_field_return\":%s,"
               "\"kanto_wild_runtime_rock_rate_species_level_field_return\":%s,"
               "\"kanto_wild_runtime_fishing_rate_species_level_field_return\":%s,"
               "\"kanto_wild_fishing_old_good_super_rng_boundaries\":%s,"
               "\"thin_events_initial_pickup\":%s,"
               "\"thin_events_repeat_no_duplicate\":%s,"
               "\"thin_events_blockdata_walkable_non_event_adjacent\":%s,"
               "\"thin_events_bag_full_retry_all_6\":%s,"
               "\"thin_events_native_flag_neighbor_bits_stable\":%s,"
               "\"thin_events_quest_log_normal_save_recorded\":%s,"
               "\"thin_events_quest_log_reload_next_input_flag_stable\":%s,"
               "\"thin_events_quantities_preserved_across_normal_saves\":%s,"
               "\"pc_object_storage_callback_field_return\":%s,"
               "\"pc_normal_ui_deposit\":%s,"
               "\"healer_object_hp_pp_status\":%s,"
               "\"healer_zero_party_field_return\":%s,"
               "\"healer_egg_hp_pp_status\":%s,"
               "\"healer_fainted_hp_pp_status\":%s,"
               "\"healer_normal_hp_pp_status\":%s,"
               "\"mart_object_open_navigate_cancel_unchanged\":%s,"
               "\"mart_money_purchase\":%s,"
               "\"mart_bag_full_no_charge\":%s,"
               "\"mart_normal_ui_sell_ball\":%s,"
               "\"mart_normal_ui_sell_item\":%s,"
               "\"codex_npc_normal_a_battle_start_finish_field_return\":%s,"
               "\"codex_reward_closed_open_closed\":%s,"
               "\"codex_transaction_request_owned\":%s,"
               "\"codex_natural_readkeys_all_11_requests\":%s,"
               "\"codex_external_capabilities_7fff_preserved\":%s,"
               "\"codex_request_window_not_cleared\":%s,"
               "\"codex_forfeit_result_kind_4\":%s,"
               "\"codex_disconnect_cpu_controller_uninstalled\":%s,"
               "\"codex_disconnect_cpu_win_result_kind_1\":%s,"
               "\"codex_disconnect_cpu_normal_input_field_reward_return\":%s,"
               "\"codex_cpu_win_thin_quantities_preserved\":%s,"
               "\"codex_forfeit_thin_quantities_preserved\":%s,"
               "\"codex_cpu_win_save_layout_restored\":%s,"
               "\"codex_forfeit_save_layout_restored\":%s,"
               "\"thin_codex_owner_hash_unchanged\":%s,"
               "\"hub_codex_boundaries_valid\":%s,"
               "\"save_after_normal_ui_mutation\":%s",
               graph ? "true" : "false", thin_graph ? "true" : "false",
               codex_result_graph ? "true" : "false",
               wild ? "true" : "false",
               wild_runtime.land ? "true" : "false",
               wild_runtime.water ? "true" : "false",
               wild_runtime.rock ? "true" : "false",
               wild_runtime.fishing ? "true" : "false",
               wild_runtime.fishing_rng_boundaries ? "true" : "false",
               thin_initial ? "true" : "false",
               thin_repeat ? "true" : "false",
               thin_initial ? "true" : "false",
               thin_retry ? "true" : "false",
               thin_retry ? "true" : "false",
               s58_quest_log_recorded ? "true" : "false",
               thin_questlog ? "true" : "false",
               thin_quantities_preserved ? "true" : "false",
               pc ? "true" : "false", pc_ui_deposit ? "true" : "false",
               healer ? "true" : "false", healer_empty ? "true" : "false",
               healer_egg ? "true" : "false",
               healer_fainted ? "true" : "false",
               healer_normal ? "true" : "false", mart ? "true" : "false",
               mart_purchase ? "true" : "false",
               mart_bag_full ? "true" : "false",
               mart_sales.ball ? "true" : "false",
               mart_sales.item ? "true" : "false",
               codex_battle.battle_start_finish_field_return
                    ? "true" : "false",
               codex_battle.reward_closed_open_closed ? "true" : "false",
               codex_battle.request_owned ? "true" : "false",
               codex_battle.natural_requests == 11U ? "true" : "false",
               codex_battle.external_capabilities_preserved
                    ? "true" : "false",
               codex_battle.request_window_preserved ? "true" : "false",
               codex_battle.forfeit_result_kind ? "true" : "false",
               codex_battle.cpu_controller_uninstalled ? "true" : "false",
               codex_battle.cpu_win_result_kind ? "true" : "false",
               codex_battle.cpu_normal_input_field_reward_return
                    ? "true" : "false",
               codex_battle.cpu_thin_quantities_preserved
                    ? "true" : "false",
               codex_battle.forfeit_thin_quantities_preserved
                    ? "true" : "false",
               codex_battle.cpu_save_layout_restored
                    ? "true" : "false",
               codex_battle.forfeit_save_layout_restored
                    ? "true" : "false",
               codex_unchanged ? "true" : "false",
               codex_unchanged ? "true" : "false",
               saved ? "true" : "false");
    } else {
        printf("\"hub_exact_graph\":%s,\"thin_events_exact_graph\":%s,"
               "\"codex_result_win_loss_draw_table_exact\":%s,"
               "\"wild_exact_slots\":%s,"
               "\"pc_normal_ui_deposit_persisted\":%s,"
               "\"mart_money_purchase_persisted\":%s,"
               "\"mart_normal_ui_sales_persisted\":%s,"
               "\"codex_post_battle_closed_reset_boundary\":%s,"
               "\"codex_external_mailbox_volatile_reset\":%s,"
               "\"thin_events_pickups_persisted\":%s,"
               "\"reload_box\":%s,\"reload_party_healed\":%s,"
               "\"reload_field_codex_boundaries\":%s",
               graph ? "true" : "false", thin_graph ? "true" : "false",
               codex_result_graph ? "true" : "false",
               wild ? "true" : "false",
               reload_pc_deposit ? "true" : "false",
               reload_mart_purchase ? "true" : "false",
               reload_mart_sales ? "true" : "false",
               reload_codex_closed_reset ? "true" : "false",
               reload_codex_mailbox_reset ? "true" : "false",
               reload_thin_persisted ? "true" : "false",
               box ? "true" : "false", party ? "true" : "false",
               field ? "true" : "false");
    }
    printf("},\"coverage\":{\"hub_objects\":4,\"thin_events\":%u,"
           "\"thin_retry\":%u,\"wild_representatives\":%u,"
           "\"wild_modes\":%u,\"wild_slots\":%u,"
           "\"wild_runtime_modes\":%u,\"fishing_tiers\":%u,"
           "\"fishing_rng_samples\":%u,\"codex_battle_paths\":%u,"
           "\"codex_result_routes_exact\":%u},"
           "\"evidence\":{\"pc_normal_ui_deposit\":{"
           "\"species\":%u,\"box\":%u,\"slot\":%u,"
           "\"party_before\":2,\"party_after\":1},"
           "\"mart_purchase_item\":%u,"
           "\"mart_sales\":{\"ball\":%u,\"item\":%u,"
           "\"final_money\":%" PRIu32 "},"
           "\"codex_battle\":{\"outcome\":%u,"
           "\"last_sequence\":%" PRIu32 ","
           "\"natural_requests\":%u,"
           "\"natural_cpu_requests\":%u,"
           "\"cpu_controller_installed\":%u,"
           "\"external_capabilities\":%" PRIu32 ","
           "\"request_command\":%u,\"result_kind\":%u},"
           "\"cpu_battle\":{\"outcome\":%u,\"result_kind\":%u},"
           "\"codex_save_layout\":{"
           "\"seen_before\":\"%016" PRIx64 "\","
           "\"seen_after_cpu\":\"%016" PRIx64 "\","
           "\"seen_after_forfeit\":\"%016" PRIx64 "\","
           "\"personality_before\":\"%016" PRIx64 "\","
           "\"personality_after_cpu\":\"%016" PRIx64 "\","
           "\"personality_after_forfeit\":\"%016" PRIx64 "\","
           "\"owned_before\":\"%016" PRIx64 "\","
           "\"owned_after_cpu\":\"%016" PRIx64 "\","
           "\"owned_after_forfeit\":\"%016" PRIx64 "\"},"
           "\"wild_natural\":[",
           phase1 ? thin_covered : cases.thin_event_count,
           phase1 && thin_retry ? cases.thin_event_count
                               : (phase1 ? 0U : cases.thin_event_count),
           wild_representatives, wild_modes, wild_slots,
           phase1 ? wild_runtime.generated : 0U,
           phase1 && wild_runtime.fishing ? 3U : 0U,
           phase1 ? wild_runtime.fishing_rng_samples : 0U,
           phase1 ? (unsigned)codex_battle.battle_start_finish_field_return
                    + (unsigned)codex_battle.cpu_normal_input_field_reward_return
                  : 0U,
           codex_result_graph ? cases.codex_result.row_count : 0U,
           S58_DEPOSIT_SPECIES, S58_DEPOSIT_BOX, S58_DEPOSIT_SLOT,
           cases.hub.mart_items[0],
           mart_sales.ball_id, mart_sales.item_id, mart_sales.final_money,
           codex_battle.outcome, codex_battle.last_sequence,
           codex_battle.natural_requests,
           codex_battle.natural_cpu_requests,
           read8(core, S58_CODEX_STATE + 47U),
           codex_battle.external_capabilities,
           codex_battle.request_command,
           codex_battle.result_kind,
           codex_battle.cpu_outcome,
           codex_battle.cpu_result_kind,
           codex_battle.save_seen_before_hash,
           codex_battle.save_seen_cpu_hash,
           codex_battle.save_seen_forfeit_hash,
           codex_battle.save_personality_before_hash,
           codex_battle.save_personality_cpu_hash,
           codex_battle.save_personality_forfeit_hash,
           codex_battle.save_owned_before_hash,
           codex_battle.save_owned_cpu_hash,
           codex_battle.save_owned_forfeit_hash);
    for (unsigned index = 0U; index < wild_runtime.evidence_count; ++index) {
        printf("%s{\"method\":\"%s\",\"map_group\":%u,"
               "\"map_num\":%u,\"x\":%u,\"y\":%u,"
               "\"behavior\":%u,\"facing\":%u,"
               "\"required_item_or_move\":%u,"
               "\"encounter_species\":%u,\"encounter_level\":%u,"
               "\"source_key\":\"%s\"}",
               index == 0U ? "" : ",",
               wild_runtime.evidence[index].method,
               wild_runtime.evidence[index].group,
               wild_runtime.evidence[index].map,
               wild_runtime.evidence[index].x,
               wild_runtime.evidence[index].y,
               wild_runtime.evidence[index].behavior,
               wild_runtime.evidence[index].facing,
               wild_runtime.evidence[index].required_item_or_move,
               wild_runtime.evidence[index].species,
               wild_runtime.evidence[index].level,
               wild_runtime.evidence[index].source_key);
    }
    printf("],\"thin_reload\":[");
    if (!phase1) {
        uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
        uint16_t quantity_key = s58_ewram_pointer(save2)
            ? read16(core, save2 + S58_SAVE2_KEY_OFFSET) : 0U;
        for (unsigned index = 0U; index < cases.thin_event_count; ++index) {
            const struct ThinEvent *event = &cases.thin_events[index];
            uint8_t pocket = read8(
                core, S58_ITEM_TABLE
                      + (uint32_t)event->item_id * S58_ITEM_STRIDE
                      + S58_ITEM_POCKET_OFFSET);
            uint32_t descriptor = pocket > 0U && pocket <= 5U
                ? S58_BAG_POCKETS + (pocket - 1U) * 8U : 0U;
            uint32_t slots = descriptor ? read32(core, descriptor) : 0U;
            int slot = s58_item_slot(core, event->item_id);
            uint16_t raw_quantity = slot >= 0 && s58_ewram_pointer(slots)
                ? read16(core, slots + (uint32_t)slot * 4U + 2U) : 0U;
            printf("%s{\"item_id\":%u,\"flag_byte\":%u,"
                   "\"quantity_key\":%u,\"raw_quantity\":%u,"
                   "\"decoded_quantity\":%" PRIu32 ","
                   "\"expected_quantity\":%u}",
                   index == 0U ? "" : ",", event->item_id,
                   s58_flag_byte_direct(core, event->flag), quantity_key,
                   raw_quantity, s58_item_quantity(core, event->item_id),
                   event->quantity);
        }
    }
    printf("]},\"warnings\":%u,\"warnings_errors\":%u}\n",
           log_problem_count, log_problem_count);

    free(cases.source);
    qol_close(core);
    return passed ? 0 : 1;
}
#endif
