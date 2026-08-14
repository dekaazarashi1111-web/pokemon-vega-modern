# Changelog

## Unreleased

- なし。

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
