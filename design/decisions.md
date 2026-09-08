# decisions.md（追記のみ）

重要な設計判断、根拠、代替案、影響タスクを記録する。既存項目は削除・書換えず、後続ADRで置き換える。

## 2026-08-12 — D-001: パッチ重ね当てではなくソース移植

- 決定: Factory UPSをVegaへ直接適用せず、Vegaを母体にDPE-JP/CFRU-JP公開ソースを移植する。
- 根拠: 両パッチは269区間・775 byteを直接二重変更し、厳密比較では584 byteが異なる最終値になる。直接競合外にもhook、repoint、RAM、SaveBlock、ID依存がある。
- 却下: IPS/UPSの順次適用、checksum無効化、重複byteだけの片側優先。
- 影響: T00〜T10、T17、T18。

## 2026-08-12 — D-002: Vega既存IDをcanonicalとして固定

- 決定: Vega既存のSpecies IDとMove ID 0〜511を移動しない。追加IDはmanifestへ登録し、生成物だけが数値を参照する。
- 根拠: Vegaのストーリー、トレーナー、野生、進化、イベント参照を一括で壊さず、CFRU/DPE側を対応表で適応できる。
- 影響: T02、T04、T05、T07、T09、T12、T16。

## 2026-08-12 — D-003: カントーは殿堂入り後の別名前空間

- 決定: 原作FireRedのカントーをVegaクリア後の地方として復活させ、Map/Trainer/Flag/Varを `KANTO_*` 名前空間で新規割当する。最初の縦切り入口はクチバ港とする。
- 根拠: Vega本編の進行状態を維持しつつ、原作地形・NPC配置・ジム構造を再利用できる。
- 影響: T11、T13〜T17。

## 2026-08-12 — D-004: 地形を活用し、グローバル状態は再定義

- 決定: カントーの地形、NPC座標、ジム構造は活用できるが、原作ストーリー依存script、badge、trainer、item、warp、flag、varはVega向けに再定義する。
- 根拠: FireRedのグローバル状態を復元するとVegaの同一ID・イベントと衝突するため。
- 影響: T11、T13〜T16。

## 2026-08-12 — D-005: 2026-08-12時点のGitHub HEADを上流pinに採用

- 決定: CFRU-JP `e24a16fe39e27ae162faf5b78596d1f3df18489d`、DPE-JP `10ff98c85ebf37ab5cb39a41b6e9b50f06efb19e`、pret/pokefirered `c75f352304d529f6ba92d4f74b9cf8b5c3810788` を固定する。
- 根拠: 各リポジトリの既定ブランチHEADをGitHubへ直接照会した結果。DPE設計CSVの旧基準 `520937c0959e2a1be57771d1dfee9f6fee806c7e` は現HEADの1コミット前で、差分は `src/Back_Pic_Coords_Table.c` の1行のみだった。
- 代替: 設計CSVの旧DPE pinを実装pinに使う案。最新版を望むユーザー方針により不採用。
- 影響: T00〜T02、T07、T09、T12。

## 2026-08-12 — D-006: タスク状態の正本を一本化

- 決定: `design/tasks_next.md` を唯一の状態正本、`tasks/task_graph.json` を依存関係正本、`tasks/T*.md` を完了条件正本とする。`state/task_status.json` は生成ミラーにする。
- 根拠: プレイブックと既存運用の二重状態更新によるdriftを防ぐため。
- 影響: 全タスク、`scripts/taskctl.py`、検証。

## 2026-08-12 — D-007: 受領した統合設計データはreview状態から開始

- 決定: `design/imported/VEGA_CFRU_DPE_統合設計/**` は受領時点の不変参照とし、個別レビュー・修正後にmanifestや実装用データへ昇格する。
- 根拠: パッケージ整合性はPASSしたが、フォームを区別できない進化条件、意味重複、全国番号の小数文字列、救済道具の参照欠落などが独立監査で見つかった。
- 影響: T02、T05、T07、T09、T12、T16。

## 2026-08-12 — D-008: 効率化はキャッシュ・並列化・生成で行う

- 決定: 入力hash・source commit・tool versionが同一の成果は再利用し、独立作業をファイル所有権付きで並列化し、ID/表はgeneratorで作る。検証ゲートは省略しない。
- 根拠: 長期開発での重複解析、セッション再開コスト、手作業の転記ミスを抑えるため。
- 影響: 全タスク。

## 2026-08-12 — D-009: V2二地方生態版を設計の優先資料にする

- 決定: `design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/**` を、完成像・進行・二地方生態・イベント設計のactive review資料とする。V1は来歴保存専用にする。
- 根拠: V2はトーホク49地点、カントー47地点、541系統×2地方、追加イベント34件を定義し、JSON/SHA manifest 47/47が一致した。
- 制約: V2は設計仕様書であり、進化重複、フォーム識別、ID型、道具参照、未確定templateをT12等で解消するまでCSVを実装正本にしない。上流実装pinはV2記載の旧DPE commitではなくD-005を正とする。
- 置換: D-007の対象範囲をV2へ拡張し、V1を新規判断に使わない。
- 影響: T02、T05、T07、T08〜T17。

## 2026-08-12 — D-010: 元FireRedからカントー本土を復元し二地方を往復可能にする

- 決定: clean BPRJ Rev.0と固定済みpokefireredを原資産として、カントー本土の地形・建物・接続・NPC座標・ジム構造を新規 `KANTO_*` 名前空間へ複製する。初回殿堂入り後にクチバへ到着し、トーホクへ常時帰還できる双方向移動を必須にする。
- 根拠: Vegaに上書きされた原FireRed IDへ戻すより、新規Map/Flag/Var/Trainer/ItemFlagへ変換する方がVega本編を保護し、二地方を同居させられる。
- 制約: 原作ストーリー状態は再利用しない。V2の47地点は生態設計単位であり、全建物・階層を含むraw map scopeはT11で別途確定する。ナナシマはV2本体では予約に留める。
- 影響: T02、T08、T11〜T17。

## 2026-08-12 — D-011: カントーをVega中盤から任意解禁する

- 決定: カントーへの渡航はVega初回殿堂入りを必要とせず、シオウの3個目バッジ取得後、アーシア島D・Hビルの初回攻略完了を概念条件として恒久解禁する。実装はT02で確定するVega実flagから一度だけ `KANTO_TRAVEL_UNLOCKED` を設定し、以後の渡航でVega進行flagを再判定しない。既存の殿堂入り済みsaveには移行時に渡航権を付与する。
- 二段階進行: 早期解禁後はクチバ、初期回廊、高レベル生態、要求認定章数0〜4のジム・調査を任意攻略できる。Vega殿堂入りは後半認定章、カントーリーグ、終盤伝説、二地方共鳴だけを解禁する。
- 難易度: V2のLv.68〜100の固定帯を維持し、動的party scalingは使わない。高レベル個体の捕獲・持ち帰りによる戦力面のsequence breakは、任意ルートの報酬として許容する。Vegaの物語・warp・HM・重要道具flagを飛ばす進行sequence breakは禁止する。
- 安全条件: 初回乗船前に推奨Lv.65以上の警告を出す。船上戦は任意・勝敗不問とし、クチバのPC/回復と帰還船までに強制戦闘やfield move要求を置かない。クチバからの無料帰還は認定章、所持金、RTC、story flagに依存させない。
- 状態分離: `KANTO_TRAVEL_UNLOCKED`、`KANTO_VISITED`、`KANTO_CERT_*`、`KANTO_STORY_*`、`VEGA_HALL_OF_FAME` を別状態にし、Kantoのfield permitはTohokuのHM判定を変更しない。
- 置換: D-003とD-010の「殿堂入り後に解禁」という時期だけを本決定で置き換える。別名前空間、clean BPRJからの復元方式、常時帰還は維持する。V2受領原本は編集せず、T12の正規化層で殿堂入り前提をoverrideする。
- 影響: T02、T08、T12〜T17、リリース回帰。

## 2026-08-12 — D-012: 現代育成と高速操作QOLをrelease scopeにする

- 決定: `docs/QOL_POLICY.md` のQOL-A/QOL-Bを全て実装対象にする。文章は既定 `INSTANT`、ダッシュはVega比25%以上、自転車は50%以上の移動時間短縮を受入条件とする。現代式孵化、経験アメ、複数使用、IV/EV表示、全体学習装置、タマゴPC/queue、mint、特性道具、SV式Hyper Training、PC検索・一括操作、field PC、タマゴバスケット、自動戦闘を含む。
- 既定値: ジャッジは最初から利用可能でタマゴIVも数値表示する。王冠は元IVを書き換えず「きたえた！」を別保存する。孵化演出は既定FAST、技思い出しは2個目badge後から無料、まるいおまもりは100種捕獲またはカントー預かり屋questの早い方で解禁する。
- 実装順: T01/T02で固定upstreamとVega hookを実証し、T05〜T10でQOL-Aを統合、T12/T15/T16で解禁と供給、T17の全回帰前にQOL-Bを統合し、T18で配布説明を完成させる。最初のカントー縦切りを高度PC改造で待たせず、DAGは変更しない。
- 根拠: 育成の反復作業と移動・文章待ちを大幅に減らし、二地方・1025種規模でも遊びやすくするため。添付内で分岐していた案は、SV準拠と利便性を優先して上記へ固定した。
- 影響: T01、T02、T05、T06、T08〜T10、T12、T15〜T18。

## 2026-08-12 — D-013: READYタスクの先頭順は推奨にする

- 決定: 正本IN_PROGRESSは1件、DAG依存は維持するが、依存READY候補の先頭以外も `taskctl.py start` で開始できる。`PRIMARY` は推奨、`PARALLEL_PREP` は他のREADY候補として扱う。
- 根拠: toolchainや長時間buildを待つ間にT02/T12など独立タスクを正本化でき、固定順による遊休をなくせる。Git上の状態一貫性は単一IN_PROGRESS、依存、task commitで維持できる。
- 検証: 反復中は対象test、タスク完了時は標準ゲートを内包する既定verifyを1回実行し、同じsuiteの直列二重実行を避ける。
- 置換: D-006の正本構造とD-008の効率原則は維持し、`design/tasks_next.md` の並びを強制開始順としていた運用だけを置き換える。
- 影響: 全タスク、`scripts/taskctl.py`、再開prompt、並列運用。

## 2026-08-12 — D-014: UI追加と新規イベント演出を最小化する

- 決定: 採用済み機能は維持するが、新しいfull-screen UI、独自window、装飾asset、長いcutscene、minigame、多段questを原則作らない。既存summary/PC/list/数量選択/技思い出し/Options、既存NPC/端末と標準script commandを薄いadapterで再利用する。
- UI: IV/EVは既存情報欄のcompact切替、複数使用は既存数量選択、PC高度機能は標準list/文字入力/SELECT marker、field PCは既存PC画面、自動戦闘は簡単な既存menu commandで実装する。
- イベント: QOL解禁と追加イベントは `SIMPLE_EVENT` を既定とし、短い会話、条件check、flag、標準reward/battle/warpだけで完了させる。元Vega/FireRedの既存gym puzzleや地形仕掛けは再利用する。
- 根拠: UI・演出制作をcritical pathから外し、機能、二地方化、再現性へ実装時間を集中するため。
- 影響: T09、T10、T12、T15〜T17、content生成、release UI。

## 2026-08-12 — D-015: 固定CFRU-JP AIで横強化と段階再戦を実装する

- 実装元: source-lock済みCFRU-JP commit `e24a16fe39e27ae162faf5b78596d1f3df18489d` の `src/Battle_AI/**`、AI hook、battle controller、damage/accuracy、switch/item/gimmick判断を正とする。別AI engineや浮動HEADは導入しない。
- 本編方針: Vega初回殿堂入りまでは一律level scalingを使わず、一般trainerは元難度を基準に `AI_BASIC` / `AI_SEMI_SMART` を選び、ジム/幹部/ライバル/初回リーグは編成、役割、性格、EV/IV、特性、持ち物と進行別AI profileで横方向に強化する。全bossを無条件に最高AIへせず、既存の象徴的なVega個体と役割を保護する。
- AI知識: 固定CFRU-JPの既定knowledge modelをそのまま移植・監査し、未公開情報を遮断する独自AI再設計は行わない。難度の公平性は合法な技/道具/育成値、回避や確率発動への過度な依存禁止、決定論fixtureで担保する。
- レベル: 1個目badge後から全体学習装置を既定ONにするD-012を維持し、中盤以降は連続saveの実測に基づき一般trainer、boss、野生をmap/batch単位で最大+0〜3調整できる。全trainer一括補正、party連動scale、CFRUのglobal Hard/Expert化は採用しない。KantoのLv.68〜100固定任意帯も維持する。
- 段階再戦: League Iは `VEGA_HALL_OF_FAME`、League IIは `VEGA_HALL_OF_FAME && KANTO_CERT_4 && LEAGUE_I_CLEARED`、Final Leagueは `KANTO_LEAGUE_CLEAR && SPHERE_COMPLETE && LEAGUE_II_CLEARED` で順番に解禁する。通常/地方強豪の第3再戦はKanto League後に解禁してよいが、Lv.100 leagueはFinal条件まで出さない。既存の即Lv.100強化leagueはFinalへ後送りして再利用する。
- 道具: `docs/QOL_POLICY.md` のfirst-availability/repeatabilityを後退させない。ここでの段階条件は追加の対戦道具、Mirage/Sphere報酬、TM再利用license、ギミック、UB/Paradoxの供給を制御し、既に解禁済みの育成QOLを再ロックしない。
- 施設: MirageはLv.100の育成済み持込施設、Factoryはrental施設として分離する。双方で相手の持ち物を盗難・持出しできず、報酬、記録、通貨も相互更新しない。
- 影響: T01、T02、T06、T08、T10、T12、T15〜T18、trainer/encounter manifest、回帰試験。

## 2026-08-13 — D-016: V3技調整をVega固定IDへ優先適用する

- 決定: `VEGA_CFRU_DPE_技調整設計_V3` の技現代化61件とVega独自技70件をT04のactive入力にする。Vega Move ID 0〜511を固定し、NFKC完全一致するCFRU identityを対応、未収録551技を512〜1062へappendする。
- 同名衝突: Vega ID 470「くらいつく」は「ソウルバイト」/`MOVE_KEY_SOUL_BITE`、ID 509「ねらいうち」は「ダークスナイプ」/`MOVE_KEY_DARK_SNIPE`へ変更する。CFRU公式 `MOVE_JAWLOCK` / `MOVE_SNIPESHOT` は別技としてappendする。
- 効果: V3独自技70件の自由記述を固定operation列へ構造化し、Vega legacy effect pointerを来歴に保持したcompile済みhandler/dispatchを生成する。CFRU側の未知effect IDは流用せず安全なbase effect 0を使い、T06がbattle runtime callbackを接続する。
- 文字列: 技名・説明はUTF-8 literalではなくゲームcharmap byte＋`0xFF`終端で生成する。CFRU外部説明354件はhash固定clean ROMのrooted pointerから抽出し、`@0x...` placeholderを許可しない。
- 影響: T04、T06、T09、T12、T16、全技manifestとbattle smoke。

## 2026-08-13 — D-017: Type・Ability・Itemを意味契約付きの配置前ID modelにする

- 決定: Vega Type 0〜17、Ability 0〜77、Item 0〜374を未使用slot込みで固定し、固定CFRU-JP/DPE-JPをType 25、Ability 312、Item 999の連続canonical IDへ解決する。T05はROM stageを作らず、生成manifest/C/JSONをT06がstage 04と統合する。
- 意味同一: Itemは同じsource ID、NFKC名、説明、hold/field/battle ABI、pocket、`unk19`、callback、secondary IDが一致した161件だけを自動対応する。表示だけ異なる明示identity 3件と、別entityとして保持する例外には根拠を`config/id_spaces.json`へ固定し、証明できない613件はCFRU rangeへappendする。
- 直交契約: ItemType、進化石/進化道具、ball kind、pocket、icon/palette、説明、hold/field/battle effectとcallback、`unk19`、consume/target/supply/runtime bindingを別fieldとして保持する。opaque byteや単一roleへ意味を潰し込まない。
- Runtime受渡し: T05の生成Cは配置前semantic tableであり、上流のpositional runtime ABI表ではない。T06で実`struct Item`/icon表999行とAbility名/説明312行をcanonical順に再生成し、全consumerのrepoint、全行round-trip、source ID直index不在をhard gateとする。832 ID分の`itemObtainedFlags`はT08でresize/translationするまで関連featureを有効化しない。
- 追加type/QOL: FairyとStellarは表示icon、RGB/BGR555色、25×25相性、特殊規則をactive契約とし、Stellar runtimeはT06でbindする。経験アメ5種と単能力EV reset 6種は末尾988〜998へ置き、既存育成道具を含む45 QOL効果をstable keyへ固定する。
- 影響: T05、T06、T07、T09、T10、T12、T16、Type/Ability/Item参照と生成表。

## 2026-08-14 — D-018: 本編トレーナー再設計V4を既存IDへ決定的に結合する

- 決定: V4の141戦・610体をcanonical Species/Move/Itemへ厳密解決し、Vega本編に実在する
  Trainer IDへ明示または決定的policyで結合する。主要人物は名前・進行段階・既存party、Gym
  trainerは実map上のNPC、一般・バトルサーチャーは元level/class/double属性を根拠にする。
- AI: V4独自の6段階AIは作らず、固定CFRU-JP commit `e24a16f...` の既存段階を流用する。
  rank 1はflags 1、rank 2〜3はflags 3、rank 4〜5はflags 5とする。
- ABI: 通常TrainerMonへSpecies、level、held item、4技、IV下限を入れ、Trainer recordへ
  trainer itemとAI flagsを入れる。名前、class、gender/music、pic、double flagは保持する。
  通常ABIに欄のない性格・特性・EV・個別gimmick triggerは入力台帳に保持し、広範なbattle
  core改造は行わない。
- 安全境界: Mirageと未指定Sphereを一般対応から除外する。追加event/Trainer IDのない21戦は
  推測で既存戦へ上書きせずcatalog-onlyとし、実イベントが追加された時だけ明示bindする。
- 配置: stage 17のrepoint済みTrainer tableをexpected input hash付きでin-place更新し、共有party
  blobだけを中央allocatorのintegration_modulesへ追加する。元ROM、ZIP、stage 17は変更しない。
- 影響: stage 19、v1.1.0 release、Vega本編trainer、release文書・検証。

## 2026-08-14 — D-019: Factory Trialを小さい実ROM縦切りとして結合する

- 決定: 文書・host fixtureだけだったFactory機能から、クチバ受付で実際に開始できるTrialを
  stage 20へ結合する。固定CFRU-JP生成器のLv.50候補6体から既存party UIで3体を選び、
  single 3v3を3戦する。1・2勝後は実対戦相手から保持したランダム1体と任意の手持ち1体を
  交換でき、各戦後全回復、完走9 BPとする。
- 所有権: 入場前party 6×100 byteをversioned ledgerへ保存し、完走、敗北、辞退、cancel、
  save/reset後のクチバ復帰でexact復元する。rentalと対戦相手はseenだけを更新し、caught、
  通常trainer報酬、Mirage状態へ波及させない。
- 保存: CFRU-JPのsector 31 writeを利用する。2,048-byte rollback像はGBA stackへ置かず、
  予約済みEWRAM `0x0203E400..0x0203EC00`へ固定する。host検証では従来どおりstack-localを使う。
- リリース境界: v1.2.0で実ROM受付から保証する施設modeはTrialである。Standard / Full /
  Master、BP shop、施設外報酬遭遇は進行・content manifestとfixtureを保持するが、実受付へは
  未接続として明記し、実装済みとは表示しない。
- 検証: 重いfresh checkout全再構築はユーザー指示により繰り返さず、stage 20の決定論build、
  中央allocator、物理NPC/script graph、libmGBA exact-ROM 2 process、BPS完全往復へ絞る。
- 影響: stage 20、save runtime、v1.2.0 release、Factory文書・検証。

## 2026-08-14 — D-020: QOL統合releaseをstage 25と単一save境界で確定する

- 決定: 初戦防御、HM field能力、固定CFRU-JP battle rules、技選択UI、わざメモリーを
  stage 20→25の順に結合し、stage 25をv1.3.0の唯一の最終ROMとする。各旧stageのfixtureを
  転記せず、Kanto/QOL-B、Factoryと全QOL runnerへ同じstage 25を渡して再観測する。
- 保存: stage 20以後にserialized fieldを追加しない。HM解禁はVega HM Item 339〜346のバッグ
  所持から導出し、わざメモリーの通常／タマゴ技modeはvolatile EWRAM 1 byteだけを使う。
  v1.2.0 battery saveは互換とし、version間のemulator savestateは引き続き対象外とする。
- 配布: clean FireRed日本版Rev.0用BPS、32 MiB BPRJ最終ROM、固定順・固定時刻ZIPをv1.3.0へ
  更新する。archiveへROM、save、元IPS/UPS、private pathを含めない。
- 検証: 通常worktreeでは検証済みstageをhash一致時に再利用する。全chainの重い再構築は
  annotated tag `v1.3.0` の隔離fresh worktreeで最後に1回だけ行い、final/BPS/ZIPのbyte一致を
  release完了gateとする。
- 影響: stage 25、v1.3.0 release、save互換性、release文書・統合回帰。

## 2026-08-14 — D-021: fresh rebuildで検出した配置依存をv1.3.1で除去する

- 判定: ローカルannotated tag `v1.3.0` の隔離fresh checkoutは、T05生成modelの
  古いfingerprint pinをT06が拒否したためrelease gate不合格とする。tagは移動・削除せず、
  配布・pushも行わない。
- 原因: QOL追加時に検証済みstageを再利用した際、T05→T06の来歴pinと、再リンクで
  変化するCFRU絶対addressを参照する下流overlay/runnerの契約がクリーン再構築に
  追従できていなかった。
- 修正: T05/T06の来歴を現行入力で再固定し、Factory、HM、battle rules/UI、
  わざメモリーの実addressをhash検証済みT06 offsetsから解決する。初戦防御は
  T06 sourceに統合済みの場合を明示的なzero-patch契約にする。
- 配布: 修正済みsourceは `v1.3.1` に分け、そのtagged sourceの隔離fresh checkoutで
  final/BPS/ZIPがbyte一致した場合に限りrelease完了とする。
- 影響: T05〜T07、T09、T16〜T17、stage 19〜25、v1.3.1 release、来歴・配置検証。

## 2026-08-14 — D-022: local toolの固定inventoryをv1.3.2で同期する

- 判定: annotated tag `v1.3.1` のfresh checkoutは、上流ビルドを開始する前に
  `tools/mgba_ai_fixture_runner.c` の実hashとT01 inventoryの固定hashが不一致で停止した。
  この候補もrelease gate不合格とし、tagを移動・削除せず配布・pushしない。
- 修正: runner本体、`config/ai_fixture_inputs.json`、`config/upstream_inventory.json`、
  T02 state inventoryが持つrunner/config hashを同一byteへ同期する。戦闘ロジックと
  最終ROM byteは変更しない。
- 再試行: 前回は重い上流build前にfail-closedしたため、`v1.3.2` tagged sourceで
  隔離fresh rebuildを再試行し、final/BPS/ZIP byte一致を最終gateとする。
- 影響: T01/T02来歴、AI fixture、v1.3.2 release、fresh-checkout再現性。

## 2026-08-14 — D-023: T06の可変計測値をUI ABI pinから除外する

- 判定: annotated tag `v1.3.2` のfresh checkoutはstage 23まで同一ROMを再構築したが、
  `build/stages/06_battle_core.json` 全体SHAが通常worktreeと異なるためbattle UI gateで停止した。
  この候補もrelease gate不合格とし、tagを移動・削除せず配布・pushしない。
- 原因: T06メタデータは来歴として各上流runの `elapsed_seconds` を保持する。UI実装はその値へ
  依存しないのにJSON全体SHAを固定していたため、正常な実行時間差をABI差として誤判定した。
- 修正: battle fingerprint、stage 06 ROM、offsets、linked objectのSHAだけをUI入力契約にする。
  経過時間が変わっても受理し、offsetsまたはlinked objectが変われば拒否する回帰を追加する。
- 再試行: ROM byteを変えない `v1.3.3` sourceをtag固定し、隔離fresh rebuildで
  final/BPS/ZIP byte一致を最終gateとする。
- 影響: battle UI入力来歴、v1.3.3 release、fresh-checkout再現性。

## 2026-08-20 — D-024: 共通数量UIのproduction consumerを実在Item ABIへ限定する

- 判定: T10のmodel fixtureは共通数量UIのconsumerとしてTera shardとcoinをPASS扱いしたが、
  Stage35固定baselineのcanonical Itemは0..998で、Tera shard 18種を含まない。reserved Item
  589は1枠だけであり、type別item、save、effect、iconの18種ABIを表現できない。
- coin境界: Item 950のコレクレーのコインは`ITEM_TYPE_EVOLUTION_ITEM`、`PARTY_ONE`の
  1個消費道具である。Vega arcade coinはbag itemではなくSaveBlock1の暗号化u16通貨であり、
  いずれもbag数量callbackのconsumerとして扱わない。
- 決定: Stage36の共通数量UIは実在する経験アメ、栄養drink、ハネ、ふしぎなアメ、
  単能力EV reset用品へ接続する。汎用数量resolverは維持するが、Item namespace拡張を伴う
  Tera shardをT19の35 production ownerへ偽装せず、T10 fixture、QOL方針、テスト方針、
  release操作説明を実buildへ同期する。
- 根拠: T19のrelease正本は`content/qol_progression.csv`の35行であり、Tera shard/coinは
  独立行に存在しない。この訂正は35機能の削減ではなく、model-only PASSをproduction実在性へ
  合わせるT19受入条件の整合修正である。
- 影響: T10 quantity fixture、QOL方針・テスト・操作説明、T19 Stage36検証。

## 2026-08-21 — D-025: Mirageを独立ownerとactive-safe cleanupでproduction接続する

- field: map `31/1`の受付object、map-entry type 3、既存warp先2 cleanupだけをexpected-byte付きで
  薄いdispatcherへrepointする。受付は標準party UI `special 0x29`、戦闘は初期化とpost-script復帰を
  両立するcanonical `trainerbattle 0x5C/mode3`を使う。map-entry cleanupはactive challenge中のjournalを
  保持し、inactive時だけstale stateを復旧する。旧Mirage flag/varと全badge set scriptはownerにしない。
- party/battle: playerは選択した持込3体の600-byte snapshotを保持し、永続level/EXPを変更せず
  battle copyだけをLv.100化する。相手はmanifestのSPECIAL 6体から決定的に3体を生成し、既存ChangeKitを
  exactly once delegateした後にMirage active時だけparty/abilityを上書きする。Factory rental、BP、streak、
  reward、party snapshotには相乗りしない。
- RAM/save: volatile stateは`0x0203EE00..0x0203F098`のexact 664 byteとし、既存battle UI state
  `0x0203F101`を予約外に保つ。既存40-byte `VegaMirageState`は拡張せず、未使用の
  `current_record[4..7]`をmarker/inverse＋badge/round/gimmick payload/inverseの8-byte journalにする。
  stock saveとsector 31を一度ずつ書き、片側失敗時は台帳・party・badgeを戻して両storeを補償する。
- reset検証: fresh coreではstock titleと同じ`SetSaveBlocksPointers→LoadGameSave`順を再現する。
  save blockだけを初期化して`gPokemonStoragePtr=0`のままload adapterを直呼びするfixtureは、次の通常saveで
  PC sector checksumを破損するためproduction reset証跡に使わない。256 badge maskを専用save imageから
  各回開始し、active保存→core破棄→fresh load→exact復旧を確認する。
- 影響: T21 Stage38、Mirage field/runtime/save/QA。ChatGPT Pro待ち4領域、Factory、Raid、acquisition、
  T20 event、既存trainer contentは変更しない。

## 2026-08-21 — D-026: Codex対戦はRetroArch NCI外部controller方式で段階統合する

- transport: GBA link cable、RetroArch netplay、save file pollingを使わない。iPadで1本のROMを動かし、
  RetroArch NCIのsystem memory mapからversioned EWRAM mailboxだけをread/writeする。SSHは設定診断、
  versioned ROM転送、証跡取得だけに使う。plain UDPのためtrusted LAN限定とする。
- protocol: magic/version/size、Stage identity、boot session nonce、sequence/inverse、CRC、phase、legal actionを
  fixed-width ABIへ置く。PCは宣言request spanだけを書き、ROMがphase・nonce・sequence・CRC・合法性を
  検証してからbattle controllerへ渡す。PCからparty/saveを直接編集しない。
- battle: single 3v3、双方6体preview、プレイヤーは標準party UI、CodexはCLIで3体を選ぶ。
  固定regulationはLv.50統一／自由と同一持ち物許可／禁止だけ。種族・content banlistと報酬balanceは
  systemへ固定せず、ユーザーとCodexの会話で決める。
- reward: 正常resultに紐づくreward windowから、canonical item/Pokémon IDを既存ROM transactionへ渡す。
  match ID、request sequence、payload hash、journalでreset/save fault/retryをexactly onceへ収束させる。
- 分割: T26 Stage43で実iPad transport/mailbox、T27 Stage44で6→3 battle、T28 Stage45で任意報酬・
  Codex companion skill・iPad E2Eを完成させる。T26実機gate不合格時は代替transportを推測実装しない。
- 影響: T26〜T28、Stage 43〜45、RetroArch local設定、Codex CLI/skill、battle/save/reward QA。

## 2026-08-21 — D-027: Codex対戦CLIは能力提供に限定し、公平な公開情報と自由gimmickを採用する

- CLI責務: `vega-codex-battle`は接続診断、read-only catalog、状態・公開情報・合法候補の取得、wait、
  明示されたteam/選出/action/rewardの送信だけを担う。戦略、構築、選出、行動、gimmick、乱数報酬、
  理由説明、発話頻度を自動決定または強制せず、Codex taskのpromptへ残す。
- 公平性: プレイヤーが現turnで確定したmove、switch先、target、gimmick、入力時刻、private command bytesを
  Codex action commit前にmailbox/CLIへ出さない。ROM内private bufferへsealし、双方commit後だけ通常battle
  controllerへ渡す。選出順、未公開move/item/ability/Tera typeも通常の公開時点まで秘匿する。
- 構築資料: canonical Species/Move/Item/Abilityとlevel/egg/TM/tutor/form learnsetをread-only catalogへ生成する。
  bounded searchとID exact readを既定にし、全件は明示file exportへ書く。毎turnの入力contextへ全catalogを
  混ぜず、learnsetは参考情報であってsystem banにしない。
- gimmick: Codex対戦は`UPSTREAM_OPEN`固定とし、双方の物語進行/key item gateだけをbattle-localに外す。
  Mega/Z/Dynamax/TerastalのSpecies/item/move/Tera type適合性、使用済み状態、相互作用はfixed CFRU-JPを正とする。
  T06の通常戦・Factory・Mirage等のbattle-wide mechanic modeを変えず、個々の自主縛りは会話で扱う。
- 影響: T27 Stage 44のprotocol/team/catalog/action/privacy/gimmick/QA、T28 companion skillとoperator guide。

## 2026-08-27 — D-028: iPad実機確認を完了／release gateから分離する

- 決定: iPadへのROM／save配置、実機プレイ、人手承認は任意の運用確認とし、task完了、release判定、
  依存READY判定の必須条件にしない。利用できない場合やユーザーが実施しない場合も、ローカルgate合格を
  妨げない。
- 完了gate: clean入力identity、決定的build、declared span外変更0、ROM／RAM／save／map／hook overlap 0、
  差分／直接BPS往復、fresh-core自然入力、独立process再現、warning／error 0を機械可読証跡として残す。
- 任意配置: ローカルgate合格後にユーザーが希望し接続可能な場合だけ、
  `docs/IPAD_RETROARCH_MGBA_SAVE_PLACEMENT.md`に従って別basenameで配置する。配置失敗や未実施は
  ROM実装の完了状態を変更しない。
- 影響: Stage55をDONEへ確定し、Stage56および今後のtask／release仕様からiPad承認依存を除く。
  過去の実機証跡は履歴として保持し、再解釈や削除をしない。

## 2026-09-08 — D-029: 私有開発資材を持つGitHub repositoryをPrivate固定する

- 発見: `private-environment-v1` Releaseの名称だけをprivateと解釈していたが、GitHub APIで
  repository自体がPublic、Releaseが非draft公開状態であることを確認した。assetにはROM／save／
  受領原本を含むため、repository可視性を実際の公開境界として扱う必要がある。
- 決定: ユーザーの明示指示により`dekaazarashi1111-web/pokemon-vega-modern`全体をPrivateへ変更し、
  APIの`private=true`／`visibility=private`を読み戻した。既存Release 5 assetは削除せず保持する。
- 再発防止: private Releaseを取得するGitHub-hosted workflowは、downloadより前にGitHub APIの
  `.private == true`を必須確認し、Publicなら資材を取得せずfail closedする。名称、tag、過去状態だけを
  非公開性の根拠にしない。
- 運用: 通常の開発・重い検証はローカルを優先し、必要なcheckpointだけを後からGitHubへ反映する。
  P04のroot license不在素材はPrivate化後も再配布可能とは扱わず、Releaseへ追加しない。

## 2026-09-08 — D-030: サイドチェンジ候補を現行版では採用しない

- 決定: 原作技`Side Change`（プロジェクト候補Move ID 1063）は現行版へ実装しない。
  Move ID、効果、AI、UI、アニメーション、save互換処理を追加せず、代替技への置換もしない。
- 習得境界: 受領原本に含まれる159経路は来歴・監査用source evidenceとして保持する一方、
  runtime選択集合から159件すべてを明示的に除外する。全sourceは118,528経路、現行選択は
  118,369経路とし、machine 68件／tutor 4件を供給不足数へ含めない。
- 容量境界: Move namespaceは既存`0..1062`のまま、P04のMove append予約は0件とする。
  新MoveがないためMove固定表の行拡張・新effect slot・Move 1063を含むsave roundtripを要求しない。
- 再採用: 将来実装する場合はこの判断を上書きせず、新しい意思決定で採用状態、効果仕様、
  runtime実装、全159経路の再選択を同時に更新する。
- 影響: P03習得契約／Stage67、P04容量、P05新技・特性契約、P07追加習得、P08統合監査。

## 2026-09-08 — D-031: Winds/Waves御三家3種を現行追加対象から外す

- 決定: Browt／Pombon／Gecquaは現行modernizationへ追加しない。通常Species追加数を0件、Mega用
  Species/Form追加数を49件とし、3種へ数値ID、固定表行、素材、習得、取得経路、runtime処理を割り当てない。
- 来歴: 公式発表に基づく名称、タイプ、特性、出典URLは候補監査の来歴として保持するが、3件すべてを
  `NON_ADOPTED_USER_SCOPE`／`NOT_APPLICABLE_NON_ADOPTED`として機械可読に区別する。将来追加する場合は
  新しい採用判断と容量監査を必要とする。
- 容量: Species/Form予約を1621〜1669の49件へ縮小し、34固定表の見積りを616,521→636,378 bytes
  （+19,857、alignment込み636,392）へ再計算する。Winds/Waves素材の不足を現行release blockerに数えない。
- 影響: P04候補／素材／容量、P05 battle content、P07習得、P08統合、modernization引継ぎ。

## 2026-09-08 — D-032: 追加Mega Stone 45件を専用Factory BP店で供給する

- 決定: Mega Stone 45件をItem ID 999〜1043にstable key順で配置し、map `96/5`の別店員から全品16 BPで購入できるようにする。既存Factory店員と通貨は共有するが、カタログとUIは分離する。
- 解禁・重複: Mega Ring ID 580を解禁条件とし、個別expanded event flag `0x14A0..0x14CC`で1saveにつき各1回までとする。固定999-item取得bitmapやMirage 10-bit virtual itemには混ぜない。
- Item境界: Item固定5表を1,044行へ拡張し、base sanitizerとCFRU `item.c`由来の12 consumerだけをsemantic owner／exact context付きallowlistで1043 inclusiveへ更新する。1044は拒否し、Codex／Mirageの既存固定カタログは998のまま。
- 保存: Item追加→BP支払→claim flag→通常save→sector 31の順で確定し、失敗時はItem／BP／flagを補償して再保存する。実ROMで代表3件とfresh-core再読込を確認する。
- 影響: Stage68、P04 Item／入手経路、P08統合。Mega Speciesの戦闘変化は後続Stageとする。

## 2026-09-08 — D-033: えいえんのはなフラエッテは既存ID 1029の入手経路だけ追加する

- 決定: メガシンカ前のえいえんのはなフラエッテは、Stage67に種族値・画像・名称・習得表まで存在するSpecies ID 1029／`FORM_KEY_FLOETTE_ETERNAL`を再利用する。別の通常Species IDは追加しない。
- 配布: Stage69でmap `96/5` local 15のNPCを追加し、Mega Ring 580所持時にLv.50個体を手持ち→PCの順で1save1回配布する。フォーム固有取得はflag `0x14CD`、National 670のseen/caughtは既存collection ledger bit 850を正とする。旧FireRed 52-byte図鑑bitmapの範囲外へ書かない。
- 保存: 個体配置→flag／collection反映→通常save→sector 31の順で確定し、失敗時は配置先・取得状態・台帳を補償する。party/PC配布はexact ROM、全満／rollback／fresh reloadはhostまでを現checkpointの保証範囲とする。
- 影響: Stage69、P04取得経路、P08統合。Mega Floette Eternalの戦闘中変化は後続Stageとする。

## 2026-09-08 — D-034: Mega 49形態の固定表と戦闘意味をStage70/71/72に分離する

- Stage70所有: Species ID 1621〜1669の49形態、画像素材、Species固定24表、Ability固定4表、Species上限、Ability行上限と派生ポインターの再接続までを担当する。既存Species 0〜1620の行はbyte一致で保持する。
- Stage71所有: 既存Mega engine ABIを変えず、49形態のbase species＋Mega Stone順方向行と戦闘終了用逆方向行をevolution表へ追加する。Mega Ring 580、1戦闘1回、誤石拒否、解除は固定CFRU-JPの既存処理を正とする。
- Stage72所有: Ability ID 312〜317の実効果、発動／不発／抑制／複数対象／AI・UI意味。Stage70の「こうかは じゅんびちゅう。」とrating 0はOOBを防ぐための仮行で、stable keyとIDを保って差し替える。
- 安全境界: `TeamBuilder.abilityOnTeam[312]`は新Abilityをfacility生成poolへ入れない間は非到達とし、将来入れる場合は構造体ABIを再ビルドする。Browt／Pombon／GecquaはStage70でも追加しない。
- 影響: Stage70〜72、P04種族・Mega runtime、P05 Ability runtime、P08統合。

## 2026-09-08 — D-035: Stage71は既存のmode別Mega gateとひんし時復元を継承する

- 訂正: D-034の「Mega Ring 580、1戦闘1回」は全mode共通条件ではない。Stage71は新しい
  battle hookを追加せず、既存のproject mechanic policyを最初に通した後、通常戦ではMega Ring
  580を要求し、Frontier／Linkでは固定CFRU-JPのRing例外を継承する。
- 使用回数: 通常戦はproject側のside-used markとCFRU側のowner doneを維持し、同一side／ownerの
  2回目を拒否する。上流Mega Brawlは`megaData.done`を立てないが、先行するproject side-used gateとの
  厳密な合成挙動はStage72後の最終mGBAで確定し、それまではrelease claimに含めない。
- 形態寿命: 交代ではMega形態を維持する。ひんし時は既存`Faint_FormsRevert -> TryFormRevert`で
  baseへ戻る一方、`megaData.done`は残るため蘇生後の再Megaを拒否する。戦闘終了は既存
  `MegaRevert`とStage71の逆方向行を使い、中断／saveは既存snapshot ownerを変更しない。
- allocation: Stage71はStage70が確保したallocation #73内のevolution行だけを変更するため、同ownerの
  全850,544-byte slice SHA-256を更新する。新allocationは作らず、非対象73行のledger／ROM sliceと
  region summaryをbyte一致で保持する。
- 影響: Stage71 Mega runtime、Stage72最終mGBA、P08統合。D-034の無条件に読める記述は本決定で補正する。

## 2026-09-08 — D-036: P03持越し意味と実供給完了を別claimとして扱う

- 境界: Stage73候補の条件付きegg 41、shared egg 5,023、pre-evolution carry 35,141、
  reminder 295、form change 70を、保留67,218から計40,570経路として分離する。通常egg、level-up、
  evolution level0へ意味を潰して転記しない。
- 持越し: 進化／form変更で既存4技枠を保持する挙動は35,141 routeの必要条件だが、新しい技の
  供給実装ではない。うちTM／TR／tutor由来23,578 routeは元技の供給が実装されるまで入手完了と
  数えず、既存owner意味と新規materializationを別々に記録する。
- タマゴ: 共有タマゴはdirect eggとの重複2,272とshared-only 2,751を分け、作品／受け手条件を
  保持する。Volt Tackle 1件は既存special breeding owner、alias／incense衝突40件はexact target
  adapter候補とし、無条件eggへ統合しない。
- 親固定: Stage73 ROM工程はStage72のcommit、ROM path／size／SHA-256が揃うまでfail closedとする。
- 影響: P03 Stage73 consumer実装、後続machine／tutor供給、P08統合。

## 2026-09-08 — D-037: Ability 312〜317は薄いCFRU adapterとしてStage72へ接続する

- 決定: Dragonize／Eelevate／Fire Mane／Mega Sol／Piercing Drill／Spicy SprayをAbility ID
  312〜317のu16 ABIで固定し、6 Mega形態の全3 ability slot、説明、rating、Mold Breaker表と
  29箇所の既存CFRU-JP consumerへ薄いadapterで接続する。既存Ability 0〜311と名前表0〜317は保持する。
- 優先順位: DragonizeはIon Delugeを上書きするがElectrifyを上書きせず、Max／Z／active Teraでは
  不正なtype／power変更を行わない。Mega Solはfield天候を永続変更せず、使用者のUtility Umbrellaより
  personal sunを優先し、damage計算中に味方Flower Giftを誤発火させない。
- 防御境界: Eelevateはdamaging GroundだけをLevitate相当にし、Ability ShieldとFuture Sight元使用者を
  保持する。KO処理はstate29で効果なしの時だけstate30へyieldし、Moxie script完了後に元bankへ戻す。
  Piercing Drillは単体contactの個人Protectだけを1/4 damageで貫通し、side guard／Max Guardと
  contact shield反応を保持する。Spicy Sprayは実damageと存在する元攻撃者だけを対象にする。
- 未完了: Solar Beam系charge省略時のability popup、Eelevate専用switch AI、Piercing DrillのAI仮想Protect
  1/4予測、Spicy Sprayの味方発火AI評価、exact-ROM mGBAをrelease blockerとして残す。Stage72は
  checkpointであり、P04／P05完了や現行プレイ基準への昇格を意味しない。
- 影響: Stage72 Ability runtime、Stage73親identity、P04／P05／P08、最終累積mGBA。

## 2026-09-08 — D-038: Stage73は5群consumer接続と供給完了を分離する

- 決定: 条件付きegg 41、shared egg 5,023、pre-evolution carry 35,141、reminder 295、
  form change 70の計40,570経路を、Stage73のconsumer境界としてStage72上へ接続する。
- 新規実装: alias／incense衝突7種のexact egg 40、shared egg 5,023、reminder 295、
  ロトム5 form moveの計5,363を新規runtime materializationとする。Pichu＋Light Ballの
  Volt Tackle 1件は既存`BuildEggMoveset` ownerをbyte列まで照合し、二重hookしない。
- 既存owner: pre-evolutionの4技保持35,141、generic form保持61、固定form transition 4を
  新規技供給と数えず、既存owner 35,207件として別計上する。ロトムは既存技4枠を無断で消さず、
  空きも旧signatureもない場合は`EFFECTLESS`として技メモリーでの空き作成を要求する。
- 完了境界: 通常／共有技候補は40枠内でdrop 0。Browt／Pombon／Gecqua、Side Change、禁止された
  level／eggへの意味変換は0を維持する。machine 26,279＋tutor 369は未供給のため、Stage73を
  P03完了やrelease candidateとして扱わない。
- 影響: Stage73、P03、Move Memory、Collection form service、P08、最終累積mGBA。

## 2026-09-08 — D-039: P08の選択候補をStage73へ再固定しmaterializedとaccountedを分離する

- 選択: P08の累積候補をStage73へ更新する。現行プレイ基準はStage62、完了工程はP01だけ、
  P02〜P08は未完了、release-readyはfalseのままとする。
- P03勘定: 新規runtime materializationは累積56,514経路、既存ownerを含むconsumer境界accountは
  累積91,721経路とし、既存owner 35,207を新規供給へ重複計上しない。残る直接供給26,648のうち
  23,595は既存owner経路のmachine／tutor上流依存でもあり、別枠加算しない。
- 継承監査: Stage70〜73の4 incremental BPSをexact applyし、ROM／metadata／allocation、allocator
  sequence 74〜76、既存ownerのcontent hashを固定する。Stage70→71の同owner payload更新だけは
  旧新hashを個別固定する。
- 未完了: P02 Stage71は`STOPPED_EXACT_UI_PENDING`／production `UNJUDGED`。P04は49 Mega runtime、
  P05はAbility 6件＋29 hookまでROM接続済みだが、残る供給、明示AI／UI境界、最終累積mGBAを
  blockerとして維持する。本checkpointでは重いmGBAを実行しない。
- 影響: `config/modernization_candidate.json`、P08 integration／runtime／release handoff、
  modernization引継ぎ。active baseline、iPad、save、Releaseは変更しない。

## 2026-09-08 — D-040: 残るmachine／tutorはfamily分離archiveで供給し退化時保持を別表にする

- 決定: Stage73に残ったmachine 26,279＋tutor 369の26,648経路は、既存128 TM/HM slot／64 tutor
  slotへ押し込まず、殿堂入り後のBagわざメモリーにfamily分離したindexed archiveとして接続する。
  machineは40件×最大4ページ、tutorは1ページとし、暫定価格は無料で後続の中央経済設定から
  差し替え可能にする。
- 保全: `BuildLearnableMoveset`を使うBenjamin Butterfree退化処理は、Stage73のshared egg／reminderや
  持越し合法技を知らない。全118,369選択経路から、現行level／egg family／TM／tutorとStage74直接
  archiveで既に合法と判定できる集合を引き、残る4,014 path／2,223 target-moveを削除防止専用表へ
  入れる。この表はUIへ公開せず、供給数とaccountingへ加算しない。
- 容量: 全1,621種の実buffer最大は238、unique最大234、構造上限319で、呼出し側429 u16に対する
  overflowは0。Move Memoryの既存allocation #33はlayoutを動かさず実ROM slice hashだけを更新し、
  Stage74 payloadをsequence 77へ追加する。
- 完了境界: 新規runtime materializationは累積83,162、既存owner込みaccountedは118,369、直接供給残0。
  Side Change、Browt／Pombon／Gecqua、family統合、level／egg coercionは0を維持する。Own Tempo Rockruff
  0744.01の38持越し経路と最終累積mGBAが残るため、P03／release completionは主張しない。
- 影響: Stage74、P03、Move Memory、Benjamin Butterfree、P08、最終累積mGBA。active baseline、iPad、
  save、Releaseは変更しない。

## 2026-09-09 — D-041: P08の選択候補をStage74へ再固定する

- 選択: P08の累積候補をStage74 `481083bc…e22d65e`へ更新する。現行プレイ基準は
  Stage62、完了工程はP01のみ、P02〜P08は未完了、release-readyはfalseのままとする。
- 継承監査: Stage69→70→71→72→73→74の5 incremental BPSを実byteへexact applyし、Stage74の
  ROM／metadata／allocation／BPS、2 hook、allocation #33内容更新と#77追加を固定する。
- P03勘定: 新規runtime materializationは累積83,162、既存owner込みaccountedは118,369、
  直接供給残は0。退化時の削除防止4,014 path／2,223 target-moveはUI供給と経路勘定へ加算しない。
- 未完了: Own Tempo Rockruff 0744.01の38経路意味、暫定archive経済、P02通常UI、
  Floette full/fresh reload、P05の4 AI/UI edge、最終累積mGBAをrelease blockerとして維持する。
- 影響: `config/modernization_candidate.json`、P08 integration／runtime／release handoff、
  modernization引継ぎ。active baseline、iPad、save、Releaseは変更しない。

## 2026-09-09 — D-042: Own Tempo Rockruffは図鑑非加算の内部条件フォームとして追加する

- 決定: 通常イワンコ1142を別種へ置換せず、Own Tempo Rockruff 0744.01をSpecies 1670、
  `INTERNAL_CONDITIONAL_FORM`、National Dex 744、collection class 4／weight 0としてappendする。
  これはユーザー指定の「通常ポケモン追加0」を変えない内部実装IDであり、Browt／Pombon／Gecquaの
  ID・素材・runtimeは引き続き0とする。
- 特性・進化: 1670の3 ability slotは全てマイペース20。通常1142に誤って開いていたLv.25・
  17〜19時のルガルガン黄昏1263進化行を削除し、同じ8 bytesを1670だけへ移す。既存1142／1263は
  save migrationせず保持する。
- 取得・繁殖: 既存の野生1142生成が成功した後だけ、personalityを混合した決定的1/8を1670へ
  変換する。追加RNGは使わず、非1142・生成失敗・既存個体を変更しない。繁殖は1263／1670だけを
  1670へ解決し、他Speciesは進化表逆走をせず既存`GetEggSpecies`へexact delegateする。
- P03: 0744.00のlevel 14／machine 38／egg 4／shared egg 4、計60 routeを別identity ownerへ
  exact cloneする。既に1263側でaccount済みのcarry 38件は既存slot 21＋Stage74 archive 17へ解決し、
  missing owner 0、materialized 83,162、accounted 118,369、delta 0を維持する。
- 完了境界: 24 Species表、310 pointer、19 count consumer、5 hookをStage75へ接続するが、
  最終累積mGBAまでは`full_p03_done=false`、release candidate falseとする。P08 selected candidate、
  active Stage62、iPad、save、Releaseはこのcheckpointでは変更しない。

## 2026-09-09 — D-043: P05は安全に定義できる3 edgeだけをStage76へ接続する

- 決定: Mega SolのSolar charge時popup、Piercing DrillのAI上の予測Protect 1/4 damage、
  Spicy Sprayの意図的な味方発火評価をStage76へ実装する。新Move、Side Change、通常Species、
  Browt／Pombon／Gecquaは追加しない。
- Protect境界: Detect 197はProtect 182へ正規化して既存判定へ渡す。Max Guard 891と未選択時の
  Dynamax予測は貫通対象にせず、実際にProtect中のdamageを二重に1/4化しない。
- 味方発火境界: direct／spread評価は排他にし、実際に味方へ当たる即時damageだけを対象とする。
  planned Protect／Detect／Max Guard、semi-invulnerable、Present、Future Sight／Doom Desire、
  Pollen Puff、Substitute、KO、自己犠牲、回復系持ち物は保守的に除外する。
- 保留: Eelevate 313をEarth Eater 298へ単純置換する方式は、Ground damage、Thousand Arrows、
  接地、Gravity、Mold Breaker、Ability Shieldの意味を保てない。候補2 siteをStage75とbyte同一に
  保ち、完全な文脈を扱える別checkpointまで`PENDING`とする。
- 完了境界: pointer 1件＋hook 3件＋payload 2,066 bytesをStage76へ接続する。focused test、
  builder check、独立runtime／artifact監査はPASSしたが、mGBAとP05全体は未完了、release-readyは
  false、active baselineはStage62のままとする。

## 2026-09-09 — D-044: P08の選択候補をStage76へ再固定する

- 選択: P08の累積候補をStage76 `f753f137…0100100ac`へ更新する。Stage75のOwn Tempo Rockruffと
  Stage76のP05安全edge 3件を統合し、現行プレイ基準Stage62、完了工程P01のみ、P02〜P08未完了、
  release-ready=falseを維持する。
- 継承監査: Stage74→75→76のincremental BPSを含むStage67→76 chainを実byteへexact applyし、
  ROM／metadata／allocation、Stage75の24表・310 pointer・19 count consumer・5 hook、Stage76の
  pointer 1件＋hook 3件をfail closedで固定する。
- 境界: P03のmaterialized 83,162、accounted 118,369、直接供給残0、Browt／Pombon／Gecquaと
  Side Changeの採用0を維持する。Eelevate専用switch AI、暫定archive経済、P02通常UI、Floette
  full／fresh reload、最終累積mGBAはrelease blockerとして残す。
- 影響: `config/modernization_candidate.json`、P08 integration／runtime／release handoff、
  modernization引継ぎ。iPad、save、Release、現行プレイ基準は変更しない。

## 2026-09-09 — D-045: Battle Circus特性無効はStage72 wrapperの手前で全29 hookを迂回する

- 決定: Battle Circusのbattle type bit 26とcircus特性無効bit 31が同時に立つ時だけ、Stage72で
  接続した29 hook／33 Ability surfaceを各original trampolineへ委譲する。通常時はStage72 wrapperへ
  委譲し、新Ability 6件とStage76の3 edgeを維持する。
- 既存抑制: Gastro Acid／Neutralizing Gas／Mold BreakerはCFRUがactive abilityをraw 0へ移す既存
  意味を変更しない。Circusだけはraw abilityを保持するため、後段dispatcherで明示的に抑制する。
- ABI: 12-byte veneer 7本は元r3をr12へ退避し、抑制経路でr3を復元する。残る8-byte veneer 22本は
  Stage72と同じr3 scratch契約を使う。r0〜r2、SP、LR、5番目のstack引数を保持してtail delegateする。
- 完了境界: Stage77 payload 1,220 bytes、hook 29件、allocation sequence 80を接続する。親80行、
  Stage76のpointer 1＋hook 3、Eelevate保留2 site、通常抑制意味を保持する。focused test、builder check、
  独立監査はPASSしたが、mGBAとEelevate専用switch AIが残るためP05／release完了は主張しない。
- 影響: Stage77、P05、Battle Circus、最終累積mGBA。active baseline、iPad、save、Releaseは変更しない。
