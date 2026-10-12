# HOF/mainの世代結合と永続容量contract

## 到達点

実行可能なhost参照実装、故障注入器、容量validatorを追加した。実ROM、ARM、実Save parser、通常画面、独立cold processへの接続ではない。現候補88be8811と正式ROM/Save101は変更しない。HOF/mainの実機世代結合・跨領域原子性は未受入のまま。

## なぜタグだけでは足りないか

現mode3はHOF28/29を上書きしてからmain COWを実行する。main失敗時には旧mainが残るが、旧HOFの永続復元元がない。mainCounter以下を許す方式では、失敗後の通常Saveがcounterに追いついた時に未commitのHOFを誤受入する。stat10も999で飽和する。タグ不一致のread拒否は世代混同防止であり、旧HOFの保存保証とは別である。

参照実装はmainへ64bit非wrap HOF epochと全7936byte SHA256を格納する。通常Saveはそのtokenをそのまま継承し、HOF更新時だけepochを増分する。復元ではmain authorityを先に確定し、完全token一致のHOFだけを返す。HOFが失われた時に勝手に別mainへ降格しない。

## 参照transaction

1. 二重main、二重HOF、既存auxiliaryの非重複・永続容量と全入力を先に検査する。
2. 非選択HOF bankをeraseし、新HOF＋tokenを書き、全byte readback後に最後のcommit byteをprogramする。
3. 非選択main bankへ同tokenと新mainを書き、全byte readback後に最後のcommit byteをprogramする。
4. 最後のwriteが実際には成功してdriverだけが失敗を返した場合も、永続像から確定結果を再判定する。

selected旧main/旧HOFとsector30/31は書かない。epoch上限、型不一致、容量不足はwrite前に拒否する。未commit shadowが残ってもnormal Saveから採用しない。mainCounterのu32 wrapは合成selectorで扱うが、半周差と同counter異内容は拒否する。

合成形式は64byte header、CRC32、SHA256、署名最後書込みを持つ。既存ROMの保存形式と互換ではない。34sector合成fixtureは実Saveの拡張や暗黙migrationを意味しない。

## 現配置の拒否と容量根拠

- 現Flashは32×4096=131072byte。main28sector＋HOF2sector＋既存sector30/31で全32sectorを使う。
- 独立した二重HOFを単純追加するには34sectorが必要で8192byte不足する。validatorは現32sector配置を拒否する。
- mainのchecksum外tail候補は片bank1740byte。計算は204＋304＋11×112。logical13はPC2000＋S61E1558＋MDX522=4080で空き0。
- この1740byteは使用許可済みownerではない。現writerは予約領域を0で生成し、全4096byteのreadback期待値へ含める。新ownerにはwriter/clone/readback/load全体の変更が必要。
- sector31旧候補1100byteのうち522byteはMDX shadow。残578byteも4080byte全体を扱うQOL serializerの管理下で、独立ownerの空きではない。
- sector30は未使用認定しない。固定CFRU upstreamは4080byte拡張領域を扱うが、現ROMの全reader/writer到達性は未監査。
- ROMの現115owner、scheduler43subowner、実残186byteをそのまま保全。古い366byteや旧suffixを空き扱いしない。

## 検証範囲

単一writer、同期readback、NOR byte program、CRC/SHA衝突がない故障モデルのhost検証である。blank shadowと有効旧bank再利用の各保存について、全program byte直後と全erase前後で永続像だけからold/new pairを再選択する。再利用target全16sectorの6種erase prefix中断、driver失敗、silent write省略、commit直後誤error、power loss/restart、counter wrap、epoch枯渇、失敗後normal Saveを検査する。

これは実Flashの全故障、任意破損、同時writer、ARM ABI、自然HOF到達、HOF全種族、実cold Continueの受入ではない。実ROM/nativeの無影響再走はしない。

## 次の実装

永続表現を先に決め、必要ownerと容量を証明する。候補はHOF不変base＋main tailへの追加team logである。固定upstreamの20byte mon×6=120byte teamならheader60byte以内で最大14件だが、満杯時compaction、現在ROMのABI、末尾1936byte用途が未解決。有限logを全HOF保存完了とはしない。容量不足を不明領域借用や履歴切捨てで隠さない。

その後、全mode/通常Save/Link clone、HOF-only load、validator、読戻し、migration、cold復元を同契約へ接続する。共通SaveFailed、早期sector31/単bank原子性、残typed consumer、全cold owner、正式切替、trainer131後半も未完。最終目標はシオウ通常回復・保存・独立cold Continueであり、雑魚毎Saveは復活させない。

## 固定source参照

- overlays/stage61_display_npc_event_audit/stage61_display_npc_event_audit.c: chunkサイズ、予約tail zero、全byte readback、COW。
- overlays/dex_owner/dex_owner.h: MDX522byteとlogical13配置。
- overlays/qol_production/qol_production.c: sector31全4080byte serializer。
- content/modernization/pr16_dex_storage_audit.json と pr16_dex_loadchain_audit.json: 旧候補容量と既存owner。新空き認定には使わない。
- 固定[CFRU save.c](https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/save.c)と[FireRed hall_of_fame.c](https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/hall_of_fame.c)。upstreamの確認を現ROM ABI受入へ昇格しない。
