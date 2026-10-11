# 図鑑owner runtime接続の現在地

正式進行はSave101のまま。ROM、正式Save、active baselineは変更していない。
基礎codecの記録は `PR16_DEX_OWNER_IMPLEMENTATION_JA.md`、今回の正本は `content/modernization/pr16_dex_runtime_checkpoint.json`。

## 新たに実証したRAM寿命

固定候補06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5とSave101のprivate copyで、MDX候補0x0203DB40..0x0203DD4Aへ有効522byteを一度だけ配置した。
Bag、party Summary、図鑑、PC、PCからbox-nameを開いて戻る5経路で未保存MDXを保持した。各UIの画面を目視確認した。

- 全522byteを全frame検査。末尾2byteのalignment guardも保持
- CPU store8/16/32、STM、DMAを元callbackへ一度だけ委譲する監視で、同値書込も含め未所有writeは全件拒否。実測は0件
- watcherを通らないHLE memset等は全frame照合で補完。未知差分を後続storeのせいにしない
- party600byteとPC0x83D0を往復前後の現在pointerから論理比較。全byte一致
- Flash128KiBとSave101/RTC131088byteは不変。通常保存0
- PCの入口だけ各1回の明示direct-call fixture。その他は通常キー入力。自然なPC到達・ストーリー進行の受入ではない

Bagはrun37216583954の原本を再利用し、最終run37217077790は残る4経路だけ実行した。
最初のcompileはCのread16/read32静的名衝突でnative0。codecを別translation unitにした。
Summaryの最初の2試行はUI未到達で停止。実画面の先頭Summaryに対し余計なUPがCancelへwrapすることを確認して除去した。owner破壊を許可して通したものではない。

この結果は、この固定ROMの5UI経路で候補RAMが保持されたことに限る。全ゲームlifetime、保存、consumer接続の受入ではない。
既存のCodex PC消去smokeはhostで128byteを消す模擬試験だった。実PCが同じ領域を消去する根拠としては使わない。

## 新しい実C adapter

`dex_adapter.c` と生成表はSIDと公式nationalのAPIを分離する。
- SID129とSID481を別ownerへ解決。公式national129はSID481側へ解決
- 公式countは1025owner専用maskを1回のvalidate後に集計。Bag直接popcountを使わない
- 代表SIDはbase stable keyから解決。追加413以後だけを探す誤った逆引きを使わない
- reward caught clearはseenを保持する
- Factory用4byte snapshotは対象ownerを束縛し、別ownerへのrollbackを拒否
- Codex用151byte seen snapshot/restoreはlegacy208byteとcaughtを保持。snapshotに存在しない新caughtがある場合は原子的に拒否

これらは呼出し先の実装であり、既存ROM callsiteはまだ接続していない。native地方図鑑UIの番号mappingも未接続。

## 新しい保存companion bridge

`dex_save_bridge.c` はlogical13の0xDE6..0xFEFだけを扱う。
- blank全0/全FFと非空破損recordを区別。CRC/version/flags/padding等を拒否
- 親検証済みフラグだけでなくlogical id13・signature・同じcounterを照合
- stock全bank検証はcallerの責務。bridge単独をbank妥当性の証明にしない
- 注入でPC payload、S61E、reserved/footerを変更しない
- 選択bankのstock復元後Save1/Save2から旧4鏡208byteを固定順序で保存
- valid MDXのloadでは旧履歴snapshotを撮り直さない
- failed-loadの無効化は明示newgame初期化と区別し、自動flash reloadしない

このbridgeもStage61の実保存schedulerへ未接続。全save mode/CRC fallback/native保存を受入したことにはしない。

## 次の接続条件

1. Stage61旧sourceを保ち、専用late-stage生成copyでvalidate_slot/inject_tail/expected_prepared_byte/tail_matches/load/clone/record-onlyを同じMDX契約へ接続。
2. 元S61E v1の0x616byteとCRCは不変。MDXを共通record sizeへ黙って混入しない。
3. normal COWとLINK/LinkFullのsignature-last、全4096byte readback、lying-success拒否を保持。EREADER、HOF、overwriteの副作用を個別に扱う。
4. newgameのCFRU wipeは0x0203B0E8..0x0203DF8Cをclearする。wipe後に明示InitNewを行う。失敗loadではInitNewしない。
5. sector31 serializerはMDX RAMの副写しを含む。非正本shadowとして扱い、選択されたmain bankのMDXで上書きする時点を外側復旧Saveより前に固定する。
6. SIDが失われる前のbattle/capture/gift/evolution/research/facility/DexNav、旧Bag count、reward clear、Factory/Codex transactionをすべて接続する。
7. 未検証candidateを正式進行へ切り替えない。isolated normal Save/独立cold Continue、全非owner・bank/rotation/partial-writeを受入後だけtrainer131以降へ戻る。
8. 最終story節目はシオウPokecenter通常回復・保存・cold Continue。全雑魚戦ごとのSaveは作らない。

新ARM compile、ROM patch、新候補採用、ゲーム保存ABI、consumer native、trainer勝利、シオウ回復はまだ0/未受入。
一般CIの既知QOL source不一致、bot commit action_required/job0、Stage79 cache再利用を新nativeの成功として数えない。

## 独立レビューで補ったStage75内部フォーム

基礎namespaceの1670slotは0..1669であり、現固定候補の全runtime数ではなかった。
Stage75 config/contractと実ROMの両national表・BaseStats・Stage61/T09 countを照合し、Own Tempo RockruffのSID1670が現存すると確認した。
専用adapter表を1671slotへ拡張し、SID1670→base SID1142（SPECIES_KEY_ROCKRUFF）→official national744→stable owner925へ明示結合した。公式代表SIDは1142のまま。
owner1206の意味・順序・保存version・基礎namespace原本は変更していない。種数上限を1670のまま接続しない。

## late-stageの容量制約

署名付きの40空き窓・21入口・Stage75根拠は `content/modernization/pr16_dex_placement_audit.json`。size8は関数全体でなくpatch前確認窓の大きさ。

最終107-owner allocationと固定candidateの未割当40窓を照合した結果、未割当は合計3151byte。
大きい2窓はROM offset0x015FF958..0x01600000の1704byteと0x01FFFB28..0x02000000の1240byteで、残る207byteは1..14byteの断片である。
4KiB以上の連続leaseはない。Stage61全体を新payloadへ単純再リンクする案はこの容量に収まらない。
次はcompact owner mappingと既存owner内置換/再配置の正式leaseを設計し、到達性・所有者・全preimage hash・遅いpatch順を検証する。既存owner内のFFを勝手に空き扱いしない。
stock HandleSavingData 0x080DB230はwrapper内の委譲先なので直接置換しない。既存near veneer経由を維持する。
