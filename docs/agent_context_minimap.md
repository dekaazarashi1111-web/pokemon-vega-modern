# agent_context_minimap.md

## 1画面地図

- プロジェクト入口: `README.md`
- 運用ルール: `AGENTS.md`
- 現在状態: `design/current_state.md`
- 次タスク: `design/tasks_next.md`
- 依存関係: `tasks/task_graph.json`
- タスク完了条件: `tasks/T*.md`
- 全体計画: `MASTER_PLAN.md`
- 採択済み判断: `design/decisions.md`
- 入力一覧: `design/import_inventory.md`
- 受領資料レビュー: `design/import_review.md`
- 現行二地方設計: `design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/`
- カントー復元の初期実現性: `design/kanto_feasibility.md`
- カントー復元・往復ポリシー: `docs/KANTO_PORT_POLICY.md`
- 設計/成果物索引: `design/catalog.md`
- レポート索引: `design/report_lifecycle_index.md`
- 実行ログ: `design/run_log.md`
- ブロッカー: `design/blockers.md`
- ChatGPT Web操作: `tools/chatgpt_browser/README.md`
- 検証: `bash scripts/verify_wsl.sh`

最初に `python3 scripts/taskctl.py next` を実行し、`RESUME`または`PRIMARY`を選びます。全waveは`make plan`、必要な資料は`design/agent_context_map.md`から確認します。
