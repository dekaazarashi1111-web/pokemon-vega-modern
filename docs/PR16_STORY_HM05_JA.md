# HM05通常取得・Save20 限定受入

`PASS_HM05_SAVE20_SCOPED`。支援story-fastの未完区間のみ。Save19からRoute502の通常NPC会話でHM05「フラッシュ」取得、新トレーナー2勝、野生2離脱、PC通常回復、Save20と独立Continueを受入。HM05習得/使用、自然育成/進化、全国図鑑、研究施設自然到達、全storyは未受入。

## 完了原本

測定source `b47f2d1720b200a7eb01888691e1e489c3df215e`、run `36572961114`、job `109421243251`、upload/postを含む全8step成功。artifact `11036251453`、17868824bytes、SHA256 `baeb19534fa0782976f62eea7b0367f951defc1cb32a240b22a7a81dc3684ac6`、期限 `2026-12-28T13:08:33Z`。全107member/82画面を全byte検証。開発35anchorを正式pixelに結び、追加cold10を目視して合計36anchor。記録は完了原本の読取だけでnative/受入60試験再走/compile0。

248/cold59入力、23900/cold3690frames。ノゾミ128円・タツヤ112円の2勝で5776→6016円。戦闘は12→19→22と25→30→32、野生フロン/スバメは42→45→46と49→50→51で通常離脱。捕獲/野生勝利/敗北0。HM05はmap3/20 object5・7,4のROM checkitem/checkitemspace/additem343と通常会話35〜40を照合。trainer91/116とphysical bits1371/1396を照合し、未実行rematch分岐を合格にしない。

## 保存・回復・境界

Save20 `2ed14acca7a475598bde7098f68f4c8a8f0fb131ad8f2bc8ad6e4b508c1d08e5`、131088bytesを独立Continue後も全保持。PC map5/4・7,4北・party4全回復/RP0・badge1・6016円・HM05所持。Bag全slotはmachines slot1の(0,0)→(343,1)以外不変。手持ち600bytes中友情2bytesとEV欄2bytesのみ変化、EXP/種族/Lv100不変。これはEV因果全ケースや自然育成の受入ではない。

全Save差分6783bytes/1784範囲を照合。旧Save19 bank57344bytes、boxed PC、未使用party200bytes保持。ROM宣言payload checksum42件、S61E CRC/反転値を検証しS61E payload不変。legacy変数4021=46→24/4022=3→0以外不変。NationalDex magic0/var404e0/flag840=0、story4071=5/4072=1、分離progression/grant owner不変。全差分hex/ROM/Save/画像はartifactだけ、tracked text原本は `content/modernization/pr16_story_hm05_evidence`。

load中1枚の転送先Save座標/転送元live座標不一致だけを種別付きで許可し、field到達にはしない。旧判定器は不変。観測64〜68は書込途中、69/70でcounter20/Flash安定/通常callback/lock0。warm終端の旧field補助述語falseを改竄せず記録。保存成功文言frameは未採取。開発coldはcard/menu終了で未受入、正式coldはその原本prefixを全保持し、追加待機/B/待機後のobserve10でfield=true/lock0を確認した。開発2・正式2native成功。60試験を開発と正式の計120別件に水増ししない。

## 既存結果との切分け

Save19のジム2勝/エルナトバッジ/通常報酬/Save19受入はd2a97721で記録済み。旧視覚注釈の「エリナ」は「エルナト」の誤字で、旧raw画面/flag2080/受入値は変更していない。旧一般CI run36559155007はP03 capacityで `tested source changed: overlays/qol_production/qol_production.c`、25試験中2ERROR。旧原本とのsource一致規約は緩めず専用Actions成功と区別する。一般CI全成功/PR merge/release/active baseline切替は主張しない。

## 次の唯一の開始点

story-fastの唯一の開始点はartifact11036251453のstory-fast.srm（Save20、131088bytes、SHA256 2ed14acca7a475598bde7098f68f4c8a8f0fb131ad8f2bc8ad6e4b508c1d08e5）。アヤメPC map5/4・7,4北・party4全回復/RP0、6016円・badge1・var4071=5/4072=1、HM05フラッシュ所持から通常storyの未完区間だけを進める。HM05は未習得/未使用。通常NPC取得、新トレーナー2勝、野生2離脱、PC回復/Save20/coldは完了。248/cold59入力・60試験・Save1〜19/旧BP/P08は無影響に再走しない。分離progression原本Axew Lv37/EXP68589とNationalDex magic0・grant ownerを保全し、flag/var注入で解禁しない。正規全国図鑑解禁、自然育成/進化、Lucky Egg対照・12成長ケース・Lv100soak・研究施設自然到達・全storyは未完。

記録source `556e4b2150df292af3ab90d8e88db9e41a759dfc`、run `36573749814`。記録自身のpush/upload成功は自己予測せず、別API・record-head.txt・record.zipで読戻し確認する。
