# PR16 Issue19: 最初の質問での拒否

状態 `PARTIAL_BATTLE_EXP_FIRST_REFUSAL`。入力HEAD `dbba6d9d7623bb8b2987244e7f3a89126a51b1b0`、run `36071387743`。Actions終端確認 `False`。

候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91` は保存recipeを復元。ROM変更0、ARM0、旧4境界native再実行0。

battle script 0x5aを観測して通常B、0x5bで通常A中止確認。技一覧summaryへ入った場合は失敗。Lv43→44、拒否技497、保存4技と未使用PP、攻撃PP消費、正常HP、Save counter2→3→3と100byteをfresh coreまで照合する。開始個体/EXP/能力/進行はfixture。

新unit 21、host compile 1、新native process 1。受入case []。失敗 {'butterfree-exp-first-refuse': {'error': 'command failure: butterfree-exp-first-refuse', 'type': 'ValueError'}}。原本 `content/modernization/pr16_learnset_first_refuse_evidence/36071387743`。終端照合時のunit/native/host再実行は0。

旧受入の `pr16_learnset_boundaries_checkpoint.json` とguideは不変。first-question refusalをsummary-B拒否で代用せず、今回1caseを全owner/進化/共有EXP/自然供給の証明にしない。

## 次の未完工程

今回失敗原本を保持し、最初の質問での拒否だけ修復する。旧EXP4成功/アメ11/Bag23/egg8は再実行しない。
