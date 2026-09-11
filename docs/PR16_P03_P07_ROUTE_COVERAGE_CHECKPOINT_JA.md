# PR #16 P03 / P07 経路被覆 checkpoint

## 結論

この checkpoint は、P03・P07の残件を「表全件をもう一度実行する」という曖昧な状態から、処理所有者ごとの有限な一覧へ変える。

- **P03の追加実操作は2件だけ**である。
  - `P03_GENERIC_FORM_CHANGE_CARRY_PHYSICAL`
  - `P03_FIXED_FORM_TRANSITION_PHYSICAL`
- **P07固有の追加実操作は0件**である。P07で変更した499保持行とHappiny衝突adapterは、親候補 `635fd890…` の実学習・実繁殖・実わざメモリーで受入済みである。
- ショップ表示修正後の後継候補 `e630f7f1…` への受入移送は、P07の経路不足ではない。これは `FINAL_NATIVE_ACCEPTANCE` が扱うP08統合作業として残す。

正本は `content/modernization/pr16_p03_p07_route_coverage.json`、検証器は `scripts/pr16_p03_p07_route_coverage.py` である。

## P03

### 既存成功へ接続した経路

次の経路は新規残件にしない。

1. レベル習得と進化習得。空き枠、満杯、取消を含む。
2. 通常の預け入れ・受取・タマゴ・孵化。父、母、両親、重複防止、対象なしを含む。
3. ピチューの条件技とピンプクのおこう分岐。
4. 通常技・タマゴ技のわざメモリー、技忘れ、保存再開。
5. 機械技・教え技の追加アーカイブ。機械と教えを別処理のまま、空き枠、4枠置換、拒否、ロック、取消、ページ境界、保存再開まで受入済み。
6. 943受け手・5,023行の共有タマゴ技静的照合と、バクーダ・ドンファンの16操作。
7. 実受付を通るRotom 5フォームの付与・解除・満杯拒否・取消・保存再開。

通常繁殖を共有技の受入で代替したことにはしていない。通常繁殖はrun `34434453733` の8ケースそのもので接続した。

### 残る2処理所有者

Stage73のフォーム契約は70経路・19種である。内訳を処理所有者で分けると次のとおり。

| 所有者 | 経路 | 種 | 状態 |
|---|---:|---:|---|
| generic form-change carry | 61 | 10 | 実操作不足 |
| existing fixed transition | 4 | 4 | 実操作不足 |
| Rotom bespoke transition | 5 | 5 | 実受付で受入済み |

したがって、Rotomをもう一度試すことも、70経路を総当たりすることも残件ではない。実際の非Rotom入口からgeneric carryを1件、実際の固定遷移または戦闘変身入口からfixed transitionを1件通し、同一個体、技スロット、取消、通常保存、fresh Continueを確認する。

## P07

### 静的照合

- ベガ種から通常技への歴史的採用: 1,073行
  - レベル450
  - タマゴ254
  - 機械179
  - 教え190
- 通常種からベガ技への保持: 499行
  - レベル310
  - タマゴ189
- 欠落・競合: 0

### 変更面と受入

P07が親候補へ加えた処理面は次の3つに限定される。

1. 保持レベル310行。Taillowのmove 457を空き枠・満杯・取消・保存再開で確認済み。
2. 保持タマゴ189行。Taillowのmove 466をわざメモリーで、Pichuのmove 440を通常の預け入れ・受取・孵化・保存再開で確認済み。
3. Happiny衝突adapter。moves 461/464/357を実おこう繁殖の先頭・中間・満杯・対照で確認済み。

1,073採用行はP07差分で書き換えた処理面ではなく、Stage84親候補から保持した内容である。ROM表の全件照合は0不足であり、各供給源はP03側の合格済みconsumer契約へ対応する。よって、1,073行を1行ずつ再実行することも、4供給源について「変更行の受入」と称して新規ケースを増やすことも行わない。

## 候補SHAの扱い

既存成功は元の候補SHAとrun IDを保持する。この台帳は古い成功を `e630f7f1…` の新規実行へ付け替えない。

- P07親候補: `635fd890a8d1071560d3cb56c9c663425f7c988119ce098dedad6bf6554f973e`
- 後継候補: `e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267`

後継候補で必要な変更影響回帰と受入集約はP08で行う。

## 検証

```bash
python scripts/pr16_p03_p07_route_coverage.py
python -m unittest tests.test_pr16_p03_p07_route_coverage
```

`p08_remaining_work.json` を投影内容へ更新するときは、正本を検証してから次を実行する。

```bash
python scripts/pr16_p03_p07_route_coverage.py \
  --apply-remaining content/modernization/p08_remaining_work.json \
  --output artifacts/pr16-p03-p07-route-coverage/receipt.json
```

この更新でP03は2件の具体的な実操作待ちへ変わり、P07の経路残件は親候補上で閉じる。ただしP08、release-ready、clean-ROM再生成、PRのマージ状態は変更しない。
