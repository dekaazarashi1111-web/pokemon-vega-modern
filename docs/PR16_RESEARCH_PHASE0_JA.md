# PR16 phase0保存不可の限定検証

初期化/V1 RAM正常・破損拒否5件に加え、phase0既存native保存不可3/3件を記録。次は同一coreの失敗後再試行とV1通常load adapter。特にEMPTY失敗後はV2 RAMを残してblockedとなるため、再試行時の永続化をまだ保証していない。受入済み5/18/phase0成功ケースを再実行しない。

## 実行境界

候補4aee03e8の変更なし。native trampolineのliteral0x09378b28が指す0x03005044を、観測開始前だけ1から0へ設定する。既存engine0x080db356のcmp/bneが保存不可分岐へ進み、QOL wrapperへ返るPC0x0937767aのr0=255をreadonly観測する。research fault flagをphase0の故障として偽装しない。7 API host-write guardは観測中有効。

3ケースは空/消去済み初期化とV1 RAM移行。phase0試行1回、native失敗1回、保存counter増分0、全128KiB Flash不変、Bag/手持ち不変を検査する。V1は全2KiB rollback、新規はRAM V2を残してblocked=1。独立coreで通常Continue2回、全ledger/owner/Bag/手持ちが旧保存と一致する。

## 未受入

物理Flash装置故障、途中書込、同一core再試行、通常V1ファイルのload adapter、新規ゲーム全体・通常取引UIは別境界。EMPTY失敗後の同一core再試行は優先して調べる。今回の新規18unit/3native/7guard/host compile1/ARM0、旧5+18native再実行0。BP/P08/特殊野生/active baselineは不変。

## 原本

source `4946ff7f22401b260362ca6d6be7e7cb4bd1c460` / run `36234797221`。成功: init-erased-save-unavailable, init-zero-save-unavailable, v1-save-unavailable。失敗: 。終端確認: False。
