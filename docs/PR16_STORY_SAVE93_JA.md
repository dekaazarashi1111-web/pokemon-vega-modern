# 博物館50円受付・Save93限定受入

`PASS_MUSEUM_ADMISSION_SAVE93_SCOPED`。Save92/14,9北から新北4歩、14,5で自動受付。4で50円説明/東向き、5は実はいcursor、6で50円受領/23114円、7field。到着直後の通常Save93/独立Continueを受入。バッジ2・紙274一個・全party600byte/HP277/PP3,9,8,2を保持。2階到達/紙引渡しは未実行。

source `2718151982e8cdd82768c720b05c852ccdbb7d1b` / run `37188523239` / job `111395599488` 全8step成功。artifact `11298425525` / 203718bytes / SHA256 `99507ee5a36eff68e1e85dab0e31edf9b90a7cfa9c5dd089f849be685b91f08a`。52member/36画面/60+cold13入力。原controller38を再走せず保持、新影響controller15、新独立受入63。成功native2/初回未保存失敗native1/記録native0/旧受入再走0/ROM変更0。

## 未知受付での初回安全停止

初回run37188126911/job111394391365/artifact11298047173はfailureのまま保持。最初の北4歩、14,5のcoord event/var4061=0による受付を計画が未登録だった。20入力5画面/native1、通常保存0、全Save92/RTC保持。ROM-rootedのcoord3件と今回root7node/56命令を照合し、新しい50円受付だけに縮小。原script/test/preparationは改作せず、別admission controllerを作成。旧受入区間の再走ではない。

## 保存と差分

8〜12menu0→4、13/14確認、15〜29保存中。28は最終hashが一度現れてもcounter92/保存中文字。29counter93で別hash、30成功文言と最終hash→33field。全131088byteSaveRTCと全38400pixelが独立Continue/120frame後も一致。hash/counter単独で完了としない。

全party600byte/HP277/294/PP3,9,8,2/Bag/紙/PC/S61E/今回全RAM/legacy flags保持。所持金23164→23114、受付scriptのremove-money50と一致。4001:0→2はcoord位置分岐、4061:0→1は受付完了の実命令へbinding。4021:71→74/4022:3→1はowner未解明。42checksum、全Save7046byte/1785範囲、旧Save92bank57344byte保持。過去Save92のRAM/2056/3vars、Save91/89/87等の未解明差分は今回不変と混同しない。

## 次

[支払済み状態から2階への新9歩](../content/modernization/pr16_story_save93_next_route.json)。14,5東から西6南3で階段8,8へ。12/13/14,5のcoordは4061==0条件、現在1なので受付を再入力しない。最初の2階6/1到着後だけ保存。実到着/自動歩行は未確認。local2紙引渡しはさらに別区間。

Save93 artifact11298425525のstory-fast.srm（131088bytes/SHA256 93cdaccd2cd5cb969a9d4bc78187b25b62fd0f9b05924f2c2bd0ad26ed73d255）だけから再開。博物館1階6/0・14,5東、通常50円受付/Save93/独立Continueを完了。所持金23114円、var4061=1。次は西6南3の新9歩で階段8,8へ、最初の2階6/1到着直後だけ保存。到着はwarp11,8と通行可能な隣接11,7/11,9/12,8のいずれか、実到着/自動歩行未確認。旧北4歩/受付を再走しない。local2への紙引渡しは後続別区間。紙274一個/4383/未引渡し4382/バッジ2/全party600byte/HP277/294/PP3,9,8,2保持。今回全RAM/legacy flags/S61E/PC保持。4001:0→2と4061:0→1は受付ROM ownerと一致、4021:71→74/4022:3→1のowner未解明。過去Save92RAM観測5/2056/3vars、Save91の5vars/Save89RAM14/Save87raw41等は未解明のまま。全36画面/60+cold13入力、成功native2と初回未保存失敗native1。原38controllerと新影響15、新受入63、旧成功再走0。28最終hash先行でも保存中/counter92→29counter93別hash→30成功文言/最終hash→33field。全SaveRTC/全38400pixel一致。2階/紙引渡し/全国図鑑/自然成長進化/全story/release未受入。入力ROM/runtime非再配布・host補充・ROM変更・merge/release/baseline変更0。一般CI既知qol_production.c不一致を全成功にしない。
