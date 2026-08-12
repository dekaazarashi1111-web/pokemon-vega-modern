# Codex Task 01 — Vega × DPE/CFRU 移植前監査

## 目的

Pokemon Vega 2018-02-23のストーリー、マップ、イベント、固有ポケモンを維持したまま、
DPE-JP/CFRU-JPのポケモン拡張と戦闘機能を移植する。
Factory UPSをVegaへ直接重ねてはならない。

## 入力

ユーザーがローカルで用意するもの：

- FireRed日本版Rev 0 clean ROM — CRC32 `3B2056E9`
- Vega IPS
- Factory UPS
- DPE-JP source
- CFRU-JP source

ROMと生成ROMをGitへcommitしないこと。

## このタスクで実施すること

1. `tools/build_reference_roms.py`でVega referenceとFactory referenceを別々に生成する。
2. `reports/conflicts.csv`の269件を起点に、各競合を以下へ分類する。
   - `PORT`: Vegaの既存関数／テーブルへCFRU/DPE機能を接続し直す
   - `RELOCATE`: 32 MiB拡張領域へコード／データを移動する
   - `VEGA`: Vega実装をそのまま採用する
   - `CFRU`: CFRU実装を採用しVega側呼出し元を適応する
3. DPE-JP/CFRU-JP内の固定ROMアドレスを全抽出し、Vega referenceがcleanから変更した場所を検出する。
4. 直接競合だけでなく、次を監査する。
   - ROM pointer/repoint dependencies
   - RAM addresses
   - save-block layout
   - script command/special IDs
   - Species IDs
   - Move/Ability/Item IDs
   - Pokedex and evolution tables
5. `audit/fixed_address_audit.csv`と`audit/semantic_conflicts.md`を生成する。
6. この段階では統合ROMを生成しない。

## 必須方針

- VegaのSpecies IDを移動しない。
- Vegaに存在する本家ポケモンは重複追加せず、ID mappingでDPE側から参照する。
- Vegaに存在しないポケモンだけを後続IDへ追加する。
- 野生出現、トレーナー、進化条件の調整はエンジン移植後に行う。
- ストーリー、マップ、NPC、BGMはVega優先。
- 戦闘エンジン、新技、新特性、新アイテム、新進化方式はCFRU優先。ただしVega側呼出し元を手動適応する。

## 完了条件

- 全固定アドレスについて、clean/Vega/Factoryの3者比較がある。
- 未分類競合が0件、または理由付きで明示される。
- ROMや著作物バイナリがリポジトリに含まれていない。
