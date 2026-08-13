# report_lifecycle_index.md

プロジェクト内のレポート、調査メモ、検証結果の状態を管理するための索引です。

## active

- `design/current_state.md`
- `design/agent_context_map.md`
- `design/catalog.md`
- `design/import_inventory.md`: 私有入力のhashと配置を公開可能な情報だけで記録
- `design/import_review.md`: 受領資料の採否、既知課題、優先順位
- `state/source-lock.json`: bootstrap後の入力hash・上流commit
- `reports/generated/`: 現在の入力/source pinから再生成するローカル監査（Git管理外）
- T02 exact audit 11成果: `make t02-audit` で生成し、`make t02-check` が一時再生成byte一致、fixed-write/ROM/state意味契約、UNKNOWN 0を検証する。入力policy SHA-256は `d06c0895a24d67317beb40d73619a584f88ae391a05f7fd09af3b2271c2f4429`。
- T03 harness: `make harness` が `reports/generated/harness_smoke.md` と `build/stages/03_harness.{gba,json}` を生成し、`make harness-check` が現在の入力/config fingerprint、Vega-owned byte一致、module配置、allocation reportを照合する。
- T04 move port: `make moves` が `reports/generated/move_port.md`、`build/stages/04_moves.{gba,json}`、`generated/engine/moves/`、`manifests/move_ids.csv` を生成し、`make moves-check` が1063技model、V3 131行、70 adapter、178 repoint、allocation、ROM、runner identityを現在入力から照合する。
- T05 ID space model: `python3 scripts/build_id_spaces.py build` が `reports/generated/id_space_report.md`、`generated/engine/ids/`、Type/Ability/Item manifestを生成し、同`check`が999 itemを含む13成果のbyte一致、host/ARM C compile、公開header共存を副作用なしで照合する。ROM stageとallocator配置はT06で行う。

`reports/generated/**` は `make clean-build` で削除可能なため、タスク完了時は生成コマンド、入力/source/config/tool fingerprint、主要成果hashを `design/run_log.md` または追跡対象manifestへ残す。生成レポートだけを唯一の跨セッション証跡にしない。

## reference

- `audit_seed/reports/conflict_report.json`: パッチのみの機械可読競合証跡
- `audit_seed/reports/conflict_report.md`: 269 ranges / 775 bytesの人間向け要約
- `audit_seed/reports/semantic_hotspots.md`: Move優先などの初期意味分析
- `audit_seed/reports/public_source_reference.md`: 初期監査時の公開source blob参照
- `design/imported/VEGA_CFRU_DPE_統合設計/`: V2に置き換えられたV1来歴資料

## archive

- `audit_seed/reports/legacy_summary.json`: 現行 `conflict_report.json` に置き換えられた旧形式

## review

- `design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/`: 二地方設計のactive review資料。JSON/SHA manifestは47/47 PASS。
- `design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/data/*.csv`: 付属59検査はPASSしたが、V1由来の意味不整合は `design/import_review.md` を参照。
- 受領資料を直接編集しない。修正済みschema/dataはT12等で `manifests/` / `content/` へ昇格する。
- 新しいレポートはactive / reference / archive / reviewのどれかと、生成条件（input hash、source commit、tool version）を明記する。
