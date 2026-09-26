# PR16 採掘の実RP稼得 — 実装チェックポイント

USER-20260927-RESEARCH-MINING / WIP_NATIVE_MEASURED_ORACLE_PENDING

開始HEAD `8ec5a37666e07a12f1b31d8c5257324168d8fe4e`。context保存 `f12167c776d230fa1cc10dab93f2617f1534c4df`、run36266517223 SUCCESS。写真・虫取り・保存viewの受入原本と候補を変更せず、新規採掘3ケース専用ランナーを追加した。

候補26dac23c / 33554432bytesは専用recipeのbyte適用だけで復元、ARM compile0。現ROMのmap97/82、local12、(1,20)、event0x09413B40、record0x0941397C、script0x093C050Cを確認。現在のobject template数は17、live対象岩1。旧configのappend前件数を現ROMの件数へ流用しない。

ローカル開発8processのうち失敗5、成功3。バッジ不足・技不足はRP0/Flash不変、取消も不変。標準いわくだき→岩除去→実FieldMiningで0→10RP、counter2→4、取引自身の保存2回、手動Save0。独立coreの通常Continueで全2048byte台帳・party600byte・Bag・他owner・checksumと残高10を保持。日次上限は3番目のcoreの開始fixtureで隣接階へstock warpして戻し、実岩を再度調べてresult4/残高10/Flash不変を確認。自然な階往復を受入とはしない。

初期party/技/バッジ/進行/warpはfixture。報酬・上限文言で止め、後続RockSmashWildEncounterの自然終端は未受入。初期の過剰A入力によるparty変化2失敗、岩消去がContinueでも残るため再interactionへ進めなかった1失敗、件数誤仮定とCPU非保存のsetup各1失敗を成功に読み替えない。全原本はこの作業のローカルmeasurementへ保存してあり、次commitで固定のtext証拠として記録する。

4文言（条件不足、確認、10ポイント、日次上限）を目視確認。形式oracle・負例unit・Actionsでのexact source測定と引継ぎ/両ログ同期が未完了。採掘の正式受入へまだ昇格しない。次はこのランナーを再利用して原本検査を完成し、写真/虫取りのnativeを再実行しない。残る釣り・生態・ゲームコーナー、通常進行からResearch受付/ショップ接続は未完。PR draft/open、未merge、release/baseline変更なし。
