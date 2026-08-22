# Codex対戦アーキテクチャ

状態: IMPLEMENTATION-READY
基準日: 2026-08-21
実装順: T26 → T27 → T28（Stage 43 → 44 → 45）

## 1. 目的

iPadのRetroArch/mGBAで動くPokemon Vegaと、PC上のCodexを対戦させる。GBA同士の通信対戦は使わず、
同じROM内の相手側battle controllerへCodexが選んだ行動を安全に渡す。

```text
iPad: RetroArch + mGBA + Stage 43以降ROM
        ↕ RetroArch Network Control Interface / UDP
PC: vega-codex-battle CLI
        ↕ 小さく予測可能なJSON
Codex task / ユーザーとの会話
```

SSHはRetroArch設定の診断、versioned ROMの転送、証跡取得にだけ使う。各turnの対戦入力は
`READ_CORE_MEMORY` / `WRITE_CORE_MEMORY`を使い、SSH、save file polling、GBA link cable、
RetroArch netplayを対戦transportにしない。

## 2. 実機で確認済みの開始状態

- `ipad-wifi-ssh doctor`と通常remote commandはPASSしている。
- RetroArchのapp Documents配下に`config/retroarch.cfg`が存在する。
- `network_cmd_enable = "false"`、`network_cmd_port = "55355"`であり、現時点のUDP probeは無応答。
- mGBA libretro framework、mGBA info/config/save/state領域が存在する。
- RetroArch実行バイナリには`READ_CORE_MEMORY`、`WRITE_CORE_MEMORY`、`network_cmd_enable`が含まれる。
- 実際のRetroArch/mGBA version、core memory mapのread/write成功はT26で固定する。

端末固有IP、app container UUID、秘密鍵、private ROM/save pathはGit管理文書や証跡へ保存しない。
接続先はGit管理外のlocal configまたは明示CLI引数で与える。

## 3. 固定する製品仕様

### 3.1 対戦形式

- シングルバトル、双方6体を提示して3体を選出する。
- プレイヤー側は現在の手持ち6体を使い、標準party UIで3体を選ぶ。
- Codex側はmatch開始前に6体の一時teamをCLIから登録し、CLIで3体を選ぶ。
- タマゴ、範囲外ID、壊れた個体dataなどbattle engineが扱えない入力だけを拒否する。
- 種族重複、伝説、幻、UB、Paradox、能力、技構成等のbanlistをROMへ固定しない。
- system上で選択できるbattle optionは`level_mode: FLAT_50|OPEN`だけとする。
- 種族・伝説・同一持ち物・技・構築等の対戦ルールはROM/CLIで強制せず、対戦ごとにユーザーとCodexが
  合意して自分たちで守る。engineへ安全に渡せない壊れた個体だけをfail-closedで拒否する。
- battle gimmickはregulation toggleへ増やさず、Codex対戦では`UPSTREAM_OPEN`を固定する。Mega、Z-Move、
  Dynamax、Terastalを双方へbattle-localに解禁し、物語進行やkey itemの所持はCodex対戦中だけ要求しない。
  Species、held item、move、Tera type等の適合性、使用済み状態、gimmick間の相互作用は固定CFRU-JPの
  `CanMegaEvolve` / `CanUseZMove` / `CanDynamax` / `CanTerastal`を正とし、独自の回数・組合せ規則を足さない。
- T06の通常戦・Factory・Mirage等が使うbattle-wide mechanic modeは変更せず、`UPSTREAM_OPEN`は
  Codex対戦active中だけの薄いpolicy adapterとして実装する。個々の対戦で「Teraなし」等を決めても、
  それはユーザーとCodexが守る任意regulationであり、CLI/ROMは強制しない。
- `OPEN`のlevelはengine-safeな1〜100。`FLAT_50`はbattle copyだけをLv.50相当にし、永続個体を変更しない。
- battle中のbag item、捕獲、逃走、賞金、EXP、EV、friendship、held item消費の永続化を禁止する。
- 合法行動は`MOVE`、`SWITCH`、`FORFEIT`。disconnect時は`WAIT`、`CPU_FALLBACK`、`FORFEIT`を選べる。

### 3.2 Codex側team入力

team JSONはversion付きで、6 memberを持つ。各memberは最低限`species_id`と`level`を持ち、
`moves`、`held_item_id`、`ability_slot`、`nature_id`、`ivs`、`evs`、`shiny`、`tera_type`を省略可能にする。
省略値はROM側で決定的に生成し、同じJSONとsession seedから同じ個体を作る。

指定内容の対戦バランスや通常の習得可否はユーザーとCodexの会話で決める。ROM/CLIはcanonical ID、
field幅、個体値・努力値合計、技数、item pocket等の構造安全性だけを検証する。

構築時だけ使うread-only catalogをCLIへ持たせる。Speciesの名前・type・base stats・ability、Moveの
type/category/power/accuracy/PP、Itemのheld effect、level/egg/TM/tutor/form learnsetをcanonical IDで引けるようにする。
検索/listは既定件数を小さくし、ID exact readを用意する。全件は明示`catalog export --output ...`へ書いて
pathとhashだけを返し、毎turnのsnapshotへcatalogを混ぜない。catalogは構築の参考であり、team upload時の
learnset banや戦略policyには使わない。

### 3.3 情報境界

- team previewでは双方の6 speciesと公開情報を見せ、player側のlevel・gender・shinyも96-byte
  snapshotの対戦前unionから返す。選出した3体と順番は公開しない。
- T27では`choose team`受理直後にPC側へowner-only PNGを自動生成し、左右6体をStage 44 ROM内の
  canonical icon/paletteで表示する。画像生成AIや固定team画像は使わず、各matchの実previewを描画する。
  iPad側は壊れやすい独自windowを重ねず、既存の標準party UIでプレイヤー3体を選ぶ。
- Codexは自分のteam情報を全て読める。
- Codex選出3体は現在HP／最大HPをu16実数で返し、activeはlive species、level、技ID、現在PP、
  item、ability、type、5実能力値をBattlePokemonから返す。bench HP/statusはenemy partyを正とし、
  activeだけlive値で上書きする。owner team sheetは技・道具・特性・性格・Tera typeと対戦levelでの
  計算済み能力値をcompact viewへ返し、計算後のraw IV/EVは毎turn反復しない。
- プレイヤーactiveは画面相当のspecies、level、HP割合、瀕死、主要状態異常を返す。技、持ち物、能力、
  type等はbattleで公開された範囲だけをsnapshotへ載せ、Illusion中の真species/typeは載せない。
- 双方の7能力ランク、公開volatile、Disable/Encore対象技と残りcounter、天候・terrain・room、壁・hazard・
  side timer、Wish/Future Sight/Healing Wish、Mega/Z/Dynamax/Terastal使用・継続状態を固定180-byte
  public stateへ圧縮する。sleepの内部残りturn、Quick Claw等の未公開乱数、AI予測値は載せない。
- `CONTROLLER_PRINTSTRING`（command 16）とcommand 52のCFRU特性表示animation（0x42）だけを4件ringへ取り込み、
  command 17のplayer-only選択文と、それ以外のcontroller dataは除外する。
  標準369種はStage 44 ROM内の日本語テンプレート、CFRU追加文は固定sourceから生成したCRC候補へ照合する。
  eventはmessage/move/item/ability/bankと、文面が各contextを実際に参照したかを返す。`wait`は50 ms pollで
  ringを継ぎ合わせ、sequence gapの有無を返すため、作業値を発動情報と誤認しない。
- 公開されたplayer itemは`UNKNOWN|HELD|CONSUMED_OR_REMOVED|CHANGED_UNRESOLVED`を区別する。
- playerのactiveには実party slotや選出順ではなく、初登場順だけを表すopaque ID `P1..P3`を割り当てる。
  eventにもその時点のIDを付け、交代後も同一個体の公開済み技・道具・特性・最終HP/状態をowner-only
  public knowledgeへ保持する。重複speciesやIllusionがあってもprivate slotを公開しない。
- HP 0／瀕死、撃破後の強制交代、通常交代の継続を別状態として返し、HP 0 slotはlegal switchから除外する。
- プレイヤーが現在turnで確定済みのmove slot、switch先、target、gimmick指定、入力時刻、private command bytesは、
  Codexの行動commit前にはsnapshot、error、sequence差分、CLI出力のいずれにも載せない。ROM内のprivate action bufferへ
  sealし、双方の行動が揃ってから通常battle controllerへ渡す。
- `legal_gimmicks`はCodex自身のactive battlerとmoveごとの候補だけを返す。プレイヤー側の未発動gimmick、
  held item、Tera typeや使用予定は、通常の戦闘演出で公開されるまで返さない。
- CLIはROM構造体や未公開save領域を任意読取するdebug commandをproduction interfaceへ公開しない。
- 通常の判断読取は`match view --json`または`wait --compact --json`を使う。現在盤面は毎回自己完結で返し、
  eventだけをowner-only cursor以後の差分とする。0/neutral効果、既読event全文、コード、raw構造体を省き、
  完全監査用`match status --json`と分離する。

### 3.4 任意報酬

- 正常に結果が確定した直近matchだけがreward windowを開ける。transport abortやstale sessionは対象外。
- Codexは報酬なし、item、Pokémonを任意に選べる。勝敗と報酬内容の固定tableや価値上限を設けない。
- itemはcanonical numeric IDと数量、Pokémonは最低限species IDとlevelで指定できる。
- Pokémonには必要に応じて技、持ち物、特性、性格、IV/EV、色違い、Tera type、
  入っているボール（canonical ball item ID）を追加指定できる。ボール指定は道具付与ではなく、
  生成する個体の捕獲ボール情報としてROM側の正規データへ記録する。
- PCからparty/save byteを直接書かない。ROM側の`AddBagItem`、`CreateMon`、`GiveMon`と既存transactionを通す。
- ID範囲、数量、party/box/bag容量、checksum、request sequenceを検査し、失敗時は無変更に戻す。
- 同じreward requestの再送、reset、save faultで二重付与しない。複数報酬は一意sequenceの複数transactionで扱う。

## 4. CLI契約

command名は`vega-codex-battle`とする。最低限、次を提供する。

```text
vega-codex-battle doctor --json
vega-codex-battle device configure --host HOST --port 55355 --json
vega-codex-battle device status --json
vega-codex-battle bridge ping --json
vega-codex-battle catalog species search --query TEXT --limit N --json
vega-codex-battle catalog species get SPECIES_ID --json
vega-codex-battle catalog move search --query TEXT --limit N --json
vega-codex-battle catalog move get MOVE_ID --json
vega-codex-battle catalog item search --query TEXT --limit N --json
vega-codex-battle catalog item get ITEM_ID --json
vega-codex-battle catalog learnset get SPECIES_ID --json
vega-codex-battle catalog export --output PATH --json
vega-codex-battle team validate --file TEAM.json --json
vega-codex-battle match configure --level flat50|open --json
vega-codex-battle match upload-team --file TEAM.json --json
vega-codex-battle choose team 1,3,6 --json
vega-codex-battle match view --json
vega-codex-battle wait --timeout 55 --compact --json
vega-codex-battle choose move 2 --gimmick none|mega|z|dynamax|tera --json
vega-codex-battle choose switch 3 --json
vega-codex-battle choose forfeit --json
vega-codex-battle reward item ITEM_ID --quantity N --json
vega-codex-battle reward mon SPECIES_ID --level N [--ball BALL_ITEM_ID] [optional fields] --json
vega-codex-battle reward close --json
```

- read、wait、writeを別subcommandにし、writeは期待phaseとsession/request sequenceが一致しない限り失敗する。
- device設定はXDG準拠のowner-only local configへ保存し、repo、skill、reportへhostを埋め込まない。
- 既定出力は短く、機械可読なversioned JSON。巨大dumpは明示`--output`へ書き、pathだけを返す。
- exit codeとerror codeを固定し、timeout、接続不能、wrong core、wrong ROM、stale command、illegal actionを区別する。
- source folder外から`command -v vega-codex-battle`、`--help`、`doctor`が成功するようにinstallする。
- `choose team`成功JSONは自動生成したteam preview PNGのowner-only absolute path、SHA-256、寸法を返す。
  PNGは双方6体だけを示し、どの3体を選んだかや選出順を表示しない。
- 対戦中のCodexは`wait --timeout 55 --json`で次の入力要求を待てる。OpenAI API keyや常駐daemonは必須にしない。
- CLIはteam、3体、move、switch、gimmick、報酬を自動選択せず、乱数policyや説明要求も持たない。
  Codexへ現在状態、公開情報、合法候補、安定error、操作方法だけを渡し、判断と発話は呼出元taskのpromptへ残す。

この方針はOpenAI公式のagent-friendly CLI指針に合わせ、composable command、predictable JSON、
setup/auth診断、safe write、別directoryからの実行検証を完了条件にする。

## 5. ROM mailbox契約

T26でStage 42のRAM mapを再監査し、既存ownerと重ならない連続EWRAMを確定する。addressをこの設計文書で
先に固定せず、`config/ram_layout.csv`、generated header、CLI protocol metadataの3者を同じgeneratorから作る。

mailboxは最低限、次を持つversioned fixed-width little-endian ABIとする。

- magic `VCBX`、protocol major/minor、struct size、capability bits、Stage identity
- bootごとの`session_nonce`
- ROMが公開する`snapshot_sequence`、payload size、CRC32、sequence inverse
- hostが書く`request_sequence`、command type、payload size、CRC32、sequence inverse
- ROMが返す`response_sequence`、status/error code
- phase、match ID、turn、公開battle snapshot、合法action mask

ROMはpayload→CRC→sequence/inverseの順で公開する。host writeもpayload→CRC→sequence/inverseの順とし、
ROMは同一frameで整合するpairだけを受理する。wrong version、wrong nonce、stale/future sequence、CRC不一致、
phase不一致、illegal actionは無変更で拒否する。CRC/nonceは事故・stale/replay防止であり、暗号認証ではない。
RetroArch NCIはplain UDPなので、信頼できる同一LANだけで使う。

Stage 44 protocol 2.2はSnapshotV2の96 byteとpublic stateの180 byteを固定したままphase unionを使う。
対戦中は旧Codex preview 12 byteをactiveの5実能力値とappearance/opaque IDへ、対戦前はlive HP領域12 byteを
player 6体のlevel/gender/shinyへ割り当てる。phaseと`battle_live`を確認せずunionを解釈しない。
`gBattlerPartyIndexes`はCFRU/FireRedどおり`u16[4]`としてbank 1を`+2` byteで読む。

## 6. 状態機械

```text
IDLE
  -> CONFIGURING
  -> TEAM_PREVIEW
  -> AWAITING_PLAYER_SELECTION / AWAITING_CODEX_SELECTION
  -> BATTLE_AWAITING_PLAYER / BATTLE_AWAITING_CODEX
  -> RESULT
  -> REWARD_WINDOW
  -> IDLE

通信異常:
任意のCodex待機phase -> DISCONNECTED -> WAIT / CPU_FALLBACK / FORFEIT
不正command         -> 同じphaseのままERROR応答
transport abort     -> ABORTED -> exact cleanup -> IDLE
```

`BATTLE_AWAITING_PLAYER`で受けたcommandはprivate action bufferへsealするだけでmailboxへ写さない。
Codex actionも同様にcommitし、双方が揃った時だけ通常battle controllerへ同時選択済み入力として渡す。
勝敗・forfeit・abortのcleanup後は、受付スクリプトの結果msgboxとreleaseが完了するまで
`field_completion_pending=1`を保持する。この期間は`active=0`でも新規configureを`BUSY`で拒否し、
結果／error script末尾の`CodexBattleRuntime_FieldFinish`だけがpendingを消して`IDLE`へ遷移する。
これにより、旧script世代の遅延cleanup callbackが次のmatch stateを終了させる競合を防ぐ。

## 7. iPad運用境界

- Network Commandsは可能ならRetroArch UIで有効化する。設定fileを直接変える場合はRetroArch停止、原本hash、
  新規backup、変更後再読込を必須とし、実行中fileをblind overwriteしない。
- iPadへ配置するROM/saveはversionedな新規filenameにし、既存ROM/saveを上書きしない。
- development testは専用save copyを使い、ユーザーの通常saveを破壊しない。
- NCI writeによりRetroAchievements hardcoreが無効化され得ることをdoctorと操作説明へ表示する。
- host key mismatch時にSSH設定を緩めない。NCIが使えない場合もsave pollingへfallbackせずT26をBLOCKEDにする。

## 8. タスク分割

- T26 / Stage 43: NCIを実機で有効化し、versioned mailbox、CLI doctor/status/ping、read/writeを実証する。
- T27 / Stage 44: 6体team登録、read-only構築catalog、双方3体選出、level option、構築ルール非強制、`UPSTREAM_OPEN` gimmick、
  pending action非公開、Codexのmove/switch/forfeit、cleanupを完成させる。
- T28 / Stage 45: 任意item/Pokémon報酬、exactly-once save、Codex companion skill、iPad実戦完走を完成させる。

## 9. 参照

- RetroArch Network Control Interface: https://docs.libretro.com/development/retroarch/network-control-interface/
- mGBA libretro memory map source: https://github.com/mgba-emu/mgba/blob/master/src/platform/libretro/libretro.c
- OpenAI / Create a CLI Codex can use: https://learn.chatgpt.com/use-cases/agent-friendly-clis
- Pokémon Showdown simulator protocol（公開event・HP・情報境界の比較対象）:
  https://github.com/smogon/pokemon-showdown/blob/master/sim/SIM-PROTOCOL.md
- fixed CFRU battle/public state構造の比較対象:
  https://github.com/Skeli789/Complete-Fire-Red-Upgrade/blob/master/include/battle.h
- FireRed controller/battle ABIの比較対象:
  https://github.com/pret/pokefirered/blob/master/include/battle.h
