# マスタープラン

## 完成像

```text
FireRed JPN Rev0 clean
  └─ Vega 2018-02-23
      └─ Vega互換DPE-JP
          └─ Vega互換CFRU-JP
              └─ Early-access / post-HoF Kanto maps
                  └─ Tohoku/Kanto symbolic ecology manifests
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
| T10 | Engine vertical slice | Engine/QA | T04–T09 | 新要素＋トーホク非破壊overlayを通しで動作 |
| T11 | Kanto importer | Map | T00,T02 | FR本土inventory、1マップround-trip、新Map ID |
| T12 | Dual-region content schema | Content | T00 | 二地方の野生/トレーナー/アイテム/イベント仕様 |
| T13 | Early Kanto vertical slice | Map/Content | T10,T11,T12 | 本編中盤の港→クチバ→安全帰還 |
| T14 | Full Kanto import | Map | T11,T13 | 選定マップと接続を一括追加 |
| T15 | Dual-phase Kanto progression | Content/Engine | T13,T14 | 早期解禁・認定章・殿堂入り後進行 |
| T16 | Populate dual-region content | Content | T12,T14,T15 | トーホク49＋カントー47論理地点を生成 |
| T17 | Regression/playtest | QA | T10,T13,T16 | Vega本編＋二地方回帰確認 |
| T18 | Release pipeline | Platform | T17 | 再現ビルド・差分パッチ・記録 |

## 並行可能範囲

T00完了後、以下を同時に開始できます。

- T01: 上流ビルド再現
- T02: 競合監査
- T12: コンテンツschemaと設計

T02完了後にT11（カントーマップ変換）を開始できます。T03以後はEngineレーンを進めながら、MapとContentを継続できます。Kantoの正確な数値IDを書き込むのはT10以後ですが、記号名での設計はT12から可能です。

受領したV2二地方生態版は完成像・進行・生態・イベントのactive review資料です。V1は来歴保存専用です。V2の47カントー地点はraw map総数ではないため、T11ではclean BPRJとpokefireredから約256候補mapの再現可能なinventoryを作り、論理地点とのcrosswalkを確定します。採用済みデータだけをT12/T16のschemaへ昇格します。

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

Vegaのシオウ3個目バッジ取得後・アーシア島D・Hビル攻略後の安全な実flagでカントーを恒久解禁する。殿堂入り前saveからクチバへ移動し、推奨Lv.65警告、NPC、PC/回復、セーブ、全滅復帰、強制戦闘なしの常時帰還が動作する。ジムは必要認定章のtest fixtureで別検証する。

### Gate E — Release candidate

再現ビルド、静的検査、主要手動チェック、配布用差分パッチ生成が完了する。
