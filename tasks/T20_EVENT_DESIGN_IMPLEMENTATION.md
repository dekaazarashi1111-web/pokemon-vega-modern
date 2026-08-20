# T20 — Integrate implementation-ready event design

- Lane: `maps/content/engine/save/qa`
- Depends on: `T19`

## 目的

T19完了済みのStage 36を固定baselineとし、ユーザー提供の
`Pokemon-Vega_EVENT-DESIGN_IMPLEMENTATION-READY.zip`に収録されたカントーイベント設計を、
設計・catalog・host fixtureで終わらせず、通常プレイから到達できる実map event、会話、進行状態、
既存trainer/acquisition/QOL service、save/reloadへ接続し、Stage 37として決定的に再構築する。

## 固定入力

### 現行baseline

- Git commit: `df52e8c89cc1fd6b2352bc7a98fedf3be8ad72be`
- ROM: `build/stages/36_qol_production.gba`
- ROM SHA-256: `c262fbb121957950f890c7b28ab64b19f9bc8fdf541b543747c39ab1f7c381dd`
- ROM size: 33,554,432 bytes
- metadata: `build/stages/36_qol_production.json`
- metadata SHA-256: `f901673fb0eef34ac9fdad6585697007f1077e16d42f84a36dbcb79433a34bce`
- Stage 35の1,302 trainer / 6,490 member / 74 DOUBLE / 201 Kanto trainerと、T19のQOL 35/35機能・97 hook・保存transactionを回帰不変条件とする。

### 受領設計ZIP

- 読取専用原本: `userfile/imports/Pokemon-Vega_EVENT-DESIGN_IMPLEMENTATION-READY.zip`
- Size: 71,084 bytes
- SHA-256: `576847447f0c659c3db639179aa1fa71057b909d8eff5b408ba725ee285fee8e`
- ZIP: 6 files、展開後755,156 bytes、CRC PASS、unsafe path / symlink / encrypted entry 0。
- submission SHA-256: `776d8c911ad3c2705ffdaf840d1b6cdbefe816cf000accdf3ea47a45991c4fec`
- validator: PASS、warnings 0、errors 0、open questions 0。
- 収録数: 28 arcs、80 states、14 actors、63 placements、160 conditions、7 rewards、76 events、7 batches、326 dialogues、98 coverage rows。

`userfile/**`のZIP原本は変更・追跡・ステージしない。実装用の正規化入力は安全展開後に別のGit管理対象へ生成し、原文との対応hashを保持する。

## Stage 35設計のStage 36へのrebase原則

受領bundleのauthoring catalogはStage 35 commit `993e1419caa0a51d78ac15be8e2caad042470549`、
ROM SHA-256 `2ff8d61d7e17d120eaf60a81863dc29f6666d84c48a245e1be3d8dfa2447d180`を基準に作られている。
そのため次を必須とする。

- `event_plan.json`のsymbolic keyと仕様を正とし、Stage 35 catalogのnumeric address、pointer、free-space、object budgetをStage 36へ盲目的に流用しない。
- 63 placementのphysical host、map object/bg/coord record、collision、warp、trainer sight、local ID、script root、expected bytesをStage 36実ROMとrooted graphから再解決する。
- 80 stateを中央flag/var/save allocatorへsymbolic keyで割り当て、既存Vega/Kanto/Factory/acquisition/QOL ownerとの衝突を0にする。
- QOLはStage 35 authoring catalogの古いprofileではなく、T19の`config/qol_production_bindings.csv`と`overlays/qol_production/service_abi.md`へ接続する。
- Stage 36差分で物理hostまたは意味が変わっていれば、別のsymbolic hostへ明示的に再結合する。判断できない場合は推測せずblockerとする。

## 所有範囲

このタスクが所有するもの:

- 受領bundleの安全検証、正規化、provenance、Stage 36 binding ledger。
- event state/condition/reward/placement/stepのserializer、field script、text、dispatcher、save migration。
- 7 batchのproduction map event接続と各batchのfocused test / rollback boundary。
- Stage 36→37 build、clean FireRed日本版Rev.0からの再構築、BPS、mGBA quick/full。

このタスクが再設計しないもの:

- 受領bundleの物語、発生条件、state遷移、報酬、失敗時挙動、会話、batch依存。
- 既存trainer party/AI/gimmick/reward/defeat flag、acquisition transaction、QOL engineの能力本体。
- Vega badge/HM/story state、Factory経済、既存取得台帳の意味。
- 専用full-screen UI、専用map、長いcutscene、独自minigame。

## 実行

1. 原ZIPのsize/hashとエントリ安全性を再検証し、生成catalog付きauthoring packet validatorでPASSさせる。同梱`VALIDATION_REPORT.json`だけを完了証拠にしない。
2. 6ファイルをスキーマ保持の正規化正本へ変換し、件数、symbolic reference、dialogue `next_step_key`、coverageの一致を固定する。
3. Stage 36 rooted graphからphysical placementを再監査し、`REPOINT_SOURCE_BG`、`RESTORE_SOURCE_OBJECT`、`REPOINT_SOURCE_COORD`、`ALLOCATE_SAFE_TILE`、`NO_PHYSICAL_HOST`を実体化する。mapごとのlive object上限15と安全座標を守る。
4. state/conditionを一度だけcompileし、`MONOTONIC_FLAG`は0→1、`MONOTONIC_STAGE`は増加だけとする。Stage 36 saveを読み込んだ際のzero/default migrationを明示する。
5. `dialogue.csv`を現行game charmapでencodeし、18 glyph/line、2 lines/message、全6文字Species表示、control code、choice復帰を検査する。
6. `BATCH_KEY_PILOT_VERMILION`を最初の動く縦切りとし、その後`batches[].depends_on`のtopological順に全7 batchを実装する。batchごとに入力hash、所有file、focused test、rollback可能なcheckpointを残す。
7. `SHOW_DIALOGUE`、`CHECK_CONDITION`、`YES_NO`、`SET_STATE`、`GIVE_REWARD`、`START_TRAINER_BATTLE`、`CALL_ACQUISITION_HOST`、`OPEN_SERVICE`、`HEAL_PARTY`、`WARP_SAFE`、`END`を既存ABIへcompileする。helper直呼びだけで完了しない。
8. decline、bag full、party/PC full、戦闘勝敗・全滅・reset、save failure、中断transactionで、完了/claim state、報酬、所持数に部分更新がないことを実ROMで確認する。
9. Stage 36へexpected-byte付きhook/repointを適用し、Stage 37を生成する。allocator、RAM、save、map object、trainer table、CFRU/QOL hook所有重複を0にする。
10. 通常のfield/map/NPC/bg/coord入力で全76 eventを到達させ、acceptance fixture、mGBA quick/full、clean rebuildをPASSさせる。

## 必須成果物

- `content/event_design_implementation/**`（正規化設計、provenance、source manifest）
- `config/event_design_bindings.csv`
- `overlays/event_design/**`
- `scripts/build_event_design_stage.py`
- `scripts/rebuild_event_design_from_clean.py`
- `tools/mgba_event_design_smoke.c`
- `tests/test_event_design_implementation.py`
- `reports/generated/event_design_{audit,coverage}.json`
- `build/stages/37_event_design.gba`（Git管理外）
- Stage 36→37 BPS、clean→Stage 37 BPS、clean rebuild証跡（Git管理外）

既存生成器やoverlayを再利用する方が安全な場合は、上記名の薄いadapterと同等の機械可読証跡を用意してよい。空stubは不可。

## 受入条件

- [ ] 原ZIPの71,084 bytes / SHA-256、6 entry、submission SHA-256が固定値と一致し、catalog付きvalidatorがwarnings/errors/open questions 0でPASSする。
- [ ] 28 arcs / 80 states / 14 actors / 63 placements / 160 conditions / 7 rewards / 76 events / 7 batches / 326 dialogues / 98 coverage rowsを欠落・重複0で実装する。
- [ ] Stage 35 catalogの全63 placementをStage 36で再監査し、host unresolved、所有競合、object budget超過、collision/warp/trainer sight異常、古いexpected byteの流用が0。
- [ ] 76 eventが通常プレイのfield/NPC/bg/coord/auto-unlock入口から到達でき、helper直呼びに依存しない。
- [ ] 全7 batchをDAG順に接続し、pilot、前半4認定、殿堂入り後再開、8認定・Kanto League、Sphere共鳴・Final League完結が各gateで成立する。
- [ ] 326会話の全文字、改行、`next_step_key`、choice、actor名が実ROMで保持され、encode不能・overflow・途中切れ0。
- [ ] 一度限りevent/rewardは成功後だけcommitし、decline、容量不足、敗北/全滅、reset、save failureで増殖・消失・二重claim・進行飛び0。
- [ ] Stage 36既存saveの読込、各batch進行中のsave/reload、完了saveの再読込でstateが一致し、Vega badge/HM/storyを書き換えない。
- [ ] 8認定戦とLeagueが既存encounter ownerを呼び、trainer party/AI/gimmick/reward/defeat flagを重複生成しない。
- [ ] acquisition、reward、heal、warp、QOL serviceがそれぞれ既存production transaction/ABIへ接続し、QOL 35/35の一意ownerを維持する。
- [ ] Stage 36の1,302 trainer、74 DOUBLE、6,490 member、201 Kanto trainer、Mega/Z/Dynamax/Tera、Factory、Raid、取得イベント201件、QOL 35機能、save cleanupが回帰PASSする。
- [ ] Stage 37がclean FireRed日本版Rev.0から決定的に再構築でき、Stage 36差分BPSとclean直接BPSが完全往復し、declared span外変更0。
- [ ] allocator/RAM/save/map object/trainer/CFRU/QOL所有重複0、mGBA quick/full独立2 processがwarnings/errors 0かつresult identity一致でPASSする。
- [ ] 操作説明、event正本、binding ledger、coverage、実buildが一致し、全47論理地点にcoverageがある。

## 禁止する完了判定

- 受領ZIPを展開・コピーし、validatorをPASSさせただけでDONEにしない。
- Stage 35 catalogのhost address、numeric ID、free-spaceをStage 36へ無監査で流用しない。
- design bundle、script graph、host fixture、host-side model、runtime probeだけで「実装済み」と報告しない。
- 7 batchの一部だけを通し、76 event完了としない。
- 入力不足がない仕様をDEFERへ落としたり、文章から新仕様を推測したりしない。

## 完了

1. task固有のbuild/check、focused tests、全7 batchの実ROM入力、mGBA quick/full、clean rebuildをPASSする。
2. `design/run_log.md`と`design/version_log.md`へ証跡を追記する。
3. `python3 scripts/taskctl.py done T20 --summary "実裁76イベントをStage37へ統合しclean rebuildを検証"`を実行する。
4. 最終indexに意図した差分だけをstageし、task graph、private guard、`git diff --check`をPASSする。
5. `T20:`で始まるcommitを作る。pushしない。
