# PLANS.md

製品・技術ロードマップの正本はルートの `MASTER_PLAN.md`、依存関係の機械可読正本は `tasks/task_graph.json`、状態正本は `design/tasks_next.md` である。このファイルは運用上の入口だけを持つ。

## 完成経路

```text
FireRed JPN Rev.0 clean
  -> Vega 2018-02-23
  -> Vega互換DPE-JP
  -> Vega互換CFRU-JP
  -> battle/species縦切り
  -> トーホク非破壊生態overlay縦切り
  -> 早期カントー往復縦切り
  -> 全コンテンツと回帰試験
  -> 32 MiB final ROM
  -> ROMを含まない差分パッチ
```

## 進め方

- Gate A〜EとT00〜T21は `MASTER_PLAN.md` を参照する。
- 現在の推奨PRIMARY、依存READY候補、DAG由来のwaveは `make plan` で確認する。PRIMARYは強制順ではなく、待ち時間とfan-outを見て別のREADY候補を選べる。
- 二地方設計の優先参照は `design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/`。V1は来歴保存専用とし、`design/import_review.md` の問題を解消したデータだけ段階的に正本化する。
- V2のカントー設計をD-003/D-004/D-010/D-011、`docs/KANTO_PORT_POLICY.md`、T11/T13〜T16の入力に使う。殿堂入り後限定の原案はD-011の早期任意アクセスでoverrideする。ただしV2の47地点はraw map総数ではなく、マップ実体はT11の全資産inventoryを正とする。
- 並列化は `WORKSTREAMS.md` の所有権に従い、親側の正本IN_PROGRESSは1件に保つ。
- 育成・操作QOLの固定scope、既定値、解禁時期は `docs/QOL_POLICY.md` を正とし、QOL-A/QOL-Bともrelease対象にする。
- T21はStage 37と既存Mirage設計だけを入力にし、ChatGPT Pro待ちの4領域と独立してStage 38へ進める。
