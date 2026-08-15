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
| 次タスク | `design/tasks_next.md` | `tasks/task_graph.json`, 対応する`tasks/T*.md` |
| 入力・hash | `design/import_inventory.md` | `docs/INPUT_CONTRACT.md`, `state/source-lock.json` |
| 受領資料の評価 | `design/import_review.md` | `design/imported/README.md`, `design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/README.md` |
| 採択済み判断 | `design/decisions.md` | 根拠となる監査レポート |
| パッチ競合 | `audit_seed/PHASE_01_STATUS.md` | `audit_seed/reports/conflict_report.md`, `semantic_hotspots.md` |
| T02 exact監査 | `config/t02_audit_policy.json` | `tools/t02/`, `reports/generated/address_audit.csv`, `id_inventory.json`, `semantic_conflicts.md` |
| ビルド/ROM配置 | `docs/BUILD_PIPELINE.md` | `docs/ROM_LAYOUT_POLICY.md`, `docs/INPUT_CONTRACT.md` |
| ID統合 | `docs/ID_POLICY.md` | `manifests/*.csv`, T04/T05/T07 |
| 二地方・カントー復元 | `docs/KANTO_PORT_POLICY.md` | `design/decisions.md` D-011, `design/kanto_feasibility.md`, V2 `00_採用仕様_V2.md`, `04_カントー地方_クリア後出現・イベント詳細.md`, T02/T08/T11〜T17 |
| 育成・操作QOL | `docs/QOL_POLICY.md` | T01/T02/T05/T06/T08〜T10/T12/T15〜T18 |
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
- 初戦ループ: `tasks/USER_20260814_FIRST_BATTLE_LOOP.md`、`scripts/build_first_battle_hotfix.py`、`tools/mgba_first_battle_loop_smoke.c`、`scripts/build_battle_core.py`、stage 20/21。
- HM field能力: `tasks/USER_20260814_HM_FIELD_ACCESS.md`、`overlays/hm_field_access/`、`scripts/build_hm_field_access.py`、`tools/mgba_hm_field_access_smoke.c`、stage 21/22、`docs/QOL_POLICY.md`。
- battle rules: `tasks/USER_20260814_BATTLE_RULES.md`、`config/battle_rules.json`、`scripts/build_battle_rules.py`、`tools/mgba_battle_rules_smoke.c`、固定CFRU-JP battle source、stage 22/23、T06 hook/runtime表。
- battle UI: `tasks/USER_20260814_BATTLE_UI.md`、`config/battle_ui.json`、`overlays/battle_ui/`、`scripts/build_battle_ui.py`、`tools/mgba_battle_ui_smoke.c`、固定CFRU-JP move menu/type source、stage 23/24、T06 policy fixture。
- わざメモリー: `tasks/USER_20260814_MOVE_MEMORY.md`、`config/move_memory.json`、`overlays/move_memory/`、`scripts/build_move_memory.py`、`tools/mgba_move_memory_smoke.c`、T09 learnset、stage 24/25。
- QOL release: `tasks/USER_20260814_QOL_RELEASE.md`、`scripts/build_qol_release.py`、`scripts/build_release.py`、`docs/RELEASE_POLICY.md`、stage 20〜25 metadataと統合fixture。
- Species名6文字: `tasks/USER_20260815_SPECIES_NAME_LENGTH.md`、`scripts/build_species_surface.py`の`legacy_species_names`と40 direct consumer、`overlays/species_surface/species_runtime.{c,h}`、`generated/engine/species/species_names{,_legacy}.bin`、`manifests/species_ids.csv`、`tools/mgba_{species_runtime,battle_ui}_smoke.c`、stage 09/24以降。

## 読みすぎ・やり直し防止

- 全Markdown横断は、参照切れ・仕様矛盾・根拠監査が必要な時だけ行う。
- `design/imported/**` はタスクに必要なモジュール/CSVだけ読む。統合版Markdownは各章の複製なので通常読まない。
- 同じ入力hash・source commit・tool versionで生成済みの `reports/generated/**` は再利用する。
- `userfile/**` はGit管理外の原本/受け渡し領域。通常は `inputs/**` の安定名か `state/source-lock.json` を参照する。
