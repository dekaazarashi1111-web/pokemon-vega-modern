/* T26 Stage 43 mailbox/PING exact-ROM validation for libmGBA. */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define BATTLE_CORE_EMBEDDED
#include "mgba_battle_core_smoke.c"

#include <ctype.h>

enum {
    CBB_MAILBOX = 0x0203F800U,
    CBB_MAILBOX_SIZE = 256U,
    CBB_RESERVED_SIZE = 512U,
    CBB_REQUEST = CBB_MAILBOX + 0x80U,
    CBB_REQUEST_SIZE = 64U,
    CBB_HOOK_POINTER = 0x080005ECU,
    CBB_HOOK_STUB = 0x080005E8U,
    CBB_MAGIC = 0x58424356U,
    CBB_STAGE_IDENTITY = 0x0DB5FBE5U,
    CBB_BUILD_IDENTITY = 0x43364254U,
    CBB_BASE_ROM_CRC32 = 0xEECED58BU,
    CBB_PONG_MAGIC = 0x474E4F50U,
    CBB_CAPABILITIES = 7U,
    CBB_PHASE_IDLE = 1U,
    CBB_COMMAND_PING = 1U,
    CBB_STATUS_READY = 1U,
    CBB_STATUS_PONG = 2U,
    CBB_STATUS_ERROR = 3U,
    CBB_ERROR_FUTURE = 1U,
    CBB_ERROR_STALE = 2U,
    CBB_ERROR_NONCE = 3U,
    CBB_ERROR_OVERSIZE = 4U,
    CBB_ERROR_PAYLOAD_CRC = 5U,
    CBB_ERROR_REQUEST_CRC = 6U,
    CBB_ERROR_PHASE = 7U,
    CBB_ERROR_COMMAND = 8U,
};

#define CBB_SYMBOL_LIST(X) \
    X(probe, "CodexBattleBridge_Probe") \
    X(initialize, "CodexBattleBridge_Initialize") \
    X(initialize_nonce, "CodexBattleBridge_InitializeWithNonce") \
    X(poll, "CodexBattleBridge_Poll") \
    X(read_keys, "CodexBattleBridge_ReadKeysAdapter")

struct CbbSymbols {
#define CBB_MEMBER(member, name) uint32_t member;
    CBB_SYMBOL_LIST(CBB_MEMBER)
#undef CBB_MEMBER
};

struct CbbCases {
    bool schema;
    bool exact_case_names;
    uint32_t mailbox_address;
    uint32_t payload_address;
};

struct ProtectedSpan {
    uint32_t address;
    uint32_t size;
};

static const struct ProtectedSpan PROTECTED_SPANS[] = {
    {0x020241E4U, 600U},
    {0x02023B24U, 0x430U},
    {0x0203D000U, 0x800U},
    {0x0203F220U, 0x500U},
    {0x0203EE00U, 0x298U},
    {0x0203F110U, 0x100U},
    {0x03005040U, 4U},
};

static void cbb_die(const char *message)
{
    fprintf(stderr, "mgba-codex-battle-bridge: %s\n", message);
    exit(1);
}

static char *cbb_read_text(const char *path)
{
    FILE *stream = fopen(path, "rb");
    if (!stream)
        cbb_die("fixture open failed");
    if (fseek(stream, 0, SEEK_END) != 0)
        cbb_die("fixture seek failed");
    long length = ftell(stream);
    if (length <= 0 || length > 4L * 1024L * 1024L)
        cbb_die("fixture size differs");
    rewind(stream);
    char *text = malloc((size_t)length + 1U);
    if (!text || fread(text, 1, (size_t)length, stream) != (size_t)length)
        cbb_die("fixture read failed");
    if (fclose(stream) != 0)
        cbb_die("fixture close failed");
    text[length] = '\0';
    return text;
}

static const char *cbb_find_key(const char *text, const char *key)
{
    char needle[160];
    int length = snprintf(needle, sizeof(needle), "\"%s\"", key);
    if (length <= 0 || (size_t)length >= sizeof(needle))
        cbb_die("JSON key formatting failed");
    return strstr(text, needle);
}

static uint32_t cbb_parse_number(const char *cursor)
{
    while (*cursor && (isspace((unsigned char)*cursor)
                       || *cursor == ':' || *cursor == '"'))
        ++cursor;
    errno = 0;
    char *end = NULL;
    unsigned long value = strtoul(cursor, &end, 0);
    if (errno || end == cursor || value > UINT32_MAX)
        cbb_die("JSON numeric value differs");
    return (uint32_t)value;
}

static uint32_t cbb_json_number(const char *text, const char *key)
{
    const char *found = cbb_find_key(text, key);
    if (!found || !(found = strchr(found, ':')))
        cbb_die("required JSON number is missing");
    return cbb_parse_number(found + 1);
}

static uint32_t cbb_json_symbol(const char *text, const char *name)
{
    const char *found = text;
    size_t name_length = strlen(name);
    for (;;) {
        found = cbb_find_key(found, name);
        if (!found)
            break;
        const char *separator = found + name_length + 2U;
        while (isspace((unsigned char)*separator))
            ++separator;
        if (*separator == ':') {
            found = separator;
            break;
        }
        ++found;
    }
    if (!found)
        cbb_die("required runtime symbol is missing");
    ++found;
    while (isspace((unsigned char)*found))
        ++found;
    if (*found == '{') {
        const char *end = strchr(found, '}');
        const char *address = cbb_find_key(found, "address");
        if (!end || !address || address > end || !(address = strchr(address, ':')))
            cbb_die("runtime symbol address object differs");
        found = address + 1;
    }
    return cbb_parse_number(found);
}

static unsigned cbb_occurrences(const char *text, const char *needle)
{
    unsigned count = 0U;
    size_t length = strlen(needle);
    for (const char *cursor = text; (cursor = strstr(cursor, needle)) != NULL;
         cursor += length)
        ++count;
    return count;
}

static struct CbbSymbols cbb_load_symbols(const char *path)
{
    char *text = cbb_read_text(path);
    struct CbbSymbols result = {0};
#define CBB_LOAD(member, name) result.member = cbb_json_symbol(text, name);
    CBB_SYMBOL_LIST(CBB_LOAD)
#undef CBB_LOAD
    free(text);
    return result;
}

static struct CbbCases cbb_load_cases(const char *path)
{
    char *text = cbb_read_text(path);
    static const char *const invalid[] = {
        "torn", "duplicate", "stale", "future", "wrong_nonce",
        "wrong_payload_crc", "wrong_request_crc", "wrong_phase",
        "oversize", "unknown_command",
    };
    bool exact = true;
    for (unsigned index = 0U; index < ARRAY_LEN(invalid); ++index) {
        char quoted[80];
        snprintf(quoted, sizeof(quoted), "\"%s\"", invalid[index]);
        exact = exact && cbb_occurrences(text, quoted) == 1U;
    }
    struct CbbCases result = {
        .schema = cbb_json_number(text, "schema_version") == 1U
            && cbb_occurrences(text, "\"protected_spans\"") == 1U
            && cbb_occurrences(text, "\"invalid_cases\"") == 1U,
        .exact_case_names = exact,
        .mailbox_address = cbb_json_number(text, "mailbox_address"),
        .payload_address = cbb_json_number(text, "payload_address"),
    };
    free(text);
    return result;
}

static uint32_t cbb_call(struct mCore *core, uint32_t function,
                         uint32_t r0, uint32_t r1, uint32_t r2, uint32_t r3)
{
    if (!(function & 1U))
        cbb_die("runtime entrypoint is not Thumb");
    return call_bounded(core, function, r0, r1, r2, r3).result;
}

static uint32_t cbb_crc_byte(uint32_t crc, uint8_t value)
{
    crc ^= value;
    for (unsigned bit = 0U; bit < 8U; ++bit) {
        uint32_t mask = 0U - (crc & 1U);
        crc = (crc >> 1) ^ (UINT32_C(0xEDB88320) & mask);
    }
    return crc;
}

static uint32_t cbb_crc_bytes(const uint8_t *raw, size_t size)
{
    uint32_t crc = UINT32_C(0xFFFFFFFF);
    for (size_t index = 0U; index < size; ++index)
        crc = cbb_crc_byte(crc, raw[index]);
    return crc ^ UINT32_C(0xFFFFFFFF);
}

static uint32_t cbb_snapshot_crc(struct mCore *core)
{
    uint32_t crc = UINT32_C(0xFFFFFFFF);
    for (uint32_t offset = 0U; offset < 0x40U; ++offset)
        crc = cbb_crc_byte(crc, read8(core, CBB_MAILBOX + offset));
    for (uint32_t offset = 0x50U; offset < 0x80U; ++offset)
        crc = cbb_crc_byte(crc, read8(core, CBB_MAILBOX + offset));
    return crc ^ UINT32_C(0xFFFFFFFF);
}

static void cbb_put16(uint8_t *raw, unsigned offset, uint16_t value)
{
    raw[offset] = (uint8_t)value;
    raw[offset + 1U] = (uint8_t)(value >> 8);
}

static void cbb_put32(uint8_t *raw, unsigned offset, uint32_t value)
{
    for (unsigned byte = 0U; byte < 4U; ++byte)
        raw[offset + byte] = (uint8_t)(value >> (byte * 8U));
}

static uint16_t cbb_read16(struct mCore *core, uint32_t address)
{
    return read16(core, address);
}

static uint32_t cbb_read32(struct mCore *core, uint32_t address)
{
    return read32(core, address);
}

static void cbb_write_request(struct mCore *core, const uint8_t request[64],
                              bool torn)
{
    for (unsigned index = 0U; index < 56U; ++index)
        write8(core, CBB_REQUEST + index, request[index]);
    for (unsigned index = 56U; index < 60U; ++index)
        write8(core, CBB_REQUEST + index,
               torn ? (uint8_t)(request[index] ^ 0xA5U) : request[index]);
    for (unsigned index = 60U; index < 64U; ++index)
        write8(core, CBB_REQUEST + index, request[index]);
}

enum RequestVariant {
    REQUEST_VALID,
    REQUEST_STALE,
    REQUEST_FUTURE,
    REQUEST_WRONG_NONCE,
    REQUEST_PAYLOAD_CRC,
    REQUEST_REQUEST_CRC,
    REQUEST_WRONG_PHASE,
    REQUEST_OVERSIZE,
    REQUEST_UNKNOWN_COMMAND,
};

static void cbb_build_request(uint8_t request[64], uint32_t nonce,
                              uint32_t sequence, uint32_t token,
                              enum RequestVariant variant)
{
    memset(request, 0, 64U);
    uint32_t used_nonce = variant == REQUEST_WRONG_NONCE ? nonce ^ 0x10203040U : nonce;
    uint16_t command = variant == REQUEST_UNKNOWN_COMMAND ? 0x55U : CBB_COMMAND_PING;
    uint16_t phase = variant == REQUEST_WRONG_PHASE ? 2U : CBB_PHASE_IDLE;
    uint16_t payload_size = variant == REQUEST_OVERSIZE ? 33U : 8U;
    cbb_put32(request, 0U, used_nonce);
    cbb_put16(request, 4U, command);
    cbb_put16(request, 6U, phase);
    cbb_put16(request, 8U, payload_size);
    cbb_put32(request, 16U, token);
    cbb_put32(request, 20U, ~token);
    uint32_t payload_crc = cbb_crc_bytes(request + 16U, 8U);
    if (variant == REQUEST_PAYLOAD_CRC)
        payload_crc ^= 1U;
    cbb_put32(request, 12U, payload_crc);
    uint32_t request_crc = cbb_crc_bytes(request, 48U);
    if (variant == REQUEST_REQUEST_CRC)
        request_crc ^= 1U;
    cbb_put32(request, 48U, request_crc);
    cbb_put32(request, 56U, ~sequence);
    cbb_put32(request, 60U, sequence);
}

static bool cbb_snapshot_valid(struct mCore *core)
{
    uint32_t sequence = cbb_read32(core, CBB_MAILBOX + 0x40U);
    return sequence != 0U
        && cbb_read32(core, CBB_MAILBOX + 0x44U) == ~sequence
        && cbb_read16(core, CBB_MAILBOX + 0x48U) == 48U
        && cbb_read32(core, CBB_MAILBOX + 0x4CU) == cbb_snapshot_crc(core);
}

static void cbb_seed_protected(struct mCore *core)
{
    for (unsigned span = 0U; span < ARRAY_LEN(PROTECTED_SPANS); ++span) {
        for (uint32_t index = 0U; index < PROTECTED_SPANS[span].size; ++index) {
            uint8_t value = (uint8_t)(0x31U + span * 19U + index * 7U);
            write8(core, PROTECTED_SPANS[span].address + index, value);
        }
    }
}

static uint32_t cbb_hash_span(struct mCore *core, const struct ProtectedSpan *span)
{
    uint32_t value = UINT32_C(2166136261);
    for (uint32_t index = 0U; index < span->size; ++index) {
        value ^= read8(core, span->address + index);
        value *= UINT32_C(16777619);
    }
    return value;
}

static void cbb_capture_protected(struct mCore *core,
                                  uint32_t hashes[ARRAY_LEN(PROTECTED_SPANS)])
{
    for (unsigned index = 0U; index < ARRAY_LEN(PROTECTED_SPANS); ++index)
        hashes[index] = cbb_hash_span(core, &PROTECTED_SPANS[index]);
}

static bool cbb_protected_equal(
    struct mCore *core, const uint32_t expected[ARRAY_LEN(PROTECTED_SPANS)])
{
    for (unsigned index = 0U; index < ARRAY_LEN(PROTECTED_SPANS); ++index) {
        if (cbb_hash_span(core, &PROTECTED_SPANS[index]) != expected[index])
            return false;
    }
    return true;
}

static bool cbb_header(struct mCore *core, const struct CbbSymbols *symbols)
{
    uint32_t nonce = UINT32_C(0x6A17C0DE);
    cbb_call(core, symbols->initialize_nonce, nonce, 0U, 0U, 0U);
    return cbb_read32(core, CBB_MAILBOX) == CBB_MAGIC
        && cbb_read16(core, CBB_MAILBOX + 4U) == 1U
        && cbb_read16(core, CBB_MAILBOX + 6U) == 0U
        && cbb_read16(core, CBB_MAILBOX + 8U) == CBB_MAILBOX_SIZE
        && cbb_read16(core, CBB_MAILBOX + 0x0CU) == 0x80U
        && cbb_read16(core, CBB_MAILBOX + 0x0EU) == 0x40U
        && cbb_read32(core, CBB_MAILBOX + 0x14U) == CBB_CAPABILITIES
        && cbb_read16(core, CBB_MAILBOX + 0x18U) == 43U
        && cbb_read16(core, CBB_MAILBOX + 0x1AU) == CBB_PHASE_IDLE
        && cbb_read32(core, CBB_MAILBOX + 0x1CU) == CBB_STAGE_IDENTITY
        && cbb_read32(core, CBB_MAILBOX + 0x20U) == CBB_BASE_ROM_CRC32
        && cbb_read32(core, CBB_MAILBOX + 0x24U) == CBB_BUILD_IDENTITY
        && cbb_read32(core, CBB_MAILBOX + 0x28U) == nonce
        && cbb_read32(core, CBB_MAILBOX + 0x2CU) == ~nonce
        && cbb_read32(core, CBB_MAILBOX + 0x30U) == CBB_MAILBOX
        && cbb_read32(core, CBB_MAILBOX + 0x34U) == CBB_RESERVED_SIZE
        && cbb_read16(core, CBB_MAILBOX + 0x58U) == CBB_STATUS_READY
        && cbb_snapshot_valid(core);
}

static bool cbb_ping_once(struct mCore *core, const struct CbbSymbols *symbols,
                          uint32_t token)
{
    uint32_t nonce = cbb_read32(core, CBB_MAILBOX + 0x28U);
    uint32_t accepted = cbb_read32(core, CBB_MAILBOX + 0x70U);
    uint32_t sequence = accepted + 1U;
    if (sequence == 0U)
        sequence = 1U;
    uint8_t request[64];
    cbb_build_request(request, nonce, sequence, token, REQUEST_VALID);
    cbb_write_request(core, request, false);
    cbb_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    return cbb_snapshot_valid(core)
        && cbb_read32(core, CBB_MAILBOX + 0x50U) == sequence
        && cbb_read32(core, CBB_MAILBOX + 0x54U) == ~sequence
        && cbb_read16(core, CBB_MAILBOX + 0x58U) == CBB_STATUS_PONG
        && cbb_read16(core, CBB_MAILBOX + 0x5AU) == 0U
        && cbb_read16(core, CBB_MAILBOX + 0x5CU) == 12U
        && cbb_read16(core, CBB_MAILBOX + 0x5EU) == CBB_COMMAND_PING
        && cbb_read32(core, CBB_MAILBOX + 0x60U) == token
        && cbb_read32(core, CBB_MAILBOX + 0x64U) == ~token
        && cbb_read32(core, CBB_MAILBOX + 0x68U) == CBB_PONG_MAGIC
        && cbb_read32(core, CBB_MAILBOX + 0x70U) == sequence;
}

static bool cbb_error_case(struct mCore *core, const struct CbbSymbols *symbols,
                           enum RequestVariant variant, uint32_t sequence,
                           uint16_t expected_error, uint32_t salt)
{
    uint32_t nonce = cbb_read32(core, CBB_MAILBOX + 0x28U);
    uint32_t accepted = cbb_read32(core, CBB_MAILBOX + 0x70U);
    uint8_t request[64];
    cbb_build_request(request, nonce, sequence, 0xA7000001U ^ salt, variant);
    cbb_write_request(core, request, false);
    cbb_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    return cbb_snapshot_valid(core)
        && cbb_read16(core, CBB_MAILBOX + 0x58U) == CBB_STATUS_ERROR
        && cbb_read16(core, CBB_MAILBOX + 0x5AU) == expected_error
        && cbb_read32(core, CBB_MAILBOX + 0x70U) == accepted;
}

static bool cbb_invalid_cases(struct mCore *core,
                              const struct CbbSymbols *symbols,
                              bool *torn_duplicate_stale,
                              bool *future_nonce_crc,
                              bool *phase_oversize_command)
{
    uint32_t accepted = cbb_read32(core, CBB_MAILBOX + 0x70U);
    uint32_t expected = accepted + 1U;
    uint32_t snapshot = cbb_read32(core, CBB_MAILBOX + 0x40U);
    uint32_t nonce = cbb_read32(core, CBB_MAILBOX + 0x28U);
    uint8_t request[64];
    cbb_build_request(request, nonce, expected, 0x71000001U, REQUEST_VALID);
    cbb_write_request(core, request, true);
    cbb_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    bool torn = cbb_read32(core, CBB_MAILBOX + 0x40U) == snapshot
        && cbb_read32(core, CBB_MAILBOX + 0x70U) == accepted;

    /* Restore the last accepted request: exact duplicate must be byte-stable. */
    uint32_t duplicate_sequence = accepted;
    cbb_build_request(request, nonce, duplicate_sequence, 0x71000002U, REQUEST_VALID);
    cbb_write_request(core, request, false);
    snapshot = cbb_read32(core, CBB_MAILBOX + 0x40U);
    cbb_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    bool duplicate = cbb_read32(core, CBB_MAILBOX + 0x40U) == snapshot
        && cbb_read32(core, CBB_MAILBOX + 0x70U) == accepted;

    bool stale = cbb_error_case(core, symbols, REQUEST_STALE,
                                accepted - 1U, CBB_ERROR_STALE, 3U);
    bool future = cbb_error_case(core, symbols, REQUEST_FUTURE,
                                 expected + 1U, CBB_ERROR_FUTURE, 4U);
    bool wrong_nonce = cbb_error_case(core, symbols, REQUEST_WRONG_NONCE,
                                      expected, CBB_ERROR_NONCE, 5U);
    bool payload_crc = cbb_error_case(core, symbols, REQUEST_PAYLOAD_CRC,
                                      expected, CBB_ERROR_PAYLOAD_CRC, 6U);
    bool request_crc = cbb_error_case(core, symbols, REQUEST_REQUEST_CRC,
                                      expected, CBB_ERROR_REQUEST_CRC, 7U);
    bool phase = cbb_error_case(core, symbols, REQUEST_WRONG_PHASE,
                                expected, CBB_ERROR_PHASE, 8U);
    bool oversize = cbb_error_case(core, symbols, REQUEST_OVERSIZE,
                                   expected, CBB_ERROR_OVERSIZE, 9U);
    bool command = cbb_error_case(core, symbols, REQUEST_UNKNOWN_COMMAND,
                                  expected, CBB_ERROR_COMMAND, 10U);
    *torn_duplicate_stale = torn && duplicate && stale;
    *future_nonce_crc = future && wrong_nonce && payload_crc && request_crc;
    *phase_oversize_command = phase && oversize && command;
    return *torn_duplicate_stale && *future_nonce_crc && *phase_oversize_command;
}

static bool cbb_roots(struct mCore *core, const struct CbbSymbols *symbols,
                      const struct CbbCases *cases)
{
    bool exports = true;
#define CBB_EXPORT_CHECK(member, name) exports = exports && ((symbols->member & 1U) != 0U);
    CBB_SYMBOL_LIST(CBB_EXPORT_CHECK)
#undef CBB_EXPORT_CHECK
    bool stub = read8(core, CBB_HOOK_STUB) == 0x00U
        && read8(core, CBB_HOOK_STUB + 1U) == 0x4BU
        && read8(core, CBB_HOOK_STUB + 2U) == 0x18U
        && read8(core, CBB_HOOK_STUB + 3U) == 0x47U;
    bool payload = true;
    static const uint8_t signature[8] = {'V', 'E', 'G', 'A', 'C', 'B', '4', '3'};
    for (unsigned index = 0U; index < sizeof(signature); ++index)
        payload = payload && read8(core, cases->payload_address + index) == signature[index];
    bool mailbox = cases->mailbox_address == CBB_MAILBOX;
    bool hook = cbb_read32(core, CBB_HOOK_POINTER) == symbols->read_keys;
    bool result = exports && stub && payload && mailbox && hook;
    if (!result) {
        fprintf(stderr,
                "mgba-codex-battle-bridge roots: exports=%u stub=%u "
                "payload=%u mailbox=%u hook=%u hook_value=%08" PRIX32
                " expected=%08" PRIX32 "\n",
                exports, stub, payload, mailbox, hook,
                cbb_read32(core, CBB_HOOK_POINTER), symbols->read_keys);
    }
    return result;
}

int main(int argc, char **argv)
{
    if (argc != 5)
        return 2;
    bool full = !strcmp(argv[4], "full");
    if (!full && strcmp(argv[4], "quick"))
        return 2;
    struct CbbSymbols symbols = cbb_load_symbols(argv[2]);
    struct CbbCases cases = cbb_load_cases(argv[3]);
    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {
        .sample = NULL, .unixTime = fixed_unix_time,
        .serialize = NULL, .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core))
        cbb_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1]))
        cbb_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);

    cbb_seed_protected(core);
    uint32_t protected_hashes[ARRAY_LEN(PROTECTED_SPANS)];
    cbb_capture_protected(core, protected_hashes);
    bool fixture = cases.schema && cases.exact_case_names
        && cases.mailbox_address == CBB_MAILBOX;
    bool roots = cbb_roots(core, &symbols, &cases);
    bool header = cbb_header(core, &symbols)
        && cbb_protected_equal(core, protected_hashes);
    unsigned iterations = full ? 64U : 8U;
    bool ping = true;
    for (unsigned index = 0U; index < iterations; ++index)
        ping = ping && cbb_ping_once(core, &symbols, 0x43000001U + index);
    bool torn_duplicate_stale = false;
    bool future_nonce_crc = false;
    bool phase_oversize_command = false;
    bool invalid = cbb_invalid_cases(
        core, &symbols, &torn_duplicate_stale,
        &future_nonce_crc, &phase_oversize_command);
    bool protected_unchanged = cbb_protected_equal(core, protected_hashes);
    bool warnings = log_problem_count == 0U;
    bool tests[] = {
        fixture, roots, roots, header, ping, torn_duplicate_stale,
        future_nonce_crc, phase_oversize_command,
        protected_unchanged && invalid, warnings,
    };
    bool passed = true;
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index)
        passed = passed && tests[index];

    char rom_sha[65], runner_sha[65], symbols_sha[65], cases_sha[65];
    sha256_file(argv[1], rom_sha);
    sha256_file(argv[0], runner_sha);
    sha256_file(argv[2], symbols_sha);
    sha256_file(argv[3], cases_sha);
    fprintf(stderr,
            "mgba-codex-battle-bridge %s: fixture=%u roots=%u header=%u "
            "ping=%u invalid=%u protected=%u logs=%u\n",
            full ? "full" : "quick", fixture, roots, header, ping,
            invalid, protected_unchanged, log_problem_count);
    printf(
        "{\"schema_version\":1,\"task\":\"T26\",\"mode\":\"%s\","
        "\"status\":\"%s\",\"result_identity\":\"CB43:1:256:512:10:7\","
        "\"rom_sha256\":\"%s\",\"runner_sha256\":\"%s\","
        "\"symbols_sha256\":\"%s\",\"cases_sha256\":\"%s\","
        "\"tests\":{\"case_fixture\":%s,\"runtime_exports\":%s,"
        "\"rooted_delegate\":%s,\"header_snapshot_crc\":%s,"
        "\"ping_pong\":%s,\"torn_duplicate_stale\":%s,"
        "\"future_nonce_crc\":%s,\"phase_oversize_command\":%s,"
        "\"protected_state_unchanged\":%s,\"warnings_zero\":%s},"
        "\"total\":%zu,\"warnings\":%u,\"invalid_case_count\":10,"
        "\"protected_span_count\":7}\n",
        full ? "full" : "quick", passed ? "PASS" : "FAIL",
        rom_sha, runner_sha, symbols_sha, cases_sha,
        fixture ? "true" : "false", roots ? "true" : "false",
        roots ? "true" : "false", header ? "true" : "false",
        ping ? "true" : "false", torn_duplicate_stale ? "true" : "false",
        future_nonce_crc ? "true" : "false",
        phase_oversize_command ? "true" : "false",
        protected_unchanged && invalid ? "true" : "false",
        warnings ? "true" : "false", ARRAY_LEN(tests), log_problem_count);

    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return passed ? 0 : 1;
}
