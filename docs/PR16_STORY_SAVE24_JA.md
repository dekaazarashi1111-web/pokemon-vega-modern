# 洞窟東通路31,4・Save24 限定受入

`PASS_EAST_CORRIDOR_SAVE24_PERSISTENCE_SCOPED`。Save23から東11歩/南1歩で31,4南へ進み、通常Save24と独立Continueを受入。新戦闘0、teleport/洞窟走破は未達。

## 実測と原本

source `d983562695f17ecac20e1ede1a6916dc04392468`、run `37093559410`、job `111118784339` は全8step completed/success。artifact `11263343138`、17559812bytes、archive SHA256 `6a0cff0cd7a5d4118fd090bd8588c9076f1525d689b7e53802cbea9bbe9d49b0`。47member全byte、進行56入力2782frames/cold13入力1510frames、22画面を検査。保存成功文言だけのanchorは採取しておらず、通常Save UI→安定field/counter24→独立Continueでの全Save/RTC保持を根拠にする。

Save24 SHA256 `42a5fd672e8be714d40720a9fa4fece27e53293c0b0ca49a2ed0696e206455a0`、131088bytes。全party600bytes、Bag/HM05、12296円、旧Save23 bank57344bytes、PC/S61E、全国図鑑magic0/404e0/flag8400、story4071=6/4072=1は不変。全stock checksum42/S61E CRCを確認。補助flags差分0、4021:26→38/4022:1→3だけ。6937byte/1754範囲の差分hexはartifactのみ。

## 失敗は保全し、静的候補を可達性へ昇格しない

run37092974275/source85e1e7d2/artifact11263731555はfailure。36入力1870frames・native1で27,4南まで進み、27,5への3試行が同位置。Save23全byte不変、Save24未作成。旧11歩候補は高さ3→4かつ北側進入不可behavior0x32を無視していた。ROM修正は不要と判断し同方向を反復しない。失敗で未保存のため当回は唯一のSave23から再開し、受入済み区間の再実行とはしない。

run37093437062/source45ccca9b/artifact11263278045は砂床0x2bをfloor whitelistに含め忘れた事前検査failure、native0。walk/save sourceと12試験は不変で成功原本を再利用し、7地形試験だけ追加。前段32/12/7試験も当記録で再実行0、新24受入/拒否試験のみ。古い4root/5node静的監査と全11step成功も継承。

地形名照合の一次資料: https://github.com/pret/pokefirered/blob/master/include/constants/metatile_behaviors.h 。固定ROMで0x2b砂床/0x32北側不可/0x2a岩階段を照合。ROMの同定とnative停止を根拠にし、参照資料だけでVega全体の挙動を保証しない。

## 次の未完工程

Save24 artifact11263343138のstory-fast.srm（42a5fd672e8be714d40720a9fa4fece27e53293c0b0ca49a2ed0696e206455a0、131088bytes）だけから再開。map1/73・31,4南・party4/RP0・12296円・badge1・var4071=6/4072=1。次は東側通路を南へ通常入力で進み、NPC/野生戦は通常UIで対処し次のSave/独立Continue境界へ。27,4→27,5は高さ3→4/北側進入不可なので旧11歩候補を再試行しない。岩階段23,14へ回り込む候補は未実測、19,14のcoordはflag4367で27,7/8,10へ分岐する。静的座標ownerは再利用し、敵trainer/script/進路と手持ちPPを保存候補から照合して入力を計画する。当回56/cold13入力・32+12+7/新24試験・Save1〜23/旧BP/P08は無影響に再走しない。teleport/洞窟走破/HM05原因/全国図鑑/自然成長進化/全storyは未完。hostによるstory/flag/var解禁禁止。

record source `1a842ee45ca361522fd4e6f6cee766df6534428e` / run `37094105840`。record自身のpush/upload/postは後続外部APIで確認。merge/release/active baseline変更なし。
