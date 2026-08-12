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

## Required outputs

- `src/kanto/vermilion/`
- `content/vermilion/`
- `reports/generated/vermilion_slice.md`

## Acceptance gates

- [ ] Travel is reversible and does not alter Vega warps.
- [ ] Gym puzzle resets/finishes correctly.
- [ ] Trainer and reward IDs are new and namespaced.
- [ ] Save/load and return travel work.
- [ ] Arrival cannot softlock even before the full Kanto route graph is imported.
- [ ] 解禁直前は乗船できず、解禁直後・殿堂入り前・全国図鑑なしで往復できる。
- [ ] 船上戦の拒否・敗北・辞退で渡航権を失わず、カントーでの全滅後も帰還できる。

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T13:`.
4. Mark the task done with `python3 scripts/taskctl.py done T13 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
