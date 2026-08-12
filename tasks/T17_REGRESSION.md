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

## Required outputs

- `tests/manual/VEGA_CHECKPOINTS.md`
- `tests/manual/KANTO_CHECKPOINTS.md`
- `reports/generated/regression_summary.md`
- `reports/generated/qol_b_integration.md`
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

## Finish

1. Run task-specific acceptance checks, then run the platform default verify once as defined by `AGENTS.md`.
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T17 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T17:`.
5. If another task is READY, continue without waiting for approval.
