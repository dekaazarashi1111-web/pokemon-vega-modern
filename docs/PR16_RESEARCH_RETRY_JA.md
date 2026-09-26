# PR16 研究保存・同一core再試行

修正版の同一core再試行3ケースと影響のある拒否/回復4controlを実測。成功 7 / 7。

測定runの終端を原本照合してから、未検証のV1通常load adapterを進める。失敗ケースがある場合はその原本と原因だけを先に扱う。受入済み再試行/29unit/旧18取引/BP/P08/特殊野生は影響なしに再実行しない。

## 原因と修正

旧4aee03e8候補では空ledger初期化のphase0保存失敗後、V2 RAMだけが残る。同一coreの再試行はSAVE_EMPTYを通らず、保存なしでblockedを解除する。旧候補のnative原本は content/modernization/pr16_research_retry_local_diagnostic.json。ローカル実測1process/1coreでありActions実測とは区別し、再実行しない。

canonical ensure_save_idleは初期化前の2048byteを既存rollback領域に保存し、失敗時に全復元する。V1と初期化の失敗経路を共有し、同じcanonical関数本文だけをThumb ARM7TDMIで既存188byte窓へlinkする。新規ROM/RAM配置なし。窓外全byteとrollbackを確認する。

## 検証scope

zero/erased/V1について保存不可を2回連続で実行し、入力全復元・128KiB Flash不変・blocked保持を検査。可用性fixtureだけを戻して同じcoreで再試行し、実保存1回/counter+1、その次は追加保存0回を確認。実DestroyTaskで各callbackを終了し、通常schedulerへの復帰まで観測する。fresh通常Continueを2回行い全ledger/owner/Bag/手持ちを照合。7host書込みAPIを観測中禁止。

変更影響のあるV1 checksum/tail拒否、既存V2 idle/blocked解除を4controlとして検証。29unitには同じcanonical関数のstub境界試験を含む。stubは実Flash受入ではない。旧18境界/BP/P08/特殊野生の原本は不変、新候補の全取引受入へ再ラベルしない。物理Flash装置故障、V1通常load、通常new-game/取引UI、全catalog、map3/19除外130行、Issue19全体/releaseは未完。

## 記録

source `9978dcfdafe356dd4815b021aa897e4e605abc34` / run `36236714339` / 候補 `58079dfbdbe15899d9b86f53ad3a21fe46ddcebf5fed231c85dcd2332ddd2d75`。
受入: reject-v1-checksum, reject-v1-tail, retry-erased, retry-v1, retry-zero, valid-v2-blocked, valid-v2-idle。失敗: 。Actions終端確認: False。
