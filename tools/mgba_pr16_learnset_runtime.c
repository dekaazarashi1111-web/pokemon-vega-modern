/* New two-entrypoint ROM gate. Host fixture/direct-call scope, NOT gameplay E2E. */
#define BATTLE_CORE_EMBEDDED
#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1
#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203D000U
#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203E000U
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#include "mgba_battle_core_smoke.c"
#pragma GCC diagnostic pop
#include "pr16_learnset_samples.h"

static uint32_t call_new(struct mCore *core, uint32_t function, uint32_t arg0, uint32_t arg1)
{
    struct CpuState original = capture_cpu_state(core);
    struct HostCallStack stack;
    uint32_t instructions = 0;
    bool seen = false;
    begin_host_call_stack(core, &stack, NULL, 0U);
    write_register(core, "cpsr", (uint32_t)original.registers[16] | 0xA0U);
    write_register(core, "lr", 0x08000001U);
    write_register(core, "r0", arg0);
    write_register(core, "r1", arg1);
    write_register(core, "r2", 0U);
    write_register(core, "r3", 0U);
    write_register(core, "pc", function);
    while (((uint32_t)read_register(core,"pc") & ~1U) != 0x08000002U) {
        uint32_t pc = (uint32_t)read_register(core,"pc") & ~1U;
        if (pc >= PR16_CODE_START && pc < PR16_CODE_END) seen = true;
        if (++instructions > BATTLE_CORE_DIRECT_CALL_LIMIT) battle_core_die("new call timeout");
        core->step(core);
    }
    uint32_t result = (uint32_t)read_register(core,"r0");
    bool okay = restore_host_call_stack(core,&stack);
    restore_cpu_state(core,&original);
    if (!okay || !seen) battle_core_die("new code PC/stack gate failed");
    return result;
}

int main(int argc, char **argv)
{
    if (argc != 3) return 2;
    char sha[65]; sha256_file(argv[1],sha);
    if (strcmp(sha,argv[2])) battle_core_die("candidate SHA mismatch");
    struct mLogger logger = {.log=quiet_log,.filter=NULL}; mLogSetDefaultLogger(&logger);
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core) || !mCoreLoadFile(core,argv[1])) battle_core_die("core load failed");
    mCoreInitConfig(core,NULL);
    mCoreConfigSetDefaultValue(&core->config,"idleOptimization","ignore");
    core->reset(core);
    const uint32_t scratch=0x0203C000U;
    unsigned calls=0;
    for (unsigned n=0; n<sizeof(pr16_samples)/sizeof(pr16_samples[0]); ++n) {
        const struct Pr16Sample *s=&pr16_samples[n];
        /* Host fixture only: zero personality/OT gives a valid empty checksum.
         * The ROM setter fills species and four nontrivial move/PP fields.
         * No natural creation/Save/Continue acceptance is claimed here. */
        for (unsigned b=0;b<POKEMON_SIZE;++b) write8(core,ADDR_PLAYER_PARTY+b,0U);
        write16(core,scratch,s->species);
        (void)call_bounded(core,ROM_SET_MON_DATA,ADDR_PLAYER_PARTY,11U,scratch,0U);
        for (unsigned i=0;i<4U;++i) {
            const uint16_t moves[4]={33U,45U,85U,182U};
            const uint16_t pp[4]={17U,21U,5U,7U};
            write16(core,scratch,moves[i]);
            (void)call_bounded(core,ROM_SET_MON_DATA,ADDR_PLAYER_PARTY,13U+i,scratch,0U);
            write16(core,scratch,pp[i]);
            (void)call_bounded(core,ROM_SET_MON_DATA,ADDR_PLAYER_PARTY,17U+i,scratch,0U);
        }
        write16(core,scratch,0x39U);
        (void)call_bounded(core,ROM_SET_MON_DATA,ADDR_PLAYER_PARTY,21U,scratch,0U);
        if (call_bounded(core,ROM_GET_MON_DATA,ADDR_PLAYER_PARTY,65U,0U,0U).result!=s->species)
            battle_core_die("fixture species2 readback failed");
        uint8_t mon[POKEMON_SIZE];
        for (unsigned b=0;b<POKEMON_SIZE;++b) mon[b]=read8(core,ADDR_PLAYER_PARTY+b);
        for (unsigned i=0;i<42U;++i) write16(core,scratch+2U*i,0xDEADU);
        uint32_t count=call_new(core,0x091142A1U,s->species,scratch); ++calls;
        if (count!=s->count) battle_core_die("new level count mismatch");
        for (unsigned i=0;i<42U;++i)
            if (read16(core,scratch+2U*i)!=(i<count?s->moves[i]:0xDEADU)) battle_core_die("level output/canary mismatch");
        for (unsigned slot=0;slot<129U;++slot) {
            uint32_t expected=slot<128U?((s->bits[slot/8U]>>(slot%8U))&1U):0U;
            if (call_new(core,0x09110185U,ADDR_PLAYER_PARTY,slot)!=expected) battle_core_die("new machine bit mismatch");
            ++calls;
        }
        for (unsigned b=0;b<POKEMON_SIZE;++b)
            if (read8(core,ADDR_PLAYER_PARTY+b)!=mon[b]) battle_core_die("existing mon modified");
    }
    /* Unknown species must return without touching the output. */
    for (unsigned i=0;i<42U;++i) write16(core,scratch+2U*i,0xDEADU);
    if (call_new(core,0x091142A1U,1671U,scratch)) battle_core_die("invalid species accepted");
    ++calls;
    for (unsigned i=0;i<42U;++i)
        if (read16(core,scratch+2U*i)!=0xDEADU) battle_core_die("invalid species wrote output");
    if (log_problem_count) battle_core_die("mGBA warning/error");
    printf("{\"status\":\"PASS_TWO_LINKED_ROM_ENTRYPOINTS\",\"candidate_sha256\":\"%s\",\"samples\":%zu,\"calls\":%u,\"new_code_pc_seen_for_every_call\":true,\"existing_mon_bytes_unchanged\":true,\"output_canaries_unchanged\":true,\"scope\":\"HOST_FIXTURE_DIRECT_ROM_CALL_NOT_GAMEPLAY_E2E\"}\n",sha,sizeof(pr16_samples)/sizeof(pr16_samples[0]),calls);
    mCoreConfigDeinit(&core->config); core->deinit(core); free(core);
    return 0;
}
