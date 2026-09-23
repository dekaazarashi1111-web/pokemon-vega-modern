# Issue19: 通常アメlevel-up・進化・保存再開

候補 `6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2`、run35850873307 / source `502e5c35f5960cbd1c1adb5b334c588715574e5a`。状態 `FAIL`。

11ケース: キャタピーの空き枠/置換/拒否/summary取消/既習得/閾値未満、キャタピー→トランセルとトランセル→バタフリー、バタフリー同level3行/先頭既習得/3行拒否。原本level/evolution spanを別々に照合し通常習得後の進化技順を検査。通常Bagアメ消費→習得/進化→通常Save→新coreのContinueで全100bytes・PP・道具消費を保持。

開始個体/進行/道具はfixture。ふしぎなアメによるlevel-upは実操作だが戦闘EXP由来level-upや野生/配布の初期技生成ではない。3観測区間は7API書込barrier。区間外GetMonDataのCPU復元付き測定をnative gameplayの追加入口へ読み替えない。

新unit 31 / 継承unit 0、新native 11、今回成功fresh core 16、累計成功8ケース。失敗原本と成功原本を保持し成功caseの単純再実行禁止。正本 `content/modernization/pr16_learnset_progression_checkpoint.json`。Actions終端は後続の記録限定照合で確定。

## 次

Issue19: 保存された通常Bagアメlevel-up/進化の成功ケースは再実行しない。未成功caseだけ修復し、完了後は自然生成の初期技・戦闘EXP由来level-upの変更影響へ。Bag23/通常戦闘/条件付きタマゴ8/代表画面/Wiki/旧4hook/ARM/PLA1/PLC2は不変・再実行しない。全owner/Issue19/release/baseline切替は未完。
