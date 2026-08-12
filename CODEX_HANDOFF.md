# Codex Handoff

目的は、Vega本編を保持したDPE-JP/CFRU-JP統合と、clean FireRed日本版Rev.0から新規名前空間へ復元する高難度カントーを、1本のROMに再現ビルドすることです。カントーはVega本編中盤、シオウの3個目バッジとアーシア島D・Hビル初回攻略後から任意訪問でき、トーホクと常時双方向に往復可能にします。後半認定章、カントーリーグ、最終共鳴だけはVega殿堂入り後です。Factory UPSは参照専用で、Vegaへ重ねません。

再開時は `AGENTS.md` → `design/current_state.md` → `design/agent_context_map.md` → `design/tasks_next.md` を読み、`python3 scripts/taskctl.py next` を実行してください。`RESUME`を最優先し、なければ依存READY候補から1件を選びます。`PRIMARY`は推奨、`PARALLEL_PREP`も開始可能な候補であり、toolchain待ちやfan-outを見て先に選べます。全waveは`make plan`で確認できます。タスク状態は `design/tasks_next.md`、依存は `tasks/task_graph.json`、完了条件は `tasks/T*.md` が正本です。

私有原本は `userfile/imports/`、ツール向け参照は `inputs/` にあり、どちらもGit管理外です。入力hashと上流pinは `design/import_inventory.md` / `state/source-lock.json` を参照します。

二地方のactive review資料は `design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/`、採択方針は `design/import_review.md`、初期実現性評価は `design/kanto_feasibility.md` です。V1は来歴保存専用です。カントーはVega内の残存領域を上書きせず、clean BPRJのraw資産を新規MapGroupへ複製・再接続します。

育成・操作QOLは `docs/QOL_POLICY.md` を正とし、即時文章、高速移動、現代孵化、経験アメ、育成値UI、PC一括操作までrelease scopeです。分析だけで止まらず、選択タスクの実装、最小検証、ログ、状態更新、コミットまで進め、完了時の既定verifyは重複させず1回実行します。
