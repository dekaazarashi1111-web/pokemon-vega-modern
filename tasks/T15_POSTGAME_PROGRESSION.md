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

## Required outputs

- `content/kanto_progression.csv`
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

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T15:`.
4. Mark the task done with `python3 scripts/taskctl.py done T15 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
