# Issue19 Vega原本の採取・方法別隔離監査

工程ID: `vega-original-capture-method-audit-20260921`。正本は `content/modernization/pr16_vega_original_checkpoint.json`。これは原本観測と比較の完了であり、Vega baselineのruntime採用・Issue19全体完了ではない。

## 完了した範囲

固定Vega ROM `f600fb3faa565bd335ea75114f9233f9a4fe97c12cfed145e0a7b48784d0c9d5`（16,777,216 bytes）とWiki図鑑入口＋181個別ページをrun `35612400716` で一度だけ採取。全181種のdexNo・Species ID・key一致、未知技0。ページの取得時刻・表示更新版・SHA/size、原作tableのoffset/順序を保持。

直接原本はlevel-up 3044、TM/HM 3549、Tutor 1540、egg 1790、計9923行。TM/HM 58slot/stride8とTutor15slot/stride2は全種照合・予約bit・境界・別stride対照を記録。別表記くらいつく/ねらいうちと同名ID1/511は既存configの固定crosswalkで解決し、IDの追加や置換はしていない。

`vega_original_baseline.jsonl` は凍結ROM観測であり全件HELD。`wiki_methods.jsonl` はWiki原文由来の別layer。進化前等経由の92種2394行は `wiki_nondirect_egg.json` に隔離。直接eggが存在する68種はWikiと一致するが、進化前経由を当該種の直接習得へ複製しない。

## 所有者決定: 固定原作Vega ROMを優先する

固定ROMとatwikiの個別ページが食い違う場合、Issue19のVega原作習得baselineでは**固定原作Vega ROMの観測行を採用する**。atwikiは独立照合・差分記録として保持するが、単純な不一致だけを理由に採用を停止しない。機械可読正本は `content/modernization/pr16_vega_original_source_decision.json`。

現在の3群5行は次のとおり確定する。

- リーテイル: Lv32は固定ROMの「リーフブレード」、Lv46は固定ROMの「こうごうせい」を採用する。atwikiの「はかいこうせん」「じこさいせい」は差分履歴として保持する。
- ゴートン: 「かみつく」は固定ROMのLv18を採用する。atwikiのLv20は差分履歴として保持する。
- ディザソル: 固定ROMに存在するTutor「ギガスパーク」「バグノイズ」を採用する。atwikiに記載がないことを理由に削除しない。

`source_conflicts.json` は採取時点の不一致原本として改作しない。後継adjudication/crosswalkから上記decisionを参照して採用結果を記録する。固定ROMの同定、table offset、stride、終端、move crosswalk、抽出器の完全性に疑義が生じた場合だけfail-closedで停止する。この判断は新規バランス追加ではなく出典優先順位の確定であり、`owner_approved_overlay` は増やさない。

## 次の未完作業

まず、3群5行へ固定ROM優先決定を適用したadjudication/crosswalkを生成する。これは採用方針の実装であり、再調査や再採取ではない。

次に92種2394行の非直接eggを原作Vegaの進化/孵化consumerと照合する。進化前、同系統共有、参考表示、直接eggを区別し、進化前経由を当該種の直接習得へ複製しない。新規採取が必要な場合も欠落している原作進化/孵化範囲だけに限定し、182ページ全体や公式原本を取り直さない。

Side Changeは所有者決定どおり非採用。効果・AI・教え技等を追加しない。削除だけで成立するなら代替不要。今回owner overlay追加0、既存Move ID/効果/歴史は不変。

## 検証と再開

検証run `35614274855`、HEAD `9e53b256aeab708f20143509afabe09503094f43` の43試験と独立2生成（hash seed11/29）、実CLI純読取checkでbyte/mtime不変、ローカル期待値一致を完了原本から記録。記録器10境界試験も実施。`content/modernization/pr16_vega_original_evidence` の16証拠とcheckpoint proof_bindingsを参照。採取/検証のActions artifactは30日保存であり、expiryを過ぎて元HTMLが必要なら既存artifact/保存元の有無を先に確認する。trackedのtyped原本・台帳・hashは失わない。

公式1299件/118524経路、旧候補ROM、受入済みnative、旧Wikiは不変。新native/ARM build/ROM変更0、merge/release/active baseline変更なし。受入済み範囲の入力hash不変なら再検証しない。
