# アヤメ前提3連戦・ジム入場・Save18 限定受入

`PASS_AYAME_CHAIN_GYM_ENTRY_SAVE18_SCOPED`。固定Save17から通常ジム前会話、カチヌキ3兄弟の3連勝、ジム前NPCの退去、実ジムmap6/2入場、PC通常回復・Save18・独立Continue・手持ちUIまで完了。ジムリーダー/バッジ、自然育成/進化/自然難易度/全国図鑑/研究施設自然到達/全storyは未受入。

## 原本・実測

測定source `2577d253823bdca94bf3dfac0a67dea9776a6d8a`、run `36522150353`、job `109257152262` 全7step completed/success。artifact `11012768108`、18101058bytes、SHA256 `4e7a2e5d25dbf01284fdd992327971b7a0d84df2e86022ea6cefc685b2dd064b`、期限 `2026-12-28T04:33:24Z`。全170member hashと全Save差分6731bytes/1740範囲を再構成照合。ROM/Save/全145画像/全差分はartifactのみ。tracked text原本は `content/modernization/pr16_story_ayame_gate_evidence`。

381/cold23入力、36244/cold1714frames。全145画像hash/形式検証、開発時の30pixelレビューanchorを正式同一画像に結合。キミカ200円・コウタ176円・カナコ192円、所持金3372→3940。BATTLE開始37/62/86、勝利55/78/109、field復帰58/81/112、連戦全体解錠115。中間lock1を許容し、交代UI46・KO・残留outcome1を別勝利に数えない。初回の条件未成立の上階訪問も元の入力どおり保持。

map22/1の通常条件eventはvar0x4071=2から発火し、root138585288がtrainer1/1200/1203を参照、終了時stage3を書込む。別のobject会話trainer557/558/559と混同しない。ジムobject1の通常scriptでflag4355をsetし、実際の入場観測123を照合。元ROMの変更やflag注入なし。

## 保存境界・保持

観測138はcounter17/lock1の書込中、139はcounter18/lock0の完了。成功文言frameそのものは未採取。独立Continueではcounter18・party4・RP0・全回復の手持ちUIとfieldを確認し、Save/RTC全131088bytes保持。前Save17 bank57344bytes、PC sections5〜12とchunk13 boxed payload2000bytes、unused party200bytes、Bag5pocketを保持。party変更は歩行友情2bytesだけ。chunk13+0x7d0のS61E拡張recordはCRC32/反転値を検証し、payload offset256の3→11（gym flag4355 bit3）だけが変化。他expanded flags/vars/ball/coinsは保持。一般sector checksum全体を追加受入したものではない。

chain helperのsave_acceptance_claimed=falseは連戦だけではSaveを受入しない意味で原本に残す。別completion/byte/cold/Actions gateを全通過したSave18の受入はcheckpoint最上位のsave18_accepted=true。

## 失敗と実行会計

開発harnessを保存途中で早期quitした1processと、その部分Saveから古いSave17へfallbackした診断cold1processは失敗として保持。未受入新区間だけを1回再実行し、全失敗観測prefix95617bytesを一致させた上で600frame待機を追加した。失敗stdout95806bytesは正式prefix+既知終端から元hash一致でlossless再構成したtextを保存。失敗を成功扱いにしない。開発native4（失敗2+成功2）、正式native2、記録native/compile/受入試験再実行0。新規55試験は開発/Actionsで同じ55件、110別件ではない。

旧未保存WIP c0e9970のHM05受領/野生逃走は今回のSaveに含まれず、Bagは不変。旧317/cold22入力・34/19試験・BP/P08/Save1〜17の明示再走0。PR CIの既存P03 capacity failure/action_requiredを専用成功へ合算しない。PR16 draft/open/未merge、release=false、active baseline/source-lock・分離progression原本・全国図鑑owner不変。

## 次の唯一のstory-fast開始点

story-fastの唯一の開始点はartifact11012768108のstory-fast.srm（Save18、131088bytes、SHA256 dc1f690f0616affc61b6d45632924e4c81995c91c7c1939994f37bbe8527432d）。アヤメPC map5/4・7,4・北向き・party4全回復/RP0から、通常出口→入場可能になったアヤメジムの未完storyを進める。ジムリーダー勝利/バッジはまだ未受入。旧未保存WIPのHM05はこのSaveには無く、必要時は通常会話で取得する。新381/cold23入力・55試験・旧BP/P08/Save1〜17を無影響に再走しない。分離progression原本Axew Lv37/EXP68589、NationalDex magic0とownerを保全し、flag/var注入で解禁しない。正規全国図鑑解禁、自然育成/進化、Lucky Egg対照・12成長ケース・Lv100soak・研究施設自然到達・全storyは未完。

記録workflow source `2e88af576e6c72b621b7ad221930e4f611c04e2a`、run `36523214697` のpush/upload終端は自己予測しない。別API照合し、artifactのrecord-head.txtとrecord.zipで全text読戻しを確定する。
