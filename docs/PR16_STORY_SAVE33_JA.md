# 東岩階段・解禁後teleport・Save33 限定受入

`PASS_CAVE_UNLOCKED_TELEPORT_SAVE33_SCOPED`。Save32の21,19から東岩階段23,14/上段23,13を通過し、flag4367=1の正規19,14→8,10転送と通常Save33/独立Continueを受入。戦闘0。洞窟出口/次event/trainer360は未到達。

source `73741f547eba9bb5519afb22c37d524416a9beb9` / run `37122926665` / job `111202448744` 全8step成功。artifact `11273622658` / 215872bytes / SHA256 `bb0733bdf3894d364fbaf96eba893d9f5b9d79797da136aad57cf01292b0ae24`。全46member、69/cold13入力、31画面。階段8/上段9、trigger17、着地18/解錠19、書込中23〜26、保存文言27/field28。counter33先行の26を保存完了へ昇格せず、全Flash完成27を区別。

party全600byte/HP322/PP[1,14,0,0]、Bag/HM05/所持金13128/PC/S61E全payload不変。legacy flags不変、story4071=7/4072=1・flag4367=1・badge1保持。補助var4021=103→115/4022=0→2のruntime ownerは未解決。42sector checksum/S61E CRC・旧Save32bank57344byte・全Save/RTC cold同一、6970byte/1779範囲差分。候補内のcheckflag/goto_ifと両warp実30byteを独立照合。

15controller試験は測定原logを保持して再走0。新24受入/拒否試験だけ実行。地形採取/旧受入試験/native再走/ROM変更/compile/fixture0。Save32記録run37122527387全11step終端を固定JSONに反映し、旧失敗原本は変更しない。一般CI全成功/releaseは主張しない。

次: Save33 artifact11273622658のstory-fast.srm（ceb55e1df60f35b69f4854017afa19d703df987c602c3a0f6b0090c2323e0685、131088bytes）だけから再開。map1/73・8,10西・party4/RP0・13128円・badge1・story4071=7/4072=1。東岩階段23,14とflag4367=1の正規19,14→8,10teleport、Save33/独立Continueを受入。ミュウツーHP322/354・PP[1,14,0,0]、party/Bag/PC/S61E/所持金は不変。れいとうビーム/火炎放射を選ばず通常UIの残存技/必要時通常回復だけ。host回復/PP/flag/var注入は禁止。保存済全920マスと7,5のcoord6nodeから西側区間を調べ、var4071=7でtrainer360を含む次の正規eventへ向かう。8,10から踏み直し転送で東へ戻らない経路を選ぶ。静的壁だけで出口不可と決めず必要ならmap-load動的地形ownerだけ照合。物理出口4,19はmap1/38へ、隣接warp4,6はmap3/21へ接続する静的表。通常到達/洞窟走破/全国図鑑は未完。69/cold13入力・31画面・新15controller/24受入試験、Save1〜32を無影響再走しない。補助var4021=115/4022=2のruntime ownerは未解決。trainer352/360、洞窟出口、HM05原因、全国図鑑、自然成長進化、全storyは未完。既存ROM/runner/runtimeはActions入力だけ、新公開artifactは新save/画面/textだけ。
