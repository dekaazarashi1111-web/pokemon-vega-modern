# PR16 Issue19: 最初の質問での拒否

状態 `PASS_BATTLE_EXP_FIRST_REFUSAL`。入力HEAD `f99b97530b25e11e71ee5d89363d33ca585a8af8`、run `36071876126`。Actions終端確認 `False`。

候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91` は保存recipeを復元。ROM変更0、ARM0、旧4境界native再実行0。

battle script 0x5aを観測して通常B、0x5bで通常A中止確認。技一覧summaryへ入った場合は失敗。Lv43→44、拒否技497、保存4技と未使用PP、攻撃PP消費、正常HP、Save counter2→3→3と100byteをfresh coreまで照合する。開始個体/EXP/能力/進行はfixture。

新unit 5、host compile 1、新native process 1。受入case ['butterfree-exp-first-refuse']。失敗 {}。原本 `content/modernization/pr16_learnset_first_refuse_evidence/36071876126`。終端照合時のunit/native/host再実行は0。

旧受入の `pr16_learnset_boundaries_checkpoint.json` とguideは不変。first-question refusalをsummary-B拒否で代用せず、今回1caseを全owner/進化/共有EXP/自然供給の証明にしない。

## 次の未完工程

native成功を再実行せずcompleteでActions終端・push・artifact原本だけ照合する。

## 日本語版symbol訂正と履歴

初回run36071387743はsummaryへの到達を検出してFAIL（未受入、履歴保全）。コメントの英語版RAM0x02023D74ではなく、固定CFRU-JP BPRJ.ldのgBattlescriptCurrInstr=0x02023CD4を使用する。ROM/opcode/状態は変更しない。成功unit21の原本をhash照合し、変更なし20を再利用。今回unit5は新binding4と変更C構造1。合計25種のunit契約。旧4成功のnative再実行0。実行/記録入口は scripts/pr16_first_refuse_jp.py。
