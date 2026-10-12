# ミルシティ回復施設への通常到達・Save53限定受入

`PASS_MIRU_HEALING_BUILDING_SAVE53_SCOPED`。ミルシティ28,0南から26歩/3方向転換で38,16へ。通常door38,15からポケモンセンター1F map6/5の7,8北へ入り、Save53と独立Continue全SaveRTC一致を受入。受付との会話と回復は未完。

source `c7a396747031908a74cc8c9a63698e6c513dced8` / run `37148257409` / job `111276541041`全8step成功。artifact `11283178064` / 300967bytes / SHA256 `58c4507d868e77fea5f0f1a28d12f15e61a4e8fd1b08db672b07f1a15fea2670`。75member/60画面/108+cold13入力、20controller原log/39新受入拒否試験。native2/record0/旧入力再走0/ROM変更0。

## Ownerの限定確認

保存済town mapを再利用。最初の候補6/0は回復specialがなく除外。後続6/5でrespawn3、受付local3(7,2)のscript135790449からshared135872070/135872156、命令135872182のspecial0へ到達するgraphを固定。同候補の既存母親heal special0と一致し、画面にもポケモンセンターが表示された。ただし会話/実回復は次。

旧Save52のflag2194はtown load script136400616の命令136400637/setworldmapflagで解決。旧原本の未解明記述は改作せず、後継調査として扱う。aux varsと旧cold RAM差は未解明。

## 保存境界

31で室内field。32〜36通常menu、37確認、38上書き。39〜53は部分write、53でcounter53へ先行、54〜56成功文言、57field。cold0/1同位置。全party600byte/HP/PP/Bag/17040円/RP0/badge1/story4071=9/4072=1/PC/S61E不変。flags変化0、aux4021=84→110/4022=1→2。respawnは[3,1,255,0,16,0,13,0]から[3,2,255,0,38,0,16,0]へ通常更新。旧Save52 bank57344byte保全、42checksum、6989byte/1765範囲。今回progress/cold ledgerはSave52 cold値def3a8d7…から不変。

次: Save53 artifact11283178064のstory-fast.srm（131088bytes/SHA256 e22287b3ef44b53029d855aca7cac243f567af75fce21d557f28294c7f4c9a13）からのみ再開。ミルシティのポケモンセンター1F map6/5・7,8北。通常26歩/入口/Save53/独立Continueを限定受入。party600byte/Bag/17040円/RP0/badge1/story4071=9/4072=1不変。オノノクスHP294/294・PP[11,10,15,14]、ミュウツーHP50/354・PP全0で正常回復が最優先。施設map/warps/owner graphは保存済み。受付local3の7,2、script135790449→135872070→135872156→special0を同一候補で確認。必要な室内経路高度だけ読み、カウンター越しの通常会話/回復へ進む。最初の新event/未通過境界/実回復で通常保存、必須story省略なし。Save52のflag2194 ownerはtown load script136400616の命令136400637/setworldmapflag。既受入の原本を書換えず後継解決として記録。今回var4021=84→110/4022=1→2と旧cold RAM差のowner未解明を保持。今回progress/cold ledgerはdef3a8d727dc95294ed0908fa68914b62022587e25ef55d2fe352a942c1ec502で同一。Save53成功54→field57、counter53だけでは完了判定しない。108+cold13入力60画面20controller39受入75memberを無影響再走0。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完、doubletarget分離native未実証。既存ROM/runtime/input非再配布、host補充/故意全滅/merge/release/baseline切替なし。一般CI既知source不一致/action_requiredを全成功にしない。
