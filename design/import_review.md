# import_review.md

## 結論

受領した3パッケージは、次の役割に分けて使う。

1. `vega_modern_codex_playbook`: 再現ビルド基盤、T00〜T18のDAG、検証雛形として採用する。
2. `vega_cfru_integration_audit`: パッチ競合の一次証跡と監査ツールの正本として採用する。
3. `VEGA_CFRU_DPE_統合設計`: 完成像とコンテンツ案の有力な下書きだが、データはreview状態から開始する。

完成目標は、FireRed日本版Rev.0からVegaを再生成し、公開ソースのDPE-JP/CFRU-JPをVega互換で移植し、殿堂入り後カントーと記号manifestによる追加コンテンツを載せた32 MiB ROMを再現ビルドし、ROMを含まない差分パッチを作ることである。

## プレイブック評価

- task graph、manifest validator、付属unit testはPASSした。
- 実装領域の多くは `.gitkeep` と空のCSVであり、完成コードではない。
- T00後の最初の並列波はT01（上流再現）、T02（完全監査）、T12（symbolic content schema）。T11はT02完了後である。
- Factory UPSは参照専用。Vegaへの直接適用は禁止する。
- Vega Move ID 0〜511と既存Species IDを固定し、追加IDはmanifestから生成する。
- quickstart、bootstrap、taskctl、private guardは現行運用へ統合する前に安全性と二重状態管理を補強する。

## 競合監査評価

単体監査パッケージの `MANIFEST.sha256` は15/15 PASSした。プレイブック同梱 `audit_seed` は2 CSVだけ改行/BOMが正規化され、同梱MANIFESTとbyte hashが合わないため、単体ZIP版を `audit_seed/` の正本にした。

主要事実:

- Vega IPS変更量: 3,782,136 byte。
- Factory UPS変更量: 14,680,526 byte。
- Factoryの元16 MiB内変更: 13,187 byte。
- 直接重複: 269 ranges / 775 byte。
- 技名・技データpointer関連: 169 ranges / 533 byte（68.774%）。
- clean ROMによる厳密比較: `SAME_TARGET=191`、`DIFFERENT_TARGET=584`。
- 最初のエンジン移植対象はSpeciesではなくMove ID・技表・effect・description・animationである。

191 byteが同値でも周辺pointerやRAM/SaveBlockが互換とは限らない。269件の `PORT` / `RELOCATE` は自動提案であり、人手レビュー済み判断ではない。

## 統合設計パッケージ評価

パッケージmanifestの35対象ファイルはsize・SHA-256が全件一致した。全国図鑑1025種、進化541系統、進化条件553行、フォーム509行、特殊イベント125種、主要道具255行、Vega既存386枠、基礎Species ID台帳1206行を含む。

採用価値が高い方針:

- Vega本編の必須進行と既存386枠を保持する。
- 全国番号と内部Species IDを分離する。
- 公式1025種とVega固有181種を共存させる。
- 通信・RTC・マルチプレイを必須条件にしない。
- 野生11枠を大量置換せず、DexNav、時間帯、大量発生、保護区などのoverlayへ分散する。
- SaveBlock、フック、ID、32 MiB配置を推測で埋めず、実ROM監査後に確定する。

正本昇格前に解消する問題:

1. 進化553行に、ID以外が同一の余剰23行（21群）がある。
2. 同じ全国番号のfrom/toで条件が異なる組があり、リージョンフォームを識別する列が不足している。
3. Vega保護台帳の公式205件の全国番号が `276.0` 形式で、他CSVの整数文字列と直接joinできない。
4. `じばのコア` 等、進化条件が参照する救済道具の一部が道具入手マスターにない。
5. フォーム509行は分類方針であり、個別Form ID・場所・解禁条件の実装正本ではない。
6. trainer、move、ability、hook、SaveBlockは方針またはTEMPLATEのみである。
7. カントー／ナナシマ方針は含まれない。カントーは `MASTER_PLAN.md` とD-003/D-004を正とする。
8. Z、ダイマックス、テラが「任意」と「標準版収録」の両方で記述され、v1.0必須範囲のADRが必要である。

## 資料の優先順位

矛盾時は次の順で判断する。

1. `AGENTS.md` の運用・安全規則。
2. `design/decisions.md` の採択済みADR。
3. `design/tasks_next.md`、`tasks/task_graph.json`、選択タスクの `tasks/T*.md`。
4. `MASTER_PLAN.md` と `docs/` の現行技術方針。
5. `audit_seed/` と生成監査の測定証拠。
6. `design/imported/VEGA_CFRU_DPE_統合設計/` のreview資料。

測定証拠が上位仕様と矛盾する場合は、仕様を黙って優先せずADRを追加して解決する。
