# FireRedカントー復元・二地方運用ポリシー

## 既定仕様

- 元FireRedのカントー本土を、Vega初回殿堂入り後に解禁する第二地方として復元する。
- トーホクとカントーは連絡船で常時双方向移動できる。港、セーブ、回復、全滅復帰のどの状態からも帰還不能にしない。
- 初期入口はクチバ港。V2の地理矛盾を避けるため、到着時からクチバ市街、6/11番道路、ディグダのあなを通る初期回廊を移動可能にし、ジムや後半イベントだけを認定章でgateする。
- カントーの認定章8個はVegaバッジと別flagで管理する。初期縦切りではflag表示を優先し、専用UIは基盤安定後に追加できる。
- ナナシマはV2本体のscope外。予約IDだけを残し、カントー本土完成後の別判断にする。

## 復元方式

Vega ROM内に残る元FireRedの番号・領域を「元に戻す」方式は禁止する。clean BPRJ Rev.0からraw資産を取り出し、固定済みpokefireredを意味名・構造の補助資料として、新規の論理 `KANTO_*` 名前空間へ複製・再リンクする。

物理MapGroupは256候補mapを一つへ詰めず、例えば次のように分割する。

```text
KANTO_OUTDOOR_*
KANTO_DUNGEON_*
KANTO_INDOOR_*
```

mapGroup/mapNumを扱う既存APIにはsigned 8-bit経路と `0x7F/0x7F` の予約値があるため、各groupは安全側で127件未満とし、実番号はT02/T11のVega inventory後に確定する。

## 資産の正本

- raw layout/blockdata/border/tileset: 所有するclean BPRJ Rev.0から抽出した値を正とする。
- map名、source構造、依存関係の意味: `state/source-lock.json` で固定したpokefireredを補助にする。
- 日本語textと後日談script: 統合版で新規作成する。英語版decompのtextは持ち込まない。
- 二地方の進行・生態・イベント候補: V2二地方生態版をreview入力にする。

初期照合ではカントー本土候補180 unique layoutの179件がclean日本版BPRJ内のbyte列と一致し、Route 11だけがpokefirered側と一致しなかった。個別差異では必ずclean BPRJを優先する。

## V2の47地点と実mapの違い

V2のカントー47地点は生態・進行上の論理地点であり、建物の部屋、洞窟階層、ゲート、ジム内部などを数えたraw map総数ではない。

初期inventoryの本土候補は256 physical maps、180 unique layoutsだった。T11で次のcrosswalkを生成する。

```text
V2 logical location
  -> FireRed physical maps
  -> shared layouts / tilesets
  -> warps / connections
  -> scripts / text / field specials
  -> new KANTO symbols
```

詳細な初期評価は `design/kanto_feasibility.md` を参照する。

## 再利用しやすいもの

- 地形、border、collision、elevation
- BPRJ照合済みtileset資産とmetatile属性
- 建物配置とマップ接続の大枠
- warp/object/bg/coord eventの座標
- NPCの見た目・配置、generic movement
- ジム仕掛けの地形・演出骨格

## 新規名前空間へ変換するもの

- Map group/num/header/layout ID、pointer、connection、warp destination
- map section、region map、Fly/heal/Escape/dynamic warp
- tileset pointer/animation callback、music、object graphics ID
- Trainer ID/party/defeat state、Item ID/取得flag、wild header
- 全persistent flag/var、badge/HM/story state
- script/text/script specialとmap固有C処理

local object IDはmap内に閉じる限り座標と一緒に保持できる。global scriptが参照するIDだけを再割当する。hidden item flag幅が足りない場合は、KANTO専用scripted bg eventと拡張flagへ変換する。

## 原作からそのまま持ち込まないもの

- 御三家選択、図鑑受取、おとどけもの
- 原作ライバルとロケット団の全体進行
- 原作badge/HM gate、殿堂入り、エンディング
- シルフスコープ、ふえ、カードキー等の元flag体系
- ナナシマ解禁条件

NPC座標や演出を残す場合でも、V2のNPC再利用26件・重要アイテム置換24件をreview入力にし、呼び出す状態は統合版専用にする。

## 最初の二段縦切り

1. T11 importer spike:
   - 無害な小map 1枚を新IDへimport。
   - 開発terminalから往復。
   - layout/collision/tileset/warpのround-trip diffとVega map非変更を証明。
2. T13 product slice:
   - Vega側港NPC → Kanto terminal → クチバ市街。
   - PC/回復所、クチバジム、1 trainer、1 item、1 wild header、認定章1個。
   - save/load、reset、whiteout、即時帰還を通す。

## 完了条件

- Vega既存Map ID/header/warpの上書き0。
- 全Kanto destinationが解決し、意図しないunreachable/one-wayが0。
- 港は常時双方向で、save/load/reset/heal/whiteout/Escape後も帰還可能。
- 認定章、trainer defeat、item取得、story stateがVega側と衝突0。
- Map group予約値・signedness、local ID、tileset、music、object、trainer/item/species ID衝突0。
- linker allocation重複0、末尾reserve維持、Vega本編回帰PASS。
- 地方往復200回と長時間save試験PASS。
