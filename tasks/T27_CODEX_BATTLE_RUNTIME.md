# T27 — Codex操作6→3対戦をStage 44へproduction統合する

- Lane: `engine/ui/content/tooling/qa`
- Depends on: `T26`

## 目的

T26の実iPad検証済みtransport/mailboxを使い、プレイヤー6体とCodex team 6体から双方3体を選出する
シングル対戦を通常プレイ入口へ接続する。CodexがCLIでteam選出、技、交代、降参を選べるStage 44を作る。

## 固定入力

- T26完了commit: `6f058ccbd4d079cba4dc2446d30275feabcbaae3`。
- ROM: `build/stages/43_codex_battle_bridge.gba`、33,554,432 bytes、SHA-256
  `4834d42bc28d044e99b2686263808718441f4abe2347353a9eca1592224d8a9c`。
- metadata: `build/stages/43_codex_battle_bridge.json`、SHA-256
  `0e1017542f8481fbcc2145632869803e3b84dfec91d0e8b3fb5e4c6cce9edee4`。
- protocol 1.0: `generated/runtime/codex_battle_bridge_protocol.json`、SHA-256
  `a014e6b219d2daf8ab1d15c7ce3aa76c2dabda76331664`。T26 CLIと実iPad NCI reportを正規入力にする。
- `design/codex_battle_architecture.md`とT26 `docs/CODEX_BATTLE_PROTOCOL.md`。
- Stage 42までのbattle controller、party selection、CreateMon、Factory/Mirage exact restore、battle rule/UIをbehavior oracleにする。
- canonical Species/Move/Item/Ability manifest、T09/T22のlevel/egg/TM/tutor/form learnsetを構築catalogの入力にする。
- T06のfixed CFRU-JP Mega/Z/Dynamax/Terastal判定と、通常戦・Factory・Mirageのmechanic policyを比較oracleにする。

## 固定仕様

- 対戦は`SINGLE_3V3`固定。双方6体previewから3体を選び、選出順は相手へ公開しない。
- プレイヤーは現在party内のbattle可能な6体から標準party UIで3体を選ぶ。最低3体未満なら開始しない。
- Codexはversioned team JSONで正確に6体を登録し、CLIで3 slotを選ぶ。
- team JSONはmove/item/ability/nature/IV/EV/shiny/tera typeを指定でき、省略fieldは同じsession seedから
  決定的に補完する。canonical ID/幅/個体安全性はfail-closedにするが、通常習得可否をbanとして強制しない。
- ROM/CLIが強制する対戦構築ルールは設けない。種族・伝説・同一持ち物・技・構築の制限は、対戦ごとに
  ユーザーとCodexが合意して自分たちで守る。技術的にbattle engineへ渡せない壊れた個体だけを拒否する。
- レベル処理だけは対戦用optionとして`FLAT_50|OPEN`を用意する。
- gimmickはregulation項目へ増やさず`UPSTREAM_OPEN`固定とする。Codex対戦中だけ双方の物語進行/key item gateを
  battle-localに外し、Mega/Z/Dynamax/Terastalの適合性、使用済み状態、相互作用はfixed CFRU-JPを正とする。
  T06のbattle-wide mechanic modeや他battle modeを変更せず、Codex対戦active時だけ専用adapterを使う。
- 個々の対戦でユーザーとCodexが決めたgimmick、構築、選出、行動の縛りはCLI/ROMで強制しない。
- `FLAT_50`はbattle copyだけ、`OPEN`は入力levelを使う。退出時にplayer party 600 byteをexact restoreする。
- battle bag、捕獲、逃走、EXP/EV/賞金/friendship/永続held-item消費を抑止する。
- Codex合法行動はmove、switch、forfeitで、moveは`none|mega|z|dynamax|tera`のgimmick指定を伴える。
  ROMがmoveごとに公開した`legal_gimmicks`を含むlegal maskにない入力は同じphaseのまま拒否する。
- Codexへは自team全情報と公開済みplayer情報だけを渡す。未公開move/item/ability/Tera typeやraw save dumpを渡さない。
- Codex選出3体は現在HP／最大HPの実数、自activeはlive species/level/move ID/PP/item/ability/typeを返す。
  player activeは公開species/level/HP割合/瀕死だけを返し、HP 0、強制交代、通常交代継続を別状態にする。
- team previewのplayer 6体は公開level/gender/shinyも返す。live中はCodex activeの5実能力値と双方の
  appearanceを返し、playerの既出個体は選出順を漏らさない初登場順opaque IDで交代後も追跡する。
- 公開stateは主要状態異常、7能力ランク、公開volatile、Disable/Encore、field/side/hazard、遅延効果、
  gimmick状態を含む。command 16の画面表示とcommand 52のCFRU特性ポップアップだけをevent化し、
  標準日本語template/CFRU追加文候補と実参照contextを返す。command 17、それ以外のcontroller data、
  内部乱数counter、Illusion真identityは含めない。
- プレイヤーが現turnで確定したmove、switch先、target、gimmick、入力時刻、private command bytesはCodex actionの
  commit前に一切返さない。player commandはROM内private bufferへsealし、双方commit後だけbattle controllerへ渡す。
- Codex入力待ちはgame内に明示し、無期限WAITを既定とする。disconnect時はWAIT、CPU fallback、forfeitを選べる。
- CPU fallbackは固定CFRU AIを使い、再接続後に同じturnを二重実行しない。
- 通常battle、Factory、Mirage、Raid、Reward encounterのcontroller/stateへCodex commandを漏らさない。
- production入口は既存施設内の通常NPC/端末と標準menuを使い、debug menuだけにしない。
- CLIは状態、公開情報、合法候補、操作方法だけを提供し、team/選出/行動/gimmickを自動決定しない。
  戦略、乱数policy、理由説明、発話頻度は呼出元Codex taskのpromptに委ねる。
- `match view`と`wait --compact`は現在の判断盤面を自己完結で返し、戦闘eventだけを前回cursor以後の差分にする。
  既読全文、neutral/0効果、コード、raw構造体、計算後のraw IV/EVを毎turn反復しない。完全監査は`match status`へ分ける。
- read-only catalogはSpecies/Move/Itemのbounded searchとexact get、learnset get、全件file exportを提供する。
  list/search既定出力を小さくし、全catalogを各turn snapshotへ含めない。

## CLI command surface

- `team validate --file ... --json`
- `catalog species search --query ... --limit N --json`
- `catalog species get SPECIES_ID --json`
- `catalog move search --query ... --limit N --json`
- `catalog move get MOVE_ID --json`
- `catalog item search --query ... --limit N --json`
- `catalog item get ITEM_ID --json`
- `catalog learnset get SPECIES_ID --json`
- `catalog export --output PATH --json`
- `match configure --level flat50|open --json`
- `match upload-team --file ... --json`
- `choose team 1,3,6 --json`
- `wait --timeout 55 --json`
- `wait --timeout 55 --compact --json`
- `choose move N [--target N] --gimmick none|mega|z|dynamax|tera --json`
- `choose switch N --json`
- `choose forfeit --json`
- `match status --json`
- `match view [--reset-events] --json`

全writeはsession/match/phase/request sequenceを明示し、成功時に受理されたsequenceと次phaseを返す。

## 実行

1. T26 Stage 43、protocol、CLI、iPad transport証跡を再確認する。
2. player/enemy party、party selection、battle controller、AI、gimmick、battle end/cleanup、entry mapをrooted監査する。
3. canonical manifest/learnsetから小さいlookupと全件file exportを持つread-only catalogを生成する。
4. team/rule/action/public snapshot/private action sealのversioned schemaとprotocol capabilityを追加する。
5. Codex 6体生成、双方3体選出、battle-local level/item rule、`UPSTREAM_OPEN` adapter、相手controller待機を実装する。
6. move＋gimmick/switch/forfeit、双方private commit、disconnect WAIT/CPU/forfeit、再接続、stale command拒否を
   単一state machineへ接続する。
7. player partyと全battle副作用のbefore image/cleanupを実装し、全exitでexact restoreする。
8. 通常施設入口と標準UIを物理接続し、expected-byte付きStage 44を生成する。
9. catalog、privacy/non-interference、gimmick、host protocol matrix、exact-ROM mGBA quick/full、
   iPad multi-turn vertical slice、clean rebuild/BPSを検証する。

## 必須成果物

- `content/codex_battle/**`
- `config/codex_battle_runtime.json`
- `overlays/codex_battle_runtime/**`
- `scripts/build_codex_battle_runtime.py`
- `scripts/rebuild_codex_battle_runtime_from_clean.py`
- `tools/mgba_codex_battle_runtime_smoke.c`
- `tests/test_codex_battle_runtime.py`
- `tests/fixtures/codex_battle_teams/**`
- `reports/generated/codex_battle_runtime_{audit,coverage,matrix,catalog,privacy,gimmick}.json`
- `build/stages/44_codex_battle_runtime.gba`（Git管理外）
- Stage 43→44 BPS、clean→Stage 44 BPS、mGBA、clean rebuild証跡（Git管理外）

## 受入条件

- [ ] T26 Stage 43/protocol/CLI identityが一致し、iPad NCI doctorがPASSする。
- [ ] player 6→3とCodex 6→3が通常入口から完了し、双方の選出順を相手に漏らさない。
- [ ] exact 6-member team JSON、全省略値、invalid ID/width/EV/IV/move count、duplicate fieldを決定的に検査する。
- [ ] `FLAT_50|OPEN`の2 level modeが仕様どおり動き、種族・同一持ち物・content banlist等の
      対戦構築ルールをROM/CLIが強制しない。
- [ ] catalogのSpecies/Move/Item/learnset exact read、bounded search、全件exportがcanonical入力と一致し、
      full exportはfile path/hashだけを返してteam validationのlearnset banにならない。
- [ ] `UPSTREAM_OPEN`でMega/Z/Dynamax/Terastalの代表合法入力が双方で発動し、不適合・再使用・相互作用は
      fixed CFRU-JPどおり拒否される。通常戦、Factory、Mirage、Raidのmechanic policyはbyte/挙動不変である。
- [ ] move＋各gimmick、switch、forfeitの全合法分岐とillegal/stale/duplicate command拒否を実battle controllerで確認する。
- [ ] public snapshotが自team全情報（選出3体のHP実数、active live技/PPを含む）、player公開情報
      （active species/level/HP割合/瀕死、公開済み技/item/abilityを含む）、能力ランク、状態・場・side・
      遅延効果、公開battle event、Codex legal actionだけを含み、未公開情報を含まない。
- [ ] 対戦前player level/gender/shiny、live Codex実能力値、双方appearance、初登場順opaque IDを公開し、
      交代後も既知のplayer技/item/ability/最終HP・状態を同一公開IDへ保持する。実slot・選出順は復元できない。
- [ ] `match view`/`wait --compact`が自己完結した最新判断盤面＋新着eventだけを返し、2回目の無変化読取は
      event 0件となる。full statusより十分小さく、コードやraw dumpを含まない。
- [ ] player撃破をHP 0＋forced switchとして公開し、HP 0 slotをlegal switchから除外する。通常交代は
      voluntary continuationとして1回の明示入力で完了し、forced switch先も1回の明示入力でactive更新する。
- [ ] player pending move/switch/target/gimmick/private bytesを値、長さ、error、sequence、timing metadataのいずれからも
      Codex action commit前に復元できず、双方commit後だけ通常turnが解決される。
- [ ] CLI/ROMがteam、選出、行動、gimmick、説明を自動決定せず、`wait`と明示writeだけで対戦を進められる。
- [ ] disconnect WAIT、再接続、CPU fallback、forfeitがdeadlock・二重turn・無限loopなしで完了する。
- [ ] 勝敗・降参・通信abort・resetの全exitでplayer party、level、EXP/EV、item、badge、RNG ownerをexact restoreする。
- [ ] exact cleanup後も受付の最終msgbox完了までは新規configureを`BUSY`で拒否し、field completion後の
      新matchが旧世代の遅延release/cleanupで終了しない。
- [ ] battle後にEXP/EV/賞金/捕獲/永続item消費がなく、通常saveへ意図しないwriteがない。
- [ ] Codex stateが通常battle、Factory、Mirage、Raid、Reward encounterへ漏れない。
- [ ] `wait`→明示actionを3 request cycle以上繰り返し、task側の戦略や説明policyなしで同一matchを継続できる。
- [ ] iPad Stage 44でteam upload→双方選出→pending action非公開→複数turn→Codexのgimmick付きmove→switch→
      safe abort/cleanupを実証する。T28の報酬付き全試合完走はまだ要求しない。
- [ ] ROM/RAM/save/UI/hook overlap、declared span外変更が0で、clean rebuild/BPS/mGBAがPASSする。

## 禁止する完了判定

- CPU AIをCodex入力と表示する、選出を固定する、相手6体をROMへhardcodeする実装をしない。
- playerのpending commandをmailboxへ複製したり、host側で先読みしてからCodex actionを決めたりしない。
- `STANDARD`固定でgimmickを全無効化したり、T06のglobal mechanic policyをCodex対戦のために変更したりしない。
- CLIやcatalogに戦略、構築、選出、行動、gimmick、説明頻度のpolicyを埋め込まない。
- playerの永続partyをLv.50へ書き換えない。
- raw EWRAM/saveを無制限にCLIへdumpしない。
- host-side state machineや1turn fixtureだけでDONEにしない。実battleの複数turn、交代、終了cleanupをmGBAで通す。

## 完了

1. task固有build/check、protocol matrix、mGBA、iPad multi-turn vertical slice、clean rebuildをPASSする。
2. `design/run_log.md`と`design/version_log.md`へ証跡を追記する。
3. `python3 scripts/taskctl.py done T27 --summary "Codex操作6対3対戦をStage44へproduction統合"`を実行する。
4. task graph、private guard、`git diff --check`をPASSし、意図した差分だけをstageする。
5. `T27:`で始まるcommitを作る。pushしない。
