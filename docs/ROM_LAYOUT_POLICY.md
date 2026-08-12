# ROM/RAM/Save配置方針

## ROM

最終ROMは32 MiBを前提にします。ただし、拡張領域を単なる連続空き領域として扱いません。

- 各moduleにowner tagを付ける。
- linker symbolまたはallocation manifestから配置する。
- hard-coded offsetは監査対象とする。
- 既存Vega領域へ書く場合はexpected bytesを検証する。
- Factory UPSの格納場所は参考にするが、同じoffsetを再利用する義務はない。

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
