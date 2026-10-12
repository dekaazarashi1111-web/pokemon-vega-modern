# 博物館入場・Save92限定受入

`PASS_MUSEUM_ENTRY_SAVE92_SCOPED`。Save91/20,11南から新23歩・旋回3・warp1。26で町19,25の入口遷移、27で博物館1階6/0・14,9北へ到着。自動北1歩は起きない。到着直後の通常Save92/独立Continueを受入。バッジ2・紙274一個・23164円、全party600byte/HP277/PP3,9,8,2を保持。2階到達/紙引渡しは未実行。

source `afe866267733b0b48d0f971f52b971d03aa6f2bc` / run `37187019619` / job `111390998562` 全8step成功。artifact `11297164221` / 263493bytes / SHA256 `c2597abb5dac65d37d1011066547495d5fac963ea76275186100d2f48f2184e9`。70member/55画面/98+cold13入力。controller36と独立受入63。native2/記録native0/旧受入再走0/ROM変更0。

## 保存と差分

28〜32menu0→4、33/34確認、35〜47保存中。46/47は同じ途中hashでもcounter91/保存中文字。48最終hash/counter92/成功文言、52field。全131088byteSaveRTCと全38400pixelが独立Continue/120frame後も一致。安定hash/counter単独で完了としない。

全party600byte/HP277/294/PP3,9,8,2/Bag/紙/23164円/PC/S61E全payload保持。42checksum、全Save7105byte/1806範囲、旧Save91bank57344byte保持。町20,16の観測5でprogress RAM ledger差分が発生。coldは新ledger保持。physical2056:0→1、legacy4021:49→71/4022:1→3/404d:33→7。このruntime ownerと過去Save91の5vars/Save89RAM14/Save87raw41/RAM等のownerは未解明。現在差分を過去ownerの解決と混同しない。

## 次

[2階への新13歩](../content/modernization/pr16_story_save92_next_route.json)。14,9北から北4西6南3で階段8,8へ、最初の2階map6/1到着後だけ保存。静的target11,8/自動歩行はnative未確認。local2への封書引渡しはさらに後続の別区間。

Save92 artifact11297164221のstory-fast.srm（131088bytes/SHA256 79864ff24d80a3b1cee73166bffb95f5795e2450f54582bad67ac6c024e2f9bf）だけから再開。新23歩/旋回3/warp1で博物館1階6/0・14,9北、通常保存/独立Continueを完了。自動北1歩は起きず14,9が実到着。次は北4西6南3の新13歩で階段8,8へ、最初の2階6/1到着直後だけ保存。静的target11,8/自動歩行はnative未確認。2階local2への紙引渡しはさらに別区間。紙274一個/4383/未引渡し4382/バッジ2/23164円/全party600byte/HP277/294/PP3,9,8,2保持。町20,16の観測5でprogress RAM差分、coldは新ledger保持。physical2056:0→1とlegacy4021:49→71/4022:1→3/404d:33→7のowner未解明。過去Save91の5vars/Save89RAM14/Save87raw41等も未解明のまま。全55画面/98+cold13入力/native2/新controller36/新受入63、旧受入再走0。35〜47保存中、46/47途中同hashでもcounter91/保存中文字、48最終hash/counter92/成功文言→52field。全SaveRTC/全38400pixel一致、S61E全payload保持。がくしゅうそうち未装備、Flash未使用、紙引渡し/全国図鑑/自然成長進化/全story/release未受入。入力ROM/runtime再配布・host補充・ROM変更・merge/release/baseline変更0。一般CI既知qol_production.c不一致を全成功にしない。
