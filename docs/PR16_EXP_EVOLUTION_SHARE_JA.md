# PR16 Issue19: 戦闘EXP進化と控え共有

状態 `PASS_BATTLE_EXP_EVOLUTION_SHARE`。入力HEAD `b6b301e673483c01562cb56d69f8104b829a8afd`、run `36084083370`。Actions終端確認 `False`。

候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91` / 33554432 bytesは保存recipeを復元。ROM変更0、ARM0、旧受入native再実行0。

Metapodの戦闘EXP進化承認とB取消、2体Butterfreeの控え共有EXPを別processで検証。原本413/414のlevel/evolution表から期待技を求める。共有の開始flag・個体・EXP・能力・進行はfixtureであり、自然供給や通常UIでのEXP共有有効化の受入ではない。戦闘/進化・Save・fresh Continueの3区間で7書込APIを拒否。出場indexを毎frame観測し控え非出場、攻撃PPのみ消費、HP<=最大HP、全100/200byte保存を確認する。

新unit 6、host compile 1、新native 1。保存成功 ['butterfree-exp-share', 'metapod-exp-cancel', 'metapod-exp-evolve']。未成功 []。原本 `content/modernization/pr16_exp_evolution_share_evidence/36084083370`。

## 次の未完工程

保存3case成功を再実行せずcompleteでActions終端・push・artifactだけ照合する。
