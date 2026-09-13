> 2026-09-10更新: **現在の残件は `content/modernization/p08_remaining_work.json` を参照。** `p08_current_acceptance.json` はStage81起点の履歴であり、繁殖未完了・P06採用0件などを現在の残件として数えない。技忘れ12件の個別受入は `p08_p03_forgetting_acceptance.json`。工程全体・リリースは未承認。

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

## 2026-09-10 — P03 five-egg FIFO and party/PC capacity acceptance

Original Actions 34439826111, tested source 40dec97d5360422e66d02a3ae0261a00df566f86: fixed toolchain; three new mGBA processes, nine cores, zero cache reuse; all three capacity routes passed. Normal deposit and walking fill the five-egg FIFO; 512 additional steps do not overwrite it. Real dialogue fills the party then uses the first/last PC vacancy, or preserves pending eggs when all 420 PC slots are full. Two normal saves/fresh-core Continues and the repeated full-PC refusal preserve exact party, PC, queue and parent bytes. Seven actual host-write denial probes pass; no ROM calls after the fixture barrier. Original ZIP and Actions metadata: content/modernization/p08_breeding_capacity_evidence/34439826111. This integration performs no additional mGBA run. Parent/PC layout is an isolated fixture. Other P03/P05 routes, P06/P07 adoption and final release remain incomplete. Stage82 product bytes, Stage62 baseline, existing evidence and release_ready=false are unchanged.


## 2026-09-10 — USER-P03-RELEARNER / 固定環境46経路の原本受入

Actions run 34446029812、source HEAD 3c894515d6d73a21fde48228853eef38501933ef、GCC 13.3.0 / mGBA 0.10.2で通常思い出し17件とタマゴ技29件の全46件をPASS。新規46プロセス・92 core、キャッシュ0。全ケースで通常保存、新規coreの通常Continue、個体100byte・技・PP・PP Up・解禁フラグ・ハーブを検証。ホスト書込7 APIの実拒否も確認した。

原本175ファイルのZIP（93814 bytes、SHA-256 ba584a0a5e393a08f1b7a3202945faa4c3e129f91a0d35f2ace6c78f56a960ed）、Actions run/jobs/artifactの取得原本、26入力ソースhashを照合し、56 runtime契約テストと24原本改変テストの計80件をPASS。受入先は content/modernization/p08_p03_relearner_acceptance.json、証跡先は content/modernization/p08_relearner_evidence/34446029812/。検査のみのコマンドが証跡内容・mtimeを変更しないことも確認した。本統合は新規mGBA実行0件。

試験開始前の個体・道具・フラグは隔離fixtureであり自然入手の受入ではない。Stage82 ROMは変更0byte、Stage62基準と実プレイsaveは不変。全P03/P05・最終releaseを昇格しない。並行P06/P07の採用状況はこの試験から判定せず別管理とする。既存全index guardのROM/save・過去path違反は残し、今回の差分indexで同じguardをPASS、全体の違反出力が親と変わらないことを確認してcommit/pushする。

Integration run: 34446703839; integration source: 43a9a22fac95538d17a36cc7ced5ace62c80a81a.


## 2026-09-10 — USER-MODERNIZATION-P03-P05 / 技忘れ12経路とStage84空き技PP修正

Stage83の通常Bag→わざメモリー→技忘れで、末尾MOVE_NONEのPPが35になる不具合を実再現。Stage84はID 0のcanonical PP 35→0の1byteだけを修正した。実技の全行、P06採用2種3項目、保存ABI、Stage62基準は不変。旧Stage83で同じPP残留を検出する対照1件も通した。

実行HEAD 8846cd86de22af35b41eb358b9ed30e4c825750c、Actions 34459625383、GCC 13.3.0 / mGBA 0.10.2で12経路PASS。4枠削除、PP Up警告拒否、最終確認拒否、画面取消、最後の1技拒否、2フォーム制約、秘伝技削除、Keldeoの姿復帰を、通常保存・新規core Continueまで検証。12新規プロセス・24core・キャッシュ0、ホスト書込7 API拒否、保存後100byte個体一致。準備個体・位置・道具はfixtureなので自然入手の受入ではない。

原本78ファイルのZIP、Actions run/jobs/artifact原本、20入力source hashを照合し、content/modernization/p08_p03_forgetting_acceptance.jsonへ接続。新総括はcontent/modernization/p08_remaining_work.json。旧p08_current_acceptance.jsonはStage81起点の履歴として保持し、現在の残件数には使わない。繁殖8件・容量3件・Mega6+36件・思い出し46件を未着手へ戻さず、P06採用2件を反映する。異なる候補の成功を単一最終候補全体の受入とはしない。

P05の現行facility_modes.csvはFactory/Mirageの20モードで、Circus入場モードは同採用表に無い。表外の入口まで不存在とは断定しない。実際の受付・入場から特性抑制までの検証は未完了。P03のその他の進化・フォーム習得・タマゴ供給・economy正式確定、P06工程受入、P07既存資料照合・採用・実装、単一最終候補と配布判定も残る。

本統合は新規mGBA実行0件。PRはDraftのまま、マージ・配布・プレイ基準変更なし。全体guardの既存ROM/save・過去path違反は未解消であり、差分guardと区別する。通常CIの設定は別の権限付き変更として追加する。

Integration run: 34461845380; source: 5783414f58fcfd1c222e26cd3cc1280eea8d0b2e.
