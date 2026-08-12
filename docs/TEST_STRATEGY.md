# テスト戦略

## 1. Static

毎コミットで実行します。

- private binary guard
- task DAG validation
- manifest header/uniqueness validation
- ID range overlap
- pointer範囲
- ROM allocation overlap
- table count一致
- symbol未解決

## 2. Build

- clean ROM hash
- stage input/output hash
- expected-byte assertion
- toolchain version
- source commit pin
- 32 MiB size
- GBA header checksum

## 3. Engine smoke

最低限の自動/半自動ケース:

1. title
2. new game
3. starter/初回party生成
4. wild battle
5. trainer battle
6. capture
7. level up
8. evolution
9. save
10. restart/load
11. party summary
12. Pokedex registration

## 4. Vega regression

主要checkpoint saveを個人環境で作り、次を確認します。

- 序盤イベント
- ジム戦
- マップ接続
- 固定戦闘
- 殿堂入り
- 殿堂入り後シナリオ
- 図鑑関連

セーブステートを互換性判定に使わず、ゲーム内セーブを使用します。

## 5. Kanto vertical slice

- unlock flag
- 港NPC出現
- 地方間warp
- map name/music
- NPC会話
- gym puzzle
- trainer party
- boss reward
- save/load in Kanto
- heal/whiteout/reset in Kanto
- return travel

## 6. 二地方生態・進行

- トーホク49論理地点で、未解禁・抽選外の元Vega encounterが変化しない。
- カントー47論理地点を全physical mapへcrosswalkし、全warp destinationを解決する。
- 541進化系統の両地方導線と全進化道具の入手可能性を検査する。
- 追加イベント34件の捕獲・撃破・逃走・敗北・満杯・再訪を検査する。
- 特殊個体125種は地方共有flagで重複捕獲できない。
- 港の往復を200回行い、save/load/heal/whiteout後も帰還できる。
- クチバ到着時の初期回廊と認定章gateにunreachable/circular prerequisiteがない。

## 7. Release

- clean inputから一発再生成
- 差分パッチをcleanへ適用してfinal hash一致
- ROMや元パッチがrelease archiveへ混入していない
- credits/changelog/readmeを含む
