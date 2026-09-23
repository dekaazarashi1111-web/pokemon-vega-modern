# Issue19: 通常Bag・習得技戦闘・保存再開

候補 `6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2` / CRC32 `00F31AF7`。ROM変更0。

## 完了: Bag/習得/Save/Continue

run35831256129/job107084145752 completed/success、反映 `574975b3ea189ae37c4258c583ba5d1efb1c5d82`。23ケース・46fresh core。Floette追加12技、殿堂入り前後、raw40ページ/選択/取消、既習得除外、通常思い出し、4技/PP、100byte party、通常Save counter2→3とfresh Continueを受入。20境界試験を継承し追加12試験成功。元失敗run35830398856は履歴として保持。Task初期化前のDOWN送信を60frame待ちで修復しmode6/11技を確認。

正本 `content/modernization/pr16_learnset_gameplay_checkpoint.json` / `content/modernization/pr16_learnset_gameplay_completed_actions.json`。初期party/進行/道具はfixtureであり、通常ストーリー取得の受入ではない。

## 今回: 保存済み習得個体からの通常戦闘

run35832603358、source `ea7cf90458ee011719c7aafd137c740a97320c05`、状態 `FAIL`。追加unit 16件、native 0 process。正本 `content/modernization/pr16_learnset_battle_checkpoint.json`。Bag再実行0。成功時は習得済みFloette420の100byteを初期fixtureとして継承し、歩行遭遇→通常の技選択→PP消費/敵HP低下→帰還→通常Save/fresh Continueを確認。タマゴ/全owner/全技戦闘の受入ではない。Actions終端は後続の記録限定照合で確定。

## 見た目の証拠の限界

保存/再開のfield画像は確認。旧Bag runのsummary16画像はフェード中の黒画面で、一覧もstate4から直接進むためstate6撮影がない。実入力/nativeメニュー/文字列/100byteの証拠と、見た目の受入を混同しない。全23ケースを撮影のために再実行しない。

## 次の未完

最新battle checkpointのerrorと原本を先に読み、未受入の戦闘だけ修復する。Bag23/32unit/Wiki/旧hookは再実行しない。
