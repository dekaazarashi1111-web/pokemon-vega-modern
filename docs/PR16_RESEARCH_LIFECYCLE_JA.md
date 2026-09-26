# PR16 研究保存lifecycle限定受入

研究保存初期化/V1 RAM移行の5ケースと15fresh coreを受入。次はphase0実失敗とV1 load adapter。成功済み5件/旧18境界/unit22は再実行しない。通常new-game/取引UI・全catalog・map3/19除外130行は別の未完境界。

## 結果

候補4aee03e8、測定source17871a2b、run36234024026。空/消去済み初期化、正常V1 RAM移行、V1 checksum不正拒否、V1 tail不正拒否の5件PASS。保存counterは成功系2→3→3→3、拒否系2→2→2→2。全64byte owner/Bag/party/2KiB ledgerと独立core Continue2回を照合。通常new-game全体、V1保存の通常load、phase0失敗、通常取引UIは未受入。

## buildと履歴

初回run36233675420はmainマクロ衝突のcompile failure、native0。次runは外側main宣言だけを生成時改名し旧runner/productionを不変にしてstrict compile成功。22unit原本をsource hash一致で再利用、native5/guard7を一度だけ実行。次run終端は過去compiler原本の末尾空白でdiff check failure。原本を削らずUTF8 JSON文字列へ可逆写像し、原本ZIP/hashを保持して記録する。公開写像8新unit、記録native/compile/ARM0。

## 再開

専用checkpointとmanifestに固定原本・全member/source hash・失敗runの状態を保持。Actions記録終端確認: False。BP/P08/特殊野生/active baselineは不変。
