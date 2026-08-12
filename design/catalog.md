# catalog.md

## Project Docs

- `README.md`: プロジェクト入口
- `AGENTS.md`: エージェント運用規約
- `design/current_state.md`: 現在状態の要約
- `design/agent_context_map.md`: 読む順番の短縮地図
- `design/tasks_next.md`: 唯一のタスク状態正本
- `tasks/task_graph.json`: T00〜T18の依存関係正本
- `tasks/T*.md`: タスクごとの目的、成果物、完了条件
- `MASTER_PLAN.md`: 製品・技術ロードマップ
- `design/PLANS.md`: 運用計画索引
- `design/decisions.md`: 採択済みADR（追記のみ）
- `design/import_inventory.md`: 受領入力、hash、配置、上流pin
- `design/import_review.md`: 受領パッケージの採否と既知課題
- `design/run_log.md`: 実行ログ
- `design/version_log.md`: バージョン履歴
- `design/blockers.md`: ブロッカー記録
- `design/feature_ideas.md`: 将来案、気づき
- `design/report_lifecycle_index.md`: レポート類の状態管理

## Scripts

- `scripts/verify_wsl.sh`: WSL/Linux向け既定検証
- `scripts/verify_linux.sh`: native Linux向け検証
- `scripts/verify_windows.ps1`: Windows向け検証
- `scripts/bootstrap_project.py`: 私有入力検証、上流取得、source lock生成
- `scripts/preflight.py`: 入力とtoolchainの事前検査
- `scripts/run_baseline_audit.py`: cleanからの参照ROMと厳密競合監査
- `scripts/taskctl.py`: `design/tasks_next.md` の安全な状態操作
- `scripts/guard_private_files.py`: 私有バイナリのGit混入防止
- `scripts/verify_imported_packages.py`: 受領した監査/設計資料の整合性検査

## Imported Evidence

- `audit_seed/`: 受領した単体競合監査パッケージの正本
- `design/imported/VEGA_CFRU_DPE_統合設計/`: 受領時点を保つreview資料
- `reports/generated/`: 再実行可能なローカル監査結果（Git管理外）
- `userfile/imports/`: ROM、patch、元ZIP、展開バックアップ（Git管理外）

## Playbook

- `CODEX_START_HERE.md`: bootstrapと再開手順
- `CODEX_HANDOFF.md`: 短い受け渡し説明
- `WORKSTREAMS.md`: 並列レーンと所有権
- `docs/`: 入力、ID、ROM配置、Kanto、test、release方針
- `manifests/`: IDとコンテンツの機械可読正本候補
- `state/source-lock.json`: 入力hashと上流commitの固定記録

## Tools

- `tools/chatgpt_browser/README.md`: ChatGPT Web ブリッジ操作手順
- `audit_seed/tools/`: patch解析、参照ROM生成、source address監査
