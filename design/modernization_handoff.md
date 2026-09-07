# Modernization 引継ぎ入口

## 工程境界

対象は USER-MODERNIZATION-P01（ID・対象区分・共通処理の先行監査と根本修正）のみ。工程2の進化仕様整理、工程3の原作習得全反映は開始しない。タスク状態の正本は `design/tasks_next.md` のままとし、既存の Stage60 監査 IN_PROGRESS と別PRの状態を変更しない。

## 開始時の正本と保全

2026-09-08（JST）、GitHub main `f2d3ed3546f07b4d4aa34ff61de9b9135b19bac2` を読取基準に、専用branch `chatgpt/user-modernization-p01-20260908` を作成した。指定WSL workspaceはこの実行環境には存在せず、git cloneはDNS解決に失敗した。GitHub connectorでbranch・commit・PR・Actionsを実確認して作業する。既存のユーザー作業コピーは変更していない。

現行プレイ基準は `config/active_play_baseline.json` のStage62。size 33554432、SHA-256 `d97a0d4a6cd6f8f77a1503a5ac6d473b0e94c4892e3d5a94098497ce35cb6e6f`、CRC32 `73E4FB73`。本工程はこの基準、実機ROM/save、収集済みbit、ROM/RAM/save配置を変更しない。新しいROMを生成・検証したという主張はしない。

## 入力の受領確認

- 技習得品質改善版 v1.3.0（2026-09-05）: 82683251 bytes、SHA-256 `80b678320c08203e7b39236e5c123f5c2f2f0c729e7f4e5101bed88c84158adb`。今回の複製番号(4)でもユーザー指定(3)の受領hashと一致した。
- ID固定・原作復元監査資料（2026-09-05）: 67698 bytes、SHA-256 `448608de12a431bef8eaaaf2dc3024743bfd77ad7925e5fb6ae01b6086cfac08`。今回の複製番号(3)を実測した。指定(2)の比較元hashは未提示なので、同一byteだったとは断定しない。復元・進化の候補資料であり、全提案の採用承認ではない。

両原本は会話添付から読み取り専用で扱い、Gitへ入れない。再開時は一時pathを仮定せず、保有原本を上記size/hashで再確認する。永続的な非公開再取得先は未確認。repositoryは開始時のAPI確認でpublicであり、`private-environment-v1` というRelease名だけを非公開の根拠にしない。私有入力の安全な取得経路を確認するまではROM検証をPASSと記録しない。

## 修正の原則と再開点

現行manifestで `SPECIES_KEY_CATERPIE=649`、`SPECIES_KEY_EGG=412` を再確認した。旧取得・収集台帳の数値IDと現行IDを直接結合せず、species_keyから解決して意味を照合する。キャタピーを通常基本種の習得対象へ戻し、内部タマゴの除外は維持する。他の除外フォームは一括有効化しない。過去Stage/Wiki/入力スナップショットは上書きせず、訂正表と現行用の生成経路を分離する。

取得表のGitHub API本文が空になることを実確認した。次は正本の `/vega-read`・`/vega-find` で対象HEADの範囲を取得し、consumer・validator・focused testを接続する。監査・検証は未完了であり、この入口作成をP01完了とは扱わない。


<!-- USER-MODERNIZATION-P01-20260908-SOURCE-CHECKPOINT -->
## 2026-09-08 USER-MODERNIZATION-P01 検証済みsource checkpoint

- 結果: BLOCKED。P01受入未完了。P02/P03未開始。ROM/save/プレイ基準は未変更。
- 検証source HEAD: `62b0c76e4b402de8d3253566a3f606f99b0cfd21`
- Actions: https://github.com/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/34147922725
- 既存focused testsと既存カタログのbuild/check・guard・task整合性が成功。新投影の全consumer接続とROM検証の成功を意味しない。
- 限定結果: `{"errors": 0, "failures": 0, "identity_contract_sha256": "00fa015276eef8506c57caa660ec3093ce137bd0506cb7db5af062cea6b1b265", "identity_contract_size": 9549, "skipped": 0, "tests": 27}`
- 採用入力・変更理由・親候補・残件・再開点: design/modernization_p01_checkpoint.md、config/modernization_inputs.json、config/modernization_candidate.json。
