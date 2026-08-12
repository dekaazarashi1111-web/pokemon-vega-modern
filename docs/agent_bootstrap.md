# agent_bootstrap.md

## 起動時に読むもの

1. `README.md`
2. `AGENTS.md`
3. `design/current_state.md`
4. `design/agent_context_map.md`
5. `design/tasks_next.md`
6. READYになった `tasks/T*.md`

## 作業開始前チェック

- `git status --short` で既存差分を確認します。
- 既存のユーザー変更を勝手に戻しません。
- `python3 scripts/taskctl.py next` で `RESUME` / `PRIMARY` / `PARALLEL_PREP` を確認し、全waveは `make plan` で確認します。
- `state/task_status.json` は生成ミラーなので編集しません。

## 進め方

1. `RESUME` があれば再開し、なければ `PRIMARY` だけを `taskctl.py start` で開始します。`PARALLEL_PREP` は別worktreeまたは読取調査に限定します。
2. `design/agent_context_map.md` から必要資料だけを読みます。
3. 独立作業は所有ファイルを分けて並列化します。
4. 最小の縦切りを実装し、タスク固有テストを先に実行します。
5. `make validate guard test` と既定verifyを実行します。
6. `design/run_log.md` と `design/version_log.md` に証跡を残し、taskctlで完了してコミットします。

## 入力の扱い

- 私有原本は `userfile/imports/`、ツール向け安定名は `inputs/private/` / `inputs/reference/` です。
- 原本へ直接patchせず、build側へコピーして再生成します。
- Factory UPSはVegaへ適用せず、clean ROMから別参照を作ります。
- 同一hash/source pinの生成済み監査は再利用します。
- 二地方設計はV2をactive reviewとし、`design/import_review.md` と `design/kanto_feasibility.md` から必要範囲だけ読みます。
- V2の47カントー地点は生態上の論理単位です。全建物・階層・warpの物理map scopeはT11で再生成します。
