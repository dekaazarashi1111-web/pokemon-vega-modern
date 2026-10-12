# PR16 残る研究活動の実装

未受入3活動のsource契約・前回採掘記録終端を保存済み。PR16_RESEARCH_REMAINING_JA.mdから釣り/生態/ゲームコーナーのnative経路を実装する。SOURCE_CONTRACT_READY_NATIVE_OPENはnative未受入。旧写真/虫取り/採掘を無変更再実行しない。通常進行の受付/ショップ接続・残るnative文言も未完。

source契約と検証: `content/modernization/pr16_research_remaining_evidence/36273404788/source-contract.json`。新規10検査、native/ARM/host compile 0。

釣り4RP/日24、生態10RP/日50、ゲームコーナー3RP/日18。入力/進行fixtureと実捕獲・配当を区別する。RP・結果・乱数・捕獲状態をbarrier後に注入しない。旧checkpointと候補26dac23cを保持する。
