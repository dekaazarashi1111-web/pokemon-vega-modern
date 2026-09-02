# USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT — 表示・NPC配置・全イベント／全NPC会話の全map監査

## 状態

- Queue ID: `USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT`
- Status: IN_PROGRESS
- Baseline: Stage 60 `60_wild_species_root_repair`
- 2026-09-02最新セッション切替時の実装checkpointと再開手順: `design/HANDOFF_STAGE61_DISPLAY_NPC_EVENT_AUDIT_20260831.md`末尾
- 本文書は2026-08-30時点の既知不具合メモである。ユーザー指示により、記録時点ではROM、生成器、配置manifestを修正しない。
- 後続修正では既知地点だけを個別補修せず、全map・全interaction owner・全NPC会話を対象に、同根不具合を列挙して共通の所有境界から根本修正する。

## 観測1: カントーのマップ名表示がトーホク名になる

- 再現地点: カントーのディグダのあな（physical map `97/36`、`97/37`、`97/38`）。
- 観測表示: 「ちえのどうくつ」。
- 期待表示: 「ディグダのあな」。
- 既知の物理根拠:
  - FireRedの`MAPSEC_DIGLETTS_CAVE`は数値ID `131`を使う。
  - 現行Vega側の同じ数値ID `131`は「ちえのどうくつ」の表示文字列を指す。
  - カントーimport後のmap headerがFireRed側の`regionMapSectionId`を保持したため、異なる名前空間の同値IDが表示時に衝突している疑いが強い。
- 横断監査範囲:
  - Stage 60の全678 physical map headerについて、`regionMapSectionId`、実際の表示文字列、logical map key、期待する地方／地名を列挙する。
  - カントーimport対象253 mapだけでなく、トーホク既存mapと後続追加mapも含め、同値ID衝突、誤った地方名、空文字、意図しない別名共有を検出する。
  - popup、タウンマップ、そらをとぶ等が別の名前取得経路を持つ場合はconsumerごとに確認する。

## 観測2: NPC自動配置後に会話対象が到達不能になる

- 再現地点: ディグダのあなB1F、physical map `97/37`。
- 再現対象: Stage 35で追加されたTrainer Archive NPC 5人。
- 最終配置:
  - 中央 local ID 1: `(42,40)`
  - 上 local ID 2: `(42,39)`
  - 左 local ID 3: `(41,40)`
  - 右 local ID 4: `(43,40)`
  - 下 local ID 5: `(42,41)`
- 実害:
  - 中央NPCの上下左右が永続NPCで埋まり、通常移動では隣接できないため会話・対戦を開始できない。
  - 周囲4人の勝利後scriptはNPCを移動・消去せず、その場でpost-battle会話へ移るため中央への導線は開かない。
- 既知の原因候補:
  - `tools/trainer_final/kanto_events.py`のArchive配置は、各NPCを追加した時点の空きtileで個別監査する。
  - 中央NPCを最初に配置した時点では隣接4方向が空いていたが、その後4方向へ別NPCを配置した後の最終到達可能性を再監査していない。
- 横断監査範囲:
  - Stage 60の全physical mapについて、import後に自動追加・再配置された会話NPC、trainer、受付、報酬host、field objectを最終object集合で再評価する。
  - 各interaction ownerに、入口から到達可能で、永続objectに占有されない会話隣接tileが最低1つあることを検証する。
  - 「戦闘勝利後に空く」という仮定を置かず、hide／remove／movement命令を実際に持つobjectだけを条件付き解放として扱う。
  - object単体のwalkable判定だけでなく、複数object追加後の囲い込み、通路封鎖、warp／coord／bg eventとの競合、視線による任意戦強制を検出する。
  - Stage 35 Trainer Archive以外の後続自動配置器も同じ最終状態validatorへ接続する。

## 観測3: 12ばんどうろの固定イベントが表示・進行・Species IDの複合不整合を持つ

- 再現地点: カントー12ばんどうろ、physical map `96/23`、local ID 15、座標`(14,70)`。
- 観測表示: 橋の上でラティアスに似た個体が寝ている。
- 期待実体: FireRedの`Route12_EventScript_Snorlax`が所有するカビゴン通行止めイベント。
- Stage 60実体:
  - objectは`graphics_id=109`、script root `0x081769BB`を使う。画面上の姿とsource roleが一致しないため、object graphics IDのFireRed／Vega名前空間衝突または変換漏れを疑う。
  - scriptはポケモンのふえのバッグ所持ではなくFireRed側`FLAG_GOT_POKE_FLUTE=0x023D`を読む。
  - Vega本編のD・Hだん離脱NPC（physical map `1/45`、local ID 9、座標`(22,24)`、script root `0x087700B1`）は同じItem 350「ポケモンのふえ」を渡すが、完了時に立てるflagは`0x119E`である。地方間のstory key adapterがないため、ベガ地方で正規入手した1個をカントー側が認識しない。
  - 固定戦闘命令は旧FireRedの`Species 143`を保持する一方、現行canonicalカビゴンは`Species 491`であり、現行`Species 143`はベガ固有のタツゴンである。条件だけを強制成立させても戦闘相手が正しいカビゴンになる保証がない。
- 想定仕様:
  - ポケモンのふえは両地方で2個配るのではなく、ベガ本編で入手したstory key 1個をカントーでも使用する。
  - 寝ているobjectへ通常入力で話しかけ、「はい」を選ぶと笛を使い、canonicalカビゴンとの固定戦闘へ進む。
- 横断監査範囲:
  - imported event scriptが参照するgraphics、flag、var、item、move、Species、trainer、map、sound等の全数値IDを、source名前空間から現行canonical IDへ変換したか列挙する。
  - 通行止め、固定遭遇、鍵アイテム、受取、交換、移動、trainer、Raid、postgame解禁を、取得元から利用先まで一続きのevent dependency graphで検証する。
  - 「所持Item」「取得済みflag」「source story flag」を混同せず、地方間で共有するstory keyは明示的なadapter仕様を持たせる。

## 観測4: カントーのフジ老人からポケモンのふえを受け取れない

- 再現地点: シオンタウン・ポケモンハウス、physical map `98/30`、local ID 1、座標`(3,3)`。
- Stage 60実体:
  - objectはsource label `LavenderTown_VolunteerPokemonHouse_EventScript_MrFuji`としてscript root `0x08181B5D`へ接続されている。
  - FireRed日本版Rev.0の同addressは`lock`／`faceplayer`から始まり、`FLAG_GOT_POKE_FLUTE=0x023D`を立ててItem 350を渡す。
  - Stage 60の同addressはVegaで上書きされた3命令のメッセージ表示／終了scriptから始まり、後方に残るItem付与命令へ到達しない。このため話しかけてもアイテム自体を受け取れない。
- 既知の原因候補:
  - `SOURCE_DIRECT_OBJECT_OWNER`の復旧が「source symbolと同じ数値addressを指す」「event bytecodeとしてdecode可能」であることだけを見ており、そのaddressのStage 60 bytecodeがsource labelの意味を保つかを検証していない。
  - Vega ROMで再利用・上書き済みのFireRed addressを直接ownerに戻す方式は、無関係な会話、空会話、到達不能な後続命令、誤った副作用を正常scriptとして受理し得る。
- 想定仕様:
  - 統合ROMではベガ本編の笛1個を共有するため、フジ老人から2個目を重複取得させない。
  - ただしフジ老人の会話とカントー側の進行は、既所持／未所持を含む明示仕様どおりに表示・分岐し、無関係なVega scriptや到達不能命令へ依存しない。
- 横断監査範囲:
  - 全`SOURCE_DIRECT_OBJECT_OWNER`、source直結のBG／coord／map script、共通scriptを対象に、source label、期待命令列、実root、到達CFG、表示文、side effectの意味同一性を検査する。
  - address一致をsource同一性の証明に使わない。必要なsource scriptは現行ROMへ再配置して内部pointerとIDを変換するか、統合仕様に沿うsemantic adapterとして再実装する。

## 観測5: 完全に空のメッセージを表示するNPCが複数いる

- ユーザー実機観測として、話しかけてもメッセージ内容が完全に空のNPCが複数存在する。
- 空文字列pointer、EOSだけ、空白／制御codeだけ、placeholder pointer、誤ったscript owner、未到達の本文、文字code／表示consumer不一致を原因候補とする。
- 静的にpointer範囲内・script decode可能・`msgbox`命令ありと判定するだけでは、実際に可視文字が表示されることを証明できない。

## 全NPC実表示テストの必須契約

- Stage 60の全678 physical mapから、scriptを持つ全NPC objectを列挙する。trainer、受付、shop、報酬、交換、story、固定遭遇、汎用会話、後続追加NPCを除外しない。
- NPCごとにphysical map、logical map key、local ID、座標、graphics、script root、owner分類、必要flag／var／item、会話分岐を機械可読catalogへ記録する。
- 各NPCの各到達可能会話分岐について、exact ROM上で合法な隣接tileから通常の方向入力＋Aボタンでinteractionを開始する。script関数の直接呼出しだけで合格にしない。
- 初回／完了後、trainer戦前／戦後、鍵アイテム未所持／所持、バッグ空きあり／なし、選択肢、解禁前／後など、表示文または副作用が変わる状態をbranch matrixとして実行する。
- 実際に画面へ出た文字列をUTF-8へdecodeしてNPC／branchごとに保存し、可視glyph数、終了状態、入力復帰、期待する意味、framebufferまたは同等のrender証跡を記録する。「何か出た」ではなく「何が表示されたか」を監査可能にする。
- 表示を意図するbranchは、空、空白だけ、制御codeだけ、未解決placeholder、文字化け、別NPCの文、source roleと無関係な文をすべてFAILにする。
- 意図的に無言のfield objectがある場合はNPCと混同せず、個別の仕様根拠付きallowlistへ限定する。未レビューの空表示は0件を完了条件とする。
- 会話後の`release`／入力復帰、object移動／消去、flag／var、Item増減、戦闘相手、warp、再会話時の状態も検証し、表示が正常でもsoftlock、無限再取得、進行不能、副作用欠落があればFAILにする。

## 根本修正の所有境界

- FireRed／Vega／CFRU／DPE／project追加領域のmap section、object graphics、event ID、script addressを別名前空間として扱い、manifest／relocator／validatorで明示変換する。
- source scriptはpointerの範囲内性ではなく、期待するCFG、表示、参照ID、side effectまでsource-to-runtime対応を証明する。
- 全mapの最終object集合、全event dependency graph、全NPC実表示catalogを共通validatorの入力にし、後続generatorも同じgateを必ず通す。
- 既知NPCだけのaddress差替え、個別flagの強制設定、個別座標移動、空文字を汎用文で埋めるだけの修正は禁止する。
- 横断監査で見つかった同根不具合は対象タスク内ですべて修正し、未解決件数0、未テストNPC／branch 0で完了させる。

## 別タスクでの完了条件

- [ ] 表示名、object graphics、NPC最終到達可能性、全event owner、全NPC実表示を機械可読レポートとして生成する。
- [ ] ディグダのあな2件、12ばんどうろ固定イベント、フジ老人Item付与不能、空会話NPCを再現する回帰fixtureを追加する。
- [ ] 全`SOURCE_DIRECT_*` ownerについて、source labelとStage 60実scriptのCFG／表示／参照ID／副作用の意味同一性を証明する。
- [ ] 全NPC・全到達可能会話branchをexact ROMでinteractionし、実表示文、入力復帰、side effectを記録する。空／誤文／未テストを0件にする。
- [ ] 鍵アイテム・flag・固定遭遇・trainer・warp等のevent dependency graphを列挙し、取得から利用まで進行不能経路を0件にする。
- [ ] ベガ本編で入手するポケモンのふえ1個をカントーで認識し、12ばんどうろで正しい姿・鳴き声・canonicalカビゴン戦へ進める。フジ老人から重複2個目は配らない。
- [ ] 同根の不具合を全mapから列挙し、個別address／flag／座標／文言の場当たり修正ではなく、名前空間変換・script再配置・最終配置・実表示validatorの所有境界で根本修正する。
- [ ] 修正後もトーホクの正規「ちえのどうくつ」表示、既存warp、story、trainer、item、Raid、event ownerを保持する。
- [ ] exact ROMで中央を含む全対象NPCへ通常入力だけで到達・会話でき、全分岐後に操作と進行が継続することを確認する。
- [ ] Stage 60入力、差分BPS、clean直接BPS、declared span、allocator overlap、private guardを対象タスクの完了gateで検証する。

## 記録時点で意図的に行わないこと

- Stage 60 ROM、BPS、saveの更新。
- map header、表示文字列table、NPC座標、object flag、event scriptの変更。
- ディグダのあな、12ばんどうろ、フジ老人、既知の空会話NPCだけを対象にした暫定的なすり抜け、消去、座標移動、flag強制、個別文言差替え。

## 2026-09-02 critical-release中間出口

- ユーザー指示により、元の全件監査を完了扱いにしないまま、先に「重大なゲーム進行不具合を検出しないStage61候補ROM」をWIP checkpointとして固定する。
- 既存strict build、oracle、期待値は削除・緩和・追認変更しない。候補生成は専用`CRITICAL_RELEASE` profileへ分離し、既定strict経路を維持する。
- 中間必須gateは、ROM再現性、宣言領域外変更0、boot／Continue／通常save／reload、移動／warp、可視会話、主要進行、鍵Item、固定遭遇、Gift／party／PC storage、両育て屋、戦闘後field復帰、crash／softlock／save破損／進行阻害0とする。
- 全678 map×全owner×全branch×runs=2、unused state完全列挙、全owner exact trace ordinal、coverage 0 omissionは`DEFERRED_AUDIT`として後続へ残す。strict実行で観測した非critical差異も期待値へ合わせず同分類で保存する。
- 中間判定正本は`reports/generated/stage61_critical_release_validation.json`。候補ROMは`build/stages/61_critical_release_candidate.gba`、SHA-256 `e736acd0828be5ccb583b85b4a07c940f08a7f880026c8e14bd4e520b0433669`。元taskの完了条件と`[>]`状態は変更しない。
