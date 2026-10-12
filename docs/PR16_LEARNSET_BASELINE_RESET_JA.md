# Issue #19 技習得基準復元

固定入口は `CHATGPT_RESUME.md`。この工程は既存の候補ROM・Issue #18 Wiki・native受入原本を変更しない。

## 実装中の区切り

`tools/pr16_learnset_baseline.py` とCLIで、指定ZIPの公式採用1299件を隔離生成する。外側ZIPとmemberのSHA-256/size、canonical key/ID/form、参考JSONLと5 CSV（全経路+4 partition）の全内容を照合する。原本の経路・条件・順序を保持し、原本TM/TR番号を現在のruntime slotと取り違えない。

出力は専用 `.local/` 配下。`official_baseline.jsonl` とper-species index、空の `owner_approved_overlay`、別管理の旧P07全1572行、未取込Vega181種、例外候補台帳を生成する。ZIP内の「Vega保存指示」はVega元来の習得表ではない。

既存P01のキャタピーID649追加訂正は履歴として保持し、Issue19へ黙って転用しない。

## 所有者決定: サイドチェンジは実装しない

原本にある技ID1063 / Side Change / サイドチェンジ相当の159経路・103種について、所有者は本プロジェクトでの技実装・採用を不要と決定した。

- battle effect、battle script、animation、AI、Z/Max変換、TM/TR/Tutor、タマゴ・共有タマゴ等の新規実装を行わない。
- 原本159経路・103種は出典証拠と比較履歴から削除せず、`OWNER_DECLINED_NO_ENGINE_IMPLEMENTATION` 相当の明示dispositionで保持する。
- active learnsetでは、まずサイドチェンジ経路を除外する。除外だけで表構造・level-up順序・runtime consumerが正常に成立する場合、別技を補充しない。
- とくにlevel-up行の欠落が表構造や生成器を不必要に複雑化する場合だけ、現在実装済みの目立つ伝説専用技を一時placeholderとして同じlevel/order位置へ置いてよい。第一候補は「ときのほうこう」。実装時に現行Move manifestからstable keyと数値IDを解決し、推測したkey/IDをハードコードしない。
- placeholder行には `TEMP_OWNER_PLACEHOLDER_FOR_ALLYSWITCH` 相当の由来を必須とし、元のSpecies/Form、route、level/order、条件、原本route ID、元技Side Changeをcrosswalkへ保存する。
- このplaceholderは最終バランス決定でも `owner_approved_overlay` でもない。後続のバランス確認でベガ技または別の適切な技へ置換、あるいは削除するための仮置きである。
- level-up以外のTM/TR/Tutor/egg/shared-egg等へplaceholderを自動展開しない。除外不能な構造上の理由がある経路だけ個別台帳化し、Wikiで仮置きと明示する。
- validatorは、active側のSide Change経路0、Side Change実装追加0、全placeholderのcrosswalk欠落0、未表示placeholder 0を検査する。後継Wikiは仮技を通常の確定習得技と同列に見せず、要後続置換として集計する。
- Side Changeそのもののnative受入は不要。placeholderを使用した場合は、該当level-up表が壊れていないことと仮置き台帳との一致だけを変更影響に応じて確認する。

この決定により、Side Changeは `EXPLICIT_ENGINE_ADJUDICATION_REQUIRED` の未決事項ではない。ほかの未知move・runtime制約・原本衝突は引き続き個別に停止・台帳化する。

## 再現

```bash
python3 -B -m unittest tests.test_pr16_learnset_baseline -v
python3 -B scripts/pr16_learnset_baseline.py prepare --zip <固定ZIP> --output .local/pr16-learnset-baseline/new-build
python3 -B scripts/pr16_learnset_baseline.py check --output .local/pr16-learnset-baseline/new-build
```

`prepare` は既存出力を上書きしない。`check` は読み取り専用であり、入力/生成器/出力hashの不一致を修復しない。全ゲーム受入の再実行は含まない。

## 継続が必要な範囲

Vega元来181種の凍結ROM由来またはatwiki一次表とdexNo/SpeciesID/keyの結合、方法別の原本照合、Side Change以外の明示例外の判断、runtime全consumer切替、旧候補との差分台帳、後継ROM/Wiki、変更影響に限ったnative受入は未完。基準復元全体・P08 releaseを完了扱いしない。


## Issue19公式原本隔離の完了checkpoint

公式1299件/118524経路・39境界試験・独立2生成/純読取checkをrun `35605822056` で検証し、全stepとartifactを完了照合済み。正本は `content/modernization/pr16_learnset_baseline_checkpoint.json`。Vega元来181種/Side Change以外の例外/runtime切替/後継ROM・Wiki/nativeは未完。旧候補と受入済み原本は不変。
