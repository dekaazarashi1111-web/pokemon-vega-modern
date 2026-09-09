# P05 6特性の実ターン進行・対照・抑制試験

Stage80固定候補 `6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3` を変更せず、8シナリオ×3条件＝24個の新規mGBA processで試験する。過去Stage79 PASS cacheは使用しない。

```sh
python3 -m unittest tests.test_modernization_p05_scheduler_e2e -v
python3 scripts/run_modernization_p05_scheduler_e2e.py
```

## 初期条件と実操作の境界

固定QA seedの私有コピーを通常Continueで起動し、既存のnative wild battle入口から戦闘を構築する。最初の行動選択より前に、特性・技・能力・HP・タイプ・Battle Circusフラグを明示的なテストfixtureとして用意する。特性の自然入手や実際の施設入場を試験したとは扱わない。

fixture確定後は7種類のmCoreメモリ/CPUレジスタ書込APIを失敗終了するガードに交換する。観測処理はAキー・runFrame・受動的読取だけであり、技効果の関数直接呼出し、callback/PC/カーソルの強制、snapshot復元は行わない。7 APIの拒否は独立した負例processで実際に確認する。

技のPP消費、相手の行動、ターン末処理から次の行動mainへ戻る境界を観測する。Solar Beamの溜め中は次のChooseAction命令が来ないため、その命令を待たず、次のフレームを実行する前のmain境界で停止する。最後の相手を倒すケースだけはnative勝利outcomeまで観測する。

## 24条件

各行を「特性なし」「特性有効」「同じ特性＋Battle Circus抑制」の3条件で実行する。

| シナリオ | 有効時 | 特性なし・抑制時 |
|---|---|---|
| Dragonize | Normal技がGhostへ命中する | 無効でHP不変 |
| Eelevate・地面 | Earthquakeを無効化 | 被ダメージあり |
| Fire Mane | Emberのダメージが対照より増える | 通常ダメージ。抑制結果も通常側と一致 |
| Mega Sol | Solar Beamが1ターン目にダメージを与える | 1ターン目は溜め、相手HP不変 |
| Piercing Drill | Protect中でも接触技ダメージが発生する | Protectが防ぐ |
| Spicy Spray | 被ダメージ後に攻撃者がやけどし、ターン末ダメージを受ける | やけど・残留ダメージなし |
| Eelevate・最後の1体を撃破 | 能力は上昇しない | 同じく上昇しない |
| Eelevate・別の相手が残る撃破 | ダブルの対象撃破後、最大raw能力の攻撃が1段階上がる | 攻撃段階は変化しない |

ダブルでは4体をnative戦闘生成し、残る相手と味方のPP消費も確認する。最後の1体では上昇しない期待値は、既存Stage72の`ViableMonCount(owner ^ 1)`契約に従う。対照で違いがなければPASSにしない。

## 証跡の扱い

C出力は`OBSERVED`であり、それだけではPASSではない。Pythonが終了コード、厳密なJSON型・キー、個別効果、24条件の完全性、Fire Maneの対照差を検証した後だけ集約`result.json`を原子的に作成する。

再実行開始時に旧結果と対象ログを削除する。タイムアウトでも部分stdout/stderrをバイト列で保存し、原本ROM・私有ROM・seed・source・Stage62基準のハッシュ検査を省略しない。異常終了後のPASS風JSON、重複キー、条件欠落、二重実行したSolar Beamを拒否する。

## 範囲外

これは6特性の代表的な実ターン経路の追加受入であり、P05の全技・全特性・全hook・全AI・全交代経路の受入ではない。Dragonizeの倍率全域、Mega Solの全晴れ効果、Piercing Drillの全威力境界もこの追加試験だけでは網羅しない。自然入手、Mega進化からの特性獲得、実施設への入場、通信対戦も未検証である。

`representative_scheduler_e2e=true`はこの限定scopeだけに使い、`full_p05_acceptance=false`、`release_ready=false`を維持する。過去Stage79/P08原本を上書きせず、P03繁殖・他の習得UI・P06/P07採用仕様を完了扱いにしない。
