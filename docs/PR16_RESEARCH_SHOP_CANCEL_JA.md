# PR16 実ショップ取消・通常Save/Continue

実ResearchショップのB取消/末尾取消と通常Save→独立Continue2回を受入。進行・100RP・stock warpはfixture、購入/new-game全体は未受入。

## 実経路

現候補のmap98/3背景0、(2,1)の実script pointerを確認。初期進行/残高はprivate seedのledgerだけのfixture。停止区間でstock warp4呼出とfield callback1wordを設定し(2,2)へ入る。以後7 API書込barrierを装着し、通常方向/A/B入力だけで実menu task/windowの生成、B取消、再受付と全表示ページの末尾取消、task/window解放、idle field復帰を確認。shop dispatch・結果・PCの観測中注入なし。停止fixtureのregister/stack書込が0とは主張しない。

取消両経路で128KiB Flash全byte/counter不変、全Bag5pocket/party600byte不変、ledger全2048byteは通常minuteとそのchecksum以外不変。研究ownerは100RP/rank1/nextTransaction1のまま、稼得/消費/pending/claim変更0。通常Start Save1回/counter+1、独立coreのContinue2回でledger/Bag/party保持とUI揮発状態resetを確認。

## 計測

新native1process/3cores、7guard拒否probe、host compile1、oracle20PASS。旧受入再実行/ARM compile/link/ROM変更0。候補 `5d1fc9c47225ae8c0a369514b899a062af3699fa3c9a2f617e94ffd5f7dcc1ab` を既存recipeから復元。失敗試行があれば別原本として保存し成功に読み替えない。画面の目視監査・全catalog価格/日本語文言・購入成功・通常進行からの到達・実RP稼得・通常new-gameは未受入。

## 次工程

まず本runの終端・非force push・uploadを照合する。次は通常new-game→初回Save/Continueと実ショップの選択/購入/不足/保存境界。取消2経路/native1件/新oracle20件、host49件、既受入phase0/V1/retryは影響なしに再実行しない。

run `36247330231` / source `7513da51e99e4511f88ecdc153c95434ed044791` / 終端確認 `False`。manifest/source/protected bindingsはcheckpoint参照。一般CIのaction_requiredは全CI成功に読み替えない。

## 入力seam修正と原本の分離

初回run `36246971189` は20oracleとcompile/guard、実背景→B取消まで通過したが次ページ確認で失敗。1frame押下から既存qol_press相当の2frame押下/受付settleへ変更した新driverだけを再実行し、元runを成功に改変しない。成功済み20件は依存hash照合で再利用し、再実行0。旧native stdout/stderr/process/compile/guard/inputs/invocationはprefix付き原本として新manifestに保存。今回のnative1/host compile1は受入run単体の値で、初回失敗分を消した総数ではない。エントリは `scripts/pr16_research_shop_cancel_followup.py`。
