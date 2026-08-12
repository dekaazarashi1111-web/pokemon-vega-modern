# Codex Resume Prompt

`AGENTS.md`、Git status、`design/current_state.md`、`design/tasks_next.md`、`design/decisions.md`、`design/blockers.md`、`design/run_log.md`末尾を読む。`state/task_status.json` は生成ミラーなので正本として読まない。

`python3 scripts/taskctl.py next` の `RESUME` があれば、変更がcommit済みか、acceptance gateが本当にPASSしたか、同一条件の既存成果があるかを確認し、不完全な作業を先に直す。なければ `PRIMARY` を選ぶ。`PARALLEL_PREP` を正本タスクとして先に開始しない。

完了済み分析を繰り返さず、既存report、source lock、生成manifestを再利用する。独立作業は所有権を分けて並列化し、実装、テスト、ログ、状態更新、commitまで進める。
