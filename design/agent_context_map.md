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
- T04: `audit_seed/CODEX_TASK_02_MOVE_PORT.md`、`docs/ID_POLICY.md`、T04。
- T05/T06/T08〜T10: `docs/QOL_POLICY.md` と対象タスク。上流機能の実在根拠が必要ならT01/T02成果だけを追加で読む。
- T08/T11/T13: `docs/KANTO_PORT_POLICY.md`、`docs/ROM_LAYOUT_POLICY.md`、V2のカントー章、該当タスク。
- T12/T16: `docs/CONTENT_PIPELINE.md`、`design/import_review.md`、V2の二地方配置・遭遇・イベントCSV、該当タスク。
- T17/T18: `docs/TEST_STRATEGY.md`、`docs/RELEASE_POLICY.md`、該当タスク。

## 読みすぎ・やり直し防止

- 全Markdown横断は、参照切れ・仕様矛盾・根拠監査が必要な時だけ行う。
- `design/imported/**` はタスクに必要なモジュール/CSVだけ読む。統合版Markdownは各章の複製なので通常読まない。
- 同じ入力hash・source commit・tool versionで生成済みの `reports/generated/**` は再利用する。
- `userfile/**` はGit管理外の原本/受け渡し領域。通常は `inputs/**` の安定名か `state/source-lock.json` を参照する。
