# Issue19: V4固定野生技の分離・自然生成と戦闘EXP

状態 `PASS_WILD_INITIAL_AND_BATTLE_EXP_EMPTY` / run36042409576 / source `29aee3e4fbaf4618425ff1bad26838aa1bad8d7e`。
候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91`。Actions終端確認 `True`。

## 原因と実装

run36041199782の受動命令traceで、初期化が原本[92,537,76,147]を与えた後、V4 wild-only adapterが[72,488,73,182]を2回上書きすることを確認。
`MoveDistributionV4_ApplyWildInitialMoves`の入口0x093925F4だけを新adapterへ接続。原本/旧V4表は履歴として不変。
新adapterは敵partyの正規6slot、非egg、PLR1 prepared owner、level1..100に限定。条件確認前は書込み0。
対象だけ技4枠/PP4枠/PP Upsを消し、保存済み原本initializerで現Speciesの技を設定する。保管個体/保全ownerへの一括移行ではない。
旧code/PLR1/初回level-up修復/P03進化分岐は変更しない。宣言外差分0・byte全体rollback照合。

## 検証と範囲

new unit16 / inherited unit25 / new ARM1 / native1 / successful cases1。開始バタフリーLv43、EXP閾値-1、技53/89、能力値999、開始進行は明示fixture。
野生タマゲタケLv76の初期技/PP、通常キー戦闘→EXP→Lv44技497、通常Save→新core Continueを検査。
3観測区間は7API host書込禁止。全owner/通常手持ち取得/最終バランス/釣り/隠し/自然孵化/配布/form/EXP共有/置換/拒否/進化には拡張しない。
アメ11/Bag23/egg8の経路は新しい野生専用入口を通らないため再実行0。旧battle証拠は履歴として保持し新候補の全戦闘受入へ流用しない。
旧ARM/全件host/Wiki/原本の再生成0。新ARMはこのadapter1 translation unitだけ。
原本 `content/modernization/pr16_learnset_natural_evidence/36042409576`。最初のFAILとtrace停止/補助metadata停止も改変せず保持。
run36040259713のunit25表記は実行でなく継承（新unit0/native0）であり、保存inherited-unit.jsonを正とする。

## 次

Issue19: V4固定野生4技の切離しと自然野生初期技/戦闘EXP空き枠の保存成功は再実行しない。未受入の自然配布/孵化/form、戦闘EXP置換/拒否/既習得/複数level/進化/共有を影響台帳と照合して限定追加。釣り/隠し等の同じ野生adapterへの特殊技順は未受入。原本再採取/旧Wiki/旧host/ARM、アメ11/Bag23/egg8は変更影響なしに再実行しない。全owner/Issue19/release/baseline切替は未完。
