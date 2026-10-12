# PR16 受付の残高・rank数値表示

Task: `USER-20260927-RESEARCH-COUNTER`

## 完了した範囲

受付の固定文「ポイントを／かくにんします。」を、実際の残高とランクを表示する2行の会話へ接続した。
`RP 0 / ランク 1` と `RP 9999 / ランク 7` を物理キー操作と独立oracleで確認し、全18画面を視認した。
9999RPは起動前の表示境界fixtureであり、自然に稼いだRPとは主張しない。
標準listはまだ実装しておらず、現時点のUIは標準buffernumberとmsgboxによる数値会話である。

## 実装と後継ROMの境界

親は32MiB `26dac23cfdbc02c3c25e357b79dcdf3d247c10d893f54a4f6d6b1227bf5624da`。
後継は32MiB `c3971e83184613a27730eaec6490d203a2c1261c77894b711b0352f487808557`。
既存の15byte文言と132byteイベント窓だけを使用し、宣言147byte内の88byteを変更。外部差分0、完全rollback一致、新領域0、新ARM compile0。
残高getter→buffernumber slot0、rank getter→slot1を接続し、成功resultを0へ戻す。cap4、保存失敗13、その他の終了分岐は保持する。
canonical model/overlayは歴史的な親の正本として不変。数値層の正本は `scripts/pr16_research_counter_numeric.py` と `content/modernization/pr16_research_counter_numeric_recipe.json`。
次のcandidate生成では、親の受入済みrecipe列を再利用して26dac23cを復元した後、数値層を一度だけ適用する。旧モデルの固定文やP08/BP候補を後継の代用品にしない。

## 検証と失敗記録の扱い

元run36286898098 / source9ec402333e9c5c0defba6073d6f20d551086c6cbの結論はfailureのまま保持する。
同runのnative2process、厳格host compile1、host書込み拒否7方式は成功原本を再利用した。
終了後のファイル131088byteと入力Flash131072byteの全ファイル比較、および終了後ファイルを使う試験loaderが検証失敗の原因だった。
入力の不変コピーと終了後ファイルを分離し、各拒否試験の前に陽性原本が通ることを必須化した。末尾16byte付入力の拒否2件も追加。
旧negative60件の見かけのPASSは採用せず、修正後の63件をすべてPASS。無変更のevent VM試験15件だけ旧成功原本から再利用し、有効な試験は計78件。
VM試験をnative試験件数に含めない。観測barrier以降は物理keyのみ。実値、2数値buffer、展開全文、owner64byte、ledger2048byte、Bag、party、save counter、全観測点の実コアFlashが一致。
終了後ファイルのbytesは元artifactに存在せず、追加16byteの意味やdisk prefix一致を今回の証拠から推測しない。
修正後driverのprefix検査は将来用の修正であり、今回それを動かしたとは主張しない。
旧unit tracebackはcheckout絶対pathを含むためguardがcommitを止めた。旧artifactはそのまま保存し、trackedコピーだけroot表記を正規化してbefore/after hashを記録した。
今回の回復・受入でnative/guard/host compile/ARM/ROM生成を再実行した回数はすべて0。

## 画面確認

固定artifact10920589167の18 PPMを拡大して視認。2境界の数値が枠内に収まり、対象表示に欠け・文字化けなし。導入・活動案内・再訪案内と会話終了を確認した。
画像、member、hashの対応は `content/modernization/pr16_research_counter_acceptance/visual-review.json` に固定した。
全map、全活動、全ゲーム画面の無欠陥を主張するものではない。

## 次の作業・再実行禁止

受付の数値残高/rankは0RP・rank1と9999RP・rank7の2境界を限定受入済み。次はSTANDARD_LISTの選択・取消・再訪を後継candidate c3971e83へ実装し変更影響だけ検証、その後自然稼得RP→ショップ支出と通常ストーリー進行を接続する。数値2境界、物理4入口、旧稼得/BP/P08の成功部分を無変更再実行しない。

新しい標準listは「開く・選択・取消・再訪」を一つの受入単位にする。以後の自然RP支出は今回の人工9999RPとは別の根拠を必要とする。
数値の元workflowは固定source hashを持つ歴史的実測入口で、再実行しない。後継受付に変更影響がある場合だけ、新しいscope/source/inputを宣言して必要部分を検証する。
BP/Circus/P08、旧4入口の受入、旧稼得、固定再開入口、active baselineは不変。merge、draft解除、release、Issue19全完了は行わない。
checkpoint: `content/modernization/pr16_research_counter_checkpoint.json`。原本終端failureと独立受入を混同しない。受入用Actions自身の終端はGitHub側で照合する。
