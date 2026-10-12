# 32sector内のHOF世代journalと一時scratch

## 目的と境界

34sectorへの拡張、履歴削減、圧縮の平均値、sector30/31やopaque1936byteの流用に頼らない。現物と同じ131072byte、main14sector×2、HOF28/29、CFRU30・QOL31というgeometryのまま、非選択mainを一時scratchとして明示的に再利用する。

今回の実装はCの256byte journal codec/逆差分復元、実geometryのhost scheduler、固定ROMの新しい隔離HOF ABI検査である。稼働ROMの保存writer/loaderへ接続した受入ではない。main内S61E/MDX等はopaqueでbyte保持し、host main parserは既存の全validatorの代用品ではない。正式ROM/Save101・現候補88be8811は不変。

## 固定ROMから得た制約

mon20byte×6=team120byte、最大50team。非満杯では先頭mon speciesが0の最初のteamへ追加し、満杯時だけ49teamを左shiftする。保存payload7936byteのうち先頭6000byteがteam配列、残1936byteは意味を推測せず全byte保持する。live8192byteの末尾256byteは保存されない。

HOF sectorはpayload3968byteと、FF8の署名08012025、FF4のu16 payload checksumを持つ。mainのchecksum欄FF6やcounterFFCはHOFでzeroになる。main footerとHOF footerを混同しない。新probeはこれらの不変window SHAを現候補でも要求する。

現HOF speciesは9bitであり、512以上を切り捨てる。今回その現状を観測するが修復済み・全種族対応とはしない。自然殿堂入り・実保存・cold UIの受入でもない。

## owner契約

- 選択済みmain14sectorは終始書かない。
- 非選択mainのlogical8/9はtransaction中だけ旧HOF2sectorのscratchへ移譲し、最終main COWで本来の内容へ戻す。physical番号はtarget rotationから算出する。
- logical4のpayload末尾EC0〜FBFへ新journal256byteを正式に割り当てる設計。FC0〜FEFの48byteはzeroのまま。既存ROM writerのzero/readback契約を未変更で借りられる空きとは扱わない。
- logical13は最初に無効化し、最後にcommitする。S61E/MDX ownerを侵食しない。
- sector30/31、他main tail、HOF opaque1936byteは一切借りない。
- ROMの現115owner/43subowner/実残186byteは不変。新codecのARM object sizeを測り、これだけで現186byteへ収まるとは主張しない。

## 永続transaction

1. 選択main/HOF、全差分shape、source main全14sectorのSHA、counter successor、64bit HOF epoch上限を検査。未知suffix変更や任意全HOF置換はwrite前拒否。
2. 非選択mainのlogical13を無効化。
3. logical8/9へ旧HOFを全sectorコピーしreadback。
4. logical4へ最終main内容とjournalを書き全byte readback。journalは旧/新epoch、旧/新payload SHA、旧main全SHA、counter、kind/index、失われる旧120byte、CRCを含む。
5. 固定HOF28/29へ新payloadを書き全byte readbackし、全7936byte SHAを確認。
6. この後だけscratchをmainへ戻す。旧HOFは新HOF＋120byte undoから全7936byteを復元できる。logical4は消し直さず、logical13を最後にcommitする。

非満杯のundoはoldestではなく実際に上書きしたslotの120byteである。満杯shiftでは最古120byteを保存する。50履歴を保ち、有限append logの満杯停止はない。

## cold・中断後通常Save

まず完全なmain authorityを決める。選択mainに対してsource counterだけでなく全main SHAが一致する非選択bank journalだけを読む。HOFが旧SHAなら直接読み、新SHAなら逆差分で旧像を復元し、書換途中ならscratchを読む。mainが新tokenへcommit済みなら完全一致する新HOFだけを読む。欠落HOFを理由に別mainへ勝手に降格しない。

通常Save/Link cloneは未完journalを解決する前にscratchやjournalを消せない。rollback時は新HOFから復元した旧像をまずscratchへ完成させてから固定HOFへ戻す。既にscratchが唯一の復元元なら、そのscratchを消し直さない。固定旧HOFが確認できた後にだけjournalを無効化する。通常Saveは選択済みtokenをそのまま継承する。

INITIALは外部ownerが『旧valid HOFなし』と明示した場合だけ許す。loader異常を無条件にabsenceへ変換しない。実ROMのhas-records flagとloader結果による移行preflightは未接続であり、このhost引数を実機の証拠にしない。既存valid履歴の破棄は認めない。

## 検証と未完

新16host suiteは全rotation/parity/wrap、50append/shift、C/Python全byte一致、全256byte journal破損、各destructive境界、erase-prefix/program故障、独立再選択・通常Save、rollback中再起動、55連続満杯HOFと通常Saveを対象にする。CRC/SHA衝突なし、単一writer、同期で正しいreadbackのNOR modelである。任意外部破損、driver再順序、実Flash全故障を受け入れない。

実ROM ABIの228caseは16pack＋204append/shift＋8clear。GetMonData/load/memory/UI依存を明示stubし、実保存・ゲーム画面は実行しない。新nativeが失敗すればfailureのまま保存し、成功した旧nativeを再走して埋めない。

次はcodec/schedulerを現save ownerへ配置し、全writer/clone/readback/normal/load/HOF-only/INITIAL migrationを同一契約へ接続する。ROM code容量と初回absence判定、species9bitの後継typed ownerを別途閉じる。共通SaveFailed、早期sector31、全cold owner、残typed consumerも未完。正式切替は検証後。最終シオウ通常回復・保存・独立cold Continue、雑魚毎checkpointなし。
