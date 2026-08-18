# Changelog

## Unreleased

- post-release stage 34として、Trainer Redesign V5のGym1直後map-script 1命令とmap `3/21`の
  連続14物理命令をstage 33へ累積し、54 encounter／54一意party／171 member、
  50 SINGLE／4 DOUBLEへ拡張した。
- 共有source IDをcommand-data addressと組で解決する8-byte RematchMap V2を23行へ移行し、
  source 119の二つの再戦を1043/1045へ位置別に束縛した。exact rebind／defeat flag mapは29行。
- 独立2 processのexact-ROMで新15命令、trainer 1362 sidecar、RematchMap V2、旧Batch02、
  rooted kind-4 DOUBLE、勝敗、再戦、flag、save/loadを確認した。v1.4.0とstage 27〜33は不変。

- post-release stage 33として、Trainer Redesign V5のTohoku次14物理trainerbattle命令を
  stage 32へ累積し、39 encounter／39一意party／113 member、35 SINGLE／4 DOUBLEへ拡張した。
- map `3/21`・`3/22`・`22/1`を命令pointer＋kind＋source IDの三つ組で再束縛し、
  source 119の複数命令と非整列kind-3を区別する。論理alias 419/424は物理root 420/425へ統合した。
- 独立2 processのexact-ROMで20 exact rebind、live ability/nature/IV/6EV、rooted kind-4
  DOUBLE、勝敗、再戦、物理flag、save/loadを確認した。v1.4.0とstage 27〜32は不変。

- post-release stage 32としてTrainer Redesign V5の先行25 encounter／25 party／71 memberを
  Stage 31の個別map/object/scriptへ接続し、23 SINGLE／2 DOUBLEを1,367行Trainer tableと
  16-byte live sidecarへ生成した。
- グローバルflag APIと最適化private party関数はhookせず、trainer専用flag入口、公開
  `BuildTrainerPartySetup`、exact kind-4再束縛だけを使用する。初回DOUBLE scriptは物理ID 702を
  保持し、戦闘引数消費後だけV5 ID 1342へ切り替えるため、NPC敗北flagと既存saveを維持する。
- 独立2 processのexact-ROMで自然trainer、SINGLE sidecar、rooted DOUBLE、4 controller、
  勝敗、再戦、flag、save/loadを確認した。v1.4.0とstage 27〜31は不変。
- stage 30のFactory Trial完了wrapperを先に呼ぶpost-release stage 31を実装し、ACTIVE
  `SHINY_MEMORIAL` 100連勝行をFactory Master解禁後の一度限りclaim bit 9へ接続した。
- special event catalogを除外した旧図鑑安全範囲137種からLv.50色違いを生成し、party優先・
  満杯時PCへ配布する。generated National／取得台帳bit表で図鑑・collectionを正しく登録する。
- PREPARED/STAGED write-ahead journalと個体markerで、容量不足、通常save／sector 31失敗、
  journal喪失から再試行・commit復旧し、claim消費と二重配布を防ぐ。v1.4.0とstage 27〜30は不変。
- stage 29のFactory Trial完了wrapperを先に呼ぶpost-release stage 30を実装し、ACTIVE
  `SPECIAL_EVENT` 49連勝行をFactory Master解禁後の一度限りclaim bit 8へ接続した。
- Master未解禁、streak 48以下、既claimではStage 30の永続状態を変更せず、Stage 29の反復item/BP、
  基本9 BP、連勝credit、party exact復元を維持する。sector 31失敗時はpost-stage-29台帳へ補償する。
- v1.4.0 release tag／配布ROMとstage 27〜29は不変。stage 30用incremental/cumulative BPSと
  再現builderを独立管理し、100連勝色違い記念枠は次タスクへ残す。
- stage 28のFactory Trial完了wrapperを先に呼ぶpost-release stage 29を実装し、ACTIVE
  `TRIAL_REPEAT` 2行を反復完走へ接続。stock RNGで「オレンのみ×1＋1 BP」または
  「ハイパーボール×1＋2 BP」を抽選する。
- 初回報酬claimが呼出前から完了している成功完走だけを反復対象にし、初回item／追加3 BP、
  連勝credit、party復元、基本9 BPはstage 28の所有権を維持する。bag満杯時は反復itemと
  追加BPだけを同時に見送り、保存失敗時はpost-stage-28状態へ補償rollbackする。
- v1.4.0 release tag／配布ROMとstage 27・28は不変。stage 29用incremental/cumulative BPSと
  再現builderを独立管理する。
- stage 27のFactory Trial完了scriptへ、既存完了処理を先に呼ぶmanifest報酬wrapperを接続する
  post-release stage 28を実装。初回はExp Candy XS×5、S×2、追加3 BP、連勝3/7/14/21では
  HABITAT/TYPE/RARE/RANDOM encounter creditを各1回だけ付与する。
- 基本9 BP、連勝更新、party復元、sector 31保存は既存runtimeのまま保持。bag満杯時は
  基本完了だけを確定して追加報酬を繰り越し、反復時のitem・追加BP・credit重複を抑止する。
- v1.4.0 release tag／配布ROMとstage 27は不変。stage 28用incremental/cumulative BPSと
  再現builderを独立管理する。
- v1.4.0をhash固定入力として、クチバFactoryへ18品目のBPショップNPCを追加する
  post-release stage 27を実装。Trialと同じBP残高を使用し、解禁、5件ページmenu、
  通常save＋sector 31の購入確定、保存失敗時rollback、残高不足・bag満杯の無変更終了を接続した。
- v1.4.0 release tag／配布ROMは不変。stage 27用BPSと再現builderを独立管理する。

## 1.4.0 — 2026-08-16

- コレクション対象1,206種と到達性に必要な10フォームを監査し、既存の野生・進化経路と
  不足分201件の取得イベントを統合。T17で省略されたclean FireRed由来object 24件を
  19マップへ元の座標・object予算内で復元し、新規設計objectは追加していない。
- 固定捕獲、ギフト、タマゴ、化石復元、現代進化支援、交換エミュレータ、サービスの7方式を
  共通transaction runtimeへ接続。解禁、5件ページmenu、捕獲後だけのclaim、重複防止、
  party→PC、全収納満杯、道具消費rollback、reset復旧を実装した。
- 既存2 KiB save台帳内へ、4 byte整列した240 byteの取得台帳を後続offset不変で配置。
  v1.3.9以前のzero領域を一度だけ移行し、outer/inner CRCとsector 31直接保存を検証した。
  手持ち・PC・図鑑は通常save、取得台帳はsector 31へ確定し、双方の再読込も確認した。
- 通信進化30経路をItem 395「リンクケーブル」で単独ROM進化可能にし、必要持ち物を保持。
  化石16経路と採掘補助を追加し、内部Species 282だった野生2slotをストライク255へ補正した。
- 2,035 exact case、24 host graph、allocator overlap 0、clean ROMからのBPS往復に加え、
  libmGBA独立2 processで7方式、実flash再読込、通常save、タマゴ孵化時登録、party/PC満杯、
  固定進化・野生byteを確認した。
- 最終ROM SHA-256:
  `30f19ee3ebab856379393a572bfde33c2ccfdac7351e73ff3a7f3e231f3f553e`。

## 1.3.9 — 2026-08-16

- stock UI向けSpecies名互換表が各行を5文字へ切っていた問題を修正。canonical 1,621行の
  長さ分布を固定し、6文字名134行を8 byte互換表でも末尾文字＋終端まで保持する。
- `gSpeciesNames`直接参照40か所とstride/bound命令48か所をfail-closed inventoryへ固定。
  戦闘データへのnickname転送4経路と、監査済み表示bufferの5文字上限も局所的に6文字へ拡張した。
- exact-ROM mGBAでエースバーンとムゲンダイナの戦闘メッセージ、HPバー文字列・OBJ tile、
  buffer canaryを検査。メガピジョット／キョダイマックスゲンガーのLv.100表示と、
  手持ち・概要・PC・図鑑・進化／通知・道具対象の共有文字列経路も再検証した。
- 最終ROM SHA-256:
  `0f7406c70021adf9778f0e7a9220f4e014feaac73d7e988ba39700a63be97fcd`。

## 1.3.8 — 2026-08-15

- DPE由来の追加1209種で、画像・色・アイコンのresource tagがDPE側IDのまま残り、
  FireRed/Vega側の表示関数もSpecies 412を上限としていた問題を修正。ポッポ、グルトンを含む
  canonical Species 0〜1620を同じ表示経路へ統一した。
- FireRed/Vegaが予約するタマゴID 412へキャタピーを割り当てていた衝突を解消。タマゴを412へ戻し、
  キャタピーだけを旧タマゴ枠649と交換したため、ほかの1619種のcanonical IDは変更しない。
- exact-ROM mGBA gateでタマゴ、ポッポ、キャタピー、グルトン、最大IDの前後画像・通常色・
  アイコンを直接実行し、全1620表示名とタマゴを除く1619種の個体生成も確認する。Vega固有種の
  従来図鑑値と追加種の公式全国番号を分離し、施設・レイドを含む戦闘ルール回帰も維持した。
- 最終ROM SHA-256:
  `51b154c056f5bd83cdff6d9afbe124204d88ab65137d85271480ffce4448a1f2`。

## 1.3.7 — 2026-08-15

- v1.3.6で未接続だった夜間34、大量発生29、朝昼／ずつき28、釣り等22、
  DexNav／隠れ相当18、屋内異常8、夜間水上1を実ROMへ接続。通常153行と合わせ、
  トーホク外来生態293行を95 runtime entry・294候補bindingとして0件保留で生成する。
- 通常遭遇、実際の釣り入口、RTC朝昼／夜、日替わり群れ、屋内を含む隠れ探索を別々に接続。
  既存遭遇表は維持し、バッジ、竿、殿堂入り前後のlevel条件を反映する。T-E04固有依頼だけは
  2個目のバッジ＋いいつりざおへ解禁条件を正規化し、生態チケット代替はレーダーの夜固定へ接続した。
- 1個目のバッジ報酬へ「せいたいレーダー」（Item 348）を追加。RTC自動の現在modeを確認し、
  朝昼・夜・群れへ手動固定、または現在mapの隠れ枠を直接探索できる。既存saveではシオウが補う。
- exact-ROMを2 processで実行し、全layer、RTC entry、手動mode、最初の草むら4096抽選、
  釣り生成、屋内隠れ生成、trainer／戦闘UI／HP／Factory／Raidの既存回帰を確認した。
  最終ROMは32 MiB、SHA-256
  `cb8ac173bf8f9e0e4bc51ecd12adc581c6344761955f38766ce7211e2dd5f167`。

## 1.3.6 — 2026-08-15

- Vega既存種と追加Speciesで異なっていた初期技表ABIを統一し、追加種を使うtrainer戦が
  開始時に黒画面で停止する問題を修正。Vega既存412種は従来処理を保ち、追加1209種だけを
  3-byte学習表adapterへ分岐する。
- 最初の草むら（map 3/19）へ追加生態レイヤーを実接続。既存遭遇表を変更せず5%で8候補を
  抽選し、別マップへ漏れないことを実ROMの4096回抽選と遭遇生成関数で確認した。
- トーホク生態設計293行の実ROM coverageを再監査。通常の草むら・洞窟・水上・
  いわくだき153行だけが接続済みで、夜間・大量発生・ずつき・釣り・DexNav専用140行は
  未接続であることをbuild metadataと回帰testへ固定した。
- 最終ROM上で有効trainer ID 0〜771の全772件、全1620 Species生成・名前・初期技、初戦、
  L技詳細、戦闘規則、Factory/Raid、傷薬使用前後のHP表示を再検証した。

## 1.3.5 — 2026-08-15

- v1.3.4で「旧savestate混入」とした診断を訂正。FR由来の旧HELPが戦闘中のLを先に受け取り、
  画面退避領域でCFRUの戦闘EWRAMを上書きして`gNewBS`を0にしていたROM統合不具合を修正した。
  提供されたbattery saveは正常で、Delta固有の問題や「ヘドロえき」の効果ではなかった。
- ボタン設定が通常のHELPでも、技選択中のLはCFRUの技詳細（接触・威力・命中）を開く。
  旧HELPを抑止するのは戦闘中だけで、fieldでは従来のHELPを維持する。
- 最終ROMそのものを固定VBA-M engineで確認し、L詳細の開閉、`gNewBS=0x02017634`の維持、
  HELP state 0、battle controller不変を確認。stage 24以降だけを225.3秒で再生成した。

## 1.3.4 — 2026-08-15

- アクタシの第2特性（Ability 64）で誤って残ったクイックドロウ判定が、最初のライバル戦で
  空欄の特性通知と「こうどうが はやくなった！」を繰り返す問題を修正。実際のAbilityが
  クイックドロウ（260）でない限りindicatorを破棄する。
- 技選択UIの表示関数だけでなく、固定CFRUビルドで旧処理がinline展開されていたメニュー初期化・
  カーソル入力経路も接続。実際の「たたかう→技選択→カーソル移動」で抜群・半減・無効・
  タイプ一致表示が更新されることを実ROMで確認。
- stage 20以前を再利用する差分ビルドで、境界防御を含む最終stage 21〜25と最終ROMを
  約386.2秒（6分26秒）で再生成した。

## 1.3.3 — 2026-08-14

- `v1.3.2` 候補のfresh checkoutがstage 23まで再構築後、T06メタデータの実行時間差だけで
  battle UI入力pinを拒否する問題を検出。その候補は配布・pushせず、旧tagも移動しない。
- T06入力をメタデータ全体のSHAではなく、battle fingerprint、ROM、offsets、linked objectの
  決定的なUI ABI契約へ固定。戦闘UIと最終ROM byte、save形式、遊べる機能は変更しない。

## 1.3.2 — 2026-08-14

- `v1.3.1` 候補のfresh checkoutが重い上流build前に検出した、更新済み
  `mgba_ai_fixture_runner.c` とT01/T02固定inventoryのhash不一致を解消。その候補は
  配布・pushせず、旧tagも移動しない。
- 戦闘UIとROM byteは `v1.3.1` 候補から不変。1×・抜群・半減・無効・STAB、
  Stellar/テラバースト、ダブル対象別、Factory/Raid共通経路の契約を維持。

## 1.3.1 — 2026-08-14

- `v1.3.0` 候補の隔離fresh checkoutが検出したT05→T06の古い入力pinを更新。
  その候補は配布・pushせず、旧tagも移動しない。
- 固定CFRU-JPの再リンクで変化する絶対addressを、hash検証済みT06 offsetsから決定的に
  解決する契約へ更新。Factory、初戦、HM、戦闘規則/UI、わざメモリーの
  runnerを、最終ROMの実配置で再検証した。
- 技選択UIは1×・抜群・半減・無効・STAB、Stellar/テラバースト、ダブル対象別、
  Factory/Raidの共通ownerを同一実ROMで再確認。

## 1.3.0 — 2026-08-14

- 初戦で不正なQuick Claw/Custap通知が残留した場合に「？？？？？？？？」表示へ入る経路を防止。
  御三家3分岐、異常indicator注入、正規のせんせいのツメ・イバンのみ・クイックドロウを実ROM確認。
- Vega既存HM01〜08をバッグで所持するだけでフィールド能力を解禁。バッジ、手持ち、習得技へ
  依存せず、地形・map・follower等の安全境界と「ポケモンへ技を書き込まない」契約を維持。
- 固定CFRU-JPの麻痺、眠り、凍り、毒・猛毒・やけど、急所、天候規則を正式な単一ownerとして
  固定し、通常、trainer、double、Factory Trial、Raidで回帰確認。
- 戦闘中の技選択へ実タイプ、有効度（1×・抜群・半減・無効）、タイプ一致を表示。ダブルの
  対象別判定、Stellar、テラバーストも実damage計算と一致させた。
- 1個目のバッジ報酬に携帯用「わざメモリー」を追加。無料の思い出し・技忘れ・D・Hビル後の
  タマゴ技管理をシオウ／カラスバNPCと共通化し、キノコやものまねハーブを消費しない。
- stage 20〜25を同じ最終ROMで横断し、Factory/Kanto、初戦、HM、戦闘規則/UI、わざメモリー、
  save境界を再検証。clean FireRed日本版Rev.0用BPSと決定論ZIPをv1.3.0へ更新。

## 1.2.0 — 2026-08-14

- クチバへBattle Factory Trial受付NPCを実配置。固定CFRU-JP生成器によるLv.50・重複なし
  候補6体、既存party UIでの3体選択、single 3v3×3を実ROM eventへ結合。
- 1・2勝後に実対戦相手からランダム保持した1体と、選択した手持ち1体を任意交換する経路を追加。
  各戦後全回復、3連勝9 BP、seenのみ更新を実装。
- 参加前6×100 byte partyをsector 31へ保存し、完走・敗北・辞退・cancel・保存後復旧で
  HP・PP・状態・持ち物を含む600 byteを完全復元。ROM用2 KiB rollbackをEWRAMへ移し、
  GBA stack破損を防止。
- 自然new-gameから候補生成、選択、CFRU policy、交換、BP、全出口復元、Flash round-trip、
  physical NPC/map scriptを2 processのlibmGBA exact-ROM smokeで確認。

## 1.1.0 — 2026-08-14

- ユーザー提供「ベガ本編トレーナー再設計V4」の141戦・610体をcanonical
  Species/Move/Item IDへ全件解決し、既存本編Trainer ID 648件へ実ROM結合。
- 主要人物62件、既存Gym NPC 39件、一般・バトルサーチャー547件を、元の名前・class・
  double battle flagを保ったまま編成、レベル、道具、技、IV下限、trainer itemごと更新。
- V4 AI rankを固定CFRU-JPの既存3段階へ変換（1→Basic、2–3→Semi Smart、4–5→Full Smart）。
  新規AI engineや6段階AIは追加していない。
- Mirageと未指定Sphere枠を保護し、追加event枠のない21設計は誤ったTrainer IDへ割り当てず
  検証済み台帳として保持。中央allocatorの重複0と実party pointerを軽量gateで検証。

## 1.0.0 — 2026-08-14

- FireRed日本版Rev.0＋Vega 2018-02-23から毎回再生成する32 MiB build chainを完成。
- Vega Move 0〜511 / Species 0〜411を固定し、CFRU-JP battle core、3段階AI、DPE-JPの
  追加Species/form、画像・鳴き声・図鑑・進化・learnsetを統合。
- トーホク本編を保ったまま、クチバ起点のカントー253 map、180 layout、wild table、
  8 Gym＋四天王・Champion、Lv.68〜100固定高難度進行、無料往復を実ROMへ追加。
- 即時文章、高速移動、全体学習装置、経験アメ、現代孵化、SV式王冠、IV/EV、育成道具、
  PC検索・複数選択・一括操作、Field PC、タマゴバスケット、自動戦闘をrelease設定へ追加。
- Battle Factory Trial/Standard/Full/Master、rental交換、BP shop、施設外捕獲NPC、
  NORMAL/RESEARCH、三段階再戦・League、高難度Raid、段階的gimmick解禁を追加。
- versioned save ledger、旧Vega一回性migration、Factory/遭遇transaction復旧を追加。
- 中央allocatorでT09/T14の重複を解消し、Kanto map/content/QOL runtimeを単一stageへ実配置。
- exact-ROM libmGBA、400地方往復、253 map到達、125共有捕獲、34 event分岐、20 facility mode、
  BPS完全往復、禁止binary監査、fresh-checkout再構築をrelease gate化。
