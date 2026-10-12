# アヤメジム・バッジ1・Save19 限定受入

`PASS_AYAME_GYM_BADGE1_SAVE19_SCOPED`。支援story-fastで通常ハヤカ/アマナ2勝、窓のスイッチ、バッジ1、報酬、町のモスギス会話、PC通常回復、Save19と独立Continueを受入。自然難易度・自然育成/進化・全国図鑑・研究施設自然到達・全storyは未受入。

## 原本と検証

測定source `e9c9a55c59705490cd49f834fb8586c41bb1861b`、run `36559147649`、job `109375512907`、upload/postを含む全7step成功。artifact `11028517527`、18664867bytes、SHA256 `d93e36abb202788962f1ddd866189d1a72443efa51102a4b66a197ec0549156a`、期限 `2026-12-28T11:01:14Z`。全264memberと243画像を全byte検証し、35anchorを目視照合。全Save差分6817bytes/1718範囲と保存済みoracle全値が一致。ROM/Save/画像/全差分hexはartifactのみ、tracked text原本は `content/modernization/pr16_story_gym_evidence`。

464/cold34入力、57403/cold2492frames。2戦の開始/勝利/復帰/解錠は16/49/52/52と92/141/152/162。交代UIと残留outcomeを別勝利に数えない。通常賞金336+1500円で3940→5776円。key items347/348/364、TM15=303を追加。他pocket不変。364の個別ownerは未同定のまま、HM05所持は主張しない。通常badge flag2080、trainer physical bits1422/1694、var4071=3→5/4072=0→1をROM rootと保存差分で照合した。

## 保存境界と未受入範囲

観測227/228は書込み途中、229/230はcounter19/field解錠。成功文言frame自体は未採取。独立Continueでmap5/4・7,4北・party4全回復/RP0・5776円・badge1、Save/RTC全131088bytes保持。前bank57344bytes、boxed PC、未使用party200bytesを保持。partyは歩行友情4bytesのみ、EXP/Lv100/種族不変。ROM宣言payload checksum42件と別S61E CRC/反転値、S61E payload差分3bytesを検証。NationalDex magic0/var404e0/flag840=0、分離progression原本とgrant owner不変。

旧hash-only WIP1processは未受入のまま保持。開発成功2process・正式成功2process、同じ73試験を146別件に数えない。記録時は新しい32拒否試験のみ、受入73試験/native/compile/ROM変更/旧区間再走0。一般CIのP03 capacity failureを専用run成功で隠さない。PR16 draft/open/未merge、release/active baseline切替なし。

## 次の唯一の開始点

story-fastの唯一の開始点はartifact11028517527のstory-fast.srm（Save19、131088bytes、SHA256 dd7adddc09555c2232299075bba657e9e7261ad3b868d9cabb5f0edccc8ed06d）。アヤメPC map5/4・7,4北・party4全回復/RP0、badge1・var4071=5/4072=1から通常storyの未完区間だけを進める。ハヤカ/アマナ2勝・通常報酬・モスギス会話・Save19/coldは完了。HM05は未所持で必要なら通常会話で取得する。新464/cold34入力・73試験・旧BP/P08/Save1〜18は無影響に再走しない。分離progression原本Axew Lv37/EXP68589とNationalDex magic0・grant ownerを保全しflag/var注入で解禁しない。正規全国図鑑解禁、自然育成/進化、Lucky Egg対照・12成長ケース・Lv100soak・研究施設自然到達・全storyは未完。

記録source `6b7cbb0b5c133ca505ed5ef29cd6f7e8175c601f`、run `36567761064`。記録workflow自身のpush/upload成功は自己予測せず、別APIとrecord-head.txt/record.zipで読戻し確認する。
