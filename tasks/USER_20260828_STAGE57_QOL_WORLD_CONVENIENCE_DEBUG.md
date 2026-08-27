# USER-20260828-STAGE57-QOL-WORLD-CONVENIENCE-DEBUG — Stage57のQOL・世界・利便性を再監査してStage58へ改善する

- Status: `IN_PROGRESS`
- Lane: `qa/qol/item/economy/world/event/npc/wild/facility/save/release`
- Depends on: `USER-20260827-STAGE56-COMPREHENSIVE-DEBUG-REPAIR`、`T19`、`T20`、`T29`、`T30`
- Queue ID: `USER-20260828-STAGE57-QOL-WORLD-CONVENIENCE-DEBUG`
- Baseline: Stage 57 / ROM SHA-256 `546136a6baa26efd7a70c2b6826bf902c4841a4a1113cb53bfdc44c77971663d`
- Target: Stage 58（QOL実使用、Codex拠点、薄い場所、野生・item・shopを実ROMで改善する）

## 目的

Stage57の横断修復を土台に、QOL系道具が所持できるだけでなく通常操作から効果を発揮し、保存後も維持されることを再監査する。イベント、会話NPC、trainer、野生、field itemの既存ownerと到達性を保ちながら、到達コストに対して探索価値が薄い場所、野生確率の偏り、消耗品やQOL道具の売買・供給不足を定量化し、根拠のある小規模改善を行う。

Codex対戦受付map `96/5`では、受付NPCの真横へ通常PC Storageを開ける端末と、ポケモンセンターと同等にHP・PP・状態異常を全回復する人物を配置する。Codex mailbox、対戦、任意報酬、Windowsカタログ、Box 14固有個体庫のtransaction境界は変更しない。

## 固定入力と境界

- `build/stages/57_comprehensive_debug_repair.gba`、33,554,432 bytes、SHA-256 `546136a6baa26efd7a70c2b6826bf902c4841a4a1113cb53bfdc44c77971663d`。
- `build/stages/57_comprehensive_debug_repair.json`、`build/stages/57_allocation.json`、Stage57 full/static/mGBA証跡。
- map `96/5`のCodex受付はlocal ID 2、座標 `(20,19)`、script `0x093CDA80`を正本とし、既存10 object、warp、BG event、map scriptを保持する。
- Vega本編story、既存NPC台詞、固有event、取得台帳、レア遭遇、Kanto Lv.68〜100方針を無断で置換しない。追加は短い任意導線とし、必須進行flagを新設しない。
- 価格・確率・配置はmanifest/configから生成し、ROM byteや数値IDを手作業で継ぎ足さない。
- 標準QA save、私有ROM、iPad上のROM／saveは検証入力として複製して使い、直接変更しない。

## 実装方針

1. QOL item／serviceを入手、bag使用、UI入口、効果、cancel、容量不足、save/reloadまで分類し、未接続・誤接続を再現してowner側で修正する。
2. 全678 map、全wild header／slot、field item、shop／供給sourceを機械走査し、既存Stage57のscript CFG・Species identity・story trainer監査を継承する。
3. 「薄い場所」は到達性、object／BG event、item、wild多様性、施設、既存story ownerを指標化し、採用候補と非採用理由をmachine-readableに残す。採用変更は少数の安全な縦切りを優先する。
4. 野生はslot重み、重複Species、level band、通常／水上／釣り／岩砕きの役割を比較し、レア枠とVega固有生態を保ったまま極端な偏りだけを補正する。
5. shop／供給はunlock時点、買値、売値、反復性、通常通貨／BP／研究通貨を分離し、無限利益、重要品の誤売却、進行前入手、供給不能を0にする。
6. Codex受付横のPC端末と回復人物はobject上限、local ID、座標、collision、script lifecycleをfail-closedで検査し、通常A入力、UI終了、field復帰、save、Codex対戦前後をmGBAで通す。

## 必須成果物

- Stage58 builder／config／必要なruntime adapter。
- QOL item/service、world value、wild balance、shop/economyのmachine-readable監査と日本語report。
- Codex拠点のmap event header再配置、PC／回復script、通常入力mGBA runner。
- Stage57既存7 domainを継承したfocused/static/full回帰。
- `build/stages/58_*.gba`、Stage57→58 BPS、clean→Stage58 BPS、clean rebuild証跡（Git管理外）。

## 受入条件

- [ ] Stage57 ROM／metadata／allocation／証跡のidentityを固定し、旧ROM／save／私有原本／iPadを変更しない。
- [ ] QOL item／serviceの全対象で、入手可能性、通常UI入口、効果、cancel／失敗、save/reloadを分類し、採用した実使用caseをexact ROMで独立2 process検証する。
- [ ] map `96/5`のCodex受付NPC、BP shop、warp、BG eventを保持し、真横のPC端末と全回復人物を衝突なしで追加する。
- [ ] PC端末は通常Storageを開閉し、party／Box変更を通常saveで保持し、終了後にscript contextとfield入力が復帰する。
- [ ] 回復人物はparty全員のHP、全技PP、主要状態異常を回復し、0体、タマゴ、瀕死、通常個体の境界で停止しない。
- [ ] Codex runtime `IDLE`／対戦開始・終了、reward closed/open境界、Windows bank、Box 14 vaultの既存契約を壊さない。
- [ ] 全678 map、全接触可能root、全wild header／slot、全field item、story trainerのStage57診断を継承して不一致0にする。
- [ ] 薄い場所、野生確率、shop／item供給の変更前後を定量report化し、Vega story／レア度／通貨ownerの意図しない変更を0にする。
- [ ] shop／供給で無限利益、重要QOL品の誤売却、unlock前販売、入手不能、bag満杯時の減算を0にする。
- [ ] changed byteがdeclared span内で、ROM／RAM／save／map／hook overlapが0。
- [ ] Stage57差分BPS、clean直接BPS、clean→Stage57→Stage58の3経路がbyte一致する。
- [ ] focused unit、task graph、private guard、staged private guard、`git diff --check`をPASSし、ログ／version／状態を更新して完了コミットする。

## 禁止する完了判定

- QOL itemのmanifest上の存在、静的pointer、単一成功caseだけで「使える」と判定しない。
- PCや回復をhost-sideで代替せず、実ROMの通常A入力とUI／script復帰を通す。
- 薄い場所を長いcutsceneや強制戦闘で埋めず、既存Vega eventを汎用台詞へ置換しない。
- 野生率や価格を感覚だけで変更せず、変更前分布、進行帯、通貨source、売値を同時に監査する。
- 人手散策やsavestateだけを自動回帰の代替にしない。
