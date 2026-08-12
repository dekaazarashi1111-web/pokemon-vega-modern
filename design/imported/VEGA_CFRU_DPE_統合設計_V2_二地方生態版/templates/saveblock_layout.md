# SaveBlock拡張レイアウト雛形

> 数値オフセットはベガ実ROMのSaveBlock監査後に確定する。この文書は領域、サイズ式、所有者、CRC範囲を先に固定するための雛形。

## 必要最低サイズ

| 領域 | 計算 | 最低バイト |
|---|---:|---:|
| 全国図鑑 seen | ceil(1025/8) | 129 |
| 全国図鑑 caught | ceil(1025/8) | 129 |
| フォーム seen | ceil(509/8) | 64 |
| フォーム obtained | ceil(509/8) | 64 |
| DexNav検索レベル | 1025×1 byte | 1,025 |
| 伝説等イベント状態 | 125×3 byte目安 | 375 |
| 進化・調査カウンタ | sparse 32 slots×8 byte | 256 |
| 拡張PC 25箱 | 25×30×80 byte | 60,000 |

PC以外の上表だけで最低2,042 byte。実際には研究ランク、チケット、レイド、RTC補助、構造ヘッダ、予約域を足し、4 KiB以上の連続拡張領域を確保する。PCはCFRUの25箱実装とセーブセクタ循環を別途監査する。

## 構造案

```c
typedef struct {
    u32 magic;              // 'VCX1'
    u16 version;            // セーブ構造版
    u16 payloadSize;
    u32 payloadCrc32;
    u32 buildId;
    u8  nationalSeen[129];
    u8  nationalCaught[129];
    u8  formSeen[64];
    u8  formObtained[64];
    u8  dexnavSearchLevel[1025];
    ResearchState research;
    EvolutionCounterSlot evolutionCounters[32];
    LegendaryState legendary[125];
    u8  reserved[/* 4 KiB境界まで */];
} VegaCfruExtension;
```

## 監査項目

- ベガ既存SaveBlock1/2、PC、フラグ、変数、図鑑、袋と重複しない。
- CFRU-JP既定アドレスを直接採用せず、全参照をシンボルへ置換。
- セクタ書込み途中の電源断を想定し、世代番号＋CRC＋前世代バックアップを保持。
- 構造版不一致時は初期化せず、移行不可画面を出す。
- 旧ベガセーブ移行は別ツール。ROM内で曖昧変換しない。
