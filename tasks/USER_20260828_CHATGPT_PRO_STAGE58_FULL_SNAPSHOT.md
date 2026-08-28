# USER-20260828-CHATGPT-PRO-STAGE58-FULL-SNAPSHOT — Stage58完全版ZIPを作成する

## 目的

前回のStage35完全版ZIPと同じ自己完結運用をStage58へ更新し、ROM、私有入力、固定toolchain、
mGBA、全source、Git履歴、再生成・検証基盤を1個のZIPでChatGPT Proへ渡せるようにする。

## 完了条件

- Stage58 candidate、focused入力Stage57、標準QA saveのsize／SHA-256を固定する。
- clean/Vega/Factory ROM、IPS/UPS、固定上流、全Git履歴、host/ARM toolchain、mGBAを保持する。
- 旧Stage ROM、battle-core/upstream cache、一時mGBA作業域、過去完全版ZIPを除外する。
- ZIPは単一root、unsafe path 0、duplicate 0、CRC不一致0とする。
- fresh展開した`VERIFY_SNAPSHOT.py`でmanifest、Git、candidate、doctor、Stage58 focused checkをPASSする。
- `design/run_log.md`と`design/version_log.md`を追記してcommitする。

## 非目標

- Stage58 ROM、save、ゲーム仕様を変更しない。
- ChatGPT Webへ自動アップロードしない。
- iPad上のROM／saveを変更しない。
