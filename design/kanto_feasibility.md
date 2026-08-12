# FireRedカントー復元・二地方化の初期実現可能性評価

評価日: 2026-08-12

## 判定

**GO（実現可能性は高いが大規模）**。

VegaとFireRedは同系統のフィールドエンジンを使い、所有するclean BPRJ Rev.0にカントー原資産がある。Vega内の元領域を上書き復元するのではなく、cleanから資産を抽出し、新規KANTO MapGroupへ複製・全参照を再リンクすれば、トーホクとカントーを1本のROMに同居させられる。この構成はVega殿堂入りを待たず、本編中盤から任意で渡航させることもできる。

## 初期読取inventory

固定済みpokefireredの全425 mapから、ナナシマ・link等を除くカントー本土候補を構造的に絞った初期値。

| 対象 | 件数 |
|---|---:|
| physical maps | 256 |
| outdoor | 38 |
| dungeon | 96 |
| indoor | 122 |
| unique layouts | 180 |
| object events | 1,137 |
| warps | 938 |
| connections | 84 |
| coord events | 159 |
| bg events | 539 |
| primary / secondary tilesets | 2 / 49 |

180 layoutのblockdataをclean日本版BPRJへbyte検索したところ179件が一致した。Vega参照ROMに同じbyte列が残るlayoutは54件だけだった。pokefireredとclean日本版が一致しなかったRoute 11を含め、raw値はclean BPRJを正とする。

layout/border raw合計は概算約287 KiB、対象mapの構造的source量は約1.23 MiBだった。これは最終圧縮・link sizeではない。32 MiBへ収められる見込みはあるが、Factory拡張16 MiBをコピーせず、DPE/CFRU/カントーを重複排除して再リンクすることが前提となる。

このinventoryは実装前の初期測定であり、T11で再現可能なCSVとcrosswalkとして再生成する。

## 主な難所

- Vegaには完全なdecomp sourceがないため、実ROMのmap group table、field special、script ABIへ接続するharnessが必要。
- pokefireredは英語版decompなので、raw資産と日本語版固有差分はclean BPRJから抽出する必要がある。
- 256 mapのwarp graph、shared layout/tileset、map固有script依存をV2の47論理地点へ対応付ける必要がある。
- Map group/numのsigned 8-bit経路、予約値、hidden item flag幅をT02で監査する必要がある。
- SaveBlockへ認定章、研究ランク、地方状態、特殊個体125共有flag、再戦queueを安全に追加する必要がある。
- 32 MiB内でDPE/CFRU画像・鳴き声・コードとカントー資産をdeduplicateして配置する必要がある。

## 進行上の要修正点

V2はクチバ到着を入口にする一方、認定章0の主対象を1〜4番道路・ニビ・ハナダ、クチバ周辺を認定章2相当としている。このまま物理接続をgateすると到着直後に進行不能になり得る。

採用方針:

- 到着時からクチバ港・市街・6/11番道路・ディグダのあなの初期回廊を通行可能にする。
- クチバジム、船上大会、後半施設だけを認定章でgateする。
- 連絡船の帰還NPCは常時有効にする。
- T15の進行graph validatorでunreachable、循環前提、帰還不能をエラーにする。

## 早期アクセスの成立条件

- 概念解禁点は、シオウの3個目バッジ取得後、アーシア島D・Hビルの初回攻略完了時。使用する実flagはT02のscript監査で確定する。
- 初回便はアーシア島から、初訪問後はシオウにも再訪用乗船NPCを登録する。クチバからの帰還は常時無料とする。
- カントーのLv.68〜100帯は固定し、party平均に合わせて下げない。初回乗船前に「推奨Lv.65以上」を警告する。
- クチバ港から市街、PC/回復、帰り船までに強制戦闘、不可避の草むら、field move要求を置かない。船上戦は任意で、敗北・辞退で渡航権を失わない。
- カントーの高レベル個体を持ち帰ってVega本編の戦闘が易しくなるのは、任意高難度ルートの報酬として許容する。一方、Vegaの必須flag、warp、HM、重要道具を飛ばすsequence breakは許容しない。
- 早期フェーズは認定章進行0〜4、Vega殿堂入り後は後半認定章、カントーリーグ、最終共鳴を解禁する。

## 先行ゲート

1. T02: Map/Flag/Var/Trainer/Item/Save/RAM/ROM allocationの実使用域を確定。
2. T03/T10: Vega module harnessとengine縦切り。
3. T08: 二地方状態を含むSaveBlock設計。
4. T11: 256候補map inventory、V2 crosswalk、1map importer spike。
5. T12: region付きsymbolic schemaとvalidator。
6. T13: クチバ往復product slice。

この順を守れば、元FireRedらしいカントーを残しながら、Vega本編を壊さず二地方を往復可能にする方針は技術的に成立する。
