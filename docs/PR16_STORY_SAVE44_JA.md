# 通常Bag確認・控え先頭交代・Save44 限定受入

`PASS_NORMAL_PARTY_REORDER_SAVE44_SCOPED`。504番道路39,12西の同じ場所で、バッグの道具ポケットが空なのを確認し、既存オノノクスを通常「ならびかえ」で先頭へ。通常Save44と独立Continueを限定受入。PP回復と通常回復地点到達は未完。

source `aaf2d62ce3166349714eeeaff04e5f7ec630c3b1` / run `37135192951` / job `111238199087` 全8step成功。artifact `11278342404` / 326897bytes / SHA256 `c784ec6dfa7e27a489d5b837a8b2a632af12a46c65d3eb88214d94e7ad29fb21`。全60member/45画面/78+cold13入力。16controller成功原logを継承、新32原本受入/拒否試験だけ。native2/record0/旧受入再走0/ROM変更0。

4は道具が「とじる」だけ、5大切なものはタウンマップ/わざメモリー/せいたいレーダー/わざマシンケース、6はモンスターボール3個。9〜15通常手持ち/ならびかえでオノノクス先頭。全party600byteは100byte個体2体の順番交換だけ。オノノクスHP294/294・PP[15,10,15,20]、ミュウツーHP314/354・PP[0,0,0,0]を保持。費用0・道具消費0・戦闘0・移動0。控えの既存PPと主力のPP回復を混同しない。

16menu→17field、18〜21実menu cursor1→4。24〜37部分write14状態。37はcounter44だが書込み中で最終Flashではない。38〜41成功文言/安定全Flash、42field。cold0/1は39,12西。全45画面を目視。

全Bag/14264円/全legacy flags・vars/PC/S61E/story4071=9/4072=1/badge1不変。42sector checksum/旧Save43bank57344byte/6885byte1708範囲/cold全SaveRTC一致。RAM ledgerは13のならびかえ選択で変化し、保存最終/cold `4bc47968c1071a65f115cc64d8aa48dc2a37fcf75718360dd375f3dc7e8dfa0a` 一致。変更ownerの断定はしない。Save39旧cold差owner未解明も保持。

保存済み504地形1440cellは再採取0。南側接続map3/23の静的headerだけを追加読取し、そこから3/2への接続候補を記録。いずれも通常到達/回復受入ではない。

## 次checkpoint送信前の確認

新counterのAST/import/CP/GUIDE/EVIDENCE/VISUAL/OUT/CODE/workflow名を大小文字別に照合。新counter ORIGINAL/ROMと親counter INPUTのenv集合、親artifact/run/source/save SHA/counter/bank世代/全member数を原本と照合。送信treeとstaged一覧を明示し、旧正本と交差0を確認。専用宛先/private/source guardを維持。unittestはreturncode/全成功行/正確な終端で判定し、試験名内skipped等へのsubstring判定を禁止。成功試験は記録器だけの失敗で再走しない。

次: Save44 artifact11278342404のstory-fast.srm（c7a27be2dbcedecccc139899210415d391ee1946a70894836f80603d7cd86d1b、131088bytes）だけから再開。map3/44・39,12西/上段elevation4・party4/RP0・14264円・badge1・story4071=9/4072=1。バッグの道具/きのみは空。通常ならびかえで既存オノノクスを先頭へ移しHP294/294・PP[15,10,15,20]、ミュウツーは2番目HP314/354・PP[0,0,0,0]のまま。回復済みとは扱わない。費用/道具消費/移動/戦闘0、個体全byte不変。次はこの戦力で通常回復地点へ向かう。保存済み1440地形から39,12→38,12→37,12→37,13を経て西上段、26,10→26,11下り階段→26,12下段を有限候補にする。最初の新戦闘/event/未通過境界で通常Save。主力変更に合わせて既存PPと新実cursorを照合し通常技を選ぶ。未到達南map3/23から3/2へつながる静的候補を今回追加したが回復施設の位置/到達は未受入。Bagキー品わざメモリー/せいたいレーダーをPP回復品と誤認しない。host補充/ROM編集/故意の全滅なし。全45画面・78+cold13入力・16controller32受入試験を無影響再走しない。counter44は37だが部分write、38成功文言/安定Flash→42field。全SaveRTC/cold RAM ledger一致。並替選択13のRAM ledger変化ownerは未解明、全保存legacy flags/vars/PC/S61E不変。Save39旧差・Save40/41/42失敗回収履歴を保持。通常story/正規全国図鑑/自然EXP・技習得・進化/Lucky Egg/12ケース/Lv100soak/研究施設自然到達未完。全story/一般CI全成功/製品release未完、cleanROM二重生成/BPS固定/merge/release/baseline切替は別途所有者判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。
