/*
 * Factory / CFRU Factory-like behavior fixture runner.
 *
 * This program executes selected FireRed Special ABI functions in isolated
 * libmGBA cores.  It never writes a ROM, save file, savestate, or RAM dump.
 * Build example:
 *   cc -std=c11 -O2 -Wall -Wextra -Werror \
 *      -o build/factory_fixture_runner tools/factory_fixture_runner.c -lmgba
 * Run example:
 *   build/factory_fixture_runner \
 *      --config config/factory_fixture_inputs.json \
 *      --factory build/reference/factory.gba \
 *      --candidate build/upstream-cache/<fingerprint>/cfru/factory-like/run-1/test.gba \
 *      --candidate-sha256 <hash-from-current-build-outcome>
 */

#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <mgba/core/core.h>
#include <mgba/internal/arm/arm.h>
#include <mgba/internal/arm/isa-inlines.h>

#define ARRAY_COUNT(array) (sizeof(array) / sizeof((array)[0]))
#define MAX_CONFIG_BYTES (1024U * 1024U)
#define MAX_SELECTION_SEEDS 32U
#define MAX_BP_STREAKS 128U
#define MAX_RANDOMIZE_STREAKS 32U
#define MAX_RANDOMIZE_SEEDS 16U
#define MAX_RANDOMIZE_TIERS 8U
#define MAX_RANDOMIZE_CASES \
    (MAX_RANDOMIZE_TIERS * MAX_RANDOMIZE_STREAKS * MAX_RANDOMIZE_SEEDS)
#define PARTY_SIZE 6U
#define SHA256_HEX_LENGTH 64U
#define EWRAM_START 0x02000000U
#define EWRAM_SIZE 0x00040000U
#define IWRAM_START 0x03000000U
#define IWRAM_SIZE 0x00008000U

struct Sha256Context {
    uint8_t data[64];
    uint32_t data_length;
    uint64_t bit_length;
    uint32_t state[8];
};

struct FixtureConfig {
    char fixture_id[96];
    char factory_sha256[SHA256_HEX_LENGTH + 1U];
    char candidate_sha256[SHA256_HEX_LENGTH + 1U];
    uint32_t independent_runs;
    uint32_t instruction_limit;
    uint32_t special_table_address;
    uint32_t var_set_address;
    uint32_t var_get_address;
    uint32_t create_mon_address;
    uint32_t set_mon_data_address;
    uint32_t flag_get_address;
    uint32_t rng_address;
    uint32_t save_block1_pointer_address;
    uint32_t save_block2_pointer_address;
    uint32_t save_block1_fixture_address;
    uint32_t save_block2_fixture_address;
    uint32_t player_party_address;
    uint32_t special_var_8000_address;
    uint32_t special_var_last_result_address;
    uint32_t scratch_address;
    uint32_t stack_top_address;
    uint32_t return_sentinel_address;
    uint32_t selection_special_id;
    uint32_t bp_update_special_id;
    uint32_t bp_reward_special_id;
    uint32_t eligibility_special_id;
    uint32_t randomize_options_special_id;
    uint32_t facility_number_var;
    uint32_t facility_party_size_var;
    uint32_t facility_level_var;
    uint32_t facility_battle_type_var;
    uint32_t facility_tier_var;
    uint32_t facility_trainer_id_var;
    uint32_t facility_trainer_name_var;
    uint32_t pokemon_struct_size;
    uint32_t mon_data_is_egg;
    uint32_t ot_id_preset;
    uint32_t selection_battler;
    uint32_t selection_trainer_group;
    uint32_t selection_brain_id;
    uint32_t selection_seeds[MAX_SELECTION_SEEDS];
    size_t selection_seed_count;
    uint32_t bp_facility_number;
    uint32_t bp_party_size;
    uint32_t bp_level;
    uint32_t bp_battle_type;
    uint32_t bp_tier;
    uint32_t bp_streaks[MAX_BP_STREAKS];
    size_t bp_streak_count;
    uint32_t battle_mine_facility_number;
    uint32_t battle_mine_original_tiers[MAX_RANDOMIZE_TIERS];
    size_t battle_mine_original_tier_count;
    uint32_t inverse_flag;
    uint32_t dynamax_flag;
    uint32_t randomize_option_streaks[MAX_RANDOMIZE_STREAKS];
    size_t randomize_option_streak_count;
    uint32_t randomize_option_seeds[MAX_RANDOMIZE_SEEDS];
    size_t randomize_option_seed_count;
    uint32_t eligibility_choice;
    uint32_t eligibility_species[PARTY_SIZE];
    uint32_t eligibility_level;
    uint32_t eligibility_fixed_iv;
    uint32_t eligibility_personality_base;
    uint32_t eligibility_ot_id;
};

struct Entrypoints {
    uint32_t selection;
    uint32_t bp_update;
    uint32_t bp_reward;
    uint32_t eligibility;
    uint32_t randomize_options;
};

struct SelectionObservation {
    uint32_t seed;
    uint32_t overworld_sprite;
    uint32_t trainer_id;
    uint32_t trainer_name_id;
    uint32_t rng_after;
};

struct BpObservation {
    uint32_t streak;
    uint32_t reward;
};

struct EligibilityObservation {
    uint32_t empty_party;
    uint32_t valid_six;
    uint32_t egg_in_party;
};

struct RandomizeObservation {
    uint32_t streak;
    uint32_t seed;
    uint32_t original_tier;
    uint32_t format;
    uint32_t tier;
    uint32_t level;
    uint32_t party_size;
    uint32_t inverse;
    uint32_t dynamax;
    uint32_t rng_after;
};

struct RomObservation {
    struct Entrypoints entrypoints;
    struct SelectionObservation selection[MAX_SELECTION_SEEDS];
    size_t selection_count;
    struct BpObservation bp[MAX_BP_STREAKS];
    size_t bp_count;
    struct EligibilityObservation eligibility;
    struct RandomizeObservation randomize[MAX_RANDOMIZE_CASES];
    size_t randomize_count;
};

enum CallStatus {
    CALL_STATUS_RETURNED,
    CALL_STATUS_TIMEOUT,
    CALL_STATUS_INVALID,
};

struct LoadedCore {
    struct mCore *core;
    struct ARMCore *cpu;
};

static uint32_t rotate_right(uint32_t value, uint32_t bits) {
    return (value >> bits) | (value << (32U - bits));
}

static void sha256_transform(struct Sha256Context *context, const uint8_t data[64]) {
    static const uint32_t constants[64] = {
        0x428A2F98U, 0x71374491U, 0xB5C0FBCFU, 0xE9B5DBA5U,
        0x3956C25BU, 0x59F111F1U, 0x923F82A4U, 0xAB1C5ED5U,
        0xD807AA98U, 0x12835B01U, 0x243185BEU, 0x550C7DC3U,
        0x72BE5D74U, 0x80DEB1FEU, 0x9BDC06A7U, 0xC19BF174U,
        0xE49B69C1U, 0xEFBE4786U, 0x0FC19DC6U, 0x240CA1CCU,
        0x2DE92C6FU, 0x4A7484AAU, 0x5CB0A9DCU, 0x76F988DAU,
        0x983E5152U, 0xA831C66DU, 0xB00327C8U, 0xBF597FC7U,
        0xC6E00BF3U, 0xD5A79147U, 0x06CA6351U, 0x14292967U,
        0x27B70A85U, 0x2E1B2138U, 0x4D2C6DFCU, 0x53380D13U,
        0x650A7354U, 0x766A0ABBU, 0x81C2C92EU, 0x92722C85U,
        0xA2BFE8A1U, 0xA81A664BU, 0xC24B8B70U, 0xC76C51A3U,
        0xD192E819U, 0xD6990624U, 0xF40E3585U, 0x106AA070U,
        0x19A4C116U, 0x1E376C08U, 0x2748774CU, 0x34B0BCB5U,
        0x391C0CB3U, 0x4ED8AA4AU, 0x5B9CCA4FU, 0x682E6FF3U,
        0x748F82EEU, 0x78A5636FU, 0x84C87814U, 0x8CC70208U,
        0x90BEFFFAU, 0xA4506CEBU, 0xBEF9A3F7U, 0xC67178F2U,
    };
    uint32_t words[64];
    uint32_t a;
    uint32_t b;
    uint32_t c;
    uint32_t d;
    uint32_t e;
    uint32_t f;
    uint32_t g;
    uint32_t h;

    for (size_t index = 0; index < 16U; ++index) {
        const size_t offset = index * 4U;
        words[index] = ((uint32_t)data[offset] << 24U)
            | ((uint32_t)data[offset + 1U] << 16U)
            | ((uint32_t)data[offset + 2U] << 8U)
            | (uint32_t)data[offset + 3U];
    }
    for (size_t index = 16U; index < ARRAY_COUNT(words); ++index) {
        const uint32_t s0 = rotate_right(words[index - 15U], 7U)
            ^ rotate_right(words[index - 15U], 18U)
            ^ (words[index - 15U] >> 3U);
        const uint32_t s1 = rotate_right(words[index - 2U], 17U)
            ^ rotate_right(words[index - 2U], 19U)
            ^ (words[index - 2U] >> 10U);
        words[index] = words[index - 16U] + s0 + words[index - 7U] + s1;
    }

    a = context->state[0];
    b = context->state[1];
    c = context->state[2];
    d = context->state[3];
    e = context->state[4];
    f = context->state[5];
    g = context->state[6];
    h = context->state[7];

    for (size_t index = 0; index < ARRAY_COUNT(words); ++index) {
        const uint32_t s1 = rotate_right(e, 6U) ^ rotate_right(e, 11U) ^ rotate_right(e, 25U);
        const uint32_t choose = (e & f) ^ ((~e) & g);
        const uint32_t temporary1 = h + s1 + choose + constants[index] + words[index];
        const uint32_t s0 = rotate_right(a, 2U) ^ rotate_right(a, 13U) ^ rotate_right(a, 22U);
        const uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
        const uint32_t temporary2 = s0 + majority;
        h = g;
        g = f;
        f = e;
        e = d + temporary1;
        d = c;
        c = b;
        b = a;
        a = temporary1 + temporary2;
    }

    context->state[0] += a;
    context->state[1] += b;
    context->state[2] += c;
    context->state[3] += d;
    context->state[4] += e;
    context->state[5] += f;
    context->state[6] += g;
    context->state[7] += h;
}

static void sha256_init(struct Sha256Context *context) {
    context->data_length = 0U;
    context->bit_length = 0U;
    context->state[0] = 0x6A09E667U;
    context->state[1] = 0xBB67AE85U;
    context->state[2] = 0x3C6EF372U;
    context->state[3] = 0xA54FF53AU;
    context->state[4] = 0x510E527FU;
    context->state[5] = 0x9B05688CU;
    context->state[6] = 0x1F83D9ABU;
    context->state[7] = 0x5BE0CD19U;
}

static void sha256_update(struct Sha256Context *context, const uint8_t *data, size_t length) {
    for (size_t index = 0; index < length; ++index) {
        context->data[context->data_length++] = data[index];
        if (context->data_length == sizeof(context->data)) {
            sha256_transform(context, context->data);
            context->bit_length += 512U;
            context->data_length = 0U;
        }
    }
}

static void sha256_final(struct Sha256Context *context, uint8_t hash[32]) {
    uint32_t index = context->data_length;
    context->data[index++] = 0x80U;
    if (index > 56U) {
        while (index < 64U) {
            context->data[index++] = 0U;
        }
        sha256_transform(context, context->data);
        index = 0U;
    }
    while (index < 56U) {
        context->data[index++] = 0U;
    }
    context->bit_length += (uint64_t)context->data_length * 8U;
    for (size_t byte = 0; byte < 8U; ++byte) {
        context->data[63U - byte] = (uint8_t)(context->bit_length >> (byte * 8U));
    }
    sha256_transform(context, context->data);
    for (size_t word = 0; word < 8U; ++word) {
        hash[word * 4U] = (uint8_t)(context->state[word] >> 24U);
        hash[word * 4U + 1U] = (uint8_t)(context->state[word] >> 16U);
        hash[word * 4U + 2U] = (uint8_t)(context->state[word] >> 8U);
        hash[word * 4U + 3U] = (uint8_t)context->state[word];
    }
}

static void sha256_to_hex(
    const uint8_t digest[32],
    char output[SHA256_HEX_LENGTH + 1U]
) {
    static const char digits[] = "0123456789abcdef";
    for (size_t index = 0; index < 32U; ++index) {
        output[index * 2U] = digits[digest[index] >> 4U];
        output[index * 2U + 1U] = digits[digest[index] & 0x0FU];
    }
    output[SHA256_HEX_LENGTH] = '\0';
}

static bool sha256_file(const char *path, char output[SHA256_HEX_LENGTH + 1U]) {
    uint8_t buffer[64U * 1024U];
    uint8_t digest[32];
    struct Sha256Context context;
    FILE *file = fopen(path, "rb");
    if (file == NULL) {
        fprintf(stderr, "ROMを開けません: %s: %s\n", path, strerror(errno));
        return false;
    }
    sha256_init(&context);
    while (!feof(file)) {
        const size_t length = fread(buffer, 1U, sizeof(buffer), file);
        if (length != 0U) {
            sha256_update(&context, buffer, length);
        }
        if (ferror(file)) {
            fprintf(stderr, "ROMの読取りに失敗しました: %s\n", path);
            fclose(file);
            return false;
        }
    }
    fclose(file);
    sha256_final(&context, digest);
    sha256_to_hex(digest, output);
    return true;
}

static char *read_text_file(const char *path) {
    FILE *file = fopen(path, "rb");
    long raw_size;
    size_t size;
    char *text;
    if (file == NULL) {
        fprintf(stderr, "fixture configを開けません: %s: %s\n", path, strerror(errno));
        return NULL;
    }
    if (fseek(file, 0L, SEEK_END) != 0 || (raw_size = ftell(file)) < 0L
        || fseek(file, 0L, SEEK_SET) != 0) {
        fprintf(stderr, "fixture configのsize取得に失敗しました: %s\n", path);
        fclose(file);
        return NULL;
    }
    if ((unsigned long)raw_size > MAX_CONFIG_BYTES) {
        fprintf(stderr, "fixture configが大きすぎます: %s\n", path);
        fclose(file);
        return NULL;
    }
    size = (size_t)raw_size;
    text = malloc(size + 1U);
    if (text == NULL) {
        fprintf(stderr, "fixture config用memoryを確保できません\n");
        fclose(file);
        return NULL;
    }
    if (fread(text, 1U, size, file) != size) {
        fprintf(stderr, "fixture configの読取りに失敗しました: %s\n", path);
        free(text);
        fclose(file);
        return NULL;
    }
    text[size] = '\0';
    fclose(file);
    return text;
}

static const char *skip_space(const char *cursor) {
    while (*cursor == ' ' || *cursor == '\t' || *cursor == '\r' || *cursor == '\n') {
        ++cursor;
    }
    return cursor;
}

static const char *json_value(const char *json, const char *key) {
    char pattern[128];
    const int written = snprintf(pattern, sizeof(pattern), "\"%s\"", key);
    const char *match;
    const char *second;
    if (written < 0 || (size_t)written >= sizeof(pattern)) {
        return NULL;
    }
    match = strstr(json, pattern);
    if (match == NULL) {
        fprintf(stderr, "fixture configに必須keyがありません: %s\n", key);
        return NULL;
    }
    second = strstr(match + (size_t)written, pattern);
    if (second != NULL) {
        fprintf(stderr, "fixture configのkeyが重複しています: %s\n", key);
        return NULL;
    }
    match = skip_space(match + (size_t)written);
    if (*match != ':') {
        fprintf(stderr, "fixture configのkey直後にcolonがありません: %s\n", key);
        return NULL;
    }
    return skip_space(match + 1);
}

static bool parse_json_string(
    const char *json,
    const char *key,
    char *output,
    size_t output_size
) {
    const char *cursor = json_value(json, key);
    size_t length = 0U;
    if (cursor == NULL || *cursor != '"') {
        fprintf(stderr, "fixture configのstringが不正です: %s\n", key);
        return false;
    }
    ++cursor;
    while (*cursor != '\0' && *cursor != '"') {
        if (*cursor == '\\' || (unsigned char)*cursor < 0x20U || length + 1U >= output_size) {
            fprintf(stderr, "fixture configのstring値が不正または長すぎます: %s\n", key);
            return false;
        }
        output[length++] = *cursor++;
    }
    if (*cursor != '"') {
        fprintf(stderr, "fixture configのstring終端がありません: %s\n", key);
        return false;
    }
    output[length] = '\0';
    return true;
}

static bool parse_u32_text(const char *text, uint32_t *output) {
    char *end = NULL;
    unsigned long long value;
    errno = 0;
    value = strtoull(text, &end, 0);
    if (errno != 0 || end == text || value > UINT32_MAX) {
        return false;
    }
    end = (char *)skip_space(end);
    if (*end != '\0') {
        return false;
    }
    *output = (uint32_t)value;
    return true;
}

static bool parse_json_u32(const char *json, const char *key, uint32_t *output) {
    const char *cursor = json_value(json, key);
    char token[64];
    size_t length = 0U;
    char terminator = '\0';
    if (cursor == NULL) {
        return false;
    }
    if (*cursor == '"') {
        terminator = '"';
        ++cursor;
    }
    while (*cursor != '\0'
           && ((terminator != '\0' && *cursor != terminator)
               || (terminator == '\0' && *cursor != ',' && *cursor != '}'
                   && *cursor != ']' && *cursor != ' ' && *cursor != '\t'
                   && *cursor != '\r' && *cursor != '\n'))) {
        if (length + 1U >= sizeof(token)) {
            fprintf(stderr, "fixture configの数値が長すぎます: %s\n", key);
            return false;
        }
        token[length++] = *cursor++;
    }
    if (terminator != '\0' && *cursor != terminator) {
        fprintf(stderr, "fixture configのquoted数値終端がありません: %s\n", key);
        return false;
    }
    token[length] = '\0';
    if (!parse_u32_text(token, output)) {
        fprintf(stderr, "fixture configの数値が不正です: %s=%s\n", key, token);
        return false;
    }
    return true;
}

static bool parse_json_u32_array(
    const char *json,
    const char *key,
    uint32_t *output,
    size_t capacity,
    size_t *count
) {
    const char *cursor = json_value(json, key);
    *count = 0U;
    if (cursor == NULL || *cursor != '[') {
        fprintf(stderr, "fixture configのarrayが不正です: %s\n", key);
        return false;
    }
    cursor = skip_space(cursor + 1);
    while (*cursor != ']') {
        char *end = NULL;
        unsigned long long value;
        if (*count >= capacity) {
            fprintf(stderr, "fixture configのarray要素が多すぎます: %s\n", key);
            return false;
        }
        errno = 0;
        value = strtoull(cursor, &end, 10);
        if (errno != 0 || end == cursor || value > UINT32_MAX) {
            fprintf(stderr, "fixture configのarray数値が不正です: %s\n", key);
            return false;
        }
        output[(*count)++] = (uint32_t)value;
        cursor = skip_space(end);
        if (*cursor == ',') {
            cursor = skip_space(cursor + 1);
        } else if (*cursor != ']') {
            fprintf(stderr, "fixture configのarray区切りが不正です: %s\n", key);
            return false;
        }
    }
    if (*count == 0U) {
        fprintf(stderr, "fixture configのarrayが空です: %s\n", key);
        return false;
    }
    return true;
}

static bool is_lower_hex_digest(const char *value) {
    if (strlen(value) != SHA256_HEX_LENGTH) {
        return false;
    }
    for (size_t index = 0; index < SHA256_HEX_LENGTH; ++index) {
        if (!((value[index] >= '0' && value[index] <= '9')
              || (value[index] >= 'a' && value[index] <= 'f'))) {
            return false;
        }
    }
    return true;
}

static bool load_config(const char *path, struct FixtureConfig *config) {
    char *json = read_text_file(path);
    uint32_t schema_version = 0U;
    bool success = false;
    memset(config, 0, sizeof(*config));
    if (json == NULL) {
        return false;
    }
#define PARSE_U32(field, key) \
    do { if (!parse_json_u32(json, (key), &config->field)) goto cleanup; } while (false)
    if (!parse_json_u32(json, "schema_version", &schema_version)
        || schema_version != 1U
        || !parse_json_string(json, "fixture_id", config->fixture_id, sizeof(config->fixture_id))
        || !parse_json_string(
            json, "factory_reference_sha256", config->factory_sha256,
            sizeof(config->factory_sha256))
        || !parse_json_string(
            json, "factory_like_candidate_sha256", config->candidate_sha256,
            sizeof(config->candidate_sha256))) {
        goto cleanup;
    }
    PARSE_U32(independent_runs, "independent_runs");
    PARSE_U32(instruction_limit, "instruction_limit_per_call");
    PARSE_U32(special_table_address, "special_table_address");
    PARSE_U32(var_set_address, "var_set_address");
    PARSE_U32(var_get_address, "var_get_address");
    PARSE_U32(create_mon_address, "create_mon_address");
    PARSE_U32(set_mon_data_address, "set_mon_data_address");
    PARSE_U32(flag_get_address, "flag_get_address");
    PARSE_U32(rng_address, "rng_address");
    PARSE_U32(save_block1_pointer_address, "save_block1_pointer_address");
    PARSE_U32(save_block2_pointer_address, "save_block2_pointer_address");
    PARSE_U32(save_block1_fixture_address, "save_block1_fixture_address");
    PARSE_U32(save_block2_fixture_address, "save_block2_fixture_address");
    PARSE_U32(player_party_address, "player_party_address");
    PARSE_U32(special_var_8000_address, "special_var_8000_address");
    PARSE_U32(special_var_last_result_address, "special_var_last_result_address");
    PARSE_U32(scratch_address, "scratch_address");
    PARSE_U32(stack_top_address, "stack_top_address");
    PARSE_U32(return_sentinel_address, "return_sentinel_address");
    PARSE_U32(selection_special_id, "selection_special_id");
    PARSE_U32(bp_update_special_id, "bp_update_special_id");
    PARSE_U32(bp_reward_special_id, "bp_reward_special_id");
    PARSE_U32(eligibility_special_id, "eligibility_special_id");
    PARSE_U32(randomize_options_special_id, "randomize_options_special_id");
    PARSE_U32(facility_number_var, "facility_number_var");
    PARSE_U32(facility_party_size_var, "facility_party_size_var");
    PARSE_U32(facility_level_var, "facility_level_var");
    PARSE_U32(facility_battle_type_var, "facility_battle_type_var");
    PARSE_U32(facility_tier_var, "facility_tier_var");
    PARSE_U32(facility_trainer_id_var, "facility_trainer_id_var");
    PARSE_U32(facility_trainer_name_var, "facility_trainer_name_var");
    PARSE_U32(pokemon_struct_size, "pokemon_struct_size");
    PARSE_U32(mon_data_is_egg, "mon_data_is_egg");
    PARSE_U32(ot_id_preset, "ot_id_preset");
    PARSE_U32(selection_battler, "selection_battler");
    PARSE_U32(selection_trainer_group, "selection_trainer_group");
    PARSE_U32(selection_brain_id, "selection_brain_id");
    PARSE_U32(bp_facility_number, "bp_facility_number");
    PARSE_U32(bp_party_size, "bp_party_size");
    PARSE_U32(bp_level, "bp_level");
    PARSE_U32(bp_battle_type, "bp_battle_type");
    PARSE_U32(bp_tier, "bp_tier");
    PARSE_U32(battle_mine_facility_number, "battle_mine_facility_number");
    PARSE_U32(inverse_flag, "inverse_flag");
    PARSE_U32(dynamax_flag, "dynamax_flag");
    PARSE_U32(eligibility_choice, "eligibility_choice");
    PARSE_U32(eligibility_level, "eligibility_level");
    PARSE_U32(eligibility_fixed_iv, "eligibility_fixed_iv");
    PARSE_U32(eligibility_personality_base, "eligibility_personality_base");
    PARSE_U32(eligibility_ot_id, "eligibility_ot_id");
#undef PARSE_U32
    if (!parse_json_u32_array(
            json, "selection_seeds", config->selection_seeds,
            ARRAY_COUNT(config->selection_seeds), &config->selection_seed_count)
        || !parse_json_u32_array(
            json, "bp_streaks", config->bp_streaks,
            ARRAY_COUNT(config->bp_streaks), &config->bp_streak_count)
        || !parse_json_u32_array(
            json, "battle_mine_original_tiers", config->battle_mine_original_tiers,
            ARRAY_COUNT(config->battle_mine_original_tiers),
            &config->battle_mine_original_tier_count)
        || !parse_json_u32_array(
            json, "randomize_option_streaks", config->randomize_option_streaks,
            ARRAY_COUNT(config->randomize_option_streaks),
            &config->randomize_option_streak_count)
        || !parse_json_u32_array(
            json, "randomize_option_seeds", config->randomize_option_seeds,
            ARRAY_COUNT(config->randomize_option_seeds),
            &config->randomize_option_seed_count)
        ) {
        goto cleanup;
    }
    {
        size_t species_count = 0U;
        if (!parse_json_u32_array(
                json, "eligibility_species", config->eligibility_species,
                ARRAY_COUNT(config->eligibility_species), &species_count)
            || species_count != PARTY_SIZE) {
            fprintf(stderr, "eligibility_speciesは6要素でなければなりません\n");
            goto cleanup;
        }
    }
    if (!is_lower_hex_digest(config->factory_sha256)
        || strcmp(config->candidate_sha256, "FROM_BUILD_OUTCOME") != 0
        || config->fixture_id[0] == '\0'
        || config->independent_runs != 2U
        || config->instruction_limit < 1000U
        || config->special_table_address < 0x08000000U
        || config->special_table_address >= 0x0A000000U
        || config->selection_special_id > 0x1FFU
        || config->bp_update_special_id > 0x1FFU
        || config->bp_reward_special_id > 0x1FFU
        || config->eligibility_special_id > 0x1FFU
        || config->randomize_options_special_id > 0x1FFU
        || config->eligibility_level == 0U
        || config->eligibility_level > 100U
        || config->eligibility_fixed_iv > 31U
        || config->pokemon_struct_size < 80U
        || config->pokemon_struct_size > 256U
        || config->selection_battler > 2U
        || config->selection_trainer_group > 2U
        || config->bp_party_size == 0U
        || config->bp_party_size > PARTY_SIZE
        || config->bp_level == 0U
        || config->bp_level > 100U
        || config->eligibility_choice > 2U
        || config->battle_mine_original_tier_count == 0U
        || config->randomize_option_seed_count == 0U
        || config->randomize_option_streak_count == 0U
        || config->battle_mine_original_tier_count >
            MAX_RANDOMIZE_CASES / config->randomize_option_seed_count
                / config->randomize_option_streak_count
        || config->inverse_flag > 0xFFFFU
        || config->dynamax_flag > 0xFFFFU
        ) {
        fprintf(stderr, "fixture configのcontract値が不正です\n");
        goto cleanup;
    }
    for (size_t index = 1U; index < config->bp_streak_count; ++index) {
        if (config->bp_streaks[index] <= config->bp_streaks[index - 1U]) {
            fprintf(stderr, "bp_streaksは昇順かつ重複なしでなければなりません\n");
            goto cleanup;
        }
    }
    for (size_t index = 1U; index < config->randomize_option_streak_count; ++index) {
        if (config->randomize_option_streaks[index]
            <= config->randomize_option_streaks[index - 1U]) {
            fprintf(
                stderr,
                "randomize_option_streaksは昇順かつ重複なしでなければなりません\n");
            goto cleanup;
        }
    }
    for (size_t index = 1U; index < config->battle_mine_original_tier_count; ++index) {
        if (config->battle_mine_original_tiers[index]
            <= config->battle_mine_original_tiers[index - 1U]) {
            fprintf(
                stderr,
                "battle_mine_original_tiersは昇順かつ重複なしでなければなりません\n");
            goto cleanup;
        }
    }
    success = true;
cleanup:
    free(json);
    return success;
}

static void close_core(struct LoadedCore *loaded) {
    if (loaded->core != NULL) {
        loaded->core->deinit(loaded->core);
    }
    loaded->core = NULL;
    loaded->cpu = NULL;
}

static bool clear_memory_block(struct mCore *core, uint32_t address, size_t required_size) {
    size_t available = 0U;
    void *memory = mCoreGetMemoryBlock(core, address, &available);
    if (memory == NULL || available < required_size) {
        fprintf(stderr, "mGBA memory blockを取得できません: 0x%08" PRIx32 "\n", address);
        return false;
    }
    memset(memory, 0, required_size);
    return true;
}

static bool prepare_core(
    struct LoadedCore *loaded,
    const struct FixtureConfig *config
) {
    struct mCore *core = loaded->core;
    core->reset(core);
    loaded->cpu = (struct ARMCore *)core->cpu;
    if (loaded->cpu == NULL
        || !clear_memory_block(core, EWRAM_START, EWRAM_SIZE)
        || !clear_memory_block(core, IWRAM_START, IWRAM_SIZE)) {
        return false;
    }
    core->busWrite16(core, config->return_sentinel_address, 0xE7FEU); /* b . */
    core->busWrite32(
        core, config->save_block1_pointer_address, config->save_block1_fixture_address);
    core->busWrite32(
        core, config->save_block2_pointer_address, config->save_block2_fixture_address);
    return true;
}

static bool open_core(
    const char *rom_path,
    const struct FixtureConfig *config,
    struct LoadedCore *loaded
) {
    struct mCore *core;
    memset(loaded, 0, sizeof(*loaded));
    core = mCoreFind(rom_path);
    if (core == NULL) {
        fprintf(stderr, "mGBAがROM coreを判定できません: %s\n", rom_path);
        return false;
    }
    if (!core->init(core)) {
        fprintf(stderr, "mGBA core初期化に失敗しました: %s\n", rom_path);
        free(core);
        return false;
    }
    mCoreInitConfig(core, NULL);
    core->opts.useBios = false;
    core->opts.skipBios = true;
    if (!mCoreLoadFile(core, rom_path)) {
        fprintf(stderr, "mGBA coreへROMをloadできません: %s\n", rom_path);
        core->deinit(core);
        return false;
    }
    loaded->core = core;
    loaded->cpu = (struct ARMCore *)core->cpu;
    if (!prepare_core(loaded, config)) {
        close_core(loaded);
        return false;
    }
    return true;
}

static enum CallStatus call_thumb_status(
    struct LoadedCore *loaded,
    const struct FixtureConfig *config,
    uint32_t function,
    const uint32_t arguments[4],
    const uint32_t *stack_arguments,
    size_t stack_argument_count,
    uint32_t instruction_limit,
    uint32_t *result,
    uint32_t *instructions
) {
    struct ARMCore *cpu = loaded->cpu;
    struct mCore *core = loaded->core;
    uint32_t stack_pointer;
    if ((function & 1U) == 0U || (function & ~1U) < 0x08000000U
        || (function & ~1U) >= 0x0A000000U
        || stack_argument_count > 32U) {
        fprintf(stderr, "Thumb function pointerが不正です: 0x%08" PRIx32 "\n", function);
        return CALL_STATUS_INVALID;
    }
    stack_pointer = config->stack_top_address - (uint32_t)(stack_argument_count * 4U);
    stack_pointer &= ~7U;
    for (size_t index = 0; index < stack_argument_count; ++index) {
        core->busWrite32(core, stack_pointer + (uint32_t)(index * 4U), stack_arguments[index]);
    }
    for (size_t index = 0; index < 13U; ++index) {
        cpu->gprs[index] = 0;
    }
    for (size_t index = 0; index < 4U; ++index) {
        cpu->gprs[index] = (int32_t)arguments[index];
    }
    cpu->gprs[ARM_SP] = (int32_t)stack_pointer;
    cpu->gprs[ARM_LR] = (int32_t)(config->return_sentinel_address | 1U);
    cpu->cpsr.i = 1U;
    cpu->cpsr.f = 1U;
    cpu->halted = 0;
    _ARMSetMode(cpu, MODE_THUMB);
    cpu->gprs[ARM_PC] = (int32_t)(function & ~1U);
    cpu->cycles += ThumbWritePC(cpu);
    for (uint32_t instruction = 0U; instruction < instruction_limit; ++instruction) {
        /*
         * Immediately after ThumbWritePC, mGBA keeps PC at target + 2 until
         * the next instruction advances the pipeline.  Detect the sentinel
         * before executing its defensive infinite-loop instruction.
         */
        if ((uint32_t)cpu->gprs[ARM_PC] == config->return_sentinel_address + 2U
            || _ARMPCAddress(cpu) == config->return_sentinel_address) {
            *result = (uint32_t)cpu->gprs[0];
            if (instructions != NULL) {
                *instructions = instruction;
            }
            return CALL_STATUS_RETURNED;
        }
        core->step(core);
    }
    if (instructions != NULL) {
        *instructions = instruction_limit;
    }
    return CALL_STATUS_TIMEOUT;
}

static bool call_thumb(
    struct LoadedCore *loaded,
    const struct FixtureConfig *config,
    uint32_t function,
    const uint32_t arguments[4],
    const uint32_t *stack_arguments,
    size_t stack_argument_count,
    uint32_t *result
) {
    const enum CallStatus status = call_thumb_status(
        loaded, config, function, arguments, stack_arguments,
        stack_argument_count, config->instruction_limit, result, NULL);
    if (status == CALL_STATUS_RETURNED) {
        return true;
    }
    if (status == CALL_STATUS_INVALID) {
        return false;
    }
    fprintf(
        stderr,
        "ROM functionがinstruction limit内にreturnしません: function=0x%08" PRIx32
        " pc=0x%08" PRIx32 "\n",
        function, _ARMPCAddress(loaded->cpu));
    return false;
}

static bool call_no_stack(
    struct LoadedCore *loaded,
    const struct FixtureConfig *config,
    uint32_t function,
    uint32_t r0,
    uint32_t r1,
    uint32_t r2,
    uint32_t r3,
    uint32_t *result
) {
    const uint32_t arguments[4] = {r0, r1, r2, r3};
    return call_thumb(loaded, config, function, arguments, NULL, 0U, result);
}

static bool var_set(
    struct LoadedCore *loaded,
    const struct FixtureConfig *config,
    uint32_t variable,
    uint32_t value
) {
    uint32_t ignored = 0U;
    return call_no_stack(
        loaded, config, config->var_set_address, variable, value, 0U, 0U, &ignored);
}

static bool var_get(
    struct LoadedCore *loaded,
    const struct FixtureConfig *config,
    uint32_t variable,
    uint32_t *value
) {
    if (!call_no_stack(
            loaded, config, config->var_get_address, variable, 0U, 0U, 0U, value)) {
        return false;
    }
    *value &= 0xFFFFU;
    return true;
}

static bool flag_get(
    struct LoadedCore *loaded,
    const struct FixtureConfig *config,
    uint32_t flag,
    uint32_t *value
) {
    if (!call_no_stack(
            loaded, config, config->flag_get_address, flag, 0U, 0U, 0U, value)) {
        return false;
    }
    *value = *value != 0U;
    return true;
}

static uint32_t read_special_entry(
    struct mCore *core,
    const struct FixtureConfig *config,
    uint32_t special_id
) {
    return core->busRead32(core, config->special_table_address + special_id * 4U);
}

static bool load_entrypoints(
    struct LoadedCore *loaded,
    const struct FixtureConfig *config,
    struct Entrypoints *entrypoints
) {
    entrypoints->selection = read_special_entry(
        loaded->core, config, config->selection_special_id);
    entrypoints->bp_update = read_special_entry(
        loaded->core, config, config->bp_update_special_id);
    entrypoints->bp_reward = read_special_entry(
        loaded->core, config, config->bp_reward_special_id);
    entrypoints->eligibility = read_special_entry(
        loaded->core, config, config->eligibility_special_id);
    entrypoints->randomize_options = read_special_entry(
        loaded->core, config, config->randomize_options_special_id);
    const uint32_t values[] = {
        entrypoints->selection,
        entrypoints->bp_update,
        entrypoints->bp_reward,
        entrypoints->eligibility,
        entrypoints->randomize_options,
    };
    for (size_t index = 0; index < ARRAY_COUNT(values); ++index) {
        if ((values[index] & 1U) == 0U || (values[index] & ~1U) < 0x08000000U
            || (values[index] & ~1U) >= 0x0A000000U) {
            fprintf(stderr, "ROM Special table entryが不正です: 0x%08" PRIx32 "\n", values[index]);
            return false;
        }
    }
    return true;
}

static bool observe_selection(
    struct LoadedCore *loaded,
    const struct FixtureConfig *config,
    const struct Entrypoints *entrypoints,
    struct RomObservation *observation
) {
    observation->selection_count = config->selection_seed_count;
    for (size_t index = 0; index < config->selection_seed_count; ++index) {
        struct SelectionObservation *item = &observation->selection[index];
        uint32_t result = 0U;
        item->seed = config->selection_seeds[index];
        loaded->core->busWrite32(loaded->core, config->rng_address, item->seed);
        loaded->core->busWrite16(
            loaded->core, config->special_var_8000_address, config->selection_battler);
        loaded->core->busWrite16(
            loaded->core, config->special_var_8000_address + 2U,
            config->selection_trainer_group);
        loaded->core->busWrite16(
            loaded->core, config->special_var_8000_address + 4U,
            config->selection_brain_id);
        if (!call_no_stack(
                loaded, config, entrypoints->selection, 0U, 0U, 0U, 0U, &result)) {
            return false;
        }
        item->overworld_sprite = result & 0xFFFFU;
        if (!var_get(
                loaded, config, config->facility_trainer_id_var,
                &item->trainer_id)
            || !var_get(
                loaded, config, config->facility_trainer_name_var,
                &item->trainer_name_id)) {
            return false;
        }
        item->rng_after = loaded->core->busRead32(loaded->core, config->rng_address);
    }
    return true;
}

static bool observe_bp(
    struct LoadedCore *loaded,
    const struct FixtureConfig *config,
    const struct Entrypoints *entrypoints,
    struct RomObservation *observation
) {
    uint32_t current_streak = 0U;
    if (!var_set(loaded, config, config->facility_number_var, config->bp_facility_number)
        || !var_set(loaded, config, config->facility_party_size_var, config->bp_party_size)
        || !var_set(loaded, config, config->facility_level_var, config->bp_level)
        || !var_set(loaded, config, config->facility_battle_type_var, config->bp_battle_type)
        || !var_set(loaded, config, config->facility_tier_var, config->bp_tier)) {
        return false;
    }
    observation->bp_count = config->bp_streak_count;
    for (size_t index = 0; index < config->bp_streak_count; ++index) {
        const uint32_t target = config->bp_streaks[index];
        uint32_t result = 0U;
        while (current_streak < target) {
            loaded->core->busWrite16(loaded->core, config->special_var_8000_address, 0U);
            if (!call_no_stack(
                    loaded, config, entrypoints->bp_update, 0U, 0U, 0U, 0U, &result)) {
                return false;
            }
            ++current_streak;
        }
        if (!call_no_stack(
                loaded, config, entrypoints->bp_reward, 0U, 0U, 0U, 0U, &result)) {
            return false;
        }
        observation->bp[index].streak = target;
        observation->bp[index].reward = result & 0xFFFFU;
    }
    return true;
}

static bool create_fixture_party(
    struct LoadedCore *loaded,
    const struct FixtureConfig *config
) {
    for (size_t index = 0; index < PARTY_SIZE; ++index) {
        const uint32_t arguments[4] = {
            config->player_party_address + (uint32_t)(index * config->pokemon_struct_size),
            config->eligibility_species[index],
            config->eligibility_level,
            config->eligibility_fixed_iv,
        };
        const uint32_t stack_arguments[4] = {
            1U,
            config->eligibility_personality_base + (uint32_t)index,
            config->ot_id_preset,
            config->eligibility_ot_id,
        };
        uint32_t ignored = 0U;
        if (!call_thumb(
                loaded, config, config->create_mon_address, arguments,
                stack_arguments, ARRAY_COUNT(stack_arguments), &ignored)) {
            return false;
        }
    }
    return true;
}

static bool call_eligibility(
    struct LoadedCore *loaded,
    const struct FixtureConfig *config,
    uint32_t function,
    uint32_t *result
) {
    uint32_t ignored = 0U;
    loaded->core->busWrite16(
        loaded->core, config->special_var_8000_address, config->eligibility_choice);
    if (!call_no_stack(loaded, config, function, 0U, 0U, 0U, 0U, &ignored)) {
        return false;
    }
    *result = loaded->core->busRead16(
        loaded->core, config->special_var_last_result_address);
    return true;
}

static bool observe_eligibility(
    struct LoadedCore *loaded,
    const struct FixtureConfig *config,
    const struct Entrypoints *entrypoints,
    struct RomObservation *observation
) {
    uint32_t ignored = 0U;
    if (!call_eligibility(
            loaded, config, entrypoints->eligibility,
            &observation->eligibility.empty_party)
        || !create_fixture_party(loaded, config)
        || !call_eligibility(
            loaded, config, entrypoints->eligibility,
            &observation->eligibility.valid_six)) {
        return false;
    }
    loaded->core->busWrite8(loaded->core, config->scratch_address, 1U);
    if (!call_no_stack(
            loaded, config, config->set_mon_data_address,
            config->player_party_address + 2U * config->pokemon_struct_size,
            config->mon_data_is_egg, config->scratch_address, 0U, &ignored)
        || !call_eligibility(
            loaded, config, entrypoints->eligibility,
            &observation->eligibility.egg_in_party)) {
        return false;
    }
    return true;
}

static bool set_facility_variables(
    struct LoadedCore *loaded,
    const struct FixtureConfig *config,
    uint32_t facility_number,
    uint32_t tier
) {
    return var_set(loaded, config, config->facility_number_var, facility_number)
        && var_set(loaded, config, config->facility_party_size_var, config->bp_party_size)
        && var_set(loaded, config, config->facility_level_var, config->bp_level)
        && var_set(loaded, config, config->facility_battle_type_var, config->bp_battle_type)
        && var_set(loaded, config, config->facility_tier_var, tier);
}

static bool observe_randomize_options(
    struct LoadedCore *loaded,
    const struct FixtureConfig *config,
    const struct Entrypoints *entrypoints,
    struct RomObservation *observation
) {
    size_t output_index = 0U;
    for (size_t tier_index = 0U;
         tier_index < config->battle_mine_original_tier_count;
         ++tier_index) {
        for (size_t streak_index = 0U;
             streak_index < config->randomize_option_streak_count;
             ++streak_index) {
            const uint32_t streak = config->randomize_option_streaks[streak_index];
            for (size_t seed_index = 0U;
                 seed_index < config->randomize_option_seed_count;
                 ++seed_index) {
            struct RandomizeObservation *item = &observation->randomize[output_index++];
            uint32_t ignored = 0U;
            if (!prepare_core(loaded, config)
                || !set_facility_variables(
                    loaded, config, config->battle_mine_facility_number,
                    config->battle_mine_original_tiers[tier_index])) {
                return false;
            }
            for (uint32_t current = 0U; current < streak; ++current) {
                loaded->core->busWrite16(
                    loaded->core, config->special_var_8000_address, 0U);
                if (!call_no_stack(
                        loaded, config, entrypoints->bp_update,
                        0U, 0U, 0U, 0U, &ignored)) {
                    return false;
                }
            }
            item->streak = streak;
            item->seed = config->randomize_option_seeds[seed_index];
            loaded->core->busWrite32(loaded->core, config->rng_address, item->seed);
            if (!call_no_stack(
                    loaded, config, entrypoints->randomize_options,
                    0U, 0U, 0U, 0U, &item->original_tier)
                || !var_get(
                    loaded, config, config->facility_battle_type_var, &item->format)
                || !var_get(loaded, config, config->facility_tier_var, &item->tier)
                || !var_get(loaded, config, config->facility_level_var, &item->level)
                || !var_get(
                    loaded, config, config->facility_party_size_var, &item->party_size)
                || !flag_get(loaded, config, config->inverse_flag, &item->inverse)
                || !flag_get(loaded, config, config->dynamax_flag, &item->dynamax)) {
                return false;
            }
            item->original_tier &= 0xFFU;
            item->rng_after = loaded->core->busRead32(loaded->core, config->rng_address);
            }
        }
    }
    observation->randomize_count = output_index;
    return true;
}

static bool observe_rom(
    const char *rom_path,
    const struct FixtureConfig *config,
    struct RomObservation *observation
) {
    struct LoadedCore loaded;
    bool success = false;
    memset(observation, 0, sizeof(*observation));
    if (!open_core(rom_path, config, &loaded)) {
        return false;
    }
    if (!load_entrypoints(&loaded, config, &observation->entrypoints)
        || !observe_selection(&loaded, config, &observation->entrypoints, observation)
        || !prepare_core(&loaded, config)
        || !observe_bp(&loaded, config, &observation->entrypoints, observation)
        || !prepare_core(&loaded, config)
        || !observe_eligibility(&loaded, config, &observation->entrypoints, observation)
        || !observe_randomize_options(
            &loaded, config, &observation->entrypoints, observation)) {
        goto cleanup;
    }
    success = true;
cleanup:
    close_core(&loaded);
    return success;
}

static bool selection_equal(
    const struct RomObservation *left,
    const struct RomObservation *right
) {
    if (left->selection_count != right->selection_count) {
        return false;
    }
    for (size_t index = 0; index < left->selection_count; ++index) {
        const struct SelectionObservation *a = &left->selection[index];
        const struct SelectionObservation *b = &right->selection[index];
        if (a->seed != b->seed
            || a->overworld_sprite != b->overworld_sprite
            || a->trainer_id != b->trainer_id
            || a->trainer_name_id != b->trainer_name_id
            || a->rng_after != b->rng_after) {
            return false;
        }
    }
    return true;
}

static bool bp_equal(const struct RomObservation *left, const struct RomObservation *right) {
    if (left->bp_count != right->bp_count) {
        return false;
    }
    for (size_t index = 0; index < left->bp_count; ++index) {
        if (left->bp[index].streak != right->bp[index].streak
            || left->bp[index].reward != right->bp[index].reward) {
            return false;
        }
    }
    return true;
}

static bool eligibility_equal(
    const struct RomObservation *left,
    const struct RomObservation *right
) {
    return left->eligibility.empty_party == right->eligibility.empty_party
        && left->eligibility.valid_six == right->eligibility.valid_six
        && left->eligibility.egg_in_party == right->eligibility.egg_in_party;
}

static bool randomize_equal(
    const struct RomObservation *left,
    const struct RomObservation *right
) {
    if (left->randomize_count != right->randomize_count) {
        return false;
    }
    for (size_t index = 0U; index < left->randomize_count; ++index) {
        const struct RandomizeObservation *a = &left->randomize[index];
        const struct RandomizeObservation *b = &right->randomize[index];
        if (a->streak != b->streak
            || a->seed != b->seed
            || a->original_tier != b->original_tier
            || a->format != b->format
            || a->tier != b->tier
            || a->level != b->level
            || a->party_size != b->party_size
            || a->inverse != b->inverse
            || a->dynamax != b->dynamax
            || a->rng_after != b->rng_after) {
            return false;
        }
    }
    return true;
}

static bool complete_observation_equal(
    const struct RomObservation *left,
    const struct RomObservation *right
) {
    return left->entrypoints.selection == right->entrypoints.selection
        && left->entrypoints.bp_update == right->entrypoints.bp_update
        && left->entrypoints.bp_reward == right->entrypoints.bp_reward
        && left->entrypoints.eligibility == right->entrypoints.eligibility
        && left->entrypoints.randomize_options == right->entrypoints.randomize_options
        && selection_equal(left, right)
        && bp_equal(left, right)
        && eligibility_equal(left, right)
        && randomize_equal(left, right);
}

static void print_entrypoints(const struct Entrypoints *entrypoints) {
    printf(
        "{\"selection\":\"0x%08" PRIx32 "\","
        "\"bp_update\":\"0x%08" PRIx32 "\","
        "\"bp_reward\":\"0x%08" PRIx32 "\","
        "\"eligibility\":\"0x%08" PRIx32 "\","
        "\"randomize_options\":\"0x%08" PRIx32 "\"}",
        entrypoints->selection, entrypoints->bp_update,
        entrypoints->bp_reward, entrypoints->eligibility,
        entrypoints->randomize_options);
}

static void print_selection(const struct RomObservation *observation) {
    putchar('[');
    for (size_t index = 0; index < observation->selection_count; ++index) {
        const struct SelectionObservation *item = &observation->selection[index];
        if (index != 0U) {
            putchar(',');
        }
        printf(
            "{\"seed\":%" PRIu32 ",\"overworld_sprite\":%" PRIu32
            ",\"trainer_id\":%" PRIu32 ",\"trainer_name_id\":%" PRIu32
            ",\"rng_after\":%" PRIu32 "}",
            item->seed, item->overworld_sprite, item->trainer_id,
            item->trainer_name_id, item->rng_after);
    }
    putchar(']');
}

static void print_bp(const struct RomObservation *observation) {
    putchar('[');
    for (size_t index = 0; index < observation->bp_count; ++index) {
        if (index != 0U) {
            putchar(',');
        }
        printf(
            "{\"streak\":%" PRIu32 ",\"reward\":%" PRIu32 "}",
            observation->bp[index].streak, observation->bp[index].reward);
    }
    putchar(']');
}

static void print_eligibility(const struct EligibilityObservation *observation) {
    printf(
        "{\"empty_party\":%" PRIu32 ",\"valid_six\":%" PRIu32
        ",\"egg_in_party\":%" PRIu32 "}",
        observation->empty_party, observation->valid_six, observation->egg_in_party);
}

static void print_randomize(const struct RomObservation *observation) {
    putchar('[');
    for (size_t index = 0U; index < observation->randomize_count; ++index) {
        const struct RandomizeObservation *item = &observation->randomize[index];
        if (index != 0U) {
            putchar(',');
        }
        printf(
            "{\"streak\":%" PRIu32 ",\"seed\":%" PRIu32
            ",\"original_tier\":%" PRIu32 ",\"format\":%" PRIu32
            ",\"tier\":%" PRIu32 ",\"level\":%" PRIu32
            ",\"party_size\":%" PRIu32 ",\"flags\":{" 
            "\"inverse\":%" PRIu32 ",\"dynamax\":%" PRIu32 "},"
            "\"rng_after\":%" PRIu32 "}",
            item->streak, item->seed, item->original_tier, item->format,
            item->tier, item->level, item->party_size, item->inverse,
            item->dynamax, item->rng_after);
    }
    putchar(']');
}

static void print_json(
    const struct FixtureConfig *config,
    const char *factory_actual_sha256,
    const char *candidate_actual_sha256,
    const struct RomObservation *factory,
    const struct RomObservation *candidate
) {
    const bool selection_matches = selection_equal(factory, candidate);
    const bool bp_matches = bp_equal(factory, candidate);
    const bool eligibility_matches = eligibility_equal(factory, candidate);
    const bool randomize_matches = randomize_equal(factory, candidate);
    const unsigned matching_categories = (unsigned)selection_matches
        + (unsigned)bp_matches + (unsigned)eligibility_matches
        + (unsigned)randomize_matches;
    printf("{\n");
    printf("  \"schema_version\": 1,\n");
    printf("  \"fixture_id\": \"%s\",\n", config->fixture_id);
    printf("  \"status\": \"PASS\",\n");
    printf("  \"comparison_policy\": \"different_is_classification_not_failure\",\n");
    printf("  \"artifacts_written\": [],\n");
    printf("  \"repeatability\": {\"factory\":\"PASS\",\"candidate\":\"PASS\",\"runs\":2},\n");
    printf(
        "  \"roms\": {\"factory_sha256\":\"%s\","
        "\"candidate_sha256\":\"%s\"},\n",
        factory_actual_sha256, candidate_actual_sha256);
    printf("  \"entrypoints\": {\"factory\":");
    print_entrypoints(&factory->entrypoints);
    printf(",\"candidate\":");
    print_entrypoints(&candidate->entrypoints);
    printf("},\n");
    printf(
        "  \"selection\": {\"comparison\":\"%s\",\"factory\":",
        selection_matches ? "match" : "different");
    print_selection(factory);
    printf(",\"candidate\":");
    print_selection(candidate);
    printf("},\n");
    printf(
        "  \"bp_reward\": {\"comparison\":\"%s\",\"factory\":",
        bp_matches ? "match" : "different");
    print_bp(factory);
    printf(",\"candidate\":");
    print_bp(candidate);
    printf("},\n");
    printf(
        "  \"eligibility\": {\"comparison\":\"%s\",\"factory\":",
        eligibility_matches ? "match" : "different");
    print_eligibility(&factory->eligibility);
    printf(",\"candidate\":");
    print_eligibility(&candidate->eligibility);
    printf("},\n");
    printf(
        "  \"battle_mine_options\": {\"comparison\":\"%s\",\"factory\":",
        randomize_matches ? "match" : "different");
    print_randomize(factory);
    printf(",\"candidate\":");
    print_randomize(candidate);
    printf("},\n");
    printf(
        "  \"summary\": {\"matching_categories\":%u,"
        "\"different_categories\":%u}\n",
        matching_categories, 4U - matching_categories);
    printf("}\n");
}

static void usage(const char *program) {
    fprintf(
        stderr,
        "usage: %s --config FILE --factory ROM --candidate ROM "
        "--candidate-sha256 HASH_FROM_BUILD_OUTCOME\n",
        program);
}

int main(int argc, char **argv) {
    const char *config_path = NULL;
    const char *factory_path = NULL;
    const char *candidate_path = NULL;
    const char *candidate_expected_sha256 = NULL;
    struct FixtureConfig config;
    struct RomObservation factory_runs[2];
    struct RomObservation candidate_runs[2];
    char factory_sha256[SHA256_HEX_LENGTH + 1U];
    char candidate_sha256[SHA256_HEX_LENGTH + 1U];

    for (int index = 1; index < argc; ++index) {
        const char *option = argv[index];
        if (index + 1 >= argc) {
            usage(argv[0]);
            return 2;
        }
        if (strcmp(option, "--config") == 0) {
            config_path = argv[++index];
        } else if (strcmp(option, "--factory") == 0) {
            factory_path = argv[++index];
        } else if (strcmp(option, "--candidate") == 0) {
            candidate_path = argv[++index];
        } else if (strcmp(option, "--candidate-sha256") == 0) {
            candidate_expected_sha256 = argv[++index];
        } else {
            usage(argv[0]);
            return 2;
        }
    }
    if (config_path == NULL || factory_path == NULL || candidate_path == NULL
        || candidate_expected_sha256 == NULL
        || !is_lower_hex_digest(candidate_expected_sha256)) {
        usage(argv[0]);
        return 2;
    }
    if (!load_config(config_path, &config)
        || !sha256_file(factory_path, factory_sha256)
        || !sha256_file(candidate_path, candidate_sha256)) {
        return 1;
    }
    if (strcmp(factory_sha256, config.factory_sha256) != 0) {
        fprintf(
            stderr, "Factory参照ROMのSHA-256がfixtureと一致しません: %s\n",
            factory_sha256);
        return 1;
    }
    if (strcmp(candidate_sha256, candidate_expected_sha256) != 0) {
        fprintf(
            stderr, "Factory-like候補ROMのSHA-256がfixtureと一致しません: %s\n",
            candidate_sha256);
        return 1;
    }
    for (uint32_t run = 0U; run < config.independent_runs; ++run) {
        if (!observe_rom(factory_path, &config, &factory_runs[run])
            || !observe_rom(candidate_path, &config, &candidate_runs[run])) {
            return 1;
        }
    }
    if (!complete_observation_equal(&factory_runs[0], &factory_runs[1])) {
        fprintf(stderr, "Factory参照ROMの独立2回実行が一致しません\n");
        return 1;
    }
    if (!complete_observation_equal(&candidate_runs[0], &candidate_runs[1])) {
        fprintf(stderr, "Factory-like候補ROMの独立2回実行が一致しません\n");
        return 1;
    }
    print_json(
        &config, factory_sha256, candidate_sha256,
        &factory_runs[0], &candidate_runs[0]);
    return 0;
}
