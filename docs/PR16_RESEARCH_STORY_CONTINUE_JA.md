# PR16 保存スターター以後の通常進行

## 開発checkpoint（正式Actions受入前）

保存済みstarter.srmをContinueし、序盤ライバル戦の敗北・正常復帰、研究所退出、517番道路の切れる木の拒否会話、町への帰還、東側道路map3/19へ進めた。通常Saveでcounter1→2、別coreのContinueでparty600bytes・Flash128KiB・研究ledger・位置・RP0を保持した。勝利・木の切断・研究活動施設の到達は受入していない。

候補は e1efb1009c6e6b0ec4967bf7b20562d2330bbd933f64f7f7863cdad56eb1f842 のまま。ROM変更、ARM/host compile、NewGame再生、旧受入ケースの再実行は0。旧starter原本は変更しない。

## 正本と次の限定測定

開発原本は `content/modernization/pr16_research_story_continue_development/verification.json`、閉じた入力は同directoryのcommands.txt、専用oracleは `scripts/pr16_research_story_continue.py`。実入力114区間/12012frames、通常Save1回。開発nativeは2process/core、実画面22枚を確認した。新59検査は陽性前提付きで成功。最初の入力件数誤記の検査失敗は別receiptへ保持し、失敗時の負例okを受入へ加算しない。

次はこの新しい区間だけを固定starter artifact10932059074と同一runnerからActionsで独立測定し、後継route.srmをartifactへ保存して引継ぐ。既に新しいrun/artifactが存在する場合はその原本を先に照合し、成功した入力を再実行しない。受入済みの初期化・スターター・RP稼得支出・UI・BP・P08は再実行しない。

後継Saveの予定identityは131088bytes / SHA-256 503e26cfdc8605ff79984afdcab3ffd9ce448f4557a8d1cdf64526ad15cdd65a。これは開発測定値であり、Actions artifactの確認前に正式な再開artifactと呼ばない。map3/19 (1,14)、party1、RP0、counter2。全体ストーリー・研究活動施設(map96/0外部→98/3内部)への通常到達は未完。

merge・release・active baseline変更なし。一般CIの失敗/action_requiredと歴史的全体private guardを成功へ読み替えない。ROM/save/画面/runnerは非tracked入力またはActions artifactに限る。
