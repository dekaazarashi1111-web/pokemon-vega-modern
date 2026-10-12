/* 宣言済milestone用の読取専用observer。ROM call、書込、frame実行なし。
 * 既受入runnerには加えず、新runnerの同一frame observeへ接続する。 */
static void lv_hex(struct mCore *c, const char *name, unsigned at, unsigned size) {
    si_need(at >= 0x02000000U && at + size <= 0x02040000U, "live observation RAM bounds");
    printf(",\"%s\":\"", name);
    for (unsigned i = 0; i < size; ++i) printf("%02x", read8(c, at + i));
    printf("\"");
}
static void lv_emit(struct mCore *c, unsigned n, unsigned frame) {
    unsigned s1 = read32(c, QOL_SAVE_BLOCK1_SLOT), s2 = read32(c, QOL_SAVE_BLOCK2_SLOT);
    si_need(s1 >= 0x02000000U && s1 + 0x3D40U <= 0x02040000U &&
            s2 >= 0x02000000U && s2 + 0xF24U <= 0x02040000U, "live save pointers");
    printf("{\"live\":%u,\"frame\":%u,\"schema\":1,\"save1_pointer\":%u,\"save2_pointer\":%u", n, frame, s1, s2);
    lv_hex(c, "party", QOL_PLAYER_PARTY, 600);
    lv_hex(c, "enemy_party", QOL_ENEMY_PARTY, 600);
    lv_hex(c, "save1", s1, 0x3D40U);
    lv_hex(c, "save2", s2, 0xF24U);
    lv_hex(c, "ledger", 0x0203D000U, 2048);
    lv_hex(c, "expanded_flags", 0x0203B0E8U, 512);
    lv_hex(c, "expanded_vars", 0x0203B2E8U, 1024);
    lv_hex(c, "last_ball", 0x0203B6ECU, 2);
    lv_hex(c, "coins", 0x0203B78CU, 4);
    lv_hex(c, "objects", 0x02036D6CU, 36 * 16);
    printf(",\"battle_main\":%u,\"controller\":%u,\"execution\":%u,\"command\":%u,\"action_cursor\":%u,\"move_cursor\":%u,\"enemy_count\":%u,\"chosen_move\":%u}",
           read32(c, 0x03004FC4U), read32(c, 0x03005020U), read32(c, 0x02023B28U),
           read8(c, 0x02022B24U), read8(c, BATTLE_CORE_ACTION_SELECTION_CURSOR),
           read8(c, BATTLE_CORE_MOVE_SELECTION_CURSOR), read8(c, BATTLE_CORE_ENEMY_PARTY_COUNT),
           read16(c, BATTLE_CORE_CHOSEN_MOVES));
    printf("\n");
}
