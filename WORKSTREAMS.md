# 並行ワークストリーム

## 基本運用

`design/tasks_next.md` の正本IN_PROGRESSは1件に保ち、その親タスク内で読み取り専用調査や所有範囲の重ならない実装を並列化します。複数の長期レーンを同時に進める必要がある場合だけ、ブランチ/worktreeへ分離します。

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

- `tests/**`
- `tools/validate/**`
- `reports/**`
- `manifests/id_ranges.csv`
- `state/**`

## 共有ファイル

`AGENTS.md`、`MASTER_PLAN.md`、`design/tasks_next.md`、`design/run_log.md`、`design/version_log.md`、`config/`、`Makefile`、`state/source-lock.json`はintegration/親担当だけが変更します。必要な変更は小さな専用コミットに分けます。

## マージ順

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
