# コンテンツ生成パイプライン

## 設計と実装を分離

野生出現、トレーナー、アイテムはT12から設計できます。数値IDの確定を待つ必要はありません。

```text
CSV/YAML相当のsymbolic spec
  -> schema validation
  -> ID resolution
  -> generated C/ASM/binary tables
  -> ROM insertion
```

## 二地方共通キー

すべての配置行は `region_key`（`TOHOKU` / `KANTO`）と安定した `map_key` を持つ。V2の論理地点コードはreview入力であり、T11のphysical map crosswalkと解決してからROM用Map IDへ変換する。

V2 CSVを取り込む前に次を正規化する。

- 全国番号を整数文字列へ統一する。
- 進化のfrom/toフォームキーを追加する。
- ID以外が同一の進化行を意味単位で統合する。
- 進化条件が参照する全道具・counterをregistryへ登録する。
- V2記載の数値IDを直接採用せず、symbolへ置換する。

## 野生・生態overlay

カントーの新規表とトーホクの非破壊overlayを別policyで生成する。

主要列:

- `map_key`
- `method`: land/water/rock_smash/old_rod/good_rod/super_rod
- `slot`
- `species_key`
- `level_min`, `level_max`
- `condition`
- `layer`: original / overlay / dexnav / time / outbreak / fixed
- `fallback_policy`

トーホクは抽選不成立時に元Vega表へ戻り、既存11/12枠を直接書き換えない。カントーは新規表を生成し、元FireRedを象徴する系統の最低比率をvalidatorで検査する。

## トレーナー

トレーナー表は1匹につき1行とし、`region_key`を持つ。

- `trainer_key`
- `party_slot`
- `species_key`
- `level`
- `move1_key` ... `move4_key`
- `item_key`
- `ability_policy`
- `nature`
- `ai_profile`

## アイテム

item ball、hidden item、NPC reward、gym rewardを一つのsymbolic schemaで扱い、取得flagは地方名前空間へ解決する。

## Generator要件

- unresolved keyをエラーにする。
- duplicate slotをエラーにする。
- 同一map/conditionで不正なslot数をエラーにする。
- Trainerのparty slot重複をエラーにする。
- 全生成物にsource manifest rowを追跡できるコメントまたはmapを付ける。
- 541系統に両地方導線があるか、特殊個体125種の捕獲flagが一意かを検査する。
- 未解禁のトーホクoverlayが元Vega結果と一致することをfixtureで検査する。
