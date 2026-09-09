# P08：代表的な実操作試験の追補

Stage79の7領域証跡とStage77の履歴は変更しない。その上に
`current_representative_e2e` を追加し、P03/P05で後から成功した実操作試験を
現在の受入表示へ接続する。これは工程全体の完了認定ではない。

## 保存する原本

| 組 | 原本Actions run | 原本の新規プロセス数 | 検証範囲 |
| --- | --- | ---: | --- |
| P03 learning | 34347153852 | 2 | 通常のバッグ・手持ち操作、進化キャンセル、習得境界、通常保存、新規coreでのContinue |
| P05 scheduler | 34351006779 | 24 | 既採用6特性の発動・非保有・Circus抑制と撃破境界の実ターン進行。別にhost書込み拒否7条件 |
| P05 controller | 34354997505 | 4 | Dragonize有無と相手Ghost/Normalの組合せ。行動選択、技選択、PP消費、次ターン復帰の受動観測 |

3組とも同じStage80候補ROM
`6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3` を用いた。
原本中の新規実行は合計30件、各原本のキャッシュ再利用は0件。
この追補処理と通常CIは原本の再検証であり、新規mGBA実行は0件である。
試験範囲には重なりがあり、30件を30種類の独立した製品要件の受入とは数えない。

`content/modernization/p08_representative_evidence/<suite>/<run>/` へ、原本ZIPを
そのまま保存し、全メンバーの展開コピーとActions照合結果も保存する。
既存のP03 learning/P05 scheduler記録、Stage79の原本は上書きしない。

## 検証の入口

```sh
python3 -m unittest tests.test_modernization_p08_representative_evidence -v
python3 scripts/check_modernization_p08_current_acceptance.py --check
```

検証器はZIP固定SHA、結果固定SHA、重複のない完全なファイル集合、原本と
展開コピーの一致、実行時のROM・seed・runner・依存ソース、workflow・toolchain、
Actionsのrun/HEAD/job/必須step/artifactを照合する。実行時のworkflow・toolchain
ソースは、統合時に原本HEADを指定してGitHub REST APIから取得・照合する。
通常CIでは期限付きartifactへ依存せず、コミット済み原本を検証する。

ケース別のstdoutは元の契約検証器へ再入力する。終了コードは整数0に限定し、
JSONのfalseを0として受け入れない。controller原本に含まれるprocess記録も照合し、
非zero終了・timeout・起動エラー・違う実行コマンドを拒否する。コンパイル成功や
stdoutのPASSだけでは成功にしない。合成データの回帰検証はmGBA実行に数えない。

## 過去と現在の区別

`declared_runtime_limits` はStage79原本のfalseを保存する。
`declared_runtime_limits_scope` がその意味を明示し、後続の代表成功は
`representative_e2e` に表示する。したがって古いfalseは「代表試験も一度も
実行していない」という意味ではない。現行の残件理由は、成功済み代表ケースと
未検証経路を分けて記述する。

P03の技枠満杯時の入替・拒否、他の習得画面、繁殖・タマゴ、各経路の保存再読込と
archive economy確定は残る。P05の全技・特性経路、自然な特性取得やMega経路、
自然なBattle Circus入場、通信等を今回の代表ケースへ含めない。
P06/P07の未採用仕様も採用しない。

`full_p03_acceptance=false`、`full_p05_acceptance=false`、`release_ready=false` を維持する。
Stage62のプレイ基準は変更せず、PRのDraft解除やマージもしない。
`--require-release-ready` は証跡が整合していても、残件がある限り終了コード1で止まる。
