# PR16 Issue19: 釣り・隠し野生の特殊技順

状態 `STOPPED_SPECIAL_WILD_DIAGNOSTIC`。run `36152934075` / source `23420259b94bcfff71078d91ccb7593a1c30c92b`。
候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91` / 33554432 bytes。判定 `{}`。

## 今回の境界

新規のnative直接呼出診断であり、通常釣竿/スキャナーUI、通常解禁、捕獲、Save/Continueの受入ではない。
新規起動後のmap/進行flag/profile/RNGは開始fixture。呼出入口/復帰のレジスタ設定も観測区間外。
区間内は7種類のhost書込APIを拒否し、CPUをstepするだけで生成→QOL特殊技第4枠→実V4再初期化→復帰を記録。
保存原本の同一PID/species/level・技4枠/PP/PP Upsを比較する。getter補助は区間外。
候補のStage59入口、Research Economy delegate、V4 delegate、QOL special setterの実通過が必要。
新規unit 13、host compile 1、native process 1。旧受入再実行/ARM/ROM変更0。
Actions終端 `False`。診断のActions成功を製品受入へ読み替えない。
原本 `content/modernization/pr16_special_wild_evidence/36152934075`。1281 identity-only、Issue19全体未完、release_ready=false、PR未merge、baseline不変。

## 次

Issue19: 特殊野生診断の保存失敗原本から未成功caseだけ縮小修復。成功したcase/既受入を再実行しない。Issue19: 特殊野生checkpointの実ROM呼出順とbefore/afterを根拠に釣り/隠し専用の最小修復へ進む。診断済み同条件は再実行せず、変更後の必要な対照だけ追加。通常釣竿/スキャナー操作→捕獲→Save/fresh Continueは未受入。研究孵化15/研究配布17/旧野生/EXP/Bag/egg/旧ARM/Wikiは変更影響がなければ再実行しない。
