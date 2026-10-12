# 図鑑owner修復の実装checkpoint

## 現在の結論

正式進行はSave101のまま。ROM基準・Save原本・既受入nativeは変更しない。
実装済みはstable-key namespaceとhostで動く保存codec。ゲームへはまだ接続しておらず、修復完了やシオウ到達を受入しない。

## 番号の正本

既存 `vendor/vega_acquisition/TARGET_DEFINITION.md` の方針を再利用する。
公式1025種とVega181種の計1206 ownerは既存collection ledger bit0..1205と同じ順序。
公式フォーム437は本体owner共有。進化入口10フォームの取得台帳は別のまま。
新たな完成数・フォーム収集方針は作っていない。

`pr16_dex_namespace.py` はspecies_keyで現manifestをjoinする。全1670slotのうち1643 variantが1206 ownerへ対応し、NONE/Egg/内部25slotは除外する。
vendor snapshotの数値IDはコピーしない。Eggは現412、キャタピーは現649。
namespace v1のkey順序SHA256は4a0cb4d7c386ae62e69c16fa939bdadbd3bff683ea95e51d9c444bbca10a4072で固定し、順序変更を自動追認しない。

固定候補の旧hybrid番号には別owner衝突277群、旧1..386では276bitの曖昧さ、同一ownerの番号分裂52群がある。
native公式205行中188行は現在番号が公式nationalと異なる。native全範囲が恒等写像という意味ではない。
SID129メタグロスはowner129、SID481コイキングはowner456となり旧番号129の衝突を解消できる。
SID1537/1147はowner1144/930。official national、native地方図鑑番号、SIDを同一整数APIで推測解釈しない。
既存公式逆引きの413開始探索もnative公式を代表baseへ返さないため、生成表では正本base keyから代表SIDを明示する。

## codecの実装

`overlays/dex_owner/dex_owner.c` は522byteのMDX1を扱う。
- header12byte: magic4、CRC32 4、namespace/version u16、legacy snapshot flag u8、reserved u8
- seen151byte、caught151byte。1206 owner以外の末尾2bitは0
- 旧seen三鏡/caughtの208byteは順にSave1 primary、Save1 secondary、Save2 seen、Save2 caughtをそのまま保全
- CRC32は522byte全体を対象としCRC欄だけ0扱い。非整列アクセスはbytewise
- caughtはseenを含む。不正owner/mode/version/CRC/flags/paddingは変更前に拒否
- caught clearはseen保持、seen clearはcaughtもclear。legacy snapshotは両方で不変
- legacy移行は親bank検証後、companionが全0または全FFのときだけ候補にする。非空の壊れたrecordを旧version扱いで上書きしない

旧bitから新ownerへ根拠なしの複製・消去はしない。VACQも旧getterからseedされた可能性があり無条件に取り込まない。
旧caughtの高番号書込はSave2 seenへ重なるため、ownerが一意というだけでも安全な移行根拠にならない。
party/PCの実個体など別の確実な根拠からの昇格と、既存履歴をどう見せるかは接続工程で明示する。現ゲームで履歴を初期化したという意味ではない。

## 保存場所の候補と未完条件

logical13のPC payloadは0..0x7D0、既存S61E v1は0x7D0..0xDE6。
残り0xDE6..0xFF0の522byteにcompanionが収まる。Save101両bankのこの領域は全0と確認。
末尾reserved4byteとfooterは占有しない。物理sector13固定ではなくlogical id13とcounterを解決する。
main二重bankのCOWに結び、独立sector31を保存正本にしない。stock checksumはPC本体までなのでMDX独立CRCが必須。

RAM候補0x0203DB40..0x0203DD4Aは宣言ownerとは衝突しないが、PC/UIが未保存bitを消さないことは未証明。
既存の「cache invalidならflash reload」は新しい未保存seenを失うため流用不可。
このRAMはsector31 imageに含まれ他owner保存時に副写しが生じる。非正本shadowとするかserializerで保全するかを明示してから接続する。
現save_layout/ram_layoutへLIVE登録したり、ROMへ書き込んだりはしていない。

## late-stage接続ゲート

1. 未保存seen/caughtのRAM lifetimeをPC/summary/bag/naming/図鑑で実証する。必要な退避/復元ownerを宣言する。
2. Stage61のvalidate_slot、inject_tail、expected_prepared_byte、tail_matches_live、load_compatible_record、clone、record-onlyを同じcompanion契約にする。
3. normal/link/HOF/overwrite/EREADER/newgame/failed-load/cold Continueを確認。CRC破損bankは採用せず前bankへfallback。選択bankのstock復元後にlegacy snapshotを取る。
4. SIDを失う前のbattle/capture/gift/acquisition/research/facilityを新owner APIへ接続。official count/UIとnative地方UIは専用mappingを使う。
5. Repeat Ball/critical captureの旧Bag直接popcount、reward rollbackの旧owned直接clear、memorial/Codexの旧bitmap snapshot/restoreも修復対象。
6. T09早期再リンクを避ける。Stage70はT09の5literalに加えStage61 headerの絶対位置もpatchするので専用late-stageの署名照合で接続する。
7. host境界、全非owner sentinel、bank/counter/rotation、partial-write/lying-success、再暗号化、通常Save/独立cold Continueを限定受入。
8. 新候補保存ABIとconsumer受入後のみSave101未保存失敗区間へ戻り、trainer131/128/1065からシオウPokecenter通常回復・Save・cold Continueへ進む。雑魚戦ごとのSaveは作らない。

## 実施と未実施

namespace生成/check、実host GCCによるcodec試験、固定ROMの読み取り専用alias監査を実施。
ARM/native、ROM patch、候補採用、通常Save/cold Continue、trainer新勝利は未実施。
sourceと最終試験件数は `content/modernization/pr16_dex_owner_checkpoint.json` を参照。
一般CIの既知QOL source不一致、最終bot commitのaction_required/job0、Stage79 cache再利用はこの保存codecのnative受入とは別。

根拠は開始HEAD1c71d539e245d6a9fe83650b8a19ff3282e66c94の固定source、既存owner台帳、指定候補とSave101のhash照合。公開する実ROM診断はaddress/size/SHA256と必要なowner metadataだけ。raw byte、ROM/runtime/inputSaveは公開しない。
