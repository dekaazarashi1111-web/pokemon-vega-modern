# ROM/RAM/Save配置方針

## ROM

最終ROMは32 MiBを前提にします。ただし、拡張領域を単なる連続空き領域として扱いません。

- 各moduleにowner tagを付ける。
- linker symbolまたはallocation manifestから配置する。
- hard-coded offsetは監査対象とする。
- 既存Vega領域へ書く場合はexpected bytesを検証する。
- Factory UPSの格納場所は参考にするが、同じoffsetを再利用する義務はない。

T03以降の正本partitionは `config/rom_regions.csv`、配置APIは `tools/rom_allocator.py` とする。intervalはROM file offsetのhalf-open表記で、現行32 MiB layoutは次の通り。

- `[0x00000000, 0x01000000)`: Vega-owned、予約
- `[0x01000000, 0x01200000)`: CFRU payload、予約
- `[0x01200000, 0x01600000)`: integration module、配置可能
- `[0x01600000, 0x01F50000)`: DPE payload、予約
- `[0x01F50000, 0x02000000)`: future tail、配置可能

T03 no-op adapterはfile offset `0x01200000` / GBA `0x09200000` から34 bytesを使用する。Vega-owned領域へのhook/repointは0件で、挿入前の全byteが `0xFF` であることをassertする。

## RAM

CFRU、DPE、VegaのRAM使用範囲を`reports/ram_map.csv`へ統合します。

- byte単位ではなく構造体/用途単位でownerを管理
- temporary RAMとsave-backed RAMを区別
- script vars/flagsとの重複を検査
- battle中だけ使う領域でもoverworld callbackとの同時使用を考慮

## Save

Vegaの既存セーブ互換を維持できれば望ましいが、最優先ではありません。T08で次の順に判断します。

1. Vega既存`.sav`を移行なしで読み込める。
2. 一度だけのmigration routineで変換できる。
3. 新規セーブ専用にし、旧セーブ非互換を明示する。

ただし、セーブ破損を黙って許容しない。version markerとchecksum検証を入れます。
