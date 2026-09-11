# PR #16 現在の受入と実装再開点 — 2026-09-11

**製品完成・配布承認ではない。P06の採用範囲は完了。P03/P07の実経路を追加受入し、P05と最終配布を含む残件は明示して保持する。**

## 最初に読む正本

1. `content/modernization/p08_remaining_work.json` — 再生成される現在の残件。各項目の `resume` と `pass_condition` から続行。
2. `content/modernization/pr16_completion_acceptance.json` — 現候補・実行run・旧結果と新結果の区別。
3. 本文の「残る実作業」、次に関係する実装・テスト。
4. `content/modernization/p08_owner_approved_policy.json` — 承認済み仕様を再び承認待ちにしない。

古い `p08_final_candidate_acceptance.json` と引き渡し文書のStage84本文は歴史的記録として不変。現在の候補や残件を古い文章から逆算しない。PR #16、`codex/modernization-followup-20260908` を継続し、節目ごとにcommitする。

## 候補と実行の識別

現候補は Stage84 + V4既存保持層 + 進化時native呼出の修復である。Stage84そのものへの改称はしない。

- SHA-256: `635fd890a8d1071560d3cb56c9c663425f7c988119ce098dedad6bf6554f973e`
- 33,554,432 bytes、CRC32 `5B8BFB51`
- 先行候補試験: run `34512326368`、HEAD `d49c3d721f3eac994a48d190e980dc34346f0942`
- 今回の進化試験: run `34552826501`、HEAD `37ec0121e8170673542adb1e1213d51954bad576`
- 今回の繁殖試験: run `34553503441`、HEAD `64bf90f83cb928b989fea45ff52696f0d3f775e9`

先行runはこのセッションで原本を再検査したもので、新たに実行した件数へ足さない。今回追加した実ROM受入は **進化2 + 繁殖5 = 7プロセス・19コア**。今回の変更は試験・検証・現在ビューであり、候補ROMの機能修復そのものは上記先行HEADまでに実装済みだった。

### P06: 採用2種3項目の工程受入を閉じる

対象はジバクンの通常特性2枠とカモナイツの攻撃75→45のみ。先行runの既存/新規個体8件・24コア、通常再計算・Save・別コアContinue、戦闘/表示9件、Stage82攻撃対照1件を再検証した。

のろわれボディの発動と枠違い対照、おみとおしの道具あり/なし/枠違い対照、攻撃変更に伴う計算値・ダメージ差、通常Summaryの特性名・説明・攻撃表示を確認。3枚のSummary原本ピクセルも確認済み。原本ZIP内の `acceptance/p06/phase`、`acceptance/p06/slots` と新受入JSONの `p06` を参照する。

**自然捕獲の証拠ではない**。親候補対照1件を現候補上の件数に足さない。レビュー194行の全調整、未採用の再調整は不要。古いJSONの `full_p06_acceptance=false` は、その時点の記録としてそのまま残す。

### P03: 進化の満杯・取消を新規受入

`scripts/pr16_evolution_fullslots.py` は固定された従来コントローラからケースと観測対象のみを拡張。進化固有のYes/No taskを読取で識別し、通常レベルアップのParty画面と混同しない。

ルカリオ進化後、満杯で第2技へ入れ替える経路と、技選択画面からBで戻り習得中止を確認する経路を実行。技4枠・PP・PP Up・進化先・100byte個体一致、通常Save、別コアContinueを検証した。取消で進化自体を取り消した成功とは扱わない。先行の進化空き枠成功は別runのまま保持。

### P07/P03: ピチューの復元タマゴ技を実繁殖で受入

`scripts/pr16_breeding_delta.py` はV4 `egg_moves_final.csv` 273行、Pichu24 / egg440（たいでん）の **CURRENT_PRESERVED** を根拠とする。通常卵技7件に440を加える差分で、共有タマゴ技や新規採用へ読み替えない。PP40は固定候補と親ROMの物理技テーブルから独立取得。

父のみ、母のみ、両親からの重複防止、でんきだま併用で満杯となる順序、対象技なしの対照を5件実行。事前fixtureの後、通常預入→歩行でタマゴ生成→屋外NPC受取→タマゴ通常Save/別コアContinue→歩行・通常孵化/ニックネーム取消→孵化後Save/第3コアContinueを通した。親・queue・子の保存一致とhost-write API7種の拒否を維持する。

これは親個体の自然捕獲や全ての繁殖組合せの証拠ではない。元のStage82繁殖8件を別候補の5件へ改称しない。

### P07の資料照合は判断待ちではない

現候補に、ベガ種→通常技の歴史的採用追加1,073行（level450/egg254/machine179/tutor190）、通常種→ベガ技の歴史的保持499行（level310/egg189）の実在を確認。

499行は **既知472行 + 名前付き技キーの旧表27行**。27行はSOUL_BITE/DARK_SNIPEの別名キー照合で回収された既存保持であり、新規の広範配布を採用したものではない。472行を撤回・再承認待ちに戻さない。元の1,073行を二重適用しない。

`content/modernization/p07_preserved_layer_spec.json`、`scripts/pr16_p07_preserved_layer.py` が仕様・照合の入口。先行runの技メモリー10件、レベル習得3件と今回の繁殖5件を保持し、未受入の差分経路だけを詰める。

## 残る実作業

### P03 / P07: フォームサービス、他の該当する供給経路

進化の空き/満杯/取消、従来の繁殖・思い出し・技忘れ、今回のPichu実繁殖は閉じた範囲。フォームサービスの実操作と、他の採用差分の物理経路対応は未完了。

フォームの具体的入口は `overlays/collection_supply_v1/collection_supply_v1.c` の `CollectionSupply_FieldHost` / `Task_CollectionMenu`、続いて `overlays/modernization_p03_stage73_consumer_runtime` の `Stage73_CollectionApplySelectedForm`。実サービスメニュー→個体選択→Rotom系の署名技変更/解除→通常保存・別コアContinueを確認する。現実装の満杯時の非破壊拒否、取消、解除時の技/PP/PP Upの詰め方を確認し、根拠なく自動上書き仕様を増やさない。

Happinyの新保持技3件は技メモリー上では先頭/中間/末尾/取消を受入済み。一方、baby/incenseを伴う実繁殖との差分対応は未受入。`pr16_breeding_delta.py` はPichu専用であり、Happinyまで合格した扱いにしない。必要な親・道具・物理孵化条件を固定ROM/元表から特定し、独立した期待値で拡張する。

### P05: 通常取得から戦闘、実際のCircus受付

`NATURAL_CAPTURE_GEAR`: `run_modernization_p05_controller_witness.py` / `run_modernization_p05_scheduler_e2e.py` の戦闘側は既存合格。通常捕獲・道具取得からつながる証拠ではないため、自然取得後にfixtureで差し替えず戦闘まで通す。

`PHYSICAL_CIRCUS_ADMISSION`: 実施設の受付・入場から特性抑制へ到達する試験が残る。Circusフラグの直接設定やdirect-callを実入場へ読み替えない。CFRUの限られた27ファイルのsource hit確認だけでは、受付がリポジトリ全体に存在しないとは言えない。実map/event経路を特定してから試験する。

### P08: 同一最終候補とclean ROMからの配布

現候補上の7領域回帰は `PASS_WITH_DECLARED_LIMITS`。上記P03/P07/P05を閉じ、変更があれば影響する試験だけを新しい正確な候補に結び直す。

clean ROM起点の全工程ソース再生成2回、clean-to-final配布パッチ、安全な導入/戻し方を含む製品パッケージは未完了。Stage80起点の再生成や既存BPSの適用一致だけをclean全工程ソース再生成と呼ばない。工程用のP07候補→進化修復候補の正逆BPSは先行原本に存在するが、cleanやStage62へ適用できる配布パッチではない。

## 実行・再検査

原本はGit追跡する `content/modernization/pr16_completion_evidence/<run>/original.zip` と `actions.json`。各ZIPのSHAは新受入JSONにある。原本保存commitは `b1215b03f03477ca24fe7fcb3efe0474467e5b64`。新規ZIPにROM/saveを含めない。

```sh
# 既に追跡済みの3 ZIPと実行HEAD・native出力・候補・画像・ガードを再検証。新しいエミュレータ実行ではない。
python3 scripts/pr16_completion_checkpoint.py

# 現在ビューを両既存生成経路で再検証（旧原本9件がcheckoutに無ければ先に復旧）。
python3 scripts/restore_modernization_final_originals.py
python3 scripts/pr16_refresh_current_view.py
python3 scripts/record_modernization_final_acceptance.py
python3 scripts/record_modernization_p03_forgetting.py
```

新しい実ROM試験は `.github/workflows/pr16-evolution-fullslots.yml` と `.github/workflows/pr16-breeding-delta.yml` が再現例。いずれも固定Stage84生成→固定V4回収→保持層→進化修復層→否定unit→新規mGBAプロセス→原出力保存を行う。`--fetch` はGitHub原本の再取得であり、新規native試験の起動ではない。

## 維持する承認と禁止操作

追加技アーカイブは **殿堂入り後・Bagのわざメモリーから無料**を正式採用済み。通常思い出し・技忘れに新しい殿堂入り制限を足さない。

**publicは所有者の正しい設定**。非公開化や追跡原本の削除を承認待ち・製品完成条件に戻さない。過去の全index guard失敗をPASSと改称せず、新規の秘密・意図しないROM/saveの混入を防ぐ。

Stage62、実プレイsave、active_play_baseline、元ROM、過去原本、Git履歴、公開範囲を変更しない。PRを勝手にmergeしない。既存成功を失敗/未実施へ戻さず、証拠整理だけで製品完成と報告しない。
