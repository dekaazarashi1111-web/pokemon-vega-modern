# マスタープラン

## 完成像

```text
FireRed JPN Rev0 clean
  └─ Vega 2018-02-23
      └─ Vega互換DPE-JP
          └─ Vega互換CFRU-JP
              └─ Postgame Kanto maps
                  └─ symbolic content manifests
                      └─ final 32 MiB ROM
                          └─ 配布用差分パッチ
```

## フェーズ

| ID | タスク | 主レーン | 依存 | ゴール |
|---|---|---|---|---|
| T00 | Bootstrap | Platform | — | 入力検証・source pin・参照ROM |
| T01 | Upstream reproducibility | Engine | T00 | DPE/CFRUビルド環境を再現 |
| T02 | Exact address audit | QA | T00 | ROM/RAM/save/ID競合を機械化 |
| T03 | Rebuildable Vega harness | Engine | T01,T02 | clean→Vega→moduleの再現ビルド |
| T04 | Move ID port | Engine | T03 | Vega技ID固定でCFRU技系統合 |
| T05 | Type/Ability/Item IDs | Engine | T03,T02 | 拡張ID空間と生成header |
| T06 | CFRU battle core | Engine | T04,T05 | 戦闘コアをVega上で起動 |
| T07 | DPE Species port | Engine | T04,T05,T03 | Vega species固定＋追加species |
| T08 | Save/RAM compatibility | QA/Engine | T02,T03 | save/RAM衝突解消 |
| T09 | Graphics/Dex/Evolution | Engine | T07,T08 | 表示・図鑑・進化・習得技 |
| T10 | Engine vertical slice | Engine/QA | T04–T09 | 新要素を1セット通しで動作 |
| T11 | Kanto importer | Map | T00,T02 | 1マップround-tripと新Map ID |
| T12 | Content schema | Content | T00 | 野生/トレーナー/アイテム仕様 |
| T13 | Vermilion vertical slice | Map/Content | T10,T11,T12 | 港→町→ジム→帰還 |
| T14 | Full Kanto import | Map | T11,T13 | 選定マップと接続を一括追加 |
| T15 | Postgame progression | Content/Engine | T13,T14 | 解禁・ジム進行・地方間移動 |
| T16 | Populate content | Content | T12,T14,T15 | 野生・手持ち・報酬を生成 |
| T17 | Regression/playtest | QA | T10,T13,T16 | Vega本編＋Kanto回帰確認 |
| T18 | Release pipeline | Platform | T17 | 再現ビルド・差分パッチ・記録 |

## 並行可能範囲

T00完了後、以下を同時に開始できます。

- T01: 上流ビルド再現
- T02: 競合監査
- T12: コンテンツschemaと設計

T02完了後にT11（カントーマップ変換）を開始できます。T03以後はEngineレーンを進めながら、MapとContentを継続できます。Kantoの正確な数値IDを書き込むのはT10以後ですが、記号名での設計はT12から可能です。

受領した `design/imported/VEGA_CFRU_DPE_統合設計/` は現代化コンテンツのreview資料であり、このカントー工程を置き換えません。採用済みデータだけをT12/T16のschemaへ昇格します。

## 重要ゲート

### Gate A — 再現可能な参照ビルド

- clean ROM hash一致
- Vega reference生成
- Factory reference生成
- pinned source記録

### Gate B — No-op module boot

Vegaへ拡張領域を追加してもタイトル、ニューゲーム、セーブが壊れない。

### Gate C — Battle vertical slice

Vega既存技と追加技、新特性、新Species、追加道具が1つずつ動作する。

### Gate D — Kanto vertical slice

Vegaからクチバへ移動し、NPC、ジム、報酬、セーブ、帰還が動作する。

### Gate E — Release candidate

再現ビルド、静的検査、主要手動チェック、配布用差分パッチ生成が完了する。
