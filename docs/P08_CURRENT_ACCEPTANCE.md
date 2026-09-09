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
