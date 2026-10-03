# ミルシティ通常受付のHP・PP全回復・Save54限定受入

`PASS_MIRU_NORMAL_HEALING_SAVE54_SCOPED`。Save53から室内を北へ4歩、受付前7,4へ移動。カウンター越しに通常A、実画面「あずける」を選択し通常回復、Save54と独立Continue全SaveRTC一致を受入。

source `041077371f32b04015916058fe460e1ade4dd989` / run `37149491580` / job `111280129663`全8step成功。artifact `11283366654` / 239323bytes / SHA256 `6db6c9ef736923cd4c2078aa5b78532d8f12318f35f8c22a816b53ceb5624e6a`。54member/39画面/66+cold13入力、21controller原log/43新受入拒否試験。native2/record0/旧入力再走0/ROM変更0。

## 回復の独立照合

観測5で挨拶、6で「あずける／やめる」、7で預け、8で回復後party、9で挨拶終了、10で操作可能field。既読受付local3(7,2)のscript135790449→shared135872070→135872156、命令135872182のspecial0に対応。host補充なし。

オノノクスHP294/294、PP[11,10,15,14]→[15,10,15,20]。ミュウツーHP50→354/354、PP[0,0,0,0]→[10,20,15,10]。ミュウ342/342、ビーダル300/300、技は空のまま。全600partybyteの差分8byteだけを許可し、残592byteは不変。現候補ROMのpointer0x1cc/stride12/PPoffset4から8技の最大PPを照合。PPbonus0、全員HPとstatusを独立確認。

## 保存境界と未解明範囲

11〜15通常menu、16確認、17上書き。18〜32部分write、32counter54へ先行、33〜35成功文言、36field。cold0/1同位置。Bag/17040円/RP0/badge1/story4071=9/4072=1/全flags/PC/S61E/respawn不変。aux4021=110→114/4022=2→1。旧bank57344byte保全、42checksum、6936byte/1739範囲、全SaveRTC一致。

観測10でRAM台帳がdef3a8d7…から3aef553d…へ変化しcoldまで保持。回復との時間的対応はあるがowner未解明。保存済S61E payloadは不変。旧Save52 cold差/aux ownerも未解明のまま保持。台帳全不変と主張しない。

次: Save54 artifact11283366654のstory-fast.srm（131088bytes/SHA256 bfdd4fb964fd8a3b526b919921b2400e3c1f44c02011208b03f0507606a496ad）だけから再開。ポケモンセンター1F map6/5・7,4北。通常4歩/受付「あずける」/HP・PP全回復/Save54/独立Continueを限定受入。オノノクスHP294/294・PP[15,10,15,20]、ミュウツーHP354/354・PP[10,20,15,10]、空技のミュウ/ビーダルも全HP。party600byte差分は回復8byteだけ。Bag/17040円/RP0/badge1/story4071=9/4072=1/全flags/PC/S61E不変。回復を再実行せず、保存済室内mapとtown ownerから出口→ミルシティの次必須storyを限定調査し通常入力で進める。最初の新event/戦闘/未通過境界で通常保存、必須story省略なし。aux4021=110→114/4022=2→1と回復後RAM台帳3aef553d4f2dba8f52868966ed63e2e315f111535d017321afe1c0df1a7bd384のowner未解明、旧Save52 cold差ownerも未解明。Save54 progress/coldは同一。Save54counter32は書込中、成功33→field36。66+cold13入力39画面21controller43受入54memberを無影響再走0。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完、doubletarget分離native未実証。既存ROM/runtime/input非再配布、host補充/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。
