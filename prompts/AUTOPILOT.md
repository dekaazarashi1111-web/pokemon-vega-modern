# Codex Autopilot Prompt

変更前に `AGENTS.md`、`design/current_state.md`、`design/agent_context_map.md`、`design/tasks_next.md` を読む。`MASTER_PLAN.md` や全タスク文書は一括で読まず、context mapとREADYタスクに必要なものだけ読む。

Operate autonomously and aggressively on generated files and feature branches. The private source files are backed up; do not be timid about rebuilding or discarding generated ROMs. Never modify or commit `inputs/private`.

1. `python3 scripts/taskctl.py next` を実行し、`RESUME` があれば再開、なければ依存READY候補から最も待ち時間とfan-outを改善する1件を選ぶ。`PRIMARY` は推奨であり強制順ではない。
2. `python3 scripts/taskctl.py start <ID>` で開始し、そのタスク文書を最後まで読む。
3. 同一hash/source pin/tool versionの既存成果を先に探し、再解析を避ける。
4. 独立した調査・実装は所有ファイルを分けて並列化し、共有状態・ログ・コミットは親側で統合する。
5. 分析だけで止まらず、実装、最小縦切り、必要なreport、acceptance gateまで進める。
6. 失敗は短く記録して実用的な代替を試し、3方式で進展しなければ前提と縮小条件を再評価する。
7. 戻せる仮定は自律的に採用し、重要判断を `design/decisions.md` へ追記する。
8. 不可欠な私有入力、利用不能なtoolchain、後戻り不能な仕様分岐だけをBLOCKEDにする。
9. 反復中はタスク固有検証、完了前は標準ゲートを内包する既定verifyを1回だけ実行する。
10. `design/run_log.md` / `design/version_log.md` を更新し、taskctlで完了してコミットする。

入力原本は変更せず、Factory UPSをVegaへ直接適用しない。具体的な変更か真のblockerまで進めてから報告する。
