# Phase 01 Status

## 完了

- IPS/UPSコンテナ検証
- UPS source/target/patch CRC抽出
- UPS 16 MiB → 32 MiB拡張確認
- 両パッチの全変更range復号
- 直接二重変更269 ranges / 775 bytes抽出
- Move pointer patternの集計と主要テーブル推定
- 全競合CSV/JSON/Markdown生成
- クリーンROMを端末内だけで使う厳密判定ツール作成
- 公開DPE-JP/CFRU-JP sourceの固定アドレス監査ツール作成
- Codex向け次タスク定義

## 未完了

- 775 bytesの最終値比較（クリーンROMをローカルで使う必要あり）
- Vega reference / Factory referenceの逆アセンブル比較
- RAM/save-block/script special/ID体系の完全監査
- DPE-JP/CFRU-JP source forkへの実コード移植
- 起動可能な統合ROM／統合パッチ生成

## 現時点のGo/No-Go

- 二つのパッチを単純結合: **NO-GO**
- Vegaを土台にDPE-JP/CFRU-JP sourceを移植: **GO（大規模開発として）**
- 最初の実装対象: **Move ID・技名・技データ・効果script・説明・animationの統合**
