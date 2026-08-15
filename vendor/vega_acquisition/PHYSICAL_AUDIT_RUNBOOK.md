# 物理監査・exact-ROM runbook

## A. 前提固定

1. 入力ROMを32 MiBへ展開済みの既存stageとする。
2. stage metadataのSHA-256と実ROMを一致させる。参考pinは `cb8ac173bf8f9e0e4bc51ecd12adc581c6344761955f38766ce7211e2dd5f167`。
3. `scripts/validate_acquisition_content.py` と再生成checkをPASSさせる。
4. repository固有engine adapterを実装し、ABI probeを1へする。
5. save/flag/var ownerとmigrationを既存policyへ登録する。

## B. Tohoku legacy audit

```bash
python scripts/audit_legacy_vega_events.py \
  --rom exact_stage.gba \
  --stage-metadata exact_stage.json \
  --package . \
  --output reports/legacy_event_candidates.json
```

候補を目視／script逆参照し、`manifests/legacy_event_bindings.template.csv`へmap group/map、event kind/local ID、script pointer、observed Species ID、completion stateを記入します。合格条件は、自然進行からentryへ到達し、対象IDが正しく、成功だけが共有ledgerへseedされ、撃破/escape/resetが再試行可能なことです。単なるbyte一致や場所名一致では昇格しません。

## C. 内部Speciesのwild漏れをsanitize

canonical ID 282の内部ストライクがmap 1/64と1/111のLANDへ漏れているため、runtime注入より前に公式ストライク255へ置換します。toolは265 headersを全走査し、blocklist 25 IDの未宣言出現、correction zero-match、patch後残存をすべて失敗にします。

```bash
python scripts/sanitize_internal_wild_species.py \
  --package . \
  --rom exact_stage.gba \
  --stage-metadata exact_stage.json \
  --output-rom build/exact_stage_sanitized.gba \
  --output-metadata build/exact_stage_sanitized.json \
  --report reports/wild_species_sanitization.json
```

## D. allocator

`manifests/allocation_requests.csv`の `acquisition_runtime` と `acquisition_map_scripts` を既存named allocatorへ渡します。出力contractには各nameのaddress、capacity、fill_byteが必要です。手入力raw addressは禁止。runtime/map allocation overlap、既存allocation overlap、declared fill mismatchは失敗です。

## E. runtime buildとstage serialize

```bash
python scripts/build_acquisition_runtime.py \
  --package . \
  --allocation-contract build/allocations.json \
  --adapter-source path/to/acquisition_engine_adapter_vega.c \
  --output-bin build/acquisition_runtime.bin \
  --output-symbols build/acquisition_runtime.symbols.json \
  --output-meta build/acquisition_runtime.metadata.json

python scripts/build_acquisition_stage.py \
  --package . \
  --input-rom build/exact_stage_sanitized.gba \
  --stage-metadata build/exact_stage_sanitized.json \
  --allocation-contract build/allocations.json \
  --runtime-bin build/acquisition_runtime.bin \
  --runtime-meta build/acquisition_runtime.metadata.json \
  --runtime-symbols build/acquisition_runtime.symbols.json \
  --output-rom build/vega_acquisition.gba \
  --output-metadata build/vega_acquisition.metadata.json
```

serializerはobject count、local ID、x/y/elevation、current script pointerをexact ROMから再検査してからscript pointerを置換します。

## F. acceptance

```bash
python scripts/run_exact_rom_acceptance.py \
  --package . \
  --rom build/vega_acquisition.gba \
  --stage-metadata build/vega_acquisition.metadata.json \
  --runtime-bin build/acquisition_runtime.bin \
  --emulator-result reports/mgba_all_cases.json \
  --require-emulator \
  --report reports/exact_rom_acceptance.json
```

mGBA resultは `tests/exact_rom_acceptance_cases.csv` の全case keyをPASSで含める必要があります。代表7縦切りだけでなく、全eventのlocked/cancel/reset/success/duplicate/full/save failure、captureのdefeat/escape、egg hatch、fossil missing inputを実行します。

## G. release判定

static PASS、generated reproducibility PASS、C runtime PASS、wild sanitation PASS、exact byte inspection PASS、mGBA全case PASS、legacy binding採否記録を揃えて `IMPLEMENTED_AND_TESTED` に昇格します。
