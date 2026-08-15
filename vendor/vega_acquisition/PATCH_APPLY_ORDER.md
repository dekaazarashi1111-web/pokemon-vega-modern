# PATCH APPLY ORDER

## 0. rollback単位

追加物は `content/`, `manifests/`, `schemas/`, `overlays/acquisition_runtime/`, `generated/`, `scripts/`, `tests/` の独立treeに置きます。既存mapへ直接手編集せず、serializer出力stageを破棄すればrollbackできます。ROM本体をsource controlへ入れません。

## 1. content import

全CSVをrepositoryへ追加し、`validate_acquisition_content.py` をCIへ登録します。ここではROMを変更しません。内部ID、route graph、unlock cycle、dialogue/FSM、host statusをfail-closed検査します。

## 2. generated source

`build_acquisition_content.py` を既存content buildの前段へ追加し、C table、host wrapper、map script manifestを生成します。生成差分がある状態をCIで拒否します。

## 3. engine adapter / save owner

`acquisition_engine_adapter.h` の全hookを現行CFRU-JP/DPE ABIへbindingします。save blockを既存allocatorへ要求し、version/CRC/migrationをsave load pathへhookします。fail-closed adapterはrelease linkから除外します。

## 4. symbols and allocations

item/move/unlock/script symbolsを既存manifest/allocatorへ登録。`allocation_requests.csv`をnamed allocatorへ渡し、runtime/map script領域を決定します。raw addressをcontentへ戻しません。

## 5. internal wild Species sanitation

clean exact stageに対して `sanitize_internal_wild_species.py` を先に実行します。`content/wild_source_corrections.csv` のmap/kind/from-ID selectorが各1 slot以上に一致し、blocklist 25 IDが全wild tableから消えた場合だけ次工程へ進めます。入力SHA、wild header root/count、全patch addressと出力SHAをmetadata/reportへ残します。

## 6. runtime link

`build_acquisition_runtime.py` をexisting ARM toolchainへ接続し、payload、symbol table、metadataを生成。最大requestはruntime 256 KiB、map scripts 4 KiBですが、実使用量をmetadataで記録し、既存32 MiB allocation mapとのoverlapを0にします。

## 7. map stage

wild sanitation済みstageへ `build_acquisition_stage.py` がruntimeを注入し、次にserializerが24 existing object scriptsを置換します。`PHYSICAL_COORD_AUDIT_REQUIRED` と `RESERVED_UNUSED_HOST` はemitされません。

## 8. exact acceptance

`run_exact_rom_acceptance.py --require-emulator` をrelease gateにします。全2035ケース、route 1216ケース、代表7縦切りを記録します。

## 9. legacy promotion

Tohoku legacy bindingが証明できた行だけprimaryへ昇格し、同じshared capture keyでKanto fallbackを抑止します。未証明行はKanto fallbackを残します。

## 10. release metadata

input/output SHA、wild sanitation report、allocator report、runtime payload hash、host patch list、mGBA case result、content hash manifestを既存release metadataへ追記します。
