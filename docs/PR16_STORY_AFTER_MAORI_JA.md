# マオリ後の通常進行・アヤメSave17 限定受入

## 完了範囲

`PASS_STORY_AFTER_MAORI_AYAME_SAVE17_SCOPED`。固定Save16から502番道路を通常移動し、ミキとスイの双子戦、ムギヒコ、ブンタの計3戦に勝利。通常ゲートを通過し、アヤメシティのポケモンセンターで通常回復・Save17・独立Continue・手持ちUI確認まで完了した。

自己OT Lv100支援partyのstory-fast限定。自然入手、自然育成、自然難易度、進化、研究施設自然到達、全storyを受入したものではない。NationalDex magic0を保持。flag注入・host書込・ROM変更・compile・旧受入の明示再走0。

## 原本・実測

測定source `0c5a118c855ee52eecbadaa7c4114d32a59e500f`、run `36510782954`、job `109222190727` の全7stepが completed/success。artifact `11008723945` は 18112423bytes、SHA-256 `e78ed5327d55427cca992406d43fa488f92065d11fe0bc0636493a83c97fb4db`、期限 `2026-12-28T02:03:16Z`。manifestと全144memberを照合。ROM/Save/119画像/全Save byte差分はartifactのみ、追跡textは `content/modernization/pr16_story_after_maori_evidence`。

progress317入力・28007frames・116画面、cold22入力・1746frames・3画面。全119画像の形式/全byte SHA/非空を検証し、開発時の直接pixelレビュー31anchorを同一hashの正式画像に結び付けた。双子戦の味方誤攻撃も通常入力のまま保持した。賞金168+108+160=436、所持金2936→3372。新規34試験は開発とActionsで同じ34件を実行した数であり、68別件とは数えない。先行19試験は同一sourceの完了原本を再利用し、再実行0。

3戦はBATTLE開始14/47/69、勝利35/59/80、field解錠39/61/82で判定。ひんしやfieldに残るoutcome1を追加勝利に数えない。map列は3/19→3/20→3/11→3/20→3/1→5/4。保存中113の部分Flash変更を保存完了と混同せず、114/115のcounter17・解錠とcoldで確定した。保存成功文言そのもののframeは未取得。

全Save/RTC131088bytesがcold後も一致。前回bank57344bytes、PC section5〜13、未使用party200bytes、全5Bag pocketを保持。party600bytesの差分は8bytes（友情/PP/通常戦闘EV）。species/EXP/Lv100/状態保持、4体全回復。3trainer flag175/190/702を新ROM ownerと照合し、別flag913は4戦目と数えない。全Save差分6620bytes/1732範囲を再構成一致。一般sector checksum全体の受入は主張しない。

## 失敗も含む実行数

開発native3（保存前の900frame上限違反1、修正後progress1、cold1）。失敗SaveはSave16のまま。修正は600frame上限と起動前の全操作列検査。失敗stdout全73502bytesが正式成功stdoutのprefixと一致し、失敗の再実行はしていない。初期Actionsのfixture転記失敗36507857717と出力directory事前作成衝突36508880929はいずれもnative0で停止し、今回修正済み。正式native2、記録native/compile/受入試験再実行0。既存push CIは専用測定の実行数と分け、全成功とは主張しない。

## 次の唯一のstory-fast開始点

同artifactの `story-fast.srm`（`cold.srm`も全byte同一）。131088bytes、SHA-256 `6bd7a37962e31b3c3c553a882903c766b7146f016cdf00a62036273789ab6f2a`、counter17、map5/4（アヤメシティ・ポケモンセンター）、座標7,4、北向き。party4/RP0。ROMは既存33554432bytes、SHA-256 `06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5` のまま。

story-fastはアヤメシティ通常回復Save17を唯一の開始点とする。artifact11008723945のstory-fast.srmを復元し、map5/4・7,4・北向きのポケモンセンターから通常の出口・町イベントを進める。今回の317/cold22入力・34試験・受入済み19試験・マオリ・旧BP/P08/Save1〜16は影響なしに再走しない。全国図鑑正規解禁へ向けて通常storyを継続し、次の自然保存境界で区切る。progression原本は戦闘前Axew Lv37/EXP68589のまま保持し、NationalDex magic0を注入で解除しない。自然育成/進化、Lucky Egg対照・12成長ケース・Lv100soak・研究施設自然到達・全storyは未完。

非支援Save14・分離progression原本・全国図鑑owner・正式BP/P08受入を変更しない。旧候補や別baselineへ混ぜない。PR16 open/draft/未merge、release=false、active baseline/source-lock不変。source-validationの旧P03 capacity原本段階failureやaction_requiredを本scopeの成功に合算しない。

記録workflow自身のpush/upload終端は自己予測しない。record run `36511503554` をAPIで別照合する。記録commitと全textの読戻し結果はそのartifactの `record-head.txt` / `record.zip` が正本。
