# USER-20260827-STAGE56-COMPREHENSIVE-DEBUG-REPAIR — Stage56を横断デバッグしてStage57へ修復する

- Status: `IN_PROGRESS`
- Lane: `qa/wild/species/world/npc/menu/story/save/battle/release`
- Depends on: `USER-20260827-COLLECTION-SUPPLY-V1-IMPLEMENTATION`、`USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR`、`USER-20260827-STAGE56-TEST-READY-SAVE`
- Queue ID: `USER-20260827-STAGE56-COMPREHENSIVE-DEBUG-REPAIR`
- Baseline: Stage 56 / ROM SHA-256 `9309c073798dc363174458ebcb75bf3f1e86d475dcd129b74875d5a6bb875778`
- Target: Stage 57（報告済み再現バグを修正し、高速な継続QA基盤をproduction gateへ追加する）

## 目的

ユーザー実プレイで判明した、505番道路でニャルマー／ミルタンクという名前なのにエルフーンの外見になる野生個体不整合と、NPCへ話しかけた際に壊れたメニューが表示され操作不能になる不具合を最優先で再現・修正する。

局所的なbyte修正で終わらせず、同じowner・table・menu lifecycleを使う全対象へ監査を広げる。Stage56 exact ROMからfixtureを自動生成し、mGBA上で短時間にdomain別／全体回帰を選択実行できるデバッグ基盤を追加する。story、warp、trainer、item、field object、会話、wild、battle、save／Continueのcritical pathを機械検査し、新しく見つかった再現可能な重大不具合も同じStage57へ統合する。

## 固定入力

- `build/stages/56_collection_supply_v1.gba`、33,554,432 bytes、SHA-256 `9309c073798dc363174458ebcb75bf3f1e86d475dcd129b74875d5a6bb875778`。
- `build/stages/56_collection_supply_v1.json`、`build/stages/56_allocation.json`。
- Stage55 owner ledger、Stage56 Collection Supply canonical model／symbols／14 physical host。
- canonical Species 1,621行と、名前、BaseStats、front/back sprite、palette、icon、cry、learnsetの現行runtime pointer。
- logical T505=`MAP_KEY_TOHOKU_T505`、physical map `3/23`。原作Vega既存野生表を保持し、追加overlayはcanonical IDだけを使う。
- 標準QA saveは検証入力として複製して使用し、追跡対象ROM、私有原本、iPad上のROM／saveを上書きしない。

## 実装方針

1. Stage56の自然歩行から505番道路の報告個体を再現し、生成Species ID、表示名、BaseStats、front sprite、palette、icon、戦闘中Speciesを同一traceへ記録する。
2. 全wild header／全slot／全追加overlayを列挙し、Species ID範囲、name／sprite／stats consumerの同一canonical行、table stride、pointer境界を監査する。
3. 全14 Collection hostと既存service familyを、通常A入力からmenu open、first／last item、page遷移、B cancel、成功／失敗、window破棄、script context解放、field入力復帰まで実行する。
4. 全678 mapの接触可能object／BG scriptを静的走査し、無効root、終端なし、無条件`waitstate`、不正menu count／pointer、重複host、field復帰不能をfail-closedで列挙する。動的検証はowner familyごとの全rootまたは意味同一を証明した代表fixtureを実行する。
5. story critical pathのmap／warp／flag／trainer／item／save境界をmanifest化し、new gameからVega本編、殿堂入り、カントー往復・リーグ、主要施設まで到達不能な必須edgeを検出する。状態を飛ばすfixtureは、直前状態を通常ROM APIで構築したことを記録する。
6. `quick`、domain選択、`full`を持つ高速QA入口を追加し、exact-ROM identity、case fingerprint、独立process一致、mGBA warning／error 0を必須にする。

## 必須成果物

- Stage57 builder／config／runtime adapter（修正がROM byteを要する場合）。
- Stage56/57から自動抽出するmachine-readable QA case／coverage／failure report。
- mGBA exact-ROM runnerと、野生identity、menu lifecycle、story/world critical pathのfocused tests。
- `build/stages/57_*.gba`、Stage56→57 BPS、clean→Stage57 BPS、clean rebuild証跡（Git管理外）。
- 再現原因、同型監査件数、修正件数、残存既知制約を記録したtracked report。

## 受入条件

- [ ] Stage56、metadata、allocation、canonical入力のidentityを固定し、私有原本、旧ROM、saveを変更しない。
- [ ] 505番道路の報告症状を修正前ROMで再現し、原因をSpecies生成／名前／画像／palette／table pointerのどの境界か証明する。
- [ ] 修正後は505番道路の全通常／overlay枠で、生成Species、名前、front sprite、palette、icon、BaseStatsが同一canonical個体を示す。
- [ ] 全wild header／slot／overlayのSpecies範囲、pointer、stride、consumer identityを監査し、不一致0にする。
- [ ] 全14 Collection hostでmenu open、全page境界、first／last、B cancel、成功／失敗、再open、field入力復帰を独立2 processで通す。
- [ ] 全接触可能NPC／BG eventで無効root、不正menu pointer／count、非同期でない無条件wait、到達可能な無表示終了、入力復帰不能を0にする。
- [ ] story critical path、warp、trainer、item、field、battle、save／Continueの機械可読coverageを生成し、必須edgeの到達不能を0にする。
- [ ] `quick`は開発中の主要回帰を短時間で実行でき、`full`は全生成caseをexact Stage57上で独立2 process一致、warning／error 0で完走する。
- [ ] changed byteがdeclared span内で、ROM／RAM／save／map／hook overlapが0。
- [ ] Stage56差分BPS、clean直接BPS、clean→Stage56→Stage57の3経路がbyte一致する。
- [ ] focused unit、task graph、private guard、staged private guard、`git diff --check`をPASSし、ログ／version／状態を更新して完了コミットする。

## 禁止する完了判定

- 505番道路の1枠、報告された2名称、特定NPCだけを手修正してDONEにしない。
- host-side CSV／静的件数だけで、実ROMの通常入力、field復帰、save／Continueを代替しない。
- savestateだけの再現、in-process再利用だけの一致、fixture用ROMへの未宣言patchをrelease証跡にしない。
- 人手で「一通り歩いた」ことを自動coverageの代替にしない。
- iPad実機承認を完了条件にせず、iPad上の既存成果物を直接更新しない。
