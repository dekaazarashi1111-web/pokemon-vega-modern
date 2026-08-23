# USER-20260823-SPECIES-FORM-BACKSPRITE-COMPAT — Species依存フォームと背面戦闘画像を正規化する

- Lane: `engine/species/battle/graphics/qa`
- Depends on: `T09`, `T30`
- Queue ID: `USER-20260823-SPECIES-FORM-BACKSPRITE-COMPAT`
- Baseline: Stage 47 / commit `6f6fd82` / ROM SHA-256 `fccc882e7b11315a36b146715396d63348b726268e7560a99a55f4ccbad3d3c9`

## 目的

Vega既存Species `0..411`を維持したまま、DPE-JP由来Species/Formを再配置したcanonical IDと、
固定CFRU-JPがsource IDで直接比較・遷移する全Species依存処理を一元対応させる。
同じずれがあるAbility IDも全定義・全利用箇所をmanifest基準で正規化し、ミミッキュ、
ジガルデ等の既知例に限定せず、CFRU-JP由来の特性処理全体を対象とする。
同時に、追加Speciesのプレイヤー側back spriteが実戦画面で欠ける経路を修正し、
表のbyte検査だけでなく実OAM・VRAM・描画まで継続的に検証する。

upstream vendorは変更せず、現行のDPE-JP/CFRU-JP統合をproject-side compatibility layerで修正する。

## 実行

1. `manifests/species_ids.csv`と`manifests/ability_ids.csv`からproject／DPE-JP／CFRU-JPの数値を機械比較し、全Species/Form/Abilityの整合性レポートを生成する。
2. CFRU-JPの全`SPECIES_*`／`ABILITY_*`利用箇所、Species直接比較、特性分岐、`DoFormChange()`遷移、indexed tableを監査し、個別ハードコードではなくmanifest生成のcanonical mappingへ接続する。
3. 特性ID全件を静的に検証し、Species依存フォーム特性を自動列挙したうえで、Hunger Switch、Disguise、Battle Bond、Schooling、Zen Mode、Ice Face、Power Constructを最低限の実ROM代表として発動・遷移・復元まで検証する。
4. 追加Speciesのback table、coords、loader、OAM、OBJ VRAM、palette、画面描画をplayer/opponentで比較し、原因箇所だけを意味移植する。
5. Gen 1／3 Vega既存、Gen 6／7／8／9追加、alternate／Mega／regional formの表示回帰を追加する。
6. Stage 48、Stage 47差分BPS、clean直接BPS、再生成可能なmetadata/reportを生成する。

## 受入条件

- [x] Vega既存412枠とcanonical Species `0..1620`を再採番しない。
- [x] manifestにある全Species/Formと全Abilityのproject／DPE-JP／CFRU-JP数値・symbol・変換可否をレポートできる。
- [x] 固定CFRU-JP buildへ入る全`SPECIES_*`／`ABILITY_*`利用箇所を分類し、未定義・source ID残存・重複変換をfail-closedで拒否する。
- [x] 全Abilityのcanonical IDとCFRU-JP source IDの対応、およびruntimeのinstance解決経路が一致する。
- [x] Hunger Switchを4ターン、Disguiseを初撃防御・1/8減少・次撃通常・交代／終了復元、Battle BondをKO後変身まで実ROMで確認する。
- [x] Schooling、Zen Mode、Ice Face、Power ConstructのSpecies依存遷移がcanonical IDで動作する。
- [x] form change後のbattle Species、party Species、type、stats、ability、front/back sprite、palette、終了時復元が破綻しない。
- [x] 追加Speciesのplayer back spriteが64×64 OAM／2,048-byte OBJ tileとして全身表示され、上下・左右clip、別Species、palette破損がない。
- [x] PC／party icon、summary、enemy front、player back、shiny、form前後を世代・フォーム別代表で実画面またはframebuffer検証する。
- [x] IntimidateとSpeed Boost、single/double、wild/trainer、Factory、Raid、Codex対戦、Box 14の既存回帰を維持する。
- [x] upstream vendorを変更せず、manifest／vendor定数／対象sourceのいずれかが変わった時に未監査のSpecies・Ability直値がfail-closedになる。
- [x] 対象check、BPS往復、private guard、ログ、version履歴、タスク単位commitを完了する。

## 完了

対象検証と実測値を `design/run_log.md` / `design/version_log.md` / `design/current_state.md`へ記録し、
`design/tasks_next.md`の本タスクだけを`[>]`から`[x]`へ変更する。
`USER-20260823-SPECIES-FORM-BACKSPRITE-COMPAT:`で始まるコミットを作る。
