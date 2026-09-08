# Modernization引継ぎ

最終更新: 2026-09-08

この文書は`USER-MODERNIZATION-P01`からP08までの累積候補、検証済み境界、未実装境界を示す入口である。機械可読の候補identityは`config/modernization_candidate.json`、入力原本は`config/modernization_inputs.json`、現行プレイ基準は`config/active_play_baseline.json`を正とする。

## 現在位置

- 現行プレイ基準はStage62のまま。開発中の最大StageをiPad、通常save、Codex対戦へ自動採用しない。
- P01はDONE。Stage63はEgg 412／Caterpie 649の意味逆転をstable keyで修復し、ROM SHA-256は`6642602d33e1e074c20afebfc649846f0aaf106c2455f2ca212a4f427ec74fbd`。
- P02はStage64 checkpoint。Rayquazaの進化parameterをItem 773誤参照からMove 630へ2 bytesだけ修正した。ROM SHA-256は`ddb9bf76d7f35c375d44941cd276f07e64501ed5cee34b8d448e76f0454095c3`。全条件種別、キャンセル、道具消費、save/reloadを含むP02受入は未完了。
- P03はStage65代表縦切りを継承し、Stage66 bulk checkpointまで進んだ。Stage66 ROM SHA-256は`0d92f5377b4ad1a2fa5cbf905f81b5b6162e16cdd09a12c65c4a342e73c5c97e`、CRC32は`808D5140`。checkpoint commitは`90a1811964a19e3c058448af173007678b42a7e3`。
- P04〜P08は設計・入力・容量・統合checkpointであり、ROM反映完了ではない。P01以外をDONEまたはrelease readyと扱わない。

## P03 Stage66の採用境界

提出された118,528経路と全1,300対象をstream検証し、実consumerへ安全に結べる47,548経路を実装した。

- level-up: 18,530経路を照合し18,515を実装。Move 1063を使う15経路は保留。
- machine: 55,380経路を照合し、現行128-slot catalogに存在する29,033を実装。供給slotがない26,347は保留。
- その他の保留: evolution 341、reminder 298、tutor 1,113、egg 2,572、shared egg 5,041、pre-evolution carry 35,183、form change 70。
- 全consumerを合算したMove 1063依存は159経路。既存技への近似置換はしていない。
- Stage65から81,693 bytes変更、3,520 spans、宣言外変更0。追加level-up payloadは`future_tail`の`0x01FDA248`から60,116 bytes。
- mGBAは実level-up／machine consumerを独立2 process、先頭・中央・末尾・Caterpie代表でPASSした。scheduler E2E、4枠満杯、save/reload、未実装consumerは未検証なのでP03完了ではない。

## P04の素材と容量

- 追加予約はSpecies/Form 52件（1621〜1672）、Item 45件（999〜1043）、Ability 6件（312〜317）、Move 1件（1063）。予約はmanifest appendの順序を固定するが、現行runtime表へはまだ反映していない。
- Mega 49件とMega Stone 45件は固定commitの外部sourceからprivate-use stagingへ再現可能に変換した。49/49 species palette、45/45 stone asset、670 payload files、426,648 bytes、asset-set SHA-256 `462fed5d292582f44a29007e2da488829973c57b1964f86fa12e6da41c6e749c`。
- Tatsugiri Droopy／Stretchyは同じupstream共通Mega paletteが正本であり、欠落扱いを解消した。
- Winds/WavesのBrowt／Pombon／Gecquaは完全なGBA素材を確認できず、3/3ともIDだけ予約してasset未生成。別種画像や生成placeholderで隠していない。
- 外部source rootにlicense fileがないため、生成素材は`userfile/generated/modernization_p04_assets`のGit管理外・個人private利用限定。GitHub private environment bundleからも明示除外する。
- 39固定表の拡張見積りは655,852→676,757 bytes（+20,905）。`integration_modules`候補へ収まるが、Item 1024以降の10-bit consumer、公開event 88→89 bit、legacy Ability u8、save item bitmap 125→131 bytes、全表relink/migrationは未実装。
- 容量manifestはStage65基準。Stage66はP04の`integration_modules`候補と非重複だが、`future_tail`残量は155,064から94,948 bytesへ減る。

## P05〜P08の境界

- P05は採用済み新MoveをSide Change／Ally Switch 1063の1件、新Abilityを6件として固定した。技性能の提出済み採用差分は0。未実装効果を既存effectへ近似していない。
- 公式特性が不明な対象は、stable replacement key、`TEMPORARY_REPLACEABLE`、非公式表示guardを持つ仮特性14件として保持した。分類保留2件を含め、後から中央bindingだけを差し替えられる。
- P06の提出済み種族調整差分は0、P07の追加習得差分も0。review-only資料を自動採用していない。
- P08は上記checkpointのhash、生成実装、ignored ROM/BPS、evidence sourceを統合監査する。active baseline Stage62、P01のみDONE、P02〜P08未完了、release-ready=falseを維持する。

## 入力・GitHub・権利境界

- 受領ZIPは`userfile/imports/modernization_p01/`の読取専用原本で、Gitへ追加しない。複製番号ではなくsize／SHA-256／内部member identityで照合する。
- 2026-09-08、`private-environment-v1`を置いたrepositoryが誤ってPublicだったことを実APIで確認し、ユーザー指示によりrepository全体をPrivateへ変更した。Release 5資材は削除せず保持した。
- private資材を読む全GitHub workflowは、GitHub APIの`.private == true`をdownload前に必須確認する。repositoryが将来Publicへ戻った場合はfail closedする。
- P04外部素材は既存private Releaseへ追加していない。root license不在のため再配布可能とは扱わない。

## 最小の再検証入口

同一入力hash・同一実装HEADの重い検証は再利用し、変更に直結するcheckだけを選ぶ。

```bash
python3 scripts/build_modernization_p04_assets.py --check --compact
python3 scripts/build_modernization_p04_capacity.py --check --compact
python3 scripts/build_modernization_p05.py --check
python3 scripts/build_modernization_p07.py --check
python3 scripts/build_modernization_p03_stage66.py check
python3 scripts/run_modernization_p03_stage66_mgba.py check
python3 scripts/build_modernization_p08.py --check
```

Stage66をclean private環境から作り直す必要がある時だけ`modernization-p03-stage66` suiteを使う。全repository unitと実mGBA chainを毎回重ねない。

## 再開順

1. P02の未検証進化条件・キャンセル・道具・特性/form・save/reloadを実consumerで閉じる。
2. Move 1063、Ability 6件、Item/Ability/public-event/saveの幅拡張と全固定表relinkを実装する。
3. P03の70,980保留経路をconsumer別に小分けし、供給方針と実ROM testを付けてStage66へ積み上げる。
4. P04の52 Species/Form、45 Stone、入手・Mega lifecycle・UI・図鑑・saveを累積候補へ接続する。Winds/Waves 3種の素材不足は解消まで明示保留する。
5. 提出済み採用差分が入った場合だけP06/P07を実装し、最後にP08 release gateを再評価する。

どの再開点でも、過去Stage、原本ZIP、既存saveを上書きせず、候補Stageを現行プレイ基準へ自動昇格しない。
