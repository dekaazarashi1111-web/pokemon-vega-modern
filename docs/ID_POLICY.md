# ID互換性ポリシー

## Canonical

Vega既存IDをcanonicalとします。

- Move: Vega 0–511を固定する方針
- Species: Vegaの既存範囲を抽出して固定
- 既存の本家ポケモンがDPEにもある場合、重複追加せずDPE symbolをVega IDへmapping
- Vega固有ポケモンはDPE形式へ変換するがIDは維持
- Vegaにない要素だけをappend

## 記号名

コンテンツでは数値IDを使いません。

```text
SPECIES_KEY_FLETCHLING
MOVE_KEY_ROOST
ITEM_KEY_MEGA_STONE_X
MAP_KEY_KANTO_ROUTE_01
TRAINER_KEY_KANTO_SURGE
```

Generatorがmanifestから数値defineを作ります。

T04でMove範囲は確定済みです。Vega 0〜511を固定し、NFKC完全一致するCFRU identityを対応付け、未収録551技を512〜1062へappendします。Vega ID 470/509はCFRU公式同名別技との衝突を避けるため、それぞれ `MOVE_KEY_SOUL_BITE`（ソウルバイト）、`MOVE_KEY_DARK_SNIPE`（ダークスナイプ）へ表示名とsymbolを変更します。CFRU公式 `MOVE_JAWLOCK` / `MOVE_SNIPESHOT` は別append IDとして保持します。

## 予約

`manifests/id_ranges.csv`でownerと範囲を管理します。未確定範囲は空欄のまま`PROPOSED`とし、監査後に確定します。

## 禁止

- 既存空き番号に見えるIDを目視だけで再利用
- 同じID表を複数ファイルへ手書き
- コンテンツCSVに裸の数値Species/Move/Item IDを書く
- ID移動を伴う自動sort
