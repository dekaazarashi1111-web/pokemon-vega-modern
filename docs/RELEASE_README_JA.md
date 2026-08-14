# Pokémon Vega Modern — トーホク＋カントー二地方版 v1.3.5

これは非公式・非営利のファン制作差分パッチです。ROM本体は含みません。Nintendo、
Creatures、GAME FREAK、The Pokémon Company、およびVega原作者とは無関係です。
CFRUの利用条件に従い、本作を販売・有料配布・paywall化せず、任意寄付の対価にも
しないでください。

## 適用方法

1. 所有している無改変の「ポケットモンスター ファイアレッド」日本版Rev.0を用意する。
2. BPS対応patcherで `vega-modern-kanto-v1.3.5.bps` をそのclean ROMへ直接適用する。
3. 出力が32 MiBで、SHA-256が
   `7db577ce5a2db02c9a33b1d87338be756f42e5cfe0cbad49bac4ff7dada45cc8`
   であることを確認する。

入力ROMのSHA-256は
`1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486`。
Vega IPSやFactory UPSを先に適用したROM、別言語版、Rev.1には適用しない。元ROMと
saveは必ず別名でbackupする。patcherのsource/targetを逆に指定しない。

## ゲーム開始と二地方

新規saveを推奨する。Vega本編はトーホクで進み、シオウの3個目badgeとアーシア島
D・Hビル攻略の両方を終えると `KANTO_EARLY_ACCESS` が恒久解禁される。全国図鑑は
不要。最初の船はアーシア、再訪便はシオウ、カントー側はクチバの船員からいつでも
無料で帰還できる。

カントーは任意の固定高難度地方で、野生・trainerはLv.68〜100。player側へ合わせた
動的scaleは行わない。早期は認定章1〜4、Vega殿堂入り後に認定章5〜8とKanto League
が開く。253 physical map、180 layout、二地方のwild table、Gym 8戦と四天王・Champion
が同じ32 MiB ROMへ格納されている。未解決の通信施設・動的elevatorは進行停止を避ける
ため、クチバの安全地点へ戻す。

## 操作と既定QOL

- 文章は `TEXT_SPEED=INSTANT` が既定。制御code、選択肢、改ページ、明示waitは飛ばさない。
- ダッシュの `RUN_COURSE_FRAME_RATIO=0.625`、自転車の
  `BICYCLE_COURSE_FRAME_RATIO=0.375` が既定。tile eventは飛ばさない。
- 孵化演出は `HATCH_MODE=FAST`。`NORMAL / FAST / SKIP` を選べ、SKIPでも図鑑登録と
  nickname確認を残す。
- 全体学習装置は `EXP_SHARE=ON` が既定。戦闘経験値だけを分配する。
- 数量選択は `x1 / x5 / x10 / ALL`。アメ、栄養、ハネ、ふしぎなアメ、テラピース、
  coin、EV resetで共通利用する。
- Summary/PC欄はSELECTで通常/ジャッジ、L/RでIV/EVを切り替える。PCは既存listの
  文字入力で名前・type・ability検索、SELECT markerで複数選択する。一括移動・逃がし・
  持ち物回収は容量不足や禁止個体があれば全体rollbackする。
- Field PCはD・Hビル攻略後、許可された町・道路だけでfield menuから開く。battle、gym、
  dungeon、league、event中は開かない。
- タマゴバスケットはカントー預かり屋依頼後、許可mapのfield menuでON/OFFする。
  現在預けている2匹を親として256歩ごとに判定し、預かり屋と共有する5個queueへ入れる。
- 自動戦闘はD・Hビル攻略後、通常random野生戦だけで選べる。trainer、固定・story・
  legendary・色違いでは通常戦へ戻り、開始前と各turnにcancelできる。

### HMフィールド能力

Vega既存のHM01〜HM08（だいじなものItem 339〜346）をバッグで所持すると、対応する
フィールド能力を利用できる。HM05はフラッシュ、HM08はダイビング。バッジ、手持ち数、
対応技を覚えたポケモン、技枠、技の適性は解禁条件にしない。いあいぎり対象、なみのり可能な
水辺、フラッシュ対象map、follower制約など、実行地点の安全判定は従来どおり残る。
フィールド能力を使ってもポケモンの技は書き換えない。

### 戦闘規則と技選択表示

戦闘規則は固定CFRU-JP commit `e24a16fe39e27ae162faf5b78596d1f3df18489d` が単独で所有する。
麻痺は素早さ1/2・行動不能1/4、眠りは付与時2〜4 turn、凍りの自然回復は1/5。毒は最大HPの
1/8、やけどは1/16、猛毒は1/16から段階増加する。急所倍率は1.5倍で、天候は通常5 turn、
延長道具で8 turn。雨・晴れの炎/水補正も同じCFRU規則を使う。

戦闘中の技選択画面には、その時点の実タイプと相手ごとの有効度を表示する。等倍・タイプ不一致は
元CFRUどおり追加表示なしとし、「こうかばつぐん」相当、半減、無効、タイプ一致（STAB）を
色分けする。ボタン設定が通常の`HELP`でも`L/R`でも、戦闘中のLで技名・接触・威力・命中の
詳細を開閉できる。FR由来の全画面HELPは戦闘中だけ開かず、fieldでは従来どおり利用できる。
ダブルでは対象ごとに計算し、Stellarとテラバーストのタイプ変更も実damage計算と同じ判定を使う。
通常野生、trainer、double、Factory Trial、Raidのいずれでも同じUIを使う。

### わざメモリー

1個目のバッジ報酬として、だいじなもの「わざメモリー」（Item 347）を受け取る。既存saveで
報酬地点を通過済みの場合は、シオウの技管理NPCが未所持分を補う。道具またはシオウ・カラスバの
NPCから同じmenuを開き、「おもいだす」「わすれる」「タマゴ技」「やめる」を選べる。

- おもいだす: 現在Lv以下のレベル技（Lv.0/1を含む）を無料で習得する。既に覚えている技は候補外。
- わすれる: 無料。HMも削除できるが、最後の1技、タマゴ、一時form専用技、戦闘・施設・Raid中は
  拒否する。PP Up段階は技slotと一緒に移動し、ケルディオ等のform連動も更新する。
- タマゴ技: D・Hビル攻略後に解禁。Vega殿堂入り前はものまねハーブ所持と空き技枠を必要とするが、
  ハーブは消費しない。殿堂入り後は無料で、空き枠がなければ通常の技選択で入れ替える。

キノコ、ものまねハーブ、その他の道具はどの技管理でも消費しない。PCの技思い出し
（`PC_RELEARN` / `VEGA_BADGE_2`）も残るが、携帯できるわざメモリーは1個目のバッジから使える。

### release feature matrix

`release default` と `unlock` は同梱 `FEATURE_MATRIX.csv` の値そのもの。`DEBUG_GIFT=OFF`
で、release buildでは利用できない。

| feature key | release default | unlock |
|---|---|---|
| `TEXT_SPEED` | `INSTANT` | `UNLOCK_GAME_START` |
| `HATCH_MODE` | `FAST` | `UNLOCK_GAME_START` |
| `RUN_COURSE_FRAME_RATIO` | `0.625` | `UNLOCK_GAME_START` |
| `BICYCLE_COURSE_FRAME_RATIO` | `0.375` | `UNLOCK_BICYCLE` |
| `EXP_SHARE` | `ON` | `UNLOCK_BADGE_1` |
| `EXP_CANDY` | `ENABLED` | `UNLOCK_DH_BUILDING` |
| `QUANTITY_UI` | `ENABLED` | `UNLOCK_GAME_START` |
| `MODERN_BREEDING` | `ENABLED` | `UNLOCK_DAYCARE` |
| `IV_EV_COMPACT` | `IV` | `UNLOCK_GAME_START` |
| `HYPER_TRAINING` | `SV_STYLE` | `UNLOCK_BADGE_7` |
| `MINT_ABILITY_ITEMS` | `ENABLED` | `UNLOCK_DH_BUILDING` |
| `EGG_PC_QUEUE` | `ENABLED` | `UNLOCK_DAYCARE` |
| `TM_REUSE_LICENSE` | `DISABLED` | `TM_LICENSE_UNLOCKED` |
| `ENCOUNTER_PROFILE` | `NORMAL` | `RESEARCH_PROFILE_UNLOCKED` |
| `PC_SEARCH` | `ENABLED` | `UNLOCK_GAME_START` |
| `PC_MULTISELECT` | `ENABLED` | `UNLOCK_GAME_START` |
| `PC_BULK_MOVE_RELEASE` | `ENABLED` | `UNLOCK_GAME_START` |
| `FIELD_PC` | `ENABLED` | `VEGA_DH_CLEAR` |
| `PC_RELEARN` | `ENABLED` | `VEGA_BADGE_2` |
| `PC_HELD_ITEM_BULK` | `ENABLED` | `VEGA_DH_CLEAR` |
| `EGG_BASKET` | `ENABLED` | `KANTO_DAYCARE_QUEST` |
| `AUTO_BATTLE` | `ENABLED` | `VEGA_DH_CLEAR` |

経験アメXS/S、能力capsuleと一部mint、全EV resetはD・H攻略後。power系は5個目badge、
アメM反復は6個目、アメLと銀冠は7個目、全mint・特性patch・単能力EV reset・標準育成店は
8個目。アメXLはVega殿堂入り時に一度、Kanto League後に反復解禁される。王冠はSV式で
実IVを変えず戦闘時だけ31相当。PC技思い出しは2個目badge後、わざメモリーは1個目badge後から無料。

## Battle Factory

クチバの受付NPCからTrialを始める。固定CFRU-JP生成器がLv.50の重複なしrental候補6体を
毎回ランダム生成し、既存party画面で任意の3体を選ぶ。single 3v3を3戦し、1・2戦目の
勝利後は相手側からランダムに保持された1体と、自分で選んだ手持ち1体を交換できる。
各戦後は全回復し、3連勝で9 BPを得る。棄権・敗北・選択cancel・reset後は参加前partyの
全600 byte（HP・PP・状態・持ち物を含む）を復旧し、rentalと相手はseenだけを更新する。
連勝記録とBPはsector 31へ保存する。BP shopと施設外の調査NPCについては、進行条件、
価格、支払い/credit、空き容量、再開用個体のcontent定義を保持する。

v1.3.5で受付から実際に遊べるよう結合済みなのはTrialだけである。下表のStandard / Full /
Master、BP shop、施設外報酬遭遇は進行・content定義と回帰fixtureを保持しているが、実ROMの
受付・NPCへはまだ接続していない。

| tier | unlock | 主な形式・mechanic | v1.3.5 runtime |
|---|---|---|---|
| Trial | `KANTO_EARLY_ACCESS` | single 3v3×3、一般rental、gimmickなし | 接続済み |
| Standard | `FACTORY_STANDARD`（Vega 5個目badge） | single 3v3 / double 4v4、交換、Mega | 未接続 |
| Full | `FACTORY_FULL`（Vega殿堂入り） | single/double/Little/Monotype/OU等、Mega/Z | 未接続 |
| Master | `FACTORY_MASTER`（Kanto League clear） | 49/100連勝、region mix/Ultimate、Mega/Z/Tera/Dynamaxから入場時1つ | 未接続 |

通信相手が必要なlink multiは対象外。NPC partner multiは利用できる。Mirageは持込partyと
仮想itemを使う攻略施設、Factoryはrental交換施設であり、save owner・連勝・報酬を共有しない。

## Trainer AI、再戦、遭遇、Raid

固定CFRU-JP commit `e24a16fe39e27ae162faf5b78596d1f3df18489d` のAIを使う。
既定knowledge modelは `GLOBAL_FIXED_BEFORE_DECISION`。一般trainerは `AI_BASIC`、強敵・Gymは
`AI_SEMI_SMART`、boss・League・facilityは `AI_FULL_SMART`。本編を一律level scaleせず、
trainer party、技、持ち物、IV/EV、profileを進行帯ごとに横方向へ強化している。

v1.1.0以降は「トレーナー再設計V4」の141戦・610体を正規化し、Vega本編に実在する648個の
Trainer IDへ編成を結合した。主要人物、Gymと既存Gym NPC、一般trainer、バトルサーチャー
再戦が対象で、Mirageと未指定Sphere枠は維持する。V4のAI rank 1は `AI_BASIC`、rank 2～3は
`AI_SEMI_SMART`、rank 4～5は `AI_FULL_SMART` へ対応し、独自AI段階は追加しない。
Species、level、持ち物、4技、IV下限、trainer itemはROMへ反映済み。性格・特性・EV指定と
gimmick triggerは現行の通常Trainer party ABIに直接欄がないため設計台帳に保持し、既存の
CFRU生成規則と1戦1gimmick policyを変更しない。追加event枠を必要とする21戦は既存戦へ
誤接続せず台帳のみとし、実在する本編戦はすべて決定的に対応付ける。

Vega殿堂入り、認定章4、Kanto League clearでトーホク強豪再戦I/II/IIIが順次開く。
League I、League II、Final Leagueも前段clear flagで順番に開き、FinalはLv.100。
通常出現の既定は `NORMAL` で元tableを維持し、殿堂入り後に `RESEARCH` を任意選択できる。
RESEARCHは高IV・隠れ特性等の調査枠で、NORMALを置換しない。

MegaはVega殿堂入り、Zは後半認定章、Tera/Dynamax storyはKanto League clear後。
高難度RaidはVega殿堂入り＋認定章4で解禁し、固定CFRU battle coreでshield、partner、報酬、
共有一回捕獲stateを処理する。Raid後の通常戦へ一時stateを持ち越さない。

## Save

詳細は `SAVE_COMPATIBILITY.md`。新規saveを推奨する。条件を満たす旧Vega battery saveだけを
一回性migrationし、未知magic/version、checksum不正、予約領域汚染は拒否する。emulatorの
savestateはruntime内部状態を固定するためversion間で引き継がず、ゲーム内saveから再開する。
Factory参加中や報酬遭遇中の電源断は、最後にflashへ確定したtransactionから復旧する。

既知の仕様上の除外は `KNOWN_ISSUES.md`、第三者source・作者・利用条件は `CREDITS.md`、
全入力/source pinとbuild情報は `BUILD_METADATA.json`、ファイルhashは `CHECKSUMS.txt` を参照。
