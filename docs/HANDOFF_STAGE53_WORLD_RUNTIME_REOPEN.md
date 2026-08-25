# Stage 53 world runtime再調査 引き継ぎ

## 再開する正本タスク

- `tasks/USER_20260824_STAGE51_WORLD_RUNTIME_E2E_REPAIR.md`
- 状態は`IN_PROGRESS`のまま。Stage 53は配布候補・修正済み・ローカルPASSとして扱わない。
- 現行候補はStage 55。ROMと正常進行saveをWi-Fi SSHでiPadへ配置済みだが、実プレイ承認前の非release候補として扱う。

## 最重要の訂正

1. Stage 53で「知恵の洞窟」として試験したmapが間違っていた。
   - 正しい原作Vegaの「ちえのどうくつ」: map section `131`、map `1/36`、`1/37`、`1/38`、`1/73`。
   - Stage 53が試験したmap: `1/83`、`1/84`、`1/85`、`1/11`、`1/100`、`3/59`。全てmap section `139`の別map群。
   - よって「知恵の洞窟6 mapをPASS」「老人部屋は氷ポケモンLv.49〜51」というStage 53の判定を破棄する。
2. ユーザー報告の博士NPCは`96/5 local 5 (25,7)`で確定した。プレイヤーは`(25,8)`から上向きにA入力する。
   - script rootは`0x093C330C`、既存のReward Encounters V2 Scientistで、`callnative`の同期終了後にも無条件で`waitstate`していたことが停止原因。
   - 前回の`3/2 local 9 (4,16)`は別NPCであり、博士・Scientistとして扱わない。専用表記と506番道路調査会話を削除し、通常の汎用finite dialogue ownerへ戻す。
3. Stage 53のiPad用ROMとsaveは置かれているが、上記2点により候補自体が不合格。上書きや再配置をしない。

## 2026-08-25 再開結果

- 修正版は旧Stage 53と分離したStage 54として生成した。ROM SHA-256は`b130c03b0a10b80e1d10ef962d8fa6fb2f70c6529155119a3673a9a338e34c03`。
- 博士NPCは`96/5 local 5 (25,7)`、player `(25,8)`上向きA入力で固定した。同期終了は即releaseし、進行済みの非同期メニューはBキャンセル後にreleaseする2 fixtureを独立2 processでPASSした。
- 旧`3/2 local 9 (4,16)`は`VEGA_RECOVERED_FINITE_DIALOGUE`として扱い、博士・Scientist・506番道路調査という専用表記を削除した。
- 知恵の洞窟は北口・南口から`3/21 → 1/36/38 → 1/73 → 3/21`、B2Fは`1/73 ↔ 1/37`を通常キー入力で往復した。B1FはSpecies `16` Lv.9、B2FはSpecies `387` Lv.45を通常歩行で取得し、方向転換32回遭遇0、逃走後通常移動もPASSした。
- 全20 fixture×独立2 processは完全一致、warnings 0。Stage 54 ROMと正常進行saveは2026-08-25にiPadへ別basenameで配置済み。実プレイ未確認の非release候補で、taskは`IN_PROGRESS`のまま。

## 2026-08-25 Stage 55 可視応答の根本修正

- Stage 54の実機ではfreezeは解消したが、博士NPCと近くを歩くNPCが無表示で終了した。これは正常仕様ではない。
- event-design復元TALK_OBJECT 15件のsource fallback pointerは台帳に存在したが、runtime dispatcherへはdaycare 1件だけしか設定されていなかった。rank条件に一致しない残り14件は共通の`release/end`へ落ち、別mapの同系NPCでも無表示になり得た。
- source builderを全TALK_OBJECT必須fallbackへ修正し、Stage 55 retrofitでも15 dispatcherをcloneして各mapをrepointした。全678 map／3,093 objectの静的監査は接触可能な無効root 0、可視応答契約違反0、可視source fallback 15をPASSした。
- 博士`96/5 local 5 (25,7)`は`BUSY=9`だけ`waitstate`し、同期result 13種を6種類の可視メッセージへ接続した。player `(25,8)`上向きAから同期結果とメニュー結果の両方を回帰した。
- 歩行中の近隣NPCは`96/5 local 4`のevent-design port coordinatorだった。GBA方向キーだけで接近してA入力し、可視メッセージとfield復帰を確認した。通常walkerも別fixtureで確認した。
- 全22 fixture×独立2 processは完全一致、warnings 0。Stage 55 ROM SHA-256は`b0a825cb7d3886419e4122f2de54a069fdf8e7a5fe41a9fef0bc3235e68cbcf8`。
- `55_world_runtime_visible_feedback_repair.gba`と同名`55_world_runtime_visible_feedback_repair.srm`をWi-Fi SSHでiPadへ配置し、read-back byte一致、一時ファイル0、旧Stage 54不変を確認した。RetroArchは停止したまま。taskは実プレイ承認待ちの`IN_PROGRESS`。

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
4. 博士NPCは`96/5 local 5 (25,7)`へ固定し、`(25,8)`上向きA入力から、同期終了（未解放等）と非同期メニュー終了の双方で可視応答を出し、有限時間でfieldへ戻ることを測る。旧`3/2 local 9`を博士fixtureへ戻さない。
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

- 博士NPCの正しい物理位置は解決済み。`96/5 local 5 (25,7)`、player `(25,8)`上向き、script root `0x093C330C`。
- 博士NPCと近隣port coordinatorのStage 55修正版をiPad実プレイで再確認すること。ローカルでは可視応答とfield復帰を独立2 processで確認済み。
- 506番道路入口double戦の正しい物理objectと、Codex inactive時に技選択後停止する正確なcontroller状態。
- ユーザーが「551番水道」と呼ぶ草むらの正しいmap/header。511番水道`3/29`という前回推定は未確定。
- 正しい知恵の洞窟に対するStage 55のiPad実挙動。ローカル通常warp／歩行／wild／退出は確認済み。
- Lv.100敵partyの原因。Codex報酬workspace汚染という前回説明は、誤map fixtureを根拠にしていたため再証明が必要。
