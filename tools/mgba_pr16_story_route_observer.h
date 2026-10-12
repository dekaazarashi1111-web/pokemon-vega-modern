/* Read-only observation for the new route adapter. No ROM calls or writes. */
static void rv_hex(struct mCore *c, const char *name, unsigned at, unsigned size) {
    si_need((at >= 0x02000000U && at + size <= 0x02040000U) ||
            (at >= 0x03000000U && at + size <= 0x03008000U), "route observer RAM bounds");
    printf(",\"%s\":\"", name);
    for (unsigned i = 0; i < size; ++i) printf("%02x", read8(c, at + i));
    printf("\"");
}
static void rv_emit(struct mCore *c, unsigned n, unsigned frame) {
    printf("{\"route_live\":%u,\"frame\":%u,\"schema\":1,\"clock_state\":%u,\"trainer_id\":%u",
           n, frame, read8(c, 0x03000E7CU), read16(c, 0x020385E2U));
    rv_hex(c, "battle_mons", 0x02023B44U, 352);
    rv_hex(c, "party_indexes", 0x02023B2EU, 8);
    rv_hex(c, "controllers", 0x03005020U, 16);
    rv_hex(c, "battle_buffer", 0x02022B24U, 2048);
    rv_hex(c, "battle_state", 0x02023D00U, 512);
    rv_hex(c, "trainer_state", 0x0203EDC0U, 48);
    rv_hex(c, "script_contexts", 0x03000EB0U, 240);
    rv_hex(c, "research_volatile", 0x0203F0A0U, 40);
    printf("}\n");
}
