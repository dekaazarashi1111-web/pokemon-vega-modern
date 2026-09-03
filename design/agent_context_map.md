# agent_context_map.md

## 最短読書順

1. `README.md`
2. `AGENTS.md`
3. `design/current_state.md`
4. `design/tasks_next.md`
5. `python3 scripts/taskctl.py next` で選んだ `tasks/T*.md`

## 目的別の入口

| 目的 | 最初に読むファイル | 必要な時だけ追加で読む |
|---|---|---|
| 全体像 | `README.md` | `MASTER_PLAN.md` |
| 高速実行順・現在の主作業 | `make plan` | `MASTER_PLAN.md`, `design/current_state.md` |
| 運用・安全・効率 | `AGENTS.md` | `WORKSTREAMS.md`, `docs/FAIL_FAST_POLICY.md` |
| 現在状態 | `design/current_state.md` | `design/run_log.md`末尾 |
| 現在遊ぶROM、Codex対戦、アイテム送付、バグ修正 | `design/active_play_baseline.md` | `docs/CODEX_BATTLE_OPERATOR_JA.md`, `docs/WINDOWS_BATTLE_CATALOG_JA.md`, `docs/WINDOWS_BOX14_VAULT_JA.md`, `docs/IPAD_RETROARCH_MGBA_SAVE_PLACEMENT.md` |
| 次タスク | `design/tasks_next.md` | `tasks/task_graph.json`, 対応する`tasks/T*.md` |
| 入力・hash | `design/import_inventory.md` | `docs/INPUT_CONTRACT.md`, `state/source-lock.json` |
| 受領資料の評価 | `design/import_review.md` | `design/imported/README.md`, `design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/README.md` |
| 採択済み判断 | `design/decisions.md` | 根拠となる監査レポート |
| パッチ競合 | `audit_seed/PHASE_01_STATUS.md` | `audit_seed/reports/conflict_report.md`, `semantic_hotspots.md` |
| T02 exact監査 | `config/t02_audit_policy.json` | `tools/t02/`, `reports/generated/address_audit.csv`, `id_inventory.json`, `semantic_conflicts.md` |
| ビルド/ROM配置 | `docs/BUILD_PIPELINE.md` | `docs/ROM_LAYOUT_POLICY.md`, `docs/INPUT_CONTRACT.md` |
| iPad RetroArch/mGBA save配置 | `docs/IPAD_RETROARCH_MGBA_SAVE_PLACEMENT.md` | `config/test_ready_save.json`、`scripts/build_test_ready_save.py`、有効な`retroarch.cfg`、実機mGBA save directory、対象ROM basename |
| Stage53 world runtime再調査 | `docs/HANDOFF_STAGE53_WORLD_RUNTIME_REOPEN.md` | `tasks/USER_20260824_STAGE51_WORLD_RUNTIME_E2E_REPAIR.md`、原作Vega参照ROM、map/wild inventory |
| ChatGPT Pro 全収集・供給設計 | `docs/CHATGPT_PRO_COLLECTION_SUPPLY_PACKET_JA.md` | `scripts/build_chatgpt_pro_collection_supply_packet.py`、取得／Item／Raid manifest、Stage53 handoff |
| ID統合 | `docs/ID_POLICY.md` | `manifests/*.csv`, T04/T05/T07 |
| 二地方・カントー復元 | `docs/KANTO_PORT_POLICY.md` | `design/decisions.md` D-011, `design/kanto_feasibility.md`, V2 `00_採用仕様_V2.md`, `04_カントー地方_クリア後出現・イベント詳細.md`, T02/T08/T11〜T17/T20/T21 |
| 育成・操作QOL | `docs/QOL_POLICY.md` | T01/T02/T05/T06/T08〜T10/T12/T15〜T25 |
| 実装可能イベント統合 | `tasks/T20_EVENT_DESIGN_IMPLEMENTATION.md` | 受領ZIP、`templates/event_authoring_packet/**`、Stage 36 ROM/metadata、map rooted graph、T19 service ABI |
| Mirage production接続 | `tasks/T21_MIRAGE_PRODUCTION_RUNTIME.md` | Stage 37 ROM/metadata、map `31/1` rooted graph、`manifests/facility_*`のMirage行、T02/T06/T08/T10/T16/T17成果 |
| Move Distribution V4統合 | `tasks/T22_MOVE_DISTRIBUTION_V4_IMPLEMENTATION.md` | 返却ZIP、Stage 38 ROM/metadata、T04/T07/T09/T17、わざメモリー・野生生成consumer |
| Research Economy V1統合 | `tasks/T23_RESEARCH_ECONOMY_V1_IMPLEMENTATION.md` | 返却ZIP、T22 Stage 39、現行save/currency/activity/map graph |
| Reward Encounters V2統合 | `tasks/T24_REWARD_ENCOUNTERS_V2_IMPLEMENTATION.md` | 返却ZIP、T23 Stage 40、捕獲・BP・research・Factory transaction |
| Factory High Modes V2統合 | `tasks/T25_FACTORY_HIGH_MODES_V2_IMPLEMENTATION.md` | 返却ZIP、T24 Stage 41、既存Factory Trial/save/UI/battle/reward runtime |
| Codex対戦bridge | `tasks/T26_CODEX_BATTLE_BRIDGE.md` | `design/codex_battle_architecture.md`、Stage 42、RetroArch NCI、mGBA memory map、`ipad-wifi-ssh` |
| Codex 6→3対戦 | `tasks/T27_CODEX_BATTLE_RUNTIME.md` | T26 Stage 43/protocol/CLI、canonical catalog/learnset、party selection、battle controller、CFRU gimmick、privacy、Factory/Mirage cleanup |
| Codex任意報酬・iPad完走 | `tasks/T28_CODEX_BATTLE_REWARDS_RELEASE.md` | T27 Stage 44、Acquisition/T24/T25 transaction、save layout、Codex companion skill |
| Windows対戦カタログ | `tasks/T29_WINDOWS_BATTLE_CATALOG.md` | T28 Stage 45/protocol/symbols、canonical catalog、T19 PC複数選択・一括逃がし、Windows CLI |
| Windows Box 14固有個体庫 | `tasks/T30_WINDOWS_BOX14_VAULT.md` | T29 Stage 46/protocol/symbols、BoxPokemon ABI、T19 PC/save transaction、Windows owner-only storage |
| Speciesフォーム・背面画像互換 | `tasks/USER_20260823_SPECIES_FORM_BACKSPRITE_COMPAT.md` | `tools/engine/cfru_canonical_ids.py`、Stage06/09、Stage48 builder/report、canonical manifests、mGBAフォーム回帰 |
| Trainer AI・難易度 | `design/decisions.md` D-015 | 固定CFRU-JP `src/Battle_AI/**`, V2 `06_出現率・トレーナー・報酬バランス.md`, T01/T02/T06/T10/T12/T15〜T18 |
| テスト | `docs/TEST_STRATEGY.md` | 選択タスクのacceptance gate |
| レポート状態 | `design/report_lifecycle_index.md` | `reports/`, `reports/generated/` |
| ブロッカー | `design/blockers.md` | 選択タスクの失敗ログ |
| ChatGPT Web | `tools/chatgpt_browser/README.md` | 必要時のみ |

## タスク別の最小セット

- T00: `docs/INPUT_CONTRACT.md`、`config/project.toml`、`design/import_inventory.md`。
- T01: `docs/SOURCE_NOTES.md`、上流README、T01。
- T02: `config/t02_audit_policy.json`、`tools/t02/`、`reports/generated/{address_audit.csv,id_inventory.json,semantic_conflicts.md}`。初期資料が必要な時だけ `audit_seed/CODEX_TASK_01.md` を読む。
- T03: `scripts/build_project.py`、`config/{rom_regions.csv,harness_smoke.json}`、`overlays/vega_adapter/`。配置方針は `docs/ROM_LAYOUT_POLICY.md`、再生成結果は `reports/generated/harness_smoke.md`。
- T04: `config/move_port.json`、`scripts/build_move_{port,stage}.py`、`tools/engine/{extract_vega_moves,cfru_move_inventory}.py`、`manifests/move_ids.csv`、`reports/generated/move_port.md`。V3原本は必要なCSVだけ読む。
- T05: `config/id_spaces.json`、`scripts/build_id_spaces.py`、`tools/engine/{extract_vega_id_spaces,cfru_id_space_inventory}.py`、`manifests/{type,ability,item}_ids.csv`、`reports/generated/id_space_report.md`。育成道具の意味契約は`docs/QOL_POLICY.md`を読む。
- T06: `config/battle_core.json`、`scripts/build_battle_core.py`、`overlays/cfru/`、`tools/engine/cfru_*`、`tools/mgba_battle_{core,core_ai,policy}_smoke.c`、`reports/generated/{battle_core,facility_core,trainer_ai}_smoke.md`。育成境界は`docs/QOL_POLICY.md`、上流根拠はT01/T02成果だけを追加で読む。
- T07: `config/species_port.json`、`scripts/build_species_port.py`、`tools/engine/extract_vega_species.py`、`manifests/species_ids.csv`、`reports/generated/species_port.md`。ID原則は`docs/ID_POLICY.md`、T05 canonical Ability/ItemとT06 BaseStats stageを入力にする。
- T08〜T10: `docs/QOL_POLICY.md` と対象タスク。上流機能の実在根拠が必要ならT01/T02成果だけを追加で読む。
- T09: `config/species_surface.json`、`scripts/build_species_surface.py`、`generated/engine/{species_assets,evolutions,learnsets}/`、`overlays/species_surface/`、`reports/generated/{dex_policy,species_asset_validation}.md`。T04/T05/T06/T07/T08のID・進化・save ABIを入力にする。
- T10: `config/{feature_matrix.csv,engine_manifest_schema.json}`、`scripts/build_engine_vertical_slice.py`、`overlays/engine_slice/`、`tests/fixtures/{engine_slice,qol_slice,factory_trial,reward_encounter,trainer_ai_slice,research_encounter_slice,raid_slice}.json`。
- T08/T11/T13: `docs/KANTO_PORT_POLICY.md`、`docs/ROM_LAYOUT_POLICY.md`、V2のカントー章、該当タスク。
- T12/T16: `docs/CONTENT_PIPELINE.md`、`design/import_review.md`、V2の二地方配置・遭遇・イベントCSV、該当タスク。
- T17/T18: `docs/TEST_STRATEGY.md`、`docs/RELEASE_POLICY.md`、該当タスク。
- T19: `tasks/T19_QOL_PRODUCTION_COMPLETION.md`、`docs/QOL_POLICY.md`、`content/qol_progression.csv`、`config/{feature_matrix.csv,qol_b.json}`、`overlays/qol_b/`、Stage 35 ROM／metadata。イベント設計は`templates/event_authoring_packet/**`を参照だけにし、編集しない。
- T20: `tasks/T20_EVENT_DESIGN_IMPLEMENTATION.md`、`userfile/imports/Pokemon-Vega_EVENT-DESIGN_IMPLEMENTATION-READY.zip`、`templates/event_authoring_packet/**`、`config/qol_production_bindings.csv`、`overlays/qol_production/service_abi.md`、Stage 36 ROM/metadata、現行map/trainer/acquisition/save graph。ZIP原本は読取専用とし、Stage 35 catalogの物理値はStage 36で再監査する。
- T21: `tasks/T21_MIRAGE_PRODUCTION_RUNTIME.md`、Stage 37 ROM/metadata、`config/t02_audit_policy.json`のMirage契約、`manifests/{facility_modes,facility_trainers,facility_rentals,facility_rewards,trainer_ids}.csv`のMirage行、`overlays/{cfru,save_migration}/`、map `31/1` rooted graph。完了済みStage 38を後続baselineにする。
- T22: `tasks/T22_MOVE_DISTRIBUTION_V4_IMPLEMENTATION.md`、`userfile/imports/Pokemon-Vega_MOVE-DISTRIBUTION-V4_IMPLEMENTATION-READY.zip`、Stage 38 ROM/metadata、`manifests/{species,move}_ids.csv`、T09 learnset/form、わざメモリー、預かり屋、TM/tutor、野生生成consumer。ZIPは読取専用、物理値はStage 38で再監査する。
- T23: `tasks/T23_RESEARCH_ECONOMY_V1_IMPLEMENTATION.md`、`userfile/imports/Pokemon-Vega_RESEARCH-ECONOMY-V1_IMPLEMENTATION-READY.zip`、T22 Stage 39 ROM/metadata、`config/save_layout.csv`、currency/activity hook、map rooted graph。T21 Mirage、Factory、既存Research encounterのsave ownerを再監査する。
- T24: `tasks/T24_REWARD_ENCOUNTERS_V2_IMPLEMENTATION.md`、`userfile/imports/Pokemon-Vega_REWARD-ENCOUNTERS-V2_IMPLEMENTATION-READY.zip`、T23 Stage 40 ROM/metadata、capture transaction、BP/credit、Research/Factory source、Vermilion host graph。pending同一個体をsave前提で検査する。
- T25: `tasks/T25_FACTORY_HIGH_MODES_V2_IMPLEMENTATION.md`、`userfile/imports/Pokemon-Vega_FACTORY-HIGH-MODES-V2_IMPLEMENTATION-READY.zip`、T24 Stage 41 ROM/metadata、`overlays/facility_runtime/`、Factory Trial save/UI/battle/reward、T24 credit hook、T21 Mirage isolation。既存Trialをbehavior oracleにする。
- T26: `tasks/T26_CODEX_BATTLE_BRIDGE.md`、`design/codex_battle_architecture.md`、Stage 42 ROM/metadata、`config/ram_layout.csv`、RetroArch NCI公式仕様、mGBA libretro memory map、`ipad-wifi-ssh`。端末固有IP/path/credentialをtracked文書へ書かず、実iPad read/writeを必須にする。
- T27: `tasks/T27_CODEX_BATTLE_RUNTIME.md`、T26 Stage 43/protocol/CLI、T06 battle controller/AI/gimmick、T08 save/RAM、標準party selection、T21/T25 party exact restore、battle UI/rules、`manifests/{species,move,item,ability}_ids.csv`、T09/T22 learnset。`UPSTREAM_OPEN`はCodex active時だけとし、pending player commandをhostへ公開しない。報酬transactionはT28まで実装しない。
- T28: `tasks/T28_CODEX_BATTLE_REWARDS_RELEASE.md`、T27 Stage 44/protocol/CLI、Acquisition runtime、T24/T25 reward/save transaction、`config/save_layout.csv`、party/box/bag、Codex companion skill。専用iPad ROM/save copyでE2Eする。
- T29: `tasks/T29_WINDOWS_BATTLE_CATALOG.md`、T28 Stage 45/protocol/symbols、`content/codex_battle/catalog.json`、T19 PSS複数選択・一括逃がし、`tools/vega_codex_battle.py`。箱数/save ABIは拡張せず、NPC前IDLEの通常生成とhost batchだけを接続する。
- T30: `tasks/T30_WINDOWS_BOX14_VAULT.md`、T29 Stage 46/protocol/symbols、BoxPokemon 80-byte ABI、Box 14 storage root、T19 PC一括処理／save rollback、`tools/vega_codex_battle.py`。Box 14だけを搬送箱とし、hostは宣言済みtransfer span以外のsave／party／boxを直接編集しない。
- 初戦ループ: `tasks/USER_20260814_FIRST_BATTLE_LOOP.md`、`scripts/build_first_battle_hotfix.py`、`tools/mgba_first_battle_loop_smoke.c`、`scripts/build_battle_core.py`、stage 20/21。
- HM field能力: `tasks/USER_20260814_HM_FIELD_ACCESS.md`、`overlays/hm_field_access/`、`scripts/build_hm_field_access.py`、`tools/mgba_hm_field_access_smoke.c`、stage 21/22、`docs/QOL_POLICY.md`。
- battle rules: `tasks/USER_20260814_BATTLE_RULES.md`、`config/battle_rules.json`、`scripts/build_battle_rules.py`、`tools/mgba_battle_rules_smoke.c`、固定CFRU-JP battle source、stage 22/23、T06 hook/runtime表。
- battle UI: `tasks/USER_20260814_BATTLE_UI.md`、`config/battle_ui.json`、`overlays/battle_ui/`、`scripts/build_battle_ui.py`、`tools/mgba_battle_ui_smoke.c`、固定CFRU-JP move menu/type source、stage 23/24、T06 policy fixture。
- わざメモリー: `tasks/USER_20260814_MOVE_MEMORY.md`、`config/move_memory.json`、`overlays/move_memory/`、`scripts/build_move_memory.py`、`tools/mgba_move_memory_smoke.c`、T09 learnset、stage 24/25。
- QOL release: `tasks/USER_20260814_QOL_RELEASE.md`、`scripts/build_qol_release.py`、`scripts/build_release.py`、`docs/RELEASE_POLICY.md`、stage 20〜25 metadataと統合fixture。
- Species名6文字: `tasks/USER_20260815_SPECIES_NAME_LENGTH.md`、`scripts/build_species_surface.py`の`compatibility_species_names`と40 direct consumer、`overlays/species_surface/species_runtime.{c,h}`、`generated/engine/species/species_names{,_legacy}.bin`、`manifests/species_ids.csv`、`tools/mgba_{species_runtime,battle_ui}_smoke.c`、stage 09/24以降。
- Species依存form／back sprite: `tasks/USER_20260823_SPECIES_FORM_BACKSPRITE_COMPAT.md`、`tools/engine/cfru_canonical_ids.py`、`scripts/build_species_form_compat.py`、`tools/mgba_species_form_compat_smoke.c`、`reports/generated/species_form_backsprite_compat.{json,md}`、Stage 06/09/48、`manifests/{species,ability}_ids.csv`。vendorは参照専用で、全C/ASM consumerのfail-closed監査と実ROMフォーム／64×64背面回帰をproject側で維持する。
- ChatGPT Pro全収集・供給設計: `docs/CHATGPT_PRO_COLLECTION_SUPPLY_PACKET_JA.md`、`scripts/build_chatgpt_pro_collection_supply_packet.py`、`templates/chatgpt_pro_design_packets/tools/validate_submission.py`、`vendor/vega_acquisition/content/{collectible_species_registry,species_acquisition_routes}.csv`、`manifests/{species_ids,item_ids,raid_encounters}.csv`、`reports/generated/world_runtime_owner_ledger.json`。Proは物理IDを確定せず、Stage53修正後にCodexが束縛する。

## 読みすぎ・やり直し防止

- 全Markdown横断は、参照切れ・仕様矛盾・根拠監査が必要な時だけ行う。
- `design/imported/**` はタスクに必要なモジュール/CSVだけ読む。統合版Markdownは各章の複製なので通常読まない。
- 同じ入力hash・source commit・tool versionで生成済みの `reports/generated/**` は再利用する。
- `userfile/**` はGit管理外の原本/受け渡し領域。通常は `inputs/**` の安定名か `state/source-lock.json` を参照する。
