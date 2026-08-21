# T27 — Codex操作6→3対戦をStage 44へproduction統合する

- Lane: `engine/ui/content/tooling/qa`
- Depends on: `T26`

## 目的

T26の実iPad検証済みtransport/mailboxを使い、プレイヤー6体とCodex team 6体から双方3体を選出する
シングル対戦を通常プレイ入口へ接続する。CodexがCLIでteam選出、技、交代、降参を選べるStage 44を作る。

## 固定入力

- T26の正規出力`build/stages/43_codex_battle_bridge.gba`、metadata、protocol report、CLI。
- identityはT26完了commitとmetadataを正とし、T27開始時に再固定する。
- `design/codex_battle_architecture.md`とT26 `docs/CODEX_BATTLE_PROTOCOL.md`。
- Stage 42までのbattle controller、party selection、CreateMon、Factory/Mirage exact restore、battle rule/UIをbehavior oracleにする。

## 固定仕様

- 対戦は`SINGLE_3V3`固定。双方6体previewから3体を選び、選出順は相手へ公開しない。
- プレイヤーは現在party内のbattle可能な6体から標準party UIで3体を選ぶ。最低3体未満なら開始しない。
- Codexはversioned team JSONで正確に6体を登録し、CLIで3 slotを選ぶ。
- team JSONの省略fieldは同じsession seedから決定的に補完する。canonical ID/幅/個体安全性はfail-closed。
- 種族重複とcontent banlistは設けない。regulationは`FLAT_50|OPEN`と同一持ち物`ALLOW|DENY`だけ。
- `FLAT_50`はbattle copyだけ、`OPEN`は入力levelを使う。退出時にplayer party 600 byteをexact restoreする。
- battle bag、捕獲、逃走、EXP/EV/賞金/friendship/永続held-item消費を抑止する。
- Codex合法行動はmove、switch、forfeit。ROMが出したlegal maskにない入力は同じphaseのまま拒否する。
- Codexへは自team全情報と公開済みplayer情報だけを渡す。未公開move/item/abilityやraw save dumpを渡さない。
- Codex入力待ちはgame内に明示し、無期限WAITを既定とする。disconnect時はWAIT、CPU fallback、forfeitを選べる。
- CPU fallbackは固定CFRU AIを使い、再接続後に同じturnを二重実行しない。
- 通常battle、Factory、Mirage、Raid、Reward encounterのcontroller/stateへCodex commandを漏らさない。
- production入口は既存施設内の通常NPC/端末と標準menuを使い、debug menuだけにしない。

## CLI command surface

- `team validate --file ... --json`
- `match configure --level flat50|open --duplicate-items allow|deny --json`
- `match upload-team --file ... --json`
- `choose team 1,3,6 --json`
- `wait --timeout 55 --json`
- `choose move N [--target N] --json`
- `choose switch N --json`
- `choose forfeit --json`
- `match status --json`

全writeはsession/match/phase/request sequenceを明示し、成功時に受理されたsequenceと次phaseを返す。

## 実行

1. T26 Stage 43、protocol、CLI、iPad transport証跡を再確認する。
2. player/enemy party、party selection、battle controller、AI、battle end/cleanup、entry mapをrooted監査する。
3. team/rule/action/public snapshotのversioned schemaとprotocol capabilityを追加する。
4. Codex 6体生成、双方3体選出、battle-local level/item rule、相手controller待機を実装する。
5. move/switch/forfeit、disconnect WAIT/CPU/forfeit、再接続、stale command拒否を単一state machineへ接続する。
6. player partyと全battle副作用のbefore image/cleanupを実装し、全exitでexact restoreする。
7. 通常施設入口と標準UIを物理接続し、expected-byte付きStage 44を生成する。
8. host protocol matrix、exact-ROM mGBA quick/full、iPad first-turn vertical slice、clean rebuild/BPSを検証する。

## 必須成果物

- `content/codex_battle/**`
- `config/codex_battle_runtime.json`
- `overlays/codex_battle_runtime/**`
- `scripts/build_codex_battle_runtime.py`
- `scripts/rebuild_codex_battle_runtime_from_clean.py`
- `tools/mgba_codex_battle_runtime_smoke.c`
- `tests/test_codex_battle_runtime.py`
- `tests/fixtures/codex_battle_teams/**`
- `reports/generated/codex_battle_runtime_{audit,coverage,matrix}.json`
- `build/stages/44_codex_battle_runtime.gba`（Git管理外）
- Stage 43→44 BPS、clean→Stage 44 BPS、mGBA、clean rebuild証跡（Git管理外）

## 受入条件

- [ ] T26 Stage 43/protocol/CLI identityが一致し、iPad NCI doctorがPASSする。
- [ ] player 6→3とCodex 6→3が通常入口から完了し、双方の選出順を相手に漏らさない。
- [ ] exact 6-member team JSON、全省略値、invalid ID/width/EV/IV/move count、duplicate fieldを決定的に検査する。
- [ ] 種族重複は許可し、level 2 mode×duplicate item 2 modeの全4 regulationが仕様どおり動く。
- [ ] move、switch、forfeitの全合法分岐とillegal/stale/duplicate command拒否を実battle controllerで確認する。
- [ ] public snapshotが自team全情報、player公開情報、legal actionだけを含み、未公開情報を含まない。
- [ ] disconnect WAIT、再接続、CPU fallback、forfeitがdeadlock・二重turn・無限loopなしで完了する。
- [ ] 勝敗・降参・通信abort・resetの全exitでplayer party、level、EXP/EV、item、badge、RNG ownerをexact restoreする。
- [ ] battle後にEXP/EV/賞金/捕獲/永続item消費がなく、通常saveへ意図しないwriteがない。
- [ ] Codex stateが通常battle、Factory、Mirage、Raid、Reward encounterへ漏れない。
- [ ] iPad Stage 44でteam upload→双方選出→Codex最初の1手→safe abort/cleanupを実証する。
- [ ] ROM/RAM/save/UI/hook overlap、declared span外変更が0で、clean rebuild/BPS/mGBAがPASSする。

## 禁止する完了判定

- CPU AIをCodex入力と表示する、選出を固定する、相手6体をROMへhardcodeする実装をしない。
- playerの永続partyをLv.50へ書き換えない。
- raw EWRAM/saveを無制限にCLIへdumpしない。
- host-side state machineや1turn fixtureだけでDONEにしない。実battleの複数turn、交代、終了cleanupをmGBAで通す。

## 完了

1. task固有build/check、protocol matrix、mGBA、iPad vertical slice、clean rebuildをPASSする。
2. `design/run_log.md`と`design/version_log.md`へ証跡を追記する。
3. `python3 scripts/taskctl.py done T27 --summary "Codex操作6対3対戦をStage44へproduction統合"`を実行する。
4. task graph、private guard、`git diff --check`をPASSし、意図した差分だけをstageする。
5. `T27:`で始まるcommitを作る。pushしない。
