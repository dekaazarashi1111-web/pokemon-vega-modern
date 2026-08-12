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

## 野生

`manifests/kanto_encounters.csv`を使用します。

主要列:

- `map_key`
- `method`: land/water/rock_smash/old_rod/good_rod/super_rod
- `slot`
- `species_key`
- `level_min`, `level_max`
- `condition`

出現率はGBA側slot modelへgeneratorが変換します。

## トレーナー

`manifests/kanto_trainers.csv`は1匹につき1行です。

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

`manifests/kanto_items.csv`でitem ball、hidden item、NPC reward、gym rewardを統一します。

## Generator要件

- unresolved keyをエラーにする。
- duplicate slotをエラーにする。
- 同一map/conditionで不正なslot数をエラーにする。
- Trainerのparty slot重複をエラーにする。
- 全生成物にsource manifest rowを追跡できるコメントまたはmapを付ける。
