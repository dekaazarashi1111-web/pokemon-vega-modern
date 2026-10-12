# 特殊野生: 通常操作検証

特殊野生通常UI: PASS_SPECIAL_WILD_UI_CAPTURE_SAVE_SCOPED。成功=['fishing', 'hidden']、失敗={}。開始fixture/実取得は区別。

Issue19: candidate23d58409の共有研究保存delegateにより影響する他の取引は旧受入を自動継承しない。通常UI2件が揃えばActions終端照合と設定・recipe bindingを確定し、同じnativeは再実行しない。特殊野生が未成功ならそのcaseだけ続行する。map3/19除外130行は変更しない。

生態レーダーID348の通常隠しメニューと、すごいつりざお264が対象。前準備のcatalog scanner278は通常隠しUIのownerではない。前準備原本は不変。

初期map/lead/item/unlock/research/RNGだけfixture。観測区間は7host APIを遮断し、CPU読取りとキーだけを使う。特殊setter/4slot/PP/捕獲100byte/保存200byte・全inventoryを照合する。

最新run `36220635424` / source `26d807032a1b423da8f14050b6469e779bc03983` / failure `None`。

原本: `content/modernization/pr16_special_wild_ui_checkpoint.json`。全Actions完了は同run実行中の自己証明をしない。release/Issue19/baseline切替なし。

## 保存先修正と通常UI 2件の記録

研究persist_phaseがSaveLoadAdapter(0x09377695)へ誤委譲し、捕獲直後に旧saveを読み戻していた。TrySavingDataAdapter(0x09377661)へ1byte修正し、configの同じdelegateを一致させた。固定親/候補hash、両target body、前後context、全rollbackを照合。ARM再compileなし。

hidden: local固定mGBA原本、species843/move244。fishing: Actions原本、species492/move225、3回の通常cast。両方で7host write APIを禁止し、通常item UIから捕獲・Save/fresh Continueと個体100byte/手持ち200byte・全inventoryを照合。開始fixtureからstory到達の受入は主張しない。

原測定run36220635424はnative/原本保存成功、index対象集合エラーでpublish skippedとなったfailureのまま。成功runへ改称しない。記録工程だけ復旧し、両nativeを再実行しない。今回phase=recover。

通常UI2件の成功原本は記録復旧済み。次は記録復旧Actionsの終端成功を確認しfinalizeのみ実行する。native/旧unit/ARMは再実行しない。

## 保存先修正と通常UI 2件の記録

研究persist_phaseがSaveLoadAdapter(0x09377695)へ誤委譲し、捕獲直後に旧saveを読み戻していた。TrySavingDataAdapter(0x09377661)へ1byte修正し、configの同じdelegateを一致させた。固定親/候補hash、両target body、前後context、全rollbackを照合。ARM再compileなし。

hidden: local固定mGBA原本、species843/move244。fishing: Actions原本、species492/move225、3回の通常cast。両方で7host write APIを禁止し、通常item UIから捕獲・Save/fresh Continueと個体100byte/手持ち200byte・全inventoryを照合。開始fixtureからstory到達の受入は主張しない。

原測定run36220635424はnative/原本保存成功、index対象集合エラーでpublish skippedとなったfailureのまま。成功runへ改称しない。記録工程だけ復旧し、両nativeを再実行しない。今回phase=finalize。

特殊野生の釣り/生態レーダー通常UI→捕獲→Save/fresh Continueは2/2受入。再実行しない。次は共有研究保存delegate修正の他取引（earn/spend/rank/recovery）の影響範囲を限定検証する。旧候補の取引受入を新candidate23d58409へ自動継承しない。map3/19除外130行は未確定のまま保持。
