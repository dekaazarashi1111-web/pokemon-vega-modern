# Sources and evidence policy

## 一次証拠（この納品で authoritative）

- 添付snapshot commit: `e0351f3deacc52816636e343ba748cb35d54e6bd`、release `v1.3.7`。
- final ROM pin metadata: SHA-256 `cb8ac173bf8f9e0e4bc51ecd12adc581c6344761955f38766ce7211e2dd5f167`。ROM本体は未添付。
- `inputs/manifests/species_ids.csv`: canonical ID 0..1620、公式/Vega/form分類。
- `inputs/analysis/**`: 暫定coverage、candidate、starter、special、Vega 206 review。
- `inputs/evidence/generated_maps/kanto/**`: Kanto 254 map JSON。hostのlocal ID、座標、object数、script stubの物理根拠。
- exact wild header root `0x092CAF0C`、265 headers。exact evolution table root `0x09F79290`。

## 公開資料（二次資料、意味・世界観の照合だけ）

- note「ポケモンベガのポケモン一覧」: 本編386、戦闘用コピー6、別枠5という整理。
  - https://note.com/jazzy_emu1935/n/nb4f36810c209
- ポケットモンスターアルタイル攻略Wiki攻略チャート: 殿堂入り後の全国図鑑進行、化石復元等のプレイヤー導線。
  - https://w.atwiki.jp/altair1/pages/39.html
- Yahoo!知恵袋の旧Vega攻略回答: ネメア→ライラプス／ガニメデ、牙・翼・闇の化石の旧導線。
  - https://detail.chiebukuro.yahoo.co.jp/qa/question_detail/q11149901906
  - https://detail.chiebukuro.yahoo.co.jp/qa/question_detail/q1469921114
- アルタイル攻略Wikiのオルマリア項目: 旧作品での進化関係の補助照合。
  - https://w.atwiki.jp/altair1/pages/391.html

公開資料は現行ROMの物理実装証拠に使いません。現行eventを `EXISTING_ROM_VERIFIED` へ昇格できるのはexact-ROMのmap/script/Species ID/state試験だけです。
