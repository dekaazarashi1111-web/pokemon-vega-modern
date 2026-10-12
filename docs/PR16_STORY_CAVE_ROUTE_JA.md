# Save23後の洞窟座標teleport — 静的owner限定照合

`PASS_CAVE_COORDINATE_ROUTE_OWNER_STATIC_ONLY`。新しいnative入力は0。Save23受入記録run37091670533/job111113139437の全11step成功と反映HEAD `46cbf4bc3e2d303c7178377e3882ecc874dba8ed` を外部APIで確認。

## 次の縦切り

既存のmap1/73衝突gridを再利用。Save23の20,3から東7歩/南4歩で27,7へ進む静的候補は11歩。通過するcoord eventは終点の1件だけ。実field通行・elevation4・VarGet条件の発火は未受入であり、衝突gridだけで出口への経路が見つからないことをバグとはしない。

map header→coord表の11件を限定読取。coord1=27,7/elevation4/var4000=0、root0x0821468Aのlock→warpteleport map1/73・19,14→release→endを確認。coord2=8,10は27,7へ戻る別root。coord0=19,14はflag4367の分岐を持つ。coord3〜8=11〜16,14・var4071=6にはflag4367/setvar4071=7があり、これは未実行の後続story owner。4root/5nodeにdecode診断0。reserved coord10のscript0はrootにしない。

固定Save23のbacking stateはvar4000=0/4071=6、拡張flag4354=0/4366=1/4367=0/4368=0/4369=0。ROM/Saveを変更せず、実runtimeのgate解禁や次teleport成功へ昇格しない。橋の見た目や全出口到達性の受入でもない。

## 再開と制限

Save23 artifact11261539316のstory-fast.srm（SHA256 728bd39b11ea53bafd31cff5fb50e7f81fe5973c0c5fae559ea22037827832bb、131088bytes）からだけ再開。map1/73・20,3東から通常入力で東7歩/南4歩の座標27,7へ進み、正規coord scriptの19,14へのteleportを新規実測する。elevation4/var4000=0のruntime発火は未受入。道中に野生戦が起きたら通常UIで対処し、host-writeやflag注入は使わない。到達後は通常Saveと独立Continueで区切る。座標trigger・静的11歩・4root/5nodeは保存済み監査を再利用。Save23までの45/cold13入力、24受入試験、旧Save1〜22/BP/P08は無影響に再走しない。27,7/19,14のteleport実到達、洞窟走破、HM05解決、全国図鑑、自然育成/進化、全storyは未完。

source `d9435a2d4af239ba25e262722bd52d8814a6bf86`、run `37092347183`。本記録のpush/upload/postは外部APIで別途確認する。merge/release/active baseline変更なし。
