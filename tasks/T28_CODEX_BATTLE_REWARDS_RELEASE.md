# T28 — 任意報酬とiPad最終ゲートをStage 45で完成させる

- Lane: `engine/save/tooling/release/qa`
- Depends on: `T27`

## 目的

T27のCodex 6→3対戦へ、対戦後にCodexが任意のitemまたはPokémonをID指定で付与できる
exactly-once reward windowを追加する。会話からCLIを操作するCodex companion skillを用意し、
iPadでルール相談→team登録→3体選出→対戦完走→任意報酬→save/restartまで通るStage 45を完成させる。

## 固定入力

- T27の正規出力`build/stages/44_codex_battle_runtime.gba`、metadata、protocol、CLI、team schema。
- identityはT27完了commitとmetadataを正とし、T28開始時に再固定する。
- T24/T25 reward/save transaction、acquisitionの`AddBagItem` / `CreateMon` / `GiveMon`、party/box容量処理。
- `design/codex_battle_architecture.md`。

## 固定仕様

- 正常にresultが確定した直近matchだけがreward windowを持つ。transport abort/stale sessionは対象外。
- 勝ち、負け、引分、明示forfeitのどれでもCodexが報酬有無を選べる。ROMに勝敗別固定報酬tableを置かない。
- `reward item ITEM_ID --quantity N`と`reward mon SPECIES_ID --level N`を最低限提供する。
- Pokémonはoptional team member schemaでmove、held item、ability、nature、IV/EV、shiny等を指定できる。
- item/Pokémonの価値、banlist、数量balanceをsystem ruleにしない。canonical ID、field幅、engine安全性、容量だけを検査する。
- itemは通常bag API、Pokémonは通常CreateMon/GiveMon経路を使い、PCからparty/save byteを直接書かない。
- 1 reward requestはsession nonce、match ID、request sequence、payload hashを持つ。
- PREPARED/STAGED/COMMITTEDまたは同等のjournalで、save fault、reset、retry、応答lost時の二重付与を防ぐ。
- bag/party/box満杯、invalid ID、生成失敗、save失敗では無変更または同一requestの安全な再試行になる。
- 複数報酬は別sequenceで付与し、`reward close`でwindowを不可逆に閉じる。close後や別matchからのreplayを拒否する。
- save owner追加・再利用は`config/save_layout.csv`で監査し、未使用byteへの暗黙相乗りを禁止する。
- companion skillはCodexへ最初にdoctor/statusを実行させ、readとwrite、reward付与を明確に区別する。
- 通常運用はユーザーがCodex taskで「Codex対戦を始めて」と依頼する形式。OpenAI API daemonを必須にしない。

## CLI/skill

- `reward status --json`
- `reward item ITEM_ID --quantity N --json`
- `reward mon SPECIES_ID --level N [optional fields] --json`
- `reward close --json`
- `session guide --json`または同等の短い運用状態表示
- companion skill sourceとinstallerを用意し、別Codex taskからCLIを発見・利用できるようにする。

skillは報酬内容を自動決定する固定policyを持たない。ユーザーとの会話でregulation、Codex team、
報酬内容を決め、実行前に現在match/result/reward windowを読み直す。

## 実行

1. T27 Stage 44、protocol、CLI、iPad vertical sliceのidentityを確認する。
2. acquisition/T24/T25/save migration、party/box/bag、save fault/rollback ownerをrooted監査する。
3. reward command/schema、match-bound authorization、journal、recovery state machineを実装する。
4. item/Pokémon grantと`reward close`をROM transactionへ接続し、Stage 45を生成する。
5. CLIへreward/status/closeとoptional Pokémon fieldを実装し、error/JSON契約を固定する。
6. Codex companion skillと日本語operator guideを作り、source folder外・別task相当環境で検証する。
7. host exhaustive transaction matrix、exact-ROM mGBA quick/full、save fault/reset/replayを検証する。
8. iPadへStage 45と専用save copyを新規filenameで配置し、Codex taskとユーザーの実対戦を最後まで通す。
9. reward後にsave/restart/loadし、付与内容、once性、party/box/bag、通常進行を再確認する。
10. Stage 44→45 BPS、clean→Stage 45 BPS、clean rebuildとStage 42〜44回帰を完了する。

## 必須成果物

- `config/codex_battle_rewards.json`
- `overlays/codex_battle_rewards/**`
- `scripts/build_codex_battle_rewards.py`
- `scripts/rebuild_codex_battle_rewards_from_clean.py`
- `tools/mgba_codex_battle_rewards_smoke.c`
- `tests/test_codex_battle_rewards.py`
- `tests/fixtures/codex_battle_reward_transactions.json`
- `docs/CODEX_BATTLE_OPERATOR_JA.md`
- `tools/codex_skills/vega-codex-battle/SKILL.md`
- `scripts/install_vega_codex_battle_skill.sh`
- `reports/generated/codex_battle_rewards_{audit,coverage,transactions,ipad_e2e}.json`
- `build/stages/45_codex_battle_rewards.gba`（Git管理外）
- Stage 44→45 BPS、clean→Stage 45 BPS、mGBA、clean rebuild証跡（Git管理外）

## 受入条件

- [ ] T27 Stage 44/protocol/CLI identityが一致し、iPad transport/first-turn gateがPASSする。
- [ ] 正常resultだけがmatch-bound reward windowを持ち、報酬なしでcloseできる。
- [ ] valid item ID/quantityとvalid Pokémon ID/levelの代表・全境界が通常bag/party/PCへ付与される。
- [ ] optional move/item/ability/nature/IV/EV/shinyがschemaどおりで、invalid fieldは無変更で拒否される。
- [ ] bag満杯、party満杯、box満杯、全収納満杯、invalid ID、生成失敗、save faultの全分岐がatomic。
- [ ] duplicate/stale/future/wrong match/wrong nonce/wrong hash/replayed rewardが二重付与0で拒否される。
- [ ] PREPARED/STAGED/COMMITTEDの各fault pointとreset/reloadから、同一requestがexactly onceへ収束する。
- [ ] 複数reward sequenceと`reward close`が正しく、close後の追加・再送を拒否する。
- [ ] reward save ownerが既存Acquisition/Research/Reward/Factory/Mirageと重複せず、version migrationを通す。
- [ ] companion skillが別task相当環境でCLIを発見し、doctor→status→wait→action→rewardの順を案内する。
- [ ] OpenAI API keyなしの通常Codex taskから会話ベースで対戦を運用できる。
- [ ] iPadでrule設定、6体登録、双方3体選出、複数turn、交代、勝敗、itemまたはPokémon報酬、save/restartを完走する。
- [ ] iPad既存ROM/saveを上書きせず、端末固有path/IP/credentialをtracked reportへ残さない。
- [ ] Stage 45のROM/RAM/save/UI/hook overlap、declared span外変更が0で、clean rebuild/BPS/mGBA回帰がPASSする。

## 禁止する完了判定

- PCからsave/party memoryを直接編集して報酬付与とみなさない。
- reward valueや勝敗条件をROMへhardcodeしない。
- host-only transaction、mock save、CLI JSONだけでDONEにしない。
- 実機で既存ROM/saveを上書きしない。専用copyが作れなければユーザーへ確認して停止する。
- companion skillにcredential、IP、private ROM/save pathを埋め込まない。

## 完了

1. task固有build/check、transaction matrix、mGBA、iPad E2E、clean rebuildをPASSする。
2. `design/run_log.md`と`design/version_log.md`へ証跡を追記する。
3. `python3 scripts/taskctl.py done T28 --summary "Codex任意報酬とiPad対戦E2EをStage45で完成"`を実行する。
4. task graph、private guard、`git diff --check`をPASSし、意図した差分だけをstageする。
5. `T28:`で始まるcommitを作る。pushしない。
