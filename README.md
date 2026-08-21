# Pokémon Vega Modern — トーホク＋カントー二地方版

FireRed日本版Rev.0からVega 2018-02-23を再生成し、DPE-JP/CFRU-JPを公開ソースからVega互換で移植したうえで、元FireRedのカントーをVega本編の中盤から任意で訪問できる高難度の第二地方として復活させる長期開発ワークスペースです。トーホクとカントーを自由に往復でき、両地方へ追加生態を配置します。最終成果は32 MiB ROMの再現ビルドと、ROM本体を含まない差分パッチです。

早期渡航は「シオウの3個目バッジ取得後、アーシア島D・Hビル初回攻略完了」を概念条件とし、実ROMの数値flagはT02監査で確定します。カントーのLv.68〜100帯は自動スケーリングせず維持し、後半認定章・リーグ・最終共鳴だけをVega殿堂入り後に解禁します。

Factory UPSをVegaへ重ねる方式は採用しません。Factory ROMは挙動・配置の参照オラクルとしてだけ使います。

## セッション開始

毎回、次だけを順に読みます。

1. `AGENTS.md`
2. `design/current_state.md`
3. `design/agent_context_map.md`
4. `design/tasks_next.md`
5. 選択した `tasks/T*.md`

```bash
git status --short --branch
python3 scripts/taskctl.py next
```

詳細資料を全件読み直さず、`design/agent_context_map.md` から目的別に絞ります。

## 重要な正本

- 状態: `design/tasks_next.md`
- 依存関係: `tasks/task_graph.json`
- タスク完了条件: `tasks/T*.md`
- 現在地: `design/current_state.md`
- 採択済み判断: `design/decisions.md`
- 全体ロードマップ: `MASTER_PLAN.md`
- 入力・上流pin: `state/source-lock.json`
- 受領物一覧: `design/import_inventory.md`
- 受領資料レビュー: `design/import_review.md`
- 育成・操作QOL: `docs/QOL_POLICY.md`
- 二地方設計のactive review資料: `design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/`

## 私有入力

ROM、IPS、UPS、元ZIPは `userfile/imports/` に読み取り専用で置き、Gitへ入れません。`inputs/private/` と `inputs/reference/` はツール向けのGit管理外参照です。入力原本へ直接パッチを当てず、生成先へコピーして処理します。

## 必要時に選ぶコマンド

```bash
make status       # 状態とRESUME/PRIMARY/並列準備候補
make plan         # PRIMARY、並列準備候補、全実行wave
make harness      # clean+Vega IPSから32 MiB T03 no-op harnessを再構築
make harness-check # 生成済みT03成果を現在の入力/configへ照合
make moves        # T03からVega固定512技＋CFRU追加551技のT04 stageを再構築
make moves-check  # エミュレータを再実行せずT04成果と現在入力を照合
python3 scripts/build_id_spaces.py build # T05 Type/Ability/Item配置前modelを再生成
python3 scripts/build_id_spaces.py check # T05公開成果を副作用なしで照合
python3 scripts/build_battle_core.py build # T04/T05からT06 battle core stageを2回再構築・実機検証
python3 scripts/build_battle_core.py check # T06成果と現在入力を副作用なしで照合
make species     # T06からVega固定412種＋DPE追加1209種のT07 stageを再構築
make species-check # T07成果と現在入力を副作用なしで照合
make species-surface # T09画像・鳴き声・図鑑・進化・技表をstage 09へ統合
make species-surface-check # T09成果のbyte一致と全テーブル境界を副作用なしで照合
make engine-slice # T10の追加種・QOL-A・Factory/AI/Raid継続save縦切りを実行
make engine-slice-check # T10 fixture/report/schemaを副作用なしで再照合
make vermilion-slice # T13クチバ早期往復とphysical contentを生成
make vermilion-slice-check # T13成果を副作用なしで再照合
make kanto-maps # T14本土253 operational mapをcanonical import
make kanto-maps-check # T14接続・ID・size成果を副作用なしで再照合
make kanto-progression # T15二段階進行・QOL・Factory・League fixtureを生成
make kanto-progression-check # T15成果を副作用なしで再照合
make content-population # T16二地方encounter/trainer/itemとROM payloadを生成
make content-population-check # T16 manifest・中央allocation・stage 16を副作用なしで再照合
make regression # T17実Kanto map/QOL-B/trainer進行をstage 17へ統合してlibmGBA回帰
make regression-check # T17の16成果を副作用なしで再生成・照合
make trainer-rebalance # V4本編trainerをstage 17へ結合してstage 19を生成
make trainer-rebalance-check # V4のID解決・record・party pointerを副作用なしで照合
make trainer-v5-foundation # Stage 31へV5先行25戦とlive sidecarを結合してstage 32を生成
make trainer-v5-foundation-check # SINGLE/DOUBLE・flag・再戦・saveのexact-ROM成果を再照合
make trainer-v5-tohoku-batch02 # Tohoku次14物理命令を累積39戦へ接続してstage 33を生成
make trainer-v5-tohoku-batch02-check # exact pointer再束縛・sidecar・DOUBLE・saveを再照合
make trainer-v5-tohoku-batch03 # Gym1直後＋map 3/21の次15物理命令を累積54戦へ接続してstage 34を生成
make trainer-v5-tohoku-batch03-check # RematchMap V2・exact rebind・sidecar・旧batch回帰を再照合
make trainer-changekit-inputs # AUTHORING_KIT＋Task01〜06を補正working copyで全validator検証
make trainer-changekit-final # 全1302戦・6490体をstage 35へserializeしmGBA quick/fullを実行
make trainer-changekit-final-check # 生成物byte一致とmGBA quick/fullを副作用なしで再照合
make trainer-changekit-clean-rebuild # clean ROM→v1.4.0→Stage34→Stage35のexact patch chainを再構築
make trainer-changekit-clean-rebuild-check # clean起点の3段patch往復・直接BPS・証跡を副作用なしで再照合
make trainer-changekit-package-check # 入力補正・30 focused tests・1302戦mGBA・clean再構築をまとめて再照合
make mirage-production # Stage37の通常受付へ持込3体・7戦×4周Mirageを接続してStage38を生成
make mirage-production-check # exact-ROM quick/full・保存復旧・badge復元・両BPSを副作用なしで再照合
make mirage-production-clean-rebuild # clean ROMからStage37→Stage38とclean直接BPSをbyte再現
make mirage-production-clean-rebuild-check # clean起点のpatch chain・直接BPS・証跡を副作用なしで再照合
make move-distribution-v4 # Stage38へ技配布V4全表と野生初期技runtimeを結合してStage39を生成
make move-distribution-v4-check # canonical表・consumer root・mGBA quick/fullを副作用なしで再照合
make move-distribution-v4-clean-rebuild # clean ROMからStage38→Stage39とclean直接BPSをbyte再現
make move-distribution-v4-clean-rebuild-check # clean起点のpatch chain・直接BPS・証跡を副作用なしで再照合
make research-economy-v1 # Stage39へ独立研究通貨・6活動・7 rank・23品交換所を結合してStage40を生成
make research-economy-v1-check # save移行・9 host・activity hook・mGBA quick/fullを副作用なしで再照合
make research-economy-v1-clean-rebuild # clean ROMからStage39→Stage40とclean直接BPSをbyte再現
make research-economy-v1-clean-rebuild-check # clean起点の両BPS・migration・Stage40証跡を副作用なしで再照合
make reward-encounters-v2 # Stage40へ4 tier・24 pool・pending再戦・10 credit sourceを結合してStage41を生成
make reward-encounters-v2-check # 全支払transaction・save/reset・Scientist・mGBA quick/fullを副作用なしで再照合
make reward-encounters-v2-clean-rebuild # clean ROMからStage40→Stage41とclean直接BPSをbyte再現
make reward-encounters-v2-clean-rebuild-check # clean起点の両BPS・32 transaction・Stage41証跡を副作用なしで再照合
make facility-runtime # クチバFactory Trialの受付・6候補・交換・保存復旧をstage 20へ実結合
make facility-runtime-check # stage 20と実ROMスモークを副作用なしで再照合
make first-battle-hotfix # 初戦の不正な行動順通知を防ぐstage 21を生成
make first-battle-hotfix-check # 初戦3分岐・fault injection・正規優先効果・BPS往復を再照合
make hm-field-access # Vega HM所持だけでfield能力を使えるstage 22を生成
make hm-field-access-check # 8 HM・手持ち3条件・地形境界・BPS往復を再照合
make battle-rules # 固定CFRU-JPの状態異常・急所・天候ownerをstage 23として確定
make battle-rules-check # 固定RNG・通常/double/Factory/Raid回帰・BPS往復を再照合
make battle-ui # 実タイプ・有効度・タイプ一致表示をstage 24へ結合
make battle-ui-check # 5表示区分・Stellar・全戦闘mode・文字列境界を再照合
make move-memory # 無料の技思い出し・技忘れ・タマゴ技管理をstage 25へ結合
make move-memory-check # 候補境界・解禁・form連動・入口scriptを再照合
make qol-release-smoke # 同じstage 25でKanto/Factoryと全QOLを横断実ROM再検証
make qol-release-smoke-check # hash一致済みの統合fixtureを副作用なしで再照合
make acquisition-events # 201件の取得イベントと共通runtimeをstage 26へ結合
make acquisition-events-check # 取得経路・host・save・実ROMfixtureを副作用なしで再照合
make final       # clean入力からv1.4.0最終ROMとbuild metadataを生成
make release-patch # ROMを含まないBPS＋文書の決定論release archiveを生成
make verify-release # BPS完全往復とarchive禁止物を副作用なしで再照合
make release-fresh-check # clean Git worktree＋私有入力からfinal/BPS/ZIPをbyte再現
make validate     # DAG、manifest、状態、受領資料の静的検査
make guard        # 私有バイナリ混入防止
make test         # unit test
```

WSLでは全体標準verifyを実行しません。選択タスクのacceptanceに必要なコマンドだけを使い、同じ検査を重ねません。

初期入力・上流取得・参照ROM生成は `make quickstart` で行います。副作用と生成先は `CODEX_START_HERE.md` を先に確認してください。

T03以降のROM stageは入力原本を上書きしません。`make harness` は固定clean ROMへVega IPSをmemory上で適用し、32 MiBへ `0xFF` 拡張して、named allocatorが許可した拡張領域へno-op moduleを配置します。

`make moves` はVega Move ID 0〜511を固定し、V3技調整を優先適用してCFRU-JPの未収録551技を512〜1062へappendします。生成したgame-encoding表、70個のVega固有effect adapter、178 pointer repointをstage 04へ配置し、固定wild battleで実際に技を1回実行します。

T05はVega既存Type/Ability/Itemを固定し、意味同一を証明できた上流entityだけを同じIDへ対応させます。Type 25、Ability 312、Item 999のstable model、source alias、C table、表示幅レポートを生成します。ROM配置は行わず、T06がT04 stageと合わせて統合します。

T06は固定CFRU-JPのbattle-only hookをexpected-byte付きでstage 04へ統合し、Type/Ability/Item/Moveのcanonical表、育成QOL境界、Factory、3段階AI、1戦1gimmick、Mirage item、high-difficulty Raidをallocator管理payloadへ配置します。通常戦・AI・policyの3本のlibmGBA runnerを各2 processで実行し、公開前にROM/report/payload/fingerprintをfail-closedで照合します。

T07はVega Species ID 0〜411を固定し、DPE primaryとのidentity 206件をalias、欠落Species/form 1209件を412〜1620へappendします。全1621行にofficial判定とcanonical全国番号を付け、フォームを重複加算しない捕獲数counterを生成します。FireRed/Vegaのタマゴ予約ID 412を維持し、キャタピーは649へ割り当てます。canonical BaseStatsをDPE予約領域へ配置して105参照をrepointし、追加Species 413を実party memoryへ生成します。

T09はVega固定412行のfront/back、palette、icon、鳴き声、図鑑をbyte一致で保ち、DPE由来の追加1209行をcanonical順に追加します。進化はSpecies/Move/Item IDを変換し、V2設計553行の意味重複43行を除去します。Species名はcanonical 11 byte表を正本とし、stock直接参照40か所を8 byte互換表へ移行して6文字名134行を保持します。level/egg/TM/HM/tutorと現代式孵化、5個queue、満杯party/box、compact IV/EV、まるいおまもりを固定RNG fixtureで検証します。

T10はstage 09上の追加オコリザルと追加Move/Ability/Item/進化をlibmGBAで生成し、wildからsave/load、QOL-A、Factory 3連戦、報酬遭遇、3 AI profile、TM license、Mirage、NORMAL/RESEARCH、4-star Raidまで1つの継続save契約で通します。releaseのdebug giftはcompile時にOFFです。

T17はstage 16から253 Kanto map、180 layout、51 tileset、133 Kanto wild header、29 trainer/174 party row、8 gym＋Leagueの実eventを中央allocatorへ配置します。自然なnew gameからクチバ描画・移動・Vega帰還、QOL-B Thumb実行、trainer pointer graphを同一32 MiB ROMでlibmGBA 2 process検証し、広い状態空間は固定fixtureへ分離します。

T18 release導線は `make final` でT03〜T17と追加stage 19〜26をclean入力から再構築可能にし、clean FireRed日本版Rev.0へ
直接適用するBPSだけを配布します。patchの再適用結果、32 MiB最終hash、固定ZIP byte、
ROM/save/元patch/private path不在、source pin、QOL/Factory/AI/save説明を機械検証します。
遊び方と適用方法は `docs/RELEASE_README_JA.md`、save互換性は
`docs/SAVE_COMPATIBILITY.md` を参照してください。

追加stage 19はユーザー提供の本編トレーナー再設計V4（141戦・610体）をcanonical IDへ解決し、
実在するVega Trainer IDへ決定的に結合します。AI rankは固定CFRU-JPのBasic / Semi Smart /
Full Smartへ対応し、Mirage・未指定Sphereの施設編成は変更しません。

追加stage 20はクチバ（group 96 / map 5）へ受付NPCを実配置し、固定CFRU-JPの
Lv.50候補生成器で重複なし6体を作る。既存party UIで3体を選択してsingle 3v3を3戦し、
1・2勝後は相手側からランダムに保持した1体と手持ちの任意1体を交換できる。完走は9 BP。
敗北・辞退・cancel・save/reset復旧では入場前party 600 byteを復元し、図鑑はseenだけを更新する。

追加stage 21はstage 20を再利用し、行動順schedulerに残留したQuick Claw/Custap indicatorが
Item ID 0の初戦リープンを「？？？？？？？？」通知へ誤送出する経路をhold effect再検証で遮断する。
初戦3分岐、正規のせんせいのツメ・イバンのみ・クイックドロウ、clean ROMからのBPS往復を
libmGBAで検証する。公開releaseへの統合と重いfresh rebuildは全QOL完了時に1回だけ行う。

追加stage 22はstage 21を再利用し、Vega既存HM01〜08（Item 339〜346）のバッグ所持を
フィールド能力の唯一の解禁条件にする。HM05はフラッシュ、HM08はダイビングとして扱い、
CFRU追加HM IDや手持ちの習得・適性・技枠へ依存しない。既存の地形、map、follower、script
入力境界は維持し、ポケモンへ技を書き込まない。実ROMで8種×手持ち0体／未習得／習得済み、
Surf状態、callback gate、clean ROMからのBPS往復を検証する。公開release更新は最終QOL統合まで行わない。

追加stage 23はstage 22を再利用し、5個のstock battle-script root、状態異常、行動順、急所、
damage、天候のownerが固定CFRU-JP payloadだけであることを確認する。麻痺1/2・行動不能1/4、
眠り・凍り、毒・猛毒・やけど、急所1.5倍とstage分母、天候5/8 turn・damage補正・終了を
固定RNGの実ROMで検査する。対象byteは既に正しかったため追加patchは0件で、stage 22とbyte-identical。
通常、trainer、double、Factory Trial、Raidを現行stageで通し、重い全再構築は行わない。

追加stage 24はstage 23の固定CFRU move menu ownerを維持し、profileで無効だった実タイプ・
有効度表示を1,200-byte adapterで接続する。inline済みの初期化・カーソル経路もwrapperで覆い、
`EmitChooseMove` が実damage側 `VisualTypeCalc` から
事前計算した結果を表示し、抜群・半減・無効・タイプ一致とStellar/Tera Blastを既存CFRUの
文字列・paletteで示す。通常のHELPボタン設定でも戦闘中のLはCFRU技詳細へ渡し、旧HELPは
戦闘中だけ抑止する。fieldのHELP、通常、trainer、double、Factory Trial、Raidの入力復帰、
canonical名、clean ROMからのBPS往復を検証し、Factory ROMのbyteは使用しない。

追加stage 25はstage 24を再利用し、1個目のバッジ報酬へだいじなもの「わざメモリー」を追加する。
通常は現在Lv以下のLv.0/1を含むlevel技だけ、D・Hビル後のタマゴ技は殿堂入り前に
ものまねハーブ所持と空き枠を要求し、殿堂入り後は無料にする。シオウ・カラスバの既存NPCも
同じ無料coreへ接続し、キノコやハーブを消費しない。技忘れはHMを許可し、最後の1技、タマゴ、
戦闘/施設/Raid、一時form専用技を拒否する。削除はCFRU `SetMonMoveSlot` 経路を通し、
ケルディオのform連動とPP Up段階のslot移動を実ROMで検証する。

追加stage 26は、コレクション対象1,206種と有効化に必要な10フォームの不足経路を201件の
取得イベントへまとめ、clean FireRed由来の既存24 objectを19マップへ復元して結合する。
固定捕獲、ギフト、タマゴ、化石、進化支援、交換エミュレータ、サービスを共通transactionで扱い、
捕獲後だけの確定、孵化時の図鑑登録、party/PC満杯、道具rollback、通常saveとsector 31台帳の
再読込を実ROMで検証する。通信進化30経路はItem 395「リンクケーブル」で単独ROM進化できる。

v1.4.0統合gateはstage 20→26のhash chainと全allocator overlap 0を確認したうえで、同じ最終
stage 26を既存runnerへ渡す。自然new game・御三家3分岐、Kanto往復、Factory選択・交換・
sector 31 save、8 HM、状態異常・急所・天候、技選択UI、わざメモリーの通常／タマゴ技／
忘却／form連動、全7取得方式を再観測する。stage 25までの新規serialized fieldは0で、
stage 26だけが既存2 KiB台帳の予約領域へ240 byte取得blockを割り当てる。

v1.3.9のトーホク外来生態runtimeは、設計293行を草むら・洞窟・水上・いわくだき・釣り・
朝昼・夜・日替わり大量発生・隠れ遭遇へすべて接続する。最初の草むらはmap `3/19`へ
5%の8候補を実結合し、抽選4096回と実遭遇生成で検証する。通常はRTCから朝昼／夜と
日替わり群れを自動選択する。1個目のバッジ報酬「せいたいレーダー」（Item 348）では
現在modeを確認し、RTCに依存せず朝昼・夜・群れへ固定したり、現在mapの隠れ枠を直接探索したりできる。
既存saveで未所持の場合はシオウの技管理NPCが補う。釣りは実際の竿入力経路と竿条件を使う。

## 効率方針

同一hash・同一source commit・同一tool versionの検証済み成果を再利用し、独立作業は所有ファイルを分けて並列化します。正本IN_PROGRESSは1件に保ちますが、`PRIMARY` は推奨順であり、依存READYの `PARALLEL_PREP` を待ち時間やfan-outに応じて先に選べます。大規模統合を一度に行わず、no-op ROM、Move/battle/Species、育成・操作QOL、クチバ往復の順に動く成果を出してから広げます。現在対象とDAG由来の準備waveは `make plan`、マイルストーン要約は `MASTER_PLAN.md`、厳密な完了条件は各 `tasks/T*.md` を正とします。

既定QOLは、全文字の即時表示、Vega比でダッシュ25%以上・自転車50%以上の移動時間短縮、現代式孵化、経験アメ、育成値表示・変更、全体学習装置、PC一括操作です。固定仕様は `docs/QOL_POLICY.md` を参照します。

UIと追加イベントは機能優先の最小構成です。既存画面・標準menu・既存NPC/端末を再利用し、新規full-screen UI、装飾演出、長いcutsceneや多段questは原則追加しません。

## 補助ツール

ChatGPT Webを補助的な相談、要約、レビュー、画像生成に使う場合だけ `tools/chatgpt_browser/README.md` を参照します。私有ROMや非公開データは送信しません。

Stage35の実map／trainer／取得host／QOL catalogから、ChatGPT Proへ渡すROM非同梱のイベント設計パケットを作る場合は次を実行します。ZIP内のschemaとvalidatorを通った返却bundleは、batch単位のCodex実装入力として使えます。

```bash
python3 scripts/build_event_authoring_packet.py \
  --output-parent dist/event_authoring_packet \
  --zip /path/to/Downloads/Pokemon-Vega_CHATGPT-PRO_EVENT-AUTHORING_STAGE35_20260819.zip \
  --report reports/generated/event_authoring_packet_stage35.json
```
