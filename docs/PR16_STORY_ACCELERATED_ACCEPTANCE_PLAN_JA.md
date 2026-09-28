# PR #16 ストーリー高速走破・自然成長分離計画

> 所有者決定。固定入口は `CHATGPT_RESUME.md`。正式停止点 `PASS_STORY_SAVE14_SCOPED` と保存済みSave14原本は変更しない。
> この文書は実行方針の正本であり、既受入の自然育成、難易度、入手経路、releaseを追加受入したものではない。

## 目的

ストーリー接続確認と、戦闘EXP・レベルアップ・技習得・進化の検証を別レーンへ分離する。
ストーリー側は自己OTのLv100テスト個体で戦闘時間を縮め、成長側は通常の野生戦開始、通常コマンド、EXP付与、技習得UI、進化、field復帰、通常Save、fresh Continueを通す。
低レベル自然育成を全ストーリー走破の前提にせず、変更境界をデータから生成して一戦単位で検査する。

## 不変境界

- Save14原本artifact `10999218544`、`training.srm`、97画面、303/cold40入力、110検査を再実行・上書きしない。
- 作業は原本から複製した `story-fast.srm` と `progression.srm` で行う。原本hash、作業コピーhash、全変更byteを記録する。
- party fixtureは戦闘開始前だけ許可する。戦闘開始後はparty、EXP、level、技、PP、進化状態、story flag、outcomeへのhost書込みを禁止する。
- 自己OTはSave14のOT ID、OT名、OT性別、言語を完全一致させ、暗号化とchecksumを正規処理で再計算する。単なる表示名一致で代用しない。
- story-fastの結果を難易度、自然捕獲、自然加入、自然な資金・用品、自然レベル曲線の受入へ昇格しない。
- progressionのfixture戦を野生テーブル、自然遭遇率、相手の自然初期技の受入へ昇格しない。
- key item、badge、HM取得flag、story flag、money、RPはfixtureで与えない。配布・入手イベントを飛ばさない。

## レーンA: Lv100自己OTによるストーリー高速走破

Save14作業コピーでは、既存のツツケラとリープンを消去せずPCの空きslotへ退避し、次の4体をpartyへ置く。2枠は固定配布、強制加入、捕獲等のため空ける。数値IDは現行identityの確認値であり、実装時は必ずstable keyから再解決する。

| 役割 | 個体 | 現行canonical ID | 能力・育成 | 持ち物 | 技構成 |
|---|---|---:|---|---|---|
| 主力特殊 | `SPECIES_KEY_MEWTWO` | 151 | Lv100、自己OT、ひかえめ、31IV、特攻252/素早さ252/HP4、通常フォーム、Pressure | ものしりメガネ | サイコブレイク(ID600) / はどうだん(ID366) / かえんほうしゃ(ID53) / れいとうビーム(ID58) |
| 物理・ability対策 | `SPECIES_KEY_HAXORUS` | 851 | Lv100、自己OT、いじっぱり、31IV、攻撃252/素早さ252/HP4、Mold Breaker | ちからのハチマキ | ドラゴンクロー(ID337) / じしん(ID89) / かわらわり(ID280) / つばめがえし(ID332) |
| field utility A | `SPECIES_KEY_MEW` | 152 | Lv100、自己OT、戦闘主力にはしない | けむりだま | なみのり(ID57) / そらをとぶ(ID19) / かいりき(ID70) / いわくだき(ID249) |
| field utility B | `SPECIES_KEY_BIBAREL` | 691 | Lv100、自己OT、戦闘主力にはしない | なし | いあいぎり(ID15) / たきのぼり(ID127) / ダイビング(ID291) / ロッククライム(ID398) |

### 編成理由

- Mewtwoは反動、溜め、命中不安、Choice固定を避け、ほぼ全相手を一手で処理する。DarkにはAura Sphere、SteelにはAura Sphere/Flamethrower、Dragon/GroundにはIce Beamを使う。
- Haxorusは特殊耐久の高い相手とability依存の停止要因を担当する。Mold BreakerでLevitate/Sturdy等の影響を減らす。自動入力の安定性を優先し、Stone Edge等の命中不安技や反動技を使わない。
- Double BattleではHaxorusのEarthquakeを味方へ当てない。Mewtwoの単体技とHaxorusのDragon Claw/Brick Break/Aerial Aceで順に処理する。
- Mega、Z、Dynamax、Terastal、伝説専用変身は高速走破の必須条件にしない。通常フォームと通常戦闘だけで進め、追加mechanicの受入と混同しない。
- field moveは、対応するHM・key item・badge・story authorizationをゲーム内で自然取得した後の区間だけ有効化する。先に技だけ入れてsequence breakしない。区間間の作業コピー更新は新しいfixture境界として記録する。

### field moveの段階解禁と差替え

基本loadoutはMewのなみのり・そらをとぶ・かいりき・いわくだき、Bibarelのいあいぎり・たきのぼり・ダイビング・ロッククライムとする。ただし、各技は対応するHM・key item・badge・story authorizationをゲーム内で自然取得した後だけ入れる。

暗所でフラッシュ(ID148)が必要な区間は、Mewのその時点で最も不要な解禁済みutility技と一時交換し、区間終了後に元へ戻す。交換前後を別fixture boundaryとして、技・PP・個体checksum・Save差分を記録する。未取得field moveを先行投入してsequence breakしない。

持ち物と支援用品は現候補のitem manifestからstable keyとABIを解決してから使用する。ものしりメガネ、ちからのハチマキ、けむりだま等を完全一致で解決できない場合は、数値IDを推測せず持ち物なしへfail-safeする。

### 支援用品

`story-fast.srm` に限り、通常Bag UIで使う支援用品として Max Repel 99、Full Restore 30、Max Elixir 10、Escape Rope 10を追加してよい。追加前後の全Bag差分を記録する。Master Ball、key item、HM、badge、money、RPは追加しない。支援用品の存在を通常経済・自然供給の受入に数えない。

### Story受入

最初に自己OT服従、通常技選択、勝利、field復帰、通常Save、fresh Continueを1戦だけsmokeする。その後はマオリ勝利、主要badge、重要施設、region/warp境界、殿堂入り、エンディング等の意味ある区切りで保存する。全雑魚戦ごとのcheckpointは作らない。失敗時は最後の成功Saveから失敗区間だけ再現する。

## レーンB: 通常戦闘EXPによる技習得・進化境界

各ケースは対象個体を「次の境界まで残り1または計算済み少量EXP」にしたpre-battle fixtureから開始する。通常のwild battle入口、通常コマンド、相手撃破、EXP加算、level-up、技習得UI、進化、field復帰を通す。期待EXPは候補ROMのgrowth rate、相手base EXP、level、参加状態、Lucky Egg、Exp. Share等から事前計算し、想定外のlevel飛越しをfail-closedにする。

### 連続育成の基準個体

`SPECIES_KEY_AXEW`（現行canonical ID 849）を自己OTで用い、現行進化契約からAxew→Fraxure→Haxorusの閾値を再解決する。性格いじっぱり、31IV、攻撃252/素早さ252、持ち物しあわせタマゴ。固定ハーネス技は、りゅうのいかり(ID82) / つばめがえし(ID332) / かわらわり(ID280) / ドラゴンクロー(ID337) とする。

- 低levelはDragon Rage、通常帯はAerial Ace、Audino/Chansey/Blissey帯はBrick Break/Dragon Clawを使う。
- long soakではハーネス技を失わないため新技を既定で拒否し、技受入・置換・拒否は別の一戦境界ケースで全て検証する。
- Max PP等のfixture設定は開始時に固定し、戦闘中に補充しない。PP切れ前に通常回復またはSave区切りを入れる。

### 相手切替

| 帯 | 相手候補 | 用途 |
|---|---|---|
| 厳密な1level境界 | `SPECIES_KEY_CATERPIE` / 低level通常種 | EXP過剰を避ける |
| 中盤 | `SPECIES_KEY_AUDINO`（現行ID789） | 中程度の高速化 |
| 高level | `SPECIES_KEY_CHANSEY`（現行ID366） | 物理技で安定して高EXP |
| 終盤・意図的複数level | `SPECIES_KEY_BLISSEY`（現行ID367） | Lv100までのsoakと複数levelケース |

相手speciesとlevelは固定表だけでなくEXP予測器が選ぶ。相手の技は安全な非攻撃技へfixture化してよいが、その結果を自然初期技受入に使わない。base EXPやgrowth tableを直接書き換えない。

### 必須境界ケース

1. 1level上昇のみ、技・進化なし。
2. 空きslotへのlevel技習得。
3. 4枠満杯からの置換。
4. 技習得拒否。
5. level-up進化。
6. 同じ勝利内で技習得と進化が連続。
7. 進化キャンセルと次levelでの再試行。
8. Lucky Eggなし/ありの同一相手差分。
9. Exp. Shareで非戦闘個体が受け取る経路。直接参加経路とは別受入。
10. 意図的な複数level上昇で中間level技の順序と進化を確認。
11. Lv99→100、さらに1戦してlevel/EXP overflowなし。
12. 技習得・進化後の通常Save、fresh Continue、次の通常戦闘。

Nincada/Shedinja、Tyrogueの能力値分岐、Eeveeの友情・時間帯、性別・フォーム・所持道具等は、現行変更影響台帳に該当する場合だけ独立fixtureを生成する。全1671 ownerを同じsoakで回すのではなく、変更された経路と条件classを網羅する。


しあわせタマゴは現候補のitem manifestからstable key・held-effect ABIを解決し、未所持/所持の同一相手EXP差を先に実測する。解決不能または倍率不一致なら高速soakへ進まず、数値IDを推測しない。

## レーンC: 長時間soak

Axew系を低levelからLv100まで自動連戦させ、10levelごと、全技習得点、全進化点、Lv100でcheckpointを残す。Lucky Eggはbase EXP対照を通過した後だけ使用する。各戦の前後でspecies/form、level、EXP、moves/PP、ability、stats、personality、OT、held item、party order、battle outcome、field復帰を記録する。

一つのprocessで連続実行してよいが、失敗位置を限定できるよう戦闘ごとのcompact ledgerと定期Saveを残す。soak成功をstory自然進行や全species受入へ拡張しない。

## 次の実装単位

1. Save14 artifactとROM/save hashを読戻し、`story-fast.srm` と `progression.srm` を別identityで生成する。
2. stable species/move/item keyを現在のmanifestから再解決し、数値ID・item ABI・自己OT・checksumを検証する。
3. story-fastで自己OT Lv100の服従、1戦勝利、field復帰、通常Save/fresh Continueをsmokeする。
4. progressionで最初の一戦縦切りを行う。現行進化契約で解決したAxew第一進化直前から通常wild EXPで進化し、Save/Continueまで確認する。
5. 3と4が通った後、storyはマオリ勝利まで、progressionはLucky Egg対照・技空きslot/置換/拒否・複数levelへ広げる。

## 完了主張の境界

この計画記録だけではnative process、ROM生成、story勝利、level-up、進化、releaseの新規受入は0。`release_ready=false`、mergeなし、active baseline切替なしを維持する。
