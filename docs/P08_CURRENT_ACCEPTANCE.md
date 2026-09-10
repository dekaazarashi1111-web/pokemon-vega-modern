# P08 現在の受入残件

## 正本と対象範囲

現在の残件は `content/modernization/p08_current_acceptance.json` の
`current_blockers` を参照する。これは登録済みStage79原本証跡、現在の候補ROM・runner、
P06/P07の採用契約から生成する読み取り専用監査のスナップショットである。

P08の既存3文書はStage77の工程完了checkpointを保持する。
`release_blockers` の古い文字列を削除したり、現在の未解決項目としてそのまま再利用したりしない。
新しいスナップショットでは `historical_stage77` に過去の一覧を分離し、元文書と
`current_cumulative_runtime` のハッシュ結合を再検証する。

## 検証と更新

```sh
python3 scripts/run_modernization_stage81_github_domain.py prepare
python3 -m unittest tests.test_modernization_p08_current_acceptance tests.test_modernization_p08_stage79_evidence -v
python3 scripts/check_modernization_p08_current_acceptance.py --check
```

`--check` はファイルを書き換えない。現在の入力から再計算した内容と記録済みスナップショットの
完全一致を要求する。新しい正当な証跡・採用仕様を導入した際は、その受入方針を検証器にも
明示的に反映した後、次でスナップショットを更新する。

```sh
python3 scripts/check_modernization_p08_current_acceptance.py --write
```

リリース可否を要求する呼出しは別である。

```sh
python3 scripts/check_modernization_p08_current_acceptance.py --check --require-release-ready
```

終了コードは、整合性成功が `0`、整合性成功でもリリース条件未達が `1`、
証跡欠落・不一致・未対応の受入変更など検証エラーが `2`。
`validation_status=PASS` はリリース承認ではない。現在は
`acceptance_status=BLOCKED`、`release_ready=false` を維持する。

## 現時点の境界

Stage80候補の同一ROM・同一ハーネスに対する7領域成功は登録済み原本から確認する。
P02、Mega店、Floette、P03代表経路、P04 Mega runtime、battle policy、P05限定経路の
成功を取り消さない。Eelevate switch AIも現在の結果JSONでは完了している。
この監査はmGBAを新規実行しない。

P03の実操作・預かり屋／タマゴ・保存再読込の通し検証とarchive economy確定、
P05の戦闘ターン進行を通した検証、P06/P07の採用仕様と実装・受入、最終リリース判断は残る。
P06の194件のレビュー資料を採用指示とみなさず、P07の双方向の技配布を創作しない。
採用内容が変わった場合も、件数の変更だけで受入完了へ自動昇格しない。

通信・全メニュー経路は未主張範囲として別欄に保持する。これらを追加の合格条件として
勝手に確定するものではない。PRのマージ、Draft解除、Stage62プレイ基準の変更も行わない。

## GitHub上の記録

通常CIは既存の53テストを維持し、現在受入31件と既存原本証跡20件の計51件を追加で検証する。
結果JSON・テストログ・検証checkout SHAを `p08-current-acceptance` artifactへ保存する。

`p08-current-acceptance-record` workflowは検証成功後だけ、標準run/versionログへの追記と
検証記録を一時ブランチへコミットする。PRブランチを自動更新せず、記録コミットを読み直して
fast-forwardで反映する。記録後HEADでも通常CIと正式Stage79を確認する。

## 2026-09-09：後続の代表的な実操作試験

`representative_e2e` にP03 learning（2ケース）、P05 scheduler（24条件）、
P05 controller witness（4条件）の原本照合を追加した。
`declared_runtime_limits` は変更していないStage79原本のフラグであり、後続の
代表成功を取り消すものではない。現在の残件理由は、代表試験で確認済みの範囲と
未検証の経路を区別する。詳細と検証手順は `docs/P08_REPRESENTATIVE_E2E.md` を参照。
原本に含まれる新規プロセス30件と、今回の証跡再検証における新規実行0件を混同しない。

## Stage81：native PP修正候補の受入

現在候補は `current_native_pp_acceptance` のStage81を優先する。
旧 `current_cumulative_runtime`（Stage80）と `current_representative_e2e`（同候補の30件）は
元のハッシュ結合のまま保存し、Stage81の新規実行件数へ足さない。
P08の現行スナップショットは両層を検証したうえでStage81の結果を採用する。

新しい原本はrun `34368455589` のplan・7領域・merge、および
run `34364100108` のP03満杯技枠等8ケースと修正前の失敗対照2ケース。
新候補の成功原本は合計15件、失敗対照は別枠2件。原本の取り込み・再検証自体は
mGBA新規実行0件である。詳細は `docs/P08_STAGE81_NATIVE_PP.md`。

`prepare` だけが `.local/stage81-native-pp/` に決定的な検証入力を作る。
その後の `--check` とP08の証跡検証は読み取り専用で、既存ROM・Stage62基準・
Stage80 gateを書き換えない。通常CIもこの順序で実行する。
P03の満杯4枠入替・拒否・キャンセル・空き枠・対照と通常保存/Continueの代表8ケースは
解消済みと区別するが、繁殖・他の習得経路・archive economyは未完了のまま。
P05全体、P06/P07の採用仕様、最終受入・リリースも自動で完了にしない。

## Stage82：通常操作による繁殖・孵化の後続証跡

旧スナップショットのbreeding_e2e=falseは旧runnerの範囲であり、後続の成功を未実施へ戻さない。Stage82の25習得画面と7領域はp08_stage82_archive_acceptance.json、今回の8条件はcontent/modernization/p08_p03_breeding_acceptance.jsonを参照する。通常の預入・歩行生成・受取・孵化、および孵化前後の保存／別core Continueを検証する。親の初期作成はfixtureであり、全種・全組合せ・満杯時等の受入は未完了。詳細はdocs/P03_BREEDING_E2E.md。

```sh
python3 scripts/record_modernization_p03_breeding.py
```

上記は読取専用の原本再検証。原本8プロセス／24 coreと統合時の新規実行0件を区別する。
