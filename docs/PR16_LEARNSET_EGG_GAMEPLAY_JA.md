# Issue19: 条件付きタマゴの通常操作

候補 `6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2`、run35837431004 / source `d9227eeb0ff92e523e4d2f848909b50ec83f022f`。状態 `PASS_SCOPED`。

育て屋へ親2体を通常会話で預ける→実歩行で生成→通常受取→タマゴSave/fresh Continue→実歩行/通常孵化→孵化後Save/fresh Continue。親個体・開始地点はfixtureであり自然捕獲は主張しない。

## 限定変更影響

PichuのLight Ball父/母・未所持・旧440除外・重複と4枠、Happinyの母/父incense・旧461/464/357除外・未所持Chansey分岐の8ケース。期待技は保存済み原本spanから固定し、タマゴ技関数の返り値をoracleにしない。344を通常タマゴ表へ平坦化しない。

追加unit 18件、native 8process、成功8ケース。成功時各3fresh core、7観測barrier、手動Save2回+自然孵化登録1回、子/親/queue bytesを照合。全孵化経路/全owner/Issue19全体/releaseの受入ではない。

正本 `content/modernization/pr16_learnset_egg_gameplay_checkpoint.json`。失敗は削除せず同run原本から読む。Actions終端は後続の記録限定照合で確定。

## 次

Issue19: 条件付きタマゴの8ケースは保存原本/最新Actionsから判定し、成功ケースを繰り返さない。次はBag一覧/summary撮影の限定修復と、未受入consumerの変更影響を絞る。Bag23/通常戦闘/Wiki/4hook/ARM/PLA1/PLC2の再実行禁止。
