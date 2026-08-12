# 並行ワークストリーム

## 基本運用

`design/tasks_next.md` の正本IN_PROGRESSは1件に保ちます。`make plan` の `PRIMARY` は推奨対象、`PARALLEL_PREP` も依存READY候補です。正本が空ならthroughputを優先してどちらを選んでもよく、正本実行中は所有ファイルが重ならない調査・実装を並列化します。短い非競合subtaskは同一worktree、長期レーンまたは競合可能性がある時だけbranch/worktreeへ分離し、担当レーンはキュー、共有ログ、共有設定を変更しません。

## ブランチ

```text
codex/lane-engine
codex/lane-maps
codex/lane-content
codex/lane-qa
codex/integration
```

必要ならGit worktreeを使います。

```bash
git worktree add ../vega-engine -b codex/lane-engine
git worktree add ../vega-maps -b codex/lane-maps
git worktree add ../vega-content -b codex/lane-content
git worktree add ../vega-qa -b codex/lane-qa
```

## 所有権

### Engine

主に編集してよい範囲:

- `src/engine/**`
- `overlays/cfru/**`
- `overlays/dpe/**`
- `tools/engine/**`
- `generated/engine/**`
- `manifests/move_ids.csv`
- `manifests/species_ids.csv`
- `manifests/ability_ids.csv`
- `manifests/item_ids.csv`

### Maps

- `src/kanto/maps/**`
- `tools/map_import/**`
- `generated/maps/**`
- `manifests/map_ids.csv`
- `manifests/kanto_maps.csv`

### Content

- `content/**`
- `manifests/*encounters.csv`
- `manifests/*trainers.csv`
- `manifests/*items.csv`
- 二地方の会話、レベル曲線、生態overlay、報酬仕様

数値IDを独断で確定せず、`*_key`を使用します。

### QA

- 横断validatorと共通fixtureを置く `tests/**`
- `tools/validate/**`
- `manifests/id_ranges.csv`

## タスク固有成果物の例外

所有権はファイル種別だけでなくタスクscopeを優先します。各タスク担当は、自タスク専用の次を編集できます。

- `tests/test_<task_scope>*.py` と専用fixture
- `reports/generated/<task_scope>/**`（Git管理外の再生成物）
- 既にタスク必須出力として明記された `config/<task_scope>*`

共有schemaや複数タスクが使うfixture/configへ昇格する変更は親が先に統合します。`state/task_status.json` はtaskctl生成ミラー、`state/source-lock.json` は親専用で、レーンから直接編集しません。

## 共有ファイル

`AGENTS.md`、`MASTER_PLAN.md`、`design/tasks_next.md`、`design/run_log.md`、`design/version_log.md`、`Makefile`、`state/task_status.json`、`state/source-lock.json`はintegration/親担当だけが変更します。`config/` は原則親担当ですが、タスク仕様が必須出力として予約した専用ファイルだけ担当レーンで作れます。必要な共有変更は小さな専用コミットに分けます。

## 推奨マージ順

1. QAのvalidator改善
2. EngineのID/header変更
3. MapsのMap ID変更
4. Contentの記号データ
5. generator出力
6. integration smoke test

## 競合回避

- 生成物を手編集しない。
- IDはmanifestが唯一のsource of truth。
- Contentレーンは数値IDを参照しない。
- MapレーンはTrainer/Species/Itemの数値IDを参照しない。
- 共通schema変更時は先にQAブランチからmergeする。
- V2は読取専用review入力とし、Contentレーンから直接編集しない。
- `PARALLEL_PREP` のコミットはlane branch内に留め、対象タスクを正本へ統合する時に親がdiffと対象testを確認する。同一base/input/tool hashで既にPASSした全検証は再実行せず、タスク完了時の既定verifyを1回だけ実行する。
