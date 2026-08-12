# Codex Task 02 — Vega Move ID／技表をCFRUへ移植

## 目的

Vegaのストーリー、トレーナー、レベル技、イベントが参照するMove IDを壊さずに、
CFRU-JPの拡張戦闘エンジン、新技効果、技説明、技アニメーションを利用できる統合Move ID空間を作る。

## 前提

- Task 01の固定アドレス監査が完了していること。
- Clean FireRed、Vega reference、Factory referenceはローカルにのみ存在すること。
- ROMをGitへcommitしないこと。
- Factory UPSをVega referenceへ重ねないこと。

## 確認済みのVega側候補

- Move names: `0x08E0BBB0`, 0x1000 bytes = 512 × 8 bytes
- Battle move data: `0x08E0CBB0`, 0x1800 bytes = 512 × 12 bytes
- Following move-related table: `0x08E0E3B0`
- `gBattleMoves` repoint site: `0x080001CC`
- `gMoveNames` repoint site: `0x0804E7B4`
- `gBattleScriptsForMoveEffects` repoint site: `0x08015B78`
- `gMoveDescriptions` repoint sites: `0x080E63F0`, `0x081383A4`
- `gMoveAnimations` repoint site: `0x08071D74`

上記は候補なので、Vega referenceの実pointerとtable境界をコードで再検証すること。

## ID方針

Vegaのバイナリ資産を書き換える範囲を最小化するため、**VegaのMove ID 0–511を固定**する。

- Vegaと本家/CFRUで同じ技: Vega IDをcanonical IDとしてCFRU側definesを合わせる。
- Vega固有技: 既存Vega IDを維持し、CFRU形式のeffect/animation/descriptionを生成する。
- VegaにないCFRU/後世代技: ID 512以降へ追加する。
- Z技、Max技、内部専用技は、通常技と衝突しない予約blockへ置く。
- ID対応を手書きで複製せず、単一の`move_id_map.csv`からheaders/tablesを生成する。

## 実装するツール

1. `tools/extract_vega_moves.py`
   - Vega referenceから512件の技名と12-byte技データを抽出。
   - pointer siteとtable境界を検証。
   - 生データ、decode済みCSV、hashを出力。
2. `tools/build_move_id_map.py`
   - Vega名とCFRU名を正規化して候補matchを作成。
   - 自動match、手動確認、Vega固有、CFRU追加を分類。
3. `tools/generate_merged_moves.py`
   - `move_id_map.csv`からCFRU用`moves.h`、技データ、名前、説明、effect script、animation tableを生成。
4. `tools/validate_move_references.py`
   - すべての生成tableが同じ`NUM_MOVES`を持つことを検証。
   - 未定義ID、重複ID、範囲外IDをエラーにする。

## 必須成果物

- `data/move_id_map.csv`
- `data/vega_moves_raw.json`
- `generated/include/constants/moves_vega_merged.h`
- `generated/src/move_names.c`
- `generated/src/battle_moves.c`
- `generated/src/move_descriptions.c`
- `generated/src/move_effect_map.c`
- `generated/src/move_animation_map.c`
- `reports/move_port_report.md`

## 検証ゲート

1. 512件のVega Move IDが一件も移動していない。
2. Vega固有技の名前、タイプ、威力、命中、PP、effect、targetが抽出結果と一致する。
3. 全CFRU move constantが一意のIDへ解決する。
4. 技名／技説明の日本語表示が画面幅を超えない。
5. タイトル起動、通常戦闘、状態異常技、複数対象技、優先度技をsmoke testする。
6. Vega序盤のトレーナーと野生戦で未定義技やフリーズがない。
7. この段階ではSpecies ID、野生配置、進化を変更しない。

## 完了条件

Move IDと全関連tableが統合され、CFRU戦闘エンジン上でVega既存技を再現できること。
作業中のROM／生成ROMは成果物へ含めないこと。
