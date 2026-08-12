# T17 — Integrate QOL-B and run regression/playtest gates

- Lane: `qa/engine`
- Depends on: `T10, T13, T16`

## Objective

Integrate the remaining QOL-B layer, then prove that the new engine and dual-region content preserve Vega completion, keep Tohoku ecology non-destructive, and make Kanto progression and return travel reliable.

## Execute

1. Create a versioned manual checkpoint matrix for Vega main story, Kanto pre-unlock, early-access pre-HoF, and post-HoF states.
2. Create clean-start tests and follow the T08 policy: test migrated saves when supported, or test explicit safe rejection when old saves are unsupported.
3. Run all static/build validators.
4. Run engine vertical slice tests.
5. Run Vermilion and full Kanto connectivity/progression tests.
6. Perform targeted battle tests for status, switching, capture, evolution, forms, items, bosses, and save/load.
7. Triage failures into release blockers, known issues, or deferred enhancements.
8. Repeat from a clean build after fixes.
9. Exercise 49 Tohoku and 47 Kanto logical locations across time/method/unlock states, 34 event branches, and 125 shared special-capture states.
10. Run 200 region round trips including save/load, reset, heal, whiteout, and full-PC cases.
11. 「未解禁」「早期解禁直後・殿堂入り前」「早期認定章進行後」「Vega殿堂入り後」のsave状態行列を検証する。
12. カントーを無視したVega本編と、早期往復・高レベル捕獲後のVega本編をどちらも完走する。
13. 地方往復200回を殿堂入り前と後の両方で実施し、Kanto permit後もTohoku側未解禁HMが使えないことを検査する。
14. QOL-Bを既存PC/list/文字入力/技思い出し画面の薄いadapterとして実装する。検索、SELECT marker複数選択、一括移動/逃がし、schema駆動field PC、relearn-pool内技変更、持ち物一括操作、登録済み預かり親から256歩ごとに共有5個queueへ生成するタマゴバスケット、通常random野生限定の自動戦闘に新規full-screen UIを作らない。
15. 序盤、中盤、殿堂入り直前/直後、Kanto League後で、即時文章、ダッシュ、自転車、現代孵化、経験アメ、IV/EV UI、育成道具、全体学習装置、タマゴPC/queueを検証する。
16. 文章の全制御code、移動の接触/座標event・warp・段差・歩数、IV/EV境界、固定RNG孵化matrix、Lv.100/box満杯/save移行を自動または決定論fixtureで回帰する。
17. QOL-Bを容量不足、禁止個体/道具/map、cancel、色違い/固定戦闘、save/load込みで検証する。タマゴバスケットは親不在/相性なし/255歩/256歩/queue満杯/無効map/再起動後の各境界を固定RNGで検査する。
18. `config/feature_matrix.csv` へ全QOL-B entry、解禁条件、release既定ON/OFFを追加し、QOL-A/Bの正本を1つに統合する。
19. FactoryのTrial/Standard/Full/Master、single/double/NPC partner multi/random、候補6→選択3、勝利後交換、BP/shop、一度限り報酬、mode別ギミックを通し、Mirage Battleの持込party/recordが変化しないことを検証する。実戦は3/7連戦を通し、49/100はstreak=48/99の決定論fixtureから境界戦と報酬だけを検証する。link multiはrelease scope外とする。
20. 施設入退場、辞退、敗北、全滅、save/load、reset、中断、blackout、変身/form、持ち物交換、消耗品、multiで、元party/HP/PP/status/持ち物と一時stateがexactに一度だけ復元されることを検証する。
21. 施設外NPCを残高不足、解禁前、party満杯かつPC満杯、cancel、支払い直後reset、逃走、撃破、全滅、再挑戦、捕獲成功で検証する。同一保留個体を再抽選せず、二重減算/増殖を起こさず、報酬戦からEXP/EV/賞金/野生所持品の盗難・持出し/drop/chainを得られないことを確認する。
22. 全Factory mode、連勝表示、Ultimate選択、BP shop、建物外NPCは既存party/list/shop/Yes-No/messageだけを再利用し、`frontier_records.c` 専用画面を含む新規full-screen UIや専用演出assetを追加しない。
23. decision直前のglobal RNGを固定して `AI_BASIC` / `AI_SEMI_SMART` / `AI_FULL_SMART` のsingle/doubleを回し、技評価、KO/2HKO、switch、hazard、setup、recovery、weather/field、trainer item、gimmick、味方巻込み回避/支援の期待actionを比較する。
24. T02で記録した固定CFRU knowledge modelと実buildを照合し、switch/faint/form/item/field変化で分散cache/historyが無効化されること、worst-caseがT01の性能閾値内であることを検証する。
25. 一般trainer、8 gym、ライバル/幹部、初回四天王/Ginnoを全体学習装置既定ONの連続saveで通し、ace範囲、gym固有戦術、地面牽制、既存/新種比、合法move/item、Vega本編完走を検証する。
26. Vega殿堂入り、HOF＋認定章4＋League I clear、Kanto League＋Sphere＋League II clearの各直前/直後で地方強豪と3段階leagueを検査し、早期認定章saveの順序飛越、Final前のLv100編成漏出、複数gimmick、未登録一般trainerの一括強化がないことを確認する。
27. NORMAL/RESEARCH/Safariを同一map/seedで比較し、元slot/1%枠/EV稼ぎ/低level導線、Tohoku area band、Kanto Lv68〜100上限、IV/ability/egg move/item/shiny policyと解禁を検証する。
28. Mirageを勝利/敗北/辞退/reset/save-load/持ち物盗難moveで検証し、Lv100、仮想item、段階reward、record/currencyとFactory分離を確認する。
29. 高難度RaidをHOF＋認定章4の直前/直後、勝利/敗北/捕獲/cancel/reset/save-loadで検証し、partner/shield、capture policy/shared key、reward repeatability/claim、retry、Mirage由来bonus tier、Raid後flag clear、通常battleと他gimmickの非干渉を確認する。

## Required outputs

- `tests/manual/VEGA_CHECKPOINTS.md`
- `tests/manual/KANTO_CHECKPOINTS.md`
- `reports/generated/regression_summary.md`
- `reports/generated/qol_b_integration.md`
- `reports/generated/facility_regression.md`
- `reports/generated/trainer_ai_regression.md`
- `config/feature_matrix.csv`
- `KNOWN_ISSUES.md`

## Acceptance gates

- [ ] All release-blocking tests pass from a clean build.
- [ ] Vega main progression remains completable to the defined gate.
- [ ] Kanto progression reaches its final objective.
- [ ] Known issues include reproduction steps and severity.
- [ ] No original Vega encounter disappears and no special species can be captured twice across regions.
- [ ] Every imported Kanto physical map is reachable or intentionally gated, and return travel is always possible.
- [ ] Kanto is unreachable immediately before the intended midgame checkpoint and reachable immediately after it without Hall of Fame or National Dex state.
- [ ] Early Kanto visitation cannot skip Vega story/warp/HM gates, and both the visited and unvisited Vega paths remain completable.
- [ ] `docs/QOL_POLICY.md` のQOL-A/QOL-Bが全checkpointでPASSし、既定即時文章・高速移動でもVega本編を完走できる。
- [ ] 育成個体、道具、タマゴ、PC操作に複製・消失・不正継承がなく、save/load後の表示と実能力値が一致する。
- [ ] QOL-Bの全機能が `docs/QOL_POLICY.md` の対象・解禁・atomicity規則どおりrelease configで有効になる。
- [ ] `config/feature_matrix.csv` がQOL-A/Bの全機能とrelease既定値を列挙し、実build configと一致する。
- [ ] QOL-Bは既存画面/標準menuへ収まり、新規full-screen UI、独自window skin、専用animation/cutscene assetを追加しない。
- [ ] 全Factory modeと連勝境界がrelease configで完走し、通常Vega戦・Mirage・save・図鑑・育成stateへの漏れがない。
- [ ] 全施設出口と異常終了で元partyがexact復元され、BP/連勝/報酬/保留遭遇の更新はatomicかつ再起動可能である。
- [ ] 施設外NPC捕獲は標準UIから即時開始し、capacity、支払い、retry、捕獲完了の全境界でcredit・個体・caught stateが一貫する。
- [ ] Factory全mode、記録、shop、遭遇NPCが既存UIだけで操作でき、link multiや専用record/capture画面をrelease scopeへ持ち込まない。
- [ ] 固定CFRU AIの全profileと既定knowledge modelがsource inventoryどおり動き、cache/RNG/performance回帰とsingle/double/gimmick fixtureを通る。
- [ ] 本編の横強化、初回league、3段階再戦/league、Sphere、NORMAL/RESEARCH/Safari、MirageがD-015とT15/T16の全境界を満たす。
- [ ] 高難度Raidが既存UIのみで全終了経路を通り、反復報酬・捕獲state・Dynamax例外を複製または通常storyへ漏出させない。

## Finish

1. タスク固有のacceptance checkだけを実行する。WSLではrepository全体のdefault verifyを実行しない。
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T17 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T17:`.
5. If another task is READY, continue without waiting for approval.
