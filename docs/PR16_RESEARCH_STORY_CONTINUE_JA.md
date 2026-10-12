# PR16 保存スターター以後の通常進行

## 今回の限定受入

保存starter以後のライバル敗北復帰→研究所退出→517番道路の木の拒否→東側道路map3/19→Save counter1→2→独立Continueを限定実測。次は後継artifactのroute.srmから未完ストーリーへ。研究活動施設への自然到達は未完。初期化/スターター/完了区間/旧RP/UI/BP/P08を再実行しない。

正本: `content/modernization/pr16_research_story_continue_checkpoint.json`。正式source `4c5d2d46bbef7f984800ea4133afe0388ac4c73d`、run `36325475401`。専用Actionsの成功終端とartifact IDは外部API確認待ち。全体完成ではない。

## 実装と検証

新continuation oracleは保存前提をstarter artifact10932059074に限定し、通常ライバル戦での敗北・正常復帰を勝利へ読み替えない。517番道路の切れる木は会話だけで通過せず、町へ戻って東側道路map3/19へ進んだ。114入力/12012frames、実画面21枚、通常Save1回。別coreのContinueは12入力/1390frames・実画面1枚、party600bytes/Flash128KiB/研究ledger/位置/RP0/counter2を保持。戦闘flags/outcomeは一時状態として0へ初期化。

新59oracle/拒否試験は成功原本とsource一致を再利用。最初のContinue入力件数誤記(17→実測12)は失敗receiptを保持し、そこでの負例okを受入しない。ローカル開発native2、正式native2は別会計。旧受入ケースの再実行0、NewGame再生0、guard再起動0、host/ARM compile0、ROM変更0。固定runnerの7禁止barrierと候補全体SHAを維持。

## 重複防止と後継保存

通常生成route.srmは131088bytes / SHA-256 503e26cfdc8605ff79984afdcab3ffd9ce448f4557a8d1cdf64526ad15cdd65a。map3/19 (1,14)、party1/RP0/counter2。固定runtime10898620034・data10898510128とrunner identityをcheckpoint.jsonで照合する。保存原本を保全し作業コピーだけに continue-story と全Save SHAを渡す。次回の入力はこの地点より先だけで、既存commands.txtは再生しない。

研究活動施設(map96/0→98/3)への通常到達、全体ストーリー、releaseは未受入。merge/active baseline変更なし。一般CI action_required/失敗と歴史的全体private guardを成功へ読み替えない。ROM/save/runner/画面はartifactだけに保持しGit trackedには入れない。

## 外部から確認した成功終端と次の再開点

run36325475401/job108637305546の全11必須stepがcompleted/success。完了commit64777bc7fea788561a994bb3589bcf9a89c26175。上の外部確認待ちは記録時点の説明で、現在は終端確認済み。receiptは `content/modernization/pr16_research_story_continue_terminal.json`。artifact10933499471 `pr16-research-story-continue-checkpoint` は1313382bytes / SHA-256 55e88187f9dbc5ed2f075857506071a06789ae03c57004f8a0f4d54b0f251362、期限2026-12-26。ZIP42member・通常生成Save/RTC・runner・22画面・原本JSON・全commit snapshotを照合した。終端照合でnative/compile/unit再実行0。

次はartifactのroute.srmを作業コピーへ複写し、同じ固定candidate/runtime/runnerでContinueする。counter2、map3/19 (1,14)、party1、RP0。

```text
<fixed-runtime>/ld.so --library-path <fixed-runtime>/lib <checkpoint>/runner <fixed-candidate> <working-route-save> continue-story 503e26cfdc8605ff79984afdcab3ffd9ce448f4557a8d1cdf64526ad15cdd65a
```

stdinは `key <mask> <frames>`、`observe <連番>`、`save`、最後に `quit`。観測0はContinue後の自動観測なので追加観測は1から。maskは0/1/2/8/16/32/64/128、framesは1〜600。完走した114入力は再生せず、この地点より先へ進む。517番道路の木は未通過で、ライバル戦は敗北後に正常復帰した経路である。研究活動施設への到達は未完。一般CIと全体完成をこの限定成功へ混同しない。
