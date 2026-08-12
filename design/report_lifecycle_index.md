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
