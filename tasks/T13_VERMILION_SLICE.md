# T13 — Implement Vermilion early-access vertical slice

- Lane: `maps`
- Depends on: `T10, T11, T12`

## Objective

Vega本編中盤の定義済みcheckpointから、殿堂入り前に安全なクチバ往復を遊べる最初の製品縦切りを完成させる。

## Execute

1. T02で確定した「シオウ3個目バッジ＋アーシアD・Hビル攻略後」の実flagから `KANTO_TRAVEL_UNLOCKED` を一度だけ設定する。
2. 初回用アーシア港NPC、初訪問後のシオウ再訪便、クチバの常時無料帰還船を作る。
3. Import Vermilion port/city and required interiors under new KANTO IDs.
4. Preserve NPC placement where useful; remap scripts, flags, trainer IDs, item flags, and text.
5. Import the gym layout and puzzle, replacing progress vars with KANTO vars.
6. クチバジムは到着時に無条件解禁せず、必要認定章状態のtest fixtureでtrainer、boss、報酬を検証する。
7. 初回乗船前に推奨Lv.65以上の警告を出し、船上戦を任意・勝敗不問にする。
8. Test save/load inside Kanto and return to Vega.
9. Test PC/heal, reset, whiteout, and Escape/dynamic-warp behavior, keeping the return NPC available in every progression state.
10. 港からPC/回復と帰還船まで、強制戦闘、不可避の草むら、field move要求、支払いを0にする。
11. T11のphysical map inventory/crosswalkをT12のlogical schemaへbindし、build-mode emissionと全参照解決を検証する。
12. クチバ港の簡易別棟または既存interior再利用で早期Factory Trialを配置し、Sevii/Trainer Tower、新規大型facility map、専用受付UIを最初の縦切りへ追加しない。`content/vermilion/factory_trial.csv` に最小候補6体、対戦相手、3連戦、初回BP/credit、早期遭遇poolを所有させ、T16はこの縦切りを拡張する。
13. 建物外へランダム捕獲NPCを置く。施設flag解除と元party復元、捕獲先（partyまたはPC）容量、`payment_kind` に対応する残高を先に検査し、標準message/list/Yes-Noで確認する。減算と固定個体の保留をT08 transactionで保存してから通常scripted wild battleを即開始し、save失敗時は減算せず開始しない。
14. 捕獲成功で保留遭遇を消し、逃走・撃破・全滅では同じ個体を保持して次回会話から無償再戦する。保留中は別抽選を拒否し、専用捕獲区画・長いevent・新規full-screen UIを作らない。

## Required outputs

- `src/kanto/vermilion/`
- `content/vermilion/`
- `content/vermilion/factory_trial.csv`
- `reports/generated/vermilion_slice.md`

## Acceptance gates

- [ ] Travel is reversible and does not alter Vega warps.
- [ ] Gym puzzle resets/finishes correctly.
- [ ] Trainer and reward IDs are new and namespaced.
- [ ] Save/load and return travel work.
- [ ] Arrival cannot softlock even before the full Kanto route graph is imported.
- [ ] 解禁直前は乗船できず、解禁直後・殿堂入り前・全国図鑑なしで往復できる。
- [ ] 船上戦の拒否・敗北・辞退で渡航権を失わず、カントーでの全滅後も帰還できる。
- [ ] T11/T12 crosswalkの全クチバ参照が実physical mapへ解決し、未解決keyを含むbuildは失敗する。
- [ ] 殿堂入り前の最初の訪問からFactory Trialと建物外NPCを利用でき、どちらからも無料帰還路を失わない。
- [ ] 建物外NPCは支払い/容量をatomicに扱い、通常partyで即時捕獲戦を開始し、施設rentalや一時stateを持ち出さない。

## Finish

1. Run task-specific acceptance checks, then run the platform default verify once as defined by `AGENTS.md`.
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T13 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T13:`.
5. If another task is READY, continue without waiting for approval.
