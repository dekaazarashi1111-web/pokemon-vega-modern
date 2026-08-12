// 統合版 Learnset パッチテンプレート
// 実際の MOVE_* / SPECIES_* は統合ID台帳確定後に置換する。

static const struct LevelUpMove sIntegratedLearnset_SPECIES_NAME[] =
{
    LEVEL_UP_MOVE(1,  MOVE_BASIC_1),
    LEVEL_UP_MOVE(1,  MOVE_BASIC_2),
    LEVEL_UP_MOVE(12, MOVE_RELIABLE_STAB),
    LEVEL_UP_MOVE(24, MOVE_SECONDARY_STAB_OR_UTILITY),
    LEVEL_UP_MOVE(36, MOVE_ROLE_DEFINING),
    LEVEL_UP_MOVE(48, MOVE_MAIN_STAB),
    LEVEL_UP_MOVE(60, MOVE_LATE_GAME_OR_SIGNATURE),
    LEVEL_UP_END,
};

// 監査項目
// 1. 同レベルに5技以上を詰めない
// 2. 予定野生レベルの直近4技に命中90以上STABを含める
// 3. 進化時専用技はLv0/1思い出しに登録
// 4. 高火力サブウェポンはTM/教え技へ
// 5. 戦闘専用フォームは基礎種の表を共有
