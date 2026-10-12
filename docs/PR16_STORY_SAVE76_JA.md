# 封書のbadge gate・新ミルジム入口Save76限定受入

`PASS_LETTER_GATE_GYM_ENTRY_SAVE76_SCOPED`。町15,20南から東5歩/北9歩/北扉への通常入力でミルジムmap10/16・6,18北へ到着。旋回2回。自動北1歩はなし。初入場で通常Save76/独立Continue、新戦闘0。

source `3f7692f280ac745d17f810bb9c46abed5324c789` / run `37171285056` / job `111344567528`全8step成功。artifact `11291861689` / 200160bytes / SHA256 `4d00a7de3010a72f5ecdb55f75ee1c4d0163ad6fb7b2ed4f57674648bb2f66f3`。58member/43画面/77+cold13入力。新controller28/新受入50。native2/record0/旧成功再走0/ROM変更0。

## 封書の正規consumerと前提

[保存済みconsumer](../content/modernization/pr16_story_save76_preparation.json)。博物館2階map6/1・local2/4,9、root0x08e1c302。badge0x823がなければ「ミルジムのナギナタさんを倒せないようでは」と断る。badge確認後のcheckitem274→removeitem274→flag4382。flag4383は像からの取得側。引渡し後の案内は505番道路のポケモンレンジャー。現badge1/0x823未set、引渡しは未実行。

受取人不明のため、既読graph116nodeと町直結ownerを再利用しても見つからず、原425mapのROM-rooted参照indexを読取専用で採取した。旧43group pointerは現relocation先と同一。9decoder診断/不正rootを保持し、全graph完全性は主張しない。今回の陽性consumer/leader151命令と11文字列だけを同一ROMで固定し、native検査時に全命令byteを照合。全ROMのbyte pattern searchなし。今後は保存済みownerを使用し全域再採取しない。

## 実入力・保存

1東旋回/7北旋回、17北扉中→18ジム6,18北。19〜23menu0→4、24確認/25上書き。26〜35保存中、34最終hash先行/counter75、35counter76でも別一時hash/未完、36〜39成功、40field。全SaveRTCとprogress40/cold0/cold1全pixel一致。

全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/flag4383/PC/S61E/全RAM台帳保持。physical2056:0→1、aux4021:71→85/4022:3→2/404d:44→33。runtime owner未解明。42checksum/6985byte1743範囲、旧Save75bank57344byte保持。

## 次

[初ディグダownerと北3歩](../content/modernization/pr16_story_save76_gym_route.json)。実到着6,18から先だけ。旧館内/町歩行/ジム入場を再走しない。

Save76 artifact11291861689のstory-fast.srm（131088bytes/SHA256 10c7d4b96e2b36db13158ba3a8d8929caabac28275e98e01a93c586b0315d836）だけから再開。紙274のconsumerは博物館2階map6/1・local2/4,9、badge0x823確認後check/removeitem274→flag4382。現badge1/0x823未setで引渡し未解禁。先にナギナタのミルジム10/16へ新通常入場、6,18北でSave76/独立Continueを受入。次は保存済gym-owner/routeから初ディグダlocal5/6,14の初期4372〜4378と台詞/配置変更を照合し、6,15まで新北3歩＋通常A。最初の新event/battleで通常保存。紙1個/flag4383・全party600byte/HP288/294・PP9,10,15,2/Bag19416円/PC/S61E/全RAM台帳保持。28新controller/50新受入、77+cold13入力43画面58member/native2。34最終hash先行counter75→35counter76/別一時hashでも保存中→36成功→40field。全SaveRTC/ジムfield全pixel一致。physical2056:0→1/aux4021:71→85/4022:3→2/404d:44→33のruntime owner未解明。ジム攻略後に博物館研究者へ紙引渡し→505道路レンジャー。紙引渡し/ジム攻略/全story/全国図鑑/自然成長・進化/LuckyEgg/研究施設自然到達未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/既存ROMruntimeinput再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
