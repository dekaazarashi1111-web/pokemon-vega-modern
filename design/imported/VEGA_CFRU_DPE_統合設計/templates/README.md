# 実装台帳テンプレート

このディレクトリは完成データではなく、ベガ実ROMの抽出・CFRU/DPEフック監査・リンカ配置を記録する作業台帳である。

- `species_id_map.csv`: 既存386枠＋追加820種。既存IDを固定してから新IDを割り当てる。
- `move_id_map.csv`: ベガ固有技とCFRU技を明示対応する。
- `item_id_map.csv`: 道具ID、ポケット、効果、イベント参照を一体で管理する。
- `ability_id_map.csv`: 効果、AI、表示文字列を同時に監査する。
- `hook_audit.csv`: 全フックの期待バイトとベガ実バイトを比較する。
- `saveblock_layout.md`: セーブ拡張領域の設計雛形。
- `build_manifest.json`: 実ビルド時にツール版、入力、出力、リンク結果を固定する。

`TEMPLATE`行は記入開始時に削除する。`linker.map`と`offsets.ini`は実ビルドでのみ生成されるため、この設計パッケージには偽物を置かない。
