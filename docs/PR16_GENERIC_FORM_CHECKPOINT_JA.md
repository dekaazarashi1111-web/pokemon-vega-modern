# PR #16 generic FORM native acceptance checkpoint

## 結論

`P03_GENERIC_FORM_CHANGE_CARRY_PHYSICAL` は、親候補
`635fd890a8d1071560d3cb56c9c663425f7c988119ce098dedad6bf6554f973e`
上の実ROM操作で受入済みである。

正本receiptは `content/modernization/pr16_generic_form_acceptance.json`、
再検証器は `scripts/pr16_generic_form_checkpoint.py` である。Actions原本は
`content/modernization/pr16_generic_form_evidence/34675976411/original.zip`
として保持する。

## 固定した原本

- run: `34675976411`
- job: `103505793891`
- tested HEAD: `92db3605070c65206696b03f8ab6bd596ae7d729`
- artifact: `10292791318`
- artifact name: `pr16-generic-form-carry-acceptance`
- ZIP size: `372130`
- ZIP SHA-256: `f5d41c58ae1be0303dd7157d08bcee77ecd5018cbbc11e4cc4d30b1a9635914b`
- candidate ROM SHA-256: `635fd890a8d1071560d3cb56c9c663425f7c988119ce098dedad6bf6554f973e`

GitHub APIのartifact digestと保存したZIPのSHA-256は一致する。ROM、save、private archiveは
原本ZIPにもリポジトリにも含めない。

## 受入範囲

実受付 `(map 1/36, x=6, y=3)` を開き、FORMメニューを入力だけで有限探索した。
2つのacceptance processはいずれも `page=1, cursor=1, probe_count=7,
pages_scanned=2` でform index 43を発見した。

- `shaymin-four-slot-roundtrip`: Land→Sky→Land、同一個体、4技・PP・PP bonus・順序、通常save、core破棄、fresh Continueを確認。
- `shaymin-party-cancel`: native party pickerの取消後に状態不変、通常save、fresh Continueを確認。
- acceptance process: 2
- acceptance fresh core: 5
- write-guard negative control: 7種類
- rendered witness: 44枚

入口条件診断14 processは `PASS_DIAGNOSTIC_ONLY` のまま保持し、acceptance件数へ加算しない。

## 主張しないこと

この受入は、61行を同じ実装所有者の有限なgeneric carry契約としてShaymin代表で受け入れる。
61行を個別に実行したという主張ではない。次もfalseのままである。

- fixed-form transition acceptance
- full P03 acceptance
- 後継候補へのP08 evidence transfer
- clean-ROM regeneration
- release readiness
- active baseline change

P03で残る実作業は `P03_FIXED_FORM_TRANSITION_PHYSICAL` だけである。

## 再検証

```bash
python scripts/pr16_generic_form_checkpoint.py
python -m unittest tests.test_pr16_generic_form_checkpoint
python scripts/pr16_p03_p07_route_coverage.py \
  --check-remaining content/modernization/p08_remaining_work.json
python -m unittest tests.test_pr16_p03_p07_route_coverage
```

原本を未配置の環境で権限付きGitHub CLIを使う場合だけ、固定run/artifactを取得する。

```bash
python scripts/pr16_generic_form_checkpoint.py --fetch
```
