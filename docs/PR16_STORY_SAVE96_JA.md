# 博物館初下降・Save96限定受入

`PASS_MUSEUM_DESCENT_SAVE96_SCOPED`。封書引渡し後のSave95から、新復路13歩/5旋回で2階11,8へ。西入力で1階6/0・8,8西へ初下降し、最初のfieldで通常Save96、独立Continueを受入。受付/封書会話の再走なし。

source `eea7968c2626dc7cc6746ade93a0c9421a95c395` / run `37192111310` / job `111406308028` 全8step成功。artifact `11299780050` / 211079bytes / SHA256 `015b6c4a6f325e486f503e6e4672324199e3ae89286bf523b6921f939cbd7f8f`。62member/47画面/83+cold13入力。controller40、新独立受入72、成功native2/失敗0/記録native0/ROM変更0/旧受入再走0。

## 記録側のimport修復

初回記録run37192785450/job111408313462はfresh unittest importでRecursionError。71実試験は未実行、loader失敗1、native追加0、正本書込み/commitなし。失敗receipt artifact11300145384を全byte保持し終端もfailureのまま。今回の新受入入口だけで過去module読取用の有限再帰上限1500を設定、上限1検査を追加し72caseを初実行する。旧source/controller/nativeを再走しない。

## 保存境界と全画面

0〜18は13歩/旋回5、19で初下降、20〜24menu0→4、25/26確認、27〜40保存中。39は最終flash hashに一時一致してもcounter95/保存中。40ではcounter96と別hash、41で成功文言と安定finalhash、44でoverlayなしclearfield。hash単独/counter単独の完了判定にしない。

44→cold0/1は202/60pixel、cold間142pixel差。全差分は上端NPC1人の矩形x18..29/y0..22内だけ。主人公/地形保持だが全画面一致とは主張しない。SaveRTC全131088byte、PC/S61E/旧Save95bank57344byte保持。差分7019byte1748範囲、42checksum。

全party600byte/HP277/294/PP3,9,8,2/23114円/紙274=0/4382/4383/4061=1/バッジ2保持。4380未完。今回全RAM台帳保持だがphysical2056:0→1、aux4021:96→109/4022:3→1のruntime owner未解明。過去Save95/94等のownerも未解明のまま。全国図鑑/自然成長進化/全story/releaseは未受入。

## 次

[新復路12歩と博物館退出](../content/modernization/pr16_story_save96_next_route.json)。1階8,8西から13,9の出口へ。13,5受付coordは4061==0だけなので支払済み値1を維持。最初の町fieldで保存。19,25/19,26は静的候補で自動歩行未確認。505道路レンジャーは退出後。

Save96 artifact11299780050のstory-fast.srm（131088bytes/SHA256 1f1d30d7f8261ff8b03f0bf290aaa61d052709b6a0a1c259da13f16895cd4b81）だけから再開。封書引渡し後の新復路13歩/5旋回、西入力で博物館1階6/0・8,8西へ初下降しSave96/独立Continueを受入。次は新復路12歩で出口13,9、最初の町3/2 fieldを保存。町19,25/19,26は静的候補、自動歩行は未確認。受付4061=1のため12/13/14,5の条件4061==0は非発火。封書会話/50円受付/階段/旧入館を再走せず、505道路レンジャーは退出後。紙274=0/4382/4383/未完4380/23114円/バッジ2/全party600byte/HP277/294/PP3,9,8,2保持。今回全RAM台帳保持だがphysical2056:0→1とaux4021:96→109/4022:3→1のruntime owner未解明、過去ownerも未解明。47画面83+cold13入力。39は最終flash hashと一時一致でも保存中/counter95、40別hash/counter96、41成功文言/安定finalhash、44clearfield。cold間142pixel差はNPC1人矩形内、全画面一致とはしない。全SaveRTC/PC/S61E/旧bank保持。controller40/新独立受入72、native2/記録native0/実測失敗0。記録初回はimport再帰上限によるloader1失敗/71実試験未実行、入口1500と新1検査で72case初実行。全国図鑑/自然成長進化/全story/release未受入。ROM/runtime非再配布・host補充・ROM変更・merge/release/baseline変更0。一般CI既知qol_production.c不一致を全成功にしない。
