# current_state.md

最終更新: 2026-08-13

## 現在地

- マイルストーン: Gate A・T02完了 / 再構築可能なVega module harnessへ移行。
- ユーザー提供の4 ZIP、3 ROM、IPS、UPSをGit管理外へ取り込み、原本とのSHA-256一致を確認済み。
- 4 ZIPは破損・パストラバーサルなし。プレイブック基盤、競合監査、V1来歴資料、V2二地方設計資料を役割別に配置済み。
- clean ROMはBPRJ01 Rev.00、CRC32 `3B2056E9`。IPS/UPSから個別生成した参照ROMは提供済み2 ROMとbyte一致。
- 厳密競合結果は775 byte中、同値191、異値584。単純なパッチ結合はNO-GO。
- 上流pinは2026-08-12時点のGitHub既定ブランチHEADへ固定する。
- T01で固定DPE-JP/CFRU-JPをvendor外のWindows ACL保護sandboxから各2回再構築し、全variantのROM・primary blob・offsets一致を確認した。再現fingerprintは `feb30b4f3b3f6324260af767096293c4fc6de79c8cf32334d720e13767a77633`。
- DPE base ROMは `eb9434745801c8f82dc1eedbda3445a45bf6d5393290c1cec4e4c6697d3c820c`、CFRU baselineは `140aa67a38046bcbf3d211550d900929039a4e7c41e55572f9503b6f27d71922`、Factory-likeは `494b488735270cc0b384febc1dc5b73f53595905f6fd51aa32f471864f7e61b1`、minimalは `964ee5b785200b018143586351373cf60aeb37df85649173c2c8f1c98e208517`。
- ARM GCC/binutils/newlib、Python、host runner closure、mGBA/libmGBA、Windows PE converter/DLL/bridgeをversion・path・SHA-256で固定した。grit/wav2agb/mid2agbは各2回のfixtureとknown-good canonical hashを通過した。
- Factory実挙動fixtureはBP、参加判定、Battle Mine optionが参照と一致し、trainer選出は差異として分類した。固定CFRU AIの保守的cold合成上限はsingle `2,584,765` cycles、double `6,297,788` cyclesで、warmはそれぞれ `339,772` / `609,210` cycles。
- T02でDPE/CFRUのactive fixed write `6,143`件を実emission spanで再生し、同値write `155`件、許可済みoverlap `156`組を含めてT01の4 ROMとbyte一致した。分類はCFRU `5,127`、PORT `943`、RELOCATE `4`、SAME_TARGET `69`、UNKNOWN `0`。
- Vega ROMをrooted walkし、43 map group / 425 map、132 encounter header、743 trainer、4,665 script nodeを機械可読化した。RAM/save/ID、QOL 14 domain、Factory/Mirage、通貨、CFRU AI ABI/cacheも同じpolicyとvalidatorへ統合した。
- T00成果としてportableな `state/source-lock.json`、preflight、参照ROM、exact auditを生成済み。同一条件の2回目quickstartでcache reuseを確認済み。
- `VEGA_CFRU_DPE_統合設計_V2_二地方生態版` をactive review資料に切替済み。V1は来歴保存専用。
- 元FireRedのカントーを新規 `KANTO_*` 名前空間へ複製し、Vega中盤からトーホクと常時往復できる二地方構成は実現可能と判定。V2の47地点は生態設計単位であり、raw map総数ではないためT11で全建物・階層・warpとのcrosswalkを生成する。
- 早期渡航の条件は、シオウ3個目バッジの完了flag `0x0824` と、アーシア島D・Hビル初回攻略完了flag `0x114B` のANDを一回性latchへ写す。`0x114B`を含むVega所有高位flagはwhitelist移行し、旧bitmap/varsの一括copyは禁止する。早期は認定章進行0〜4の範囲、Vega殿堂入り後は後半認定章・カントーリーグ・最終共鳴を解禁する。
- 育成・操作QOLをrelease scopeへ追加済み。文章は既定即時表示、ダッシュは25%以上、自転車は50%以上の移動時間短縮を目標にする。現代式孵化、経験アメ、SV式Hyper Training、IV/EV表示、全体学習装置、タマゴPC転送はT10、PC検索・一括操作、field PC、タマゴバスケット、自動戦闘は最初のカントー縦切りを待たせずT17回帰前に統合する。
- UIと追加eventは最小実装に固定した。新規full-screen UIや長いcutsceneを作らず、既存画面・標準menu・既存NPC/端末・短いflag/reward scriptを再利用する。
- Trainer AIは固定済みCFRU-JP `src/Battle_AI/**` と既定knowledge modelを移植する。本編は一律scaleせず、一般trainer・boss・野生を進行別profileと実測したmap/batch単位の横強化で調整する。League I→II→Finalを明示flagで順番に解禁し、現行Lv.100 leagueはKanto League＋Sphere完結後のFinalへ移す。
- ブロッカーなし。

## 次の正本タスク

`design/tasks_next.md` と `python3 scripts/taskctl.py next` を正とする。現在はW1で、推奨 `PRIMARY=T03`、依存READY候補 `PARALLEL_PREP=T11,T12` である。PRIMARYは強制順ではなく、待ち時間を減らせる独立準備は並列化してよい。

- T01: DONE。固定toolchain、隔離build、baseline/Factory-like/minimal、Factory/AI実fixture、再生成可能なreportをfingerprint付きで確定した。
- T02: DONE。config-aware fixed-write、RAM/SaveBlock/ID、Vega map/encounter/trainer/script graph、早期解禁flag、QOL/施設/AIをUNKNOWN 0で確定した。アーシア港はplayer込みobject上限16のため、新規静的NPCを追加しない。
- T03: clean ROMからVegaを再適用し、32 MiB拡張、named allocator、expected-byte assertion、no-op ARM module、boot/save smokeまでを決定的buildへする。
- T11: T02のmap/ID監査を入力に、元FireRedカントーmap importerを並列準備できる。
- T12: 数値IDを待たず、V2正規化、symbolic schema、validator fixtureを並列準備する。

ARM toolchain、asset converter、mGBA/libmGBAはT01で導入・固定済み。入力、参照ROM、上流commitは一致し、ブロッカーはない。

WSLではrepository全体の標準verifyを実行しない。変更対象とtask acceptanceに必要なgateだけを選び、重複検査を避ける。旧 `scripts/verify_wsl.sh` は削除済み。

T11（カントーimporter）はT02完了後に先行準備でき、依存READYになった時点で正本へ選択・統合できる。

全体wave、終了条件、最初の動作成果は `MASTER_PLAN.md`、現在の自動導出結果は `make plan` を参照する。

## 固定済み方針

- Vega本編を母体とし、Factory UPSは参照専用にする。
- Vega Move ID 0〜511と既存Species IDを固定する。
- 追加IDはmanifestから生成する。
- カントーは別名前空間の高難度地方として復活させ、Vega本編中盤から任意訪問可能にする。
- カントー本土とトーホクは連絡船で双方向移動可能にする。ナナシマはV2本体のscope外。
- カントーのLv.68〜100帯は動的に下げない。初回警告、強制戦闘なしの安全導線、無条件の無料帰還を必須にする。
- V2の統合設計CSVはreview状態であり、進化重複、フォームキー、ID型、道具参照を修正するまで実装正本にしない。
- 育成・操作QOLの正本は `docs/QOL_POLICY.md` とし、添付内の未確定案はジャッジ最初から、タマゴIV表示、SV式王冠、預かりタマゴ5個queue、無料技思い出しとして固定する。

## 再開時の確認先

1. `AGENTS.md`
2. このファイル
3. `design/agent_context_map.md`
4. `design/tasks_next.md`
5. READYになった `tasks/T*.md`

入力詳細は `design/import_inventory.md`、資料評価は `design/import_review.md`、採択済み判断は `design/decisions.md` を参照する。
