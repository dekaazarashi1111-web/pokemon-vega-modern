# Vega IPS × Factory UPS 競合監査

## 判定

**単純な重ね当てや、重複部分だけ片方を優先する方式では統合できません。**
直接重複は少量ですが、3バイト単位のポインタ／フック候補が多数含まれ、
Vegaのストーリー基盤とDPE/CFRUの拡張テーブルをソース側で接続し直す必要があります。

## 入力検証

- IPS: `18年2月23日完成版ベガ(1).ips` / SHA-256 `94955c5830888c69a7dee3696abda3b88f69184af67f28a9fb77a8e8abd77f5b`
- UPS: `factory_test_20260524(1).ups` / SHA-256 `46ef4b008b7c68a94f919d037a0bba31853b32af3f50895e722e39deea336358`
- UPS source CRC32: `3B2056E9`
- UPS target CRC32: `216AB7FD`
- UPS patch CRC32: `26E078C8` / valid: `True`
- UPS size: 16,777,216 → 33,554,432 bytes

## 数値結果

|項目|結果|
|---|---:|
|Vega IPSの変更量|3,782,136 bytes|
|Factory UPSの変更量|14,680,526 bytes|
|Factoryが元16 MiB内で変更|13,187 bytes|
|Factoryが拡張16–32 MiBへ格納|14,667,339 bytes|
|直接重複|**775 bytes / 269 ranges**|
|Vega変更量に対する重複率|0.020491%|
|Factoryの元ROM領域変更に対する重複率|5.877000%|

## 重複の性質

- 3バイト長: 166 ranges
- 1バイト長: 84 ranges
- GBA ROMポインタは上位バイトが共通のため、IPSが下位3バイトだけ変更する例が多く、
  3バイト競合の多さは単なるデータ衝突ではなく、ポインタ／フック衝突の強い兆候です。
- `0x08045214` は公開DPE-JPの `gEggMoves` repoint siteと一致します。
- move-name / move-data pointerを含む競合は 169 ranges / 533 bytes、全重複の 68.774% です。
- Vegaの `0x08E0BBB0` → `0x08E0CBB0` は0x1000 bytesで、512件×8 bytesの技名表と整合します。
- Vegaの `0x08E0CBB0` → `0x08E0E3B0` は0x1800 bytesで、512件×12 bytesの戦闘技データ表と整合します。
- したがって最初の大仕事はSpecies追加ではなく、Vega固有技をCFRUの拡張Move ID空間へ移植することです。

## ポインタ競合の主要ターゲット

|Vega pointer|推定対象|競合ranges|該当range bytes|
|---|---|---:|---:|
|0x08E0CBB0|Vega move data table; 0x1800 bytes to 0x08E0E3B0 = 512 entries x 12 bytes|137|437|
|0x08E0BBB0|Vega move-name table; 0x1000 bytes to 0x08E0CBB0 = 512 entries x 8 bytes|32|96|
|0x088B6630|Vega egg-move table target; seen at DPE-JP gEggMoves repoint site 0x08045214|2|6|
|0x08E0E3B0|Vega table immediately following the 512-entry move data table|2|10|
|0x08696890|Vega custom script/data target; exact subsystem unresolved|1|3|

## 領域別

|領域|重複ranges|重複bytes|
|---|---:|---:|
|header/pointer-vector|2|6|
|core-engine/hook-area|175|547|
|shared-table/data-area|88|152|
|occupied-storage/free-space-area|4|70|
|UPS-extension-area|0|0|

## 最大の競合クラスター

|file offset|GBA address|span|subranges|overlap bytes|
|---|---|---:|---:|---:|
|0x003C490C–0x003C49F5|0x083C490C–0x083C49F5|234|86|145|
|0x006C7D40–0x006C7DC3|0x086C7D40–0x086C7DC3|132|3|52|
|0x0001A250–0x0001A69E|0x0801A250–0x0801A69E|1,103|6|18|
|0x00777770–0x00777781|0x08777770–0x08777781|18|1|18|
|0x0001DE90–0x0001E122|0x0801DE90–0x0801E122|659|5|15|
|0x00126940–0x00126BC2|0x08126940–0x08126BC2|643|5|15|
|0x0003E3A8–0x0003E4CE|0x0803E3A8–0x0803E4CE|295|4|14|
|0x000E6330–0x000E63F2|0x080E6330–0x080E63F2|195|3|13|
|0x0001E540–0x0001E6A6|0x0801E540–0x0801E6A6|359|4|12|
|0x000CA108–0x000CA262|0x080CA108–0x080CA262|347|4|12|
|0x0001D910–0x0001DA9A|0x0801D910–0x0801DA9A|395|3|9|
|0x0001D144–0x0001D2A2|0x0801D144–0x0801D2A2|351|3|9|
|0x0001E7D8–0x0001E8D6|0x0801E7D8–0x0801E8D6|255|3|9|
|0x00029958–0x00029A56|0x08029958–0x08029A56|255|3|9|
|0x00133CC4–0x00133D9A|0x08133CC4–0x08133D9A|215|3|9|
|0x000CA638–0x000CA692|0x080CA638–0x080CA692|91|3|9|
|0x00045214–0x0004528E|0x08045214–0x0804528E|123|3|7|
|0x00015B78–0x00015B7E|0x08015B78–0x08015B7E|7|1|7|
|0x000254E0–0x000254E6|0x080254E0–0x080254E6|7|1|7|
|0x00026C40–0x00026C46|0x08026C40–0x08026C46|7|1|7|

## 推奨統合方式

1. Vegaをストーリー／マップ／イベントの基準ROMにする。
2. Factory UPSを重ねず、DPE-JP/CFRU-JPの公開ソースから機能を移植する。
3. 32 MiB拡張領域へ新コード・新データを再配置する。
4. `conflicts.csv` の `PORT` はVega側ルーチンへ手動接続し直す。
5. `RELOCATE` はVegaが使用中の格納領域を避けて再配置する。
6. Vegaの既存Species IDを固定し、追加ポケモンは後続IDへ割り当てる。
7. 種族名、種族値、画像、アイコン、鳴き声、技、進化、図鑑の全テーブルを同じID対応表から生成する。
8. 野生・トレーナー・進化条件はエンジン安定後に設定する。

## 制約

この監査はパッチだけで算出した直接バイト競合です。
真の関数依存、RAM/save-block競合、Species ID意味衝突、スクリプトspecial番号競合は、
クリーンROMから両参照ROMを生成して逆アセンブル／実行テストしないと確定できません。
