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
- カントー早期訪問を無視する経路と、訪問後にトーホクへ戻る経路の両方

セーブステートを互換性判定に使わず、ゲーム内セーブを使用します。

## 5. Kanto早期アクセスvertical slice

- 解禁直前の乗船不可
- シオウ3個目バッジ＋アーシアD・Hビル攻略直後・殿堂入り前の乗船可
- 全国図鑑なしでの乗船
- unlock flagの恒久latchと既存殿堂入りsave移行
- 港NPC出現
- 地方間warp
- 推奨Lv.65以上の警告
- map name/music
- NPC会話
- 船上戦の拒否・敗北・辞退後も渡航可能
- 港からPC/帰還船まで強制戦闘・field move不要
- ジム仕掛け、trainer party、boss rewardは必要認定章fixtureで検証
- save/load in Kanto
- heal/whiteout/reset in Kanto
- return travel
- Kanto permit取得後もトーホク側の未解禁HMを使えない
- カントー訪問後のVega本編完走

## 6. 二地方生態・進行

- トーホク49論理地点で、未解禁・抽選外の元Vega encounterが変化しない。
- カントー47論理地点を全physical mapへcrosswalkし、全warp destinationを解決する。
- 541進化系統の両地方導線と全進化道具の入手可能性を検査する。
- 追加イベント34件の捕獲・撃破・逃走・敗北・満杯・再訪を検査する。
- 特殊個体125種は地方共有flagで重複捕獲できない。
- 港の往復を200回行い、save/load/heal/whiteout後も帰還できる。
- 往復200回はVega殿堂入り前と殿堂入り後の両方で行う。
- クチバ到着時の初期回廊と認定章gateにunreachable/circular prerequisiteがない。
- 全reachable Kanto stateから無条件帰還辺があることを逆到達性検査する。
- 早期は要求認定章数0〜4、Vega殿堂入り後は後半認定章・リーグ・共鳴だけが追加解禁される。
- Kanto scriptがVega badge/story/HM flagへ書き込まず、境界ノード以外がVega進行flagを参照しない。

## 7. Release

- clean inputから一発再生成
- 差分パッチをcleanへ適用してfinal hash一致
- ROMや元パッチがrelease archiveへ混入していない
- credits/changelog/readmeを含む
