# Stage 53 world runtime再調査 引き継ぎ

## 再開する正本タスク

- `tasks/USER_20260824_STAGE51_WORLD_RUNTIME_E2E_REPAIR.md`
- 状態は`IN_PROGRESS`のまま。Stage 53は配布候補・修正済み・ローカルPASSとして扱わない。
- この引き継ぎ作成時点では、ROM、save、iPad配置、runtime実装を変更していない。

## 最重要の訂正

1. Stage 53で「知恵の洞窟」として試験したmapが間違っていた。
   - 正しい原作Vegaの「ちえのどうくつ」: map section `131`、map `1/36`、`1/37`、`1/38`、`1/73`。
   - Stage 53が試験したmap: `1/83`、`1/84`、`1/85`、`1/11`、`1/100`、`3/59`。全てmap section `139`の別map群。
   - よって「知恵の洞窟6 mapをPASS」「老人部屋は氷ポケモンLv.49〜51」というStage 53の判定を破棄する。
2. ヒスイシティ506番道路入口側の博士風NPCは未特定・未修正。
   - 前回の`3/2 local 9 (4,16)`は外見からの推測で、ユーザーが指したNPCだと実証していない。
   - ユーザーがiPadで「治っていない」と確認済み。finite dialogueへの差し替えを合格証跡にしない。
3. Stage 53のiPad用ROMとsaveは置かれているが、上記2点により候補自体が不合格。上書きや再配置をしない。

## 原作Vegaについて確定したこと

- 改変前の通常版Vegaの舞台はトーホク地方で、「ちえのどうくつ」は503番道路の途中にある原作ダンジョン。
- 通常版Vegaの攻略導線にカントー地方への渡航はない。FireRedを基礎にしているためROM内に残存素材はあるが、通常プレイ可能な完全なカントー地方ではない。
- 現プロジェクトのカントー地方は、clean FireRed日本版Rev.0から新しいKANTO namespaceへimportした追加実装。Vega内部に完成済みのカントーを解禁したものではない。
- 原作B1F `1/73`のland encounter rateは`7`。出現は次の範囲。
  - ディグダ Lv.6〜9
  - ダンゴロウ Lv.7〜9
  - ライノス Lv.7〜8
  - バルキー Lv.6〜8
- ライノスが出ること自体は正常だが、Lv.100、毎歩確定、方向転換だけの遭遇は異常。
- 殿堂入り後に開くB2F `1/37`は概ねLv.44〜48で、序盤B1Fとは別table。

## 最短の再開手順

1. `README.md`、`AGENTS.md`、本書、正本タスク、`design/current_state.md`の訂正行だけ読む。古いrun log全体を読み直さない。
2. `reports/generated/vega_map_inventory.csv`でmap section `131`と`139`を再確認し、`inputs/reference/vega_reference_provided.gba`のmap/wildをbehavior oracleにする。
3. fresh mGBAの通常new game／通常Continueから、本物の`1/73`へ通常ワープ・歩行で入り、方向転換、通常歩行、逃走後、出口到達、species、levelを独立2 processで測る。map直書きだけのfixtureを完了根拠にしない。
4. 博士風NPCはユーザーの通常移動経路にある全objectをmap/local ID、座標、sprite、script root、隣接A入力traceで列挙する。候補を外見だけで選ばない。実際の停止scriptを特定してからownerを直す。
5. 506番道路入口double戦と「551番水道」も同じ方法でruntime map/local IDとheaderを取得し、`3/24`／`3/29`を仮定せず確定する。
6. 症状別のmap差し替えを足さず、通常NPC script、通常double controller、wild header/cadence、Codex inactive分岐の共通ownerを根本から修正する。
7. 全fixture合格後も、iPad実プレイ承認まではタスクをDONEにしない。

## 最小のローカル証跡

- `reports/generated/vega_map_inventory.csv`
  - `1/36`、`1/37`、`1/38`、`1/73`はmap section `131`。
  - Stage 53 fixtureの`1/83`、`1/84`、`1/85`、`1/11`、`1/100`、`3/59`はmap section `139`。
- `reports/generated/vega_encounter_inventory.csv`
- `inputs/reference/vega_reference_provided.gba`（2018-02-23版原作Vega参照ROM、読取専用）
- `design/kanto_feasibility.md`
- `docs/KANTO_PORT_POLICY.md`

## 外部資料

- 原作攻略順と殿堂入り後調査: <https://w.atwiki.jp/np369/pages/58.html>
- 原作Vega野生データ（ちえのどうくつ）: <https://w.atwiki.jp/altair1/pages/56.html>
- Wiseman's Caveの場所と階層: <https://pokemon-vega.fandom.com/wiki/Wiseman%27s_Cave>
- トーホク地方の概要: <https://pokemon-vega.fandom.com/wiki/Tohoak>

## 未解決事項

- 博士風NPCの正しいmap/local ID、座標、script root。
- 506番道路入口double戦の正しい物理objectと、Codex inactive時に技選択後停止する正確なcontroller状態。
- ユーザーが「551番水道」と呼ぶ草むらの正しいmap/header。511番水道`3/29`という前回推定は未確定。
- 正しい知恵の洞窟に対するStage 53 ROMの実挙動。
- Lv.100敵partyの原因。Codex報酬workspace汚染という前回説明は、誤map fixtureを根拠にしていたため再証明が必要。
