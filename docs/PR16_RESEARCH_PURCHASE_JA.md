# PR16 実Researchショップ選択・購入・残高不足

実Researchショップの行選択/確認拒否、10RP購入、残高不足拒否と取引直後の独立Continueを受入。通常Saveと続く独立Continue2回も保持。進行/10RP/warpはfixture。

## 境界と限定

現候補の実背景scriptと全23行catalog368byteのhashを固定し、catalog0/item4/価格10RP/数量5を実ROMから照合する。初期進行と10RPはprivate seedのledger限定fixture、停止状態でstock warp4呼出とfield callback1wordのみ設定。以後7APIのwrite barrier下で通常キー入力だけを使う。観測中にshop dispatch/購入結果/PC/在庫/残高を書き込まない。

実行順は行選択→購入確認のB拒否→再選択→A購入→手動Saveより前の独立Continue→再選択→残高0で不足拒否→通常Start Save→独立Continue2回。購入時の取引保存2回と手動Save1回を区別する。拒否/不足は128KiB Flash全byte・counter不変、購入は対象item+5以外の全Bag5pocket/party600byte不変。全ledger2048byteをminute/checksum以外対照し、全owner64byteの残高10→0/nextTransaction1→2/claim/pendingを閉じて検証する。

これはcatalog0の限定受入であり、全catalog価格/日本語画面の目視監査・通常new-game・実RP稼得・自然進行からの到達を証明しない。ROM変更/ARM compile/link/旧受入再実行0。旧取消・旧失敗原本・P08・baselineを変更しない。

## 原本

run `36249587919` / source `bd690e9be3933332ba955900d83f16a73a8b975e`。status `PASS_NATIVE_PURCHASE_PENDING_TERMINAL`、終端確認 `False`。成功 ['shop-select-purchase-insufficient-save-continue']、失敗 []。manifest `content/modernization/pr16_research_purchase_evidence/36249587919/manifest.json`。過去失敗は `attempt_history` に別identityで保持。一般CIのaction_requiredを全CI成功へ読み替えない。

## 次工程

まず本runの終端・非force push・uploadを照合する。次は通常new-game→初回Save/Continue。購入/不足native1件・42oracle・旧取消/host49/phase0/V1/retryは影響なしに再実行しない。
