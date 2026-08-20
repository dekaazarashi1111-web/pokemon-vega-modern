/* T20 exact-ROM quick/full validation for rooted event-design field paths. */
#define QOL_PRODUCTION_EMBEDDED
#include "mgba_qol_production_smoke.c"
#include "event_design_generated.h"

enum {
    ED_MAGIC = 0x45443230U,
    ED_STATE_FLAG_BASE = 0x13B0U,
    ED_CERT_FLAG_BASE = 0x1400U,
    ED_CERT_FLAG_COUNT = 13U,
    ED_TRAINER_SET_FLAG = 0x09302841U,
    ED_SCRIPT_CONTEXT_SETUP = 0x080693A5U,
    ED_RUN_SCRIPT_IMMEDIATELY = 0x08069409U,
    ED_CHECK_BAG_SPACE = 0x08099A09U,
    ED_REMOVE_BAG_ITEM = 0x08099BE1U,
    ED_VAR_8000 = 0x02036FECU,
    ED_VAR_8001 = 0x02036FEEU,
    ED_CASE_COUNT = 76U,
    ED_EVENT_PLACEMENT_COUNT = 62U,
    ED_PLACEMENT_COUNT = 63U,
    ED_BATCH_COUNT = 7U,
};

struct EventDesignSymbols {
    uint32_t probe;
    uint32_t check_unlock;
    uint32_t check_condition;
    uint32_t event_rank;
    uint32_t set_state;
    uint32_t grant_reward;
    uint32_t open_basket;
    uint32_t schedule;
    uint32_t payload_address;
    uint32_t payload_size;
    uint32_t orphan_dispatcher;
    uint32_t transition_script;
};

struct EventDesignCase {
    char event[96];
    char batch[96];
    char placement[112];
    char trigger[32];
    uint32_t dispatcher;
    uint32_t first_step;
};

static void ed_die(const char *message)
{
    fprintf(stderr, "mgba-event-design: %s\n", message);
    exit(1);
}

static unsigned ed_split(char *line, char **fields, unsigned capacity)
{
    unsigned count = 0U;
    char *cursor = line;
    while (count < capacity) {
        fields[count++] = cursor;
        char *comma = strchr(cursor, ',');
        if (!comma)
            break;
        *comma = '\0';
        cursor = comma + 1;
    }
    if (count && fields[count - 1U][0]) {
        size_t length = strlen(fields[count - 1U]);
        while (length && (fields[count - 1U][length - 1U] == '\n'
                          || fields[count - 1U][length - 1U] == '\r'))
            fields[count - 1U][--length] = '\0';
    }
    return count;
}

static bool ed_seen(char values[][112], unsigned count, const char *value)
{
    for (unsigned index = 0U; index < count; ++index) {
        if (!strcmp(values[index], value))
            return true;
    }
    return false;
}

static unsigned ed_load_cases(const char *path, struct EventDesignCase *rows,
                              unsigned capacity, unsigned *placements,
                              unsigned *batches)
{
    FILE *stream = fopen(path, "rb");
    if (!stream)
        ed_die("case fixture open failed");
    char line[1024];
    if (!fgets(line, sizeof(line), stream))
        ed_die("case fixture header missing");
    char unique_placements[ED_EVENT_PLACEMENT_COUNT][112] = {{0}};
    char unique_batches[ED_BATCH_COUNT][112] = {{0}};
    unsigned placement_count = 0U;
    unsigned batch_count = 0U;
    unsigned count = 0U;
    while (fgets(line, sizeof(line), stream)) {
        char *fields[16] = {0};
        unsigned field_count = ed_split(line, fields, ARRAY_LEN(fields));
        if (field_count != 11U || count >= capacity)
            ed_die("case fixture row/schema differs");
        struct EventDesignCase *row = &rows[count++];
        if (strlen(fields[0]) >= sizeof(row->event)
            || strlen(fields[1]) >= sizeof(row->batch)
            || strlen(fields[2]) >= sizeof(row->placement)
            || strlen(fields[4]) >= sizeof(row->trigger))
            ed_die("case fixture key too long");
        strcpy(row->event, fields[0]);
        strcpy(row->batch, fields[1]);
        strcpy(row->placement, fields[2]);
        strcpy(row->trigger, fields[4]);
        row->dispatcher = qol_number(fields[6], "dispatcher");
        row->first_step = qol_number(fields[7], "first_step");
        if (!ed_seen(unique_placements, placement_count, row->placement)) {
            if (placement_count >= ED_EVENT_PLACEMENT_COUNT)
                ed_die("too many fixture placements");
            strcpy(unique_placements[placement_count++], row->placement);
        }
        if (!ed_seen(unique_batches, batch_count, row->batch)) {
            if (batch_count >= ED_BATCH_COUNT)
                ed_die("too many fixture batches");
            strcpy(unique_batches[batch_count++], row->batch);
        }
    }
    if (fclose(stream) != 0)
        ed_die("case fixture close failed");
    *placements = placement_count;
    *batches = batch_count;
    return count;
}

static bool ed_in_payload(const struct EventDesignSymbols *symbols,
                          uint32_t address)
{
    address &= ~1U;
    return address >= symbols->payload_address
        && address < symbols->payload_address + symbols->payload_size;
}

static bool ed_fixture_contract(struct mCore *core,
                                const struct EventDesignSymbols *symbols,
                                const struct EventDesignCase *rows,
                                unsigned count, unsigned placements,
                                unsigned batches)
{
    if (count != ED_CASE_COUNT || placements != ED_EVENT_PLACEMENT_COUNT
        || batches != ED_BATCH_COUNT)
        return false;
    if (!ed_in_payload(symbols, symbols->orphan_dispatcher)
        || read8(core, symbols->orphan_dispatcher) != 0x6AU)
        return false;
    for (unsigned index = 0U; index < count; ++index) {
        uint8_t dispatcher = read8(core, rows[index].dispatcher);
        uint8_t first = read8(core, rows[index].first_step);
        if (!ed_in_payload(symbols, rows[index].dispatcher)
            || !ed_in_payload(symbols, rows[index].first_step)
            || (dispatcher != 0x6AU && dispatcher != 0x16U)
            || first == 0xFFU)
            return false;
    }
    return true;
}

static bool ed_probe_contract(struct mCore *core,
                              const struct EventDesignSymbols *symbols)
{
    static const uint32_t expected[] = {
        ED_MAGIC, 80U, 160U, 76U, 63U, 326U, 7U, 7U,
    };
    for (unsigned selector = 0U; selector < ARRAY_LEN(expected); ++selector) {
        if (call_preserving(core, symbols->probe, selector, 0, 0, 0)
            != expected[selector])
            return false;
    }
    return true;
}

static bool ed_enable_all_prerequisites(struct mCore *core)
{
    for (uint16_t flag = QOL_FLAG_BADGE_1; flag <= QOL_FLAG_BADGE_8; ++flag)
        (void)call_preserving(core, QOL_FLAG_SET, flag, 0, 0, 0);
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR, 0, 0, 0);
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_HALL_OF_FAME, 0, 0, 0);
    for (uint16_t offset = 0U; offset < ED_CERT_FLAG_COUNT; ++offset)
        (void)call_preserving(core, QOL_FLAG_SET,
                              ED_CERT_FLAG_BASE + offset, 0, 0, 0);
    for (uint16_t trainer = 751U; trainer <= 758U; ++trainer)
        (void)call_preserving(core, ED_TRAINER_SET_FLAG, trainer, 0, 0, 0);
    write8(core, QOL_LEDGER + QOL_LEDGER_KANTO_UNLOCKED, 1U);
    write8(core, QOL_LEDGER + QOL_LEDGER_KANTO_VISITED, 1U);
    write8(core, QOL_LEDGER + QOL_LEDGER_HALL_OF_FAME, 1U);
    write8(core, QOL_LEDGER + QOL_LEDGER_LEAGUE_II, 1U);
    write8(core, QOL_LEDGER + QOL_LEDGER_CERTIFICATIONS, 0xFFU);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    uint32_t save = read32(core, QOL_SAVE_BLOCK1_SLOT);
    if (save < 0x02000000U || save + QOL_DAYCARE_OFFSET + QOL_BOX_MON_SIZE
        >= 0x02040000U)
        return false;
    create_mon(core, QOL_PARTY_SCRATCH, QOL_SPECIES_PIKACHU, 20U);
    qol_copy(core, save + QOL_DAYCARE_OFFSET,
             QOL_PARTY_SCRATCH, QOL_BOX_MON_SIZE);
    write16(core, ED_VAR_8001, 1U);
    return true;
}

static bool ed_initial_and_monotonic_state(struct mCore *core,
                                           const struct EventDesignSymbols *symbols,
                                           bool full)
{
    unsigned tested = full ? EVENT_DESIGN_STATE_COUNT : 8U;
    for (unsigned index = 0U; index < EVENT_DESIGN_STATE_COUNT; ++index)
        (void)call_preserving(core, QOL_FLAG_CLEAR,
                              gEventDesignStateFlags[index], 0, 0, 0);
    if (!ed_enable_all_prerequisites(core))
        return false;
    for (unsigned index = 0U; index < tested; ++index) {
        if (call_preserving(core, QOL_FLAG_GET,
                            gEventDesignStateFlags[index], 0, 0, 0) != 0U)
            return false;
        if (call_preserving(core, symbols->set_state, index, 0, 0, 0) != 1U
            || call_preserving(core, symbols->set_state, index, 0, 0, 0) != 1U
            || call_preserving(core, QOL_FLAG_GET,
                               gEventDesignStateFlags[index], 0, 0, 0) != 1U)
            return false;
    }
    return true;
}

static void ed_remove_all(struct mCore *core, uint16_t item)
{
    for (unsigned count = 0U; count < 999U; ++count) {
        if (!call_preserving(core, QOL_CHECK_BAG_ITEM, item, 1U, 0, 0))
            return;
        (void)call_preserving(core, ED_REMOVE_BAG_ITEM, item, 1U, 0, 0);
    }
    ed_die("bag item removal did not converge");
}

static bool ed_reward_idempotence(struct mCore *core,
                                  const struct EventDesignSymbols *symbols,
                                  const struct Snapshot *base, bool full)
{
    unsigned tested = full ? EVENT_DESIGN_REWARD_COUNT : 1U;
    for (unsigned index = 0U; index < tested; ++index) {
        restore_snapshot(core, base);
        const EventDesignReward *reward = &gEventDesignRewards[index];
        uint16_t claim = gEventDesignStateFlags[reward->claim_state];
        (void)call_preserving(core, QOL_FLAG_CLEAR, claim, 0, 0, 0);
        ed_remove_all(core, reward->item);
        if (call_preserving(core, symbols->grant_reward, index, 0, 0, 0) != 1U
            || call_preserving(core, QOL_FLAG_GET, claim, 0, 0, 0) != 1U
            || call_preserving(core, QOL_CHECK_BAG_ITEM,
                               reward->item, reward->quantity, 0, 0) != 1U)
            return false;
        for (uint16_t amount = 0U; amount < reward->quantity; ++amount)
            (void)call_preserving(core, ED_REMOVE_BAG_ITEM,
                                  reward->item, 1U, 0, 0);
        if (call_preserving(core, symbols->grant_reward, index, 0, 0, 0) != 1U
            || call_preserving(core, QOL_CHECK_BAG_ITEM,
                               reward->item, 1U, 0, 0) != 0U)
            return false;
    }
    return true;
}

static bool ed_reward_capacity(struct mCore *core,
                               const struct EventDesignSymbols *symbols,
                               const struct Snapshot *base, bool full)
{
    unsigned tested = full ? EVENT_DESIGN_REWARD_COUNT : 1U;
    for (unsigned index = 0U; index < tested; ++index) {
        restore_snapshot(core, base);
        const EventDesignReward *reward = &gEventDesignRewards[index];
        uint16_t claim = gEventDesignStateFlags[reward->claim_state];
        (void)call_preserving(core, QOL_FLAG_CLEAR, claim, 0, 0, 0);
        ed_remove_all(core, reward->item);
        for (uint16_t item = 1U; item <= 998U; ++item) {
            if (item != reward->item)
                (void)call_preserving(core, QOL_ADD_BAG_ITEM, item, 1U, 0, 0);
        }
        if (call_preserving(core, ED_CHECK_BAG_SPACE,
                            reward->item, reward->quantity, 0, 0) != 0U
            || call_preserving(core, symbols->grant_reward,
                               index, 0, 0, 0) != 0U
            || call_preserving(core, QOL_FLAG_GET, claim, 0, 0, 0) != 0U
            || call_preserving(core, QOL_CHECK_BAG_ITEM,
                               reward->item, 1U, 0, 0) != 0U)
            return false;
    }
    return true;
}

static bool ed_full_progression(struct mCore *core,
                                const struct EventDesignSymbols *symbols)
{
    if (!ed_enable_all_prerequisites(core))
        return false;
    for (unsigned index = 0U; index < EVENT_DESIGN_STATE_COUNT; ++index) {
        if (call_preserving(core, symbols->set_state, index, 0, 0, 0) != 1U)
            return false;
    }
    write16(core, ED_VAR_8001, 1U);
    return true;
}

static bool ed_unlock_condition_rank(struct mCore *core,
                                     const struct EventDesignSymbols *symbols,
                                     bool full)
{
    unsigned unlocks = full ? EVENT_DESIGN_UNLOCK_COUNT : 8U;
    unsigned conditions = full ? EVENT_DESIGN_CONDITION_COUNT : 16U;
    unsigned events = full ? EVENT_DESIGN_EVENT_COUNT : 12U;
    for (unsigned index = 0U; index < unlocks; ++index) {
        if (call_preserving(core, symbols->check_unlock, index, 0, 0, 0) != 1U)
            return false;
    }
    for (unsigned index = 0U; index < conditions; ++index) {
        if (call_preserving(core, symbols->check_condition, index, 0, 0, 0) != 1U)
            return false;
    }
    for (unsigned index = 0U; index < events; ++index) {
        uint32_t rank = call_preserving(core, symbols->event_rank,
                                        index, 0, 0, 0);
        if (rank < 1U || rank > 2U)
            return false;
    }
    return true;
}

static bool ed_field_script_paths(struct mCore *core,
                                  const struct EventDesignCase *rows,
                                  unsigned count, const struct Snapshot *progressed,
                                  bool full, unsigned *executed)
{
    bool batch_seen[ED_BATCH_COUNT] = {false};
    static const char *const batch_keys[ED_BATCH_COUNT] = {
        "BATCH_KEY_PILOT_VERMILION", "BATCH_KEY_NORTHWEST_CORRIDORS",
        "BATCH_KEY_CENTRAL_NETWORK", "BATCH_KEY_SOUTHERN_ECOLOGY",
        "BATCH_KEY_POSTHOF_REOPEN", "BATCH_KEY_LEAGUE_APPROACH",
        "BATCH_KEY_FINAL_RESONANCE",
    };
    *executed = 0U;
    for (unsigned index = 0U; index < count; ++index) {
        unsigned batch = ED_BATCH_COUNT;
        for (unsigned candidate = 0U; candidate < ED_BATCH_COUNT; ++candidate) {
            if (!strcmp(rows[index].batch, batch_keys[candidate])) {
                batch = candidate;
                break;
            }
        }
        if (batch == ED_BATCH_COUNT)
            return false;
        if (!full && batch_seen[batch])
            continue;
        batch_seen[batch] = true;

        restore_snapshot(core, progressed);
        unsigned logs = log_problem_count;
        (void)call_preserving(core, ED_SCRIPT_CONTEXT_SETUP,
                              rows[index].dispatcher, 0, 0, 0);
        if (call_preserving(core, QOL_SCRIPT_CONTEXT_ENABLED, 0, 0, 0, 0) != 1U)
            return false;
        restore_snapshot(core, progressed);
        (void)call_preserving(core, ED_SCRIPT_CONTEXT_SETUP,
                              rows[index].first_step, 0, 0, 0);
        run_key_frames(core, 0U, 4U);
        uint32_t pc = (uint32_t)read_register(core, "pc");
        if (pc < 0x08000000U || pc >= 0x0A000000U
            || log_problem_count != logs)
            return false;
        ++*executed;
    }
    return *executed == (full ? ED_CASE_COUNT : ED_BATCH_COUNT);
}

static bool ed_schedule_boundary(struct mCore *core,
                                 const struct EventDesignSymbols *symbols,
                                 uint32_t dispatcher,
                                 const struct Snapshot *progressed)
{
    restore_snapshot(core, progressed);
    write16(core, ED_VAR_8000, dispatcher & 0xFFFFU);
    write16(core, ED_VAR_8001, dispatcher >> 16);
    (void)call_preserving(core, symbols->schedule, 0, 0, 0, 0);
    return call_preserving(core, QOL_SCRIPT_CONTEXT_ENABLED, 0, 0, 0, 0) == 1U;
}

static bool ed_transition_boundary(struct mCore *core,
                                   const struct EventDesignSymbols *symbols,
                                   const struct Snapshot *progressed)
{
    restore_snapshot(core, progressed);
    if (!ed_in_payload(symbols, symbols->transition_script)
        || read8(core, symbols->transition_script) != 0x16U)
        return false;
    (void)call_preserving(core, ED_RUN_SCRIPT_IMMEDIATELY,
                          symbols->transition_script, 0, 0, 0);
    return call_preserving(core, QOL_SCRIPT_CONTEXT_ENABLED, 0, 0, 0, 0) == 1U;
}

static bool ed_save_reload(struct mCore *core, bool full)
{
    unsigned tested = full ? EVENT_DESIGN_STATE_COUNT : 8U;
    if (call_preserving(core, QOL_TRY_SAVING_DATA, 0, 0, 0, 0) != 1U)
        return false;
    for (unsigned index = 0U; index < tested; ++index)
        (void)call_preserving(core, QOL_FLAG_CLEAR,
                              gEventDesignStateFlags[index], 0, 0, 0);
    if (call_preserving(core, QOL_LOAD_GAME_DATA, 0, 0, 0, 0) != 1U)
        return false;
    for (unsigned index = 0U; index < tested; ++index) {
        if (call_preserving(core, QOL_FLAG_GET,
                            gEventDesignStateFlags[index], 0, 0, 0) != 1U)
            return false;
    }
    return true;
}

int main(int argc, char **argv)
{
    if (argc != 17) {
        fprintf(stderr, "usage: %s ROM SAVE CASES quick|full 12_VALUES\n", argv[0]);
        return 2;
    }
    bool full = !strcmp(argv[4], "full");
    if (!full && strcmp(argv[4], "quick"))
        return 2;
    struct EventDesignSymbols symbols = {0};
    unsigned argument = 5U;
    symbols.probe = qol_number(argv[argument++], "probe");
    symbols.check_unlock = qol_number(argv[argument++], "check_unlock");
    symbols.check_condition = qol_number(argv[argument++], "check_condition");
    symbols.event_rank = qol_number(argv[argument++], "event_rank");
    symbols.set_state = qol_number(argv[argument++], "set_state");
    symbols.grant_reward = qol_number(argv[argument++], "grant_reward");
    symbols.open_basket = qol_number(argv[argument++], "open_basket");
    symbols.schedule = qol_number(argv[argument++], "schedule");
    symbols.payload_address = qol_number(argv[argument++], "payload_address");
    symbols.payload_size = qol_number(argv[argument++], "payload_size");
    symbols.orphan_dispatcher = qol_number(argv[argument++], "orphan_dispatcher");
    symbols.transition_script = qol_number(argv[argument++], "transition_script");
    if (argument != (unsigned)argc)
        return 2;

    struct EventDesignCase cases[ED_CASE_COUNT] = {0};
    unsigned placements = 0U;
    unsigned batches = 0U;
    unsigned case_count = ed_load_cases(argv[3], cases, ARRAY_LEN(cases),
                                        &placements, &batches);
    qol_initialize_save(argv[2]);
    struct mLogger logger = {.log = qol_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = qol_open(argv[1], argv[2]);
    qol_log_core = core;
    bool boot = qol_run_field_trace(core);
    struct Snapshot field_base = take_snapshot(core);

    bool fixture = ed_fixture_contract(core, &symbols, cases, case_count,
                                       placements, batches);
    bool probe = ed_probe_contract(core, &symbols);
    restore_snapshot(core, &field_base);
    bool monotonic = ed_initial_and_monotonic_state(core, &symbols, full);
    restore_snapshot(core, &field_base);
    bool idempotence = ed_reward_idempotence(core, &symbols, &field_base, full);
    restore_snapshot(core, &field_base);
    bool capacity = ed_reward_capacity(core, &symbols, &field_base, full);
    restore_snapshot(core, &field_base);
    bool progression = ed_full_progression(core, &symbols);
    bool gates = progression && ed_unlock_condition_rank(core, &symbols, full);
    bool basket = progression
        && call_preserving(core, symbols.open_basket, 0, 0, 0, 0) == 1U;
    struct Snapshot progressed = take_snapshot(core);
    unsigned executed = 0U;
    bool field_paths = ed_field_script_paths(core, cases, case_count,
                                             &progressed, full, &executed);
    bool schedule = ed_schedule_boundary(core, &symbols,
                                         cases[0].dispatcher, &progressed);
    bool transition = ed_transition_boundary(core, &symbols, &progressed);
    restore_snapshot(core, &progressed);
    bool save_reload = ed_save_reload(core, full);
    bool warnings = log_problem_count == 0U;
    bool passed = boot && fixture && probe && monotonic && idempotence
        && capacity && progression && gates && basket && field_paths
        && schedule && transition && save_reload && warnings;
    fprintf(stderr,
            "mgba-event-design %s: boot=%u fixture=%u probe=%u state=%u "
            "reward=%u capacity=%u progression=%u gates=%u basket=%u "
            "field=%u schedule=%u transition=%u save=%u paths=%u logs=%u\n",
            full ? "full" : "quick", boot, fixture, probe, monotonic,
            idempotence, capacity, progression, gates, basket, field_paths,
            schedule, transition, save_reload, executed, log_problem_count);
    printf("{\"schema_version\":1,\"status\":\"%s\",\"mode\":\"%s\","
           "\"checks\":{\"field_boot\":%s,\"fixture_76_63_7\":%s,"
           "\"runtime_probe\":%s,\"state_monotonic\":%s,"
           "\"reward_idempotence\":%s,\"reward_capacity_atomic\":%s,"
           "\"full_progression_setup\":%s,\"unlock_condition_rank\":%s,"
           "\"qol_service_reuse\":%s,\"field_script_engine_paths\":%s,"
           "\"map_transition_schedule\":%s,\"save_reload\":%s,"
           "\"map_transition_immediate_path\":%s,"
           "\"warnings_errors_zero\":%s},"
           "\"coverage\":{\"events\":76,\"placements\":63,\"batches\":7,"
           "\"states\":80,\"conditions\":160,\"rewards\":7,"
           "\"dialogues\":326,\"executed_field_paths\":%u},"
           "\"result_identity\":\"ED37:76:63:7:80:160:7:326\","
           "\"warnings_errors\":%u}\n",
           passed ? "PASS" : "FAIL", full ? "full" : "quick",
           boot ? "true" : "false", fixture ? "true" : "false",
           probe ? "true" : "false", monotonic ? "true" : "false",
           idempotence ? "true" : "false", capacity ? "true" : "false",
           progression ? "true" : "false", gates ? "true" : "false",
           basket ? "true" : "false", field_paths ? "true" : "false",
           schedule ? "true" : "false", save_reload ? "true" : "false",
           transition ? "true" : "false",
           warnings ? "true" : "false", executed, log_problem_count);
    qol_close(core);
    return passed ? 0 : 1;
}
