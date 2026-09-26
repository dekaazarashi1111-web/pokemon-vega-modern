# PR16 虫取りの実RP稼得

PASS_BUG_REAL_EARNING_SCOPED

## 実装・限定受入

候補 `26dac23cfdbc02c3c25e357b79dcdf3d247c10d893f54a4f6d6b1227bf5624da` / 33554432 bytes。保存view修復後候補のbyte変更なし、ARM compile/link0。
実map97/0、local11、(43,6)、record0x09413854、script0x093C048Cを現ROMから同定。species39は現ROMのtype6/6（むし）、species1は12/12。全国図鑑番号から推測しない。

実NPCへ通常キーで話し、条件不足はresult3/RP0/Flash不変。むしありの取消はRP0/Flash不変、承諾で0→8RP、日内8/生涯8/claim1/取引ID2、counter2→4。直後の同日重複、独立coreの通常Continue、再度の重複はresult4/残高8/counter4/Flash不変。全party600bytes・Bag・ledger2048bytes・他owner・checksumを確認。取引自身の保存2回、手動Save0、警告0、観測barrier後host書込み0。

開始party/進行/warpはfixtureで、自然捕獲・自然到達の受入ではない。写真の旧候補や受入済みmap-view検査を再実行せず、元ROM/seed/旧証拠を保全。

## 原本と実行数

Actions run `36261672837` / source `5412cee1d3cbde3d818a17fa6bf53d1096fc6c2c`、数値returncode0を持つ2process/3fresh cores、host compile1、native失敗0。四文言と12PPMを目視し森林/花/道/人物/台詞枠・cold地形を確認。虫なし・確認・8ポイント・日内記録済みを区別。

原本 `content/modernization/pr16_research_bug_measurement.json` はartifact10912851229のmeasurement.jsonをbyte不変で保存。外側ZIP sha256 `dc637a82e536a2c3f8453b5e74c806f36e7d75e14dc05e863c7609729bdd0846`。`content/modernization/pr16_research_bug_evidence/36261672837/terminal.json` が全step成功を確認。`content/modernization/pr16_research_bug_evidence/36261672837/unit.json` は新規51テスト（全64owner byte変異/順序/欠落/型/過大主張拒否を含む）。原本照合・記録時native/compile再実行0。

60afcc67にあった旧ローカルJSON参照は未保存だった。過去の失敗1件やstdoutは復元できたと主張せず、過去件数unknownを保持。参照先を今回のActions原本へ変更し、2テストの由来期待だけを訂正。独立oracle/生成C/ROMは不変。`content/modernization/pr16_research_bug_evidence/36261672837/source-adjudication.json` に旧/新source hashを記録。

## 次工程・禁止

次は残る4活動（釣り・生態・ゲームコーナー・採掘）の実RP稼得、通常進行からResearch受付/ショップ接続、残るnative文言。保存view修復26dac23cを専用recipeで復元する。写真と虫取りの受入原本は変更影響なしに再実行しない。虫取りは実NPC/0→8RP/取消/条件不足/同日重複拒否/取引保存/独立Continue/4文言まで。開始party・進行・warpはfixtureで、自然到達・全活動・全map・releaseは未受入。

全体CIには既存P03 capacity source pin問題等があり、本限定PASSを全CI成功へ昇格しない。最新結果は固定引継ぎのobserved_head_checks。PR draft/open・未mergeを維持、release/baseline切替なし。

## 受入commit後の補助処理の終端

受入commit `5e428c2f09c14d4cf65b10c9da78d39ca47f8277` は51検査・resume/task graph・今回18path/全作業21path guard・非force pushまで成功。記録run36262152385はその直後の補助context exportだけがPR APIのHEAD不一致で失敗した。旧runはfailureとして保存し、成功へ読み替えない。次run冒頭のclean HEADでcontext exportを実行し、原本・unit receipt・全変更guardを再利用して終端同期。unit/native/compile再実行0。`content/modernization/pr16_research_bug_evidence/closeout/record-workflow-result.json` を参照。
