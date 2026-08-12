# Codexの使い分け

## ローカル推奨タスク

ROMを読む必要があるもの:

- T00 baseline reference
- T02 exact byte audit
- T03以降のROM build
- emulator smoke test
- release patch作成

## Cloudでも進めやすいタスク

- upstream source監査
- generator実装
- manifest schema
- map/content設計
- unit test
- documentation

## 実用的な分担

- ローカルCodex: Engine + integration
- Cloud Codex task 1: Map importer
- Cloud Codex task 2: Content schema/population
- Cloud Codex task 3: QA/static validators

Cloud側ではROMを前提にしないunit test fixtureを作り、ローカル側で実ROM integration testを実行します。
