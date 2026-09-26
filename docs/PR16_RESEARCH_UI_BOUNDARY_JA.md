# PR16 新規ゲーム初期化・取引UIのC host境界

正本Cの新規ゲーム初期化と取引UI callbackの限定host境界49試験PASS。通常native new-game/実取引は未受入。候補5d1fc9c4と既受入loadは保持。

## 受入範囲

正本22関数をexact Git blobから無改変抽出。44個のC正常境界と5個の抽出/不正要求検査、計49 unittest。新規初期化は2048byte全体・独立checksum・両端canary・badge 0/1/255・NULL・再初期化を確認。UIは全23選択位置/5ページ、絞込後catalog対応、B/末尾取消、入力待ち/不正行、task/window生成失敗、次ページ描画失敗、残高0/9999、NULL行文言、PostShopMenu、未選択購入拒否と選択済み購入委譲を確認。全選択で購入前ledger/owner不変、task/window解放とscript context復帰を検査。

## 限界

これはhost上の正本C制御フロー試験であり、ARM ABI・実描画/日本語文言・正規NPC到達・実Bag/Flash取引・初回通常Save/Continueを証明しない。engineサービスとunlock/catalog表示は明示stub。PurchaseByIndex本体はstubであり、購入成功を受入しない。normal_new_game_accepted=false / transaction_ui_accepted=falseを保持。旧native/単体再実行0、ROM変更/ARM compile/link0、mGBA実行0、host compile1。

## 次工程

次は通常new-game入口→初回通常Save/Continue、および実取引UIの取消/選択/購入/保存をnativeで限定検証する。host49件とphase0 load2件/43unit、V1 load3件/40unit、7retryは変更影響なしに再実行しない。

run `36246184229` / source `7f7575ca83765ba0d3c7a033e95015874555dd33` / 終端照合 `True`。source/protected bindingsと原本manifestはcheckpoint参照。一般CI action_requiredは全CI成功に読み替えない。
