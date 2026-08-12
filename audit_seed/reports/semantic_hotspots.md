# Vega × DPE-JP/CFRU-JP セマンティック競合ホットスポット

これはパッチの直接重複269 ranges / 775 bytesを、公開ソース側の挿入定義と照合した設計メモです。
UPSのXOR値だけではFactory側の最終byte値は分からないため、`verify_with_clean_rom.py`で厳密判定する前の分類です。

## 1. 技システムが最優先

直接重複のうち、Vegaの技名／技データポインタを含むものは **169 ranges / 533 bytes（68.774%）** です。

Vega側から推定できる主要テーブル：

- `0x08E0BBB0`: 0x1000 bytes。512 entries × 8 bytesと整合する技名表。
- `0x08E0CBB0`: 0x1800 bytes。512 entries × 12 bytesと整合する戦闘技データ表。
- `0x08E0E3B0`: 上記戦闘技データ表直後の別テーブル。技説明表の可能性が高い。

公開CFRU-JPは次を全面repointします。

- `gBattleMoves` site: `0x080001CC`
- `gMoveNames` site: `0x0804E7B4`
- `gBattleScriptsForMoveEffects` site: `0x08015B78`
- `gMoveDescriptions` sites: `0x080E63F0`, `0x081383A4`
- `gMoveAnimations` site: `0x08071D74`

これらは実際にVega IPSとFactory UPSの二重変更箇所です。したがってCFRUの技表を採用するだけではVega固有技が壊れ、Vega表を優先するだけではCFRUの新技・効果・アニメーションが使えません。

### 必要な移植

1. Vegaの全Move ID、技名、12-byte技データ、説明、効果script、animationを抽出する。
2. CFRU側のMove ID空間との対応表を作る。
3. 同一技はCFRU実装へmapし、Vega固有技はCFRU表へ追加する。
4. Vegaのトレーナー、レベル技、技マシン、イベントscript内のMove IDを新mapへ変換する。
5. 全参照先を統合後テーブルへrepointする。

Species追加より先に、この技ID統合を終える必要があります。

## 2. タマゴ技

`0x08045214` はDPE-JPの公開`gEggMoves` repoint siteで、Vegaも `0x088B6630` へ変更しています。

- 直接重複: `0x08045214–0x08045216`
- 近接重複: `0x0804528C–0x0804528E`

Vegaのタマゴ技を抽出し、Species ID mapとMove ID mapの両方を適用してDPE形式へ再生成する必要があります。

## 3. 元の戦闘技データ領域

最大クラスターは `0x083C490C–0x083C49F5`、86 subranges / 145 overlap bytesです。

これはFireRed側の旧技データ領域と強く整合します。CFRUは旧表参照を拡張表へrepointし、Vegaも技内容を直接編集しているため、旧領域をどちらか一方で残す方式ではなく、統合表を一度だけ生成する必要があります。

## 4. 技説明・戦闘文字列

- `0x080E63EC–0x080E63F2`: Vegaの技データ／直後テーブルへのポインタとCFRUの技説明repointが衝突。
- `0x081383A4–0x081383A6`: CFRUの第2技説明repoint siteと衝突。
- `0x0842B714–0x0842B717`: CFRU-JPの`Crunch Description String`修正位置とVegaの4 bytesが異なる。
- `0x083C4200–0x083C4202`: CFRUの能力関連戦闘文字列repoint位置。Vegaは独自target `0x08696890` を参照。

日本語文字コード、1行幅、技名長、説明長をCFRU設定とVega資産の両方に合わせる必要があります。

## 5. 共有可能性があるbyte

`0x081C1085` はVegaが`CC`を書き、CFRU-JPの公開`bytereplacement`も`0x081C1084`へ`00 CC`を書く「Extend Direct Sound Tracks」です。

この1 byteは同じ最終値になる可能性が高いですが、UPSはXOR形式なのでクリーンROMを使った厳密判定が必要です。`verify_with_clean_rom.py`では`SAME_TARGET`として判別できます。

## 6. コード／データ格納領域の衝突

- `0x086C7D40–0x086C7DC3`: 3 ranges / 52 overlap bytes
- `0x08777770–0x08777781`: 1 range / 18 overlap bytes

どちらもVegaが既に使っている16 MiB内の領域へFactory側データが置かれています。内容選択ではなく、CFRU/DPEのソースビルド時に32 MiB拡張領域へ再配置する`RELOCATE`対象です。

## 7. 直接重複が少なくても安全ではない理由

Factory UPSの変更量14,680,526 bytesのうち14,667,339 bytesは16–32 MiB拡張領域です。一方、元16 MiB内の変更は13,187 bytesです。

表面上の直接重複は775 bytesだけですが、その13,187 bytesには、拡張領域へ処理を飛ばすhook、repoint、save/RAM拡張、script special、ID上限変更が集中します。1箇所でもVega側の前提を上書きすると、離れた拡張データ全体が正常でも起動・戦闘・セーブが壊れます。

## 実装順序

1. クリーンROMで`verify_with_clean_rom.py`を実行し、775 bytesを`SAME_TARGET`と`DIFFERENT_TARGET`へ分離。
2. `audit_source_addresses.py`でCFRU-JP/DPE-JPの全hook/repoint/byte replacementとVega IPSを照合。
3. Move ID・技表を統合。
4. Species ID mapを作成し、Vega既存IDを固定したまま不足種だけ追加。
5. 種族値、画像、アイコン、鳴き声、図鑑、進化、レベル技、タマゴ技を同じmapから再生成。
6. RAM/save-block/script special競合を解決。
7. 起動、戦闘、進化、捕獲、セーブ／ロードを通してから、野生・トレーナー配置を編集。
8. 最後にVega本編と殿堂入り後を回帰テスト。
