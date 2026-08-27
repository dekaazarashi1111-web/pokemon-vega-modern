# blockers.md

(When blocked, the loop writes a short entry with reason, repro command, artifacts dir, and the next action to take.)

## 2026-08-19T17:07:56+09:00

- Task: `USER-20260819-TRAINER-CHANGEKIT-FINAL-INTEGRATION`
- Block reason:
  - 公式Task 05 validatorが`ENC_TOHOKU_REF_1012`でFAILする。
  - Tohoku 1,101論理行のうち51行は`trainerbattle`でなくtrainer flag consumerで、実戦闘候補はすべて別行が所有済み。全1,302固有partyを接続する物理consumerが存在しない。
  - Kanto 3戦がStage 34取得イベントと同一source object／座標を競合する。Task 06に代替配置とcollision／sightline証跡がない。
  - Kanto会話35本文／814行は現行charmapでencodeできず、承認済みかな本文またはrenderer/font入力がない。
- What you tried:
  - RECOVERED Stage 34の全snapshot hash、Git、ROM、focused checkを再検証した。
  - 元AUTHORING／ChangeKit ZIPをfresh展開し、公式validatorを順番に実行した。
  - UNKNOWN 54件だけでなくTohoku 1,101行をStage 34 ROM／T02 rooted graphへ全件照合し、command ownerと候補衝突を再計算した。
  - Kanto 188新規戦の198 object componentをclean source object、Stage 34 existing object、取得host、object budgetへ照合した。
- Error excerpt:
  - `party/partition format mismatch: ENC_TOHOKU_REF_1012`
  - `ENC_TOHOKU_REF_1012 @ 0x0885B0C0 = 0x62 cleartrainerflag 708`; real kind-8 command `0x08890AFB` is owned by `ENC_TOHOKU_REF_1013`。
  - Tohoku opcode totals: `trainerbattle=1050`, `checktrainerflag=7`, `settrainerflag=40`, `cleartrainerflag=4`。
- Question for human:
  - 51行を除外して件数を改訂するか、51個の新規物理戦の正式仕様を提供する必要がある。
  - Kanto競合3件の代替object／座標と、会話35文の承認済みかな本文または漢字renderer素材が必要である。
- Next step:
  - `reports/TRAINER_CHANGEKIT_FINAL_INPUT_BLOCKER_20260819.md`の再開条件を満たす補正版AUTHORING_KIT／Task 01〜06を受領し、全validator PASS後に同じStage 34から統合を再開する。

## 2026-08-19T20:08:50+09:00 解消

- Task: `USER-20260819-TRAINER-CHANGEKIT-FINAL-INTEGRATION`
- Resolution:
  - REF_1012は受領ZIPを変更せず、kind 8 DOUBLEの独立Archive consumerへ正規化し、AUTHORINGとTask05の補正版ZIPを再manifest化した。
  - flag命令誤認51行と共有command追加20行は71個の固有Archive物理consumerへ接続し、元flag／既存ownerを上書きしない。
  - Kanto競合3件は取得hostを保持したまま同map最近傍安全tileへ再配置し、814会話行は決定的かな正規化と幅検証を通した。
- Verify: 入7 validator、focused 30 tests、mGBA quick/full、clean rebuild、完全版ZIP fresh展開検証がすべてPASS。

## 2026-08-27T13:12:20+09:00

- Task: `USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR`
- Block reason:
  - Stage 55はローカル22 fixture×独立2 processとiPad配置をPASSしたが、タスク仕様が必須とするユーザーのiPad実プレイ承認が未受領である。
- What you tried:
  - Stage 55 ROMと正常進行saveを旧成果物と別basenameでiPadへ配置し、size／SHA-256 read-back、RetroArch停止、既存成果物不変を確認した。
  - 博士同期／メニュー、近隣NPC、trainer、item、field object、正しい知恵の洞窟とwildをローカル実入力E2Eで検証した。
- Error excerpt:
  - 実行エラーなし。人による実機プレイ確認だけが未完了。
- Question for human:
  - Stage 55で既知症状が解消したか、iPad実プレイ結果の承認または再現地点を受領する必要がある。
- Next step:
  - 承認受領後にタスクを再開してDONEへ更新する。不具合報告の場合はStage 55のexact map／local ID／入力列へ固定して修正する。
