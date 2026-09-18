/* 同名の旧関数だけを置換するCircus専用policy。Factory本体は変更しない。 */
static uint8_t restore_original(uint8_t reset_streak)
{
    VegaFactoryState before_factory;
    FacilityPokemon before_party[FACILITY_PARTY_SIZE];
    uint32_t before_generation;
    uint8_t before_count = FACILITY_PLAYER_PARTY_COUNT;
    uint8_t restored_count = 0u;
    if (!ledger_valid() || !gVegaModernSaveData->factory.snapshot_valid) {
        clear_session_runtime();
        return (uint8_t)CircusStreakRuntimeEnd(reset_streak == 0u);
    }
    copy_bytes(&before_factory, &gVegaModernSaveData->factory, sizeof(before_factory));
    copy_bytes(before_party, FACILITY_PLAYER_PARTY, sizeof(before_party));
    before_generation = gVegaModernSaveData->generation;
    gVegaModernSaveData->factory.reward_pending = 0u;
    if (VegaFactoryRestore(gVegaModernSaveData,
            (uint8_t (*)[VEGA_PARTY_MON_SIZE])FACILITY_PLAYER_PARTY,
            &restored_count, accept_callback, NULL) != VEGA_SAVE_OK)
        return 0u;
    FACILITY_PLAYER_PARTY_COUNT = restored_count;
    clear_session_runtime();
    if (CircusStreakRuntimeEnd(reset_streak == 0u))
        return 1u;
    /* 書込み失敗を報酬成功と表示せず、partyと台帳のbefore imageを戻す。 */
    copy_bytes(&gVegaModernSaveData->factory, &before_factory, sizeof(before_factory));
    copy_bytes(FACILITY_PLAYER_PARTY, before_party, sizeof(before_party));
    FACILITY_PLAYER_PARTY_COUNT = before_count;
    gVegaModernSaveData->generation = before_generation;
    VegaSaveFinalize(gVegaModernSaveData);
    return 0u;
}

FACILITY_EXPORT void CircusRuntime_AfterBattle(void)
{
    uint8_t before_pending;
    uint8_t outcome = (uint8_t)(FACILITY_BATTLE_OUTCOME & 0x7Fu);
    if (!ledger_valid() || !gVegaModernSaveData->factory.snapshot_valid
        || !CircusStreakRuntimeArmed()) {
        set_result(0u);
        return;
    }
    if (outcome != FACILITY_BATTLE_OUTCOME_WON) {
        if (!CircusStreakRuntimeRecord(outcome)) {
            set_result(0u);
            return;
        }
        (void)restore_original(1u);
        set_result(0u);
        return;
    }
    heal_rental_party();
    (void)cache_random_opponent();
    before_pending = gVegaModernSaveData->factory.reward_pending;
    if (before_pending < 3u)
        ++gVegaModernSaveData->factory.reward_pending;
    if (!CircusStreakRuntimeRecord(outcome)) {
        gVegaModernSaveData->factory.reward_pending = before_pending;
        VegaSaveFinalize(gVegaModernSaveData);
        set_result(0u);
        return;
    }
    set_result(gVegaModernSaveData->factory.reward_pending >= 3u ? 2u : 1u);
}

FACILITY_EXPORT void CircusRuntime_Complete(void)
{
    uint16_t before_bp;
    if (!ledger_valid() || !gVegaModernSaveData->factory.snapshot_valid
        || gVegaModernSaveData->factory.reward_pending != 3u) {
        (void)restore_original(1u);
        set_result(0u);
        return;
    }
    /* BP通貨だけを共用し、Factory初回claim bitや連勝24枠を消費しない。 */
    before_bp = gVegaModernSaveData->factory.battle_points;
    if (VegaFactoryAddBattlePoints(gVegaModernSaveData, FACILITY_REWARD_BP) != VEGA_SAVE_OK) {
        set_result(0u);
        return;
    }
    if (!restore_original(0u)) {
        gVegaModernSaveData->factory.battle_points = before_bp;
        VegaSaveFinalize(gVegaModernSaveData);
        set_result(0u);
        return;
    }
    set_result(FACILITY_REWARD_BP);
}
