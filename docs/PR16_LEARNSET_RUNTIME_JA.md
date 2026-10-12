# Issue19: ゲームconsumer接続

2入口GetLevelUpMovesBySpecies/CanMonLearnTMHMを新ROM aabd52a0へ接続。配置/全差分rollbackと13代表owner×2process/3382直接callを受入。188保全枠/保存個体不変。初期4技・自然level-up・条件consumer・通常操作E2E/別Wikiは未完。

## 受入境界
run35704908254 / HEAD `ba4a6367c5179372d06138fef02f0aa29588d0e2`。候補SHA-256 `aabd52a0db65737b2da0d61bd60c355bedd6ef307b6f60bffad7465d3a6ee56c`、33554432 bytes、CRC32 47902B58。

通常操作E2Eではない。host fixtureから2関数を直接呼ぶROM診断であり、自然な習得/保存/Continueを証明しない。既存4技を書き換えず、archive追加供給は0。

19試験・1671 owner・213888 machine queryの成功原本、独立2ARM配置を継承。回復runでhost/ARMを重複実行しない。過去failureは改作しない。詳細は `content/modernization/pr16_learnset_runtime_checkpoint.json` と `content/modernization/pr16_learnset_runtime_evidence/verification.json`。

## 次工程
Issue19: aabd52a0の保存配置と親/Eternal payloadを再利用し、初期4技・自然level-up・進化/思い出し等の条件consumerを明示ownerへ接続。別候補Wikiと影響nativeを生成し、通常操作E2Eを受入する。2入口直接callは再実行しない。
