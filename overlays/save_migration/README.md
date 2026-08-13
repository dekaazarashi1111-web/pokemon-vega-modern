# T08 save migration overlay

`save_migration.c` は、CFRU-JPのsave parasite image offset `0x1F18`、EWRAM
`0x0203D000..0x0203D800` に置く2 KiBのversioned ledgerを定義する。GBA側の
adapterは `gVegaModernSaveData` を既存のsector 30/31 read/writeに含め、
`VegaPersistCallback` 内で既存の全sector save routineを呼ぶ。callbackが成功を返す前に
battle開始、報酬付与、施設party破棄へ進んではならない。

## load順序

1. FireRed/Vega側のsector signatureとsector checksumを既存routineで検証する。
2. ledgerが現行magic/versionなら `VegaSaveLoad` を呼ぶ。checksum・size・versionのどれかが
   不正ならcontinueせず、破損または非対応versionを明示する。
3. ledgerが全 `0x00` / `0xFF` で、既存Vega saveが検証済みなら、legacy ABIから必要signalを
   `VegaLegacySignals` へ抽出して `VegaSaveMigrateLegacy` を一度だけ呼ぶ。
4. migration後の全sector saveが成功してからcontinueする。失敗時は旧slotを残し、移行済みと
   扱わない。

早期渡航は `FlagGet(0x0824) && FlagGet(0x114B)` またはVega殿堂入りから一度だけ付与する。
`KANTO_TRAVEL_UNLOCKED`、訪問済み、殿堂入り、認定章、地方、anchorは互いに独立しており、
Vega badge/HM/story bitmapを書き換えない。

## transaction境界

- Factory入場は600 byteのparty全体を先に永続化し、成功後だけrental partyへ切り替える。
- 復元はlive partyへbyte copyしてから、復元済みledgerとlive partyを既存save routineで同時に
  確定する。失敗時はsnapshot markerをRAM上で戻すため、同じcopyを安全に再試行できる。
- 遭遇支払いはcredit減算と、生成済み個体の全属性・generator version・fingerprintを一つの
  commitにする。成功後だけbattleを開始し、捕獲成功以外ではpendingを消さない。
- Factory、Mirage、Raidのrecord/reward ownerは分離する。Mirageはitem reward transactionで
  あり、数値通貨を持たない。battle-local仮想itemはledgerへ入れない。

`natureMint`、Hyper Training 6 bit、Tera typeはCFRUのBoxPokemon/party Pokemon両ABIで
offset `0x0F/0x10/0x11` にある。sidecarへ複製せず、個体の80-byte永続部分と一緒に
party・PC・進化・タマゴqueueを移動する。
