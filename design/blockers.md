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

## 2026-08-27T13:26:18+09:00 解消

- Task: `USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR`
- Resolution:
  - ユーザー指示によりiPad配置、実機プレイ、人手承認を今後の完了／release gateから分離した。
  - Stage55は既に22 fresh-core fixture×独立2 process、全map owner監査、BPS往復、
    declared span外0、allocator overlap 0、warnings 0をPASSしているためDONEへ確定した。
  - iPadへのROM／save配置は希望時だけ行う任意運用とし、未実施や接続不能をblockerにしない。

## 2026-09-08T12:53:05+09:00

- Task: `USER-MODERNIZATION-P04` / Winds/Waves新規3種の完全GBA素材
- Block reason:
  - Browt、Pombon、Gecquaについて、front／back／icon／normal・shiny paletteを揃えた出典固定可能なGBA素材setを確認できない。
  - 40x40 RGBAなど部分画像だけを、完成済み64x64 4bpp素材やpaletteとして偽装できない。別種画像や自動placeholderも採用しない。
- What you tried:
  - 固定DPE-JP、Shiny-Miner DPE、rh-hideout／TeamAquasHideout系、`xirosrh/wah-20-anniversary`、`Schn4pper/pokenigme`を対象名・asset directory・species symbolで照合した。
  - Mega 49件／Stone 45件は固定sourceから取得でき、Tatsugiri 2形態の共通paletteも解決したが、上記3種の完全setは0/3だった。
- Error excerpt:
  - 実行errorなし。P04 asset manifestの`winds_waves_new_species`は`covered=0, required=3`、`fake_or_placeholder_generated=false`。
- Question for human:
  - 後で完全素材を含むrepository／ZIPを指定するか、既存デザインを参照した新規sprite制作を別途承認する必要がある。
- Next step:
  - 3種のID予約を維持したまま、素材に依存しないMega 49件、Stone 45件、ID／runtime／save拡張を先行する。完全素材受領後に同じstable keyへ差し替える。


## 2026-09-13T22:07:05.622379+00:00 — USER-20260914-BP-PARTY-RETENTION
- Timestamp: 2026-09-13T22:07:05.622379+00:00
- Version: PR16 party retention WIP
- Task: USER-20260914-BP-PARTY-RETENTION / 次戦で交換個体が失われる問題の修復
- Status: BLOCKED
- Summary: WIP: 次戦限定predicateとhost4回帰はPASS、固定candidateのowner監査run34785149994もSUCCESS。target呼出位置/ABIの確定・runtime接続・修復後native保持検証は未完。追加コード反映2回がOpenAIのツール安全性確認でブロックされたため、以後は解析/接続を停止して記録のみ実施。GitHub権限不足ではない。
- Verify: host4tests PASS、owner Actions run34785149994 SUCCESS、artifact10325794218の全member hashを照合。記録回帰・resume tests/check・task graph・diff/index guard差分をpublish gateとする。native保持検証は未実行。
- Files changed: predicate/C、host tests、owner script/workflow（WIP48a36ca）。今回は記録script/tests/workflow、WIP evidence JSON、固定引継ぎMD/JSON、P08 resume、両ログとblockers。
- Commit: 実装WIP=48a36caf3361b1d167c302174eb2c4c4121c7508。記録はこの追記を含むcommit。入力HEAD=edd559148f79e65730d5ab0ccfba13ed6400e364。非force push後のhashはworkflow result.jsonとremote refで照合。
- Network: GitHub connector/API・既存Actions artifactのみ。記録工程はROM/私有入力を開かず、native実行なし。
- Blocker/Error excerpt: OpenAIツール安全性確認が追加コード反映2回をブロック。GitHubアクセス不足ではない。
- Boundary: candidate7f32/CRC0D5D9178、正式physical4/P08 gate2、BP未受入、PR open/draft、baselineを維持。merge/releaseなし。受入済みcaseの再実行0（選択工程）。自動起動既存CIは別記。
- Question for human: 権限確認の再依頼は不要。停止した要求は反復しない。
- Next step: 保存済みWIPとowner監査を再利用し、未接続のtarget呼出位置/ABI照合・最小successor接続・修復後native個体保持検証を完了する。既存host4回帰/owner監査の単独再実行や同じtool-blocked要求の反復は行わず、保持確認前に2/3戦目・BP報酬へ進まない。


## 2026-09-14T02:01:10.448721+00:00 — USER-20260914-BP-RETENTION-RESUME-NOTE
- Timestamp: 2026-09-14T02:01:10.448721+00:00
- Version: PR16 resume note
- Task: USER-20260914-BP-RETENTION-RESUME-NOTE / 未反映ABI案と再開停止の記録
- Status: BLOCKED
- Summary: 2026-09-14再開: target呼出位置/ABIの追加検証コードをローカル作成し、新規8testsはPASS。ただしGitHub create_treeによるコード・workflow追加1回がOpenAI安全性チェックでブロックされ、branchへ未反映。追加Actions/target照合/runtime接続/native保持検証は未実行。GitHub権限不足ではない。同一要求を別経路で反復せず、今回は停止記録だけを更新。
- Files changed: 記録script/tests/workflow、既存WIP JSON、固定引継ぎMD/JSON、P08再開文、両ログ、blockers。target/runtimeファイルは未変更。
- Verify: ローカルABI案8tests PASS（未反映・Actions未実行）。記録回帰/resume check/tests、task graph、diff/index guard差分をpublish gateとする。
- Native: 今回0process、受入case再実行0、candidate変更0、target ABI/保持は未検証。
- Commit: この記録を含むcommit。entry=aece42964c1ff7b9c2bfd3d3c10bdd863d95febd、記録入力HEAD=d4e1d94f3e34622136c126d3002307c009362fef。非force push結果はworkflow result.jsonとremote refで確認。
- Network: GitHub connectorのread・owner artifact取得・create_tree拒否。記録Actionsはmetadataのみ照会。private入力復元なし。
- Block reason: OpenAIツール安全性チェック。GitHub権限エラーではない。追加コード要求1回を拒否、同じ要求の再試行なし。
- Error excerpt: このツールの呼び出しは、OpenAI の安全性チェックによってブロックされました。
- Question for human: 権限確認の再依頼は不要。正式受入・旧失敗原本を変更しない。
- Boundary: BP未受入、physical4/P08ゲート2、PR open/draft、baseline維持。merge/releaseなし。
- Next step: 保存済みWIP48a36caとowner run34785149994を再利用し、未完のtarget呼出位置/ABI照合・最小successor接続・修復後native個体保持検証を進める。ローカル8testsをtarget照合や反映済み実装と混同しない。同一tool-blocked要求や既存host4/ownerの単独再実行をせず、保持確認前に2/3戦目・BP報酬へ進まない。
