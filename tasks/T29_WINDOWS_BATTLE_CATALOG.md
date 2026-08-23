# T29 — Windows対戦カタログをNPC前の一括生成導線へ接続する

- Lane: `engine/save/tooling/qa`
- Depends on: `T28`

## 目的

Windows側のcanonical catalogを再利用可能な対戦用保管庫として扱い、Codex対戦受付前の
安定したfield状態から、任意のPokémon・道具を通常bag／party／PCへ生成できるようにする。
Windows CLIは複数件を1操作として順次transactionし、不要個体の回収は既存のPC複数選択・
一括逃がしを正本とする。GBAの14箱や128 KiB save形式は拡張しない。

## 固定入力

- T28 Stage 45 ROM、metadata、protocol、symbols、任意報酬journal。
- `content/codex_battle/catalog.json` とcanonical Species／Move／Item／Ability manifest。
- T19のPC検索・複数選択・一括逃がしと通常save導線。

現行Stage 45は最初の物理baselineであり、Windows CLIとcatalog protocolを特定filenameや
単一ROM hashへ固定しない。後続ROMはversioned protocol／symbols／metadataを入力として
同じbuild/checkとCLIを再利用できること。

## 固定仕様

- catalog生成はCodex受付mapのoverworld、対戦runtime `IDLE`、通常入力可能時だけ許可する。
  battle、選出、result処理中、PC UI、script実行中、別mapでは無変更で拒否する。
- Pokémon生成はT28の通常`CreateMon`／`GiveMon`、道具生成は通常`AddBagItem`、永続化は
  現行save adapterとexactly-once journalを再利用する。hostからparty／box／save byteを
  直接編集しない。
- match-bound任意報酬のwindow、nonce、match、sequence、replay、close契約を弱めない。
  catalog requestは独立contextとして識別し、対戦報酬へ偽装しない。
- Windows側の一括操作は1件ずつ原子的にcommitし、最初の失敗で停止して成功件数・失敗行・
  再開位置をJSONで返す。同一request再送で重複生成しない。
- 全有効Species 1〜1620、Item 1〜998をcatalog検索・指定対象にする。容量、ID、level、move、
  ability、nature、IV／EV、色違い、Tera、ballの検査はT28と同じcanonical境界を使う。
- Windows catalogは再利用可能なtemplateであり、個体在庫を減算しない。固有個体のraw保管、
  cloud同期、GBA save pollingは本タスクのscope外。
- 回収は既存PC UIの複数box選択・一括逃がしを使う。通常持ち物はbagへ戻し、禁止個体、
  mail／key、bag満杯では既存all-or-rollbackを維持する。

## 必須成果物

- `config/windows_battle_catalog.json`
- `overlays/windows_battle_catalog/**`
- `scripts/build_windows_battle_catalog.py`
- `tools/mgba_windows_battle_catalog_smoke.c`
- `tests/test_windows_battle_catalog.py`
- `tests/fixtures/windows_battle_catalog_batch.json`
- `docs/WINDOWS_BATTLE_CATALOG_JA.md`
- `generated/runtime/windows_battle_catalog_protocol.json`
- `reports/generated/windows_battle_catalog_{audit,coverage}.json`
- `build/stages/46_windows_battle_catalog.gba`（Git管理外）

## 受入条件

- [x] Stage 45 exact baselineと既存saveを入力に、Stage 46を決定的に生成・checkできる。
- [x] NPC前IDLEでPokémon／itemの単件と1・6・30件batchが通常収納へ生成される。
- [x] invalid ID、容量不足、別map、PC UI、battle/result中、通信再送、save faultが無変更または
      exactly-onceへ収束し、batchは成功位置を正確に返す。
- [x] 対戦後rewardの複数付与、close、save/restartとT27対戦処理が不変。
- [x] 既存PC複数選択・一括逃がしが複数box、持ち物返却、禁止個体、bag満杯、save/reloadで不変。
- [x] CLIがprotocol／catalog metadataを発見し、特定ROM filenameや端末固有pathを要求しない。
- [x] ROM/RAM/save/hook overlapとdeclared span外変更が0で、focused mGBA quick/fullがPASSする。

## 完了

1. task固有build/check、host batch test、exact-ROM mGBA quick/fullをPASSする。
2. `design/current_state.md`、`design/run_log.md`、`design/version_log.md`へ日本語で追記する。
3. `python3 scripts/taskctl.py done T29 --summary "Windows対戦カタログをStage46へ統合"`を実行する。
4. task graph、private guard、`git diff --check`をPASSし、意図した差分だけをstageする。
5. `T29:`で始まるcommitを作る。pushしない。
