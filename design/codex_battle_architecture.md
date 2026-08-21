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
- system上の固定regulationは次の2項目だけとする。
  - `level_mode`: `FLAT_50` / `OPEN`
  - `duplicate_held_items`: `ALLOW` / `DENY`
- `OPEN`のlevelはengine-safeな1〜100。`FLAT_50`はbattle copyだけをLv.50相当にし、永続個体を変更しない。
- battle中のbag item、捕獲、逃走、賞金、EXP、EV、friendship、held item消費の永続化を禁止する。
- 合法行動は`MOVE`、`SWITCH`、`FORFEIT`。disconnect時は`WAIT`、`CPU_FALLBACK`、`FORFEIT`を選べる。

### 3.2 Codex側team入力

team JSONはversion付きで、6 memberを持つ。各memberは最低限`species_id`と`level`を持ち、
`moves`、`held_item_id`、`ability_slot`、`nature_id`、`ivs`、`evs`、`shiny`を省略可能にする。
省略値はROM側で決定的に生成し、同じJSONとsession seedから同じ個体を作る。

指定内容の対戦バランスや通常の習得可否はユーザーとCodexの会話で決める。ROM/CLIはcanonical ID、
field幅、個体値・努力値合計、技数、item pocket等の構造安全性だけを検証する。

### 3.3 情報境界

- team previewでは双方の6 speciesと公開情報を見せ、選出した3体の順番は公開しない。
- Codexは自分のteam情報を全て読める。
- プレイヤー側の技、持ち物、能力等はbattleで公開された範囲だけをsnapshotへ載せる。
- CLIはROM構造体や未公開save領域を任意読取するdebug commandをproduction interfaceへ公開しない。

### 3.4 任意報酬

- 正常に結果が確定した直近matchだけがreward windowを開ける。transport abortやstale sessionは対象外。
- Codexは報酬なし、item、Pokémonを任意に選べる。勝敗と報酬内容の固定tableや価値上限を設けない。
- itemはcanonical numeric IDと数量、Pokémonは最低限species IDとlevelで指定できる。
- Pokémonには必要に応じて技、持ち物、性格、色違い等を追加指定できる。
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
vega-codex-battle team validate --file TEAM.json --json
vega-codex-battle match configure --level flat50|open --duplicate-items allow|deny --json
vega-codex-battle match upload-team --file TEAM.json --json
vega-codex-battle choose team 1,3,6 --json
vega-codex-battle wait --timeout 55 --json
vega-codex-battle choose move 2 --json
vega-codex-battle choose switch 3 --json
vega-codex-battle choose forfeit --json
vega-codex-battle reward item ITEM_ID --quantity N --json
vega-codex-battle reward mon SPECIES_ID --level N --json
vega-codex-battle reward close --json
```

- read、wait、writeを別subcommandにし、writeは期待phaseとsession/request sequenceが一致しない限り失敗する。
- device設定はXDG準拠のowner-only local configへ保存し、repo、skill、reportへhostを埋め込まない。
- 既定出力は短く、機械可読なversioned JSON。巨大dumpは明示`--output`へ書き、pathだけを返す。
- exit codeとerror codeを固定し、timeout、接続不能、wrong core、wrong ROM、stale command、illegal actionを区別する。
- source folder外から`command -v vega-codex-battle`、`--help`、`doctor`が成功するようにinstallする。
- 対戦中のCodexは`wait --timeout 55 --json`で次の入力要求を待てる。OpenAI API keyや常駐daemonは必須にしない。

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

## 7. iPad運用境界

- Network Commandsは可能ならRetroArch UIで有効化する。設定fileを直接変える場合はRetroArch停止、原本hash、
  新規backup、変更後再読込を必須とし、実行中fileをblind overwriteしない。
- iPadへ配置するROM/saveはversionedな新規filenameにし、既存ROM/saveを上書きしない。
- development testは専用save copyを使い、ユーザーの通常saveを破壊しない。
- NCI writeによりRetroAchievements hardcoreが無効化され得ることをdoctorと操作説明へ表示する。
- host key mismatch時にSSH設定を緩めない。NCIが使えない場合もsave pollingへfallbackせずT26をBLOCKEDにする。

## 8. タスク分割

- T26 / Stage 43: NCIを実機で有効化し、versioned mailbox、CLI doctor/status/ping、read/writeを実証する。
- T27 / Stage 44: 6体team登録、双方3体選出、2 regulation、Codexのmove/switch/forfeit、cleanupを完成させる。
- T28 / Stage 45: 任意item/Pokémon報酬、exactly-once save、Codex companion skill、iPad実戦完走を完成させる。

## 9. 参照

- RetroArch Network Control Interface: https://docs.libretro.com/development/retroarch/network-control-interface/
- mGBA libretro memory map source: https://github.com/mgba-emu/mgba/blob/master/src/platform/libretro/libretro.c
- OpenAI / Create a CLI Codex can use: https://learn.chatgpt.com/use-cases/agent-friendly-clis
