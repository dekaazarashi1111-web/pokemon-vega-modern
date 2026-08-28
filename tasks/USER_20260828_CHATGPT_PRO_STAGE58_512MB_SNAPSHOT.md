# USER-20260828-CHATGPT-PRO-STAGE58-512MB-SNAPSHOT — 512MB以下のStage58完全版ZIPを作成する

## 目的

ChatGPTの単一ファイル上限に合わせ、Stage58の開発・再生成・検証能力を保持したまま
完全版ZIPを512,000,000 bytes以下へ縮小する。

## 完了条件

- ROM原本、Stage57／58、full監査用Stage50 oracle、標準QA save、全source、Git全履歴、固定上流、toolchain、mGBAを保持する。
- Stage58のcheckとclean再生成に必要なBPSだけを保持する。
- 現行source／Gitへ統合済みの過去BPSとtrainer checkpoint ZIPだけを除外する。
- ZIP sizeを512,000,000 bytes以下にし、単一root、unsafe path 0、duplicate 0、CRC不一致0とする。
- fresh展開した`VERIFY_SNAPSHOT.py`をPASSする。
- fresh展開した`BUILD_CURRENT_FROM_SOURCE.py`でStage58最終gateをPASSする。
- `design/run_log.md`と`design/version_log.md`を追記してcommitする。

## 非目標

- ROM、save、ゲーム仕様を変更しない。
- ChatGPTへ自動アップロードしない。
- 元の801MB完全版ZIPを削除しない。
