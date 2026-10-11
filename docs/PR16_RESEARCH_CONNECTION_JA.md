# PR16 研究受付・ショップ・ガイドの物理接続

固定候補26dac23c。開始位置は屋外fixtureであり、ストーリー通しの自然到達ではない。barrier後は物理キーと読取のみ。

屋外4入口の未受入計測を原本固定。独立ledger/oracleと画面レビューで受入範囲を確定し、生態ガイドの未観測文言だけ追加調査する。受付数値残高の表示欠落・自然稼得RPのショップ支出接続は未完。GAME_CORNER/旧活動/今回の成功原本を無変更再実行しない。

## 現在の証拠

source `ed1f8051c9e3ac80b3d4034553d80fe4d2172e8a` / run `36284847516`。`content/modernization/pr16_research_connection_evidence/36284847516/measurement.json` とmanifestを参照。計測のMEASUREDは正式PASSではない。受付数値表示は未実装の疑義があり、文言を見ただけで残高UIを受入しない。全RP稼得/購入/取消/Continueの旧成功は再実行していない。画像は専用Actions artifact、ROM/saveはGit管理外。

## ローカル前試行

生成前dir不足1、host compile2、guard7、native5（candidate事前拒否1、lab/fishing/game完走3、生態1は環境リセットで中断）。原本消失のため受入0。後継Actions原本で独立受入し、失敗や消失を成功へ改作しない。

## 生態ガイドの限定後続

研究室/釣り/ゲームコーナーの計測原本を再実行せず、生態ガイドの追加1件と合わせて独立oracle・画像レビューを完了する。受付の数値残高/ランク表示欠落は実装未完、自然稼得RP→ショップ支出/通常ストーリー到達は未受入。

{'measurement': 'content/modernization/pr16_research_connection_evidence/36285051878/measurement.json', 'manifest': 'content/modernization/pr16_research_connection_evidence/36285051878/manifest.json', 'source_head': '51f4ce7eae44ebb5ed6c192bf088b3ebbf030ed1', 'run_id': 36285051878, 'native_processes': 1, 'observed_complete': True, 'independent_oracle_accepted': False}
移動NPCの現在位置を旧原本で確認し、player(3,5)からlocal1(2,5)へ左を向いて通常A。NPC座標/乱数/文言の書換えなし。旧3入口を再実行しない。

## 独立受入確定

物理4入口/受付静的5文言/初期ショップ開閉/釣り・ゲーム・生態の静的ガイドは原本と独立oracleで限定受入済み。次は受付の数値残高・rank/標準listを実装し変更影響だけ検証、その後自然稼得RP→ショップ支出と通常進行の接続を実測。旧稼得/今回4入口を無変更再実行しない。

受入 `content/modernization/pr16_research_connection_acceptance.json`。新規oracle 140件PASS、全owner64byte/入力/fixture/画面/JSON型/虚偽scope昇格の拒否を含む。元33画面・12静的文言を視認しartifact/member/hash固定。今回native/compile/ARMは0。研究室は屋外→受付→ショップ初期19件/取消→屋外。釣り/ゲーム/生態は入口→案内→会話終了までで、屋外帰還は主張しない。

旧生態未観測、旧tuple事前失敗、ローカル原本消失を保持。受付の数値残高/rankは未表示のためOPEN。屋外fixture到達をストーリー通しの自然到達へ、ショップRP0表示を自然稼得RP支出へ昇格しない。
