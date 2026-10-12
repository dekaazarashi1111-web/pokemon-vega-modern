# P05 controller witness — 独立した受動観測・回帰試験

## 検証状態

前回のローカル成果物7ファイルをPR #16へ移すためのcheckpointである。
C runner、observer header、Python runner、2個のtest source、runtime workflowは
前回添付パッチとbyte一致する。検証済みローカル成果物のunit test 67件は今回も再実行してPASSした。
GitHub Actionsでの固定toolchain実行結果は、必ず本checkpoint以降のrunと原本ログで確認する。
ローカルの成功や、書き込み成功をGitHub runtimeの成功として扱わない。

初期入力はworkbench `30014ebb143e014dde324b35bacf496715ab5c9b`。
その後の `14a61c80b69d2adb2f9f9adf513fd143d86b8728` の6特性24条件試験とは
名前と対象ファイルを分離しており、既存のp05-scheduler-e2e、共有helper、通常CIを変更しない。
今回の取込baseは `9ee5a7200944cd3ed8b17ff896574eb1cf5c1825`。

## 観測する範囲

固定Stage80候補の自然なnew-game入力traceからfieldを作り、製品のwild battle
setupを実行する。最初の行動選択前にBattleMonの特性・タイプ・能力・HPなどを
明示的なテストfixtureとして設定する。自然入手、種族への特性割当、メガ進化、保存経路は対象外。
準備後はROM関数呼出し、RAM書換え、snapshot復元、engine stubを使わず、
A入力・フレーム進行・受動的な読取だけで1ターンを観測する。

双方species=1、使用者Tackle=33/PP35、相手Splash=150/PP40、開始HPは双方1000。
使用者タイプWater、特性Dragonize=312または0とし、相手Ghost/Normalの4条件を試験する。
行動選択→技選択→選択技33→双方の1 PP消費→選択技に帰属するダメージまたは
無効→次ターン復帰の順序をC observerとPythonの両方で検証する。

## 失敗をPASSにしない条件

警告、別の戦闘経路、種族/技/特性/タイプの変化、PP復元・複数ターン消費、瀕死、回復、
Splashによる使用者ダメージ、イベント欠落、タイムアウトを拒否する。
PASS JSONでも非ゼロ終了・SIGTERMは失敗。重複JSON key、型違い、古いPASSの残存も拒否する。
タイムアウトの途中stdout/stderrは不完全UTF-8を含めバイト列で保存する。
通常戦闘のIS_MASTER=0x4管理bitだけを許容し、LINK/TRAINER/DOUBLE/未知bitと
実行途中のフラグ変更を拒否する。製品ROMを変更していない。

67件は合成traceによるobserver 38件、JSON契約17件、実子process・file保護9件、
ソース境界・workflow 3件。合成traceをmGBA実行に数えない。
前回ローカルでは4ケースの新規mGBA実行がPASSしたが、GCC14.2/Python3.13と
GitHub指定GCC13.3/Python3.12の差を残しており、正式受入には転用しない。

## 実行

```sh
python3 -m unittest discover -s tests -p 'test_modernization_p05_controller_witness.py' -v
bash infra/setup_github_actions.sh --check
python3 scripts/run_modernization_p05_controller_witness.py
```

`.github/workflows/p05-controller-witness.yml` はpushまたはworkflow_dispatchで実行し、
成否を問わず `.local/p05-controller-witness/` をartifactとして保存する。

## 受入境界

これはDragonizeの代表4条件であり、倍率6/5、全特性、抑制、AI、ダブル、通信、保存の全受入ではない。
`full_p05_acceptance=false` / `release_ready=false` を維持する。
Stage62基準、P03の代表2件、Stage79/P08の過去証跡、P06/P07採用仕様は変更しない。
正式run/head/artifact照合と標準ログ追記を別途記録する。P08の全体完了へ自動昇格しない。
