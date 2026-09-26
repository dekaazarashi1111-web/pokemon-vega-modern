# PR16 V1実保存の通常ロード

通常cold boot/ContinueのV1移行・破損拒否3ケースを測定。成功 0 / 3。

まず本測定runの終端とpush/upload結果を照合する。失敗した v1-load-checksum, v1-load-tail, v1-load-valid の原本とload chainを最初に切り分ける。成功case/26unit/ARM/同一core再試行7caseは影響なく再実行しない。

## 検証境界

固定seedのコピー内のsector31 +0x64、2048byte ledgerだけをV1に変換し、checksum破損/193byte予約tail破損も別fixtureで作る。stock保存sectorと他ownerは変更0。歴史的なユーザーV1 saveそのものではなく、独立生成した私有Flash fixtureである。保存payload/ROM/binaryはGitへ入れない。

起動から通常Start/A/Continueで進める間、7host書込みAPIを禁止し、CPUのPC/SP/LR/r0は読取だけ。RAM ledger/owner/引数/戻り値/PCの注入0。0x080DB4E4の既存wrapperからResearch→Mirage→QOLの実load各1回、phase0実保存と戻り値/counterを観測する。既存188byte修正候補をrecipeで復元しARM再compile/link0、ROM変更0。

正常V1は全ledger移行内容/実Flash/他private ownerと通常field到達を比較し、2回のfresh Continueで全ledger/owner/Bag/手持ち/counterの不変を確認する。破損2例はadapter戻り境界までで、全ledger入力保持・128KiB Flash不変・エラー伝播を検証する。破損後のメニューUI全体は未受入。通常new-game/取引UI、load内保存不可、物理Flash故障、全catalog/Issue19/releaseは未完。

## 実行と記録

source `af1065f42eb965dacb26060a22595ed3f85a3adb`、run `36237653594`。26unit、host compile1、guard7、native3。終端記録は全再実行0。受入: 。失敗: v1-load-checksum, v1-load-tail, v1-load-valid。終端確認: False。候補 `58079dfbdbe15899d9b86f53ad3a21fe46ddcebf5fed231c85dcd2332ddd2d75`。
