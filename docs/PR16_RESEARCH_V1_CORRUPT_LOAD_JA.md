# PR16 V1通常loadの破損拒否修復

通常V1 loadの3件を受入。起動先行call誤認とQOLの空/破損混同を修復。破損checksum/tailは全入力とFlashを保持して拒否、正常V1は実保存と2回fresh Continue成功。

次は通常load内のphase0保存不可境界・回復を限定実装/検証する。その後通常new-game/取引UI。3load/旧26unit/新40unit/7retry/BP/P08/特殊野生は変更影響なく再実行しない。

## 修正

QOL restore_durable_ledgerが検証statusを返し、EMPTY_OR_LEGACY以外の保存原本は全2048byteをRAMへ保持。ensure_saveは空と破損を区別し、破損からSaveInitNewへ進まない。後続Mirage/Researchの既存検証がエラーを伝播する。候補 `5d1fc9c47225ae8c0a369514b899a062af3699fa3c9a2f617e94ffd5f7dcc1ab`、32MiB。元58079dfbの既存0x09378DAC～0x09378E34の136byte窓のみ、132byteコンパイルcode、差分112byte、外側変更0、完全rollback一致。外部BLは関数入口のみで旧veneer内部への参照なし。新規領域の割当なし。

## 検証

checksum/tailの通常cold boot/Continueはresult0、version1、last_result7、counter2、保存0。全ledger入力SHAと128KiB Flash不変をnative側で確認。正常V1はcounter2→3、phase0保存1回、全ledger移行、他owner/Bag/party不変、通常fieldおよび2回fresh Continueの完全一致。7host書込barrierを維持、RAM ledger/owner/PC/戻り値注入0。私有Flash fixtureであり歴史的ユーザーsaveそのものではない。

修正候補native3process/5cores、ARM compile1/link1、native用host compile1。新規unit20件の中でcanonical Cをhost compile1/process1、100組のRAM/Flash statusを検証。先行call修復の新規20unitと合わせ計40件。元の26unit/7retry/他既受入は再実行0。正常V1だけは共有QOL変更の影響で1回回帰確認。ローカル測定原本・コンパイラ版・source/生成C/候補hashはJSONに記録し、Actionsでは再実行せず照合。

## 未受入

load内phase0保存不可/回復、通常new-game/取引UI、破損拒否後メニューUI全体、物理Flash故障、全catalog、Issue19、releaseは未完。merge/release/active baseline切替なし。以前の失敗原本は改変せず保持。

## 実行記録

record source `33c78f6769104707a79f2ec027e3dff5990bd356`、run `36240353448`、終端確認 `True`。 finalize run `36240425197`。
