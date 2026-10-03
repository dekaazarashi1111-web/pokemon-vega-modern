# PR16 V1通常ロードの先行call修復

先行load call誤認を修正。正常V1は保存counter2→3/全ledger移行/2回fresh Continue成功。破損2例は通常load中に有効V2へ初期化される実不具合を保持。

QOL restore_durable_ledger/ensure_saveの空・破損混同を修復し、破損2例の実load拒否だけを先に検証。正常V1成功/旧26unit/7retry/ARMを影響なく再実行しない。

## 観測と受入境界

起動先行callはreturn PC 0x080ED736、result2/counter0/version0。通常Continueはreturn PC 0x080789FE。両callerのThumb BLが既存root0x080DB4E4へ到達するbyteを候補58079dfbで照合。呼出し数2・順序・型・値を閉じたschemaで検証し、初回だけの停止を成功にしない。ROM変更0、ARM compile/link0。

保存済みローカルnative原本3process/5fresh cores・host compile成功1を再利用。正常V1は全ledger/他owner/Bag/party/実Flash/counter保持を受入。checksum/tail破損はresult1/version2/counter2となり、拒否条件で失敗。旧3失敗と今回2失敗は別原本のまま。私有Flash fixtureであり歴史的ユーザーsaveそのものではない。新規native再実行0。

初期のローカル準備で部分sourceのmodule不足と生成前compile失敗があったがnative0。generation用の依存だけで解決し、測定したC hashを再構成照合。新規parser20試験のみ実行。7書込barrier実装は不変、guard専用process再実行0。

## 残件

破損load拒否、load内phase0保存不可/回復、通常new-game/取引UI、物理Flash故障は未受入。Issue19/全catalog/releaseは未完。merge/release/baseline切替なし。

## 記録

native source `562cd8dab16ed6ca39f11b6539da5d3ad94fcef7`、record run `36239754501`。記録run終端・push/uploadは次に照合。原本: `content/modernization/pr16_research_v1_load_root_diagnostic.json`。
