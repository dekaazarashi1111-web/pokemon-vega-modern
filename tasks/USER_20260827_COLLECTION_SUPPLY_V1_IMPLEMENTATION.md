# USER-20260827-COLLECTION-SUPPLY-V1-IMPLEMENTATION — 全収集・供給V1をStage 56へproduction統合する

- Status: `IN_PROGRESS`
- Lane: `collection/form/item/raid/world/save/vault/qa/release`
- Depends on: `USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR`のStage 55ローカル成果、`T19`、`T23`〜`T25`、`T30`
- Queue ID: `USER-20260827-COLLECTION-SUPPLY-V1-IMPLEMENTATION`
- Baseline: Stage 55 / ROM SHA-256 `b0a825cb7d3886419e4122f2de54a069fdf8e7a5fe41a9fef0bc3235e68cbcf8`
- Target: Stage 56（ローカル再現可能ゲート合格をrelease判定に使い、iPad実機承認は要求しない）

## 目的

ChatGPT Pro返却済みのCollection Supply V1を、Stage 55へproduction統合する。Stage 26の通常図鑑完成対象1,206種と進化入口フォーム10件を保持し、全388 form、G-Max factor 34行、全999 Item、既存Raid 256行を含む292 pool行、217 reward行、14 symbolic hostを実consumerへ接続する。

返却CSVを参考表やhost-side集計のまま置かない。symbolic keyを現行canonical IDへ解決し、Item shop、form service、G-Max付与／解除、Raid rotation／報酬、world host、Box 14 vault、save／Continueへ接続する。物理world bindingはStage 55 owner台帳、原作Vega参照、通常A入力でexact再監査する。

## 固定入力

### baseline

- ROM: `build/stages/55_world_runtime_visible_feedback_repair.gba`
- ROM size: 33,554,432 bytes
- ROM SHA-256: `b0a825cb7d3886419e4122f2de54a069fdf8e7a5fe41a9fef0bc3235e68cbcf8`
- metadata: `build/stages/55_world_runtime_visible_feedback_repair.json`
- owner ledger: `reports/generated/world_runtime_owner_ledger_stage55.json`
- Stage 55はローカル22 fixture×独立2 process、BPS往復、declared span監査をPASSした完了baselineとして扱う。

### 返却済み設計

- 原本: `userfile/imports/Pokemon-Vega_COLLECTION-SUPPLY-V1_IMPLEMENTATION-READY.zip`
- ZIP SHA-256: `8a1b271e9b321f6409f2b766a1b469cec15a8353dfb023d99184cd305fb641db`
- ZIP size: 41,513 bytes、12 entries
- validation fingerprint: `bf957958e2fa3e1672cddb484cb35e8f1d2c3df46a5eef34759ec5007c1de4bd`
- validator結果: PASS、open question 0、warning/error 0
- canonical rows: form 388、G-Max 34、Item 999、Raid host 14、pool 292、reward 217、host requirement 9、batch 8
- validator: `templates/chatgpt_pro_design_packets/tools/validate_submission.py`
- packet root: `userfile/chatgpt_pro_design_packets/unpacked/Pokemon-Vega_CHATGPT-PRO_COLLECTION-SUPPLY-V1_INPUT_20260825/`

原本ZIPは読取専用・Git管理外とし、直接編集・再圧縮しない。全12 entryを安全な一時領域で読み、共通validatorを毎buildの入力gateにする。

## 固定仕様

- Stage 26の1,206種と進化入口10件の既存取得transactionを変更しない。全国図鑑完成数は1,206のままとし、form別完成ledgerを追加しない。
- 保存可能formへwild overlay、孵化、進化、研究タマゴ、可逆form service、Raid捕獲のいずれかを与える。helper、Mega、Tera、戦闘中変身、G-Max表示Speciesは直接配布しない。
- G-Maxはbase個体のfactor bitだけで表現する。`ITEM_KEY_DYNAMAX_CANDY`を反復供給し、対象34行の付与／解除、Raid捕獲時bit付与、raw80 vault往復を実装する。
- Item 999行をsymbolic key単位で扱い、同名legacy／append keyを統合しない。除外69行をshop、報酬、所持個体へ混入させない。
- money 86、BP 354、research 207、Factory 20、NPC gift 82、form service 18、story 30、Vega existing 69を既存ownerへ接続する。Mega Stone 47件とZ Crystal 35件は一度限りclaimとする。
- 既存Raid 256行のspecies、level、capture policy、unlock、共有捕獲state 125件を維持し、追加36行だけを加える。捕獲stateと報酬stateを分離する。
- 14 hostは新規専用map／lobby／full-screen UIを作らず、原作意味と通常A入力を確認した既存service、会話host、terminal、BG eventへ束縛する。
- Box 14 raw80 ABIと通常PC容量は変更しない。form、G-Max bit、Tera state、持ち物を保持し、mail所持個体を拒否する。

## 実装batch

1. `BATCH_P0_REFERENCE_FREEZE`: 全返却表、canonical key、Stage 26 checksumを固定する。
2. `BATCH_P0_ITEM_CORE`: money／BP／research／Factory／form／relic claim catalogを実装する。
3. `BATCH_P0_FORM_GMAX`: form route、可逆service、G-Max factor付与／解除を実装する。
4. `BATCH_P1_RAID_POOLS`: 14 hostと292 pool行をrotation runtimeへ接続する。
5. `BATCH_P1_RAID_REWARDS`: 217 reward行とfirst-clear／repeatable transactionを接続する。
6. `BATCH_P1_WORLD_BINDING_AUDIT`: Stage 55 owner台帳から物理hostをexact再監査して束縛する。
7. `BATCH_P2_VAULT_REGRESSION`: raw80の30体往復、form／factor／持ち物、mail拒否を検証する。
8. `BATCH_P2_EXACT_ROM_ACCEPTANCE`: Stage 56、BPS、clean再構築、mGBAを受入確認する。iPad配置は任意の運用作業として別記録する。

## 必須成果物

- `content/collection_supply_v1/**`
- `config/collection_supply_v1.json`
- `overlays/collection_supply_v1/**`
- `scripts/build_collection_supply_v1.py`
- `scripts/rebuild_collection_supply_v1_from_clean.py`
- `tools/mgba_collection_supply_v1_smoke.c`
- `tests/test_collection_supply_v1.py`
- `reports/generated/collection_supply_v1_{audit,coverage,world_binding}.json`
- `build/stages/56_collection_supply_v1.gba`（Git管理外）
- Stage 55→56 BPS、clean→Stage 56 BPS、mGBA quick/full、clean rebuild証跡（Git管理外）

既存runtimeを再利用する場合も、上記名のadapter、canonical model、機械可読証跡を用意する。CSVのcopy、ROM未接続table、host-only modelだけを成果物にしない。

## 受入条件

- [ ] Stage 55と返却ZIPのsize／hash／fingerprintが一致し、原本ZIP、ROM、saveを変更しない。
- [ ] form 388、G-Max 34、Item 999、既存Raid 256＋追加36、reward 217、host 14を欠落・重複0でcanonical IDへcompileする。
- [ ] Stage 26の1,206種＋進化入口10件、既存trainer／world／QOL／Factory／Research／Reward encounter／Codexを回帰不変に保つ。
- [ ] 保存可能formの全行に実取得／変換経路があり、helper／Mega／Tera／一時形態／G-Max表示Speciesを直接受け取れない。
- [ ] Dynamax Candyの反復取得、対象可否、factor付与／解除、Raid捕獲、save／Continue、vault往復が実ROMで成立する。
- [ ] 機能Itemに供給があり、除外69行がshop／reward／held itemへ混入しない。必須消耗品は反復取得でき、Mega／Z claimは各key一度だけである。
- [ ] 既存Raid 256行の意味契約を保持し、14 host／全pool／全reward poolが通常field入力から到達できる。捕獲、非捕獲、捕獲済み報酬、reset、first-clearを原子的に処理する。
- [ ] Box 14 raw80の30体batch往復でform、G-Max bit、Tera、持ち物、checksumが一致し、mail個体を拒否する。
- [ ] changed byteがdeclared span内で、ROM／RAM／save／map／hook overlapが0。
- [ ] clean FireRed日本版Rev.0からStage 56を決定的に再構築でき、Stage 55差分／clean直接BPSが完全往復する。
- [ ] mGBA quick/fullの独立2 processがwarnings/errors 0で一致する。
- [ ] Stage 55 world修復を含むStage 56をfresh-core自然入力で独立2 process再現し、iPad実機の有無に依存せずrelease判定できる。

## 禁止する完了判定

- 返却CSVのcopy、schema変換、件数集計、host-side modelだけでDONEにしない。
- Stage 53以前の誤ったmap／NPC識別子や、Stage 55未監査のaddressを盲用しない。
- 999品を一つの巨大shopへ置かない。既存通貨、捕獲state、save ownerを無断でaliasしない。
- 旧Stage、原本ZIP、ROM、save、savestateを上書きしない。
- ローカルsmokeだけでrelease候補またはタスクDONEにしない。
