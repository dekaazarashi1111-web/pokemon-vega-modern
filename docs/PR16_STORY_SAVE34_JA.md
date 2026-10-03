# 西側北辺の未通過・Save34 限定受入

`PASS_CAVE_WEST_FRONTIER_SAVE34_SCOPED_NORTH_BLOCKED`。Save33の8,10から9,7へ進み、北辺9,7→9,6を3回通常入力したが通過しなかった。そこで通常Save34/独立Continueへ区切った。未通過を保持し、8,5/7,5 eventへ到達したとは主張しない。

source `c181dc2610d01db9a29a9dc46edd6c8bb0ac0b46` / run `37123621651` / job `111204455124` 全8step成功。artifact `11274397555` / 155597bytes / SHA256 `ca68c211b1310c02031eee089a37506be85c7f56d7413fe5d5e805084ae42d38`。全35member、50/cold13入力、20画面。9,7到達6、北向き試行7/8/9は同じ座標。13〜16は部分write4状態、counter34先行16、17で全Flash完成/field復帰。保存成功文言の瞬間は120frame採取間隔の間にあり未採取、表示済みと主張しない。受入根拠は全Flash/sector checksum/通常field復帰と独立Continueの全SaveRTC一致。

戦闘0、party全600byte/HP322/PP[1,14,0,0]、Bag/HM05/13128円/PC/S61E payload不変。legacy flags/story4071=7/4072=1・flag4367=1・badge1保持。補助var4021=115→119/4022=2→1のruntime ownerは未解決。warm ledger hashは観測4で変わるが保存S61E payload/RP0不変、稼得やstory進行に昇格しない。42sector checksum・旧Save33bank57344byte・全SaveRTC cold同一、6996byte/1788範囲差分。

新map-load採取run37123370663/job111203707030全8step成功/native0。保存済920マスは再採取0。type1 root0x08214639のflag4367→call0x0821464Cが8,5へmetatile0281/collision0を設定する3node/14命令の原本を保持。別flag4354の6tileは東側32〜34,16〜17。動的8,5はこのrunで未踏破。新14controllerは原log継承、24新受入だけ実行。旧native/受入試験/ROM変更/compile/fixture0。

上流pret/pokefireredのmetatile_behaviors.hとevent_object_movement.cを比較参照し、behavior0x32はnorth-block、通常elevation不一致は別境界と確認した。ただし現候補実ROMの関数同値性を証明したとはしない。参照URLは両ログに保持。

次: Save34 artifact11274397555のstory-fast.srm（c90cde2874e2c9a13b96c990c3907326bea066bb22a6bd61ae71b63ae5419692、131088bytes）だけから再開。map1/73・9,7北・party4/RP0・13128円・badge1・story4071=7/4072=1。北辺9,7→9,6は3回通常入力で通過せず、この失敗辺を反復しない。Save34/独立Continueだけ限定受入。ミュウツーHP322/354・PP[1,14,0,0]、party/Bag/PC/S61E/所持金は不変。れいとうビーム/火炎放射は選ばない。host回復/PP/flag/var注入は禁止。新map-load原本3node/14命令より、flag4367=1が8,5にmetatile0281/collision0を設定する。実到達は未受入。次は9,7→9,8→9,9→9,10→8,10の通常戻り転送で27,7へ。そこから26,7→25,7→24,7→23,7→22,7→21,7→20,7→19,7→18,7→18,6→18,5→17,5→16,5→16,4→15,4→14,4→13,4→13,5岩階段→13,6→12,6→11,6→10,6→9,6→8,6→8,5→7,5の候補。これは最新Save34から新しく開いた8,5/次eventへ向かう必要な通常迂回であり、旧Save再ロードや受入単体の再試験ではない。7,5 coordはvar4071=7でtrainer360を含む6node/var4071=8の保存済原本。50/cold13入力・20画面・新14controller/24受入試験、既受入Save1〜33を無影響再走しない。保存成功文言の瞬間は未採取。Save34受入は全Flash/sector checksum/field復帰/独立Continueによる。補助var4021=119/4022=1のruntime ownerは未解決。trainer352/360、洞窟出口4,19→map1/38、全国図鑑、自然成長進化、全storyは未完。既存ROM/runtimeはActions入力だけ、新公開artifactは新save/画面/textだけ。
