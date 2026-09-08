# USER-MODERNIZATION-P01 — ID・対象区分・共通処理の先行監査と根本修正

状態はdesign/tasks_next.mdのみ。P02進化条件仕様、P03全原作習得は開始しない。

## 受入gate

1. 全SpeciesおよびMove/Ability/Item/Type/Formのkey/IDと対象集合の意味を照合し、同数入替・重複・欠落・範囲外・内部枠・別姿混同を拒否する。
2. キャタピー649の通常基本種採用と内部タマゴ412除外が現行JSON/CSV/Wiki索引・生成C表・実ROM consumerまで一致する。元Wiki/vendor snapshotは不変。
3. collection_key→1216bitの対応、240-byte save ABI、有効save blockの全byte、ROM/RAM/save配置、プレイ基準を保全する。
4. clean起点累積親のbyte一致、2回再生成、10-byte限定差分、順逆/clean BPS往復、別候補実mGBAを確認する。
5. 参照と容量を測定し、資料不整合/意図仕様/未確認を区別してP02/P03の入口を残す。
6. 日本語run/versionログ、最終HEADのCI、通常PR mergeとremote結果を確認する。受入未達はDONEにしない。

## 実行入口

- docs/MODERNIZATION_CURRENT_ID_INDEX_JA.md
- design/modernization_p01_audit.md
- config/modernization_inputs.json、modernization_candidate.json、modernization_rom_repair.json
- scripts/build_modernization_catalog.py、build_modernization_targets.py、build_p01_collection_table.py
- scripts/restore_p01_environment.py、audit_p01_rom.py、audit_p01_references.py、build_p01_rom.py、run_p01_identity_mgba.py

テストは変更に直結するP01各test moduleと既存source-validationの保護テストに限定する。repo全件の新規verifyは設けない。通常プレイ全経路E2Eや他taskのstrict監査へ拡大しない。
