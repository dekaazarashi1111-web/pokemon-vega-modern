# 館の北東階段・初上階Save63限定受入

`PASS_MANSION_UPPER_STAIR_SAVE63_SCOPED`。Save62から新8歩・方向転換2で入口階30,10の階段へ。map1/60・32,10東に初到達、通常保存・独立Continue。戦闘0。像の紙は未到達。

source `a4995895e0933dc8728a53258fed3057b10ba128` / run `37160910114` / job `111313959362`全8step成功。artifact `11287229492` / 134168bytes / SHA256 `d3705b4666e2cdf3e8416a2ed2262d3e9e154a3434d312960bec42e6f9ebd900`。56member/41画面/69+cold13入力。新controller27case、50新受入拒否試験。native2/record0/旧受入再走0/ROM変更0。

## 実階段と保存

0開始、1〜10の間に新8歩・南/東へ転換2。10で30,10階段、11でmap1/60・32,10へ通常warp1回。到着11は「こころのやかた」banner付き。12〜16menu0→4、17確認/18上書き。19〜33保存中、32のFlashは一時的に最終hashと一致、33counter63でも部分write、34〜37成功文言、38field。終端38/cold0/cold1の全画面byte一致、全SaveRTC一致。map名bannerのある11を終端画像と同一扱いしない。

## 保存差分と未完

party全600byte/HP288/294/PP15,10,15,6・ミュウツー全HP/PP・EXP/持物・全Bag/18744円/RP0・PC/S61E全payload・旧Save62bank57344byte保持。physical2056の1→0、aux4021の89→97/4022の0→3だけをlegacy差分として固定。runtime ownerは未解明でstory成功へ昇格しない。RAM台帳は36の保存成功文言中に変化。42checksum/6890byte1674範囲。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達は未受入。Flash未使用/未習得、がくしゅうそうち未装備。

紙までの候補は[Save62時点の静的経路](../content/modernization/pr16_story_save62_evidence/route-plan.json)を再利用。今回だけ北東階段の1接続を実測受入した。上階北部40歩/穴31,21/入口南東階段/紙側の接続は未実測。一般CI既知不一致/action_requiredを成功にしない。

次: Save63 artifact11287229492のstory-fast.srm（131088bytes/SHA256 76dacf781f2e6cf3f44521223cf0c9228e9ca7e04ce26fadeabceba4c1777c87）だけから再開。初上階map1/60・32,10東。新8歩/方向転換2/北東階段30,10→warp2を限定受入し、通常Save63・独立Continue済み。HP288/294・PP15,10,15,6、全party600byte/Bag/18744円/RP0/badge1/story4071=9/4072=1/PC保持。次は保存済route-planの上階32,10→33,10→34,10から31,21の穴へ40歩の未通過接尾辞。最初の新event/戦闘/不通境界で保存。上階北部と紙側は静的非連結で、穴31,21→入口31,22→南東階段30,29→上階33,29→紙背面16,27が未検証候補。紙/穴作動/南東階段は未到達。27新controller/50新受入、69+cold13入力41画面56member/native2。32一時最終Flash、33counter63部分write、34成功→38field。最終field全画面/coldSaveRTC一致。physical2056解除とaux4021:89→97/4022:0→3、RAM台帳は36変化、runtime owner未解明。旧offset41/aux404d/40ac保持。Flash未使用/がくしゅうそうち未装備。受入済み通路/戦闘/保存は無影響再走しない。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。
