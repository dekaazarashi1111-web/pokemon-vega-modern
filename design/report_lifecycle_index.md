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

## reference

- `audit_seed/reports/conflict_report.json`: パッチのみの機械可読競合証跡
- `audit_seed/reports/conflict_report.md`: 269 ranges / 775 bytesの人間向け要約
- `audit_seed/reports/semantic_hotspots.md`: Move優先などの初期意味分析
- `audit_seed/reports/public_source_reference.md`: 初期監査時の公開source blob参照
- `design/imported/VEGA_CFRU_DPE_統合設計/`: 受領時点を保つ設計資料（review完了前）

## archive

- `audit_seed/reports/legacy_summary.json`: 現行 `conflict_report.json` に置き換えられた旧形式

## review

- `design/imported/VEGA_CFRU_DPE_統合設計/data/*.csv`: manifest整合性はPASS。意味上の不整合は `design/import_review.md` を参照。
- 受領資料を直接編集しない。修正済みschema/dataはT12等で `manifests/` / `content/` へ昇格する。
- 新しいレポートはactive / reference / archive / reviewのどれかと、生成条件（input hash、source commit、tool version）を明記する。
