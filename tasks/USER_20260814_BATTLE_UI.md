# USER-20260814-BATTLE-UI — 戦闘UIと有効度表示をCFRU/Factory系へ統一する

- Lane: `engine/ui/qa`
- Depends on: `USER-20260814-FIRST-BATTLE-LOOP`, `USER-20260814-BATTLE-RULES`
- Queue ID: `USER-20260814-BATTLE-UI`

## 目的

Vega固有の旧battle UIを主経路に残さず、固定CFRU-JPまたはFactory参照で既に抽出・移植済みの
戦闘HUD、行動/技選択、特性・道具通知、有効度表示を通常戦にも一貫して使用する。

## 実行

1. 通常戦、trainer、double、Factory、RaidのUI ownerと未接続surfaceを監査する。
2. Factory ROMのbyteを直接移植せず、固定CFRU sourceと既存生成asset/adapterを使用する。
3. 技選択時の「こうかばつぐん／いまひとつ／こうかなし」表示をtype判定と同期する。
4. 特性名、道具名、技名、Species名のcanonical table境界を検査し「？？？？？？？？」を排除する。
5. Vegaのstory text、map、NPC、BGMは変更しない。

## 受入条件

- [ ] 通常戦とFactoryで同じbattle UI ownerと有効度判定を使う。
- [ ] 1×、2×以上、0.5×以下、0×、Stellar/特殊規則の表示が実damage判定と一致する。
- [ ] 特性popup、item通知、技名、対象名に未解決文字列がない。
- [ ] single/double、trainer、wild、Factory、Raidの入力と画面復帰がPASSする。

## 完了

対象検証とログを更新し、queueをDONEへ変更してタスク単位コミットを作る。
