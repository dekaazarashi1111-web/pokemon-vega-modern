# Issue #19 技習得基準復元

固定入口は `CHATGPT_RESUME.md`。この工程は既存の候補ROM・Issue #18 Wiki・native受入原本を変更しない。

## 実装中の区切り

`tools/pr16_learnset_baseline.py` とCLIで、指定ZIPの公式採用1299件を隔離生成する。外側ZIPとmemberのSHA-256/size、canonical key/ID/form、参考JSONLと5 CSV（全経路+4 partition）の全内容を照合する。原本の経路・条件・順序を保持し、原本TM/TR番号を現在のruntime slotと取り違えない。

出力は専用 `.local/` 配下。`official_baseline.jsonl` とper-species index、空の `owner_approved_overlay`、別管理の旧P07全1572行、未取込Vega181種、例外候補台帳を生成する。ZIP内の「Vega保存指示」はVega元来の習得表ではない。

既存P01のキャタピーID649追加訂正と、既存Side Change非採用判断は履歴として保持し、Issue19へ黙って転用しない。原本にあるID1063の159経路/103種は削除せず、engine例外未解決として分離する。これは技1063の新規採用・実装承認ではない。

## 再現

```bash
python3 -B -m unittest tests.test_pr16_learnset_baseline -v
python3 -B scripts/pr16_learnset_baseline.py prepare --zip <固定ZIP> --output .local/pr16-learnset-baseline/new-build
python3 -B scripts/pr16_learnset_baseline.py check --output .local/pr16-learnset-baseline/new-build
```

`prepare` は既存出力を上書きしない。`check` は読み取り専用であり、入力/生成器/出力hashの不一致を修復しない。全ゲーム受入の再実行は含まない。

## 継続が必要な範囲

Vega元来181種の凍結ROM由来またはatwiki一次表とdexNo/SpeciesID/keyの結合、方法別の原本照合、明示例外の判断、runtime全consumer切替、旧候補との差分台帳、後継ROM/Wiki、変更影響に限ったnative受入は未完。基準復元全体・P08 releaseを完了扱いしない。
