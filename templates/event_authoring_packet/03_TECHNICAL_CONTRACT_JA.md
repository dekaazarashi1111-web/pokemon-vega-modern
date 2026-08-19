# 技術契約

## 正本と参照順

矛盾がある場合は次の順で優先します。

1. `schemas/event_plan.schema.json`
2. `tools/validate_submission.py`
3. `catalogs/*.csv` / `catalogs/*.json`
4. この技術契約
5. `02_PROJECT_BRIEF_JA.md`
6. `catalogs/legacy_event_seeds.csv`（発想材料。実装案はREWRITE_REQUIRED）

## IDと名前

- ROM address、numeric flag、numeric var、numeric Species/Move/Item/Trainer IDを書かない。
- 新規キーはASCII大文字、数字、underscoreだけを使う。
- 新規event stateは `STATE_KEY_EVENT_*`、conditionは `CONDITION_KEY_EVENT_*`、actorは `ACTOR_KEY_EVENT_*`、placementは `PLACEMENT_KEY_EVENT_*` を使う。
- map、unlock、QOL、trainer encounter、acquisition host、reward、serviceはcatalogのキーだけを使う。
- numeric allocationは後続Codexが中央allocatorで行う。

## 許可する物理trigger

優先順位は次のとおりです。

1. `REPOINT_SOURCE_BG`: `BGHOST::*` のsign等を再利用。object cost 0。
2. `RESTORE_SOURCE_OBJECT`: `OBJHOST::*` の `AVAILABLE_RESTORE` を復元。object cost 1。
3. `REPOINT_SOURCE_COORD`: `COORDHOST::*` を使用。collision audit必須。
4. `ALLOCATE_SAFE_TILE`: catalogに適切なhostがない場合だけ使用。Codexが座標を決める。object cost 1、collision audit必須。
5. `NO_PHYSICAL_HOST`: 自動unlockや既存eventへの論理wrapperだけ。

`OCCUPIED_CURRENT_ROM`、`RESERVED_*`、`NO_CAPACITY` のhostは選択禁止です。座標、local ID、graphics numeric IDを手入力しないでください。

1 mapのlive object上限は15です。`event_plan.json` のplacementをmap単位で合算した結果が `catalogs/maps.csv` のfree object slotsを超えてはいけません。同じplacementを複数eventから共有するのは可能です。

## SIMPLE_EVENTで許可するstep

- `SHOW_DIALOGUE`
- `CHECK_CONDITION`
- `YES_NO`
- `SET_STATE`
- `GIVE_REWARD`
- `START_TRAINER_BATTLE`
- `CALL_ACQUISITION_HOST`
- `OPEN_SERVICE`
- `HEAL_PARTY`
- `WARP_SAFE`
- `END`

専用UI、camera choreography、長いmovement列、escort、timed input、独自minigame、専用map、専用animationをstepへ隠してはいけません。

## stateとtransaction

- 一度限りeventは、成功が確定する前に完了stateを立てない。
- rewardはbag/party/PC等の容量を先に確認し、失敗時はstate・所持数を変えない。
- battle開始前に必要なpending stateだけを保存し、勝敗・逃走・reset後の再試行を定義する。
- 一度限り報酬はclaim stateを持ち、event進行stateと分離する。
- `MONOTONIC_FLAG`は0→1だけ、`MONOTONIC_STAGE`は増加だけ。巻き戻しが必要な一時値はpersistent stateにしない。
- save/reload、whiteout、decline、bag full、party/PC fullの期待動作を各eventのfailure policyとacceptance testに書く。

## battle・取得・QOL

- 新規trainer partyを設計しない。既存encounter keyを参照する。
- trainerのMega/Z/Dynamax/Tera、AI、報酬、defeat flagは既存ownerを維持する。
- fixed encounterやgiftを新設せず、既存acquisition hostを参照する。
- QOLのengine実装をstepに記述せず、catalogのfeature/serviceを短い解禁・説明eventへつなぐ。
- `CURRENCY_KEY_RESEARCH_POINT`はDEFERREDなので、獲得・支払い・報酬に使わない。
- KantoからVega badge/HM/storyを書き換えない。

## 会話ABI

- `dialogue.csv` のtextはUTF-8で、改行を文字列 `\n` として書く。
- 1行18 glyph以内、1 message 2行以内。
- `catalogs/game_charmap.json` にない文字を使わない。漢字の多くは使えないため、ゲーム内textはひらがな・カタカナ中心にする。
- ページを増やす場合はdialogue rowと`SHOW_DIALOGUE` stepを分ける。
- actorの`display_name_game`もgame charmapでencode可能にする。

## 実装batch

- 1 batchは原則5〜15 event。
- 最初は `BATCH_KEY_PILOT_VERMILION` とし、クチバ周辺5〜10 event、依存はStage35だけ。
- batchは依存先より先に実行されないDAGにする。
- 各batchに対象map、state、回帰試験、rollback boundaryを記載する。
