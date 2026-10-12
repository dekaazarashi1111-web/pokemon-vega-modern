# こころのやかた通常入館・新廊下・Save56限定受入

`PASS_HEART_MANSION_ENTRY_SAVE56_SCOPED`。Save55の16,20南から通常西1歩/北doorへ1歩、暗い館map1/59の20,33へ入館。通常北8歩で20,25北。次階層warp20,24へ踏み込まずSave56と独立Continueを受入。戦闘/会話/新item/Flash0、像の裏の紙は未調査。

source `e622b26e0c00a1572e4d879c7ea0bb5c17ed0c01` / run `37152942259` / job `111290374509`全8step成功。artifact `11284293358` / 137517bytes / SHA256 `4038800d9f5a1a74ad338b368bb51481b82bd9b58ac848046a30152586029a80`。57member/41画面/70+cold13入力。controller23case（初回22、影響2+新規1の計25実行。未影響20件は原log継承）、65新受入拒否試験。成功native2/失敗native1/record0/旧受入再走0/ROM変更0。

## 実測入口での訂正

初回run37152779196/source5bad5bee97dc0059e901984c7f35d936e65c0351/job111289893097/artifact11285040773は、warp後に1歩自動で進むという推測20,32をguardが拒否。実際は20,33出口arrowの上でfield復帰。21入力/6画面/native1、Save55全byte不変、未保存。原本を改作せずartifact全13memberと終了receiptを照合し、実観測から1tileだけ訂正。受入済み回復・レンジャー区間は再生していない。

記録run37153604849は旧Save40 parserのcamera例外を継承したため館warp一時live0を拒否。新試験0/native0で停止。専用parserの実観測4だけを限定許容し、追加19拒否/原本検査を実装。旧parserは変更しない。

## 画面と保存

0〜3town/向き、4warp transition、5入館、6〜13新廊下。14〜18menu0→4、19確認/20上書き、21〜34保存中。32/33は最終Flash hashと同じでもcounter55かつ保存中、34はcounter56でも一度別hash。35〜37成功文言、38field。hash一致やcounterだけで完了としない。cold0/1は120frame後も全SaveRTC・暗所の人物/可視範囲を含む画面byteがprogress38と一致。

## 限定差分

party600byte/HP/PP/全Bag/17904円/RP0を保持。legacy2056と2221だけ新set。2221は館map-script3のsetworldmapflag（142978050）と照合。2056runtime ownerは未解明。4021=16→25/4022=0→4/404d=21→44のownerも未解明。story4071=9/4072=1、40ac=16、badge1/全国図鑑未解禁。PC/S61E全payloadと旧Save55bank57344byte保持、42checksum/6874byte1708範囲。

未読17node/1330cell/1mapの静的採取はnative到達と分離。任意TM21民家へ入らず、がくしゅうそうちを装備せず、回復せず。紙が入口階の既読会話/背景eventにないことだけを確認し、次は隣接階の必要箇所へ。

次: Save56 artifact11284293358のstory-fast.srm（131088bytes/SHA256 cf11b02c2152e238bf0f56fd2dadc3b30038ea6c45b105ca616ad4dc2ce93386）だけから再開。map1/59・20,25北、こころのやかた入口階の未読階層手前。通常入館2歩/warpと館内8歩/戦闘0/Save56/独立Continueを限定受入。party600byteとHP288/294・PP[15,10,15,14]、ミュウツー全HP/PP、Bag/17904円/RP0/badge1/story4071=9/4072=1保持。次は北20,24の既読warp8→map1/60・warp5。未読map1/60と必要owner/最小地形を限定調査し、NPC依頼「奥のどうぞうの裏の紙」を目標に最初の新event/戦闘/未通過境界まで通常入力で進める。紙は未調査、Flash未使用/未習得、がくしゅうそうち未装備。2056flagのruntime ownerとaux4021/4022/404d未解明、2221は館map3 script setworldmapflag照合。過去RAM台帳/仲間offset41/40ac=16のowner未解明も保持。Save56のRAM台帳は全観測/cold77ccaa1d7ceee4a641d1094ab5b8f5caf44668ea125287542f3e2bed65a80e57。32/33最終似hashでも旧counter55/保存中→34counter56でhash再変化→35成功→38fieldを区別。70+cold13入力41画面57member/65新受入を無影響再走しない。初回20,32推測は実20,33で未保存停止した21入力6画面/native1を原本保持し、3影響試験だけ訂正。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CIの既知不一致とaction_requiredを全成功にしない。
