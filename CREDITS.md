# Credits and third-party notices

Pokémon、ポケットモンスターおよび関連素材の権利はNintendo、Creatures、GAME FREAK、
The Pokémon Companyほか各権利者に帰属します。本作は非公式・非営利のファン制作物で、
各権利者の承認・提携を受けていません。ROM本体や第三者の原patchは配布しません。

## Pokémon Vega

- 原作ROM hack: Pokémon Vega制作チーム（公開版 2018-02-23）。物語、トーホクmap、NPC、
  固有event、楽曲、既存Species/Move IDを本統合の優先正本として尊重しています。
- 公開patchはbuild入力ですが、release archiveには含めません。

原作者個人名を裏付けなく推定せず、原配布で用いられた集合名義を記載しています。追加の正確な
帰属情報が確認できた場合は、原表記を保って更新してください。

## Complete Fire Red Upgrade / CFRU-JP

- Complete Fire Red Upgrade main contributors: **Skeli**, **Ghoulslash**。
- Japanese BPRJ port: **kapibarasan000 (kpbr)**、固定commit
  `e24a16fe39e27ae162faf5b78596d1f3df18489d`。
- Repository: <https://github.com/kapibarasan000/CFRU-JP>
- 本作で利用: battle core、AI、facility、gimmick、Raid、現代battle/QOL基盤。

CFRU READMEの利用条件に従い、CFRUまたはそのassetを使うgameから利益を得てはならず、
paywallと任意寄付も明示許可なしでは不可です。本releaseも販売・有料配布・寄付特典化を
禁止します。

CFRU documentation記載のcontributors:

- Code: Lixdel、pret、Sagiri、DizzyEgg、FBI、Touched、Navenatox、
  Doesntknowhowtoplay、Squeetz、Azurile13、JPAN、Diegoisawesome、
  Jiangzhengwenjz、Leon Dias。
- Graphics: Golche、Criminon、Bela、Solo993、canstockphoto.ca。
- Testers: Criminon、Dionen、Gail、Leon Dias、Recko Juice、Patrickz。

## Dynamic Pokémon Expansion / DPE-JP

- Dynamic Pokémon Expansion original copyright notice: **Kevin Mills**。
- Japanese BPRJ port: **kapibarasan000 (kpbr)**、固定commit
  `10ff98c85ebf37ab5cb39a41b6e9b50f06efb19e`。
- Repository: <https://github.com/kapibarasan000/DPE-JP>
- License: WTFPL Version 2（DPE-JP同梱 `LICENSE` の原文を正とする）。
- Generation 9素材の明記source: Shiny-Miner / Dynamic-Pokemon-Expansion-Gen-9、
  rh-hideout / pokeemerald-expansion。各素材の個別条件もそれぞれのsourceを正とします。

## pret / pokefirered

- FireRed/LeafGreen decompilation and data reference: **pret contributors**。
- Repository: <https://github.com/pret/pokefirered>
- Fixed commit: `c75f352304d529f6ba92d4f74b9cf8b5c3810788`。

英語decompilationのcode/dataは日本版FireRedのABI・map assetを検証して安全に名前空間化する
ために参照しました。原ROMを配布物へ含めません。

## Battle Factory reference provenance

- 公開帰属: **kpbr氏制作のBattle Factory patch**。
- 受領reference UPS SHA-256:
  `46ef4b008b7c68a94f919d037a0bba31853b32af3f50895e722e39deea336358`
- Reference ROM SHA-256:
  `570ac486f0e66563ee23278ff7ee34dd8dfeed11cbf37ab924d13eb2c62c0da5`
- 公開帰属確認ページ: <https://w.atwiki.jp/pokehackgames/pages/62.html>

このUPS/ROMは挙動比較のblack-box oracleにだけ使い、Vegaへ適用せず、byteやpatchをreleaseへ
収録していません。実装sourceは上記固定CFRU-JPと本projectのadapter/contentです。

## Integration and tools

二地方統合、Vega ID固定adapter、symbolic content、save migration、central allocator、
Kanto importer、QOL adapter、決定論build/test/release pipelineは本projectで作成しました。
GNU Arm Embedded Toolchain、Python、Git、mGBA/libmGBAを固定manifestに従って使用しています。

本ファイルは帰属と利用条件の要約です。矛盾がある場合は各upstreamに同梱された原文license・
README・documentationが優先します。
