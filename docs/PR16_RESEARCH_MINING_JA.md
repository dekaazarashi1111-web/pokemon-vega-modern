# PR16 採掘の実RP稼得

PASS_MINING_REAL_EARNING_SCOPED / USER-20260927-RESEARCH-MINING

## 実装・限定受入

候補 `26dac23cfdbc02c3c25e357b79dcdf3d247c10d893f54a4f6d6b1227bf5624da` / 33554432bytesは不変。標準いわくだきのfield effect37→岩除去→実FieldMiningを物理Aで通す。map97/82、local12、(1,20)、event0x09413B40、record0x0941397C、script0x093C050C。現在のobject template数17とlive対象岩1を区別する。

バッジ不足・技不足・取消ではRP0/Flash不変。承諾で0→10RP、生涯10/日内mining10/claim2/取引ID2、保存counter2→4。取引自身の保存2回、手動Save0。全party600bytes・Bag・台帳2048bytes・他owner・checksumを検査。独立coreの通常Continueで残高10と全不変量を保持する。

岩消去は同mapのContinueでも保持される。日次上限は3番目のcoreの開始fixtureで隣接階97/81へstock warpして戻し、再度実岩を調べresult4/RP10/counter4/Flash不変を確認。自然な階往復とは区別する。報酬と上限文言で入力を止め、RockSmashWildEncounterの自然終端は未受入。初期party/技/バッジ/進行/warpもfixture。barrier後host書込み0、RP/resultの注入0。

## 原本・実行数・失敗履歴

Actions `36267515706` / source `8fdda1bb5e4f559cf71120f17e7fc947116e8f69` は全step成功。新規3process/5fresh cores、host compile1、ARM0、ROM変更0、失敗0。新規64unit成功（64owner byte変異、全行欠落/追加、型・順序・不変量・過大主張拒否を含む）。11PPMの完全hashが目視済み四文言に一致。記録時unit/native/compile再実行0。

原本 `content/modernization/pr16_research_mining_measurement.json` はartifact10914865008のmeasurement.jsonをbyte不変保存。外側ZIP `4c8ef9850fec610641944b1b76f7673edee49169e00dbe75623989bca9381719`。`content/modernization/pr16_research_mining_evidence/36267515706/terminal.json`、unit/visual/reconciliation/manifestを照合する。

ローカル開発は8process/成功3/失敗5。旧configの件数誤仮定1、CPU非保存のsetup1、過剰Aでwild tailへ進みparty変化2、Continue後の岩消去保持1を失敗として保存。途中失敗のstderr原文・stdout/source/measurement identity・compile/preflight履歴は `content/modernization/pr16_research_mining_local_development.json`。途中stdout全文はcontainer原本でありGitに全文保存したとは主張しない。正式原本は上記Actions。成功に読み替えない。

## 次工程

次は残る3活動（釣り・生態・ゲームコーナー）の実RP稼得、通常進行からResearch受付/ショップ接続、残るnative文言。修復候補26dac23cを専用recipeで復元し、写真/虫取り/採掘の受入済みケースは変更影響なしに再実行しない。採掘は標準いわくだきから0→10RP、条件不足/取消、取引保存2、独立Continue、別coreの階往復fixture後の日次上限、4文言まで。初期party/技/バッジ/進行/warpとcap再入場はfixture。RockSmashWildEncounterの自然終端・自然到達/再到達・全活動/全map/通常接続・releaseは未受入。

既存P03 capacity source pin等の一般CI失敗は限定PASSと分離する。最新照合は `content/modernization/pr16_research_mining_evidence/36267515706/checks.json`。PR draft/open・未merge、release/baseline切替なし。記録workflow自身の終端はrecord_run_idから確認し、自己実行中をsuccessにしない。
