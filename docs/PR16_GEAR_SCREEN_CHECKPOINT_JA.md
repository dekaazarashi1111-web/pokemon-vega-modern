# PR16 道具経路・画面原本の統合チェックポイント

## この更新で実際に行ったこと

前の会話で未反映だった原本保護と画面照合helperを、既存の `pr16_purchased_gear` に統合した。別の購入controllerや別の移動経路は作っていない。コメントだけでなくコード・テスト・runner・workflowを同じPRブランチへ反映している。

- `82601dbfc59cb3a27cb425211e1e74eeb65e6bb4`: 原本を再利用・削除しない出力準備、画面原本の照合helper。
- `5ac35109d22688ba3c809b3617c39a573705c60a`: helperの14件の不正入力・原本保護テスト。
- `b310faa4d30aff3ca8579a6be731b0579b039896`: 既存runnerへ統合。中間コミットではCIを重複起動しない。
- `4b5971179795bcdbbca1abf142387ef1bb6f1ce9`: 既存workflowへ統合して実行。

## 新規の実行と原本

- run: `34589284710` / artifact: `10194976718` / name: `pr16-purchased-gear`
- 実行HEAD: `4b5971179795bcdbbca1abf142387ef1bb6f1ce9`
- ZIP: 580351 bytes / SHA-256 `6eba3f6c0947af2e2cb446552cc37ccf832665a8ac849a80e2f45bca986e6de9`
- 対象unit test: 65件成功。
- 実ROM: 4プロセス・9コア成功。切替あり、切替なし、切替取消は各2コア。装備後のcold Continueで標準policyへ戻る対照は3コア。
- シビルドナイトを実受付で購入し、Bagで持たせ、通常歩行から自然遭遇、戦闘、復帰、通常保存、別コアContinueへ接続。各ケースでPP10→9、BP64→48、装備・在庫・保存番号等の保持を確認。
- 通常の切替ありケースだけがメガ種族1634・特性313へ変化する。他の3ケースは通常種族411・特性26を保持。

先行run `34587080329` は別の原本。この4プロセスへ旧runを足さず、別の8経路を受入したとも扱わない。今回の再実行理由は、既存controllerへの原本保護・必須画面照合の統合検証である。

## 画面とソースの照合

取得したZIPをCRC・SHA-256照合し、37入力ソース、生成された実コンパイルcontroller、4ケースのstdout/stderr/processと集約結果を照合した。必須53画面（13+13+13+14）をhelperで照合し、追加5画面も含む58画面を4枚の一覧で目視確認した。確認した静止画には明らかなUI破損を認めなかった。

全58原本の名前・サイズ・SHA-256をstable JSONにしたSHA-256:
`d594115c87f2ec3c7a05692a769cb36f3ef586d5e8f7ac065cef7f6328947934`

これは全アニメーションの品質保証ではない。`mega-active` は種族変更検出直後の画面で、sprite更新前。後の `native-turn` で変更後の姿を確認している。実行中の `.screens.json` はあくまで機械照合記録で `presentation_accepted=false` を維持する。目視確認結果は後付けの受入JSON内の `visual_review` に別記する。

## 原本の正本パスと再検査

`content/modernization/pr16_gear_evidence/34589284710/original.zip`

`content/modernization/pr16_gear_evidence/34589284710/actions.json`

`content/modernization/pr16_gear_screen_acceptance.json`

原本の保存jobは `.github/workflows/pr16-gear-screen-retain.yml`。Actionsから実物を取得し、実行HEAD・job/stepの終了状態・artifact digestを検査してから同一ブランチへ非force pushする。既存原本と異なる内容での上書きを拒否する。保存jobは新規エミュレータ実行ではない。

```sh
python3 scripts/pr16_gear_screen_checkpoint.py
python3 -m unittest tests.test_pr16_gear_screen_checkpoint -v
```

上記は保存原本を再検証する。ROM生成やエミュレータを起動しない。source identityが後で変わった場合は、その変更を照合して記録を接続すること。原本を変更したり過去の成功を未実施へ戻したりしない。

## 続ける範囲と禁止する読み替え

開始地点、Lv100の先頭個体、リング、64BP、次戦闘用policyはfixtureである。リング/BP自体やpolicy選択の通常供給、全6種の道具経路、実際のCircus受付・入場は、この成功だけでは受入しない。cold Continue後にpolicyを外部から再注入していない。

`full_p05_acceptance=false`、`release_ready=false`。P03/P07の残る取得経路整理、Circus実受付、同一候補への最終統合、clean ROMからの独立2回生成と配布は継続対象。既存のP06・P07採用1073/保持499・進化/繁殖/フォーム/共有技・自然捕獲/実戦の成功を取り消さない。

候補ROMは変更なし: SHA-256 `e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267` / 33554432 bytes / CRC32 `BFB089F9`。

前の会話ZIP内の `.chatgpt/patches/pr16-purchased-gear-evidence.patch` は再適用しない。helperとrunner/workflowへの統合は上記コミットに入っている。別の購入controller、重複する経路調査、配布表の再回収は不要。public維持・殿堂入り後のBagわざメモリー無料利用は承認済みのまま。Stage62・実プレイsave・公開範囲・既存履歴を変更せず、PRは未マージで継続する。
