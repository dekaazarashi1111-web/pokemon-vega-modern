# Stage81 native PP候補のP08受入

## 固定対象と原本

- Stage81 SHA-256: `521624a5e6065bd969b7c3143044f1d96491b8af05a0231827ba2e709d04d579`
- 不変のStage80親: `6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3`
- 7領域の新規実行: run `34368455589` / HEAD `40d2e8e49ed79a69c7675de8cd0cbb4a43677334`
- P03満杯技枠等: run `34364100108` / HEAD `f1342a81d19f5c26d7f2efdfa7cec0aa05c148fc`

P03の生成レシピは分類済み5箇所・20バイトを修正する。旧8バイト試作とは別である。
元のStage80 SHA、各命令とliteral、対象外の全領域、Stage81 SHA、修復報告書を検証する。
実操作試験はBug BiteのPP20と全4枠の保持を含み、4枠それぞれの入替、拒否、選択画面の
キャンセル、空き枠習得、早期習得しない対照を検証する。通常保存後に元coreを破棄し、
新規coreの通常Continueで復元を確認する。修正前の空き枠・入替1ケースずつはPP45で
想定通り失敗する。異常終了は失敗対照の成功に数えない。

Stage79の各領域runner・期待値・終了コード・ROMハッシュ検査は変更していない。
Stage81 adapterはStage78→80を既存検証器で通した後、厳密なStage81 childを検証する。
GitHub固定環境でplan、全7領域、mergeは成功。matrixは新規mGBA7件・キャッシュ0件であり、
mergeの再利用7件はこのmatrix結果を読むだけなので新規実行として二重計上しない。

## 原本照合と再現

`content/modernization/p08_stage81_evidence/` にZIP原本とその全メンバー、Actionsの
run/job/step/artifact識別情報、実行時workflow/toolchainの照合を保存する。
取り込み時は固定HEADのGitHub APIから直接取得し、現在のソースと比較する。
受入検証ではZIP固定SHA、抽出バイト、終了コードの厳密な型、全ケースの完全性、
原本stdout/stderr、現在のROM/runner/plan、元のgate検証器の全条件を再検証する。

```sh
python3 scripts/run_modernization_stage81_github_domain.py prepare
python3 -m unittest tests.test_modernization_stage81_github_domain tests.test_modernization_p08_stage81_evidence -v
python3 scripts/check_modernization_p08_current_acceptance.py --check
```

最初のprepareは明示的な私用入力生成であり、それ以降は読み取り専用。P08文書の新層は
旧Stage77/80/代表試験の全フィールドをハッシュ結合したまま追加される。
旧Stage80の30代表試験は過去候補の履歴であり、Stage81への成功数転用はしない。

`release_ready=false`、Stage62基準、Draft/未マージは維持する。P03全体、繁殖、その他の
習得経路、archive economy、P05全体や自然な特性取得・Mega・Circus入場、P06/P07の
仕様採用と実装、最終受入を完成扱いにしない。

## 統合後CIの確定と実CLI回帰

統合後の通常CI成功は `p08_stage81_integration_verification.json` の `normal_ci_verification` に固定HEADとrun別で記録する。原本ZIPと実コマンドの stdout/stderr/終了コードは `p08_stage81_closeout_evidence/34380153325/` に保持する。

`tests.test_modernization_stage81_acceptance_cli` の10件はmockなしで `--check` の終了0、`--check --require-release-ready` の終了1、引数不正の終了2を区別し、同一スナップショットと290入力のbyte/mtime不変を検証する。通常CIで毎HEAD実行する。受入検証器のPASSを製品のrelease-readyに置き換えず、新規mGBA件数は0と記録する。
