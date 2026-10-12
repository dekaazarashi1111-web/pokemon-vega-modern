# story-fast マオリ勝利・Save16の限定受入

## 完了した範囲

`PASS_STORY_FAST_MAORI_SAVE16_SCOPED`。自己OT Lv100支援partyで、通常の道路移動からじゅくがえりマオリに1勝し、通常Save counter15→16、独立Continueと戦闘後会話まで完了した。自然入手・自然育成・自然難易度・進化・全storyの受入ではない。

マオリのパモ♀Lv4、パピモッチ♀Lv6、コフキムシ♂Lv8にサイコブレイク3回。賞金160円、所持金2776→2936。途中の野生エネコ♀Lv2は通常逃走1回であり勝利ではない。捕獲・敗北0。相手ひんし32は勝利終端ではなく、outcome33→field36で1勝だけを計上する。fieldに残るflags12/outcome1を再戦と数えない。

## 固定原本と検証

測定source `383ce0f49f4761f6db875e1a2f0a89692d2966e8`、run `36504040292`、job `109201289995` は全8step completed/success。artifact `11006311891` (`pr16-story-fast-maori-checkpoint`) は17717828bytes、SHA-256 `304cae07573563abfb93e4bd7f1bfd5bc7e8348b374380fa487ffe20fd382d1d`、期限2026-12-28。73 member hashとmanifestを照合。ROM/save/runner/48画像/全Save byte差分はartifactだけに保管し、tracked textは `content/modernization/pr16_story_fast_maori_evidence` に限定する。

ROMは33554432bytes、SHA-256 `06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5`。旧Wiki候補46487d98…ではない。開発2process、正式2process（progress176入力15106frames、cold20入力1848frames）。7 host-write barrier、host書込/fixture呼出/警告0。開発44試験・正式44試験は同じ新規44件を別環境で実行した数であり、88別件とは数えない。記録時の追加native/compile/受入試験再実行は0。

全600partybytesではPP offset52の9→6と徒歩友情 offset141の35→36だけが変化。species/EXP/Lv100/status、未使用party200bytes、全5Bag pocket、PC sector5〜13と預けた元2匹は保持。前回保存bank57344bytes不変。全Save差分6418bytes/1757範囲を再構成一致し、byte台帳185286bytesのSHA-256は `c55298c9c21b3eb989e294f353121e184b5b5e53f9e375856373ef9b374f421d`。一般sector checksum対応全体は主張しない。

## 次回の唯一のstory-fast開始点

同artifactの `story-fast.srm`（`cold.srm`も全byte同一）は131088bytes、SHA-256 `5c4a03b9d92f7be54250d565162b03b5b85a2f221c3873d26d894b74b76778ce`、counter16。保存位置map3/19（501番道路）、座標53,10、北向き。独立Continueで全Save/RTC131088bytes、party600bytes、研究ledger/RP0を保持。マオリ再会話は戦闘後台詞となり再戦しない。

Save成功文そのもののframeは未取得。obs41は書込中、42がcounter16/field復帰であり、この区別と独立Continueで保存を証明する。obs14は逃走後の全暗転frameで、成功画面ではない。48画像は直接pixel目視し、同一hashの正式原本へ結び付けた。画像名だけで文言を創作しない。

## 未完と禁止事項

マオリ通常勝利・story-fast Save16・独立Continueは受入済み。次はartifact11006311891のstory-fast.srm（map3/19、53,10、北向き）から先へ進む。176/cold20入力とSave1〜14・分離smokeを再生しない。progression.srmは元の戦闘前Axew Lv37/EXP68589を保持。全国図鑑の正規解禁ownerと進化gateを照合し、自然解禁境界または影響台帳付きsource修正/後継候補へ進む。flag注入で進化成功扱いしない。Lucky Egg対照・12成長ケース・Lv100soak・研究施設自然到達・全storyは未完。

元の非支援Save14と分離済みprogression原本は保全した。全国図鑑magic0のままで、Axew進化成功へ読み替えない。最新の成長・進化・Lucky Egg受入状態は分離checkpointを参照。旧BP/P08/一般CIのfailure・action_requiredは本scope成功へ統合せず、Stage62 active baseline、source-lock、原本、PR draft/open/未merge、release=falseを維持する。

記録workflow自身のpush/upload終端は自己予測せず、別API照合で確認する。記録commitはbranch履歴と記録artifactの `record-head.txt` が正本。
