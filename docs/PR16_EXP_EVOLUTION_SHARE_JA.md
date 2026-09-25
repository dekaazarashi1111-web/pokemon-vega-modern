# PR16 Issue19: 戦闘EXP進化と控え共有

状態 `PARTIAL_BATTLE_EXP_EVOLUTION_SHARE`。入力HEAD `023604d280177ad971bac96649b2b15f7c8e42e7`、run `36079548406`。Actions終端確認 `False`。

候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91` / 33554432 bytesは保存recipeを復元。ROM変更0、ARM0、旧受入native再実行0。

Metapodの戦闘EXP進化承認とB取消、2体Butterfreeの控え共有EXPを別processで検証。原本413/414のlevel/evolution表から期待技を求める。共有の開始flag・個体・EXP・能力・進行はfixtureであり、自然供給や通常UIでのEXP共有有効化の受入ではない。戦闘/進化・Save・fresh Continueの3区間で7書込APIを拒否。出場indexを毎frame観測し控え非出場、攻撃PPのみ消費、HP<=最大HP、全100/200byte保存を確認する。

新unit 4、host compile 1、新native 1。保存成功 ['metapod-exp-cancel', 'metapod-exp-evolve']。未成功 ['butterfree-exp-share']。原本 `content/modernization/pr16_exp_evolution_share_evidence/36079548406`。

## 次の未完工程

今回の失敗原本を保持し未受入caseだけ修復する。保存成功caseと旧EXP4/最初の質問拒否/アメ11/Bag23/egg8は再実行しない。
