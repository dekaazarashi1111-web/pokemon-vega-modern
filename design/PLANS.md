# PLANS.md

製品・技術ロードマップの正本はルートの `MASTER_PLAN.md`、依存関係の機械可読正本は `tasks/task_graph.json`、状態正本は `design/tasks_next.md` である。このファイルは運用上の入口だけを持つ。

## 完成経路

```text
FireRed JPN Rev.0 clean
  -> Vega 2018-02-23
  -> Vega互換DPE-JP
  -> Vega互換CFRU-JP
  -> battle/species縦切り
  -> postgame Kanto縦切り
  -> 全コンテンツと回帰試験
  -> 32 MiB final ROM
  -> ROMを含まない差分パッチ
```

## 進め方

- Gate A〜EとT00〜T18は `MASTER_PLAN.md` を参照する。
- 受領した現代化コンテンツ設計は `design/imported/VEGA_CFRU_DPE_統合設計/` に保存し、`design/import_review.md` の問題を解消したデータだけ段階的に正本化する。
- カントーは統合設計パッケージに含まれないため、D-003/D-004、`docs/KANTO_PORT_POLICY.md`、T11/T13〜T16を正とする。
- 並列化は `WORKSTREAMS.md` の所有権に従い、親側の正本IN_PROGRESSは1件に保つ。
