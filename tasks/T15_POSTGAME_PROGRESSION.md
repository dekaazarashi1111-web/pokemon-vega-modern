# T15 — Implement dual-phase Kanto progression

- Lane: `content`
- Depends on: `T13, T14`

## Objective

早期任意アクセス、カントー認定章、Vega殿堂入り後の後半層を分離し、原作badge/story stateを再利用しない二段階進行にする。

## Execute

1. T02の証拠に基づき、シオウ3個目バッジ＋アーシアD・Hビル攻略後の正確な解禁flag/scriptを固定する。
2. アーシア初回便、シオウ再訪便、クチバ無料帰還船の表示・恒久latchを実装する。
3. Define KANTO gym flags and progression checks.
4. Retain gym puzzles but replace badge scripts and HM checks with independent KANTO logic.
5. 早期の要求認定章数0〜4と、`VEGA_HALL_OF_FAME` 後の後半認定章・リーグ・終盤伝説・共鳴を別ノードとして定義する。
6. Provide a fallback fast-travel terminal for development builds.
7. Generate a progression graph and detect impossible prerequisites.
8. Resolve the V2 arrival mismatch: Vermilion port/city and the Route 6/11/Diglett initial corridor are reachable on arrival while later facilities remain certification-gated.
9. Model research rank, dual-region resonance, shared special-capture state, and a permanently available return edge.
10. 初回船上戦を任意・勝敗不問にし、高レベル店売り、重要道具、伝説、後半施設を早期渡航と無条件に結び付けない。
11. Kanto scriptのVega badge/story/HM flagへの書込み、境界ノード以外のVega進行flag参照をlintする。
12. 全体学習装置、タマゴPC転送/5個queue、技思い出し、あかいいと、power系、経験アメ各tier、mint、特性道具、王冠、EV reset service/item、まるいおまもり、PC検索/一括操作、field PC、持ち物操作、タマゴバスケット、自動戦闘の解禁を `docs/QOL_POLICY.md` の境界へ接続する。
13. QOL解禁は既存NPC/端末の短い `SIMPLE_EVENT` と1回のflag/reward処理で実装し、専用cutsceneや多段questを追加しない。
14. クチバ港の同じ簡易Factory受付で4段階を解禁する。D・Hビル後は一般種・ギミックなしの3連戦Trial、Vega 5個目badge後はsingle/double・交換・7連戦のStandard、Vega殿堂入り後は高種族値/準伝説とLittle/Monotype/Unrestricted/OU/Uber/Camomons等を含むFull、Kanto League後は高難度AI・完成育成・GS/地方混成・49/100連勝戦を含むMasterとする。
15. Factoryはrental専用、Vegaミラージュバトルは育成済み持込専用としてstate/rewardを分離する。Mega/Z/Dynamax/Teraはmode別に解禁し、Ultimateだけ入場時に1方式を選択する。
16. BP shop、rental pool、遭遇credit/poolをstory gateへ接続し、早期渡航だけで後半育成品・特殊種・高連勝報酬を解禁しない。
17. `region=TOHOKU` の地方強豪へ3段階再戦を定義する。Vega殿堂入り後は通常Lv58〜68/強敵72〜84、`VEGA_HALL_OF_FAME && KANTO_CERT_4` 後は72〜82/84〜94、Kanto League後は88〜96/94〜100とする。leagueはstep 18の別順序を正とし、全一般trainerではなく主要バトルサーチャー対象、調査boss、ライバル、D・H幹部だけを登録する。Kanto trainerはV2認定章帯とLv68〜100固定方針を維持する。
18. 強化League Iを `VEGA_HALL_OF_FAME` 後（Lv84〜90、medium EV、ギミックなし）、League IIを `VEGA_HALL_OF_FAME && KANTO_CERT_4 && LEAGUE_I_CLEARED` 後（Lv92〜96、6体、一部MegaまたはZ）、Final Leagueを `KANTO_LEAGUE_CLEAR && SPHERE_COMPLETE && LEAGUE_II_CLEARED` 後（全Lv100、6V/適正nature/完成EV、各trainer最大1 gimmick）に解禁する。既存Lv100編成はFinalへ移す。
19. 通常storyではmodern gimmickを敵味方とも必須にせず、Vega殿堂入り後にMega、`VEGA_HALL_OF_FAME && KANTO_CERT_4` 後にZ、Kanto League後にTera/Dynamaxを進行systemとして解禁する。各trainerは1戦最大1方式とし、QOL道具の既存first-availability/repeatabilityは `docs/QOL_POLICY.md` を優先する。
20. Vega殿堂入り後に既存scanner/DexNav/調査端末からRESEARCH table profileを任意解禁する。NORMAL profile、Safari低level育成導線、元Vega捕獲flagは常時保護する。
21. Vega殿堂入り後にTM再利用licenseとhidden-ability DexNavを解禁し、`VEGA_HALL_OF_FAME && KANTO_CERT_4` 後に追加の競技用item供給、Kanto League後にBoost EnergyとUB/Paradox関連を解禁する。`docs/QOL_POLICY.md` のfirst-availability/repeatabilityを双方とも後退させず、ここでは未提供品の追加供給経路と戦闘system側の利用時期だけをgateする。
22. `VEGA_HALL_OF_FAME && KANTO_CERT_4` 後に高難度Raidを解禁する。既存mapの短いNPC/調査端末から標準Yes-Noで起動し、Raid中だけDynamaxを固定許可する。専用den map、ロビー、full-screen UI、長いeventは作らない。

## Required outputs

- `content/kanto_progression.csv`
- `content/qol_progression.csv`
- `content/facility_progression.csv`
- `content/trainer_progression.csv`
- `generated/kanto/progression/`
- `reports/generated/progression_graph.md`

## Acceptance gates

- [ ] 意図した中盤checkpointより前は渡航できず、checkpoint直後・殿堂入り前に渡航できる。
- [ ] All included Kanto areas have a valid progression path.
- [ ] Gym flags do not modify Vega badges.
- [ ] Development shortcuts are disabled in release config.
- [ ] The progression graph rejects unreachable nodes, circular gates, and every state in which return to Tohoku is impossible.
- [ ] 早期認定章層とpost-HoF層の境界が機械検査され、殿堂入り前に後半ノードへ到達できない。
- [ ] Kanto側の状態変更でVega本編のwarp/HM/story gateを開かない。
- [ ] 各QOL unlockの直前/直後fixtureがあり、Kanto早期アクセスだけでVega殿堂入り後・Kanto League後の育成報酬を解禁できない。
- [ ] Vega badge由来とKanto由来のQOL unlockは `content/qol_progression.csv` で一意に導出され、saveへ同じ解禁stateを二重保存しない。
- [ ] Trial/Standard/Full/Masterの直前・直後fixtureがあり、各mode、rental pool、BP shop、遭遇poolは指定境界でだけ解禁される。
- [ ] FactoryとMirageの連勝、通貨、party owner、報酬が相互に更新されず、各ギミックmodeの解禁も独立する。
- [ ] 3段階再戦/leagueの直前・直後fixtureがあり、早期認定章4個saveでもLeague I→II→Finalの順序を飛ばさず、既存Lv100 leagueはFinal条件前に選択されない。
- [ ] RESEARCH profileは殿堂入り前に選べず、解禁後もNORMAL/Safariと既存捕獲stateを置換しない。
- [ ] TM license、hidden-ability DexNav、競技用item反復、UB/Paradoxの直前/直後fixtureがあり、QOL道具の既存first-availability/repeatabilityを後退させない。
- [ ] 高難度RaidはHOF＋認定章4個の直前で起動せず、直後にだけ既存UIから起動し、通常storyのDynamax解禁や進行skipを起こさない。

## Finish

1. Run task-specific acceptance checks, then run the platform default verify once as defined by `AGENTS.md`.
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T15 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T15:`.
5. If another task is READY, continue without waiting for approval.
