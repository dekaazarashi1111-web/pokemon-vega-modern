# Trainer ChangeKit final runtime

`trainer_changekit_final_runtime.c` は、Stage 34 の Trainer V5 ABI を保ったまま、最終 ChangeKit の生成表を消費する runtime です。グローバル `FlagGet/Set/Clear` は置換せず、trainer 専用 hook と生成済み consumer 行だけへ作用します。

## 生成 header ABI

ビルダーは runtime のコンパイル前に `trainer_changekit_final_generated.h` を生成します。次の packed 構造体と、キー順にソート済みの配列が必要です。

- `TrainerChangeKitMemberSidecarV1` / `gTrainerChangeKitMemberSidecars`: 18 byte、キー `(trainer_id, side, slot)`。species/level/nature/EV/IV/ability slotと、種族の通常枠外も含む指定ability IDを保持。CFRUの任意level scaling後もChangeKitの固定species/levelへ戻してstatsを再計算
- `TrainerChangeKitExactBindingV1` / `gTrainerChangeKitExactBindings`: 12 byte、キー `(data_address, source_trainer_id, kind)`。canonical 行の `dispatch_id` は 0
- `TrainerChangeKitRematchV2` / `gTrainerChangeKitRematchMap`: 8 byte、exact command address と物理 source から rematch target を解決
- `TrainerChangeKitArchiveBindingV1` / `gTrainerChangeKitArchiveBindings`: 16 byte、`archive_id` 一意・昇順
- `TrainerChangeKitGimmickV1` / `gTrainerChangeKitGimmicks`: 12 byte、キー `(trainer_id, dispatch_id)`
- `TrainerChangeKitFlagMapV1` / `gTrainerChangeKitFlagMap`: 4 byte、`external_flag` 昇順

さらに各 `TRAINER_CHANGEKIT_FINAL_GENERATED_*_COUNT`、`TRAINER_CHANGEKIT_FINAL_TRAINER_TABLE_ADDRESS`、4284件以上の trainer table が必要です。runtime は encounter catalog が 1,302 行でない header をコンパイル時に拒否します。

## production hook 接続

既存9個の Stage 34 Trainer V5 hook は同名の `TrainerV5Runtime_*` wrapper へ接続できます。それに加え、`user_party_slot` を実戦で強制するには、CFRU の Can/Mark 呼出元を `TrainerChangeKitFinalRuntime_Can*Adapter` / `Mark*Adapter` へ接続する必要があります。adapter は player side と非 consumer battle を元の `VegaBattlePolicy*` へそのまま委譲し、active な opponent consumer だけ `gBattlerPartyIndexes` の0始まり slot を照合します。

Battle lifetime は CFRU 内の唯一の Begin/End 呼出元を `PolicyBeginAdapter` / `PolicyEndAdapter` へ置換します。これにより pending state は実際の battle 開始時だけ active になり、勝敗を問わず CFRU cleanup の直後に消えます。`Save_LoadGameData` entry は `SaveLoadAdapter` へ long-jump し、元の先頭命令を再配置した trampoline を経由します。PC-relative `ldr` があるため、元の8 byte をそのまま trampoline へコピーしてはいけません。

対象 address、expected bytes、元 target、adapter symbol、24-byte save trampoline は `hook_contract_stage34.json` が正本です。全17個のpolicy Thumb BL、ability load BL、save entry は、Stage 34 ROM SHA-256 が一致した場合だけ書き換えます。ability adapterは初期登場と交代の双方で、指定ability IDをlive `BattlePokemon`へ適用します。

## lifecycle と安全側動作

- canonical binding は exact tuple が一意の場合だけ target を差し替えます。同じ tuple が複数なら物理 source のまま fail closed します。
- archive 選択は one-shot です。`archive_id` に対応する address/source/kind/SINGLE・DOUBLE が一致しなければ破棄します。
- kind 4/6/7/8 を DOUBLE として検証します。
- kind 5/7 の proxy rematch は active exact context を stock resolver の0より先に解決します。context がない stock 0 は従来どおり availability gate として保持します。
- Mega/Z/Dynamax/Terastal は既存 CFRU policy が one-use と相互排他を所有します。runtime は指定 user slot を追加制約として重ねます。
- Tera type は CFRU Begin が復元用 backup を取得した後に、指定 opponent slot の `teratype` だけへ適用します。通常終了、敗北、abort、save/reload は元の `VegaBattlePolicyEnd` を通るため backup が復元されます。
- switch/faint 後は active battler の party index を再走査し、指定 user が不在なら local activation state を解除します。再登場時は CFRU one-use が未消費の場合だけ再び eligible です。

## 検証

```bash
python3 -m unittest tests.test_trainer_changekit_final_runtime -v
```

このテストは host C fixture、ARM7TDMI production compile、Stage 34 ROM の expected bytes/BL target/save literal relocationを検証します。
