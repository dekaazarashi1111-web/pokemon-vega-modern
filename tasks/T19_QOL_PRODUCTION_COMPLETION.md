# T19 — Complete production QOL integration

- Lane: `engine/ui/save/qa`
- Depends on: `T18`

## 目的

Stage 35を固定baselineとして、`content/qol_progression.csv`のrelease対象35機能を、
catalog、host fixture、ROM probeだけでなく、実際のVegaのUI・field・PC・預かり屋・battle・save導線へ接続する。
ユーザーが通常プレイで操作でき、解禁境界、失敗時atomicity、save/reloadまで成立した時だけQOL完成とする。

## 現在の未完了根拠

- 旧T17はQOL-B 8機能を`config/feature_matrix.csv`へENABLEDとして登録しているが、
  `overlays/qol_b/qol_b.c`の主要処理は簡略`QolBMon`配列を使うhost fixture向けである。
- Stage 17のproduction ROM接続は`QolB_RuntimeProbe`と既存portal/returnが中心で、
  PC検索・SELECT複数選択・一括操作・field PC・PC技編集・タマゴバスケット・自動戦闘の
  実PC/menu/daycare/battle callback接続を証明していない。
- QOL-Aにも、実装済み、上流設定のみ、生成tableのみ、fixtureのみが混在し得る。
  過去レポートのPASSや`release_default=ENABLED`だけをproduction実装の証拠にしない。

## 固定baseline

- ROM: `build/stages/35_trainer_changekit_final.gba`
- SHA-256: `2ff8d61d7e17d120eaf60a81863dc29f6666d84c48a245e1be3d8dfa2447d180`
- Stage 35 source commit: `993e1419caa0a51d78ac15be8e2caad042470549`
- Trainer ChangeKit 1,302戦、6,490 member、201 Kanto trainer、物理map event、gimmick/save cleanupを回帰不変条件とする。

## 所有範囲

このタスクが所有するもの:

- QOL engine/runtime、既存UIへのadapter、unlock resolver、save migration、production hook。
- 35機能のproduction binding ledgerと生成器。
- Stage 35→36 serializer、focused tests、mGBA quick/full、clean rebuild証跡。
- QOLを呼ぶための安定したsymbolic service ABI。

このタスクが所有しないもの:

- ChatGPT Proが設計する物語、人物、台詞、sidequest、map event配置。
- `templates/event_authoring_packet/**`、返却event bundle、`content/trainer_changekit_final/**`の再設計。
- Trainer party/AI/gimmick、取得イベント、Factory経済の内容変更。
- 新規full-screen UI、専用map、長いcutscene、独自minigame、装飾asset。

イベント側は後からQOL service ABIへ短い会話wrapperを接続できる。QOLの能力本体、unlock truth、
transactionはT19が所有し、イベントbundleの完成を待たずに実装・検証する。

## 実行

1. `docs/QOL_POLICY.md`、`content/qol_progression.csv` 35行、`config/feature_matrix.csv`、
   `config/qol_b.json`を一意keyで結合し、各行を次へ分類する。
   - `LIVE_ENGINE_UI`
   - `LIVE_SERVICE`
   - `LIVE_SUPPLY`
   - `MODEL_ONLY`
   - `PROBE_ONLY`
   - `CATALOG_ONLY`
   - `UNBOUND`
2. `config/qol_production_bindings.csv`を正本として、feature key、capability key、実入口、
   UI owner、unlock source、save owner、serializer owner、mGBA caseを35/35行に固定する。
3. QOL-Aを通常プレイ入口から再監査し、未接続なら実装する。
   - `INSTANT / FAST / NORMAL`文章設定と永続化
   - ダッシュ／自転車高速化とtile event非欠落
   - summary／PC右欄のIV/EV compact表示
   - 全体学習装置ON/OFFと戦闘経験値だけの分配
   - 経験アメと共通数量UI
   - 現代孵化、タマゴPC転送／queue、孵化演出設定
   - mint、特性道具、王冠、EV reset、無料わざメモリー
4. QOL-Bを簡略`QolBMon`ではなく、現行80-byte BoxPokemon、実box/save、実bag、実relearn poolへ接続する。
   - 既存PC内の名前・タイプ・特性検索
   - SELECT marker複数選択、一括box移動、一括逃がし
   - map schemaとcontextを守るfield PC
   - PC内技編集とPP初期化
   - 持ち物一括回収／移動の全体rollback
   - 実預かり親、通常相性・生成RNG、共有queue 5個を使うタマゴバスケット
   - 通常random野生だけを対象とし各turn cancel可能な自動戦闘
5. `content/qol_progression.csv`の35 unlockを実Vega/Kanto stateへ結び、解禁前、境界直後、
   save/reload、移行saveを検証する。derived supplyは既存shop/reward ownerを再利用し、二重報酬を作らない。
6. event authoring packetのservice profileと対応する安定symbolic dispatcherを公開する。
   会話が未統合でも、state fixtureと既存Options/PC/field menu/端末から能力本体を検証できるようにする。
7. Stage 35へexpected-byte付きhook/repointを適用してStage 36を生成する。
   allocator、RAM、save、map object、trainer table、CFRU hookの所有重複を0にする。
8. helper直呼びだけで完了せず、実ROMのユーザー入力経路でfocused testsとmGBAを実行する。
   失敗時は原因を修正し、同じclean入力から再生成する。

## 必須成果物

- `config/qol_production_bindings.csv`
- `overlays/qol_production/**`
- `scripts/build_qol_production.py`
- `tools/mgba_qol_production_smoke.c`
- `tests/test_qol_production.py`
- `reports/generated/qol_production_audit.json`
- `reports/generated/qol_production_coverage.json`
- `build/stages/36_qol_production.gba`（Git管理外）
- Stage 35→36 BPS、clean→Stage 36再構築証跡（Git管理外）

既存ファイルを再利用した方が安全な場合は上記へ薄いadapterを置き、同等の機械可読成果と
task固有checkを提供してよい。成果物名だけを満たす空stubは禁止する。

## 受入条件

- [ ] release対象35/35行が一意のproduction ownerを持ち、`MODEL_ONLY`、`PROBE_ONLY`、`CATALOG_ONLY`、`UNBOUND`が0。
- [ ] QOL-B 8機能が実BoxPokemon/PC/menu/daycare/battle/saveを使用し、簡略shadow modelだけではない。
- [ ] 全ユーザー操作機能が通常のfield/PC/summary/bag/options/battle入口から到達可能。
- [ ] 解禁前は利用不能、境界直後は利用可能で、save/reload後も同じ。Vega badge/HM/story stateを汚染しない。
- [ ] cancel、容量不足、禁止個体、mail/key item、box満杯、効果なし、resetで部分更新・増殖・消失・二重消費が0。
- [ ] PC検索・複数選択・技・持ち物操作を複数box、タマゴ、特殊個体、6文字名、追加Speciesで検証する。
- [ ] タマゴバスケットが親不在／相性なし／255歩／256歩／queue満杯／save-reloadを通常孵化coreでPASSする。
- [ ] 自動戦闘が通常random野生だけで動作し、trainer/static/story/legend/shiny/Factory/Raidでは通常戦へ戻る。
- [ ] 文章の全control codeと選択肢、移動の接触／座標event・warp・段差・歩数・遭遇・孵化checkを欠落／重複させない。
- [ ] 経験アメ、全体学習装置、mint/ability/Hyper Training/EV reset、現代孵化が実能力値・表示・saveで一致する。
- [ ] 35行の供給・shop・serviceが指定unlockより早く漏れず、一度限り報酬と反復供給を混同しない。
- [ ] Stage35の1,302 trainer、74 DOUBLE、Mega/Z/Dynamax/Tera、再戦、save cleanup、201 Kanto trainerを回帰する。
- [ ] Stage 36がclean FireRed日本版Rev.0から決定論的に再構築でき、BPS完全往復、declared span外変更0。
- [ ] mGBA quick/fullを独立2 processで実行し、warning/error 0、結果一致。
- [ ] `docs/QOL_POLICY.md`、操作説明、feature matrix、production ledger、実buildが一致する。

## 禁止する完了判定

- audit report、設計、catalog、生成header、host fixture、runtime probeを作っただけでDONEにしない。
- helper関数の直接呼出だけで「ユーザーが操作できる」と報告しない。
- `release_default=ENABLED`や過去T17 PASSをproduction bindingの代用にしない。
- 入力不足がなく安全に実装できる機能をDEFERへ落とさない。

## 完了

1. task固有のbuild/check、focused tests、mGBA quick/full、clean rebuildをPASSする。
2. `design/run_log.md`と`design/version_log.md`へ証跡を追記する。
3. `python3 scripts/taskctl.py done T19 --summary "QOL 35機能をproduction導線へ接続しStage36を検証"`を実行する。
4. 最終indexに意図した差分だけをstageし、task graph、private guard、`git diff --check`をPASSする。
5. `T19:`で始まるcommitを作る。pushしない。
